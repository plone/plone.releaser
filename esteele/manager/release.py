from zest.releaser.utils import ask
from zest.releaser import pypi
import sys
import os
from esteele.manager.pypi import canUserReleasePackageToPypi
from esteele.manager.buildout import VersionsFile, CheckoutsFile
from esteele.manager.changelog import Changelog

import git


def check_pypi_access(data):
    pypi_user = pypi.PypiConfig().config.get('pypi', 'username')
    if not canUserReleasePackageToPypi(pypi_user, data['name']):
        if not ask("User %s does not have pypi release rights to %s. Continue?" % (pypi_user, data['name']), default=False):
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
    print "Changelog entries for version %s." % data['new_version']
    for entry in entries:
        print entry
    if not ask("Continue?", default=True):
        sys.exit()


def update_core(data):
    if ask("Ok to update coredev versions.cfg/checkouts.cfg?", default=True):
        package_name = data['name']
        new_version = data['version']
        update_versions(package_name, new_version)
        update_checkouts(package_name)
        # git commit
        root_path = os.path.join(os.getcwd(), '../../')
        message = "%s %s" % (package_name, new_version)
        g = git.Git(root_path)
        g.add('versions.cfg')
        g.add('checkouts.cfg')
        print "Commiting changes."
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
