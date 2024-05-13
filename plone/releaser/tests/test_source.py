from plone.releaser.buildout import Source

import pytest


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
