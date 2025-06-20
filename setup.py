from setuptools import find_packages
from setuptools import setup


version = "2.5.2.dev0"

long_description = "{}\n{}".format(
    open("README.rst").read(), open("CHANGES.rst").read()
)

setup(
    name="plone.releaser",
    version=version,
    description="Plone release management utilities",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # Get more strings from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
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
    python_requires=">=3.8",
    install_requires=[
        "setuptools",
        "argh",
        "gitpython>=3.0.0",
        "configparser",
        "packaging",
        "progress",
        "zest.releaser[recommended]>=7.2.0",
        "zestreleaser.towncrier>=1.3.0",
        "docutils",
    ],
    extras_require={
        "test": ["pytest"],
    },
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
