from functools import partial
from itertools import chain

from lib.RepoProxy import RemoteRepoProxy as ProxyRepo

from typing import (
    Iterable, List
)

from pip._internal.index.package_finder import BestCandidateResult
from pip._internal.req.req_set import RequirementSet
from pip._internal.req.req_install import InstallRequirement
from pip._internal.req.constructors import install_req_from_req_string

from pip._vendor.packaging.requirements import Requirement


class Dependency:
    def __init__(self, name, version, misc):
        self.name = name
        self.version = version
        self.misc = misc


class DependencyResolver:
    def __init__(self):
        self.repo_proxy = ProxyRepo()
        self.make_install_req = partial(
            install_req_from_req_string,
            isolated=None,
            wheel_cache=None,
            use_pep517=None,
        )

    def resolve(self, root_requirements):
        # type: (Iterable[str]) -> Iterable[BestCandidateResult]
        requirement_set = RequirementSet(check_supported_wheels=True)
        for req_str in root_requirements:
            requirement_set.add_requirement(
                self.make_install_req(req_string=req_str, comes_from=None)
            )

        root_reqs = (
                requirement_set.unnamed_requirements +
                list(requirement_set.requirements.values())
        )

        discovered_reqs = []  # type: List[InstallRequirement]

        for req in chain(root_reqs, discovered_reqs):
            discovered_reqs.extend(self._resolve_one(requirement_set, req))

        return []

    def resolve_one(self, req_set, req):
        # pkg_requirement = Requirement(requirement)
        #
        # root
        raise NotImplementedError("TODO")
