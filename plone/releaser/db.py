# -*- coding: utf-8 -*-
import json
import os


class IgnoresDB(object):

    def __init__(self):
        self._filename = '.package_ignores'
        if not os.path.isfile(self._filename):
            open(self._filename, 'w').close()

        with open(self._filename, 'r') as f:
            content = f.read()
            if content != '':
                self._db = json.loads(content)
            else:
                self._db = {}

    def save(self):
        with open(self._filename, 'w+') as f:
            f.write(json.dumps(self._db))

    def get(self, package_name):
        return self._db.get(package_name)

    def set(self, package_name, sha):
        self._db[package_name] = sha
        self.save()

    def delete(self, package_name):
        del self._db[package_name]
        self.save()
