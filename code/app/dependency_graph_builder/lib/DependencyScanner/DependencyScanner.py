import json
import os
import sys
import time
import datetime
from collections import defaultdict
from typing import (
    FrozenSet, Iterable, List, Optional, Set, Text, Tuple, Union, Any, Dict
)

from poetry.packages import DependencyPackage, Package, Dependency

from lib.DependencySolver.PoetryDependencySolver.PoetryDependencySolver import PoetryDependencySolver, dep_graph_walker
from lib.RepoProxy import LocalMirrorRepoProxy
from poetry.utils.helpers import canonicalize_name
from lib.DependencySolver.PoetryDependencySolver.Repository.HybirdRepository import HybirdRepository
import signal
from contextlib import contextmanager


class TimeoutException(Exception): pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Execution time limit reached!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class DepInfoDumper:
    def __init__(self):
        self.pkg_dep = defaultdict(dict)
        self.package_lookup_tbl = dict()
        self.root_pkg_name = None
        self.root_pkg_ver = None

    def collect_dep_infomation(self, graph):
        # type: (Dict[str, Any]) -> None

        def dep_edge_handler(dependent, required_by):
            # type: (DependencyPackage, DependencyPackage) -> None
            if required_by.package:
                dep_pkg = dependent.package  # type: Package
                dep_pkg_dep = dependent.dependency  # type: Dependency
                req_pkg = required_by.package  # type: Package
                req_pkg_dep = required_by.dependency  # type: Dependency

                if dep_pkg.pretty_name in self.pkg_dep[req_pkg.pretty_name].keys():
                    # TODO: check equality
                    pass
                else:
                    self.pkg_dep[req_pkg.pretty_name][dep_pkg.pretty_name] = {
                        "dep_name": str(dep_pkg.pretty_name),
                        "dep_ver": str(dep_pkg.pretty_version),
                        "dep_constraint": "{} ({})".format(dep_pkg_dep.pretty_name, dep_pkg_dep.pretty_constraint)

                    }
            else:
                pass

        def _dep_graph_walker(curr_node, parent_node):
            # type: (Dict[str, Any],Dict[str, Any]) -> None
            for child in curr_node['children']:
                _dep_graph_walker(child, curr_node)
            assert curr_node['name'] in self.package_lookup_tbl.keys()

            dep_edge_handler(
                self.package_lookup_tbl[curr_node['name']],
                self.package_lookup_tbl[parent_node['name']],
            )

        for root_child in graph['children']:
            _dep_graph_walker(root_child, graph)

    def dump_dep_graph_info(self, package_list_with_depth, graph, dep_info_pkg_src):
        # type: (List[Tuple[DependencyPackage, int]], Dict[str, Any], HybirdRepository.DepInfoSrcUrlTracker) -> Dict

        # prepare for pkg lookup table
        from lib.DependencySolver.PoetryDependencySolver.Factory.CustomPoetryFactory import CustomPoetryFactory

        for pkg_depth_tuple in package_list_with_depth:
            if pkg_depth_tuple[1] == 0:
                if self.root_pkg_name:
                    raise ValueError(
                        "Post-process verification fail: only one package is suppose to have depth 0 in poetry output"
                        # because we resolve the dependency resolution for each package individually
                    )
                else:
                    self.root_pkg_name = pkg_depth_tuple[0].package.pretty_name
                    self.root_pkg_ver = pkg_depth_tuple[0].package.pretty_version
            self.package_lookup_tbl[pkg_depth_tuple[0].name] = pkg_depth_tuple[0]

        self.package_lookup_tbl[CustomPoetryFactory.POETRY_PROJECT_NAME] = DependencyPackage(None, None)

        # collect pkg dep information from dep graph
        self.collect_dep_infomation(graph)

        dep_info = defaultdict(dict)
        for pkg_depth_tuple in package_list_with_depth:
            pkg, depth = pkg_depth_tuple[0], pkg_depth_tuple[1]
            pkg_src = dep_info_pkg_src.query_info_src(pkg.package.pretty_name, pkg.package.pretty_version)
            pkg_rel_date = [
                dep_info_pkg_src.query_release_data_for_url(pkg.package.pretty_name,
                                                            pkg.package.pretty_version, url) for url in pkg_src
            ]
            if pkg_src:
                pkg_src = list(pkg_src)
            else:
                pkg_src = []
            dep_info[pkg.package.pretty_name] = {
                "ver": pkg.package.pretty_version,
                "src": pkg_src,
                "pkg_rel_date": pkg_rel_date,
                "dep_depth": depth,
                "dep": list(self.pkg_dep[pkg.package.pretty_name].values())
            }

        output = {
            "root_pkg": self.root_pkg_name,
            "dep_info": dep_info
        }
        return output


def dependency_scanner(avail_pkg_list, start=0, end=-1, output_folder="."):
    dep_solver = PoetryDependencySolver(verbose_output=False)
    dep_solver.setup_repo_pool()

    ANALYSIS_TIME_LIMIT_SEC = 15 * 60  # maximum 15 min allowed

    if start < 0:
        start = 0
    if end < 0 or len(avail_pkg_list) < end:
        end = len(avail_pkg_list)

    output_folder_log_folder = os.path.join(output_folder, "log")
    output_folder_data_folder = os.path.join(output_folder, "data")

    os.makedirs(output_folder_data_folder, exist_ok=True)
    os.makedirs(output_folder_log_folder, exist_ok=True)

    def log_success(_pkg_orig_name, _pkg_pretty_name, _pkg_canonical_name, _saved_filename):
        with open(os.path.join(output_folder_log_folder, "success.txt"), "a") as fp:
            fp.write("[%s/%s/%s]: '%s'\n" % (_pkg_orig_name, _pkg_pretty_name, _pkg_canonical_name, _saved_filename))

    def log_fail(_pkg_orig_name, _reason):
        with open(os.path.join(output_folder_log_folder, "fail.txt"), "a") as fp:
            fp.write("[%s]: %s\n" % (_pkg_orig_name, _reason))

    def save_dump(_pkg_orig_name, _pkg_ver, _sdump):
        filename = "%s@%s.json" % (
            _pkg_orig_name,
            _pkg_ver
        )

        with open(os.path.join(output_folder_data_folder, filename), "w") as fp:
            fp.write(_sdump)

        return filename

    def scan_dependency(pkg_name, ver_constraint):
        dep_graph, pkg_list, depth, pkg_info_src = dep_solver.solve([
            (pkg_name, ver_constraint)
        ])
        dep_dumper = DepInfoDumper()

        dep_dump = dep_dumper.dump_dep_graph_info(list(zip(pkg_list, depth)), dep_graph, pkg_info_src)

        return dep_dumper.root_pkg_name, dep_dumper.root_pkg_ver, dep_dump

    task_start_time = time.perf_counter()
    n_done = 0
    n_succ = 0
    n_fail = 0
    DISP_WID = 65
    for idx in range(start, end):
        pkg = avail_pkg_list[idx]
        time_now = time.perf_counter()

        print("*" * DISP_WID)
        print("*" + " " * (DISP_WID - 2) + "*")
        print("* %s *" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")).ljust(DISP_WID - 4))
        print("*" + " " * (DISP_WID - 2) + "*")
        print("* %s *" % ("Solving dependency %d - %d -> %d" % (start + 1, idx + 1, end)).ljust(DISP_WID - 4))
        print("* %s *" % ("Solving dependency %d - %d -> %d" % (start + 1, idx + 1, end)).ljust(DISP_WID - 4))
        print("* %s *" % ("Package name: %s" % pkg).ljust(DISP_WID - 4))
        print("* %s *" % ("Avg processing speed: %f pkg/s" % ((idx - start) / (time_now - task_start_time))).ljust(
            DISP_WID - 4))
        print("* %s *" % ("Done with %d pkgs (%d success, %d fail)" % (n_done, n_succ, n_fail)).ljust(DISP_WID - 4))
        print("*" + " " * (DISP_WID - 2) + "*")
        print("*" * DISP_WID)
        try:
            with time_limit(ANALYSIS_TIME_LIMIT_SEC):
                pkg_pretty_name, pkg_pretty_ver, dep_info_dump = scan_dependency(pkg, "*")

            dep_info_dump_json = json.dumps(dep_info_dump, indent=1)
            saved_filename = save_dump(pkg_pretty_name, pkg_pretty_ver, dep_info_dump_json)
            log_success(pkg, pkg_pretty_name, canonicalize_name(pkg_pretty_name).replace(".", "-"), saved_filename)
            n_succ += 1
        except Exception as ex:
            ex_desc = str(ex)
            print("Failed on %s, reason: %s\n" % (pkg, ex_desc))
            log_fail(pkg, ex_desc)
            n_fail += 1
        n_done += 1


def main():
    local_mirror_repo = LocalMirrorRepoProxy()
    avail_pkg_list = local_mirror_repo.available_packages()

    dependency_scanner(avail_pkg_list, int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])


if __name__ == '__main__':
    main()
