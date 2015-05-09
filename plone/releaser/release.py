# -*- coding: utf-8 -*-
from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import VersionsFile
from plone.releaser.changelog import Changelog
from plone.releaser.pypi import can_user_release_package_to_pypi
from zest.releaser import pypi
from zest.releaser.utils import ask

import git
import os
import sys


def check_pypi_access(data):
    pypi_user = pypi.PypiConfig().config.get('pypi', 'username')
    if not can_user_release_package_to_pypi(pypi_user, data['name']):
        msg = "User {0} does not have pypi release rights to {1}. Continue?"
        if not ask(msg.format(pypi_user, data['name']), default=False):
            sys.exit()


def show_changelog_entries(data):
    # Find changelog
    # TODO: Figure out how to catch malformed rst
    if data['history_file'] is not None:
        changelog = Changelog(file_location=data['history_file'])
    # Get top release's entry
    entries = changelog.latest()
    if entries is None:
        if not ask("Unable to parse changelog. Continue?", default=True):
            sys.exit()
        return
    print "Changelog entries for version {0}.".format(data['new_version'])
    for entry in entries:
        if isinstance(entry, list):
            print '\n'.join(entry)
        else:
            print entry
    if not ask("Continue?", default=True):
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
