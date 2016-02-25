# -*- coding: utf-8 -*-
from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import VersionsFile
from plone.releaser.pypi import can_user_release_package_to_pypi
from zest.releaser import pypi
from zest.releaser.utils import ask

import git
import os
import sys
import textwrap


def set_nothing_changed_yet(data):
    """Set line that we look for in prerelease.

    This is when checking if a changelog entry has been added since last
    release.

    Note that currently this must be a single line, because
    zest.releaser looks for this text in each line.
    """
    data['nothing_changed_yet'] = '*add item here*'


def set_required_changelog(data):
    """Require one of these strings to be present in the changelog.

    This is during the prerelease phase.
    """
    data['required_changelog_text'] = ['New:', 'Fixes:', 'Incompatibilities:']


def set_new_changelog(data):
    """Set text of changelog entry that is added when we do a postrelease.

    Yes, this overrides what we have set in the prerelease, and that is
    fine.
    """
    text = """
    Incompatibilities:

    - *add item here*

    New:

    - *add item here*

    Fixes:

    - *add item here*"""
    data['nothing_changed_yet'] = textwrap.dedent(text).strip()


def check_pypi_access(data):
    pypi_user = pypi.PypiConfig().config.get('pypi', 'username')
    if not can_user_release_package_to_pypi(pypi_user, data['name']):
        msg = "User {0} does not have pypi release rights to {1}. Continue?"
        if not ask(msg.format(pypi_user, data['name']), default=False):
            sys.exit()


def update_core(data):
    if ask("Ok to update coredev versions.cfg/checkouts.cfg?", default=True):
        root_path = os.path.join(os.getcwd(), '../../')
        g = git.Git(root_path)
        g.pull()  # make sure buildout.coredev is up-to-date
        package_name = data['name']
        new_version = data['version']
        update_versions(package_name, new_version)
        update_checkouts(package_name)
        # git commit
        message = "{0} {1}".format(package_name, new_version)
        g.add('versions.cfg')
        g.add('checkouts.cfg')
        print "Committing changes."
        g.commit(message=message)
        print "Pushing changes to server."
        g.push()


def update_versions(package_name, new_version):
    # Update version
    print "Updating versions.cfg"
    path = os.path.join(os.getcwd(), '../../versions.cfg')
    versions = VersionsFile(path)
    versions.set(package_name, new_version)


def update_checkouts(package_name):
    # Remove from checkouts.cfg
    print "Removing package from checkouts.cfg"
    path = os.path.join(os.getcwd(), '../../checkouts.cfg')
    checkouts = CheckoutsFile(path)
    checkouts.remove(package_name)
