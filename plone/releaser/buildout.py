from .base import BaseFile
from .utils import update_contents
from collections import defaultdict
from collections import OrderedDict
from configparser import ConfigParser
from configparser import ExtendedInterpolation
from functools import cached_property

import os
import pathlib
import re


class Source:
    """Source definition for mr.developer"""

    def __init__(
        self, protocol=None, url=None, pushurl=None, branch=None, path=None, egg=True
    ):
        # I think mxdev only supports git as protocol.
        self.protocol = protocol
        self.url = url
        self.pushurl = pushurl
        self.branch = branch
        # mxdev has target (default: sources) instead of path (default: src).
        self.path = path
        # egg=True: mxdev install-mode="direct"
        # egg=False: mxdev install-mode="skip"
        self.egg = egg

    @classmethod
    def create_from_string(cls, source_string):
        line_options = source_string.split()
        protocol = line_options.pop(0)
        url = line_options.pop(0)
        # September 2023: mr.developer defaults to master, mxdev to main.
        options = {"protocol": protocol, "url": url, "branch": "master"}

        # The rest of the line options are key/value pairs.
        for param in line_options:
            if param is not None:
                key, value = param.split("=")
                if key == "egg":
                    if value.lower() in ("true", "yes", "on"):
                        value = True
                    elif value.lower() in ("false", "no", "off"):
                        value = False
                options[key] = value
        return cls(**options)

    def __repr__(self):
        return f"<Source {self.protocol} url={self.url} pushurl={self.pushurl} branch={self.branch} path={self.path} egg={self.egg}>"

    def __str__(self):
        line = f"{self.protocol} {self.url}"
        if self.pushurl:
            line += f" pushurl={self.pushurl}"
        if self.branch:
            line += f" branch={self.branch}"
        if self.path:
            line += f" path={self.path}"
        if not self.egg:
            line += " egg=false"
        return line

    def __eq__(self, other):
        return repr(self) == repr(other)


class VersionsFile(BaseFile):
    def __init__(self, file_location, with_markers=False, read_extends=False):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()
        self.with_markers = with_markers
        self.markers = set()
        self.read_extends = read_extends

    @cached_property
    def config(self):
        config = ConfigParser(interpolation=ExtendedInterpolation(), strict=False)
        with self.path.open() as f:
            config.read_file(f)
        return config

    @property
    def extends(self):
        if self.config.has_section("buildout"):
            return self.config["buildout"].get("extends", "").strip().splitlines()
        return []

    @property
    def data(self):
        """Read the versions config.

        We use strict=False to avoid a DuplicateOptionError.
        This happens in coredev 4.3 because we pin 'babel' and 'Babel'.

        We used to combine all versions sections, like these:
        ['versions', 'versions:python27']
        That fixed https://github.com/plone/plone.releaser/issues/24
        and was needed when we had packages like Archetypes which were only for
        Python 2.  With Plone 6 I don't think we will need this.  We can still
        have Python-version-specific sections, but that would be for external
        packages.  I don't think we will be releasing Plone packages that are
        for specific Python versions.  Or if we do, it would be overkill for
        plone.releaser to support such a corner case.

        So we do not want to report or edit anything except the versions section.

        Ah, but we *do* need this information when translating to pip.
        For that: set self.with_markers = True.
        """
        versions = defaultdict(dict)
        if self.config.has_section("buildout"):
            # https://github.com/plone/plone.releaser/issues/42
            self.config["buildout"]["directory"] = os.getcwd()
            if self.read_extends:
                # Recursively read the extended files, and include their versions.
                for extend in self.extends:
                    # TODO: support downloading
                    assert not extend.startswith("http")
                    extended = VersionsFile(
                        self.path.parent / extend,
                        with_markers=self.with_markers,
                        read_extends=True,
                    )
                    for package, version in extended.data.items():
                        if not isinstance(version, dict):
                            versions[package][""] = version
                        else:
                            versions[package].update(version)

        for section in self.config.sections():
            if section == "versions":
                for package, version in self.config[section].items():
                    # Note: the package names are lower case.
                    versions[package][""] = version
            if not self.with_markers:
                continue
            parts = section.split(":")
            if len(parts) != 2 or parts[0] != "versions":
                continue
            marker = parts[1]
            self.markers.add(marker)
            for package, version in self.config[section].items():
                versions[package][marker] = version

        # simplify
        for package, version in versions.items():
            if len(version) == 1 and "" in version.keys():
                versions[package] = version[""]
                continue
        return versions

    def __setitem__(self, package_name, new_version):
        contents = self.path.read_text()
        if not contents.endswith("\n"):
            # Make sure the file ends with a newline.
            contents += "\n"
            self.path.write_text(contents)

        if isinstance(new_version, tuple):
            new_version, marker = new_version
            section = f"[versions:{marker}]"
            if marker not in self.markers:
                contents = f"{contents}\n{section}\n"
                self.path.write_text(contents)
        else:
            section = "[versions]"
        newline = f"{package_name} = {new_version}"
        # Search case insensitively.
        line_reg = re.compile(rf"^{package_name} *=.*", flags=re.I)

        def line_check(line):
            # Look for the 'package name = version' on a line of its own,
            # no whitespace in front.  Maybe whitespace in between.
            return line_reg.match(line)

        def start_check(line):
            # If we see this line, we start trying to match.
            return line == section

        def stop_check(line):
            # If we see this line, we should stop trying to match.
            return line.startswith("[")

        # set version in contents.
        new_contents = update_contents(
            contents,
            line_check,
            newline,
            self.file_location,
            start_check=start_check,
            stop_check=stop_check,
        )
        if contents != new_contents:
            self.path.write_text(new_contents)

    def rewrite(self):
        """Rewrite the file based on the parsed data.

        This will lose comments, and may change the order.
        """
        contents = []
        if self.extends and not self.read_extends:
            # With read_extends=True, we incorporate the versions of the
            # extended files in our own, so we no longer need the extends.
            contents = ["[buildout]", "extends ="]
            for extend in self.extends:
                contents.append(f"    {extend}")
            contents.append("")

        contents.append("[versions]")
        markers = defaultdict(list)
        for package, version in self.data.items():
            if isinstance(version, str):
                contents.append(f"{package} = {version}")
                continue
            # version is a dict
            for marker, value in version.items():
                if not marker:
                    # add to current [versions]
                    contents.append(f"{package} = {value}")
                    continue
                # add to markers to write at the end
                markers[marker].append((package, value))

        for marker, entries in markers.items():
            contents.append("")
            contents.append(f"[versions:{marker}]")
            for package, version in entries:
                contents.append(f"{package} = {version}")

        contents.append("")
        new_contents = "\n".join(contents)
        self.path.write_text(new_contents)


class SourcesFile(BaseFile):
    @cached_property
    def config(self):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.optionxform = str
        with self.path.open() as f:
            config.read_file(f)
        # We need to define a few extra variables that are in a different
        # buildout file that we do not parse here.
        # See this similar issue in mr.roboto:
        # https://github.com/plone/mr.roboto/issues/89
        config["buildout"]["directory"] = os.getcwd()
        return config

    @cached_property
    def raw_config(self):
        # Read the same data, but without interpolation.
        # So keep a url like '${settings:plone}/package.git'
        config = ConfigParser()
        config.optionxform = str
        with self.path.open() as f:
            config.read_file(f)
        return config

    @property
    def extends(self):
        if self.config.has_section("buildout"):
            return self.config["buildout"].get("extends", "").strip().splitlines()
        return []

    @property
    def data(self):
        sources_dict = OrderedDict()
        # I don't think we need to support [sources:marker].
        for name, value in self.config["sources"].items():
            source = Source.create_from_string(value)
            sources_dict[name.lower()] = source
        return sources_dict

    @property
    def raw_data(self):
        sources_dict = OrderedDict()
        # I don't think we need to support [sources:marker].
        for name, value in self.raw_config["sources"].items():
            source = Source.create_from_string(value)
            sources_dict[name.lower()] = source
        return sources_dict

    def __setitem__(self, package_name, value):
        raise NotImplementedError

    def rewrite(self):
        """Rewrite the file based on the parsed data.

        This will lose comments, and may change the order.
        """
        contents = []
        # TODO add [buildout], extends, docs-directory.
        # Definitions of remotes could be good.
        # But we might skip this all, as it is a one-off exercise.
        # Or keep all existing text until [sources].
        contents.append("[buildout]")
        contents.append("")
        contents.append("[sources]")
        for name, source in self.raw_data.items():
            contents.append(f"{name} = {str(source)}")

        contents.append("")
        new_contents = "\n".join(contents)
        self.path.write_text(new_contents)


class CheckoutsFile(BaseFile):
    @cached_property
    def config(self):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        with self.path.open() as f:
            config.read_file(f)
        config["buildout"]["directory"] = os.getcwd()
        return config

    @property
    def always_checkout(self):
        return self.config.get("buildout", "always-checkout")

    @property
    def data(self):
        # I don't think we need to support [buildout:marker].
        checkouts = self.config.get("buildout", "auto-checkout")
        # Map from lower case to actual case, so we can find the package.
        mapping = {}
        for package in checkouts.splitlines():
            if not package:
                continue
            mapping[package.lower()] = package
        return mapping

    def __setitem__(self, package_name, enabled=True):
        contents = self.path.read_text()
        if not contents.endswith("\n"):
            # Make sure the file ends with a newline.
            contents += "\n"
            self.path.write_text(contents)

        def line_check(line):
            # Look for the package name on a line of its own,
            # with likely whitespace in front.
            return line.strip().lower() == package_name.lower()

        # add or remove the package name from the contents.
        newline = f"    {package_name}" if enabled else None
        new_contents = update_contents(
            contents, line_check, newline, self.file_location
        )
        if contents != new_contents:
            self.path.write_text(new_contents)

    def set(self, package_name, new_version):
        # This method makes no sense for this class.
        raise NotImplementedError

    def rewrite(self):
        """Rewrite the file based on the parsed data.

        This will lose comments, and may change the order.
        """
        contents = ["[buildout]"]
        if self.always_checkout:
            contents.append(f"always-checkout = {self.always_checkout}"),
        contents.append("auto-checkout =")
        # self.values has the original case.
        # We could iterate over 'self' to get lowercase,
        # which is what we get in most other places.
        # But for now let's use the info we have.
        for package in self.values():
            contents.append(f"    {package}")
        contents.append("")
        new_contents = "\n".join(contents)
        self.path.write_text(new_contents)


class Buildout:
    def __init__(
        self,
        sources_file="sources.cfg",
        checkouts_file="checkouts.cfg",
        versions_file="versions.cfg",
    ):
        self.sources = SourcesFile(sources_file)
        self.versions = VersionsFile(versions_file)
        self.checkouts = CheckoutsFile(checkouts_file)

    def add_to_checkouts(self, package_name):
        return self.checkouts.add(package_name)

    def remove_from_checkouts(self, package_name):
        return self.checkouts.remove(package_name)

    def get_version(self, package_name):
        return self.versions.get(package_name)

    def set_version(self, package_name, new_version):
        return self.versions.set(package_name, new_version)
