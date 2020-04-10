import os
from collections import defaultdict
from typing import (
    FrozenSet, Iterable, List, Optional, Set, Text, Tuple, Union, Any, Dict
)

import poetry.packages

from poetry.locations import CACHE_DIR
from poetry.packages import Package
from poetry.packages import dependency_from_pep_508
from poetry.packages.utils.link import Link
from poetry.repositories.exceptions import PackageNotFound
from poetry.repositories.legacy_repository import LegacyRepository
from poetry.semver import Version
from poetry.semver import VersionConstraint
from poetry.semver import VersionRange
from poetry.semver import parse_constraint
from poetry.utils._compat import Path
from poetry.utils.helpers import canonicalize_name
from poetry.utils.inspector import Inspector
from poetry.utils.patterns import wheel_file_re
from poetry.version.markers import InvalidMarker, parse_marker
from lib.RepoProxy import LocalMirrorRepoProxy


class HybirdRepository(LegacyRepository):
    class PipLinkEvaluator:
        from pip._internal.index.package_finder import LinkEvaluator
        from pip._internal.models.link import Link
        from pip._internal.models.target_python import TargetPython
        from pip._vendor.packaging.utils import canonicalize_name

        def __init__(self):
            self._target_python = HybirdRepository.PipLinkEvaluator.TargetPython()
            self._allow_yanked = False
            self._ignore_requires_python = False
            self._accept_pkg_format = frozenset({'binary'})

        def _make_link_evaluator(self, pkg_name):
            return HybirdRepository.PipLinkEvaluator.LinkEvaluator(
                project_name=pkg_name,
                canonical_name=HybirdRepository.PipLinkEvaluator.canonicalize_name(pkg_name),
                formats=self._accept_pkg_format,
                target_python=self._target_python,
                allow_yanked=self._allow_yanked,
                ignore_requires_python=self._ignore_requires_python,
            )

        def evaluate_binary_pkg(self, pkg_name, urls_list):
            link_evaluator = self._make_link_evaluator(pkg_name)
            ret_val = list(filter(
                lambda url: link_evaluator.evaluate_link(HybirdRepository.PipLinkEvaluator.Link(url))[0], urls_list
            ))
            return ret_val

    def __init__(self, name, url, local_mirror_path, auth=None, disable_cache=False, cert=None, client_cert=None):
        super().__init__(name, url, auth, disable_cache, cert, client_cert)
        self.local_mirror_proxy = LocalMirrorRepoProxy(local_mirror_path)
        self.pip_link_evaluator = HybirdRepository.PipLinkEvaluator()

    def _find_packages_from_local_mirror(
            self, name, constraint=None, extras=None, allow_prereleases=False
    ):
        # type: (...) -> List[Package]
        packages = []

        if constraint is None:
            constraint = "*"

        if not isinstance(constraint, VersionConstraint):
            constraint = parse_constraint(constraint)

        if isinstance(constraint, VersionRange):
            if (
                    constraint.max is not None
                    and constraint.max.is_prerelease()
                    or constraint.min is not None
                    and constraint.min.is_prerelease()
            ):
                allow_prereleases = True

        canonical_name = canonicalize_name(name).replace(".", "-")
        meta_json_local_file_url = "file://{}".format(os.path.join(
            self.local_mirror_proxy.path_local_mirror,
            'json', canonical_name
        ))
        file_list_from_meta_json = self.local_mirror_proxy.get_pkg_file_list(canonical_name)

        if file_list_from_meta_json:
            versions = []

            ver_seen = set()
            for file_info in file_list_from_meta_json:
                try:
                    version = Version.parse(file_info['ver'])
                except ValueError:
                    version = None

                if not version:
                    continue

                if version in ver_seen:
                    continue

                ver_seen.add(version)

                if version.is_prerelease() and not allow_prereleases:
                    continue

                if constraint.allows(version):
                    versions.append(version)

            for version in versions:
                package = Package(name, version)

                package.source_url = meta_json_local_file_url

                if extras is not None:
                    package.requires_extras = extras

                packages.append(package)

            self._log(
                "{} packages found in local mirror for {} {}".format(len(packages), name, str(constraint)),
                level="debug",
            )

        return packages

    # Patched, will look up local mirror first
    def find_packages(  # patched version that will look into the json metadat in local mirror first
            self, name, constraint=None, extras=None, allow_prereleases=False
    ):
        packages = self._find_packages_from_local_mirror(name, constraint, extras, allow_prereleases)

        if packages:
            return packages
        else:
            return super().find_packages(name, constraint, extras, allow_prereleases)

    def _get_release_info_from_local_mirror(self, name, version):
        # type: (str, str) -> Optional[dict]
        canonical_name = canonicalize_name(name).replace(".", "-")
        meta_json_local_file_url = "file://{}".format(os.path.join(
            self.local_mirror_proxy.path_local_mirror,
            'json', canonical_name
        ))
        file_list_from_meta_json = self.local_mirror_proxy.get_pkg_file_list(canonical_name)
        # page = self._get("/{}/".format(canonicalize_name(name).replace(".", "-")))
        if len(file_list_from_meta_json) == 0:
            return None

        data = {
            "name": name,
            "version": version,
            "summary": "",
            "requires_dist": [],
            "requires_python": None,
            "files": [],
            "_cache_version": str(self.CACHE_VERSION),
        }

        def find_links_for_version(_file_list, _version):
            for _f_info in _file_list:
                if Version.parse(_f_info['ver']) == Version.parse(version):
                    yield Link(_f_info['url'], meta_json_local_file_url, _f_info['requires_python'])

        links = list(find_links_for_version(file_list_from_meta_json, version))
        if not links:
            return None

        urls = defaultdict(list)
        files = []
        for link in links:
            if link.is_wheel:
                urls["bdist_wheel"].append(link.url)
            elif link.filename.endswith(
                    (".tar.gz", ".zip", ".bz2", ".xz", ".Z", ".tar")
            ):
                urls["sdist"].append(link.url)

            h = link.hash
            if h:
                h = link.hash_name + ":" + link.hash
                files.append({"file": link.filename, "hash": h})

        data["files"] = files

        info = self._get_info_from_urls_patched(urls, name)

        data["summary"] = info["summary"]
        data["requires_dist"] = info["requires_dist"]
        data["requires_python"] = info["requires_python"]

        return data

    def _get_info_from_urls_patched(
            self, urls, name
    ):  # type: (Dict[str, List[str]], str) -> Dict[str, Union[str, List, None]]
        # Checking wheels first as they are more likely to hold
        # the necessary information
        if "bdist_wheel" in urls:
            # Check fo a universal wheel
            wheels = urls["bdist_wheel"]

            universal_wheel = None
            universal_python2_wheel = None
            universal_python3_wheel = None
            platform_specific_wheels = []
            pip_evaluated_wheels = self.pip_link_evaluator.evaluate_binary_pkg(name, urls["bdist_wheel"])
            for wheel in wheels:
                link = Link(wheel)
                m = wheel_file_re.match(link.filename)
                if not m:
                    continue

                pyver = m.group("pyver")
                abi = m.group("abi")
                plat = m.group("plat")
                if abi == "none" and plat == "any":
                    # Universal wheel
                    if pyver == "py2.py3":
                        # Any Python
                        universal_wheel = wheel
                    elif pyver == "py2":
                        universal_python2_wheel = wheel
                    else:
                        universal_python3_wheel = wheel
                else:
                    platform_specific_wheels.append(wheel)

            if universal_wheel is not None:
                return self._get_info_from_wheel(universal_wheel)

            info = {}
            if universal_python2_wheel and universal_python3_wheel:
                info = self._get_info_from_wheel(universal_python2_wheel)

                py3_info = self._get_info_from_wheel(universal_python3_wheel)
                if py3_info["requires_dist"]:
                    if not info["requires_dist"]:
                        info["requires_dist"] = py3_info["requires_dist"]

                        return info

                    py2_requires_dist = set(
                        dependency_from_pep_508(r).to_pep_508()
                        for r in info["requires_dist"]
                    )
                    py3_requires_dist = set(
                        dependency_from_pep_508(r).to_pep_508()
                        for r in py3_info["requires_dist"]
                    )
                    base_requires_dist = py2_requires_dist & py3_requires_dist
                    py2_only_requires_dist = py2_requires_dist - py3_requires_dist
                    py3_only_requires_dist = py3_requires_dist - py2_requires_dist

                    # Normalizing requires_dist
                    requires_dist = list(base_requires_dist)
                    for requirement in py2_only_requires_dist:
                        dep = dependency_from_pep_508(requirement)
                        dep.marker = dep.marker.intersect(
                            parse_marker("python_version == '2.7'")
                        )
                        requires_dist.append(dep.to_pep_508())

                    for requirement in py3_only_requires_dist:
                        dep = dependency_from_pep_508(requirement)
                        dep.marker = dep.marker.intersect(
                            parse_marker("python_version >= '3'")
                        )
                        requires_dist.append(dep.to_pep_508())

                    info["requires_dist"] = sorted(list(set(requires_dist)))

            if info:
                return info

            # Prefer non platform specific wheels
            if universal_python3_wheel:
                return self._get_info_from_wheel(universal_python3_wheel)

            if universal_python2_wheel:
                return self._get_info_from_wheel(universal_python2_wheel)

            if pip_evaluated_wheels:
                return self._get_info_from_wheel(pip_evaluated_wheels[0])

            if platform_specific_wheels and "sdist" not in urls:
                # Pick the first wheel available and hope for the best
                return self._get_info_from_wheel(platform_specific_wheels[0])

        return self._get_info_from_sdist(urls["sdist"][0])

    # PATCHED, will check local mirror first, won't cache the information got from local mirror
    def get_release_info(self, name, version):
        # type: (str, str) -> dict
        """
        Return the release information given a package name and a version.

        The information is returned from the cache if it exists
        or retrieved from the remote server.
        """

        info_from_local_mirror = self._get_release_info_from_local_mirror(name, version)
        if info_from_local_mirror:
            return info_from_local_mirror
        else:
            return super().get_release_info(name, version)

    # PATCHED, will to check local mirror first
    def _download(self, url, dest):  # type: (str, str) -> None
        local_mirror_path = self.local_mirror_proxy.request_pkg_file(url)
        if local_mirror_path:
            # if found in the local repo, create a symlink instead of copying
            os.symlink(local_mirror_path, dest)
            self._log("Created symlink {} -> {}".format(local_mirror_path, dest), level="debug")
        else:
            r = self._session.get(url, stream=True)
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
