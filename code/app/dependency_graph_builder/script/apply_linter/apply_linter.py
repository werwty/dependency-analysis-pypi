from typing import List, FrozenSet
import os
import shlex
import tarfile
import zipfile

from contextlib import contextmanager
from tempfile import TemporaryDirectory

from lib.RepoProxy import LocalMirrorRepoProxy
from lib.RepoProxy import RemoteRepoProxy
from script.apply_linter.ThreadPool import ThreadPool, makeRequests
from script.apply_linter.shell_cmd_warpper import ShellCmdWrapper, open_output_log, close_output_log, \
    test_and_create_dir

from threading import Lock

_global_lock = Lock()
_old_print = print


def print(*a, **b):
    with _global_lock:
        _old_print(*a, **b)


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')
local_repo = LocalMirrorRepoProxy('/mnt/MyPassportExt4/PyPI_Mirror/pypi/web')
remote_repo = RemoteRepoProxy(local_cache_dir=os.path.join(SCRIPT_DIR, "pkg_cache"))


def get_analysis_list():
    import json
    with open(os.path.join(SCRIPT_DIR, "pkg_to_analysis.json"), "r") as fp:
        return json.load(fp)


@contextmanager
def get_unpacked_package(url):
    pkg_fqn = local_repo.request_pkg_file(url)
    if not pkg_fqn:
        pkg_fqn = remote_repo.request_pkg_file(url)
    if not os.path.isfile(pkg_fqn):
        raise ValueError("Not a valid package archive: %s" % pkg_fqn)

    with TemporaryDirectory() as tmp_dir:
        archive = None
        try:
            if pkg_fqn.endswith('.zip') or pkg_fqn.endswith('whl'):
                archive = zipfile.ZipFile(pkg_fqn)
                archive.extractall(tmp_dir)
            elif pkg_fqn.endswith('gz') or pkg_fqn.endswith('bz2'):
                archive = tarfile.TarFile.open(pkg_fqn)
                archive.extractall(tmp_dir)
            else:
                raise ValueError('Not a known archive format: %s' % pkg_fqn)
        finally:
            if archive:
                archive.close()
        yield tmp_dir


def run_static_analyzer(analyzer_cmd, valid_retcode, stdout_path, stderr_path, max_freeze_time=15 * 60):
    # type: (List[str], FrozenSet[int], str,str, int) -> bool
    stdout_pipe, stderr_pipe = open_output_log(stdout_path, stderr_path)

    analyzer_process = ShellCmdWrapper(analyzer_cmd, stdout_pipe, stderr_pipe)
    analyzer_process.launch_cmd()
    # terminate the process if it freeze at least <max_freeze_time> seconds
    stuck = analyzer_process.wait_with_freeze_detection(max_freeze_time)
    if stuck:
        analyzer_success = False
        analyzer_process.stop_process()
    else:
        ret_code = analyzer_process.get_ret_code()
        analyzer_success = ret_code in valid_retcode

    close_output_log(stdout_pipe, stderr_pipe)
    return analyzer_success


def run_bandit_analyzer(proj_folder, file_save_report_to, dir_save_console_output_to):
    test_and_create_dir(os.path.dirname(file_save_report_to))
    test_and_create_dir(dir_save_console_output_to)
    stdout_path = os.path.join(dir_save_console_output_to, "stdout.txt")
    stderr_path = os.path.join(dir_save_console_output_to, "stderr.txt")

    bandit_cmd = [
        'bandit',
        '--recursive',  # recursive
        '--output', shlex.quote(file_save_report_to),  # save report to file
        '--format', 'json',  # output report in json format
        ('%s' % shlex.quote(proj_folder))
    ]

    bandit_valid_retcode = frozenset({0, 1})
    bandit_run_succ = run_static_analyzer(bandit_cmd, bandit_valid_retcode, stdout_path, stderr_path)

    return bandit_run_succ


def run_pyflakes_analyzer(proj_folder, file_save_report_to, dir_save_console_output_to):
    test_and_create_dir(os.path.dirname(file_save_report_to))
    test_and_create_dir(dir_save_console_output_to)
    stdout_path = os.path.join(dir_save_console_output_to, "stdout.txt")
    stderr_path = os.path.join(dir_save_console_output_to, "stderr.txt")

    pyflakes_cmd = [
        'pyflakes',
        ('%s' % shlex.quote(proj_folder))
    ]
    pyflakes_valid_retcode = frozenset({0, 1})

    pyflakes_succ = run_static_analyzer(pyflakes_cmd, pyflakes_valid_retcode, stdout_path, stderr_path)

    if os.path.exists(file_save_report_to):
        os.remove(file_save_report_to)
    os.symlink(stdout_path, file_save_report_to)

    return pyflakes_succ


def do_bandit(pkg_url, pkg_fqn):
    with get_unpacked_package(pkg_url) as proj_path:
        print("Analyzing %s With bandit..." % pkg_fqn)
        bandit_report_dir = os.path.join(OUTPUT_DIR, "bandit", "report")
        bandit_console_log_dir = os.path.join(OUTPUT_DIR, "bandit", "log")
        bandit_succ = run_bandit_analyzer(
            proj_path + "/.",
            os.path.join(bandit_report_dir, "%s.txt" % pkg_fqn),
            os.path.join(bandit_console_log_dir, pkg_fqn)
        )
    if not bandit_succ:
        print("  bandit failed on pkg: %s" % pkg_fqn)


def do_pyflakes(pkg_url, pkg_fqn):
    with get_unpacked_package(pkg_url) as proj_path:
        print("Analyzing %s with pyflakes..." % pkg_fqn)
        pyflakes_report_dir = os.path.join(OUTPUT_DIR, "pyflakes", "report")
        pyflakes_console_log_dir = os.path.join(OUTPUT_DIR, "pyflakes", "log")
        pyflakes_succ = run_pyflakes_analyzer(
            proj_path + "/.",
            os.path.join(pyflakes_report_dir, "%s.txt" % pkg_fqn),
            os.path.join(pyflakes_console_log_dir, pkg_fqn)
        )
    if not pyflakes_succ:
        print("  pyflakes failed on pkg: %s" % pkg_fqn)


def main():
    analysis_list = get_analysis_list()
    analyzer_call_args = []
    for pkg_to_analysis in analysis_list:
        pkg_name = pkg_to_analysis["name"]
        pkg_ver = pkg_to_analysis["version"]
        pkg_url = pkg_to_analysis["src"]
        pkg_n_dep = pkg_to_analysis["number_dependents"]
        pkg_fqn = "%s@%s" % (pkg_name, pkg_ver)
        analyzer_call_args.append(((pkg_url, pkg_fqn), {}))

    pool = ThreadPool(16)
    requests = makeRequests(do_bandit, analyzer_call_args)
    requests.extend(makeRequests(do_pyflakes, analyzer_call_args))
    [pool.putRequest(req) for req in requests]
    pool.wait()


if __name__ == '__main__':
    main()
