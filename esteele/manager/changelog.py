import urllib
from distutils.version import StrictVersion
from docutils.core import publish_doctree
import sys
from itertools import product
from esteele.manager.buildout import Buildout


DIST_URL = "http://dist.plone.org/release/%s/versions.cfg"

buildout = Buildout()


def pullVersions(versionNumber):
    try:
        from ordereddict import OrderedDict
        packageVersions = OrderedDict()
    except ImportError:
        print "Unable to find OrderedDict"
        packageVersions = {}
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


def main(argv):
    priorVersionNumber = sys.argv[1]
    currentVersionNumber = sys.argv[2]

    priorVersions = pullVersions(priorVersionNumber)
    currentVersions = pullVersions(currentVersionNumber)

    outputStr = ""
    for package, version in currentVersions.iteritems():
        if package in priorVersions:
            priorVersion = priorVersions[package]
            if version > priorVersion:
                print "%s has a newer version" % package
                packageChange = u"%s: %s %s %s" % (package, priorVersion, u"\u2192", version)
                outputStr += u"\n" + packageChange + u"\n" + u"-" * len(packageChange) + "\n"
                source, branch = getSourceLocation(package)
                if source:
                    file_names = ['CHANGES', 'HISTORY']
                    file_extensions = ['.txt', '.rst', '.md']
                    if 'github' in source:
                        paths = ['raw/%s/docs/' % branch, 'raw/%s/' % branch]
                    else:
                        paths = ['/', '/docs/', '/'.join(package.split('.'))]

                    for pathable in product(paths, file_names, file_extensions):
                        structure = ''.join(pathable)
                        url = "%s/%s" % (source, structure)
                        try:
                            response = urllib.urlopen(url)
                        except IOError:
                            print "Unable to reach %s" % url
                        else:
                            if response.code == 200:
                                logtext = response.read()
                                tree = publish_doctree(logtext)

                                def isValidVersionSection(x):
                                    if x.tagname == "section":
                                        try:
                                            logVersion = StrictVersion(x['names'][0].split()[0])
                                        except (ValueError, IndexError):
                                            pass
                                        else:
                                            return logVersion > priorVersion and logVersion <= version
                                    return False

                                foundSections = tree.traverse(condition=isValidVersionSection)
                                if foundSections:
                                    outputStr += u"\n"
                                    for s in foundSections:
                                        s.children[-1]
                                        childlist = s.children[-1]
                                        bullet = "- "
                                        for child in childlist.children:
                                            text = child.astext()
                                            text = text.replace("\n","\n" + " " * len(bullet))
                                            outputStr += bullet + text + u"\n"

                                break

    print outputStr


if __name__ == "__main__":
    main(sys.argv[1:])
