#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Medium UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select


class Medium(Base):

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, path, os_family=None):
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
        element = self.wait_until_element((locators
                                           ["medium.delete"][0],
                                           locators
                                           ["medium.delete"][1] % name))
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss()
            self.wait_for_ajax()

    def search(self, name):
        searchbox = self.wait_until_element(locators["search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(name)
            searchbox.send_keys(Keys.RETURN)
            medium = self.wait_until_element((locators
                                              ["medium.medium_name"][0],
                                              locators
                                              ["medium.medium_name"][1] % name))
            if medium:
                medium.click()
        return medium

    def update(self, oldname, newname=None, newpath=None, new_os_family=None):
        element = self.wait_until_element((locators
                                           ["medium.medium_name"][0],
                                           locators
                                           ["medium.medium_name"][1] % oldname))
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
