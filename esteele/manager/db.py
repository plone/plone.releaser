import json
import os


class IgnoresDB(object):

    def __init__(self):
        self._filename = '.package_ignores'
        if not os.path.isfile(self._filename):
            open(self._filename, 'w').close()
        f = open(self._filename, 'r')
        content = f.read()
        if content != '':
            self._db = json.loads(content)
        else:
            self._db = {}
        f.close()

    def save(self):
        f = open(self._filename, 'w+')
        f.write(json.dumps(self._db))
        f.close()

    def get(self, package_name):
        return self._db.get(package_name)

    def set(self, package_name, sha):
        self._db[package_name] = sha
        self.save()

    def delete(self, package_name):
        del self._db[package_name]
        self.save()
