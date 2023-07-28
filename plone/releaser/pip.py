from .utils import update_contents
from collections import UserDict
from configparser import ConfigParser
from configparser import ExtendedInterpolation
from functools import cached_property

import pathlib
import re


def to_bool(value):
    if not isinstance(value, str):
        return bool(value)
    if value.lower() in ("true", "on", "yes", "1"):
        return True
    return False


class ConstraintsFile:
    def __init__(self, file_location):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()

    @cached_property
    def constraints(self):
        """Read the constraints."""
        contents = self.path.read_text()
        constraints = {}
        for line in contents.splitlines():
            line = line.strip()
            if line.startswith("#"):
                continue
            if "==" not in line:
                # We might want to support e.g. '>=', but for now keep it simple.
                continue
            package = line.split("==")[0].strip().lower()
            version = line.split("==")[1].strip()
            # The line could also contain environment markers like this:
            # "; python_version >= '3.0'"
            # But currently I think we really only need the package name,
            # and not even the version.  Let's use the entire rest of the line.
            # Actually, for our purposes, we should ignore lines that have such
            # markers, just like we do in buildout.py:VersionsFile.
            if ";" in version:
                continue
            if package in constraints:
                if constraints[package] != version:
                    print(
                        f"ERROR: {package} is in {self.file_location} with two "
                        f"constraints: '{contraints[package]}' and '{version}'.")
                continue
            constraints[package] = version
        return constraints

    def __contains__(self, package_name):
        return package_name.lower() in self.constraints

    def __getitem__(self, package_name):
        if package_name in self:
            return self.constraints.get(package_name.lower())
        raise KeyError

    def __setitem__(self, package_name, new_version):
        contents = self.path.read_text()
        if not contents.endswith("\n"):
            contents += "\n"
            self.path.write_text(contents)

        newline = f"{package_name}=={new_version}"
        # Look for 'package name==version' on a line of its own,
        # no whitespace, no environment markers.
        line_reg = re.compile(rf"^{package_name.lower()}==[^;]*$")

        def line_check(line):
            return line_reg.match(line)

        # set version in contents.
        new_contents = update_contents(
            contents, line_check, newline, self.file_location
        )
        if contents != new_contents:
            self.path.write_text(new_contents)

    def get(self, package_name, default=None):
        if package_name in self:
            return self.__getitem__(package_name)
        return default

    def set(self, package_name, new_version):
        return self.__setitem__(package_name, new_version)


class IniFile(UserDict):
    """Ini file for mxdev.

    What we want to do here is similar to what we have in buildout.py
    in the CheckoutsFile: remove a package from auto-checkouts.
    For mxdev: set 'use = false'.
    The default is in 'settings': 'default-use'.
    """

    def __init__(self, file_location):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()
        self.config = ConfigParser(
            default_section="settings",
            interpolation=ExtendedInterpolation(),
        )
        with open(self.file_location) as f:
            self.config.read_file(f)
        self.default_use = to_bool(self.config["settings"].get("default-use", True))

    @property
    def data(self):
        checkouts = {}
        for package in self.config.sections():
            use = to_bool(self.config[package].get("use", self.default_use))
            if use:
                # Map from lower case to actual case, so we can find the package.
                checkouts[package.lower()] = package
        return checkouts

    def __contains__(self, package_name):
        return package_name.lower() in self.data

    def __setitem__(self, package_name, enabled=True):
        """Enable or disable a checkout.

        Mostly this will be called to disable a checkout.
        Expected is that default-use is false.
        This means we can remove 'use = true' from the package.

        But let's support the other way around as well:
        when default-use is true, we set 'use = false'.
        """
        stored_package_name = self.data.get(package_name.lower())
        if stored_package_name:
            package_name = stored_package_name
            use = to_bool(self.config[package_name].get("use", self.default_use))
        else:
            use = False
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
        for line in contents.splitlines():
            line = line.rstrip()
            if line == f"[{package_name}]":
                found_package = True
                lines.append(line)
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
                    if self.default_use:
                        # We need to explicitly disable it.
                        lines.append("use = false")
                    print(
                        f"{self.file_location}: {package_name} removed from checkouts."
                    )
                else:
                    if not self.default_use:
                        # We need to explicitly enable it.
                        lines.append("use = true")
                    print(f"{self.file_location}: {package_name} added to checkouts.")
                # We are done with the section for this package name.
                found_package = False
                # We still need to append the original line.
                lines.append(line)
                continue
            # Just a regular line.
            lines.append(line)

        contents = "\n".join(lines) + "\n"
        self.path.write_text(contents)

    def __delitem__(self, package_name):
        return self.__setitem__(package_name, False)

    def add(self, package_name):
        return self.__setitem__(package_name, True)

    def remove(self, package_name):
        # Remove from checkouts.
        return self.__delitem__(package_name)
