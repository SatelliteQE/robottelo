#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from locators import *

class Navigator():
    """
    Quickly navigate through menus and tabs.
    """

    def __init__(self, browser):
        self.browser = browser

    def go_to_organizations(self):
        self.browser.find_by_xpath(locators["menu.administer"]).click()
        self.browser.find_by_xpath(locators["submenu.organizations"]).click()

    def go_to_users(self):
        self.browser.find_by_xpath(locators["menu.administer"]).click()
        self.browser.find_by_xpath(locators["submenu.users"]).click()

    def go_to_roles(self):
        self.browser.find_by_xpath(locators["menu.administer"]).click()
        self.browser.find_by_xpath(locators["submenu.roles"]).click()

    def go_to_about(self):
        self.browser.find_by_xpath(locators["menu.administer"]).click()
        self.browser.find_by_xpath(locators["submenu.about"]).click()
