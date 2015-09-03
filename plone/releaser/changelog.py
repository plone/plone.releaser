# -*- coding: utf-8 -*-
from collections import OrderedDict
from distutils.version import LooseVersion
from docutils.core import publish_doctree
from itertools import product
from plone.releaser.buildout import Buildout

import urllib


DIST_URL = "http://dist.plone.org/release/{0}/versions.cfg"

buildout = Buildout()


def pull_versions(version_number):
    package_versions = OrderedDict()
    if version_number == 'here':
        url = 'versions.cfg'
        versions_file = open(url)
    else:
        url = DIST_URL.format(version_number)
        versions_file = urllib.urlopen(url)
    if versions_file.code == 404:
        raise ValueError("Version %s not found." % version_number)
    for line in versions_file:
        line = line.strip().replace(" ", "")
        if line and not (line.startswith('#') or line.startswith('[')):
            try:
                package, version = line.split("=")
                version = LooseVersion(version)
            except ValueError:
                pass
            else:
                package_versions[package] = version
    print "Parsed {0}".format(url)
    return package_versions


def get_source_location(package_name):
    source = buildout.sources.get(package_name)
    if source is not None:
        # Go from this:
        # git://github.com/plone/plone.batching.git
        # to this:
        # https://raw.githubusercontent.com/plone/plone.batching
        url = source.url
        url = url.replace('git:', 'https:')
        url = url.replace('.git', '')
        url = url.replace('github.com', 'raw.githubusercontent.com')
        return url, source.branch
    return "", ""


def get_changelog(package_name):
    source_url, branch = get_source_location(package_name)
    if not source_url:
        return ''
    file_names = ['CHANGES', 'HISTORY']
    file_extensions = ['.rst', '.txt']
    if 'github' in source_url:
        paths = [
            '{0}/'.format(branch),
            '{0}/docs/'.format(branch),
        ]
    else:
        paths = ['/', '/docs/', '/'.join(package_name.split('.')) + '/']
    for pathable in product(paths, file_names, file_extensions):
        structure = ''.join(pathable)
        url = "{0}/{1}".format(source_url, structure)
        try:
            response = urllib.urlopen(url)
        except IOError:
            print "Unable to reach {0}".format(url)
        else:
            if response.code == 200:
                return response.read()
    return ''


class Changelog(object):

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
                raise ValueError("Unknown version {0}".format(end_version))
        try:
            start_version_index = versions.index(str(start_version))
        except ValueError:
            raise ValueError("Unknown version {0}".format(start_version))

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

        def is_valid_version_section(x):
            if x.tagname == "section":
                try:
                    LooseVersion(x['names'][0].split()[0])
                except (ValueError, IndexError):
                    pass
                else:
                    return True
            return False

        def is_list_item(x):
            return x.tagname == 'list_item'

        found_sections = tree.traverse(condition=is_valid_version_section)
        for section in found_sections:
            version = section['names'][0].split()[0]
            list_items = section.traverse(condition=is_list_item)
            entries = [a.rawsource for a in list_items]
            self.data[version] = entries


def build_unified_changelog(start_version, end_version):
    try:
        prior_versions = pull_versions(start_version)
        current_versions = pull_versions(end_version)
    except ValueError, e:
        print e
        return

    output_str = ""
    try:
        for package, version in current_versions.iteritems():
            if package in prior_versions:
                prior_version = prior_versions[package]
                if version > prior_version:
                    print "{0} has a newer version".format(package)
                    packageChange = u"{0}: {1} {2} {3}".format(
                        package,
                        prior_version,
                        u"\u2192",
                        version
                    )
                    output_str += u"\n" + packageChange + \
                        u"\n" + u"-" * len(packageChange) + "\n"

                    logtext = get_changelog(package)
                    if not logtext:
                        print "No changelog found."
                        continue
                    changelog = Changelog(content=logtext)
                    try:
                        changes = changelog.get_changes(prior_version, version)
                    except ValueError, e:
                        print e
                    else:
                        for change in changes:
                            bullet = "- "
                            change = change.replace("\n", "\n" + " " * len(bullet))
                            output_str += bullet + change + u"\n"
    except KeyboardInterrupt:
        pass

    print output_str.encode('utf-8')
