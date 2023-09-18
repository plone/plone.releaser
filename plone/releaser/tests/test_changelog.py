from plone.releaser.changelog import Changelog

import pathlib


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
CHANGES_FILE = INPUT_DIR / "changes.rst"


def test_get_changes():
    cf = Changelog(CHANGES_FILE)
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
