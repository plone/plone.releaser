import pathlib
import re


class ConstraintsFile:
    def __init__(self, file_location):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()

    @property
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
            # The line could also contain identifiers like this:
            # "; python_version >= '3.0'"
            # But currently I think we really only need the package name,
            # and not even the version.  Let's use the entire rest of the line.
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

        # Should we use '==' or ' == '?  Use spaces when more than half already
        # uses them.
        newline = f"{package_name}=={new_version}"
        if contents.count(" == ") > contents.count("==") / 2:
            newline = newline.replace("==", " == ")
        if package_name not in self:
            contents += newline + "\n"

        reg = re.compile(
            rf"^{package_name} ?==.*$",
            re.MULTILINE,
        )
        new_contents = reg.sub(newline, contents)
        self.path.write_text(new_contents)

    def get(self, package_name):
        return self.__getitem__(package_name)

    def set(self, package_name, new_version):
        return self.__setitem__(package_name, new_version)
