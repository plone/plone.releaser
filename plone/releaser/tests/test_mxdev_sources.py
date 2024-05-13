from plone.releaser.pip import MxSourcesFile

import pathlib
import pytest
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
MX_SOURCES_FILE = INPUT_DIR / "mxsources.ini"


def test_mx_sources_file_data():
    mf = MxSourcesFile(MX_SOURCES_FILE)
    # The data used to map lower case to actual case,
    # but now actual case to True.
    assert mf.data == {
        "CamelCase": True,
        "package": True,
    }


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
    assert mf["package"] is True
    assert mf.get("package") is True
    assert mf["camelcase"] is True
    assert mf["CAMELCASE"] is True
    assert mf["CamelCase"] is True
    assert mf.get("unused") is None
    with pytest.raises(KeyError):
        mf["no-such-package"]


def test_mx_sources_file_rewrite(tmp_path):
    copy_path = tmp_path / "mxdev.ini"
    shutil.copyfile(MX_SOURCES_FILE, copy_path)
    mf = MxSourcesFile(copy_path)
    mf.rewrite()
    # Read it fresh and compare
    mf2 = MxSourcesFile(copy_path)
    assert mf.data == mf2.data
    # Check the entire text.  Note that packages are alphabetically sorted.
    # Currently we get the original case, but we may change this to lowercase.
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
"""
    )
