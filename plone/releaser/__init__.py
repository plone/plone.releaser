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
