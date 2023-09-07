from plone.releaser.pip import ConstraintsFile
from plone.releaser.pip import IniFile

import pathlib
import pytest
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
CONSTRAINTS_FILE = INPUT_DIR / "constraints.txt"
MXDEV_FILE = INPUT_DIR / "mxdev.ini"


def test_mxdev_file_data():
    mf = IniFile(MXDEV_FILE)
    # The data maps lower case to actual case.
    assert mf.data == {
        "camelcase": "CamelCase",
        "package": "package",
    }


def test_mxdev_file_contains():
    mf = IniFile(MXDEV_FILE)
    assert "package" in mf
    assert "unused" not in mf
    # We compare case insensitively.
    assert "camelcase" in mf
    assert "CamelCase" in mf
    assert "CAMELCASE" in mf


def test_mxdev_file_get():
    mf = IniFile(MXDEV_FILE)
    # The data maps lower case to actual case.
    assert mf["package"] == "package"
    assert mf.get("package") == "package"
    assert mf["camelcase"] == "CamelCase"
    assert mf["CAMELCASE"] == "CamelCase"
    assert mf["CamelCase"] == "CamelCase"
    with pytest.raises(KeyError):
        mf["unused"]
    assert mf.get("unused") is None


def test_mxdev_file_add_known(tmp_path):
    # When we add or remove a checkout, the file changes, so we work on a copy.
    copy_path = tmp_path / "mxdev.ini"
    shutil.copyfile(MXDEV_FILE, copy_path)
    mf = IniFile(copy_path)
    assert "unused" not in mf
    mf.add("unused")
    # Let's read it fresh, for good measure.
    mf = IniFile(copy_path)
    assert "unused" in mf
    assert mf["unused"] == "unused"


def test_mxdev_file_add_unknown(tmp_path):
    # We cannot edit mxdev.ini to use a package when it is not defined.
    copy_path = tmp_path / "mxdev.ini"
    shutil.copyfile(MXDEV_FILE, copy_path)
    mf = IniFile(copy_path)
    assert "unknown" not in mf
    with pytest.raises(KeyError):
        mf.add("unknown")


def test_mxdev_file_remove(tmp_path):
    copy_path = tmp_path / "mxdev.ini"
    shutil.copyfile(MXDEV_FILE, copy_path)
    mf = IniFile(copy_path)
    assert "package" in mf
    mf.remove("package")
    # Let's read it fresh, for good measure.
    mf = IniFile(copy_path)
    assert "package" not in mf
    assert "CAMELCASE" in mf
    mf.remove("CAMELCASE")
    mf = IniFile(copy_path)
    assert "CAMELCASE" not in mf
    assert "CamelCase" not in mf
    assert "camelcase" not in mf
    # Check that we can re-enable a package:
    # editing should not remove the entire section.
    mf.add("package")
    mf = IniFile(copy_path)
    assert "package" in mf
    # This should work for the last section as well.
    mf.add("CamelCase")
    mf = IniFile(copy_path)
    assert "CamelCase" in mf


def test_constraints_file_constraints():
    cf = ConstraintsFile(CONSTRAINTS_FILE)
    # All constraints are reported lowercased.
    assert cf.data == {
        "annotated": "1.0",
        "camelcase": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "package": "1.0",
        "pyspecific": "1.0",
        "uppercase": "1.0",
    }


def test_constraints_file_contains():
    cf = ConstraintsFile(CONSTRAINTS_FILE)
    assert "package" in cf
    assert "nope" not in cf
    # We compare case insensitively.
    # Let's try all combinations
    assert "camelcase" in cf
    assert "CamelCase" in cf
    assert "CAMELCASE" in cf
    assert "lowercase" in cf
    assert "LowerCase" in cf
    assert "LOWERCASE" in cf
    assert "uppercase" in cf
    assert "UpperCase" in cf
    assert "UPPERCASE" in cf


def test_constraints_file_get():
    cf = ConstraintsFile(CONSTRAINTS_FILE)
    assert cf.get("package") == "1.0"
    assert cf["package"] == "1.0"
    with pytest.raises(KeyError):
        cf["nope"]
    assert cf.get("nope") is None
    assert cf.get("nope", "hello") == "hello"
    # We compare case insensitively.
    # Let's try all combinations
    assert cf["camelcase"] == "1.0"
    assert cf["CamelCase"] == "1.0"
    assert cf["CAMELCASE"] == "1.0"
    assert cf["lowercase"] == "1.0"
    assert cf["LowerCase"] == "1.0"
    assert cf["LOWERCASE"] == "1.0"
    assert cf["uppercase"] == "1.0"
    assert cf["UpperCase"] == "1.0"
    assert cf["UPPERCASE"] == "1.0"


def test_constraints_file_set_normal(tmp_path):
    # When we set a version, the file changes, so we work on a copy.
    copy_path = tmp_path / "constraints.txt"
    shutil.copyfile(CONSTRAINTS_FILE, copy_path)
    cf = ConstraintsFile(copy_path)
    assert cf.get("package") == "1.0"
    cf.set("package", "2.0")
    # Let's read it fresh, for good measure.
    cf = ConstraintsFile(copy_path)
    assert cf.get("package") == "2.0"
    cf["package"] = "3.0"
    cf = ConstraintsFile(copy_path)
    assert cf.get("package") == "3.0"


def test_constraints_file_set_ignore_markers(tmp_path):
    # pyspecific==2.0; python_version=="3.12"
    # version pins that have a specific `python_version` are not changed.
    copy_path = tmp_path / "constraints.txt"
    shutil.copyfile(CONSTRAINTS_FILE, copy_path)
    cf = ConstraintsFile(copy_path)
    assert "pyspecific==2.0" in copy_path.read_text()
    assert cf.get("pyspecific") == "1.0"
    cf.set("pyspecific", "1.1")
    # Let's read it fresh, for good measure.
    cf = ConstraintsFile(copy_path)
    assert cf.get("pyspecific") == "1.1"
    assert "pyspecific==2.0" in copy_path.read_text()


def test_constraints_file_set_cleanup_duplicates(tmp_path):
    copy_path = tmp_path / "constraints.txt"
    shutil.copyfile(CONSTRAINTS_FILE, copy_path)
    assert copy_path.read_text().count("duplicate==1.0") == 2
    cf = ConstraintsFile(copy_path)
    assert cf.get("duplicate") == "1.0"
    cf.set("duplicate", "2.0")
    # Let's read it fresh, for good measure.
    cf = ConstraintsFile(copy_path)
    assert cf.get("duplicate") == "2.0"
    assert copy_path.read_text().count("duplicate==2.0") == 1
    assert copy_path.read_text().count("duplicate==1.0") == 0
