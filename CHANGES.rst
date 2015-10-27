Changelog
=========

1.4 (unreleased)
----------------

New:

- Require ``New:`` or ``Fixes:`` to be present in the changelog during
  prerelease.
  [maurits]

- Simplified showing last changelog entries.  Requires zest.releaser
  6.0 or higher.
  [maurits]

- Set new changelog format during postrelease.  Adapt check in
  prerelease that warns when the original changelog text has not been
  changed since the previous release.
  Issue https://github.com/plone/Products.CMFPlone/issues/1180
  [maurits]


1.3 (2015-09-27)
----------------

- Fail nicely if a Plone versions.cfg can't be located
  [esteele]

- When showing the changelog, accept 1.7.2.1 as version.  So loose
  version numbers instead of strict version numbers with only one or
  two dots.
  [maurits]

- Run git pull on buildout.coredev to make sure it is up-to-date.
  [timo]

- Refactor checkPackageForUpdates to be more flexible. Made it a class
  on its own module.
  [gforcada]

- Create a jenkins report based on checkPackageForUpdates.
  [gforcada]


1.2 (2015-03-21)
----------------

- Rename esteele.manager to plone.releaser.
  [timo]


1.1 (2014-04-23)
----------------

- add feature: add the package to the version file if it doesn't exists
  [jfroche]

- add command to set the package version in a versions config file
  [jfroche]

- return the new version number when appending jenkins build number to the versions of a package
  [jfroche]


1.0 (2014-04-23)
----------------

- Initial release
  [esteele]
