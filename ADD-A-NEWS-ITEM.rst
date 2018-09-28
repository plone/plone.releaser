.. If this works for more Plone packages, we may want to add this to the guidelines at https://docs.plone.org/develop/coredev/docs/guidelines.html
.. This text is adapted from https://pip.pypa.io/en/latest/development/#adding-a-news-entry


For contributors
----------------

The ``CHANGES.rst`` file is managed using `towncrier <https://pypi.org/project/towncrier/>`_.
All non trivial changes must be accompanied by an entry in the ``news`` directory.
Using such a tool instead of editing the file directly, has the following benefits:

- It avoids merge conflicts in ``CHANGES.rst``.
- It avoids news entries ending up under the wrong version header.

The best way of adding news entries is this:

- First create an issue describing the change you want to make.
  The issue number serves as a unique indicator for the news entry.
  As example, let's say you have created issue 42.

- Create a file inside of the ``news/`` directory, named after that issue number:

  - For bug fixes: ``42.bugfix``.
  - For new features: ``42.feature``.
  - For breaking changs: ``42.breaking``.
  - Any other extensions are ignored.

- The contents of this file should be reStructuredText formatted text that will be used as the content of the ``CHANGES.rst`` entry.
  Note: all lines are joined together, so do not use formatting that requires multiple lines.

- Towncrier will automatically add a reference to the issue when rendering the ``CHANGES.rst`` file.

- If unsure, you can let towncrier do a dry run::

    towncrier --version=X --draft


For release managers
--------------------

Configuration of ``towncrier`` is done in the ``pyproject.toml`` file in the repository root.
The following configuration should work for all core Plone packages::

    [tool.towncrier]
    filename = "CHANGES.rst"
    directory = "news/"
    title_format = "{version} ({project_date})"
    underlines = ["-", ""]

    [[tool.towncrier.type]]
    directory = "breaking"
    name = "Breaking changes:"
    showcontent = true

    [[tool.towncrier.type]]
    directory = "feature"
    name = "New features:"
    showcontent = true

    [[tool.towncrier.type]]
    directory = "bugfix"
    name = "Bug fixes:"
    showcontent = true

When you decide that a package must start using ``towncrier``, do this:

- Add a ``pyproject.toml`` like above.
- Remove ``CHANGES.rst merge=union`` from ``.gitattributes`` (probably remove the file with ``git``).
- Create a directory ``news`` with an empty file ``.gitkeep``.
- Remove the ``unreleased`` version header from ``CHANGES.rst``.
- In that place, add a marker for ``towncrier``, literally this: ``.. towncrier release notes start``
- Move the unreleased changes to files in the ``news`` directory.
- Add a hidden comment on top of ``CHANGES.rst`` to warn against editing that file directly.

For a script that automates most of this, see
https://gist.github.com/mauritsvanrees/92c40bc16ceaf3c375d81c995b4552c4

When you make a release, you could do it  manually::

    towncrier --version=X

Or do ``pip install zestreleaser.towncrier`` and just call ``fullrelease`` like you are used to.
The ``fullrelease`` script in a recent Plone coredev branch should work fine.
If ``towncrier`` doesn't do anything, you may need to make sure the command is on your ``PATH``.
