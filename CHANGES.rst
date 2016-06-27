Changelog
=========

1.5.3 (2016-06-27)
------------------

Bug fixes:

- Change  pypi-url from http to https.
  [fgrcon]


1.5.2 (2016-06-12)
------------------

New features:

- Ask before pushing to coredev, after updating the checkouts and versions.  [maurits]

Bug fixes:

- Fix new versions if they had dev/post release suffix.
  [gforcada]


1.5.1 (2016-04-28)
------------------

New features:

- Changed new headings to 'Breaking changes', 'New features', 'Bug
  fixes'.  Old headers are still accepted, but in the postrelease we
  generate the new ones.  In the unified changelog, we combine the old
  and new names.
  See https://github.com/plone/Products.CMFPlone/issues/1323
  [maurits]

Bug fixes:

- When compiling changelog, treat Incompatibilities header as special
  too.  [maurits]


1.5.0 (2016-02-27)
------------------

New:

- Added prerelease hooks to cleanup empty headers.  [maurits]

- Add header 'Incompatibilities:' in postrelease.  In prerelease check
  if at least one of New, Fixes, Incompatibilities is there.
  See https://github.com/plone/Products.CMFPlone/issues/1323  [maurits]


1.4 (2016-02-11)
----------------

New:

- Removed our 'show changelog' entry point.  Required zest.releaser
  6.6.0 that has this itself.  [maurits]

- Show ``New:`` and ``Fixes:`` in unified changelog.  [maurits]

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

Fixes:

- Temporarily require simplejson. This is needed because launchpadlib
  requires lazr.restfulclient which needs a new release.  See
  https://bugs.launchpad.net/lazr.restfulclient/+bug/1500460  [maurits]


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
