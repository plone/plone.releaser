import urllib
from distutils.version import StrictVersion
from docutils.core import publish_doctree
from itertools import product
from esteele.manager.buildout import Buildout
from collections import OrderedDict


DIST_URL = "http://dist.plone.org/release/%s/versions.cfg"

buildout = Buildout()


def pullVersions(versionNumber):
    packageVersions = OrderedDict()
    url = DIST_URL % versionNumber
    versionsFile = urllib.urlopen(url)
    for line in versionsFile:
        line = line.strip().replace(" ", "")
        if line and not (line.startswith('#') or line.startswith('[')):
            try:
                package, version = line.split("=")
                version = StrictVersion(version)
            except ValueError:
                pass
            else:
                packageVersions[package] = version
    print "Parsed %s" % url
    return packageVersions


def getSourceLocation(package_name):
    source = buildout.sources.get(package_name)
    if source is not None:
        url = source.url
        url = url.replace('git:', 'https:')
        url = url.replace('.git', '')
        return url, source.branch
    return "", ""


def get_changelog(package_name):
    source_url, branch = getSourceLocation(package_name)
    file_names = ['CHANGES', 'HISTORY']
    file_extensions = ['.txt', '.rst']
    if 'github' in source_url:
        paths = ['raw/%s/docs/' % branch, 'raw/%s/' % branch]
    else:
        paths = ['/', '/docs/', '/'.join(package_name.split('.'))]
    for pathable in product(paths, file_names, file_extensions):
        structure = ''.join(pathable)
        url = "%s/%s" % (source_url, structure)
        try:
            response = urllib.urlopen(url)
        except IOError:
            print "Unable to reach %s" % url
        else:
            if response.code == 200:
                return response.read()


class Changelog():

    def __init__(self, file_location=None, content=None):
        self.data = OrderedDict()
        if content is not None:
            self._parse(content)
        elif file_location is not None:
            with open(file_location, 'r') as f:
                self._parse(f.read())

    def __iter__(self):
        return self.data.__iter__()

    def iteritems(self):
        return self.data.iteritems()

    def get(self, version):
        return self.data.get(version)

    def get_changes(self, start_version, end_version=None):
        versions = self.data.keys()

        end_version_index = 0
        if end_version is not None:
            try:
                end_version_index = versions.index(str(end_version))
            except ValueError:
                raise ValueError("Unknown version %s" % str(end_version))
        try:
            start_version_index = versions.index(str(start_version))
        except ValueError:
                raise ValueError("Unknown version %s" % str(start_version))

        newer_releases = versions[end_version_index:start_version_index]
        changes = []
        for release in newer_releases:
            changes.extend(self.data[release])
        return changes

    def latest(self):
        if self.data.items():
            return self.data.items()[0]
        return None

    def _parse(self, content):
        tree = publish_doctree(content)

        def isValidVersionSection(x):
            if x.tagname == "section":
                try:
                    StrictVersion(x['names'][0].split()[0])
                except (ValueError, IndexError):
                    pass
                else:
                    return True
            return False

        def isListItem(x):
            return x.tagname == 'list_item'

        foundSections = tree.traverse(condition=isValidVersionSection)
        for section in foundSections:
            version = section['names'][0].split()[0]
            list_items = section.traverse(condition=isListItem)
            entries = [a.rawsource for a in list_items]
            self.data[version] = entries


def build_unified_changelog(start_version, end_version):

    priorVersions = pullVersions(start_version)
    currentVersions = pullVersions(end_version)

    outputStr = ""
    for package, version in currentVersions.iteritems():
        if package in priorVersions:
            priorVersion = priorVersions[package]
            if version > priorVersion:
                print "%s has a newer version" % package
                packageChange = u"%s: %s %s %s" % (package,
                                                   priorVersion,
                                                   u"\u2192",
                                                   version)
                outputStr += u"\n" + packageChange + \
                    u"\n" + u"-" * len(packageChange) + "\n"

                logtext = get_changelog(package)
                changelog = Changelog(content=logtext)
                try:
                    changes = changelog.get_changes(priorVersion, version)
                except ValueError, e:
                    print e
                else:
                    for change in changes:
                        bullet = "- "
                        change = change.replace("\n", "\n" + " " * len(bullet))
                        outputStr += bullet + change + u"\n"

    print outputStr
