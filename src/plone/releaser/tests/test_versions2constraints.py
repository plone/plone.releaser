from plone.releaser.manage import versions2constraints
from plone.releaser.pip import ConstraintsFile

import pathlib
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
VERSIONS_FILE = INPUT_DIR / "versions.cfg"
VERSIONS_FILE2 = INPUT_DIR / "versions2.cfg"
VERSIONS_FILE3 = INPUT_DIR / "versions3.cfg"
VERSIONS_FILE4 = INPUT_DIR / "versions4.cfg"


def test_versions2constraints_one_path(tmp_path):
    copy_path = tmp_path / "versions.cfg"
    constraints_file = tmp_path / "constraints.txt"
    shutil.copyfile(VERSIONS_FILE, copy_path)
    assert not constraints_file.exists()
    versions2constraints(path=copy_path)
    assert constraints_file.exists()
    cf = ConstraintsFile(constraints_file, with_markers=True)
    assert cf.data == {
        "CamelCase": "1.0",
        "UPPERCASE": "1.0",
        "annotated": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "onepython": {'python_version == "3.12"': "2.1"},
        "package": "1.0",
        "pyspecific": {"": "1.0", 'python_version == "3.12"': "2.0"},
    }
    assert (
        constraints_file.read_text()
        == """-c https://zopefoundation.github.io/Zope/releases/5.8.3/constraints.txt
annotated==1.0
CamelCase==1.0
duplicate==1.0
lowercase==1.0
package==1.0
pyspecific==1.0
pyspecific==2.0; python_version == "3.12"
UPPERCASE==1.0
onepython==2.1; python_version == "3.12"
"""
    )


def test_versions2constraints_all(tmp_path):
    versions_path = tmp_path / "versions.cfg"
    versions2_path = tmp_path / "versions2.cfg"
    versions3_path = tmp_path / "versions3.cfg"
    versions4_path = tmp_path / "versions4.cfg"
    constraints_file = tmp_path / "constraints.txt"
    constraints2_file = tmp_path / "constraints2.txt"
    constraints3_file = tmp_path / "constraints3.txt"
    constraints4_file = tmp_path / "constraints4.txt"
    shutil.copyfile(VERSIONS_FILE, versions_path)
    shutil.copyfile(VERSIONS_FILE2, versions2_path)
    shutil.copyfile(VERSIONS_FILE3, versions3_path)
    shutil.copyfile(VERSIONS_FILE4, versions4_path)
    assert not constraints_file.exists()
    assert not constraints2_file.exists()
    assert not constraints3_file.exists()
    assert not constraints4_file.exists()
    versions2constraints(path=tmp_path)
    assert constraints_file.exists()
    assert constraints2_file.exists()
    assert constraints3_file.exists()
    assert constraints4_file.exists()
    cf = ConstraintsFile(constraints_file, with_markers=True)
    assert cf.data == {
        "CamelCase": "1.0",
        "UPPERCASE": "1.0",
        "annotated": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "onepython": {'python_version == "3.12"': "2.1"},
        "package": "1.0",
        "pyspecific": {"": "1.0", 'python_version == "3.12"': "2.0"},
    }
    assert (
        constraints_file.read_text()
        == """-c https://zopefoundation.github.io/Zope/releases/5.8.3/constraints.txt
annotated==1.0
CamelCase==1.0
duplicate==1.0
lowercase==1.0
package==1.0
pyspecific==1.0
pyspecific==2.0; python_version == "3.12"
UPPERCASE==1.0
onepython==2.1; python_version == "3.12"
"""
    )
    cf2 = ConstraintsFile(constraints2_file, with_markers=True)
    assert cf2.data == {
        "one": "1.1",
        "three": {'python_version == "3.12"': "3.2"},
        "two": "2.0",
    }
    assert (
        constraints2_file.read_text()
        == """-c constraints3.txt
one==1.1
two==2.0
three==3.2; python_version == "3.12"
"""
    )
    cf3 = ConstraintsFile(constraints3_file, with_markers=True)
    assert cf3.data == {
        "one": "1.0",
        "three": {"": "3.0", 'python_version == "3.12"': "3.1"},
    }
    assert (
        constraints3_file.read_text()
        == """-c constraints4.txt
one==1.0
three==3.0
three==3.1; python_version == "3.12"
"""
    )
    cf4 = ConstraintsFile(constraints4_file, with_markers=True)
    assert cf4.data == {"four": "4.0", "five": {'platform_system == "Darwin"': "5.0"}}
    assert (
        constraints4_file.read_text()
        == """four==4.0
five==5.0; platform_system == "Darwin"
"""
    )
