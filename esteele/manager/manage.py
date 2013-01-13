from argh import ArghParser, command
from argh.decorators import named
from configparser import ConfigParser, ExtendedInterpolation, NoOptionError
import xmlrpclib
import git
from shutil import rmtree
from tempfile import mkdtemp
from collections import OrderedDict
from progress.bar import Bar
from github import Github
import re
import keyring


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

def getVersion(package_name):
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.readfp(open('versions.cfg'))
    version = config.get('versions', package_name)
    return version


def getAutoCheckouts():
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.readfp(open('checkouts.cfg'))
    checkouts = config.get('buildout', 'auto-checkout')
    checkout_list = checkouts.split('\n')
    return checkout_list


def setAutoCheckouts(checkouts_list):
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.readfp(open('checkouts.cfg'))
    checkouts = '\n'.join(checkouts_list)
    config.set('buildout', 'auto-checkout', checkouts)
    config.write(open('checkouts.cfg', 'w'))


def getSourcesConfig():
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.optionxform = str
    config.readfp(open('sources.cfg'))
    return config


class Source():

    def __init__(self, protocol=None, url=None, push_url=None, branch=None):
        self.protocol = protocol
        self.url = url
        self.push_url = push_url
        self.branch = branch

    def create_from_string(self, source_string):
        protocol, url, push_url, branch = (lambda a, b, c=None, d=None: (a, b, c, d))(*source_string.split())
        self.protocol = protocol
        self.url = url
        if push_url is not None:
            self.push_url = push_url.split('=')[-1]
        if branch is None:
            self.branch = 'master'
        else:
            self.branch = branch.split('=')[-1]
        return self

    @property
    def path(self):
        if self.url:
            match = re.match('(\w+://)(.+@)*([\w\d\.]+)(:[\d]+){0,1}/(?P<path>.+(?=\.git))(\.git)', self.url)
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
    checkouts = getAutoCheckouts()
    checkouts.append(package_name)
    setAutoCheckouts(checkouts)


def removeFromCheckouts(package_name):
    checkouts = getAutoCheckouts()
    checkouts.remove(package_name)
    setAutoCheckouts(checkouts)


def setVersion(package_name, new_version):
    import configparser
    versions = ConfigParser(interpolation=ExtendedInterpolation())
    versions.optionxform = str
    versions_file = open('versions.cfg')
    versions.readfp(versions_file)
    # versions.set('versions', package_name, new_version)
    # versions.write(open('versions.cfg', 'w'))


@command
def release(package, new_version):
    # Remove from checkouts
    # removeFromCheckouts(package)
    # Update version number
    setVersion(package, new_version)
    print package, new_version


def getUsersWithReleaseRights(package_name):
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    existing_admins = [user for role, user in client.package_roles(package_name)]
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
def checkPackageForUpdates(package_name):
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
                # print "Reading %s branch of %s for changes since %s..." % (source.branch, package_name, version)
                repo = git.Repo.clone_from(source.url, tmpdir, branch=source.branch, depth=20)

                g = git.Git(tmpdir)
                try:
                    latest_tag_in_branch = g.describe('--abbrev=0', '--tags')
                except git.exc.GitCommandError:
                    # print "Unable to check tags for %s" % package_name
                    pass
                else:
                    if latest_tag_in_branch > version:
                        print "\nNewer version %s is available for %s." % (latest_tag_in_branch, package_name)
                        return

                commits_since_release = list(repo.iter_commits('%s..%s' % (version, source.branch)))
                if not commits_since_release\
                        or "Back to development" in commits_since_release[0].message\
                        or commits_since_release[0].message.startswith('vb'):
                    # print "No changes."
                    if package_name in checkouts:
                        print"\nNo new changes in %s, but it is listed for auto-checkout." % package_name
                else:
                    print "\n"
                    # Check for checkout
                    if package_name not in checkouts:
                        print "WARNING: No auto-checkout exists for %s" % package_name
                    print "Changes in %s:" % package_name
                    for commit in commits_since_release: 
                        print "    %s: %s" % (commit.author.name.encode('ascii', 'replace'), commit.summary.encode('ascii', 'replace'))
                    if package_name in THIRD_PARTY_PACKAGES:
                        print "NOTE: %s is a third-party package." % package_name
                rmtree(tmpdir)
            else:
                # print "Skipped check of %s as it's not a git repo." % package_name
                pass


@named('report')
def checkAllPackagesForUpdates():
    sources = getSources()
    for package_name in Bar('Scanning').iter(sources):
        checkPackageForUpdates(package_name)
        # print "\n"


def pulls():
    sources = getSources()

    client_id = 'b9f6639835b8c9cf462a'
    client_secret = keyring.get_password('esteele.manager', client_id)

    g = Github(client_id=client_id, client_secret=client_secret)

    for package_name, source in sources.iteritems():
        if source.path:
            repo = g.get_repo(source.path)
            pulls = [a for a in repo.get_pulls('open') if a.head.ref == source.branch]
            if pulls:
                print package_name
                for pull in pulls:
                    print "    %s: %s (%s)" % (pull.user.login, pull.title, pull.url)


class Manage(object):
    def __call__(self, **kwargs):
        parser = ArghParser()
        parser.add_commands([release, checkPypi, checkPackageForUpdates, checkAllPackagesForUpdates, pulls])
        parser.dispatch()


manage = Manage()
