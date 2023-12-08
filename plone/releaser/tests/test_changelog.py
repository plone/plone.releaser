from plone.releaser.changelog import Changelog

import pathlib


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
CHANGES_RST = INPUT_DIR / "changes.rst"
CHANGES_MD = INPUT_DIR / "changes.md"


def test_get_changes_rst():
    cf = Changelog(CHANGES_RST)
    assert "3.0.2" in cf
    assert "3.0.3" in cf
    assert sorted(list(cf.get("3.0.3").keys())) == ["Bug fixes:", "Internal:", "other"]
    assert cf.get_changes("3.0.3") == []
    assert cf.get_changes("3.0.2") == [
        "Bug fixes:",
        "Respect locally allowed types when pasting objects [cekk] (#146)",
        "Fix a memory leak as reported in "
        "https://github.com/plone/Products.CMFPlone/issues/3829, changing interface "
        "declaration type as suggested by @d-maurer in "
        "https://github.com/plone/plone.dexterity/issues/186 [mamico] (#187)",
        "Internal:",
        "Update configuration files.\n[plone devs] (55bda5c9)",
    ]


def test_get_changes_md():
    cf = Changelog(CHANGES_MD)
    assert "6.0.5rc1" in cf
    assert "6.0.4" in cf
    # assert sorted(list(cf.get("6.0.5rc1").keys())) == ["Bug fixes:", "Internal:"]
    assert cf.get_changes("6.0.5rc1") == []
    assert cf.get_changes("6.0.4") == [
        "Bug fixes:",
        "Do not truncate the sortable_title index\n[erral] #3690",
        "Fix password validation tests. [tschorr] #3784",
        "Updated metadata version to 6016.\n[maurits] #6016",
        "Internal:",
        "Update configuration files.\n[plone devs] 2a5f5557",
    ]


def test_get_changes_content():
    from_file = Changelog(CHANGES_RST)
    from_string = Changelog(content=CHANGES_RST.read_bytes())
    from_bytes = Changelog(content=CHANGES_RST.read_bytes())
    assert "3.0.2" in from_file
    assert "3.0.2" in from_string
    assert "3.0.2" in from_bytes
    assert from_file == from_string
    assert from_string == from_bytes
