from typing import (
    FrozenSet, Iterable, List, Optional, Set, Text, Tuple, Union, Any, Dict, Callable
)

from clikit.api.io.flags import DEBUG
from clikit.io import ConsoleIO
from poetry.packages import Package, DependencyPackage, Dependency
from poetry.repositories import Pool
from poetry.repositories.legacy_repository import LegacyRepository
from poetry.version.markers import AnyMarker

from lib.DependencySolver.PoetryDependencySolver.Repository.HybirdRepository import HybirdRepository
from poetry.repositories.repository import Repository
from poetry.repositories.pypi_repository import PyPiRepository
# from poetry.factory import Factory as PoetryFactory
from lib.DependencySolver.PoetryDependencySolver.Factory.CustomPoetryFactory import CustomPoetryFactory
from poetry.puzzle.solver import Solver

from poetry.mixology import resolve_version

from poetry.puzzle.exceptions import CompatibilityError
from poetry.mixology.failure import SolveFailure

from poetry.utils._compat import Path
import os


class PoetryDependencySolver:
    def __init__(self):
        self.repo_pool = Pool()
        self.poetry_factory = CustomPoetryFactory()
        self.cwd = os.getcwd()
        self.console_io = ConsoleIO()
        # self.console_io.set_verbosity(DEBUG)

    def setup_repo_pool(self):
        hybird_repo = HybirdRepository("pypi-simple", "https://pypi.org/simple",
                                       local_mirror_path='/mnt/MyPassportExt4/PyPI_Mirror/pypi/web')
        self.repo_pool.add_repository(hybird_repo, True)

        # pypi_offical_repo = PyPiRepository()
        # self.repo_pool.add_repository(pypi_offical_repo)

    def solve(self, requirements, solve_extra_dep=False):
        # type: (List[Tuple[str,str]], bool) -> (Dict[str, Any], List[DependencyPackage], List[int])
        poetry = self.poetry_factory.create_poetry(Path(self.cwd), do_pool_setup=False)
        poetry.set_pool(self.repo_pool)  # Rework on pool

        for _name, _req in requirements:
            poetry.package.add_dependency(_name, _req)

        solver = Solver(
            package=poetry.package,
            pool=poetry.pool,
            # no package installed
            installed=Repository(),
            # no package locked
            locked=Repository(),
            io=self.console_io,
        )

        use_latest = None

        try:
            result = resolve_version(
                solver._package, solver._provider, locked={}, use_latest=use_latest
            )

            packages = result.packages
        except CompatibilityError as e:
            return solver.solve_in_compatibility_mode(
                e.constraints, use_latest=use_latest
            )
        except SolveFailure as e:
            from poetry.puzzle.exceptions import SolverProblemError
            raise SolverProblemError(e)

        graph = solver._build_graph(solver._package, packages)

        depths = []
        final_packages = []
        for package in packages:
            category, optional, marker, depth = solver._get_tags_for_package(
                package, graph
            )

            if marker is None:
                marker = AnyMarker()
            if marker.is_empty():
                continue

            package.category = category
            package.optional = optional
            package.marker = marker

            depths.append(depth)
            final_packages.append(package)

        return graph, final_packages, depths


def default_dep_edge_handler(dependent, required_by):
    # type: (DependencyPackage, DependencyPackage) -> None

    def format_node(_name, _ver):
        text = '{}, ver {}'.format(_name, _ver).ljust(30)
        return "[{}]".format(text)

    def format_edge(_constraint):
        # text = " {} ".format(_constraint).ljust(80, '='),
        # final_text = "===={}>".format(text)
        # return final_text
        text = (" %s " % _constraint).ljust(80, '='),
        final_text = "====%s>" % text
        return final_text

    if required_by.package:
        dep_pkg = dependent.package  # type: Package
        dep_pkg_dep = dependent.dependency  # type: Dependency
        req_pkg = required_by.package  # type: Package
        req_pkg_dep = required_by.dependency  # type: Dependency

        msg = "{} {} {}".format(
            format_node(req_pkg.pretty_name, req_pkg.pretty_version),
            format_edge("{} ({})".format(dep_pkg_dep.pretty_name, dep_pkg_dep.pretty_constraint)),
            format_node(dep_pkg.pretty_name, dep_pkg.pretty_version)
        )
    else:
        dep_pkg = dependent.package  # type: Package
        dep_pkg_dep = dependent.dependency  # type: Dependency
        msg = "{}, constraint {}".format(
            format_node(dep_pkg.pretty_name, dep_pkg.pretty_version),
            dep_pkg_dep.pretty_constraint
        )

    print(msg)


def dep_graph_walker(graph, package_list, edge_handler=default_dep_edge_handler):
    # type: (Dict[str, Any], List[DependencyPackage], Callable[[DependencyPackage,DependencyPackage], None]) -> None
    pass
    package_lookup_tbl = dict()

    from lib.DependencySolver.PoetryDependencySolver.Factory.CustomPoetryFactory import CustomPoetryFactory

    for pkg in package_list:
        package_lookup_tbl[pkg.name] = pkg

    package_lookup_tbl[CustomPoetryFactory.POETRY_PROJECT_NAME] = DependencyPackage(None, None)

    def _dep_graph_walker(curr_node, parent_node):
        # type: (Dict[str, Any],Dict[str, Any]) -> None
        for child in curr_node['children']:
            _dep_graph_walker(child, curr_node)
        assert curr_node['name'] in package_lookup_tbl.keys()

        edge_handler(
            package_lookup_tbl[curr_node['name']],
            package_lookup_tbl[parent_node['name']],
        )

    for root_child in graph['children']:
        _dep_graph_walker(root_child, graph)


def main():
    dep_solver = PoetryDependencySolver()
    dep_solver.setup_repo_pool()

    def demo_dep(pkg_name, ver_constraint):
        dep_graph, pkg_list, depth = dep_solver.solve([
            (pkg_name, ver_constraint)
        ])

        dep_graph_walker(dep_graph, pkg_list, default_dep_edge_handler)

    demo_dep("requests", "*")
    demo_dep("poetry", "*")


if __name__ == '__main__':
    main()
