from plone.releaser.base import Source
from plone.releaser.pip import MxSourcesFile

import pathlib
import pytest
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
MX_SOURCES_FILE = INPUT_DIR / "mxsources.ini"


def test_mx_sources_file_data():
    mf = MxSourcesFile(MX_SOURCES_FILE)
    assert list(mf.data.keys()) == ["package", "unused", "CamelCase", "docs"]
    for key, value in mf.data.items():
        assert isinstance(value, Source)


def test_mx_sources_file_contains():
    mf = MxSourcesFile(MX_SOURCES_FILE)
    assert "package" in mf
    assert "unused" in mf
    # We compare case insensitively.
    assert "camelcase" in mf
    assert "CamelCase" in mf
    assert "CAMELCASE" in mf


def test_mx_sources_file_get():
    mf = MxSourcesFile(MX_SOURCES_FILE)
    package = mf["package"]
    assert package
    assert mf.get("package") == package
    assert isinstance(package, Source)
    assert package.protocol == "git"
    assert package.url == "${settings:plone}/package.git"
    assert package.branch == "main"
    assert package.pushurl is None
    assert package.path is None
    assert package.egg is True
    lowercase = mf["camelcase"]
    uppercase = mf["CAMELCASE"]
    camelcase = mf["CamelCase"]
    assert lowercase
    assert isinstance(lowercase, Source)
    assert uppercase
    assert camelcase
    assert lowercase == uppercase
    assert lowercase == camelcase
    # The 'unused' package is not used (checked out), but we do not know that.
    assert isinstance(mf.get("unused"), Source)
    with pytest.raises(KeyError):
        mf["no-such-package"]
    docs = mf["docs"]
    assert docs.branch == "6.0"
    assert docs.egg is False
    assert docs.path == "extra/documentation"


def test_mx_sources_file_rewrite(tmp_path):
    copy_path = tmp_path / "mxdev.ini"
    shutil.copyfile(MX_SOURCES_FILE, copy_path)
    mf = MxSourcesFile(copy_path)
    mf.rewrite()
    # Read it fresh and compare
    mf2 = MxSourcesFile(copy_path)
    assert mf.data == mf2.data
    # Check the entire text.
    assert (
        copy_path.read_text()
        == """[settings]
requirements-in = requirements.txt
requirements-out = requirements-mxdev.txt
constraints-out = constraints-mxdev.txt
plone = https://github.com/plone

[package]
url = ${settings:plone}/package.git
branch = main

[unused]
url = ${settings:plone}/package.git
branch = main

[CamelCase]
url = ${settings:plone}/CamelCase.git
branch = main

[docs]
url = ${setting:plone}/documentation.git
branch = 6.0
install-mode = skip
target = extra/documentation
"""
    )
