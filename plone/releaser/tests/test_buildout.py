from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import Source
from plone.releaser.buildout import SourcesFile
from plone.releaser.buildout import VersionsFile

import os
import pathlib
import pytest
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
CHECKOUTS_FILE = INPUT_DIR / "checkouts.cfg"
SOURCES_FILE = INPUT_DIR / "sources.cfg"
VERSIONS_FILE = INPUT_DIR / "versions.cfg"


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


def test_source_standard():
    src = Source.create_from_string(
        "git https://github.com/plone/Plone.git pushurl=git@github.com:plone/Plone.git branch=6.0.x"
    )
    assert src.protocol == "git"
    assert src.url == "https://github.com/plone/Plone.git"
    assert src.pushurl == "git@github.com:plone/Plone.git"
    assert src.branch == "6.0.x"
    assert src.egg is True
    assert src.path is None


def test_source_not_enough_parameters():
    with pytest.raises(IndexError):
        Source.create_from_string("")
    with pytest.raises(IndexError):
        Source.create_from_string("git")


def test_source_just_enough_parameters():
    # protocol and url are enough
    src = Source.create_from_string("git https://github.com/plone/Plone.git")
    assert src.protocol == "git"
    assert src.url == "https://github.com/plone/Plone.git"
    assert src.pushurl is None
    assert src.branch == "master"
    assert src.egg is True
    assert src.path is None


def test_source_docs():
    # Plone has a docs source with some extra options.
    src = Source.create_from_string(
        "git https://github.com/plone/documentation.git pushurl=git@github.com:plone/documentation.git egg=false branch=6.0 path=docs"
    )
    assert src.protocol == "git"
    assert src.url == "https://github.com/plone/documentation.git"
    assert src.pushurl == "git@github.com:plone/documentation.git"
    assert src.branch == "6.0"
    assert src.egg is False
    assert src.path == "docs"


def test_sources_file_data():
    sf = SourcesFile(SOURCES_FILE)
    # Note that the keys are lowercase.
    assert sorted(sf.data.keys()) == ["docs", "plone", "plone.alterego", "plone.base"]


def test_sources_file_contains():
    sf = SourcesFile(SOURCES_FILE)
    assert "docs" in sf
    assert "plone.base" in sf
    assert "nope" not in sf
    # We compare case insensitively.
    assert "Plone" in sf
    assert "plone" in sf
    assert "PLONE" in sf
    assert "PLONE.BASE" in sf


def test_sources_file_get():
    sf = SourcesFile(SOURCES_FILE)
    with pytest.raises(KeyError):
        assert sf["nope"]
    assert sf["plone"] == sf["PLONE"]
    assert sf["plone"] == sf["Plone"]
    assert sf["plone"] != sf["plone.base"]
    plone = sf["plone"]
    assert plone.url == "https://github.com/plone/Plone.git"
    assert plone.pushurl == "git@github.com:plone/Plone.git"
    assert plone.branch == "6.0.x"
    assert plone.path is None
    assert plone.egg
    docs = sf["docs"]
    assert docs.url == "https://github.com/plone/documentation.git"
    assert docs.pushurl is None
    assert docs.branch == "6.0"
    assert docs.path == f"{os.getcwd()}/documentation"
    assert not docs.egg
    alterego = sf["plone.alterego"]
    assert alterego.url == "https://github.com/plone/plone.alterego.git"
    assert alterego.pushurl is None
    assert alterego.branch == "master"
    assert alterego.path is None
    assert alterego.egg
    base = sf["plone.base"]
    assert base.url == "https://github.com/plone/plone.base.git"
    assert base.pushurl is None
    assert base.branch == "main"
    assert base.path is None
    assert base.egg


def test_versions_file_versions():
    vf = VersionsFile(VERSIONS_FILE)
    # All versions are reported lowercased.
    assert vf.data == {
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
