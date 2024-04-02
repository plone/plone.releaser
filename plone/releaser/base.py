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
