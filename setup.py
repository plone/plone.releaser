# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


version = "1.8.6"

long_description = "{0}\n{1}".format(
    open("README.rst").read(), open("CHANGES.rst").read()
)

setup(
    name="plone.releaser",
    version=version,
    description="Plone release management utilities",
    long_description=long_description,
    # Get more strings from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="plone release",
    author="Eric Steele",
    author_email="eric@esteele.net",
    url="https://github.com/plone/plone.releaser",
    license="GPL",
    packages=find_packages(),
    namespace_packages=["plone"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "argh",
        "gitpython>=0.3",
        "configparser",
        "argcomplete",
        "progress",
        "PyGithub",
        "keyring",
        "six",
        "zest.releaser>=6.6.0",
        "zestreleaser.towncrier>=1.0.0b3",
        "docutils",
        "launchpadlib",
    ],
    entry_points={
        "console_scripts": ["manage = plone.releaser.manage:manage"],
        "zest.releaser.prereleaser.before": [
            (
                "set_nothing_changed_yet="
                "plone.releaser.release:set_nothing_changed_yet"
            ),
            ("set_required_changelog=" "plone.releaser.release:set_required_changelog"),
            ("cleanup_changelog=" "plone.releaser.release:cleanup_changelog"),
        ],
        "zest.releaser.prereleaser.middle": [
            # Note: we explicitly call cleanup_changelog twice.
            ("cleanup_changelog=" "plone.releaser.release:cleanup_changelog"),
            "check_pypi=plone.releaser.release:check_pypi_access",
        ],
        "zest.releaser.releaser.after": [
            "update_core=plone.releaser.release:update_core",
            (
                "update_other_core_branches="
                "plone.releaser.release:update_other_core_branches"
            ),
        ],
        "zest.releaser.postreleaser.before": [
            "set_new_changelog=plone.releaser.release:set_new_changelog"
        ],
    },
)
