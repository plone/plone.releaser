from xmlrpc.client import ServerProxy


def get_users_with_release_rights(package_name):
    # Note: this is deprecated, but I don't see an alternative:
    # https://warehouse.pypa.io/api-reference/xml-rpc.html
    client = ServerProxy("https://pypi.org/pypi")
    existing_admins = {user for role, user in client.package_roles(package_name)}
    return existing_admins


def can_user_release_package_to_pypi(user, package_name):
    # Note: most packages that we release, will have/get the 'plone' organisation
    # as owner, and the code here does not know this, and does not know if you
    # are a member of this PyPI organisation.
    return user in get_users_with_release_rights(package_name)
