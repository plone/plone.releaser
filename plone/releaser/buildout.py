from .utils import update_contents
from collections import OrderedDict
from collections import UserDict
from configparser import ConfigParser
from configparser import ExtendedInterpolation

import pathlib
import os
import re


PATH_RE = re.compile(
    r"(\w+://)(.+@)*([\w\d\.]+)(:[\d]+){0,1}/(?P<path>.+(?=\.git))(\.git)"
)


class Source:
    def __init__(self, protocol=None, url=None, push_url=None, branch=None):
        self.protocol = protocol
        self.url = url
        self.push_url = push_url
        self.branch = branch

    def create_from_string(self, source_string):
        protocol, url, extra_1, extra_2, extra_3 = (
            lambda a, b, c=None, d=None, e=None: (a, b, c, d, e)
        )(*source_string.split())
        for param in [extra_1, extra_2, extra_3]:
            if param is not None:
                key, value = param.split("=")
                setattr(self, key, value)
        self.protocol = protocol
        self.url = url
        if self.push_url is not None:
            self.push_url = self.push_url.split("=")[-1]
        if self.branch is None:
            self.branch = "master"
        else:
            self.branch = self.branch.split("=")[-1]
        return self

    @property
    def path(self):
        if self.url:
            match = PATH_RE.match(self.url)
            if match:
                return match.groupdict()["path"]
        return None


class VersionsFile:
    def __init__(self, file_location):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()

    @property
    def versions(self):
        """Read the versions config.

        We use strict=False to avoid a DuplicateOptionError.
        This happens in coredev 4.3 because we pin 'babel' and 'Babel'.

        We need to combine all versions sections, like these:
        ['versions', 'versions:python27']

        """
        config = ConfigParser(interpolation=ExtendedInterpolation(), strict=False)
        with open(self.file_location) as f:
            config.read_file(f)
        # https://github.com/plone/plone.releaser/issues/42
        if config.has_section("buildout"):
            config["buildout"]["directory"] = os.getcwd()
        versions = {}
        for section in config.sections():
            if "versions" in section.split(":"):
                for package, version in config[section].items():
                    # Note: the package names are lower case.
                    versions[package] = version
        return versions

    def __contains__(self, package_name):
        return package_name.lower() in self.versions

    def __getitem__(self, package_name):
        if package_name in self:
            return self.versions.get(package_name.lower())
        raise KeyError

    def __setitem__(self, package_name, new_version):
        contents = self.path.read_text()
        if not contents.endswith("\n"):
            # Make sure the file ends with a newline.
            contents += "\n"
            self.path.write_text(contents)

        newline = f"{package_name} = {new_version}"
        # if package_name not in self:
        #     contents += newline + "\n"
        #     print(f"{self.file_location}: '{newline}' added.")
        #     self.path.write_text(contents)
        #     return

        line_reg = re.compile(rf"^{package_name.lower()} *=.*")

        def line_check(line):
            # Look for the 'package name = version' on a line of its own,
            # no whitespace in front.  Maybe whitespace in between.
            return line_reg.match(line)

        def stop_check(line):
            # If we see this line, we should stop trying to match.
            return line.startswith("[versionannotations]") or line.startswith(
                "[versions:"
            )

        # set version in contents.
        new_contents = update_contents(
            contents, line_check, newline, self.file_location, stop_check=stop_check
        )
        if contents != new_contents:
            self.path.write_text(new_contents)

    def get(self, package_name):
        return self.__getitem__(package_name)

    def set(self, package_name, new_version):
        return self.__setitem__(package_name, new_version)


class SourcesFile(UserDict):
    def __init__(self, file_location):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()

    @property
    def data(self):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.optionxform = str
        with open(self.file_location) as f:
            config.read_file(f)
        # We need to define a few extra variables that are in a different
        # buildout file that we do not parse here.
        # See this similar issue in mr.roboto:
        # https://github.com/plone/mr.roboto/issues/89
        config["buildout"]["directory"] = os.getcwd()
        config["buildout"]["docs-directory"] = os.path.join(os.getcwd(), "docs")
        sources_dict = OrderedDict()
        for name, value in config["sources"].items():
            try:
                source = Source().create_from_string(value)
            except TypeError:
                # Happens now for the documentation items in coredev 6.0.
                # We could print, but this gets printed a lot.
                continue
            sources_dict[name] = source
        return sources_dict

    def __setitem__(self, package_name, value):
        raise NotImplementedError

    def __iter__(self):
        return self.data.__iter__()


class CheckoutsFile(UserDict):
    def __init__(self, file_location):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()

    @property
    def data(self):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        with open(self.file_location) as f:
            config.read_file(f)
        config["buildout"]["directory"] = os.getcwd()
        checkouts = config.get("buildout", "auto-checkout")
        # Map from lower case to actual case, so we can find the package.
        mapping = {}
        for package in checkouts.splitlines():
            mapping[package.lower()] = package
        return mapping

    def __contains__(self, package_name):
        return package_name.lower() in self.data

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

    def __delitem__(self, package_name):
        return self.__setitem__(package_name, False)

    def add(self, package_name):
        return self.__setitem__(package_name, True)

    def remove(self, package_name):
        # Remove from checkouts.cfg
        return self.__delitem__(package_name)


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
