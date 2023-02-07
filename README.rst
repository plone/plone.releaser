Introduction
============

Tools to make managing Plone core releases easier.

Installation
------------

To install plone.releaser add it to your buildout::

  [release]
  recipe = zc.recipe.egg
  eggs =  plone.releaser

To make it available in buildout.coredev, run buildout with releaser.cfg::

  $ bin/buildout -c releaser.cfg

Usage
-----

Check PyPi access to all Plone packages for a certain user::

  $ bin/manage checkPypi timo

Check a package for updates::

  $ bin/manage checkPackageForUpdates Products.CMFPlone

Report packages with changes::

  $ bin/manage report --interactive

Pulls::

  $ bin/manage pulls

Changelog::

  $ bin/manage changelog

Check checkout::

  $ bin/manage check-checkout

Append Jenkins build number to package version::

  $ bin/append-jenkins-build-number-to-package-version

Set package version::

  $ bin/set-package-version
