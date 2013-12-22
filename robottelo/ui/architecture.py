#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Architecture UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.common.keys import Keys


class Architecture(Base):
    """
    Manipulates architecture from UI
    """

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, os_name=None):
        """
        Creates new architecture from UI with existing OS
        """
        self.wait_until_element(locators["arch.new"]).click()
        if self.wait_until_element(locators["arch.name"]):
            self.field_update("arch.name", name)
        if os_name:
            self.select_entity("arch.os_name", "arch.select_os_name",
                               os_name, None)
        self.find_element(locators["arch.submit"]).click()
        self.wait_for_ajax()

    def remove(self, name, really):
        """
        Delete existing architecture from UI
        """
        element = self.wait_until_element((locators["arch.delete"][0],
                                           locators["arch.delete"][1]
                                           % name))
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss()

    def search(self, name):
        """
        Search existing arch name
        """
        searchbox = self.wait_until_element(locators["search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(name)
            searchbox.send_keys(Keys.RETURN)
            arch = self.wait_until_element((locators["arch.arch_name"][0],
                                            locators["arch.arch_name"][1]
                                            % name))
            if arch:
                arch.click()
        return arch

    def update(self, oldname, newname, new_osname):
        """
        Update existing arch's name and OS
        """
        element = self.wait_until_element((locators["arch.arch_name"][0],
                                           locators["arch.arch_name"][1]
                                           % oldname))
        if element:
            element.click()
        if self.wait_until_element(locators["arch.name"]):
            self.field_update("arch.name", newname)
        if new_osname:
            self.select_entity("arch.os_name", "arch.select_os_name",
                               new_osname, None)
        self.find_element(locators["arch.submit"]).click()
        self.wait_for_ajax()
