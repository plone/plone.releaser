# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


version = '1.5.3'

long_description = '{0}\n{1}'.format(
    open('README.rst').read(),
    open('CHANGES.rst').read()
)

setup(
    name='plone.releaser',
    version=version,
    description='Plone release management utilities',
    long_description=long_description,
    # Get more strings from
    # https://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
      'Framework :: Plone',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2.7',
    ],
    keywords='plone release',
    author='Eric Steele',
    author_email='eric@esteele.net',
    url='https://github.com/plone/plone.releaser',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['plone'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'argh',
        'gitpython>=0.3',
        'configparser',
        'argcomplete',
        'progress',
        'PyGithub',
        'keyring',
        'zest.releaser>=6.6.0',
        'docutils',
        'launchpadlib',
        # simplejson is needed because launchpadlib requires
        # lazr.restfulclient which needs a new release.  See
        # https://bugs.launchpad.net/lazr.restfulclient/+bug/1500460
        'simplejson',
    ],
    entry_points={
        'console_scripts': [
            'manage = plone.releaser.manage:manage',
        ],
        'zest.releaser.prereleaser.before': [
            ('set_nothing_changed_yet='
             'plone.releaser.release:set_nothing_changed_yet'),
            ('set_required_changelog='
             'plone.releaser.release:set_required_changelog'),
            ('cleanup_changelog='
             'plone.releaser.release:cleanup_changelog'),
        ],
        'zest.releaser.prereleaser.middle': [
            # Note: we explicitly call cleanup_changelog twice.
            ('cleanup_changelog='
             'plone.releaser.release:cleanup_changelog'),
            'check_pypi=plone.releaser.release:check_pypi_access',
        ],
        'zest.releaser.releaser.after': [
            'update_core=plone.releaser.release:update_core',
        ],
        'zest.releaser.postreleaser.before': [
            'set_new_changelog=plone.releaser.release:set_new_changelog',
        ],
    },
)
