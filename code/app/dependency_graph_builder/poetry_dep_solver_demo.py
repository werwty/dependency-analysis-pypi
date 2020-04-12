import sys
import time

from lib.DependencySolver.PoetryDependencySolver.PoetryDependencySolver import PoetryDependencySolver, dep_graph_walker
from lib.RepoProxy import LocalMirrorRepoProxy


def main():
    local_mirror_repo = LocalMirrorRepoProxy()

    dep_solver = PoetryDependencySolver(verbose_output=False)
    dep_solver.setup_repo_pool()

    avail_pkg_list = local_mirror_repo.available_packages()

    def demo_dep(pkg_name, ver_constraint):
        dep_graph, pkg_list, depth, pkg_info_src = dep_solver.solve([
            (pkg_name, ver_constraint)
        ])

        dep_graph_walker(dep_graph, pkg_list)

    total_pkg = len(avail_pkg_list)
    task_start_time = time.perf_counter()

    for idx, pkg in enumerate(avail_pkg_list):
        time_now = time.perf_counter()
        print("*" * 80)
        print("*" + " " * (80 - 2) + "*")
        print("* %s *" % ("Solving dependency %d/%d" % (idx + 1, total_pkg)).ljust(80 - 4))
        print("* %s *" % ("Package name: %s" % pkg).ljust(80 - 4))
        print("* %s *" % ("Avg processing speed: %f pkg/s" % (idx / (time_now - task_start_time))).ljust(80 - 4))
        print("*" + " " * (80 - 2) + "*")
        print("*" * 80)
        try:
            demo_dep(pkg, "*")
        except Exception as ex:
            sys.stderr.write("Fail for '%s', reason: %s\n" % (pkg, str(ex)))


if __name__ == '__main__':
    main()
