#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import locators
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select


class Hostgroup(Base):

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, parent = None, environment = None):
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
            hostgroup = self.wait_until_element((locators["hostgroups.hostgroup"][0], locators["hostgroups.hostgroup"][1] % name))
        return hostgroup

    def delete(self, name, really=False):
        self.search(name)
        element = self.wait_until_element((locators["hostgroups.delete"][0], locators["hostgroups.delete"][1] % name))
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss(self)


    #def update(self, name, new_name = None, parent = None, environment = None):