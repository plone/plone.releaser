from plone.releaser.manage import versions2constraints

import os
import pathlib
import pytest
import shutil


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
VERSIONS_FILE = INPUT_DIR / "versions.cfg"
VERSIONS_FILE2 = INPUT_DIR / "versions2.cfg"
VERSIONS_FILE3 = INPUT_DIR / "versions3.cfg"
VERSIONS_FILE4 = INPUT_DIR / "versions4.cfg"


def test_versions2constraints(tmp_path):
    copy_path = tmp_path / "versions.cfg"
    constraints_file = tmp_path / "constraints.txt"
    shutil.copyfile(VERSIONS_FILE, copy_path)
    assert not constraints_file.exists()
    versions2constraints(path=copy_path)
    assert constraints_file.exists()
    # TODO: we should include versions with markers:
    # pyspecific==2.0; python_version=="3.12"
    # onepython==2.1; python_version=="3.12"
    assert (
        constraints_file.read_text()
        == """annotated==1.0
camelcase==1.0
duplicate==1.0
lowercase==1.0
package==1.0
pyspecific==1.0
uppercase==1.0
""")
