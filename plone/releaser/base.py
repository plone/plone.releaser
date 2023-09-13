from collections import UserDict

import pathlib


class BaseFile(UserDict):
    def __init__(self, file_location):
        self.file_location = file_location
        self.path = pathlib.Path(self.file_location).resolve()

    @property
    def data(self):
        raise NotImplementedError

    def __iter__(self):
        return self.data.__iter__()

    def __contains__(self, package_name):
        return package_name.lower() in self.data

    def __getitem__(self, package_name):
        if package_name in self:
            return self.data.get(package_name.lower())
        raise KeyError

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
