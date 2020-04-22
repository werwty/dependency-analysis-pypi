#!/usr/bin/env python3
import re
import sys
from collections import defaultdict
from functools import partial

regex = r"^\[(\S+?)\]: (.*?)\n"

regex_dependency_has_conflict_requires = r"\s*Because \S+? \S+\sdepends on "
regex_no_available_version_match = r"\s*Because no versions of "

known_reason_list = [
    (
        "Poetry fail due to maximum recursion depth exceeded",
        lambda m: m.startswith("maximum recursion depth exceeded")
    ),

    (
        "Poetry analysis timeout",
        lambda m: m.startswith("Execution time limit reached!")
    ),

    (
        "Invalid Requirement expression",
        lambda m: m.startswith("Invalid requirement, parse error at")
    ),

    (
        "Invalid version constraint",
        lambda m: m.startswith("Could not parse version constraint:")
    ),

    (
        "No available version can satisfy the requirement",
        lambda m: re.match(regex_no_available_version_match, m)
    ),

    (
        "Requirement conflict: caused by root",
        lambda m: m.startswith("Because dep-solver-root-c6c3d607")
    ),

    (
        "Requirement conflict: caused by dependency",
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
        "Poetry internal bug",
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


def error_log_parser(error_log):
    test_str = error_log
    matches = re.finditer(regex, test_str, re.MULTILINE)

    for match in matches:
        yield match.group(1), match.group(2)


def main():
    int()
    reason_count = defaultdict(partial(int, 0))
    problematic_pkg_set = defaultdict(list)
    seen = set()

    for worker_id in range(1, 9):
        print("\n--------------\n")
        print("Statistic worker {}'s log...".format(worker_id))
        with open(sys.argv[1] + "/worker{}/log/fail.txt".format(worker_id),
                  'r') as flog_fp:
            error_log = flog_fp.read()
        for error_pkg, error_msg_first_line in error_log_parser(error_log):
            reason_unknown = True
            if error_pkg in seen:
                print("Already seen '%s'" % error_pkg)
            seen.add(error_pkg)

            for reason_id, reason_desc in enumerate(known_reason_list):
                if reason_desc[1](error_msg_first_line):
                    reason_count[reason_id] += 1
                    problematic_pkg_set[reason_id].append(error_pkg)
                    reason_unknown = False
                    break

            if reason_unknown:
                print("Pkg: {} - {} ".format(error_pkg, error_msg_first_line))

    reason_result = sorted(
        reason_count.items(), key=lambda a: a[1], reverse=True
    )

    for reason_id, reason_freq in reason_result:
        print("%10d: %s" % (
            reason_freq, known_reason_list[reason_id][0]
        ))


if __name__ == '__main__':
    main()
