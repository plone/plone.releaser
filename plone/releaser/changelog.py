# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import OrderedDict
from collections import defaultdict
from distutils.version import LooseVersion
from docutils.core import publish_doctree
from itertools import product
from plone.releaser.buildout import Buildout
from plone.releaser.release import HEADINGS
from plone.releaser.release import OLD_HEADING_MAPPING
from six.moves.urllib.request import urlopen
import six


DIST_URL = "https://dist.plone.org/release/{0}/versions.cfg"

buildout = Buildout()


def pull_versions(version_number):
    package_versions = OrderedDict()
    if version_number == "here":
        url = "versions.cfg"
        versions_file = open(url)
    else:
        url = DIST_URL.format(version_number)
        versions_file = urlopen(url)
        if versions_file.code == 404:
            raise ValueError("Version %s not found." % version_number)
    for line in versions_file:
        if not isinstance(line, type(u"")):
            line = line.decode("utf-8")
        line = line.strip().replace(u" ", u"")
        if line and not (line.startswith(u"#") or line.startswith(u"[")):
            try:
                package, version = line.split(u"=")
            except ValueError:
                continue
            if not version:
                # May be a line from versionannotation
                continue
            version = LooseVersion(version)
            package_versions[package] = version
    print("Parsed {0}".format(url))
    return package_versions


def get_source_location(package_name):
    source = buildout.sources.get(package_name)
    if source is not None:
        # Go from this:
        # git://github.com/plone/plone.batching.git
        # to this:
        # https://raw.githubusercontent.com/plone/plone.batching
        url = source.url
        url = url.replace("git:", "https:")
        url = url.replace(".git", "")
        url = url.replace("github.com", "raw.githubusercontent.com")
        return url, source.branch
    return "", ""


def get_changelog(package_name):
    source_url, branch = get_source_location(package_name)
    if not source_url:
        return ""
    file_names = ["CHANGES", "HISTORY"]
    file_extensions = [".rst", ".txt"]
    if "github" in source_url:
        paths = ["{0}/".format(branch), "{0}/docs/".format(branch)]
    else:
        paths = ["/", "/docs/", "/".join(package_name.split(".")) + "/"]
    for pathable in product(paths, file_names, file_extensions):
        structure = "".join(pathable)
        url = "{0}/{1}".format(source_url, structure)
        try:
            response = urlopen(url)
        except IOError:
            print("Unable to reach {0}".format(url))
        else:
            if response.code == 200:
                return response.read()
    return ""


class Changelog(object):
    def __init__(self, file_location=None, content=None):
        self.data = OrderedDict()
        if content is not None:
            self._parse(content)
        elif file_location is not None:
            with open(file_location, "r") as f:
                self._parse(f.read())

    def __iter__(self):
        return self.data.__iter__()

    def iteritems(self):
        return six.iteritems(self.data)

    def get(self, version):
        return self.data.get(version)

    def get_changes(self, start_version, end_version=None):
        versions = list(self.data.keys())

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
        changes = defaultdict(list)
        for release in newer_releases:
            for key, entries in self.data[release].items():
                changes[key].extend(entries)
        result = []
        for key in HEADINGS + ["other"]:
            if key in changes:
                if key != "other":
                    result.append(key)
                result.extend(changes.pop(key))
        return result

    def latest(self):
        if list(self.data.items()):
            return list(self.data.items())[0]
        return None

    def _parse(self, content):
        tree = publish_doctree(content)

        def is_valid_version_section(x):
            if x.tagname == "section":
                try:
                    LooseVersion(x["names"][0].split()[0])
                except (ValueError, IndexError):
                    pass
                else:
                    return True
            return False

        def heading(x):
            if x.tagname != "paragraph":
                return ""
            if x.rawsource in HEADINGS:
                return x.rawsource
            # Might be an old heading or unknown.
            return OLD_HEADING_MAPPING.get(x.rawsource, "")

        def is_list_item(x):
            return x.tagname == "list_item"

        found_sections = tree.traverse(condition=is_valid_version_section)
        for section in found_sections:
            version = section["names"][0].split()[0]
            # Look for paragraph headings.
            # When two are found, we have a section with:
            # paragraph 1, bullet_list 1, paragraph 2, bullet_list 2.
            # But a single bullet_list is handled fine too.
            # Put items in dictionary, with the headings as possible keys.
            entries = defaultdict(list)
            current = "other"
            for child in section.children:
                child_heading = heading(child)
                if child_heading:
                    current = child_heading
                    continue
                list_items = child.traverse(condition=is_list_item)
                entries[current] = [a.rawsource.strip() for a in list_items]
            self.data[version] = entries


def build_unified_changelog(start_version, end_version):
    try:
        prior_versions = pull_versions(start_version)
        current_versions = pull_versions(end_version)
    except ValueError as e:
        print(e)
        return

    output_str = u""
    try:
        for package, version in six.iteritems(current_versions):
            if package in prior_versions:
                prior_version = prior_versions[package]
                try:
                    if version > prior_version:
                        print("{0} has a newer version".format(package))
                        packageChange = u"{0}: {1} {2} {3}".format(
                            package, prior_version, u"\u2192", version
                        )
                        output_str += (
                            u"\n"
                            + packageChange
                            + u"\n"
                            + u"-" * len(packageChange)
                            + "\n"
                        )

                        logtext = get_changelog(package)
                        if not logtext:
                            print("No changelog found.")
                            continue
                        changelog = Changelog(content=logtext)
                        try:
                            changes = changelog.get_changes(prior_version, version)
                        except ValueError as e:
                            print(e)
                        else:
                            bullet = u"- "
                            for change in changes:
                                if change in HEADINGS:
                                    output_str += change + u"\n\n"
                                else:
                                    change = change.replace(
                                        "\n", "\n" + " " * len(bullet)
                                    )
                                    output_str += bullet + change + u"\n\n"
                except AttributeError as e:
                    # Bad version line, skip
                    pass
                except TypeError:
                    # (Pdb) version > prior_version
                    # *** TypeError: '<' not supported between instances of 'int' and 'str'
                    # (Pdb) version, prior_version
                    # (LooseVersion ('5.2.0'), LooseVersion ('5.2a1'))
                    print("ERROR {0}: cannot compare prior version {1} with new version {2}".format(
                        package, prior_version, version)
                    )
    except KeyboardInterrupt:
        pass
    print(output_str)
