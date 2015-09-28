# -*- encoding: utf-8 -*-
"""Implements User UI."""
from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class LdapAuthSource(Base):
    """Implements CRUD functions from UI."""

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
            self.field_update('ldapserver.name', name)
            self.field_update('ldapserver.server', server)
            if ldaps:
                self.click(locators['ldapserver.ldaps'])
            if port:
                self.field_update('ldapserver.port', port)
            Select(
                self.find_element(locators['ldapserver.server_type'])
            ).select_by_visible_text(server_type)
        self.click(tab_locators['ldapserver.tab_account'])
        if self.wait_until_element(locators['ldapserver.acc_user']) is None:
            raise UINoSuchElementError(u'Could not select the attributes Tab.')
        self.field_update('ldapserver.acc_user', account_user)
        self.field_update('ldapserver.acc_passwd', account_passwd)
        self.field_update('ldapserver.basedn', account_basedn)
        self.field_update('ldapserver.group_basedn', account_grpbasedn)
        if ldap_filter:
            self.click(locators['ldapserver.ldap_filter'])
        if otf_register:
            self.click(locators['ldapserver.otf_register'])
        self.click(tab_locators['ldapserver.tab_attributes'])
        if self.wait_until_element(locators['ldapserver.loginname']) is None:
            raise UINoSuchElementError(u'Could not select the account Tab.')
        self.field_update('ldapserver.loginname', login_name)
        self.field_update('ldapserver.firstname', first_name)
        self.field_update('ldapserver.surname', surname)
        self.field_update('ldapserver.mail', mail)
        if photo:
            self.field_update('ldapserver.photo', photo)
        self.click(common_locators['submit'])

    def search(self, name):
        """Searches existing ldap auth source from UI."""
        Navigator(self.browser).go_to_ldap_auth()
        strategy1, value1 = locators['ldapserver.ldap_servername']
        element = self.wait_until_element((strategy1, value1 % (name, name)))
        if element is None:
            raise UINoSuchElementError(
                u'Could not search the entity "{0}".'
                .format(name)
            )
        return element

    def delete(self, name, really=False):
        """Deletes existing ldap auth source from UI."""
        Navigator(self.browser).go_to_ldap_auth()
        strategy1, value1 = locators['ldapserver.ldap_delete']
        element = self.wait_until_element((strategy1, value1 % name))
        if element is None:
            raise UINoSuchElementError(
                u'Could not select the entity "{0}" for deletion.'
                .format(name)
            )
        element.click()
        self.handle_alert(really)
