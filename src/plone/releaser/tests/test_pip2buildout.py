from plone.releaser.buildout import VersionsFile
from plone.releaser.manage import pip2buildout

import pathlib
import shutil

TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
CONSTRAINTS_FILE = INPUT_DIR / "constraints.txt"
MXSOURCES_FILE = INPUT_DIR / "mxsources.ini"
MXCHECKOUTS_FILE = INPUT_DIR / "mxcheckouts.ini"


def test_pip2buildout_one_path(tmp_path):
    copy_path = tmp_path / "constraints.txt"
    versions_file = tmp_path / "versions.cfg"
    shutil.copyfile(CONSTRAINTS_FILE, copy_path)
    assert not versions_file.exists()
    pip2buildout(path=copy_path)
    assert versions_file.exists()
    vf = VersionsFile(versions_file, with_markers=True)
    assert vf.data == {
        "CamelCase": "1.0",
        "UPPERCASE": "1.0",
        "annotated": "1.0",
        "duplicate": "1.0",
        "lowercase": "1.0",
        "onepython": {'python_version=="3.12"': "2.1"},
        "package": "1.0",
        "pyspecific": {"": "1.0", 'python_version=="3.12"': "2.0"},
    }
    assert versions_file.read_text() == """[buildout]
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


def test_pip2buildout_all(tmp_path):
    constraints_path = tmp_path / "constraints.txt"
    versions_file = tmp_path / "versions.cfg"
    shutil.copyfile(CONSTRAINTS_FILE, constraints_path)
    mxsources_path = tmp_path / "mxsources.ini"
    sources_file = tmp_path / "sources.cfg"
    shutil.copyfile(MXSOURCES_FILE, mxsources_path)
    mxcheckouts_path = tmp_path / "mxcheckouts.ini"
    checkouts_file = tmp_path / "checkouts.cfg"
    shutil.copyfile(MXCHECKOUTS_FILE, mxcheckouts_path)
    pip2buildout(path=tmp_path)
    assert versions_file.exists()
    assert sources_file.exists()
    assert checkouts_file.exists()
    assert versions_file.read_text() == """[buildout]
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
    assert sources_file.read_text() == """[remotes]
plone = https://github.com/plone
plone_push = git@github.com:plone

[sources]
package = git ${remotes:plone}/package.git branch=main
unused = git ${remotes:plone}/package.git branch=main
CamelCase = git ${remotes:plone}/CamelCase.git branch=main
docs = git ${remotes:plone}/documentation.git pushurl=${remotes:plone_push}/documentation.git branch=6.0 path=extra/documentation egg=false
"""
    assert checkouts_file.read_text() == """[buildout]
auto-checkout =
    package
    CamelCase
"""
