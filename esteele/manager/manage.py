from collections import OrderedDict
import os
import re
from shutil import rmtree
from tempfile import mkdtemp
import xmlrpclib

from argh import ArghParser, command, arg
from argh.decorators import named
from argh.interaction import confirm
from configparser import ConfigParser, ExtendedInterpolation, NoOptionError
from db import IgnoresDB
import git
from github import Github
import keyring
from progress.bar import Bar


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


def getVersion(package_name):
    config = ConfigParser(interpolation=ExtendedInterpolation())
    with open('versions.cfg') as f:
        config.readfp(f)
    version = config.get('versions', package_name)
    return version


def getAutoCheckouts():
    config = ConfigParser(interpolation=ExtendedInterpolation())
    with open('checkouts.cfg') as f:
        config.readfp(f)
    checkouts = config.get('buildout', 'auto-checkout')
    checkout_list = checkouts.split('\n')
    return checkout_list


def setAutoCheckouts(checkouts_list):
    config = ConfigParser(interpolation=ExtendedInterpolation())
    with open('checkouts.cfg') as f:
        config.readfp(f)
    checkouts = '\n'.join(checkouts_list)
    config.set('buildout', 'auto-checkout', checkouts)
    with open('checkouts.cfg', 'w') as f:
        config.write(f)


def getSourcesConfig():
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.optionxform = str
    with open('sources.cfg') as f:
        config.readfp(f)
    return config


class Source():

    def __init__(self, protocol=None, url=None, push_url=None, branch=None):
        self.protocol = protocol
        self.url = url
        self.push_url = push_url
        self.branch = branch

    def create_from_string(self, source_string):
        protocol, url, extra_1, extra_2, extra_3 = (
            lambda a, b, c=None, d=None, e=None: (a, b, c, d, e))(*source_string.split())
        for param in [extra_1, extra_2, extra_3]:
            if param is not None:
                key, value = param.split('=')
                setattr(self, key, value)
        self.protocol = protocol
        self.url = url
        if self.push_url is not None:
            self.push_url = self.push_url.split('=')[-1]
        if self.branch is None:
            self.branch = 'master'
        else:
            self.branch = self.branch.split('=')[-1]
        return self

    @property
    def path(self):
        if self.url:
            match = re.match(
                '(\w+://)(.+@)*([\w\d\.]+)(:[\d]+){0,1}/(?P<path>.+(?=\.git))(\.git)', self.url)
            if match:
                return match.groupdict()['path']
        return None


def getSources():
    config = getSourcesConfig()
    sources_dict = OrderedDict()
    for name, value in config['sources'].items():
        source = Source().create_from_string(value)
        sources_dict[name] = source
    return sources_dict


def getSource(package_name):
    config = getSourcesConfig()
    source = Source().create_from_string(config.get('sources', package_name))
    return source


def addToCheckouts(package_name):
    path = os.path.join(os.getcwd(), 'checkouts.cfg')
    with open(path, 'r') as f:
        checkoutstxt = f.read()
    with open(path, 'w') as f:
        fixes_text = "# Test fixes only"
        reg = re.compile("^[\s]*%s\n" % fixes_text, re.MULTILINE)
        newCheckoutsTxt = reg.sub('    %s\n%s\n' %
                                  (package_name, fixes_text), checkoutstxt)
        f.write(newCheckoutsTxt)


def removeFromCheckouts(package_name):
    # Remove from checkouts.cfg
    path = os.path.join(os.getcwd(), 'checkouts.cfg')
    with open(path, 'r') as f:
        checkoutstxt = f.read()
    with open(path, 'w') as f:
        reg = re.compile("^[\s]*%s\n" % package_name, re.MULTILINE)
        newCheckoutsTxt = reg.sub('', checkoutstxt)
        f.write(newCheckoutsTxt)


def setVersion(package_name, new_version):
    path = os.path.join(os.getcwd(), 'versions.cfg')
    with open(path, 'r') as f:
        versionstxt = f.read()
    with open(path, 'w') as f:
        reg = re.compile("(^%s[\s\=]+)[0-9\.abrc]+" %
                         package_name, re.MULTILINE)
        newVersionsTxt = reg.sub(r"\g<1>%s" % new_version, versionstxt)
        f.write(newVersionsTxt)


def getUsersWithReleaseRights(package_name):
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    existing_admins = [user for role,
                       user in client.package_roles(package_name)]
    return existing_admins


def canUserReleasePackageToPypi(user, package_name):
    return user in getUsersWithReleaseRights(package_name)


@command
def checkPypi(user):
    config = getSourcesConfig()
    for package in config.options('sources'):
        if package in THIRD_PARTY_PACKAGES:
            pass
        else:
            if not canUserReleasePackageToPypi(user, package):
                print "%s: %s" % (package, getUsersWithReleaseRights(package))


@command
def checkPackageForUpdates(package_name, interactive=False):
    if package_name not in IGNORED_PACKAGES:
        source = getSource(package_name)
        checkouts = getAutoCheckouts()
        try:
            version = getVersion(package_name)
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
                        print "\nNewer version %s is available for %s." % (latest_tag_in_branch, package_name)
                        if confirm("Update versions.cfg", default=True, skip=not interactive):
                            setVersion(package_name, latest_tag_in_branch)
                            core_repo = git.Repo(os.getcwd())
                            core_repo.git.add(
                                os.path.join(os.getcwd(), 'versions.cfg'))
                            core_repo.git.commit(message='%s=%s' %
                                                 (package_name, latest_tag_in_branch))
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
                    if package_name in checkouts and package_name not in ALWAYS_CHECKED_OUT:
                        print"\nNo new changes in %s, but it is listed for auto-checkout." % package_name
                        if confirm("Remove %s from checkouts.cfg" % package_name, default=True, skip=not interactive):
                            removeFromCheckouts(package_name)
                            core_repo = git.Repo(os.getcwd())
                            core_repo.git.add(
                                os.path.join(os.getcwd(), 'checkouts.cfg'))
                            core_repo.git.commit(
                                message='No new changes in %s' % package_name)
                            del(core_repo)
                else:
                    if commits_since_ignore is None:
                        # Check for checkout
                        if package_name not in checkouts:
                            print "\n"
                            print "WARNING: No auto-checkout exists for %s" % package_name
                            print "Changes in %s:" % package_name
                            for commit in commits_since_release:
                                print "    %s: %s" % (commit.author.name.encode('ascii', 'replace'), commit.summary.encode('ascii', 'replace'))
                            if package_name in THIRD_PARTY_PACKAGES:
                                print "NOTE: %s is a third-party package." % package_name

                            if confirm("Add %s to checkouts.cfg" % package_name, default=True, skip=not interactive):
                                addToCheckouts(package_name)
                                core_repo = git.Repo(os.getcwd())
                                core_repo.git.add(
                                    os.path.join(os.getcwd(), 'checkouts.cfg'))
                                core_repo.git.commit(
                                    message='%s has changes.' % package_name)
                                del(core_repo)
                            elif confirm("Ignore changes in  %s" % package_name, default=False, skip=not interactive):
                                commit_ignores.set(
                                    package_name, commits_since_release[0].hexsha)
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
    sources = getSources()
    for package_name in Bar('Scanning').iter(sources):
        checkPackageForUpdates(package_name, args.interactive)
        # print "\n"


def pulls():
    sources = getSources()

    client_id = 'b9f6639835b8c9cf462a'
    client_secret = keyring.get_password('esteele.manager', client_id)

    g = Github(client_id=client_id, client_secret=client_secret)

    for package_name, source in sources.iteritems():
        if source.path:
            repo = g.get_repo(source.path)
            pulls = [a for a in repo.get_pulls(
                'open') if a.head.ref == source.branch]
            if pulls:
                print package_name
                for pull in pulls:
                    print "    %s: %s (%s)" % (pull.user.login, pull.title, pull.url)


class Manage(object):

    def __call__(self, **kwargs):
        parser = ArghParser()
        parser.add_commands(
            [checkPypi, checkPackageForUpdates, checkAllPackagesForUpdates, pulls])
        parser.dispatch()


manage = Manage()
