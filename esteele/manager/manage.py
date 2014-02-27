import os
from shutil import rmtree
from tempfile import mkdtemp

from argh import ArghParser, command, arg
from argh.decorators import named
from argh.interaction import confirm
from configparser import NoOptionError
from db import IgnoresDB
import git
from github import Github
import keyring
from progress.bar import Bar
from esteele.manager.buildout import Buildout
from esteele.manager import pypi


THIRD_PARTY_PACKAGES = ['Zope2',
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
                        'Products.ZCatalog']

IGNORED_PACKAGES = ['esteele.manager']

ALWAYS_CHECKED_OUT = ['Plone',
                      'Products.CMFPlone',
                      'plone.app.upgrade',
                      'plone.app.locales']


# TODO
buildout = Buildout()


@command
def checkPypi(user):
    for package in buildout.sources:
        if package in THIRD_PARTY_PACKAGES:
            pass
        else:
            if not pypi.canUserReleasePackageToPypi(user, package):
                print "%s: %s" % (package,
                                  pypi.getUsersWithReleaseRights(package))


@command
def checkPackageForUpdates(package_name, interactive=False):
    if package_name not in IGNORED_PACKAGES:
        source = buildout.sources.get(package_name)
        try:
            version = buildout.getVersion(package_name)
        except NoOptionError:
            # print "No version available for %s" % package_name
            pass
        else:
            if source.protocol == 'git':
                tmpdir = mkdtemp()
                # print "Reading %s branch of %s for changes since %s..." %
                # (source.branch, package_name, version)
                repo = git.Repo.clone_from(
                    source.url, tmpdir, branch=source.branch, depth=100)

                try:
                    latest_tag_in_branch = repo.git.describe(
                        '--abbrev=0', '--tags')
                except git.exc.GitCommandError:
                    # print "Unable to check tags for %s" % package_name
                    pass
                else:
                    if latest_tag_in_branch > version:
                        print "\nNewer version %s is available for %s." % (latest_tag_in_branch,package_name)
                        if confirm("Update versions.cfg",
                                   default=True,
                                   skip=not interactive):
                            buildout.setVersion(package_name,
                                                latest_tag_in_branch)
                            core_repo = git.Repo(os.getcwd())
                            core_repo.git.add(
                                os.path.join(os.getcwd(), 'versions.cfg'))
                            core_repo.git.commit(message='%s=%s' %
                                                 (package_name,
                                                  latest_tag_in_branch))
                            del(core_repo)

                commits_since_release = list(
                    repo.iter_commits('%s..%s' % (version, source.branch)))

                commit_ignores = IgnoresDB()
                sha = commit_ignores.get(package_name)
                commits_since_ignore = None
                if sha is not None:
                    commits_since_ignore = list(
                        repo.iter_commits('%s..%s' % (sha, source.branch)))
                if not commits_since_release\
                        or "Back to development" in commits_since_release[0].message\
                        or commits_since_release[0].message.startswith('vb'):
                    # print "No changes."
                    if package_name in buildout.checkouts and package_name not in ALWAYS_CHECKED_OUT:
                        print"\nNo new changes in %s, but it is listed for auto-checkout." % package_name
                        if confirm("Remove %s from checkouts.cfg" % package_name,
                                   default=True,
                                   skip=not interactive):
                            buildout.removeFromCheckouts(package_name)
                            core_repo = git.Repo(os.getcwd())
                            core_repo.git.add(
                                os.path.join(os.getcwd(), 'checkouts.cfg'))
                            core_repo.git.commit(
                                message='No new changes in %s' % package_name)
                            del(core_repo)
                else:
                    if commits_since_ignore is None:
                        # Check for checkout
                        if package_name not in buildout.checkouts:
                            print "\n"
                            print "WARNING: No auto-checkout exists for %s" % package_name
                            print "Changes in %s:" % package_name
                            for commit in commits_since_release:
                                print "    %s: %s" % (commit.author.name.encode('ascii', 'replace'), commit.summary.encode('ascii', 'replace'))
                            if package_name in THIRD_PARTY_PACKAGES:
                                print "NOTE: %s is a third-party package." % package_name

                            if confirm("Add %s to checkouts.cfg" % package_name, default=True, skip=not interactive):
                                buildout.addToCheckouts(package_name)
                                core_repo = git.Repo(os.getcwd())
                                core_repo.git.add(
                                    os.path.join(os.getcwd(), 'checkouts.cfg'))
                                core_repo.git.commit(
                                    message='%s has changes.' % package_name)
                                del(core_repo)
                            elif confirm("Ignore changes in  %s" % package_name,
                                         default=False,
                                         skip=not interactive):
                                commit_ignores.set(
                                    package_name,
                                    commits_since_release[0].hexsha)
                        else:
                            if not interactive:
                                print "\n"
                                print "Changes in %s:" % package_name
                                for commit in commits_since_release:
                                    print "    %s: %s" % (commit.author.name.encode('ascii', 'replace'), commit.summary.encode('ascii', 'replace'))
                                if package_name in THIRD_PARTY_PACKAGES:
                                    print "NOTE: %s is a third-party package." % package_name
                del(repo)
                rmtree(tmpdir)
            else:
                # print "Skipped check of %s as it's not a git repo." %
                # package_name
                pass


@named('report')
@arg('--interactive', default=False)
def checkAllPackagesForUpdates(args):
    sources = buildout.getSources()
    for package_name in Bar('Scanning').iter(sources):
        checkPackageForUpdates(package_name, args.interactive)
        # print "\n"


def pulls():
    client_id = 'b9f6639835b8c9cf462a'
    client_secret = keyring.get_password('esteele.manager', client_id)

    g = Github(client_id=client_id, client_secret=client_secret)

    for package_name, source in buildout.sources.iteritems():
        if source.path:
            repo = g.get_repo(source.path)
            pulls = [a for a in repo.get_pulls(
                'open') if a.head.ref == source.branch]
            if pulls:
                print package_name
                for pull in pulls:
                    print "    %s: %s (%s)" % (pull.user.login,
                                               pull.title,
                                               pull.url)


@named('changelog')
@arg('--start')
@arg('--end')
def changelog(args):
    from esteele.manager.changelog import build_unified_changelog
    build_unified_changelog(args.start, args.end)


class Manage(object):

    def __call__(self, **kwargs):
        parser = ArghParser()
        parser.add_commands(
            [checkPypi,
             checkPackageForUpdates,
             checkAllPackagesForUpdates,
             pulls,
             changelog])
        parser.dispatch()


manage = Manage()
