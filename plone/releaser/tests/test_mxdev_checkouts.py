from plone.releaser.pip import MxCheckoutsFile

import pathlib
import pytest
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
MX_CHECKOUTS_FILE = INPUT_DIR / "mxcheckouts.ini"


def test_mx_checkouts_file_data():
    mf = MxCheckoutsFile(MX_CHECKOUTS_FILE)
    # The data used to map lower case to actual case,
    # but now actual case to True.
    assert mf.data == {
        "CamelCase": True,
        "package": True,
    }


def test_mx_checkouts_file_contains():
    mf = MxCheckoutsFile(MX_CHECKOUTS_FILE)
    assert "package" in mf
    assert "unused" not in mf
    # We compare case insensitively.
    assert "camelcase" in mf
    assert "CamelCase" in mf
    assert "CAMELCASE" in mf


def test_mx_checkouts_file_get():
    mf = MxCheckoutsFile(MX_CHECKOUTS_FILE)
    assert mf["package"] is True
    assert mf.get("package") is True
    assert mf["camelcase"] is True
    assert mf["CAMELCASE"] is True
    assert mf["CamelCase"] is True
    with pytest.raises(KeyError):
        mf["unused"]
    assert mf.get("unused") is None


def test_mx_checkouts_file_add_known(tmp_path):
    # When we add or remove a checkout, the file changes, so we work on a copy.
    copy_path = tmp_path / "mxdev.ini"
    shutil.copyfile(MX_CHECKOUTS_FILE, copy_path)
    mf = MxCheckoutsFile(copy_path)
    assert "unused" not in mf
    mf.add("unused")
    # Let's read it fresh, for good measure.
    mf = MxCheckoutsFile(copy_path)
    assert "unused" in mf
    assert mf["unused"] is True


def test_mx_checkouts_file_add_unknown(tmp_path):
    # It actually does not matter for us if a package is unknown in a
    # mxdev sources file: we are happy to add it in a mxdev checkouts file.
    copy_path = tmp_path / "mxdev.ini"
    shutil.copyfile(MX_CHECKOUTS_FILE, copy_path)
    mf = MxCheckoutsFile(copy_path)
    assert "unknown" not in mf
    mf.add("unknown")
    # Let's read it fresh, for good measure.
    mf = MxCheckoutsFile(copy_path)
    assert "unknown" in mf
    assert mf["unknown"] is True


def test_mx_checkouts_file_remove(tmp_path):
    copy_path = tmp_path / "mxdev.ini"
    shutil.copyfile(MX_CHECKOUTS_FILE, copy_path)
    mf = MxCheckoutsFile(copy_path)
    assert "package" in mf
    mf.remove("package")
    # Let's read it fresh, for good measure.
    mf = MxCheckoutsFile(copy_path)
    assert "package" not in mf
    assert "CAMELCASE" in mf
    mf.remove("CAMELCASE")
    mf = MxCheckoutsFile(copy_path)
    assert "CAMELCASE" not in mf
    assert "CamelCase" not in mf
    assert "camelcase" not in mf
    # Check that we can re-enable a package:
    # editing should not remove the entire section.
    mf.add("package")
    mf = MxCheckoutsFile(copy_path)
    assert "package" in mf
    # This should work for the last section as well.
    mf.add("CamelCase")
    mf = MxCheckoutsFile(copy_path)
    assert "CamelCase" in mf


def test_mx_checkouts_file_rewrite(tmp_path):
    copy_path = tmp_path / "mxsources.ini"
    shutil.copyfile(MX_CHECKOUTS_FILE, copy_path)
    mf = MxCheckoutsFile(copy_path)
    mf.rewrite()
    # Read it fresh and compare
    mf2 = MxCheckoutsFile(copy_path)
    assert mf.data == mf2.data
    # Check the entire text.
    assert (
        copy_path.read_text()
        == """[settings]
default-use = false

[package]
use = true

[CamelCase]
use = true
"""
    )
