# -*- coding: utf-8 -*-
from collections import OrderedDict
from configparser import ConfigParser
from configparser import ExtendedInterpolation

import os
import re

try:
    from collections import UserDict
except ImportError:
    from UserDict import UserDict

PATH_RE = re.compile(
    "(\w+://)(.+@)*([\w\d\.]+)(:[\d]+){0,1}/(?P<path>.+(?=\.git))(\.git)"
)


class Source(object):
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


class VersionsFile(object):
    def __init__(self, file_location):
        self.file_location = file_location

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
        path = os.path.join(os.getcwd(), self.file_location)
        with open(path, "r") as f:
            versionstxt = f.read()

        if package_name not in self:
            newline = "{0} = {1}".format(package_name, new_version)
            versionstxt += newline

        reg = re.compile(
            "(^{0}[\s\=]+)[0-9\.abrc]+(.post\d+)?(.dev\d+)?".format(package_name),
            re.MULTILINE,
        )
        newVersionsTxt = reg.sub(r"\g<1>{0}".format(new_version), versionstxt)
        with open(path, "w") as f:
            f.write(newVersionsTxt)

    def get(self, package_name):
        return self.__getitem__(package_name)

    def set(self, package_name, new_version):
        return self.__setitem__(package_name, new_version)


class SourcesFile(UserDict):
    def __init__(self, file_location):
        self.file_location = file_location

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

    @property
    def data(self):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        with open(self.file_location) as f:
            config.read_file(f)
        config["buildout"]["directory"] = os.getcwd()
        checkouts = config.get("buildout", "auto-checkout")
        checkout_list = checkouts.split("\n")
        return checkout_list

    def __contains__(self, package_name):
        return package_name in self.data

    def __setitem__(self, package_name, enabled=True):
        path = os.path.join(os.getcwd(), self.file_location)
        with open(path, "r") as f:
            checkoutstxt = f.read()
        with open(path, "w") as f:
            if not checkoutstxt.endswith("\n"):
                # Make sure the file ends with a newline.
                checkoutstxt += "\n"
            # Look for the package name on a line of its own,
            # with likely whitespace in front.
            reg = re.compile(r"^[\s]*{0}\n".format(package_name), re.MULTILINE)
            if enabled:
                # We used to look for "# test-only fixes:" here,
                # and place the checkout before it.
                # But this text is no longer in any current checkouts.cfg.
                if not reg.match(checkoutstxt):
                    # It is indeed not yet in the checkouts.
                    newCheckoutsTxt = checkoutstxt + "    {0}\n".format(package_name)
            else:
                # Remove the package name
                newCheckoutsTxt = reg.sub("", checkoutstxt)
            f.write(newCheckoutsTxt)

    def __delitem__(self, package_name):
        return self.__setitem__(package_name, False)

    def add(self, package_name):
        return self.__setitem__(package_name, True)

    def remove(self, package_name):
        # Remove from checkouts.cfg
        return self.__delitem__(package_name)


class Buildout(object):
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
