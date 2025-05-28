from plone.releaser.buildout import VersionsFile
from plone.releaser.manage import constraints2versions

import pathlib
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
CONSTRAINTS_FILE = INPUT_DIR / "constraints.txt"
CONSTRAINTS_FILE2 = INPUT_DIR / "constraints2.txt"
CONSTRAINTS_FILE3 = INPUT_DIR / "constraints3.txt"
CONSTRAINTS_FILE4 = INPUT_DIR / "constraints4.txt"


def test_constraints2versions_one_path(tmp_path):
    copy_path = tmp_path / "constraints.txt"
    versions_file = tmp_path / "versions.cfg"
    shutil.copyfile(CONSTRAINTS_FILE, copy_path)
    assert not versions_file.exists()
    constraints2versions(path=copy_path)
    assert versions_file.exists()
    cf = VersionsFile(versions_file, with_markers=True)
    assert cf.data == {
        "CamelCase": "1.0",
        "UPPERCASE": "1.0",
        "annotated": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "onepython": {'python_version=="3.12"': "2.1"},
        "package": "1.0",
        "pyspecific": {"": "1.0", 'python_version=="3.12"': "2.0"},
    }
    assert (
        versions_file.read_text()
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

[versions:python_version=="3.12"]
pyspecific = 2.0
onepython = 2.1
"""
    )


def test_constraints2versions_all(tmp_path):
    constraints_path = tmp_path / "constraints.txt"
    constraints2_path = tmp_path / "constraints2.txt"
    constraints3_path = tmp_path / "constraints3.txt"
    constraints4_path = tmp_path / "constraints4.txt"
    versions_file = tmp_path / "versions.cfg"
    versions2_file = tmp_path / "versions2.cfg"
    versions3_file = tmp_path / "versions3.cfg"
    versions4_file = tmp_path / "versions4.cfg"
    shutil.copyfile(CONSTRAINTS_FILE, constraints_path)
    shutil.copyfile(CONSTRAINTS_FILE2, constraints2_path)
    shutil.copyfile(CONSTRAINTS_FILE3, constraints3_path)
    shutil.copyfile(CONSTRAINTS_FILE4, constraints4_path)
    assert not versions_file.exists()
    assert not versions2_file.exists()
    assert not versions3_file.exists()
    assert not versions4_file.exists()
    constraints2versions(path=tmp_path)
    assert versions_file.exists()
    assert versions2_file.exists()
    assert versions3_file.exists()
    assert versions4_file.exists()
    cf = VersionsFile(versions_file, with_markers=True)
    assert cf.data == {
        "CamelCase": "1.0",
        "UPPERCASE": "1.0",
        "annotated": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "onepython": {'python_version=="3.12"': "2.1"},
        "package": "1.0",
        "pyspecific": {"": "1.0", 'python_version=="3.12"': "2.0"},
    }
    assert (
        versions_file.read_text()
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

[versions:python_version=="3.12"]
pyspecific = 2.0
onepython = 2.1
"""
    )
    cf2 = VersionsFile(versions2_file, with_markers=True)
    assert cf2.data == {
        "one": "1.1",
        "three": {'python_version=="3.12"': "3.2"},
        "two": "2.0",
    }
    assert (
        versions2_file.read_text()
        == """[buildout]
extends = versions3.cfg

[versions]
one = 1.1
two = 2.0

[versions:python_version=="3.12"]
three = 3.2
"""
    )
    cf3 = VersionsFile(versions3_file, with_markers=True)
    assert cf3.data == {
        "one": "1.0",
        "three": {"": "3.0", 'python_version=="3.12"': "3.1"},
    }
    assert (
        versions3_file.read_text()
        == """[buildout]
extends = versions4.cfg

[versions]
one = 1.0
three = 3.0

[versions:python_version=="3.12"]
three = 3.1
"""
    )
    cf4 = VersionsFile(versions4_file, with_markers=True)
    assert cf4.data == {"four": "4.0", "five": {"platform_system == 'Darwin'": "5.0"}}
    assert (
        versions4_file.read_text()
        == """[versions]
four = 4.0

[versions:platform_system == 'Darwin']
five = 5.0
"""
    )
