from argh import arg
from argh import ArghParser
from argh.decorators import named
from github import Github
from plone.releaser import ACTION_BATCH
from plone.releaser import ACTION_INTERACTIVE
from plone.releaser import ACTION_REPORT
from plone.releaser import pypi
from plone.releaser import THIRD_PARTY_PACKAGES
from plone.releaser.buildout import Buildout
from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import VersionsFile
from plone.releaser.package import Package
from plone.releaser.pip import ConstraintsFile
from plone.releaser.pip import IniFile
from progress.bar import Bar

import glob
import keyring
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


def pulls():
    client_id = "b9f6639835b8c9cf462a"
    client_secret = keyring.get_password("plone.releaser", client_id)

    g = Github(client_id=client_id, client_secret=client_secret)

    for package_name, source in buildout.sources.items():
        if source.path:
            repo = g.get_repo(source.path)
            pulls = [a for a in repo.get_pulls("open") if a.head.ref == source.branch]
            if pulls:
                print(package_name)
                for pull in pulls:
                    print(f"    {pull.user.login}: {pull.title} ({pull.url})")


@named("changelog")
@arg("--start")
@arg("--end", default="here")
def changelog(**kwargs):
    from plone.releaser.changelog import build_unified_changelog

    build_unified_changelog(kwargs["start"], kwargs["end"])


def _get_checkouts(path=None):
    """Get the parsed checkouts file at the given path.

    If no path is given, we use several paths:
    both checkouts.cfg and mxdev.ini.
    """
    if path:
        paths = [path]
    else:
        paths = glob.glob("mxdev.ini") + glob.glob("checkouts.cfg")
    for path in paths:
        if path.endswith(".ini"):
            checkouts = IniFile(path)
        else:
            checkouts = CheckoutsFile(path)
        yield checkouts


def check_checkout(package_name, path=None):
    """Check if package is in the checkouts.

    If no path is given, we try several paths:
    both checkouts.cfg and mxdev.ini.
    """
    for checkouts in _get_checkouts(path=path):
        loc = checkouts.file_location
        if package_name not in checkouts:
            print(f"No, your package {package_name} is NOT on auto checkout in {loc}.")
        else:
            print(f"YES, your package {package_name} is on auto checkout in {loc}.")


def remove_checkout(package_name, path=None):
    """Remove package from auto checkouts.

    If no path is given, we try several paths:
    both checkouts.cfg and mxdev.ini.
    """
    for checkouts in _get_checkouts(path=path):
        checkouts.remove(package_name)


def add_checkout(package_name, path=None):
    """Add package to auto checkouts.

    If no path is given, we try several paths:
    both checkouts.cfg and mxdev.ini.
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


def get_package_version(package_name, path=None):
    """Get package version fron constraints/versions file.

    If no path is given, we try several paths.
    """
    for constraints in _get_constraints(path=None):
        if package_name not in constraints:
            print(f"{constraints.file_location}: {package_name} missing.")
            continue
        version = constraints.get(package_name)
        print(f"{constraints.file_location}: {package_name} {version}.")


def set_package_version(package_name, new_version, path=None):
    """Pin package to new version in a versions file.

    This can also be a pip constraints file.
    If the package is not pinned yet, we add it.

    If no path is given, we try several paths and set the version in all of them,
    bu only if the package is already there: we do not want to add one package
    in three versions*.cfg files.

    If you want it really fancy you can also add identifiers,
    but that only gives valid results for pip files:

    bin/manage set-package-version setuptools "65.7.0; python_version >= '3.0'" --path requirements.txt
    """
    for constraints in _get_constraints(path=None):
        if package_name not in constraints:
            if path is None:
                print(f"{constraints.file_location}: {package_name} missing.")
                continue
            print(
                f"{constraints.file_location}: {package_name} not pinned yet. "
                f"Adding pin because you explicitly gave the path."
            )
        constraints.set(package_name, new_version)


class Manage:
    def __call__(self, **kwargs):
        parser = ArghParser()
        parser.add_commands(
            [
                checkPypi,
                checkPackageForUpdates,
                checkAllPackagesForUpdates,
                pulls,
                changelog,
                check_checkout,
                remove_checkout,
                add_checkout,
                append_jenkins_build_number_to_package_version,
                set_package_version,
                get_package_version,
                jenkins_report,
            ]
        )
        parser.dispatch()


manage = Manage()
