from typing import (
    FrozenSet, Iterable, List, Optional, Set, Text, Tuple, Union, Any, Dict
)

from pip._internal.index.package_finder import CandidateEvaluator, BestCandidateResult, LinkEvaluator
from pip._internal.models.candidate import InstallationCandidate
from pip._internal.models.link import Link
from pip._internal.models.target_python import TargetPython
from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.utils import canonicalize_name


class ConstraintResolver:
    ACCEPT_PKG_FORMAT = frozenset({'binary', 'source'})

    def __init__(self):
        self._target_python = TargetPython()
        self._allow_yanked = False
        self._ignore_requires_python = False
        self._allow_all_prereleases = False
        self._prefer_binary = False

    def _make_link_evaluator(self, pkg_name):
        return LinkEvaluator(
            project_name=pkg_name,
            canonical_name=canonicalize_name(pkg_name),
            formats=ConstraintResolver.ACCEPT_PKG_FORMAT,
            target_python=self._target_python,
            allow_yanked=self._allow_yanked,
            ignore_requires_python=self._ignore_requires_python,
        )

    def pick_pkg_candidates_from_file_list(self, pkg_name, pkg_file_list):
        # type: (str, Iterable[Dict[str:Any]]) -> Iterable[InstallationCandidate]
        pkg_files = pkg_file_list
        link_evaluator = self._make_link_evaluator(pkg_name)
        platform_compatible_package = filter(
            lambda p: link_evaluator.evaluate_link(Link(p['url']))[0], pkg_files
        )
        return map(lambda p: InstallationCandidate(pkg_name, p['ver'], Link(p['url'])), platform_compatible_package)

    def resolve_best_candidate(self, requirement, candidates):
        # type: (str, Iterable[InstallationCandidate]) -> BestCandidateResult
        pkg_ver_req = Requirement(requirement)

        candidate_evaluator = CandidateEvaluator.create(
            project_name=pkg_ver_req.name,
            target_python=self._target_python,
            prefer_binary=self._prefer_binary,
            allow_all_prereleases=self._allow_all_prereleases,
            specifier=pkg_ver_req.specifier,
            hashes=None
        )  # type: CandidateEvaluator
        best_candidates = candidate_evaluator.compute_best_candidate(list(candidates))
        return best_candidates
