from plone.releaser.manage import buildout2pip
from plone.releaser.pip import ConstraintsFile

import pathlib
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
VERSIONS_FILE = INPUT_DIR / "versions.cfg"
SOURCES_FILE = INPUT_DIR / "sources.cfg"
CHECKOUTS_FILE = INPUT_DIR / "checkouts.cfg"


def test_buildout2pip_one_path(tmp_path):
    copy_path = tmp_path / "versions.cfg"
    constraints_file = tmp_path / "constraints.txt"
    shutil.copyfile(VERSIONS_FILE, copy_path)
    assert not constraints_file.exists()
    buildout2pip(path=copy_path)
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


def test_buildout2pip_all(tmp_path):
    versions_path = tmp_path / "versions.cfg"
    constraints_file = tmp_path / "constraints.txt"
    shutil.copyfile(VERSIONS_FILE, versions_path)
    sources_path = tmp_path / "sources.cfg"
    mxsources_file = tmp_path / "mxsources.ini"
    shutil.copyfile(SOURCES_FILE, sources_path)
    checkouts_path = tmp_path / "checkouts.cfg"
    mxcheckouts_file = tmp_path / "mxcheckouts.ini"
    shutil.copyfile(CHECKOUTS_FILE, checkouts_path)
    buildout2pip(path=tmp_path)
    assert constraints_file.exists()
    assert mxsources_file.exists()
    assert mxcheckouts_file.exists()
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
    assert (
        mxsources_file.read_text()
        == """[settings]
plone = https://github.com/plone
plone_push = git@github.com:plone

[docs]
url = ${settings:plone}/documentation.git
branch = 6.0
install-mode = skip
target = extra/documentation

[Plone]
url = ${settings:plone}/Plone.git
pushurl = ${settings:plone_push}/Plone.git
branch = 6.0.x

[plone.alterego]
url = ${settings:plone}/plone.alterego.git
branch = master

[plone.base]
url = ${settings:plone}/plone.base.git
branch = main
"""
    )
    assert (
        mxcheckouts_file.read_text()
        == """[settings]
default-use = false

[CamelCase]
use = true

[package]
use = true
"""
    )
