# -*- encoding: utf-8 -*-
"""Implements User UI."""
from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class LdapAuthSource(Base):
    """Implements CRUD functions from UI."""

    def navigate_to_entity(self):
        """Navigate to LDAP auth source entity page"""
        Navigator(self.browser).go_to_ldap_auth()

    def _search_locator(self):
        """Specify locator for LDAP auth source entity search procedure"""
        return locators['ldapserver.ldap_servername']

    def create(self, name=None, server=None, ldaps=False, port=None,
               server_type=None, login_name=None, first_name=None,
               surname=None, mail=None, photo=None, account_user=None,
               account_passwd=None, account_basedn=None,
               account_grpbasedn=None, ldap_filter=False, otf_register=True):
        """Create new ldap auth source from UI."""
        if not self.wait_until_element(locators['ldapsource.new']):
            return
        self.click(locators['ldapsource.new'])
        if self.wait_until_element(locators['ldapserver.name']):
            self.assign_value(locators['ldapserver.name'], name)
            self.assign_value(locators['ldapserver.server'], server)
            if ldaps:
                self.click(locators['ldapserver.ldaps'])
            if port:
                self.assign_value(locators['ldapserver.port'], port)
            self.select(locators['ldapserver.server_type'], server_type)
        self.click(tab_locators['ldapserver.tab_account'])
        if self.wait_until_element(locators['ldapserver.acc_user']) is None:
            raise UINoSuchElementError(u'Could not select the attributes Tab.')
        self.assign_value(locators['ldapserver.acc_user'], account_user)
        self.assign_value(locators['ldapserver.acc_passwd'], account_passwd)
        self.assign_value(locators['ldapserver.basedn'], account_basedn)
        self.assign_value(
            locators['ldapserver.group_basedn'], account_grpbasedn)
        if ldap_filter:
            self.click(locators['ldapserver.ldap_filter'])
        if otf_register:
            self.click(locators['ldapserver.otf_register'])
        self.click(tab_locators['ldapserver.tab_attributes'])
        if self.wait_until_element(locators['ldapserver.loginname']) is None:
            raise UINoSuchElementError(u'Could not select the account Tab.')
        self.assign_value(locators['ldapserver.loginname'], login_name)
        self.assign_value(locators['ldapserver.firstname'], first_name)
        self.assign_value(locators['ldapserver.surname'], surname)
        self.assign_value(locators['ldapserver.mail'], mail)
        if photo:
            self.assign_value(locators['ldapserver.photo'], photo)
        self.click(common_locators['submit'])

    def search(self, name):
        """Searches existing ldap auth source from UI. It is necessary to use
        custom search as we don't have both search bar and search button there.

        """
        self.navigate_to_entity()
        return self.wait_until_element(self._search_locator() % (name, name))
