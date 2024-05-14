from collections import UserDict

import pathlib


class BaseFile(UserDict):
    def __init__(self, file_location):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()

    @property
    def data(self):
        raise NotImplementedError

    @property
    def lowerkeys(self):
        # Map from lower case key to actual key in the data.
        return {key.lower(): key for key in self.data}

    def __iter__(self):
        return self.data.__iter__()

    def __contains__(self, package_name):
        return package_name.lower() in self.lowerkeys

    def __getitem__(self, package_name):
        # self.data may be a defaultdict, so we cannot use
        # 'return self.data[package_name]'
        if package_name not in self:
            raise KeyError(package_name)
        # The package_name is in the data, but the case might differ.
        if package_name in self.data:
            return self.data[package_name]
        actual_key = self.lowerkeys[package_name.lower()]
        return self.data[actual_key]

    def __setitem__(self, package_name, value):
        raise NotImplementedError

    def __delitem__(self, package_name):
        return self.__setitem__(package_name, False)

    def get(self, package_name, default=None):
        if package_name in self:
            return self.__getitem__(package_name)
        return default

    def set(self, package_name, value):
        return self.__setitem__(package_name, value)

    def add(self, package_name):
        # This only makes sense for files where package_name maps to True or False.
        return self.__setitem__(package_name, True)

    def remove(self, package_name):
        return self.__delitem__(package_name)


class Source:
    """Source definition for mr.developer or mxdev"""

    def __init__(
        self,
        name="",
        protocol=None,
        url=None,
        pushurl=None,
        branch=None,
        path=None,
        egg=True,
    ):
        self.name = name
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
    def create_from_string(cls, name, source_string):
        line_options = source_string.split()
        protocol = line_options.pop(0)
        url = line_options.pop(0)
        # September 2023: mr.developer defaults to master, mxdev to main.
        options = {"name": name, "protocol": protocol, "url": url, "branch": "master"}

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

    @classmethod
    def create_from_section(cls, section):
        options = {
            "name": section.name,
            "protocol": section.get("cvs", "git"),
            "url": section.get("url"),
            "pushurl": section.get("pushurl"),
            # September 2023: mr.developer defaults to master, mxdev to main.
            "branch": section.get("branch", "main"),
            "path": section.get("target"),
            "egg": section.get("install-mode", "") != "skip",
        }
        return cls(**options)

    def __repr__(self):
        return f"<Source name={self.name} protocol={self.protocol} url={self.url} pushurl={self.pushurl} branch={self.branch} path={self.path} egg={self.egg}>"

    def to_section(self):
        contents = [f"[{self.name}]"]
        # { 'branch': '6.0', 'path': 'extra/documentation', 'egg': False}
        if self.protocol != "git":
            contents.append(f"protocol = {self.protocol}")
        contents.append(f"url = {self.url}")
        if self.pushurl:
            contents.append(f"pushurl = {self.pushurl}")
        if self.branch:
            contents.append(f"branch = {self.branch}")
        if not self.egg:
            contents.append("install-mode = skip")
        if self.path:
            contents.append(f"target = {self.path}")
        return "\n".join(contents)

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
