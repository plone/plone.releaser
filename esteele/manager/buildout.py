from collections import OrderedDict
from configparser import ConfigParser, ExtendedInterpolation
import os
import re


class Source():

    def __init__(self, protocol=None, url=None, push_url=None, branch=None):
        self.protocol = protocol
        self.url = url
        self.push_url = push_url
        self.branch = branch

    def create_from_string(self, source_string):
        protocol, url, extra_1, extra_2, extra_3 = (
            lambda a, b, c=None, d=None, e=None: (a, b, c, d, e))(*source_string.split())
        for param in [extra_1, extra_2, extra_3]:
            if param is not None:
                key, value = param.split('=')
                setattr(self, key, value)
        self.protocol = protocol
        self.url = url
        if self.push_url is not None:
            self.push_url = self.push_url.split('=')[-1]
        if self.branch is None:
            self.branch = 'master'
        else:
            self.branch = self.branch.split('=')[-1]
        return self

    @property
    def path(self):
        if self.url:
            match = re.match(
                '(\w+://)(.+@)*([\w\d\.]+)(:[\d]+){0,1}/(?P<path>.+(?=\.git))(\.git)', self.url)
            if match:
                return match.groupdict()['path']
        return None


class Buildout():

    def __init__(self,
                 sources_file='sources.cfg',
                 checkouts_file='checkouts.cfg',
                 versions_file='versions.cfg'):
        self.sources_file = sources_file
        self.checkouts_file = checkouts_file
        self.versions_file = versions_file

    def _getSourcesConfig(self):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.optionxform = str
        with open(self.sources_file) as f:
            config.readfp(f)
        return config

    @property
    def sources(self):
        config = self._getSourcesConfig()
        sources_dict = OrderedDict()
        for name, value in config['sources'].items():
            source = Source().create_from_string(value)
            sources_dict[name] = source
        return sources_dict

    # def getSource(self, package_name):
    #     config = self.getSourcesConfig()
    #     source = Source().create_from_string(config.get('sources', package_name))
    #     return source

    def addToCheckouts(self, package_name):
        path = os.path.join(os.getcwd(), self.checkouts_file)
        with open(path, 'r') as f:
            checkoutstxt = f.read()
        with open(path, 'w') as f:
            fixes_text = "# Test fixes only"
            reg = re.compile("^[\s]*%s\n" % fixes_text, re.MULTILINE)
            newCheckoutsTxt = reg.sub('    %s\n%s\n' %
                                      (package_name, fixes_text), checkoutstxt)
            f.write(newCheckoutsTxt)

    def removeFromCheckouts(self, package_name):
        # Remove from checkouts.cfg
        path = os.path.join(os.getcwd(), self.checkouts_file)
        with open(path, 'r') as f:
            checkoutstxt = f.read()
        with open(path, 'w') as f:
            reg = re.compile("^[\s]*%s\n" % package_name, re.MULTILINE)
            newCheckoutsTxt = reg.sub('', checkoutstxt)
            f.write(newCheckoutsTxt)

    def getVersion(self, package_name):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        with open(self.versions_file) as f:
            config.readfp(f)
        version = config.get('versions', package_name)
        return version

    def setVersion(self, package_name, new_version):
        path = os.path.join(os.getcwd(), self.versions_file)
        with open(path, 'r') as f:
            versionstxt = f.read()
        with open(path, 'w') as f:
            reg = re.compile("(^%s[\s\=]+)[0-9\.abrc]+" %
                             package_name, re.MULTILINE)
            newVersionsTxt = reg.sub(r"\g<1>%s" % new_version, versionstxt)
            f.write(newVersionsTxt)

    def getAutoCheckouts(self):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        with open(self.checkouts_file) as f:
            config.readfp(f)
        checkouts = config.get('buildout', 'auto-checkout')
        checkout_list = checkouts.split('\n')
        return checkout_list

    def setAutoCheckouts(self, checkouts_list):
        config = ConfigParser(interpolation=ExtendedInterpolation())
        with open(self.checkouts_file) as f:
            config.readfp(f)
        checkouts = '\n'.join(checkouts_list)
        config.set('buildout', 'auto-checkout', checkouts)
        with open(self.checkouts_file, 'w') as f:
            config.write(f)
