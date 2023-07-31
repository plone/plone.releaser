from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import VersionsFile

import pathlib
import pytest
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
VERSIONS_FILE = INPUT_DIR / "versions.cfg"
CHECKOUTS_FILE = INPUT_DIR / "checkouts.cfg"


def test_checkouts_file_data():
    cf = CheckoutsFile(CHECKOUTS_FILE)
    # The data maps lower case to actual case.
    assert cf.data == {
        "camelcase": "CamelCase",
        "package": "package",
    }


def test_checkouts_file_contains():
    cf = CheckoutsFile(CHECKOUTS_FILE)
    assert "package" in cf
    assert "nope" not in cf
    # We compare case insensitively.
    assert "camelcase" in cf
    assert "CamelCase" in cf
    assert "CAMELCASE" in cf


def test_checkouts_file_get():
    cf = CheckoutsFile(CHECKOUTS_FILE)
    # The data maps lower case to actual case.
    assert cf["package"] == "package"
    assert cf.get("package") == "package"
    assert cf["camelcase"] == "CamelCase"
    assert cf["CAMELCASE"] == "CamelCase"
    assert cf["CamelCase"] == "CamelCase"
    with pytest.raises(KeyError):
        cf["nope"]


def test_checkouts_file_add(tmp_path):
    # When we add or remove a checkout, the file changes, so we work on a copy.
    copy_path = tmp_path / "checkouts.cfg"
    shutil.copyfile(CHECKOUTS_FILE, copy_path)
    cf = CheckoutsFile(copy_path)
    assert "Extra" not in cf
    cf.add("Extra")
    # Let's read it fresh, for good measure.
    cf = CheckoutsFile(copy_path)
    assert "Extra" in cf
    assert cf.get("extra") == "Extra"


def test_checkouts_file_remove(tmp_path):
    copy_path = tmp_path / "checkouts.cfg"
    shutil.copyfile(CHECKOUTS_FILE, copy_path)
    cf = CheckoutsFile(copy_path)
    assert "package" in cf
    cf.remove("package")
    # Let's read it fresh, for good measure.
    cf = CheckoutsFile(copy_path)
    assert "package" not in cf
    assert "CAMELCASE" in cf
    cf.remove("CAMELCASE")
    cf = CheckoutsFile(copy_path)
    assert "CAMELCASE" not in cf
    assert "CamelCase" not in cf
    assert "camelcase" not in cf


def test_versions_file_versions():
    vf = VersionsFile(VERSIONS_FILE)
    # All versions are reported lowercased.
    assert vf.versions == {
        "annotated": "1.0",
        "camelcase": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "package": "1.0",
        "pyspecific": "1.0",
        "uppercase": "1.0",
    }


def test_versions_file_contains():
    vf = VersionsFile(VERSIONS_FILE)
    assert "package" in vf
    assert "nope" not in vf
    # We compare case insensitively.
    # Let's try all combinations
    assert "camelcase" in vf
    assert "CamelCase" in vf
    assert "CAMELCASE" in vf
    assert "lowercase" in vf
    assert "LowerCase" in vf
    assert "LOWERCASE" in vf
    assert "uppercase" in vf
    assert "UpperCase" in vf
    assert "UPPERCASE" in vf


def test_versions_file_get():
    vf = VersionsFile(VERSIONS_FILE)
    assert vf.get("package") == "1.0"
    assert vf["package"] == "1.0"
    with pytest.raises(KeyError):
        vf["nope"]
    assert vf.get("nope") is None
    assert vf.get("nope", "hello") == "hello"
    # We compare case insensitively.
    # Let's try all combinations
    assert vf["camelcase"] == "1.0"
    assert vf["CamelCase"] == "1.0"
    assert vf["CAMELCASE"] == "1.0"
    assert vf["lowercase"] == "1.0"
    assert vf["LowerCase"] == "1.0"
    assert vf["LOWERCASE"] == "1.0"
    assert vf["uppercase"] == "1.0"
    assert vf["UpperCase"] == "1.0"
    assert vf["UPPERCASE"] == "1.0"


def test_versions_file_set_normal(tmp_path):
    # When we set a version, the file changes, so we work on a copy.
    copy_path = tmp_path / "versions.cfg"
    shutil.copyfile(VERSIONS_FILE, copy_path)
    vf = VersionsFile(copy_path)
    assert vf.get("package") == "1.0"
    vf.set("package", "2.0")
    # Let's read it fresh, for good measure.
    vf = VersionsFile(copy_path)
    assert vf.get("package") == "2.0"
    vf["package"] = "3.0"
    vf = VersionsFile(copy_path)
    assert vf.get("package") == "3.0"


def test_versions_file_set_ignore_markers(tmp_path):
    # [versions:python312] pins 'pyspecific = 2.0'.
    # We do not report or change this section.
    copy_path = tmp_path / "versions.cfg"
    shutil.copyfile(VERSIONS_FILE, copy_path)
    vf = VersionsFile(copy_path)
    assert "pyspecific = 2.0" in copy_path.read_text()
    assert vf.get("pyspecific") == "1.0"
    vf.set("pyspecific", "1.1")
    # Let's read it fresh, for good measure.
    vf = VersionsFile(copy_path)
    assert vf.get("pyspecific") == "1.1"
    assert "pyspecific = 2.0" in copy_path.read_text()


def test_versions_file_set_cleanup_duplicates(tmp_path):
    copy_path = tmp_path / "versions.cfg"
    shutil.copyfile(VERSIONS_FILE, copy_path)
    assert copy_path.read_text().count("duplicate = 1.0") == 2
    vf = VersionsFile(copy_path)
    assert vf.get("duplicate") == "1.0"
    vf.set("duplicate", "2.0")
    # Let's read it fresh, for good measure.
    vf = VersionsFile(copy_path)
    assert vf.get("duplicate") == "2.0"
    assert copy_path.read_text().count("duplicate = 2.0") == 1
    assert copy_path.read_text().count("duplicate = 1.0") == 0
