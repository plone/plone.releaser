import xmlrpclib


def getUsersWithReleaseRights(package_name):
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    existing_admins = [user for role,
                       user in client.package_roles(package_name)]
    return existing_admins


def canUserReleasePackageToPypi(user, package_name):
    return user in getUsersWithReleaseRights(package_name)

