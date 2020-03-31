import shutil

from typing import Dict
from typing import List
from typing import Optional

from clikit.api.io.io import IO

from poetry.io.null_io import NullIO
from poetry.packages.dependency import Dependency
from poetry.packages.locker import Locker
from poetry.packages.project_package import ProjectPackage
from poetry.poetry import Poetry

from poetry.repositories.pypi_repository import PyPiRepository
from poetry.spdx import license_by_id
from poetry.utils._compat import Path
from poetry.utils.toml_file import TomlFile

from poetry.factory import Factory


class CustomPoetryFactory(Factory):
    POETRY_PROJECT_NAME = "dep-solver-root-c6c3d607-caa7-4570-8cc4-e0db973ea00c"
    POETRY_PROJECT_VERSION = "0.1.0"
    POETRY_PROJECT_DESC = "This is a virtual project just for hacking into the poetry's dependency solving engine"
    POETRY_PROJECT_AUTHORS = ["None <None@None.com>"]

    def create_poetry(
            self, cwd=None, io=None, do_pool_setup=True
    ):  # type: (Optional[Path], Optional[IO], bool) -> Poetry
        if io is None:
            io = NullIO()

        poetry_file = self.locate(cwd)

        # local_config = TomlFile(poetry_file.as_posix()).read()
        # if "tool" not in local_config or "poetry" not in local_config["tool"]:
        #     raise RuntimeError(
        #         "[tool.poetry] section not found in {}".format(poetry_file.name)
        #     )
        # local_config = local_config["tool"]["poetry"]

        # Checking validity
        # check_result = self.validate(local_config)
        # if check_result["errors"]:
        #     message = ""
        #     for error in check_result["errors"]:
        #         message += "  - {}\n".format(error)
        #
        #     raise RuntimeError("The Poetry configuration is invalid:\n" + message)

        # Load package
        name = CustomPoetryFactory.POETRY_PROJECT_NAME
        version = CustomPoetryFactory.POETRY_PROJECT_VERSION
        package = ProjectPackage(name, version, version)
        package.root_dir = poetry_file.parent

        for author in CustomPoetryFactory.POETRY_PROJECT_AUTHORS:
            package.authors.append(author)

        # for maintainer in local_config.get("maintainers", []):
        #     package.maintainers.append(maintainer)

        package.description = CustomPoetryFactory.POETRY_PROJECT_DESC
        # package.homepage = local_config.get("homepage")
        # package.repository_url = local_config.get("repository")
        # package.documentation_url = local_config.get("documentation")
        # try:
        #     license_ = license_by_id(local_config.get("license", ""))
        # except ValueError:
        #     license_ = None

        package.license = None
        package.keywords = []
        package.classifiers = []

        # if "readme" in local_config:
        #     package.readme = Path(poetry_file.parent) / local_config["readme"]
        #
        # if "platform" in local_config:
        #     package.platform = local_config["platform"]

        # if "dependencies" in local_config:
        for name, constraint in {"python": "^3.8"}.items():
            if name.lower() == "python":
                package.python_versions = constraint
                continue

            if isinstance(constraint, list):
                for _constraint in constraint:
                    package.add_dependency(name, _constraint)

                continue

            package.add_dependency(name, constraint)

        extras = {}  # local_config.get("extras", {})
        for extra_name, requirements in extras.items():
            package.extras[extra_name] = []

            # Checking for dependency
            for req in requirements:
                req = Dependency(req, "*")

                for dep in package.requires:
                    if dep.name == req.name:
                        dep.in_extras.append(extra_name)
                        package.extras[extra_name].append(dep)

                        break

        # if "build" in local_config:
        #     package.build = local_config["build"]
        #
        # if "include" in local_config:
        #     package.include = local_config["include"]
        #
        # if "exclude" in local_config:
        #     package.exclude = local_config["exclude"]
        #
        # if "packages" in local_config:
        #     package.packages = local_config["packages"]
        #
        # # Custom urls
        # if "urls" in local_config:
        #     package.custom_urls = local_config["urls"]

        # Moving lock if necessary (pyproject.lock -> poetry.lock)
        # lock = poetry_file.parent / "poetry.lock"
        # if not lock.exists():
        #     # Checking for pyproject.lock
        #     old_lock = poetry_file.with_suffix(".lock")
        #     if old_lock.exists():
        #         shutil.move(str(old_lock), str(lock))
        #
        # locker = Locker(poetry_file.parent / "poetry.lock", local_config)

        # Loading global configuration
        config = self.create_config(io)

        # Loading local configuration
        local_config_file = TomlFile(poetry_file.parent / "poetry.toml")
        if local_config_file.exists():
            if io.is_debug():
                io.write_line(
                    "Loading configuration file {}".format(local_config_file.path)
                )

            config.merge(local_config_file.read())

        poetry = Poetry(poetry_file, dict(), package, None, config)

        # if do_pool_setup:
        #     # Configuring sources
        #     for source in local_config.get("source", []):
        #         repository = self.create_legacy_repository(source, config)
        #         is_default = source.get("default", False)
        #         is_secondary = source.get("secondary", False)
        #         if io.is_debug():
        #             message = "Adding repository {} ({})".format(
        #                 repository.name, repository.url
        #             )
        #             if is_default:
        #                 message += " and setting it as the default one"
        #             elif is_secondary:
        #                 message += " and setting it as secondary"
        #
        #             io.write_line(message)
        #
        #         poetry.pool.add_repository(repository, is_default, secondary=is_secondary)
        #
        #     # Always put PyPI last to prefer private repositories
        #     # but only if we have no other default source
        #     if not poetry.pool.has_default():
        #         poetry.pool.add_repository(PyPiRepository(), True)
        #     else:
        #         if io.is_debug():
        #             io.write_line("Deactivating the PyPI repository")

        return poetry
