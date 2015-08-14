# -*- coding: utf-8 -*-
from argh import ArghParser
from argh import arg
from argh.decorators import named
from distutils.version import StrictVersion
from github import Github
from launchpadlib.launchpad import Launchpad
from plone.releaser import ACTION_BATCH
from plone.releaser import ACTION_INTERACTIVE
from plone.releaser import ACTION_REPORT
from plone.releaser import THIRD_PARTY_PACKAGES
from plone.releaser import pypi
from plone.releaser.buildout import Buildout
from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import VersionsFile
from plone.releaser.package import Package
from progress.bar import Bar

import datetime
import keyring


# TODO
buildout = Buildout()


def checkPypi(user):
    for package in buildout.sources:
        if package in THIRD_PARTY_PACKAGES:
            pass
        else:
            if not pypi.can_user_release_package_to_pypi(user, package):
                print "{0}: {1}".format(
                    package,
                    ', '.join(pypi.get_users_with_release_rights(package))
                )


@named('jenkins')
def jenkins_report():
    """Read-only version of checkAllPackagesForUpdates."""
    sources = buildout.sources
    for package_name, source in iter(sources.iteritems()):
        pkg = Package(buildout, package_name)
        pkg(action=ACTION_REPORT)


@arg('--interactive', default=False)
def checkPackageForUpdates(package_name, **kwargs):
    pkg = Package(buildout, package_name)
    if kwargs['interactive']:
        pkg(action=ACTION_INTERACTIVE)
    else:
        pkg(action=ACTION_BATCH)


@named('report')
@arg('--interactive', default=False)
def checkAllPackagesForUpdates(**kwargs):
    sources = buildout.sources
    for package_name, source in Bar('Scanning').iter(sources.iteritems()):
        pkg = Package(buildout, package_name)
        if kwargs['interactive']:
            pkg(action=ACTION_INTERACTIVE)
        else:
            pkg(action=ACTION_BATCH)


def pulls():
    client_id = 'b9f6639835b8c9cf462a'
    client_secret = keyring.get_password('plone.releaser', client_id)

    g = Github(client_id=client_id, client_secret=client_secret)

    for package_name, source in buildout.sources.iteritems():
        if source.path:
            repo = g.get_repo(source.path)
            pulls = [a for a in repo.get_pulls(
                'open') if a.head.ref == source.branch]
            if pulls:
                print package_name
                for pull in pulls:
                    print "    {0}: {1} ({2})".format(
                        pull.user.login,
                        pull.title,
                        pull.url
                    )


@named('changelog')
@arg('--start')
@arg('--end', default='here')
def changelog(**kwargs):
    from plone.releaser.changelog import build_unified_changelog
    build_unified_changelog(kwargs['start'], kwargs['end'])


@named('launchpad')
def create_launchpad_release(version):
    launchpad = Launchpad.login_with('plone.releaser', 'production')
    plone = launchpad.projects['plone']
    parsed_version = StrictVersion(version)
    # Blech. This feels flimsy
    series_name = '.'.join([str(a) for a in parsed_version.version[0:2]])
    series = plone.getSeries(name=series_name)
    if series is None:
        return "No series named {0}.".format(series_name)
    now = datetime.datetime.now().isoformat()
    milestone = series.newMilestone(name=version,
                                    date_targeted=now)
    # TODO: Get release notes
    release = milestone.createProductRelease(date_released=now,
                                             release_notes='')

    release_url = release.web_link

    return release_url


def check_checkout(package_name, path):
    if package_name not in CheckoutsFile(path):
        msg = 'Your package {0} is not on auto-checkout section'
        raise KeyError(msg.format(package_name))


def append_jenkins_build_number_to_package_version(jenkins_build_number):
    from zest.releaser.vcs import BaseVersionControl
    from zest.releaser.utils import cleanup_version
    vcs = BaseVersionControl()
    old_version = cleanup_version(vcs.version)
    new_version = '{0}.{1}'.format(old_version, jenkins_build_number)
    vcs.version = new_version
    return new_version


def set_package_version(version_file_path, package_name, new_version):
    versions = VersionsFile(version_file_path)
    versions.set(package_name, new_version)


class Manage(object):

    def __call__(self, **kwargs):
        parser = ArghParser()
        parser.add_commands(
            [checkPypi,
             checkPackageForUpdates,
             checkAllPackagesForUpdates,
             pulls,
             changelog,
             create_launchpad_release,
             check_checkout,
             append_jenkins_build_number_to_package_version,
             set_package_version,
             jenkins_report])
        parser.dispatch()


manage = Manage()
