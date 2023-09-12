from .base import BaseFile
from .utils import update_contents
from collections import defaultdict
from collections import OrderedDict
from configparser import ConfigParser
from configparser import ExtendedInterpolation

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

    def __eq__(self, other):
        return repr(self) == repr(other)


class VersionsFile(BaseFile):
    def __init__(self, file_location, with_markers=False):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()
        self.with_markers = with_markers
        self.markers = set()

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
        config = ConfigParser(interpolation=ExtendedInterpolation(), strict=False)
        with self.path.open() as f:
            config.read_file(f)
        # https://github.com/plone/plone.releaser/issues/42
        if config.has_section("buildout"):
            config["buildout"]["directory"] = os.getcwd()
        versions = defaultdict(list)
        for section in config.sections():
            if section == "versions":
                for package, version in config[section].items():
                    # Note: the package names are lower case.
                    if not self.with_markers:
                        versions[package] = version
                    else:
                        versions[package].append(version)
            if not self.with_markers:
                continue
            parts = section.split(":")
            if len(parts) != 2 or parts[0] != "versions":
                continue
            marker = parts[1]
            self.markers.add(marker)
            for package, version in config[section].items():
                # Note: the package names are lower case.
                versions[package].append((version, marker))

        if self.with_markers:
            # simplify
            for package, version in versions.items():
                if isinstance(version, list) and len(version) == 1:
                    versions[package] = version[0]
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


class SourcesFile(BaseFile):
    @property
    def data(self):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.optionxform = str
        with self.path.open() as f:
            config.read_file(f)
        # We need to define a few extra variables that are in a different
        # buildout file that we do not parse here.
        # See this similar issue in mr.roboto:
        # https://github.com/plone/mr.roboto/issues/89
        config["buildout"]["directory"] = os.getcwd()
        sources_dict = OrderedDict()
        # I don't think we need to support [sources:marker].
        for name, value in config["sources"].items():
            source = Source.create_from_string(value)
            sources_dict[name.lower()] = source
        return sources_dict

    def __setitem__(self, package_name, value):
        raise NotImplementedError


class CheckoutsFile(BaseFile):
    @property
    def data(self):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        with self.path.open() as f:
            config.read_file(f)
        config["buildout"]["directory"] = os.getcwd()
        # I don't think we need to support [buildout:marker].
        checkouts = config.get("buildout", "auto-checkout")
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
