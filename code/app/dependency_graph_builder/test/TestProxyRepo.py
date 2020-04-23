from typing import (
    FrozenSet, Iterable, List, Optional, Set, Text, Tuple, Union, Any, Dict
)

import random
import unittest

from lib.RepoProxy import RemoteRepoProxy, LocalMirrorRepoProxy


class MyTestCase(unittest.TestCase):
    LOCAL_MIRROR_PATH = '/mnt/MyPassportExt4/PyPI_Mirror/pypi/web'
    REMOTE_REPO_ENDPOINT = "https://pypi.org/simple"

    # def __init__(self):
    #     super().__init__()
    #

    def test_remote_proxy(self):
        self.number_random_pkg = 10
        self.number_url_per_pkg = 2
        remote_proxy = RemoteRepoProxy(MyTestCase.REMOTE_REPO_ENDPOINT)

        # get available package list

        seen_pkg_set = set()
        for pkg_name in remote_proxy.available_packages():
            self.assertIsInstance(pkg_name, str, "package name should be an instance of str")
            self.assertGreater(len(pkg_name), 0, "package name should be an empty string")
            self.assertTrue(pkg_name not in seen_pkg_set, "package name should be unique")

            seen_pkg_set.add(pkg_name)

        # get file list for some package

        pkg_to_fetch = {'requests', 'scapy'}.union(set(random.sample(seen_pkg_set, self.number_random_pkg)))
        pkg_info_key = {'ver',
                        'url',
                        'upload_time',
                        'digest',
                        'pkg_type'}
        pkg_url_list = []

        for random_pkg in pkg_to_fetch:
            pkg_files_list = remote_proxy.get_pkg_file_list(random_pkg)
            # self.assertIsInstance(pkg_files_list, Iterable[Dict])
            pkg_files_list = list(pkg_files_list)
            n_avail_pkg = len(pkg_files_list)

            for p in pkg_files_list:  # type: dict
                for k in pkg_info_key:
                    self.assertIn(k, p.keys(), "the file list entry must has key {}".format(k))
                    self.assertTrue(p['ver'] is not None)
                    self.assertTrue(p['url'] is not None)

            pkg_url_list.extend(
                map(
                    lambda pj: pj['url'],
                    random.sample(
                        pkg_files_list,
                        self.number_url_per_pkg if self.number_url_per_pkg < n_avail_pkg else n_avail_pkg
                    )
                )
            )

        self.assertGreaterEqual(len(pkg_url_list), 4)
        for url in pkg_url_list:
            local_path = remote_proxy.request_pkg_file(url)
            self.assertTrue(local_path.find(local_path) == 0)


if __name__ == '__main__':
    unittest.main()
