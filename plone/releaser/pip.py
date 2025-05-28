from .base import BaseFile
from .base import Source
from .utils import update_contents
from collections import defaultdict
from collections import OrderedDict
from configparser import ConfigParser
from functools import cached_property

import pathlib
import re


def to_bool(value):
    if not isinstance(value, str):
        return bool(value)
    if value.lower() in ("true", "on", "yes", "1"):
        return True
    return False


class ConstraintsFile(BaseFile):
    def __init__(self, file_location, with_markers=False, read_extends=False):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()
        self.with_markers = with_markers
        self.read_extends = read_extends
        self._extends = []

    @cached_property
    def extends(self):
        # Getting the data fills self._extends.
        _ignored = self.data  # noqa F841
        return self._extends

    @cached_property
    def data(self):
        """Read the constraints."""
        contents = self.path.read_text()
        constraints = defaultdict(dict)
        for line in contents.splitlines():
            line = line.strip()
            if line.startswith("#"):
                continue
            if line.startswith("-c"):
                extend = line[len("-c") :].strip()
                self._extends.append(extend)
                if self.read_extends:
                    # TODO: support downloading
                    assert not extend.startswith("http")
                    # Recursively read the extended files, and include their versions.
                    extended = ConstraintsFile(
                        self.path.parent / extend,
                        with_markers=self.with_markers,
                        read_extends=True,
                    )
                    for package, version in extended.data.items():
                        if not isinstance(version, dict):
                            constraints[package][""] = version
                        else:
                            constraints[package].update(version)
                continue
            if "==" not in line:
                # We might want to support e.g. '>=', but for now keep it simple.
                continue
            package = line.split("==")[0].strip()
            version = line.split("==", 1)[1].strip()
            # The line could also contain environment markers like this:
            # "; python_version >= '3.0'"
            # But currently I think we really only need the package name,
            # and not even the version.  Let's use the entire rest of the line.
            # Actually, for our purposes, we should ignore lines that have such
            # markers, just like we do in buildout.py:VersionsFile.
            if ";" not in version:
                constraints[package][""] = version
                continue
            if not self.with_markers:
                continue
            version, marker = version.split(";")
            version = version.strip()
            marker = marker.strip()
            constraints[package][marker] = version

        # simplify
        for package, version in constraints.items():
            if len(version) == 1 and "" in version.keys():
                constraints[package] = version[""]
                continue

        return constraints

    def __setitem__(self, package_name, new_version):
        contents = self.path.read_text()
        if not contents.endswith("\n"):
            contents += "\n"
            self.path.write_text(contents)

        newline = f"{package_name}=={new_version}"
        # Look for 'package name==version' on a line of its own,
        # no whitespace, no environment markers.
        line_reg = re.compile(rf"^{package_name}==[^;]*$", flags=re.I)

        def line_check(line):
            return line_reg.match(line)

        # set version in contents.
        new_contents = update_contents(
            contents, line_check, newline, self.file_location
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
            for extend in self.extends:
                contents.append(f"-c {extend}")

        for package, version in self.data.items():
            if isinstance(version, str):
                contents.append(f"{package}=={version}")
                continue
            # version is a dict
            for marker, value in version.items():
                line = f"{package}=={value}"
                if marker:
                    line += f"; {marker}"
                contents.append(line)

        contents.append("")
        new_contents = "\n".join(contents)
        self.path.write_text(new_contents)

    def extends_to_buildout(self):
        """Translate our extends data to buildout.

        We assume that all 'extends' lines are files with constraints,
        and that a versions file is at the same place.
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
            extend = extend.replace("constraints", "versions").replace(".txt", ".cfg")
            if parent:
                extend = "/".join([parent, extend])
            new_extends.append(extend)

        return new_extends

    def to_buildout(self, versions_path):
        """Overwrite versions file with our data.

        The strategy is:

        1. Translate our data to versions data.
        2. Ask the versions file to rewrite itself.
        """
        # Import here to avoid circular imports.
        from plone.releaser.buildout import VersionsFile

        versions = VersionsFile(
            versions_path,
            with_markers=self.with_markers,
            read_extends=self.read_extends,
        )
        # Create or empty the versions file.
        versions.path.write_text("")

        # Translate our extends to Buildout.
        versions.extends = self.extends_to_buildout()

        # Translate our version pins to Buildout.
        # Actually nothing specialneeds to happen:
        # Buildout understand the pip markers.
        versions.data = self.data

        # Rewrite the file.
        versions.rewrite()


class MxSourcesFile(BaseFile):
    """Ini file for mxdev.

    What we want to do here is similar to what we have in buildout.py
    in the SourcesFile.
    """

    def __init__(self, file_location):
        super().__init__(file_location)
        self.config = ConfigParser(
            default_section="settings",
        )
        # mxdev itself calls ConfigParser with extra option
        # interpolation=ExtendedInterpolation().
        # This turns a line like 'url = ${settings:plone}/package.git'
        # into 'url = https://github.com/plone/package.git'.
        # In our case we very much want the original line,
        # especially when we do a rewrite of the file.
        with self.path.open() as f:
            self.config.read_file(f)

    @cached_property
    def data(self):
        sources_dict = OrderedDict()
        # I don't think we need to support [sources:marker].
        for package in self.config.sections():
            section = self.config[package]
            sources_dict[package] = Source.create_from_section(section)
        return sources_dict

    @cached_property
    def settings(self):
        return self.config["settings"]

    def __setitem__(self, package_name, enabled=True):
        raise NotImplementedError

    def rewrite(self):
        """Rewrite the file based on the parsed data.

        This will lose comments, and may change the order.
        """
        contents = ["[settings]"]
        for key, value in self.settings.items():
            contents.append(f"{key} = {value}")

        for package in self:
            contents.append("")
            contents.append(self[package].to_section())

        contents.append("")
        new_contents = "\n".join(contents)
        self.path.write_text(new_contents)


class MxCheckoutsFile(BaseFile):
    """Checkouts file for mxdev.

    What we want to do here is similar to what we have in buildout.py
    in the CheckoutsFile: remove a package from auto-checkouts.
    For mxdev: set 'use = false'.
    The default is in 'settings': 'default-use'.
    In fact, we only support 'default-use = false'.
    """

    def __init__(self, file_location):
        super().__init__(file_location)
        self.config = ConfigParser(
            default_section="settings",
        )
        # mxdev itself calls ConfigParser with extra option
        # interpolation=ExtendedInterpolation().
        # This turns a line like 'url = ${settings:plone}/package.git'
        # into 'url = https://github.com/plone/package.git'.
        # In our case we very much want the original line,
        # especially when we do a rewrite of the file.
        with self.path.open() as f:
            self.config.read_file(f)
        _marker = object()
        default_use = self.config["settings"].get("default-use", _marker)
        if default_use is not _marker and to_bool(default_use):
            raise ValueError(
                f"ERROR: {self.file_location}: you must set 'default-use = false'."
            )

    @cached_property
    def data(self):
        checkouts = {}
        for package in self.config.sections():
            use = to_bool(self.config[package].get("use", False))
            if use:
                checkouts[package] = True
        return checkouts

    @cached_property
    def sections(self):
        # If we want to use a package, we must first know that it exists.
        sections = {}
        for package in self.config.sections():
            sections[package] = True
        return sections

    @cached_property
    def settings(self):
        return self.config["settings"]

    @property
    def lowerkeys_section(self):
        # Map from lower case key to actual key in the sections.
        return {key.lower(): key for key in self.sections}

    def append_package(self, package_name, enabled=True):
        """Append a package to the checkouts.

        The caller should have made sure this package is currently
        not in the file.
        """
        contents = self.path.read_text()
        if not contents.endswith("\n"):
            contents += "\n"
        use = "true" if enabled else "false"
        contents += f"\n[{package_name}]\nuse = {use}\n"
        self.path.write_text(contents)
        print(f"{self.file_location}: {package_name} added to checkouts.")

    def __setitem__(self, package_name, enabled=True):
        """Enable or disable a checkout.

        Mostly this will be called to disable a checkout.
        Expected is that default-use is false.
        This means we can remove 'use = true' from the package.

        But let's support the other way around as well:
        when default-use is true, we set 'use = false'.
        """
        stored_package_name = self.lowerkeys_section.get(package_name.lower())
        if not stored_package_name:
            # Package is not known to us.
            if not enabled:
                # The wanted state is the default state, so do nothing.
                print(f"{self.file_location}: {package_name} not in checkouts.")
                return
            self.append_package(package_name, enabled=enabled)
            return
        package_name = stored_package_name
        use = package_name in self
        if use and enabled:
            print(f"{self.file_location}: {package_name} already in checkouts.")
            return
        if not use and not enabled:
            print(f"{self.file_location}: {package_name} not in checkouts.")
            return

        contents = self.path.read_text()
        if not contents.endswith("\n"):
            contents += "\n"
            self.path.write_text(contents)

        lines = []
        found_package = False
        # Add extra line at the end.  This eases parsing and editing the final section.
        orig_lines = contents.splitlines() + ["\n"]
        for line in orig_lines:
            line = line.rstrip()
            if line == f"[{package_name}]":
                found_package = True
                continue
            if not found_package:
                lines.append(line)
                continue
            if line.startswith("use =") or line.startswith("use="):
                # Ignore this line.  We may add a new one a bit further.
                continue
            if line == "" or line.startswith("["):
                # A new section is starting.
                if not enabled:
                    # We do not keep any lines of this section.
                    print(
                        f"{self.file_location}: {package_name} removed from checkouts."
                    )
                else:
                    # We need to explicitly enable it.
                    lines.append("use = true")
                    print(f"{self.file_location}: {package_name} added to checkouts.")
                # We are done with the section for this package name.
                found_package = False
                # We still need to append the original line.
                # But avoid adding multiple empty lines.
                if line or lines[-1]:
                    lines.append(line)
                continue
            # Just a regular line.
            lines.append(line)

        contents = "\n".join(lines)
        self.path.write_text(contents)

    def rewrite(self):
        """Rewrite the file based on the parsed data.

        This will lose comments, and may change the order.
        """
        contents = ["[settings]"]
        for key, value in self.settings.items():
            contents.append(f"{key} = {value}")

        for package in self.data:
            contents.append("")
            contents.append(f"[{package}]")
            contents.append("use = true")

        contents.append("")
        new_contents = "\n".join(contents)
        self.path.write_text(new_contents)
