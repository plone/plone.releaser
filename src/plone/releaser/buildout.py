from .base import BaseFile
from .base import Source
from .utils import buildout_marker_to_pip_marker
from .utils import update_contents
from collections import defaultdict
from collections import OrderedDict
from configparser import ConfigParser
from configparser import ExtendedInterpolation
from functools import cached_property
from textwrap import indent

import os
import pathlib
import re


class BaseBuildoutFile(BaseFile):
    def __init__(self, file_location, with_markers=False, read_extends=False):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()
        self.with_markers = with_markers
        self.markers = set()
        self.read_extends = read_extends

    @cached_property
    def config(self):
        # For versions.cfg we had strict=False, for the others not.
        # Let's use it always.
        config = ConfigParser(interpolation=ExtendedInterpolation(), strict=False)
        # Preserve the case instead of the default lowercase transform:
        config.optionxform = str
        with self.path.open() as f:
            config.read_file(f)
        # Especially in sources.cfg we may need to define a few extra variables
        # that are in a different buildout file that we do not parse here.
        # See this similar issue in mr.roboto:
        # https://github.com/plone/mr.roboto/issues/89
        if not config.has_section("buildout"):
            config.add_section("buildout")
        if not config.has_option("buildout", "directory"):
            config["buildout"]["directory"] = os.getcwd()
        return config

    @cached_property
    def raw_config(self):
        # Read the same data, but without interpolation.
        # So keep a url like '${settings:plone}/package.git'
        config = ConfigParser(strict=False)
        # Preserve the case instead of the default lowercase transform:
        config.optionxform = str
        with self.path.open() as f:
            config.read_file(f)
        return config

    @property
    def extends(self):
        if hasattr(self, "_extends"):
            # Our setter has been called, presumably in preparation for a rewrite.
            return self._extends
        if self.config.has_section("buildout"):
            return self.config["buildout"].get("extends", "").strip().splitlines()
        return []

    @extends.setter
    def extends(self, values):
        self._extends = values


class VersionsFile(BaseBuildoutFile):
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
        if hasattr(self, "_data"):
            # Our setter has been called, presumably in preparation for a rewrite.
            return self._data
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
                    # Note: the package names used to be lower case, but not anymore.
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

    @data.setter
    def data(self, versions):
        self._data = versions

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
            contents = ["[buildout]"]
            if len(self.extends) == 1:
                contents.append(f"extends = {self.extends[0]}")
            else:
                contents.append("extends =")
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

    def extends_to_pip(self):
        """Translate our extends data to pip.

        We assume that all 'extends' lines are files with versions,
        and that a constraints file is at the same place.
        """
        if not self.extends:
            return []
        if self.read_extends:
            # We incorporate the versions of the extended files in our own,
            # so we do not need the extends.
            return []

        new_extends = []
        for extend in self.extends:
            parts = extend.split("/")
            parent = "/".join(parts[:-1])
            extend = parts[-1]
            extend = extend.replace("versions", "constraints").replace(".cfg", ".txt")
            if parent:
                extend = "/".join([parent, extend])
            new_extends.append(extend)

        return new_extends

    def pins_to_pip(self):
        """Translate our version pins to pip.

        There is just one thing to do: translate buildout-specific markers
        to ones that pip understands.
        Note that the other way around is no problem: Buildout can meanwhile
        understand the pip markers.

        An option would be to always do this for Buildout as well.
        Or have a command to normalize a buildout file, with this and other
        small changes.
        """
        new_data = {}
        for package, version in self.data.items():
            if isinstance(version, str):
                new_data[package] = version
                continue
            # version is a dict
            new_version = {}
            for marker, value in version.items():
                if not marker:
                    new_version[marker] = value
                    continue
                # If this is a Buildout-specific marker, we need to translate it.
                new_marker = buildout_marker_to_pip_marker(marker)
                new_version[new_marker] = value
            new_data[package] = new_version
        return new_data

    def to_pip(self, constraints_path):
        """Overwrite constraints file with our data.

        The strategy is:

        1. Translate our data to constraints data.
        2. Ask the constraints file to rewrite itself.
        """
        # Import here to avoid circular imports.
        from plone.releaser.pip import ConstraintsFile

        constraints = ConstraintsFile(
            constraints_path,
            with_markers=self.with_markers,
            read_extends=self.read_extends,
        )
        # Create or empty the constraints file.
        constraints.path.write_text("")

        # Translate our extends to pip.
        constraints.extends = self.extends_to_pip()

        # Translate our version pins to pip.
        constraints.data = self.pins_to_pip()

        # Rewrite the file.
        constraints.rewrite()


class SourcesFile(BaseBuildoutFile):
    @property
    def data(self):
        sources_dict = OrderedDict()
        # I don't think we need to support [sources:marker].
        for name, value in self.config["sources"].items():
            source = Source.create_from_string(name, value)
            sources_dict[name] = source
        return sources_dict

    @property
    def raw_data(self):
        sources_dict = OrderedDict()
        # I don't think we need to support [sources:marker].
        for name, value in self.raw_config["sources"].items():
            source = Source.create_from_string(name, value)
            sources_dict[name] = source
        return sources_dict

    def __setitem__(self, package_name, value):
        raise NotImplementedError

    def rewrite(self):
        """Rewrite the file based on the parsed data.

        This will lose comments, and may change the order.
        """
        contents = []
        # First rewrite all existing sections except [sources].
        for part, section in self.raw_config.items():
            if part in ("sources", "DEFAULT"):
                continue
            contents.append(f"[{part}]")
            for key, value in section.items():
                if value.startswith("\n"):
                    contents.append(f"{key} =")
                    value = indent(value.strip(), "    ")
                    contents.append(value)
                else:
                    contents.append(f"{key} = {value}")
            contents.append("")

        # Now handle the sources.
        contents.append("[sources]")
        for name, source in self.raw_data.items():
            contents.append(f"{name} = {str(source)}")

        contents.append("")
        new_contents = "\n".join(contents)
        self.path.write_text(new_contents)

    def to_pip(self, pip_path):
        """Overwrite mxdev/pip sources file with our data.

        The strategy is:

        1. Translate our data to mxdev sources data.
        2. Ask the msdev sources file to rewrite itself.
        """
        # Import here to avoid circular imports.
        from plone.releaser.pip import MxSourcesFile

        sources = MxSourcesFile(pip_path)
        # Create or empty the sources file.
        sources.path.write_text("")

        # Translate our data to pip.
        sources.data = self.raw_data
        if "remotes" in self.config:
            remotes = self.config["remotes"]
            for key, value in remotes.items():
                sources.settings[key] = value
            for source in sources.data.values():
                source.url = source.url.replace("{remotes:", "{settings:")
                if source.pushurl:
                    source.pushurl = source.pushurl.replace("{remotes:", "{settings:")
                if source.path:
                    source.path = source.path.replace("{buildout:", "{settings:")

        # Rewrite the file.
        sources.rewrite()


class CheckoutsFile(BaseBuildoutFile):
    @property
    def always_checkout(self):
        return self.config.get("buildout", "always-checkout")

    @property
    def data(self):
        # I don't think we need to support [buildout:marker].
        checkouts = self.config.get("buildout", "auto-checkout")
        # In this case a set or list would be fine, but in all other
        # cases the data is a dictionary, so let's use that.
        mapping = {}
        for package in checkouts.splitlines():
            if not package:
                continue
            mapping[package] = True
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
        for package in self:
            contents.append(f"    {package}")
        contents.append("")
        new_contents = "\n".join(contents)
        self.path.write_text(new_contents)

    def to_pip(self, pip_path):
        """Overwrite mxdev/pip checkouts file with our data.

        The strategy is:

        1. Translate our data to mxdev checkouts data.
        2. Ask the msdev checkouts file to rewrite itself.
        """
        # Import here to avoid circular imports.
        from plone.releaser.pip import MxCheckoutsFile

        checkouts = MxCheckoutsFile(pip_path)
        # Create or empty the checkouts file.
        checkouts.path.write_text("")

        # Translate our data to pip.
        # XXX does not do anything
        checkouts.data = self.data
        # This is the only setting that makes sense for Plone coredev:
        checkouts.settings = {"default-use": "false"}

        # Rewrite the file.
        checkouts.rewrite()


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
