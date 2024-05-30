Introduction
============

Tools to make managing Plone core releases easier.
It is a wrapper around ``zest.releaser``, plus it adds some commands.

WARNING: this package is only meant for development of core Plone.
It may have useful bits for others, but we may drop features and edge cases at any time if it is no longer useful for Plone.


Installation
------------

Do ``pip install plone.releaser`` or add it to your buildout::

  [release]
  recipe = zc.recipe.egg
  eggs = plone.releaser


Main usage: release a package
-----------------------------

In  the `Plone core development buildout <https://github.com/plone/buildout.coredev>`_ go to ``src/some.package`` and run ``../../bin/fullrelease``.
This calls the ``fullrelease`` command from ``zest.releaser``, but with some extra hooks and packages available.

One nice thing it does: look in the checkouts and sources of your ``buildout.coredev`` checkout and update them:
remove the released package from the checkouts and update the version.

If you are working on branch 6.1 of coredev, then we check if you also have branches 5.2 and 6.0 checked out.
There we check if the branch of the released package is in the sources.
If you make a release from package branch ``main`` and this is the branch used in the sources, then we update the checkouts and sources of this coredev branch as well.

After releasing a package, you should wait a few minutes before you manually push the changes to all coredev branches.
This gives the PyPI mirrors time to catch up so the new release is available, so Jenkins and GitHub Actions can find it.


Main commands
-------------

Take several Buildout files and create pip/mxdev files out of them::

  $ bin/manage buildout2pip

Take a Buildout versions file and create a pip constraints file out of it.

  $ bin/manage versions2constraints

Generate a changelog with changes from all packages since a certain Plone release::

  $ bin/manage changelog --start=6.1.0a1


Other commands
--------------

Some commands are not used much (by Maurits anyway) because they are less needed these days.

Check PyPi access to all Plone packages for a certain user::

  $ bin/manage checkPypi timo

Check a package for updates::

  $ bin/manage checkPackageForUpdates Products.CMFPlone

Report packages with changes::

  $ bin/manage report --interactive

Pulls::

  $ bin/manage pulls

Check checkout::

  $ bin/manage check-checkout
