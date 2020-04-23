import sys
import time

from lib.DependencySolver.PoetryDependencySolver.PoetryDependencySolver import PoetryDependencySolver, dep_graph_walker
from lib.RepoProxy import LocalMirrorRepoProxy


def search_index(name, pkg_list):
    for i, n in enumerate(pkg_list):
        if n == name:
            return i

    return None


def main():
    local_mirror_repo = LocalMirrorRepoProxy()

    dep_solver = PoetryDependencySolver(verbose_output=False)
    dep_solver.setup_repo_pool()

    avail_pkg_list = local_mirror_repo.available_packages()

    succ_fail_list = [
        # ["Worker 1", "KubeGrade", "Krypton"],
        ['Worker 1', 'Watson', 'Watershed'],
        # ["Worker 2", "confine-controller", "confindr"],
        ["Worker 2", "diagnnose", "diagnosticism"],
        # ["Worker 4", "licpy", "lichv"],
        # ["Worker 6", "plumi.migration", "plumi.app"],
        ["Worker x", "botymcbotface", "plumi.app"],
    ]

    for wid, last_succ_pkg, last_fail_pkg in succ_fail_list:
        succ_idx = search_index(last_succ_pkg, avail_pkg_list)
        fail_idx = search_index(last_fail_pkg, avail_pkg_list)
        print(
            "%s: succ: %s (%d), fail: %s(%d), recovery idx: %d" % (
                wid, last_succ_pkg, succ_idx, last_fail_pkg, fail_idx, max(succ_idx, fail_idx) + 1
            )
        )


if __name__ == '__main__':
    main()
