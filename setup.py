# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


version = '1.3'

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
    # http://pypi.python.org/pypi?:action=list_classifiers
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
        'zest.releaser',
        'docutils',
        'launchpadlib',
    ],
    entry_points={
        'console_scripts': [
            'manage = plone.releaser.manage:manage',
        ],
        'zest.releaser.prereleaser.middle': [
            'show_changelog=plone.releaser.release:show_changelog_entries',
            'check_pypi=plone.releaser.release:check_pypi_access',
        ],
        'zest.releaser.releaser.after': [
            'update_core=plone.releaser.release:update_core',
        ]
    },
)
