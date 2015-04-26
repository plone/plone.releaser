# -*- coding: utf-8 -*-
from argh import ArghParser
from argh import arg
from argh.decorators import named
from argh.interaction import confirm
from configparser import NoOptionError
from db import IgnoresDB
from distutils.version import StrictVersion
from github import Github
from launchpadlib.launchpad import Launchpad
from plone.releaser import pypi
from plone.releaser.buildout import Buildout
from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import VersionsFile
from progress.bar import Bar
from shutil import rmtree
from tempfile import mkdtemp

import datetime
import git
import keyring
import os


THIRD_PARTY_PACKAGES = [
    'Zope2',
    'ZODB3',
    'txtfilter',
    'Products.CMFActionIcons',
    'Products.CMFCalendar',
    'Products.CMFCore',
    'Products.CMFDefault',
    'Products.CMFTopic',
    'Products.CMFUid',
    'Products.DCWorkflow',
    'Products.GenericSetup',
    'Products.GroupUserFolder',
    'Products.PluggableAuthService',
    'Products.PluginRegistry',
    'Products.ZCatalog',
]

IGNORED_PACKAGES = [
    'plone.releaser',
]

ALWAYS_CHECKED_OUT = [
    'Plone',
    'Products.CMFPlone',
    'plone.app.upgrade',
    'plone.app.locales',
]


# TODO
buildout = Buildout()


def checkPypi(user):
    for package in buildout.sources:
        if package in THIRD_PARTY_PACKAGES:
            pass
        else:
            if not pypi.canUserReleasePackageToPypi(user, package):
                print "{0}: {1}".format(
                    package,
                    ', '.join(pypi.getUsersWithReleaseRights(package))
                )


def checkPackageForUpdates(package_name, interactive=False):
    if package_name in IGNORED_PACKAGES:
        return

    source = buildout.sources.get(package_name)
    try:
        version = buildout.getVersion(package_name)
    except (NoOptionError, KeyError):
        # print "No version available for {0}".format(package_name)
        pass
    else:
        if source.protocol != 'git':
            # print "Skipped check of {0} as it's not a git repo.".format(
            #     package_name
            # )
            return

        tmpdir = mkdtemp()
        # print "Reading {0} branch of {1} for changes since {2}...".format(
        #     source.branch, package_name, version
        # )
        repo = git.Repo.clone_from(
            source.url, tmpdir, branch=source.branch, depth=100)

        try:
            latest_tag_in_branch = repo.git.describe(
                '--abbrev=0', '--tags')
        except git.exc.GitCommandError:
            # print "Unable to check tags for {0}".format(package_name)
            pass
        else:
            if latest_tag_in_branch > version:
                msg = "\nNewer version {0} is available for {1} (Currently {2})"
                print msg.format(latest_tag_in_branch, package_name, version)
                if confirm("Update versions.cfg",
                           default=True,
                           skip=not interactive):
                    buildout.setVersion(package_name,
                                        latest_tag_in_branch)
                    core_repo = git.Repo(os.getcwd())
                    core_repo.git.add(
                        os.path.join(os.getcwd(), 'versions.cfg'))
                    core_repo.git.commit(
                        message='{0}={1}'.format(
                            package_name,
                            latest_tag_in_branch
                        )
                    )
                    del(core_repo)

        commits_since_release = list(
            repo.iter_commits('{0}..{1}'.format(version, source.branch)))

        commit_ignores = IgnoresDB()
        sha = commit_ignores.get(package_name)
        commits_since_ignore = None
        if sha is not None:
            commits_since_ignore = list(
                repo.iter_commits('{0}..{1}'.format(sha, source.branch)))
        if not commits_since_release\
                or "Back to development" in commits_since_release[0].message\
                or commits_since_release[0].message.startswith('vb'):
            # print "No changes."
            if package_name in buildout.checkouts and \
                    package_name not in ALWAYS_CHECKED_OUT:
                print"\nNo new changes in {0}, but it is listed for " \
                     "auto-checkout.".format(package_name)
                msg = "Remove {0} from checkouts.cfg".format(package_name)
                if confirm(msg,
                           default=True,
                           skip=not interactive):
                    buildout.removeFromCheckouts(package_name)
                    core_repo = git.Repo(os.getcwd())
                    core_repo.git.add(
                        os.path.join(os.getcwd(), 'checkouts.cfg'))
                    core_repo.git.commit(
                        message='No new changes in {0}'.format(package_name))
                    del(core_repo)
        else:
            if commits_since_ignore is None:
                # Check for checkout
                if package_name not in buildout.checkouts:
                    msg = '\nWARNING: No auto-checkout exists for {0}\n' \
                          'Changes in {0}:'
                    print msg.format(package_name)
                    for commit in commits_since_release:
                        print "    {0}: {1}".format(
                            commit.author.name.encode('ascii', 'replace'),
                            commit.summary.encode('ascii', 'replace')
                        )
                    if package_name in THIRD_PARTY_PACKAGES:
                        msg = "NOTE: {0} is a third-party package."
                        print msg.format(package_name)

                    msg = "Add {0} to checkouts.cfg".format(package_name)
                    if confirm(msg, default=True, skip=not interactive):
                        buildout.addToCheckouts(package_name)
                        core_repo = git.Repo(os.getcwd())
                        core_repo.git.add(
                            os.path.join(os.getcwd(), 'checkouts.cfg'))
                        core_repo.git.commit(
                            message='{0} has changes.'.format(package_name))
                        del(core_repo)
                    elif confirm("Ignore changes in  {0}".format(package_name),
                                 default=False,
                                 skip=not interactive):
                        commit_ignores.set(
                            package_name,
                            commits_since_release[0].hexsha)
                else:
                    if not interactive:
                        print "\nChanges in {0}:".format(package_name)
                        for commit in commits_since_release:
                            print "    {0}: {1}".format(
                                commit.author.name.encode('ascii',
                                                          'replace'),
                                commit.summary.encode('ascii',
                                                      'replace')
                            )
                        if package_name in THIRD_PARTY_PACKAGES:
                            msg = "NOTE: {0} is a third-party package."
                            print msg.format(package_name)
        del(repo)
        rmtree(tmpdir)


@named('report')
@arg('--interactive', default=False)
def checkAllPackagesForUpdates(**kwargs):
    sources = buildout.sources
    for package_name, source in Bar('Scanning').iter(sources.iteritems()):
        checkPackageForUpdates(package_name, kwargs['interactive'])


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
@arg('--end')
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
             set_package_version])
        parser.dispatch()


manage = Manage()
