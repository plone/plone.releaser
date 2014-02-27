from zest.releaser.utils import ask
from zest.releaser import pypi
import sys
import re
import os
from esteele.manager.manage import canUserReleasePackageToPypi
import git


def check_pypi_access(data):
    pypi_user = pypi.PypiConfig().config.get('pypi', 'username')
    if not canUserReleasePackageToPypi(pypi_user, data['name']):
        if not ask("User %s does not have pypi release rights to %s. Continue?" % (pypi_user, data['name']), default=False):
            sys.exit()


def update_core(data):
    if ask("Ok to update coredev versions.cfg/checkouts.cfg?", default=True):
        package_name = data['name']
        new_version = data['version']
        update_versions(package_name, new_version)
        update_checkouts(package_name)
        # git commit
        root_path = os.path.join(os.getcwd(), '../../')
        message = "%s %s" % (package_name, new_version)
        g = git.Git(root_path)
        g.add('versions.cfg')
        g.add('checkouts.cfg')
        print "Commiting changes."
        g.commit(message=message)
        print "Pushing changes to server."
        g.push()


def update_versions(package_name, new_version):
    # Update version
    print "Updating versions.cfg"
    versionsfile = os.path.join(os.getcwd(), '../../versions.cfg')
    f = open(versionsfile, 'r')
    versionstxt = f.read()
    f.close()

    reg = re.compile("(^%s[\s\=]*)[0-9\.abrc]*" % package_name, re.MULTILINE)
    newVersionsTxt = reg.sub(r"\g<1>%s" % new_version, versionstxt)

    f = open(versionsfile, 'w')
    f.write(newVersionsTxt)
    f.close()


def update_checkouts(package_name):
    # Remove from checkouts.cfg
    print "Removing package from checkouts.cfg"
    checkoutsfile = os.path.join(os.getcwd(), '../../checkouts.cfg')
    f = open(checkoutsfile, 'r')
    checkoutstxt = f.read()
    f.close()

    reg = re.compile("^[\s]*%s\n" % package_name, re.MULTILINE)
    newCheckoutsTxt = reg.sub('', checkoutstxt)

    f = open(checkoutsfile, 'w')
    f.write(newCheckoutsTxt)
    f.close()