from copy import copy
from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import SourcesFile
from plone.releaser.buildout import VersionsFile
from plone.releaser.pip import ConstraintsFile
from plone.releaser.pip import MxCheckoutsFile
from plone.releaser.pypi import can_user_release_package_to_pypi
from zest.releaser import pypi
from zest.releaser.utils import ask
from zest.releaser.utils import read_text_file
from zest.releaser.utils import write_text_file

import git
import glob
import os
import pathlib
import sys
import textwrap


# Define texts to check for during prereleaser or add during postrelease.
NOTHING_CHANGED_YET = "*add item here*"
BREAKING_TEXT = """
Breaking changes:

- {}
""".format(
    NOTHING_CHANGED_YET
)
FEATURE_TEXT = """
New features:

- {}
""".format(
    NOTHING_CHANGED_YET
)
BUGFIXES_TEXT = """
Bug fixes:

- {}
""".format(
    NOTHING_CHANGED_YET
)
HEADERS = [BREAKING_TEXT, FEATURE_TEXT, BUGFIXES_TEXT]
# Used by changelog.py:
HEADINGS = [
    "Breaking changes:",
    "New features:",
    "Bug fixes:",
    "Documentation:",
    "Tests",
    "Internal:",
]
# For compatibility with previous names of the headers.
INCOMPATIBILITIES_TEXT = """
Incompatibilities:

- {}
""".format(
    NOTHING_CHANGED_YET
)
NEW_TEXT = """
New:

- {}
""".format(
    NOTHING_CHANGED_YET
)
FIXES_TEXT = """
Fixes:

- {}
""".format(
    NOTHING_CHANGED_YET
)
OLD_HEADERS = [INCOMPATIBILITIES_TEXT, NEW_TEXT, FIXES_TEXT]
ALL_HEADERS = copy(HEADERS)
ALL_HEADERS.extend(OLD_HEADERS)
OLD_HEADING_MAPPING = {
    "Incompatibilities:": "Breaking changes:",
    "New:": "New features:",
    "Fixes:": "Bug fixes:",
}
KNOWN_HEADINGS = copy(HEADINGS)
KNOWN_HEADINGS.extend(list(OLD_HEADING_MAPPING.keys()))


ALWAYS_CHECKED_OUT_PACKAGES = (
    "Plone",
    "Products.CMFPlone",
    "plone.app.upgrade",
    "plone.app.locales",
)


def set_nothing_changed_yet(data):
    """Set line that we look for in prerelease.

    This is when checking if a changelog entry has been added since last
    release.

    Note that currently this must be a single line, because
    zest.releaser looks for this text in each line.
    """
    data["nothing_changed_yet"] = NOTHING_CHANGED_YET


def set_required_changelog(data):
    """Require one of these strings to be present in the changelog.

    This is during the prerelease phase.
    """
    data["required_changelog_text"] = KNOWN_HEADINGS


def set_new_changelog(data):
    """Set text of changelog entry that is added when we do a postrelease.

    Yes, this overrides what we have set in the prerelease, and that is
    fine.
    """
    text = "".join(HEADERS)
    data["nothing_changed_yet"] = textwrap.dedent(text).strip()


def cleanup_changelog(data):
    """Cleanup empty headers.

    We call this twice: in prereleaser.before and prereleaser.middle.

    In 'before', we are too early and zest.releaser has not looked for
    the history file yet.  But we try 'CHANGES.rst' ourselves.

    In 'middle' we are a bit too late, as zest.releaser has already
    complained when it found the NOTHING_CHANGED_YET value in the
    history.

    So we call this twice, which should be fine.

    """
    # The history_file is probably not set yet, as we are called too early.
    # That might change subtly in future zest.releaser versions, so let's check
    # it anyway.
    history_file = data.get("history_file")
    if history_file:
        contents = "\n".join(data["history_lines"])
        encoding = data["history_encoding"]
    else:
        # We do not want to copy the logic from zest.releaser that tries to
        # find the history file, but we can check the most obvious spot.
        history_file = "CHANGES.rst"
        if not os.path.exists(history_file):
            print("Cannot cleanup history, will try again later.")
            return
        contents, encoding = read_text_file(history_file)
    orig_contents = contents
    changed = False
    for header in ALL_HEADERS:
        if header in contents:
            contents = contents.replace(header, "")
            changed = True
    if not changed:
        return
    write_text_file(history_file, contents, encoding=encoding)
    print(f"Cleaned up empty headers from history file {history_file}")
    # Update the data, otherwise our work may get overwritten.
    data["history_lines"] = contents.split("\n")
    if not os.path.isdir(".git"):
        print("Not a git checkout, cannot commit.")
        return
    g = git.Git(".")
    message = "Cleaned up empty headers from changelog.\n\n[ci skip]"
    print(g.diff(history_file))
    msg = "Commit changes?"
    if not ask(msg, default=True):
        # Restore original contents.
        write_text_file(history_file, orig_contents, encoding=encoding)
        sys.exit()
    print("Committing changes.")
    print(g.add(history_file))
    print(g.commit(message=message))


def check_pypi_access(data):
    env_var = "PLONE_RELEASER_CHECK_PYPI_ACCESS"
    try:
        if int(os.getenv(env_var, 1)) == 0:
            print(f"{env_var} variable set to zero: not checking pypi release rights.")
            return
    except (TypeError, ValueError, AttributeError):
        print(f"ERROR: could not parse {env_var} env var. Ignoring it.")

    section = os.getenv("TWINE_REPOSITORY", "pypi")
    pypi_user = pypi.PypiConfig().config.get(section, "username")
    if pypi_user == "__token__":
        print("Using token for PyPI upload: cannot check if you have release rights.")
        return
    if not can_user_release_package_to_pypi(pypi_user, data["name"]):
        msg = "User {0} does not have pypi release rights to {1}. Continue?"
        if not ask(msg.format(pypi_user, data["name"]), default=False):
            sys.exit()


def update_core(data, branch=None):
    msg = "Ok to update coredev versions.cfg/checkouts.cfg?"
    if branch:
        msg = f"Ok to update coredev {branch} versions.cfg/checkouts.cfg?"
    if ask(msg, default=True):
        root_path = os.path.join(os.getcwd(), "../../")
        g = git.Git(root_path)
        g.pull()  # make sure buildout.coredev is up-to-date
        package_name = data["name"]
        new_version = data["version"]
        update_versions(package_name, new_version)
        if package_name not in ALWAYS_CHECKED_OUT_PACKAGES:
            remove_from_checkouts(package_name)
        # git commit
        message = f"{package_name} {new_version}"
        # add all changed files
        g.add("--all")
        print("Committing changes.")
        g.commit(message=message)
        # We used to offer pushing the coredev change, but this is no longer a
        # good idea.
        print(
            "WARNING: a change in one or more buildout.coredev branches was made. "
            "Please wait a few minutes and then push this change. Otherwise the "
            "newly uploaded package is not yet available on all PyPI mirrors. "
            "This would cause Jenkins and GitHub Actions to fail."
        )
        return


def update_other_core_branches(data):
    CORE_BRANCHES = ["6.0", "6.1", "6.2"]
    package_name = data["name"]
    root_path = os.path.join(os.getcwd(), "../../")

    def _get_current_core_branch():
        g = git.Repo(root_path)
        return g.head.reference.name

    def _get_package_branch(package_name):
        path = os.path.join(root_path, "sources.cfg")
        sources = SourcesFile(path)
        try:
            return sources[package_name].branch
        except KeyError:  # package is not on sources.cfg of the current core branch
            return ""

    current_core_branch = _get_current_core_branch()
    CORE_BRANCHES.remove(current_core_branch)

    reference_package_branch = _get_package_branch(package_name=package_name)

    g = git.Git(root_path)
    for branch_name in CORE_BRANCHES:
        try:
            g.checkout(branch_name)
        except git.exc.GitCommandError:
            print(
                f"WARNING: There was an error checking out coredev branch "
                f"{branch_name}. This means we cannot check if this branch needs an "
                f"update for {package_name}. Please check manually."
            )
            continue

        package_branch = _get_package_branch(package_name=package_name)
        if package_branch == reference_package_branch:
            try:
                update_core(data, branch=branch_name)
            except Exception:
                print(
                    "There was an error trying to update {} on {}".format(
                        package_name, branch_name
                    )
                )

    g.checkout(current_core_branch)


def update_versions(package_name, new_version):
    # Update version
    print("Updating buildout versions")
    cwd = pathlib.Path.cwd()
    coredev_dir = (cwd / os.pardir / os.pardir).resolve()
    # In Python 3.10+ we could use `glob.glob("versions*.cfg", root_dir=coredev_dir),
    # but not in 3.9.  So we change directory.
    try:
        os.chdir(coredev_dir)
        # In coredev 6.0 we have versions.cfg, versions-ecosystem.cfg,
        # versions-extra.cfg.
        for filename in glob.glob("versions*.cfg"):
            path = coredev_dir / filename
            versions = VersionsFile(path)
            if package_name in versions:
                print(f"Updating {filename}")
                versions.set(package_name, new_version)

        # We may have pip constraints files to update.
        for filename in glob.glob("constraints*.txt"):
            path = coredev_dir / filename
            versions = ConstraintsFile(path)
            if package_name in versions:
                print(f"Updating {filename}")
                versions.set(package_name, new_version)

    finally:
        os.chdir(cwd)


def remove_from_checkouts(package_name):
    print("Removing package from checkouts")
    cwd = pathlib.Path.cwd()
    coredev_dir = (cwd / os.pardir / os.pardir).resolve()
    checkouts_file = coredev_dir / "checkouts.cfg"
    if checkouts_file.exists():
        checkouts = CheckoutsFile(checkouts_file)
        checkouts.remove(package_name)
    checkouts_file = coredev_dir / "mxcheckouts.ini"
    if checkouts_file.exists():
        checkouts = MxCheckoutsFile(checkouts_file)
        checkouts.remove(package_name)
