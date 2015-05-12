# -*- coding: utf-8 -*-
THIRD_PARTY_PACKAGES = (
    'Zope2',
    'ZODB3',
    'txtfilter',
    'Products.CMFActionIcons',
    'Products.CMFCalendar',
    'Products.CMFCore',
    'Products.CMFDefault',
    'Products.CMFTopic',
    'Products.CMFUid',
    'Products.DCWorkflow',
    'Products.GenericSetup',
    'Products.GroupUserFolder',
    'Products.PluggableAuthService',
    'Products.PluginRegistry',
    'Products.ZCatalog',
)

IGNORED_PACKAGES = (
    'plone.releaser',
)

ALWAYS_CHECKED_OUT = (
    'Plone',
    'Products.CMFPlone',
    'plone.app.upgrade',
    'plone.app.locales',
)

# Upon checking a package...
# ... ask every time if an action should be performed
ACTION_INTERACTIVE = 'interactive'
# ... don't ask anything and perform all actions
ACTION_BATCH = 'batch'
# ... don't ask anything *AND* don't make any action, just show the status
# of the package
ACTION_REPORT = 'report'

PACKAGE_ACTIONS = (
    ACTION_BATCH,
    ACTION_INTERACTIVE,
    ACTION_REPORT,
)
