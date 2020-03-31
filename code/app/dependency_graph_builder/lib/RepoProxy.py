import re
from typing import (
    FrozenSet, Iterable, List, Optional, Set, Text, Tuple, Union, Any, Dict
)

import os
import json
import urllib.parse
import uuid
import shutil

from lib.Utils import download_file


class RepoProxy:
    def available_packages(self):
        # type: () -> List[str]
        """
        :return: a iterator that enumerates the name of all available packages served by this repository
        """
        raise NotImplementedError

    def get_pkg_file_list(self, pkg_name):
        # type: (str) -> List[Dict[str:Any]]
        """
        :param pkg_name: The name of package

        :return: a list of available package
        """
        raise NotImplementedError

    def request_pkg_file(self, url):
        # type (str) -> Optional[str]
        """
        :param url: a package's pypi.org download link

        :return: FS path to the fetched package, the package file should considered as readonly

        .. note:: implementation should consider using local cache
        """
        raise NotImplementedError


def get_package_path_from_url(url):
    parsed_url = urllib.parse.urlparse(url)
    pkg_path = parsed_url.path
    if pkg_path[0] == '/':
        pkg_path = pkg_path[1:]
    return pkg_path


class RemoteRepoProxy(RepoProxy):
    DEFAULT_REMOTE_REPO_ENDPOINT = "https://pypi.org/simple"

    def __init__(self, remote_endpoint=DEFAULT_REMOTE_REPO_ENDPOINT, local_cache_dir=None):
        # type: (str, Optional[str]) -> None
        from pypi_simple import PyPISimple
        self.repo_client = PyPISimple(endpoint=remote_endpoint)  # type:PyPISimple
        if local_cache_dir:
            self.cache_dir = local_cache_dir
        else:
            self.cache_dir = os.path.join('.', 'pkg_cache')

    def available_packages(self):
        return self.repo_client.get_projects()

    def get_pkg_file_list(self, pkg_name):
        pkg_files = self.repo_client.get_project_files(pkg_name)
        return map(
            lambda p: {
                'ver': p.version,
                'url': p.url,
                'upload_time': None,
                'digest': None,
                'pkg_type': p.package_type,
                'requires_python': p.requires_python
            },
            pkg_files
        )

    @staticmethod
    def _download_pkg(url, save_to):
        def do_down(down_url, write_to):
            # NOTE the stream=True parameter below
            try:
                download_file(down_url, filename=write_to)
            except BaseException:
                if os.path.exists(write_to):
                    os.remove(write_to)
                raise

        target_dir = os.path.dirname(save_to)

        tmp_file_name = save_to + ".{}.tmp".format(uuid.uuid4())
        assert (not os.path.exists(target_dir)) or (os.path.isdir(target_dir))
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        do_down(url, tmp_file_name)
        shutil.move(tmp_file_name, save_to)

    def request_pkg_file(self, url):
        pkg_path = get_package_path_from_url(url)
        local_path = os.path.join(self.cache_dir, pkg_path)

        if not os.path.isfile(local_path):
            self._download_pkg(url, local_path)

        return local_path


_canonicalize_regex = re.compile("[-_]+")


def canonicalize_name(name):  # type: (str) -> str
    return _canonicalize_regex.sub("-", name).lower().replace('.', '-')


class LocalMirrorRepoProxy(RepoProxy):
    # REMOTE_PKG_FETCH_CACHE_DIR = '../pkg_cache'
    DEFAULT_LOCAL_MIRROR = '/mnt/MyPassportExt4/PyPI_Mirror/pypi/web'

    def __init__(self, path_local_mirror=DEFAULT_LOCAL_MIRROR):
        # type: (str) -> None
        self.path_local_mirror = path_local_mirror
        avail_pkg_list = self.available_packages()
        pkg_canonical_name_to_path_name_tbl = dict()
        for pkg_name in avail_pkg_list:
            pkg_canonical_name_to_path_name_tbl[canonicalize_name(pkg_name)] = pkg_name
        self.pkg_name_case_insensitive_table = pkg_canonical_name_to_path_name_tbl

    def available_packages(self):
        pkg_list = sorted(
            os.listdir(
                os.path.join(
                    self.path_local_mirror,
                    'json'
                )
            )
        )
        return pkg_list

    def find_pkg_name_case_insensitive(self, pkg_name_case_insensitive):
        return self.pkg_name_case_insensitive_table.get(pkg_name_case_insensitive, None)

    def get_pkg_file_list(self, pkg_name):
        pkg_name_case_sensitive = self.find_pkg_name_case_insensitive(pkg_name)

        path_project_meta = os.path.join(
            self.path_local_mirror,
            'json', pkg_name_case_sensitive
        )

        files_list = []

        if not pkg_name_case_sensitive:
            return files_list

        try:
            with open(path_project_meta, 'r', encoding='utf-8') as fp_json_meta:
                pkg_meta = json.load(fp_json_meta)  # type: Dict[str, Any]
                release_info = pkg_meta.get('releases', {})
                for release_ver, release_detail_list in release_info.items():
                    for release_detail in release_detail_list:
                        release_url = release_detail.get('url', None)
                        release_upload_time = release_detail.get('upload_time', None)
                        release_digest = release_detail.get('digests', None)
                        release_pkg_type = release_detail.get('packagetype', None)
                        release_requires_python = release_detail.get('requires_python', None)
                        if release_url:
                            files_list.append({
                                'ver': release_ver,
                                'url': release_url,
                                'upload_time': release_upload_time,
                                'digest': release_digest,
                                'pkg_type': release_pkg_type,
                                'requires_python': release_requires_python
                            })
        except FileNotFoundError:
            pass

        return files_list

    def request_pkg_file(self, url):
        pkg_path = get_package_path_from_url(url)
        local_path = os.path.join(self.path_local_mirror, pkg_path)

        return local_path if os.path.isfile(local_path) else None


def demo():
    LOCAL_MIRROR_PATH = '/mnt/MyPassportExt4/PyPI_Mirror/pypi/web'
    REMOTE_REPO_ENDPOINT = "https://pypi.org/simple"
    local_mirror_proxy = LocalMirrorRepoProxy(LOCAL_MIRROR_PATH)
    remote_repo_proxy = RemoteRepoProxy(REMOTE_REPO_ENDPOINT)
    print(list(remote_repo_proxy.get_pkg_file_list("ahaha")))

    def down_all_file_for_pkg(pname):
        pkg_file_list = remote_repo_proxy.get_pkg_file_list(pname)
        for p in pkg_file_list:
            downloaded_file_loc = remote_repo_proxy.request_pkg_file(p['url'])
            print("Downloaded {}".format(downloaded_file_loc))

    for pkg_name in local_mirror_proxy.available_packages():
        print(pkg_name)
        down_all_file_for_pkg(pkg_name)

    down_all_file_for_pkg("tf-nightly-gpu")


if __name__ == '__main__':
    demo()
