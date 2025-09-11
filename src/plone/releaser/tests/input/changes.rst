Example changelog from plone.dexterity.
At some point the bug fixes were missing, and the internal item was filed under bug fixes.
See https://github.com/plone/plone.releaser/issues/60


3.0.3 (2023-09-01)
------------------

Bug fixes:


- Respect locally allowed types when pasting objects [cekk] (#146)
- Fix a memory leak as reported in https://github.com/plone/Products.CMFPlone/issues/3829, changing interface declaration type as suggested by @d-maurer in https://github.com/plone/plone.dexterity/issues/186 [mamico] (#187)


Internal:


- Update configuration files.
  [plone devs] (55bda5c9)


3.0.2 (2023-03-14)
------------------

Bug fixes:


- Type error is removed and none is returned.
  In this modified version of the code, if no primary field adapter is found, the fieldname and field attributes are set to None.
  The value property checks whether the field attribute is None, and returns None if it is, instead of raising an error.
  [Coder-aadarsh] (#59)
