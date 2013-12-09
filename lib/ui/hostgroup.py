#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from lib.ui.base import Base
from lib.ui.locators import locators
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select


class Hostgroup(Base):

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, parent=None, environment=None):
        self.wait_until_element(locators["hostgroups.new"]).click()

        if self.wait_until_element(locators["hostgroups.name"]):
            self.find_element(locators["hostgroups.name"]).send_keys(name)
            if parent:
                Select(self.find_element(locators["hostgroups.parent"])).select_by_visible_text(parent)
            if environment:
                Select(self.find_element(locators["hostgroups.environment"])).select_by_visible_text(environment)
            self.find_element(locators["submit"]).click()

    def search(self, name):
        hostgroup = None
        searchbox = self.wait_until_element(locators["search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(name)
            searchbox.send_keys(Keys.RETURN)
            hostgroup = self.wait_until_element((locators["hostgroups.hostgroup"][0],
                                                 locators["hostgroups.hostgroup"][1] % name))
        return hostgroup

    def delete(self, name, really=False):
        dropdown = self.wait_until_element((locators["hostgroups.dropdown"][0],
                                           locators["hostgroups.dropdown"][1] % name))
        if dropdown:
            dropdown.click()
            element = self.wait_until_element((locators["hostgroups.delete"][0],
                                              locators["hostgroups.delete"][1] % name))
            if element:
                element.click()
                if really:
                    alert = self.browser.switch_to_alert()
                    alert.accept()
                else:
                    alert = self.browser.switch_to_alert()
                    alert.dismiss()

    def update(self, name, new_name=None, parent=None, environment=None):
        element = self.search(name)
        if element:
            element.click()
            self.wait_for_ajax()
            if parent:
                Select(self.find_element(locators["hostgroups.parent"])).select_by_visible_text(parent)
            if environment:
                Select(self.find_element(locators["hostgroups.environment"])).select_by_visible_text(environment)
            if new_name:
                self.field_update("hostgroups.name",new_name)
            self.find_element(locators["submit"]).click()
