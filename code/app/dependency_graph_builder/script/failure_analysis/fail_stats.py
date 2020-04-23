#!/usr/bin/env python3
import re
import sys
from collections import defaultdict
from functools import partial
from pprint import pformat

regex = r"^\[(\S+?)\]: (.*?)\n"

regex_dependency_has_conflict_requires = r"\s*Because \S+? \S+\sdepends on "
regex_no_available_version_match = r"\s*Because no versions of "

known_causes = [
    (
        "Maximum poetry recursion depth exceeded",
        lambda m: m.startswith("maximum recursion depth exceeded")
    ),

    (
        "Poetry analysis timeout",
        lambda m: m.startswith("Execution time limit reached!")
    ),

    (
        "Invalid Requirement: failed to parse requirement",
        lambda m: m.startswith("Invalid requirement, parse error at")
    ),

    (
        "Invalid Requirement: Could not parse version constraint",
        lambda m: m.startswith("Could not parse version constraint:")
    ),

    (
        "Requirement contradiction",
        lambda m: re.match(regex_no_available_version_match, m)
    ),

    (
        "No suitable package release was found: Root",
        lambda m: m.startswith("Because dep-solver-root-c6c3d607")
    ),

    (
        "No suitable package release was found: Dependency",
        lambda m: re.match(regex_dependency_has_conflict_requires, m)
    ),

    (
        "Not compatible with Python 3.8",
        lambda m: m.startswith("The current project's Python requirement (^3.8) is not compatible")
    ),

    (
        "Package URL no longer exist",
        lambda m: m.startswith("404 Client Error:")
    ),

    (
        "Post-process verification fail",
        lambda m: m.startswith("Post-process verification fail: only one package is suppose to have depth 0")
    ),

    (
        "To be investigated: no error msg is logged",
        lambda m: m == ""
    ),
    (
        "To be investigated: 'NoneType' object is not iterable",
        lambda m: m.startswith("'NoneType' object is not iterable")
    ),
    (
        "To be investigated: Unable to parse",
        lambda m: m.startswith("Unable to parse")
    ),
    (
        "To be investigated: join() argument must be str, bytes, or os.PathLike object",
        lambda m: m.startswith("join() argument must be str, bytes, or os.PathLike object")
    ),
    (
        "To be investigated: can only concatenate str (not \"int\") to str",
        lambda m: m.startswith("can only concatenate str (not \"int\") to str")
    ),
    (
        "To be investigated: not enough values to unpack (expected 4, got 2)",
        lambda m: m.startswith("not enough values to unpack (expected 4, got 2)")
    ),
    (
        "To be investigated: Compressed file ended before the end-of-stream marker was reached",
        lambda m: m.startswith("Compressed file ended before the end-of-stream marker was reached")
    ),
    (
        "To be investigated: expected string or bytes-like object",
        lambda m: m.startswith("expected string or bytes-like object")
    ),
    (
        "To be investigated: The dependency name for ",
        lambda m: m.startswith("The dependency name for ")
    ),
    (
        "To be investigated: 'python-xlib'",
        lambda m: m.startswith("'python-xlib'")
    ),
    (
        "To be investigated: timestamp out of range for platform time_t",
        lambda m: m.startswith("timestamp out of range for platform time_t")
    ),
    (
        "To be investigated: list index out of range",
        lambda m: m.startswith("list index out of range")
    ),
    (
        "To be investigated: file could not be opened successfully",
        lambda m: m.startswith("file could not be opened successfully")
    ),
    (
        "To be investigated: 'EmptyConstraint' object has no attribute 'min'",
        lambda m: m.startswith("'EmptyConstraint' object has no attribute 'min'")
    ),
    (
        "To be investigated: [Errno 13] Permission denied: '/tmp/",
        lambda m: m.startswith("[Errno 13] Permission denied: '/tmp/")
    ),
    (
        "To be investigated: [Errno 13] Permission denied: '/Users'",
        lambda m: m.startswith("[Errno 13] Permission denied: '/Users'")
    ),
    (
        "To be investigated: unhashable type: 'VersionUnion'",
        lambda m: m.startswith("unhashable type: 'VersionUnion'")
    ),
    (
        "To be investigated: Unable to retrieve the package version",
        lambda m: m.startswith("Unable to retrieve the package version")
    ),
]


def error_log_reader(error_log):
    test_str = error_log
    matches = re.finditer(regex, test_str, re.MULTILINE)

    for match in matches:
        yield match.group(1), match.group(2)


def main():
    int()
    cause_count_bin = defaultdict(partial(int, 0))
    failed_pkg_set = defaultdict(list)
    seen = set()

    for worker_id in range(1, 9):
        print("\n--------------\n")
        print("Statistic worker {}'s log...".format(worker_id))
        with open(sys.argv[1] + "/worker{}/log/fail.txt".format(worker_id),
                  'r') as flog_fp:
            error_log = flog_fp.read()
        for failed_pkg, recorded_exception in error_log_reader(error_log):
            cause_unknown = True
            if failed_pkg in seen:
                print("Already seen '%s'" % failed_pkg)
            seen.add(failed_pkg)

            for cause_id, cause_desc in enumerate(known_causes):
                if cause_desc[1](recorded_exception):
                    cause_count_bin[cause_id] += 1
                    failed_pkg_set[cause_id].append(failed_pkg)
                    cause_unknown = False
                    break

            if cause_unknown:
                print("Pkg: {} - {} ".format(failed_pkg, recorded_exception))

    ranked_causes = sorted(
        cause_count_bin.items(), key=lambda a: a[1], reverse=True
    )

    rerun_package_set = []
    for rank, cause in enumerate(ranked_causes, start=1):
        frequency = cause[1]
        cause_id = cause[0]
        print("No %2d. %10d: %s" % (
            rank, frequency, known_causes[cause_id][0]
        ))
        with open("output/fail_pkgs/rank{}.txt".format(rank), "w") as outfp:
            outfp.write("No %d. %10d: %s\n========\n" % (
                rank, frequency, known_causes[cause_id][0]
            ))
            outfp.write(pformat(failed_pkg_set[cause_id]))

        if cause_id != 1:
            rerun_package_set.extend(failed_pkg_set[cause_id])

    with open("output/fail_pkgs/rerun_list.txt", "w") as outfp:
        rerun_package_set = reversed(rerun_package_set)
        for pkg_name in rerun_package_set:
            outfp.write("%s\n" % pkg_name)


if __name__ == '__main__':
    main()
