Changelog
=========

.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

2.0.0 (2023-02-23)
------------------

Breaking changes:


- Require Python 3.8+.
  Cleanup code and dependencies, with help op plone/meta.
  Drop support for Plone 5.2 releases: no launchpad code anymore.
  [maurits] (#200)


1.8.8 (2022-12-21)
------------------

Bug fixes:


- Fix ValueError when calling ``bin/manage launchpad 5.2.10.1``.
  [maurits] (#45)


1.8.7 (2022-09-07)
------------------

Bug fixes:


- report: add sleep and start parameters.
  [maurits] (#44)


1.8.6 (2022-01-19)
------------------

Bug fixes:


- Insert buildout:docs-directory when reading sources.
  Workaround for issue similar to `mr.roboto 89 <https://github.com/plone/mr.roboto/issues/89>`_.
  [maurits] (#89)


1.8.5 (2021-12-01)
------------------

Bug fixes:


- Fix InterpolationMissingOptionError when parsing coredev 6.0 sources.
  [maurits] (#42)


1.8.4 (2021-10-16)
------------------

Bug fixes:


- Do not offer updating core branches 4.3 and 5.1.
  Only 5.2 and 6.0 are maintained.
  [maurits] (#41)


1.8.3 (2021-01-09)
------------------

Bug fixes:


- When reporting interesting commits, catch errors when comparing with previously ignored commit.
  Fixes `issue 39 <https://github.com/plone/plone.releaser/issues/39>`_.
  [maurits] (#39)


1.8.2 (2020-06-26)
------------------

New features:


- Support env var PLONE_RELEASER_MULTI_PACKAGES to signal doing multiple releases.
  We still change `checkouts.cfg` and `versions.cfg` in the relevant coredev branches then,
  but we do not offer to push them.
  [maurits] (#37)


Bug fixes:


- Fixed detecting changes in packages that are missing from checkouts.
  [maurits] (#35)


1.8.1 (2020-03-08)
------------------

Bug fixes:


- Fixed adding a package to checkouts.cfg.  [maurits] (#30)
- Ask before pushing an updated version when running 'report'.  [maurits] (#32)


1.8.0 (2019-11-25)
------------------

New features:


- Handle coredev branch 6.0 when releasing packages.
  [maurits] (#27)


Bug fixes:


- Fixed adding some package versions twice when releasing.
  [maurits] (#24)


1.7.3 (2019-08-29)
------------------

Bug fixes:


- Fixed Python 3 compatibility.  [maurits] (#25)


1.7.2 (2019-02-13)
------------------

No significant changes.


1.7.1 (2018-12-14)
------------------

Bug fixes:


- Python 3 compatibility fix for xmlrpclib/xmlrpc import differences. [esteele]
  (#21)
- Fix pypi URL. [gforcada] (#23)


1.7.0 (2018-10-01)
------------------

New features:


- Require ``zestreleaser.towncrier``. And start using towncrier for our own
  ``CHANGES.rst``. [maurits] (#17)


1.7.0 (unreleased)
------------------

New features:

- New zest.releaser hook: update other buildout.coredev branches as well.
  This automates the manual bookkeeping that one has to do whenever releasing packages:
  i.e. to check if the package just released is also checked out and used in other buildout.coredev branches.
  [gforcada]

- Ensure that selected packages are always kept on checkouts.cfg.
  [gforcada]


1.5.5 (2017-10-17)
------------------

Bug fixes:

- Skip over broken version definitions when building the unified changelog.
  [esteele]


1.5.4 (2016-11-01)
------------------

Bug fixes:

- Use print as a function.
  [gforcada]

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
