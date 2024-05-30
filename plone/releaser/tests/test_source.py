from configparser import ConfigParser
from plone.releaser.buildout import Source

import pytest


def test_source_standard():
    src = Source.create_from_string(
        "Plone",
        "git https://github.com/plone/Plone.git pushurl=git@github.com:plone/Plone.git branch=6.0.x",
    )
    assert src.name == "Plone"
    assert src.protocol == "git"
    assert src.url == "https://github.com/plone/Plone.git"
    assert src.pushurl == "git@github.com:plone/Plone.git"
    assert src.branch == "6.0.x"
    assert src.egg is True
    assert src.path is None


def test_source_not_enough_parameters():
    with pytest.raises(IndexError):
        Source.create_from_string("package", "")
    with pytest.raises(IndexError):
        Source.create_from_string("package", "git")


def test_source_just_enough_parameters():
    # protocol and url are enough
    src = Source.create_from_string("Plone", "git https://github.com/plone/Plone.git")
    assert src.name == "Plone"
    assert src.protocol == "git"
    assert src.url == "https://github.com/plone/Plone.git"
    assert src.pushurl is None
    assert src.branch == "master"
    assert src.egg is True
    assert src.path is None


def test_source_docs():
    # Plone has a docs source with some extra options.
    src = Source.create_from_string(
        "docs",
        "git https://github.com/plone/documentation.git pushurl=git@github.com:plone/documentation.git egg=false branch=6.0 path=docs",
    )
    assert src.name == "docs"
    assert src.protocol == "git"
    assert src.url == "https://github.com/plone/documentation.git"
    assert src.pushurl == "git@github.com:plone/documentation.git"
    assert src.branch == "6.0"
    assert src.egg is False
    assert src.path == "docs"


def test_source_from_section():
    config = ConfigParser()
    config.read_string("[Plone]\nurl = blah")
    src = Source.create_from_section(config["Plone"])
    assert src.name == "Plone"
    assert src.url == "blah"
    assert not src.pushurl
    assert src.branch == "main"
    assert src.egg
    assert not src.path

    config.read_string(
        "\n".join(
            [
                "[package]",
                "url = hop",
                "pushurl = other",
                "branch = 1.x",
                "install-mode=skip",
                "target = /some/path",
            ]
        )
    )
    src = Source.create_from_section(config["package"])
    assert src.name == "package"
    assert src.url == "hop"
    assert src.pushurl == "other"
    assert src.branch == "1.x"
    assert not src.egg
    assert src.path == "/some/path"
