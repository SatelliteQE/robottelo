# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Medium UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.support.select import Select


class Medium(Base):
    """
    Implements the CRUD functions for Installation media
    """

    def __init__(self, browser):
        """
        Sets the browser object
        """
        self.browser = browser

    def create(self, name, path, os_family=None):
        """
        Creates new Installation media
        """

        self.wait_until_element(locators["medium.new"]).click()

        if self.wait_until_element(locators["medium.name"]):
            self.find_element(locators["medium.name"]).send_keys(name)
            if self.wait_until_element(locators["medium.path"]):
                self.find_element(locators["medium.path"]).send_keys(path)
            if os_family:
                Select(self.find_element(locators
                                         ["medium.os_family"]
                                         )).select_by_visible_text(os_family)
            self.find_element(locators["submit"]).click()
            self.wait_for_ajax()

    def remove(self, name, really):
        """
        Delete Installation media
        """

        element = self.search(name, locators['medium.delete'])

        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss()
        else:
            raise Exception(
                "Could not remove the installation media '%s'" % name)
        self.wait_for_ajax()

    def update(self, oldname, newname=None, newpath=None, new_os_family=None):
        """
        Update installation media name, media path and OS family
        """

        element = self.search(oldname, locators['medium.medium_name'])

        if element:
            element.click()
        if self.wait_until_element(locators["medium.name"]):
            self.field_update("medium.name", newname)
        if newpath:
            if self.wait_until_element(locators["medium.path"]):
                self.field_update("medium.path", newpath)
        if new_os_family:
            Select(self.find_element(locators
                                     ["medium.os_family"]
                                     )).select_by_visible_text(new_os_family)
        self.find_element(locators["submit"]).click()
        self.wait_for_ajax()
