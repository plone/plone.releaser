from plone.releaser.buildout import CheckoutsFile
from plone.releaser.buildout import SourcesFile
from plone.releaser.buildout import VersionsFile

import pathlib
import pytest
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
CHECKOUTS_FILE = INPUT_DIR / "checkouts.cfg"
SOURCES_FILE = INPUT_DIR / "sources.cfg"
VERSIONS_FILE = INPUT_DIR / "versions.cfg"
VERSIONS_FILE2 = INPUT_DIR / "versions2.cfg"
VERSIONS_FILE3 = INPUT_DIR / "versions3.cfg"
VERSIONS_FILE4 = INPUT_DIR / "versions4.cfg"


def test_checkouts_file_data():
    cf = CheckoutsFile(CHECKOUTS_FILE)
    # The data used to map lower case to actual case,
    # but now actual case to True.
    assert cf.data == {
        "CamelCase": True,
        "package": True,
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
    assert cf["package"] is True
    assert cf.get("package") is True
    assert cf["camelcase"] is True
    assert cf["CAMELCASE"] is True
    assert cf["CamelCase"] is True
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
    assert cf.get("extra") is True


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


def test_checkouts_file_rewrite(tmp_path):
    copy_path = tmp_path / "checkouts.cfg"
    shutil.copyfile(CHECKOUTS_FILE, copy_path)
    cf = CheckoutsFile(copy_path)
    cf.rewrite()
    # Read it fresh and compare
    cf2 = CheckoutsFile(copy_path)
    assert cf.data == cf2.data
    # Check the entire text.  Note that packages are alphabetically sorted.
    # Currently we get the original case, but we may change this to lowercase.
    assert (
        copy_path.read_text()
        == """[buildout]
always-checkout = force
auto-checkout =
    CamelCase
    package
"""
    )


def test_sources_file_data():
    sf = SourcesFile(SOURCES_FILE)
    assert sorted(sf.data.keys()) == ["Plone", "docs", "plone.alterego", "plone.base"]


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
    assert docs.path == "extra/documentation"
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


def test_sources_file_rewrite(tmp_path):
    copy_path = tmp_path / "sources.cfg"
    shutil.copyfile(SOURCES_FILE, copy_path)
    sf = SourcesFile(copy_path)
    sf.rewrite()
    # Read it fresh and compare
    sf2 = SourcesFile(copy_path)
    assert sf.raw_data == sf2.raw_data
    assert sf.data == sf2.data
    # Some differences compared with the original:
    # - We always specify the branch.
    # - The order of the options may be different.
    assert (
        copy_path.read_text()
        == """[buildout]
extends =
    https://raw.githubusercontent.com/zopefoundation/Zope/master/sources.cfg

[remotes]
plone = https://github.com/plone
plone_push = git@github.com:plone

[sources]
docs = git ${remotes:plone}/documentation.git branch=6.0 path=extra/documentation egg=false
Plone = git ${remotes:plone}/Plone.git pushurl=${remotes:plone_push}/Plone.git branch=6.0.x
plone.alterego = git ${remotes:plone}/plone.alterego.git branch=master
plone.base = git ${remotes:plone}/plone.base.git branch=main
"""
    )


def test_versions_file_versions():
    vf = VersionsFile(VERSIONS_FILE)
    assert vf.data == {
        "annotated": "1.0",
        "CamelCase": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "package": "1.0",
        "pyspecific": "1.0",
        "UPPERCASE": "1.0",
    }


def test_versions_file_extends():
    vf = VersionsFile(VERSIONS_FILE)
    assert vf.extends == [
        "https://zopefoundation.github.io/Zope/releases/5.8.3/versions.cfg"
    ]
    vf = VersionsFile(VERSIONS_FILE2)
    assert vf.extends == ["versions3.cfg"]
    vf = VersionsFile(VERSIONS_FILE3)
    assert vf.extends == ["versions4.cfg"]
    vf = VersionsFile(VERSIONS_FILE4)
    assert vf.extends == []


def test_versions_file_read_extends_without_markers():
    vf = VersionsFile(VERSIONS_FILE2, read_extends=True)
    assert vf.data == {"four": "4.0", "one": "1.1", "three": "3.0", "two": "2.0"}


def test_versions_file_read_extends_with_markers():
    vf = VersionsFile(VERSIONS_FILE2, with_markers=True, read_extends=True)
    assert vf.data == {
        "five": {"macosx": "5.0"},
        "four": "4.0",
        "one": "1.1",
        "three": {"": "3.0", "python312": "3.2"},
        "two": "2.0",
    }


def test_versions_file_versions_with_markers():
    vf = VersionsFile(VERSIONS_FILE, with_markers=True)
    # All versions are reported lowercased.
    assert vf.data == {
        "annotated": "1.0",
        "CamelCase": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "onepython": {"python312": "2.1"},
        "package": "1.0",
        "pyspecific": {"": "1.0", "python312": "2.0"},
        "UPPERCASE": "1.0",
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


def test_versions_file_contains_with_markers():
    vf = VersionsFile(VERSIONS_FILE, with_markers=True)
    assert "package" in vf
    assert "nope" not in vf
    assert "onepython" in vf
    assert "pyspecific" in vf
    assert "ONEpython" in vf
    assert "pySPECIFIC" in vf


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


def test_versions_file_get_with_markers():
    vf = VersionsFile(VERSIONS_FILE, with_markers=True)
    assert vf.get("package") == "1.0"
    assert vf["package"] == "1.0"
    assert vf.get("onepython") == {"python312": "2.1"}
    assert vf.get("pyspecific") == {"": "1.0", "python312": "2.0"}
    assert vf["onepython"] == {"python312": "2.1"}
    assert vf["pyspecific"] == {"": "1.0", "python312": "2.0"}


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
    # How about packages that are not lowercase?
    # ConfigParser reports all package names as lower case, so we don't know
    # what their exact spelling is.  So whatever we pass on, should be used.
    assert "CamelCase = 1.0" in copy_path.read_text()
    assert copy_path.read_text().lower().count("camelcase") == 1
    vf["CAMELcase"] = "1.1"
    vf = VersionsFile(copy_path)
    assert vf["camelCASE"] == "1.1"
    assert vf["CaMeLcAsE"] == "1.1"
    text = copy_path.read_text()
    assert "CamelCase = 1.0" not in text
    assert "CAMELcase = 1.1" in text
    assert copy_path.read_text().lower().count("camelcase") == 1


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


def test_versions_file_set_with_markers(tmp_path):
    # [versions:python312] pins 'pyspecific = 2.0'.
    # We do not report or change this section.
    copy_path = tmp_path / "versions.cfg"
    shutil.copyfile(VERSIONS_FILE, copy_path)
    vf = VersionsFile(copy_path, with_markers=True)
    assert "pyspecific = 2.0" in copy_path.read_text()
    assert vf.get("pyspecific") == {"": "1.0", "python312": "2.0"}
    vf.set("pyspecific", "1.1")
    # Read it fresh, without markers.
    vf = VersionsFile(copy_path)
    assert vf.get("pyspecific") == "1.1"
    # Read it fresh, with markers.
    vf = VersionsFile(copy_path, with_markers=True)
    assert vf.get("pyspecific") == {"": "1.1", "python312": "2.0"}
    # Now edit for a specific python version.
    vf.set("pyspecific", ("2.1", "python312"))
    # Read it fresh, with markers.
    vf = VersionsFile(copy_path, with_markers=True)
    assert vf.get("pyspecific") == {"": "1.1", "python312": "2.1"}
    # Add to an unknown marker.
    vf.set("pyspecific", ("3.0", "python313"))
    # Read it fresh, with markers.
    vf = VersionsFile(copy_path, with_markers=True)
    assert "[versions:python313]" in copy_path.read_text()
    assert vf.get("pyspecific") == {"": "1.1", "python312": "2.1", "python313": "3.0"}
    # Add a new package to a new marker.
    vf.set("maconly", ("1.0", "macosx"))
    # Read it fresh, with markers.
    vf = VersionsFile(copy_path, with_markers=True)
    assert "[versions:macosx]" in copy_path.read_text()
    assert vf.get("maconly") == {"macosx": "1.0"}
    # Read it without markers.
    vf = VersionsFile(copy_path)
    assert vf["pyspecific"] == "1.1"
    assert not vf.get("maconly")


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


def test_versions_file_rewrite(tmp_path):
    copy_path = tmp_path / "versions.cfg"
    shutil.copyfile(VERSIONS_FILE, copy_path)
    vf = VersionsFile(copy_path)
    vf.rewrite()
    # Read it fresh and compare
    vf2 = VersionsFile(copy_path)
    assert vf.extends == vf2.extends
    assert vf.data == vf2.data
    # Check the entire text.
    # Note that there are differences with the original:
    # - all comments are removed
    # - the duplicate is removed
    assert (
        copy_path.read_text()
        == """[buildout]
extends = https://zopefoundation.github.io/Zope/releases/5.8.3/versions.cfg

[versions]
annotated = 1.0
CamelCase = 1.0
duplicate = 1.0
lowercase = 1.0
package = 1.0
pyspecific = 1.0
UPPERCASE = 1.0
"""
    )


def test_versions_file_rewrite_2(tmp_path):
    copy_path = tmp_path / "versions2.cfg"
    shutil.copyfile(VERSIONS_FILE2, copy_path)
    vf = VersionsFile(copy_path)
    vf.rewrite()
    # Read it fresh and compare
    vf2 = VersionsFile(copy_path)
    assert vf.extends == vf2.extends
    assert vf.data == vf2.data
    # Check the entire text.
    assert (
        copy_path.read_text()
        == """[buildout]
extends = versions3.cfg

[versions]
one = 1.1
two = 2.0
"""
    )


def test_versions_file_rewrite_with_markers(tmp_path):
    copy_path = tmp_path / "versions2.cfg"
    shutil.copyfile(VERSIONS_FILE2, copy_path)
    vf = VersionsFile(copy_path, with_markers=True)
    vf.rewrite()
    # Read it fresh and compare
    vf2 = VersionsFile(copy_path, with_markers=True)
    assert vf.extends == vf2.extends
    assert vf.data == vf2.data
    # Check the entire text.
    assert (
        copy_path.read_text()
        == """[buildout]
extends = versions3.cfg

[versions]
one = 1.1
two = 2.0

[versions:python312]
three = 3.2
"""
    )


def test_versions_file_rewrite_read_extends_without_markers(tmp_path):
    # Note: this combination may not make sense.
    copy_path = tmp_path / "versions2.cfg"
    shutil.copyfile(VERSIONS_FILE2, copy_path)
    # We extend some files and use their versions, so we need to copy them.
    shutil.copyfile(VERSIONS_FILE3, tmp_path / "versions3.cfg")
    shutil.copyfile(VERSIONS_FILE4, tmp_path / "versions4.cfg")
    vf = VersionsFile(copy_path, read_extends=True, with_markers=False)
    vf.rewrite()
    # Read it fresh and compare
    vf2 = VersionsFile(copy_path, read_extends=True, with_markers=False)
    assert vf.extends
    assert not vf2.extends
    assert vf.data == vf2.data
    # Check the entire text.  Note that packages are alphabetically sorted.
    assert (
        copy_path.read_text()
        == """[versions]
four = 4.0
one = 1.1
three = 3.0
two = 2.0
"""
    )


def test_versions_file_rewrite_read_extends_with_markers(tmp_path):
    copy_path = tmp_path / "versions2.cfg"
    shutil.copyfile(VERSIONS_FILE2, copy_path)
    # We extend some files and use their versions, so we need to copy them.
    shutil.copyfile(VERSIONS_FILE3, tmp_path / "versions3.cfg")
    shutil.copyfile(VERSIONS_FILE4, tmp_path / "versions4.cfg")
    vf = VersionsFile(copy_path, read_extends=True, with_markers=True)
    vf.rewrite()
    # Read it fresh and compare
    vf2 = VersionsFile(copy_path, read_extends=True, with_markers=True)
    assert vf.extends
    assert not vf2.extends
    assert vf.data == vf2.data
    # Check the entire text.  Note that packages are alphabetically sorted.
    assert (
        copy_path.read_text()
        == """[versions]
four = 4.0
one = 1.1
three = 3.0
two = 2.0

[versions:macosx]
five = 5.0

[versions:python312]
three = 3.2
"""
    )
