from plone.releaser.pip import ConstraintsFile
from plone.releaser.pip import IniFile

import pathlib
import pytest
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
CONSTRAINTS_FILE = INPUT_DIR / "constraints.txt"
CONSTRAINTS_FILE2 = INPUT_DIR / "constraints2.txt"
CONSTRAINTS_FILE3 = INPUT_DIR / "constraints3.txt"
CONSTRAINTS_FILE4 = INPUT_DIR / "constraints4.txt"
MXDEV_FILE = INPUT_DIR / "mxdev.ini"


def test_mxdev_file_data():
    mf = IniFile(MXDEV_FILE)
    # The data used to map lower case to actual case,
    # but now actual case to True.
    assert mf.data == {
        "CamelCase": True,
        "package": True,
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
    assert mf["package"] is True
    assert mf.get("package") is True
    assert mf["camelcase"] is True
    assert mf["CAMELCASE"] is True
    assert mf["CamelCase"] is True
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
    assert mf["unused"] is True


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


def test_mxdev_file_rewrite(tmp_path):
    copy_path = tmp_path / "mxdev.ini"
    shutil.copyfile(MXDEV_FILE, copy_path)
    mf = IniFile(copy_path)
    mf.rewrite()
    # Read it fresh and compare
    mf2 = IniFile(copy_path)
    assert mf.data == mf2.data
    # Check the entire text.  Note that packages are alphabetically sorted.
    # Currently we get the original case, but we may change this to lowercase.
    assert (
        copy_path.read_text()
        == """[settings]
requirements-in = requirements.txt
requirements-out = requirements-mxdev.txt
contraints-out = constraints-mxdev.txt
default-use = false
plone = https://github.com/plone

[package]
url = ${settings:plone}/package.git
branch = main
use = true

[unused]
url = ${settings:plone}/package.git
branch = main

[CamelCase]
url = ${settings:plone}/CamelCase.git
branch = main
use = true
"""
    )


def test_constraints_file_constraints():
    cf = ConstraintsFile(CONSTRAINTS_FILE)
    # All constraints are reported lowercased.
    assert cf.data == {
        "annotated": "1.0",
        "CamelCase": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "package": "1.0",
        "pyspecific": "1.0",
        "UPPERCASE": "1.0",
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
    # How about packages that are not lowercase?
    # Currently in ConstraintsFile we report all package names as lower case,
    # so we don't know what their exact spelling is, which is what ConfigParser
    # does for the Buildout files.  So whatever we pass on, should be used.
    assert "CamelCase==1.0" in copy_path.read_text()
    assert copy_path.read_text().lower().count("camelcase") == 1
    cf["CAMELcase"] = "1.1"
    cf = ConstraintsFile(copy_path)
    assert cf["camelCASE"] == "1.1"
    assert cf["CaMeLcAsE"] == "1.1"
    text = copy_path.read_text()
    assert "CamelCase==1.0" not in text
    assert "CAMELcase==1.1" in text
    assert copy_path.read_text().lower().count("camelcase") == 1


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


def test_constraints_file_extends():
    cf = ConstraintsFile(CONSTRAINTS_FILE)
    assert cf.extends == [
        "https://zopefoundation.github.io/Zope/releases/5.8.3/constraints.txt"
    ]
    cf = ConstraintsFile(CONSTRAINTS_FILE2)
    assert cf.extends == ["constraints3.txt"]
    cf = ConstraintsFile(CONSTRAINTS_FILE3)
    assert cf.extends == ["constraints4.txt"]
    cf = ConstraintsFile(CONSTRAINTS_FILE4)
    assert cf.extends == []


def test_constraints_file_read_extends_without_markers():
    cf = ConstraintsFile(CONSTRAINTS_FILE2, read_extends=True)
    assert cf.data == {"four": "4.0", "one": "1.1", "three": "3.0", "two": "2.0"}


def test_constraints_file_read_extends_with_markers():
    cf = ConstraintsFile(CONSTRAINTS_FILE2, with_markers=True, read_extends=True)
    assert cf.data == {
        "five": {"platform_system == 'darwin'": "5.0"},
        "four": "4.0",
        "one": "1.1",
        "three": {"": "3.0", 'python_version=="3.12"': "3.2"},
        "two": "2.0",
    }


def test_constraints_file_constraints_with_markers():
    cf = ConstraintsFile(CONSTRAINTS_FILE, with_markers=True)
    # All constraints are reported lowercased.
    assert cf.data == {
        "annotated": "1.0",
        "CamelCase": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "onepython": {'python_version=="3.12"': "2.1"},
        "package": "1.0",
        "pyspecific": {"": "1.0", 'python_version=="3.12"': "2.0"},
        "UPPERCASE": "1.0",
    }


def test_constraints_file_rewrite(tmp_path):
    copy_path = tmp_path / "constraints.txt"
    shutil.copyfile(CONSTRAINTS_FILE, copy_path)
    cf = ConstraintsFile(copy_path)
    cf.rewrite()
    # Read it fresh and compare
    cf2 = ConstraintsFile(copy_path)
    assert cf.extends == cf2.extends
    assert cf.data == cf2.data
    # Check the entire text.
    # Note that there are differences with the original:
    # - the extends line is on a separate line
    # - all comments are removed
    # - the duplicate is removed
    assert (
        copy_path.read_text()
        == """-c https://zopefoundation.github.io/Zope/releases/5.8.3/constraints.txt
annotated==1.0
CamelCase==1.0
duplicate==1.0
lowercase==1.0
package==1.0
pyspecific==1.0
UPPERCASE==1.0
"""
    )


def test_constraints_file_rewrite_2(tmp_path):
    copy_path = tmp_path / "constraints2.txt"
    shutil.copyfile(CONSTRAINTS_FILE2, copy_path)
    cf = ConstraintsFile(copy_path)
    cf.rewrite()
    # Read it fresh and compare
    cf2 = ConstraintsFile(copy_path)
    assert cf.extends == cf2.extends
    assert cf.data == cf2.data
    # Check the entire text.
    assert (
        copy_path.read_text()
        == """-c constraints3.txt
one==1.1
two==2.0
"""
    )


def test_constraints_file_rewrite_with_markers(tmp_path):
    copy_path = tmp_path / "constraints2.txt"
    shutil.copyfile(CONSTRAINTS_FILE2, copy_path)
    cf = ConstraintsFile(copy_path, with_markers=True)
    cf.rewrite()
    # Read it fresh and compare
    cf2 = ConstraintsFile(copy_path, with_markers=True)
    assert cf.extends == cf2.extends
    assert cf.data == cf2.data
    # Check the entire text.
    assert (
        copy_path.read_text()
        == """-c constraints3.txt
one==1.1
two==2.0
three==3.2; python_version=="3.12"
"""
    )


def test_constraints_file_rewrite_read_extends_without_markers(tmp_path):
    # Note: this combination may not make sense.
    copy_path = tmp_path / "constraints2.txt"
    shutil.copyfile(CONSTRAINTS_FILE2, copy_path)
    # We extend some files and use their constraints, so we need to copy them.
    shutil.copyfile(CONSTRAINTS_FILE3, tmp_path / "constraints3.txt")
    shutil.copyfile(CONSTRAINTS_FILE4, tmp_path / "constraints4.txt")
    cf = ConstraintsFile(copy_path, read_extends=True, with_markers=False)
    cf.rewrite()
    # Read it fresh and compare
    cf2 = ConstraintsFile(copy_path, read_extends=True, with_markers=False)
    assert cf.extends
    assert not cf2.extends
    assert cf.data == cf2.data
    # Check the entire text.  Note that packages are alphabetically sorted.
    assert (
        copy_path.read_text()
        == """four==4.0
one==1.1
three==3.0
two==2.0
"""
    )


def test_constraints_file_rewrite_read_extends_with_markers(tmp_path):
    copy_path = tmp_path / "constraints2.txt"
    shutil.copyfile(CONSTRAINTS_FILE2, copy_path)
    # We extend some files and use their constraints, so we need to copy them.
    shutil.copyfile(CONSTRAINTS_FILE3, tmp_path / "constraints3.txt")
    shutil.copyfile(CONSTRAINTS_FILE4, tmp_path / "constraints4.txt")
    cf = ConstraintsFile(copy_path, read_extends=True, with_markers=True)
    cf.rewrite()
    # Read it fresh and compare
    cf2 = ConstraintsFile(copy_path, read_extends=True, with_markers=True)
    assert cf.extends
    assert not cf2.extends
    assert cf.data == cf2.data
    # Check the entire text.  Note that packages are alphabetically sorted.
    assert (
        copy_path.read_text()
        == """four==4.0
five==5.0; platform_system == 'darwin'
one==1.1
three==3.0
three==3.2; python_version=="3.12"
two==2.0
"""
    )
