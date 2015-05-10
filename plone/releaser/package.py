# -*- coding: utf-8 -*-
from argh.interaction import confirm
from configparser import NoOptionError
from contextlib import contextmanager
from plone.releaser import ACTION_BATCH
from plone.releaser import ACTION_INTERACTIVE
from plone.releaser import ACTION_REPORT
from plone.releaser import ALWAYS_CHECKED_OUT
from plone.releaser import IGNORED_PACKAGES
from plone.releaser import PACKAGE_ACTIONS
from plone.releaser import THIRD_PARTY_PACKAGES
from plone.releaser.db import IgnoresDB
from shutil import rmtree
from tempfile import mkdtemp

import git
import os


@contextmanager
def git_repo(source):
    """Handle temporal git repositories.

    It ensures that a git repository is cloned on a temporal folder that is
    removed after being used.

    See an example of this kind of context managers here:
    http://preshing.com/20110920/the-python-with-statement-by-example/
    """
    tmp_dir = mkdtemp()
    repo = git.Repo.clone_from(
        source.url,
        tmp_dir,
        branch=source.branch,
        depth=100
    )

    # give the control back
    yield repo

    # cleanup
    del repo
    rmtree(tmp_dir)


@contextmanager
def buildout_coredev():
    """Context manager for buildout.coredev git repositories.

    It ensures that the git repository is cloned on a temporal folder and that
    everything is cleaned up after being used.
    """
    repo = git.Repo(os.getcwd())
    yield repo
    del repo


class Package(object):

    # A reference to an plone.releaser.buildout.Buildout instance
    buildout = None

    # The package that's checked
    name = None

    # If the user that runs this script is expected to make interactive choices
    interactive = False

    # If only a report has to be produced and no changes should be pushed
    # anywhere, i.e. jenkins.plone.org creating reports for example
    report_only = False

    # The package URI as defined on sources.cfg
    source = None

    # The package version as found on versions.cfg
    version = None

    # Database of per package ignored commits
    commit_ignores = None

    def __init__(self, buildout, package):
        self.buildout = buildout
        self.name = package
        self.source = self.buildout.sources.get(self.name)
        self.version = self.get_version()
        self.commit_ignores = IgnoresDB()

    def __call__(self, action=ACTION_INTERACTIVE):
        if action not in PACKAGE_ACTIONS:
            print 'This package action does not exist: {0}'.format(action)
            return
        self.set_interaction_and_report(action)

        # exit early if the package:
        # - is on the ignored list
        # - there is no version available
        # - is not hosted on a git VCS
        if self.name in IGNORED_PACKAGES or \
                self.version is None or \
                not self.is_git_hosted():
            return

        # clone the package and gather data about it
        with git_repo(self.source) as repo:
            # exit early if no tag can be found
            latest_tag_in_branch = self.latest_tag(repo)
            if latest_tag_in_branch is None:
                return

            # if there is a newer tag of the package not in buildout.coredev
            # versions.cfg, ask/add/report about it
            self.update_version(latest_tag_in_branch)

            commits_since_release = self.latest_commits(repo)
            latest_ignored_commit = self.commit_ignores.get(self.name)
            commits_since_ignore = None
            if latest_ignored_commit is not None:
                commits_since_ignore = self._commits_between(
                    repo,
                    latest_ignored_commit,
                    self.source.branch
                )

            # if there are no changes since the last release (i.e. last tag)
            if not commits_since_release \
                    or 'Back to development' in commits_since_release[0].message \
                    or commits_since_release[0].message.startswith('vb'):

                self.remove()

            elif commits_since_ignore is None:
                # Check for checkout
                if self.name not in self.buildout.checkouts:
                    msg = '\nWARNING: No auto-checkout exists for {0}\n Changes in {0}:'  # noqa
                    self.print_commits(
                        commits_since_release,
                        message=msg.format(self.name)
                    )

                    if self.name in THIRD_PARTY_PACKAGES:
                        msg = 'NOTE: {0} is a third-party package.'
                        print msg.format(self.name)

                    self.add(commits_since_release)

                else:
                    if not self.interactive:
                        msg = '\nChanges in {0}:'.format(self.name)
                        self.print_commits(commits_since_release, message=msg)

                        if self.name in THIRD_PARTY_PACKAGES:
                            msg = 'NOTE: {0} is a third-party package.'
                            print msg.format(self.name)

    def set_interaction_and_report(self, action):
        if action == ACTION_REPORT:
            self.interactive = False
            self.report_only = True
        elif action == ACTION_INTERACTIVE:
            self.interactive = True
            self.report_only = False
        elif action == ACTION_BATCH:
            self.interactive = False
            self.report_only = False

    def is_git_hosted(self):
        if self.source.protocol != 'git':
            if self.report_only:
                msg = 'Skipped check of {0} as it\'s not a git repo.'
                print msg.format(self.name)
            return False
        return True

    def get_version(self):
        version = None
        try:
            version = self.buildout.get_version(self.name)
        except (NoOptionError, KeyError):
            if self.report_only:
                print 'No version available for {0}'.format(self.name)

        return version

    def latest_tag(self, repo):
        tag = None
        try:
            tag = repo.git.describe('--abbrev=0', '--tags')
        except git.exc.GitCommandError:
            if self.report_only:
                print 'Unable to check tags for {0}'.format(self.name)

        return tag

    def latest_commits(self, repo):
        commits = None

        try:
            commits = self._commits_between(
                repo,
                self.version,
                self.source.branch
            )
        except git.exc.GitCommandError:
            print '\nCould not read commits for package {0}'.format(self.name)

        return commits

    @staticmethod
    def _commits_between(repo, start, end):
        return list(
            repo.iter_commits(
                '{0}..{1}'.format(start, end)
            )
        )

    def remove(self):
        if self.name in self.buildout.checkouts and \
                self.name not in ALWAYS_CHECKED_OUT:
            msg = '\nNo new changes in {0}, but it is listed for auto-checkout.'  # noqa
            print msg.format(self.name)

        if self.report_only:
            return

        msg = 'Remove {0} from checkouts.cfg'.format(self.name)
        if confirm(msg, default=True, skip=not self.interactive):
            self.buildout.remove_from_checkouts(self.name)

            with buildout_coredev() as core_repo:
                checkouts_path = os.path.join(os.getcwd(), 'checkouts.cfg')
                core_repo.git.add(checkouts_path)
                msg = 'No new changes in {0}'.format(self.name)
                core_repo.git.commit(message=msg)

    def add(self, commits_since_release):
        if self.report_only:
            return

        msg = 'Add {0} to checkouts.cfg'.format(self.name)
        if confirm(msg, default=True, skip=not self.interactive):
            self.buildout.add_to_checkouts(self.name)

            with buildout_coredev() as core_repo:
                checkouts_path = os.path.join(os.getcwd(), 'checkouts.cfg')
                core_repo.git.add(checkouts_path)
                msg = '{0} has changes.'.format(self.name)
                core_repo.git.commit(message=msg)

        elif confirm('Ignore changes in  {0}'.format(self.name),
                     default=False,
                     skip=not self.interactive):
            self.commit_ignores.set(
                self.name,
                commits_since_release[0].hexsha
            )

    @staticmethod
    def print_commits(commits_list, message=None):
        if message:
            print message

        for commit in commits_list:
            print '    {0}: {1}'.format(
                commit.author.name.encode('ascii', 'replace'),
                commit.summary.encode('ascii', 'replace')
            )

    def update_version(self, tag):
        if tag <= self.version:
            return

        msg = '\nNewer version {0} is available for {1} (Currently {2})'
        print msg.format(tag, self.name, self.version)

        if self.report_only:
            return

        if confirm('Update versions.cfg',
                   default=True,
                   skip=not self.interactive):
            self.buildout.set_version(self.name, tag)

            with buildout_coredev() as core_repo:
                versions_path = os.path.join(os.getcwd(), 'versions.cfg')
                core_repo.git.add(versions_path)
                core_repo.git.commit(message='{0}={1}'.format(self.name, tag))
                core_repo.git.push()
