from plone.releaser.buildout import VersionsFile

import pathlib
import pytest


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
VERSIONS_FILE = INPUT_DIR / "versions.cfg"


def test_versions_file_versions():
    vf = VersionsFile(VERSIONS_FILE)
    # All versions are reported lowercased.
    assert vf.versions == {
        "annotated": "1.0",
        "camelcase": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "package": "1.0",
        "pyspecific": "2.0",
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
