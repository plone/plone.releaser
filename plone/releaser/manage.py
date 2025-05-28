from argh import arg
from argh import ArghParser
from argh.decorators import named
from pathlib import Path
from plone.releaser import ACTION_BATCH
from plone.releaser import ACTION_INTERACTIVE
from plone.releaser import ACTION_REPORT
from plone.releaser import pypi
from plone.releaser import THIRD_PARTY_PACKAGES
from plone.releaser.buildout import Buildout
from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import SourcesFile
from plone.releaser.buildout import VersionsFile
from plone.releaser.package import Package
from plone.releaser.pip import ConstraintsFile
from plone.releaser.pip import MxCheckoutsFile
from progress.bar import Bar

import glob
import time


# TODO
buildout = Buildout()


def checkPypi(user):
    for package in buildout.sources:
        if package in THIRD_PARTY_PACKAGES:
            pass
        else:
            if not pypi.can_user_release_package_to_pypi(user, package):
                print(
                    "{}: {}".format(
                        package, ", ".join(pypi.get_users_with_release_rights(package))
                    )
                )


@named("jenkins")
def jenkins_report():
    """Read-only version of checkAllPackagesForUpdates."""
    sources = buildout.sources
    for package_name, source in iter(sources.items()):
        pkg = Package(buildout, package_name)
        pkg(action=ACTION_REPORT)


@arg("--interactive", default=False)
def checkPackageForUpdates(package_name, **kwargs):
    pkg = Package(buildout, package_name)
    if kwargs["interactive"]:
        pkg(action=ACTION_INTERACTIVE)
    else:
        pkg(action=ACTION_BATCH)


@named("report")
@arg("--interactive", default=False)
@arg("--sleep", default=20.0)
@arg("--start", default=0)
def checkAllPackagesForUpdates(**kwargs):
    """Check all packages for updates.

    For each package, we clone it with a depth of 100 to a temporary directory.

    GitHub often quits, probably because I do too many large requests.
    Sleeping should help, with the --sleep argument.

    If it fails anyway, you can restart the command and pass for example
    --start 50 to start at package 50 instead of the first one.
    """
    interactive = bool(kwargs["interactive"])
    sleep = float(kwargs["sleep"])
    start = int(kwargs["start"])
    sources = buildout.sources
    packages = sorted(list(sources.items()))
    if start > 0:
        packages = packages[start:]
    for package_name, source in Bar("Scanning").iter(packages):
        pkg = Package(buildout, package_name)
        if interactive:
            pkg(action=ACTION_INTERACTIVE)
        else:
            pkg(action=ACTION_REPORT)
        if sleep:
            time.sleep(sleep)


@named("changelog")
@arg("--start")
@arg("--end", default="here")
@arg("--package", default=None)
def changelog(**kwargs):
    """Build a unified changelog.

    For each package we get the changes between the start and end version,
    and unify them, so the changes of all intermediate versions get combined:
    all bug fixes together, all new features, etcetera.

    - 'start' is for example 6.0.7.
      This is used to get versions.cfg from dist.plone.org.
    - Same for 'end', where the default is 'here', meaning we take
      versions.cfg from the current directory.
    - With 'package' you can restrict to a single package.]
      This is mostly useful when debugging this command.
      You can separate packages with a comma:
      --package=plone.restapi,Products.CMFPlone

    We get the changes from the repository for this package,
    as defined in sources.cfg, and try a few locations, for example:
    https://raw.githubusercontent.com/plone/plone.restapi/main/CHANGES.rst

    Sample output in a problematic case:

        $ bin/manage changelog --start=6.0.7 --end=6.0.8 --package=plone.restapi
        Parsed https://dist.plone.org/release/6.0.7/versions.cfg
        Parsed https://dist.plone.org/release/6.0.8/versions.cfg
        plone.restapi has a newer version
        ERROR: Start version 8.43.3 not found in changelog contents.

        plone.restapi: 8.43.3 → 9.1.2
        -----------------------------

    The problem here is we get the CHANGES.rst file from the main plone.restapi branch,
    and this does not include a header for version 8.43.3: this header is only on the
    8.x branch.
    When we run the same command with `--start=6.0.6`, it does work, and you get the
    unified changes between version 8.40.0 and 9.1.2.
    """
    from plone.releaser.changelog import build_unified_changelog

    build_unified_changelog(kwargs["start"], kwargs["end"], packages=kwargs["package"])


def _get_checkouts(path=None):
    """Get the parsed checkouts file at the given path.

    If no path is given, we use several paths:
    both checkouts.cfg and mxcheckouts.ini.
    """
    if path:
        paths = [path]
    else:
        paths = glob.glob("mxcheckouts.ini") + glob.glob("checkouts.cfg")
    for path in paths:
        if path.endswith(".ini"):
            checkouts = MxCheckoutsFile(path)
        else:
            checkouts = CheckoutsFile(path)
        yield checkouts


def check_checkout(package_name, *, path=None):
    """Check if package is in the checkouts.

    If no path is given, we try several paths:
    both checkouts.cfg and mxcheckouts.ini.
    """
    for checkouts in _get_checkouts(path=path):
        loc = checkouts.file_location
        if package_name not in checkouts:
            print(f"No, your package {package_name} is NOT on auto checkout in {loc}.")
        else:
            print(f"YES, your package {package_name} is on auto checkout in {loc}.")


def remove_checkout(package_name, *, path=None):
    """Remove package from auto checkouts.

    If no path is given, we try several paths:
    both checkouts.cfg and mxcheckouts.ini.
    """
    for checkouts in _get_checkouts(path=path):
        checkouts.remove(package_name)


def add_checkout(package_name, *, path=None):
    """Add package to auto checkouts.

    If no path is given, we try several paths:
    both checkouts.cfg and mxcheckouts.ini.
    """
    for checkouts in _get_checkouts(path=path):
        checkouts.add(package_name)


def append_jenkins_build_number_to_package_version(jenkins_build_number):
    from zest.releaser.utils import cleanup_version
    from zest.releaser.vcs import BaseVersionControl

    vcs = BaseVersionControl()
    old_version = cleanup_version(vcs.version)
    new_version = f"{old_version}.{jenkins_build_number}"
    vcs.version = new_version
    return new_version


def _get_constraints(path=None):
    """Get the parsed constraints/versions file at the given path.

    If no path is given, we use several paths:
    constraints*.txt and versions*.cfg.
    """
    if path:
        paths = [path]
    else:
        paths = glob.glob("constraints*.txt") + glob.glob("versions*.cfg")
    for path in paths:
        if path.endswith(".txt"):
            constraints = ConstraintsFile(path)
        else:
            constraints = VersionsFile(path)
        yield constraints


def get_package_version(package_name, *, path=None):
    """Get package version from constraints/versions file.

    If no path is given, we try several paths.

    Note that versions with environment markers are ignored.
    See https://peps.python.org/pep-0496/ explaining them.
    The 99.99 percent use case of this part of plone.releaser is to get or set
    versions for a Plone package, and after abandoning Python 2 we are unlikely
    to need different versions of our core packages for different environments.

    So in all the following cases, package version 1.0 is reported:

    package==1.0
    package==2.0; python_version=="3.11"

    [versions]
    package = 1.0
    [versions:python311]
    package = 2.0
    [versions:python_version=="3.12"]
    package = 3.0
    """
    for constraints in _get_constraints(path=path):
        if package_name not in constraints:
            print(f"{constraints.file_location}: {package_name} missing.")
            continue
        version = constraints.get(package_name)
        print(f"{constraints.file_location}: {package_name} {version}.")


def set_package_version(package_name, new_version, *, path=None):
    """Pin package to new version in a versions file.

    This can also be a pip constraints file.
    If the package is not pinned yet, we add it.

    If no path is given, we try several paths and set the version in all of them,
    but only if the package is already there: we do not want to add one package
    in three versions*.cfg files.

    If you want to add environment markers, like "python_version >= '3.0'",
    please just edit the files yourself.
    """
    for constraints in _get_constraints(path=path):
        if package_name not in constraints:
            if path is None:
                print(f"{constraints.file_location}: {package_name} missing.")
                continue
            print(
                f"{constraints.file_location}: {package_name} not pinned yet. "
                f"Adding pin because you explicitly gave the path."
            )
        constraints.set(package_name, new_version)


def _get_paths(path, patterns):
    paths = []
    if path:
        if not isinstance(path, Path):
            path = Path(path)
        if path.is_dir():
            for pat in patterns:
                paths.extend(glob.glob(str(path / pat)))
        else:
            paths = [path]
    else:
        for pat in patterns:
            paths.extend(glob.glob(pat))
    all_paths = []
    for path in paths:
        if not isinstance(path, Path):
            path = Path(path)
        all_paths.append(path)
    return all_paths


def versions2constraints(*, path=None):
    """Take a Buildout versions file and create a pip constraints file out of it.

    If a path is given, we handle only that file.
    If no path is given, we use versions*.cfg.
    """
    paths = _get_paths(path, ["versions*.cfg"])
    for path in paths:
        versions = VersionsFile(path, with_markers=True)
        # Create path to constraints*.txt instead of versions*.cfg.
        filepath = versions.path
        filename = str(filepath)[len(str(filepath.parent)) + 1 :]
        filename = filename.replace("versions", "constraints").replace(".cfg", ".txt")
        constraints_path = filepath.parent / filename
        versions.to_pip(constraints_path)


def constraints2versions(*, path=None):
    """Take a pip constraints file and create a Buildout versions file out of it.

    If a path is given, we handle only that file.
    If no path is given, we use constraints*.txt.
    """
    paths = _get_paths(path, ["constraints*.txt"])
    for path in paths:
        constraints = ConstraintsFile(path, with_markers=True)
        # Create path to versions*.cfg instead of constraints*.txt.
        filepath = constraints.path
        filename = str(filepath)[len(str(filepath.parent)) + 1 :]
        filename = filename.replace("constraints", "versions").replace(".txt", ".cfg")
        versions_path = filepath.parent / filename
        constraints.to_buildout(versions_path)


def buildout2pip(*, path=None):
    """Take a Buildout file and create a pip/mxdev file out of it.

    If a path is given, we handle only that file, guessing whether it is a file
    with versions or sources or checkouts.
    If no path is given, we use versions*.cfg, sources*.cfg and checkouts*.cfg.
    """
    paths = _get_paths(path, ["versions*.cfg", "sources*.cfg", "checkouts*.cfg"])
    for path in paths:
        if path.name.startswith("versions"):
            buildout_file = VersionsFile(path, with_markers=True)
        elif path.name.startswith("sources"):
            buildout_file = SourcesFile(path)
        elif path.name.startswith("checkouts"):
            buildout_file = CheckoutsFile(path)
        # Create path to constraints*.txt instead of versions*.cfg, etc.
        filepath = buildout_file.path
        filename = str(filepath)[len(str(filepath.parent)) + 1 :]
        filename = filename.replace("versions", "constraints")
        if "checkouts" in filename or "sources" in filename:
            filename = (
                filename.replace("checkouts", "mxcheckouts")
                .replace("sources", "mxsources")
                .replace(".cfg", ".ini")
            )
        else:
            filename = filename.replace(".cfg", ".txt")
        pip_path = filepath.parent / filename
        if not pip_path.exists():
            pip_path.write_text("")
        buildout_file.to_pip(pip_path)


class Manage:
    def __call__(self, **kwargs):
        parser = ArghParser()
        parser.add_commands(
            [
                checkPypi,
                checkPackageForUpdates,
                checkAllPackagesForUpdates,
                changelog,
                check_checkout,
                remove_checkout,
                add_checkout,
                append_jenkins_build_number_to_package_version,
                set_package_version,
                get_package_version,
                jenkins_report,
                constraints2versions,
                versions2constraints,
                buildout2pip,
            ]
        )
        parser.dispatch()


manage = Manage()
