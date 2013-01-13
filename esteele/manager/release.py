from zest.releaser.utils import ask
from zest.releaser import pypi
import sys
from esteele.manager.manage import canUserReleasePackageToPypi


def check_pypi_access(data):
    pypi_user = pypi.PypiConfig().config.get('pypi', 'username')
    if not canUserReleasePackageToPypi(pypi_user, data['name']):
        if not ask("User %s does not have pypi release rights to %s. Continue?" % (pypi_user, data['name']), default=False):
            sys.exit()
