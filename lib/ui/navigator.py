#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import *

class Navigator(Base):
    """
    Quickly navigate through menus and tabs.
    """

    def __init__(self, browser):
        self.browser = browser

    def go_to_organizations(self):
        self.find_element(locators["menu.administer"]).click()
        self.find_element(locators["submenu.organizations"]).click()

    def go_to_users(self):
        self.find_element(locators["menu.administer"]).click()
        self.find_element(locators["submenu.users"]).click()

    def go_to_roles(self):
        self.find_element(locators["menu.administer"]).click()
        self.find_element(locators["submenu.roles"]).click()

    def go_to_about(self):
        self.find_element(locators["menu.administer"]).click()
        self.find_element(locators["submenu.about"]).click()

    def go_to_foreman(self):
#        self.browser.find_element_by_link_text('Provisioning').click()
        self.browser.find_element_by_xpath("//img[@class='link_icon icon']").click()
