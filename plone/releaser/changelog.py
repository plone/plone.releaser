from collections import defaultdict
from collections import OrderedDict
from docutils.core import publish_doctree
from itertools import product
from packaging.version import InvalidVersion
from packaging.version import parse
from plone.releaser.buildout import Buildout
from plone.releaser.release import HEADINGS
from plone.releaser.release import OLD_HEADING_MAPPING
from urllib.request import urlopen

import re


DIST_URL = "https://dist.plone.org/release/{0}/versions.cfg"
MD_HEADING_RE = re.compile(r"## (\S*).*")
MD_SUB_HEADING_RE = re.compile(r"### (.*)")
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
        if not isinstance(line, str):
            line = line.decode("utf-8")
        line = line.strip().replace(" ", "")
        if line and not (line.startswith("#") or line.startswith("[")):
            try:
                package, version = line.split("=")
            except ValueError:
                continue
            if not version:
                # May be a line from versionannotation
                continue
            try:
                version = parse(version)
            except InvalidVersion:
                pass
            package_versions[package] = version
    print(f"Parsed {url}")
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
    file_extensions = [".rst", ".md", ".txt"]
    if "github" in source_url:
        paths = [f"{branch}/", f"{branch}/docs/"]
    else:
        paths = ["/", "/docs/", "/".join(package_name.split(".")) + "/"]
    for pathable in product(paths, file_names, file_extensions):
        structure = "".join(pathable)
        url = f"{source_url}/{structure}"
        try:
            response = urlopen(url)
        except OSError:
            print(f"Unable to reach {url}")
        else:
            if response.code == 200:
                return response.read()
    return ""


class Changelog:
    def __init__(self, file_location=None, content=None):
        self.file_location = file_location
        self.content = content
        self.data = OrderedDict()
        if content is not None:
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            self._parse(content)
        elif file_location is not None:
            with open(file_location) as f:
                self._parse(f.read())

    def __iter__(self):
        return self.data.__iter__()

    def __eq__(self, other):
        return self.data == other.data

    def iteritems(self):
        return self.data.items()

    def get(self, version):
        return self.data.get(version)

    def get_changes(self, start_version, end_version=None):
        versions = list(self.data.keys())

        end_version_index = 0
        if end_version is not None:
            try:
                end_version_index = versions.index(str(end_version))
            except ValueError:
                raise ValueError(
                    f"End version {end_version} not found in changelog contents."
                )
        try:
            start_version_index = versions.index(str(start_version))
        except ValueError:
            raise ValueError(
                f"Start version {start_version} not found in changelog contents."
            )

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

    def _parse_rst(self, content):
        tree = publish_doctree(content)

        def is_valid_version_section(x):
            if x.tagname == "section":
                try:
                    parse(x["names"][0].split()[0])
                except (InvalidVersion, ValueError, IndexError):
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
            return OLD_HEADING_MAPPING.get(x.rawsource, "other")

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

    def _parse_md(self, content):
        # Parse as markdown.
        # I thought of using markdown-it-py, but I don't find it intuitive
        # enough for our use case.  So try it "by hand".

        def heading(text):
            if text in HEADINGS:
                return text
            # Might be an old heading or unknown.
            return OLD_HEADING_MAPPING.get(text, "other")

        version = None
        current = "other"
        entries = defaultdict(list)
        list_item = None
        for line in content.splitlines():
            if not line.strip():
                continue
            match = MD_HEADING_RE.match(line)
            if match:
                if list_item:
                    # add previous list item
                    entries[current].append(list_item)
                if version:
                    # Store the previous version
                    self.data[version] = entries
                list_item = None
                entries = defaultdict(list)
                current = "other"
                version = match.groups()[0]
                continue
            if not version:
                continue
            match = MD_SUB_HEADING_RE.match(line)
            if match:
                if list_item:
                    # add previous list item
                    entries[current].append(list_item)
                list_item = None
                text = match.groups()[0]
                child_heading = heading(text)
                if child_heading:
                    current = child_heading
                continue
            # Now look for the real entries: list items.
            if line.startswith("- ") or line.startswith("* "):
                if list_item:
                    # add previous list item
                    entries[current].append(list_item)
                # start new list item
                list_item = line[2:]
                continue
            if list_item:
                list_item += "\n" + line.strip()
        if list_item:
            # Store the last list item.
            entries[current].append(list_item)
        if version:
            # Store the last version.
            self.data[version] = entries

    def _parse(self, content):
        # Try to parse as restructuredtext.
        self._parse_rst(content)
        if not self.data:
            # Try to parse as markdown.
            self._parse_md(content)


def build_unified_changelog(start_version, end_version, packages=None):
    try:
        prior_versions = pull_versions(start_version)
        current_versions = pull_versions(end_version)
    except ValueError as e:
        print(e)
        return

    if isinstance(packages, str):
        packages = packages.split(",")

    output_str = ""
    try:
        for package, version in current_versions.items():
            if packages is not None and package not in packages:
                # We are not interested in this package.
                continue
            if package in prior_versions:
                prior_version = prior_versions[package]
                try:
                    if version > prior_version:
                        print(f"{package} has a newer version")
                        packageChange = "{}: {} {} {}".format(
                            package, prior_version, "\u2192", version
                        )
                        output_str += (
                            "\n"
                            + packageChange
                            + "\n"
                            + "-" * len(packageChange)
                            + "\n"
                        )

                        logtext = get_changelog(package)
                        if not logtext:
                            print("WARNING: No changelog found.")
                            continue
                        changelog = Changelog(content=logtext)
                        try:
                            changes = changelog.get_changes(prior_version, version)
                        except ValueError as e:
                            print(f"ERROR: {e}")
                        else:
                            bullet = "- "
                            for change in changes:
                                if change in HEADINGS:
                                    output_str += change + "\n\n"
                                else:
                                    change = change.replace(
                                        "\n", "\n" + " " * len(bullet)
                                    )
                                    output_str += bullet + change + "\n\n"
                except AttributeError:
                    # Bad version line, skip
                    pass
                except TypeError:
                    # (Pdb) version > prior_version
                    # *** TypeError: '<' not supported between instances of 'int' and 'str'
                    # (Pdb) version, prior_version
                    # (LooseVersion ('5.2.0'), LooseVersion ('5.2a1'))
                    print(
                        "ERROR {}: cannot compare prior version {} with new version {}".format(
                            package, prior_version, version
                        )
                    )
    except KeyboardInterrupt:
        pass
    print(output_str)
