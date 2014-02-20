#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.ui.base import Base
from robottelo.ui.locators import locators


class OperatingSys(Base):

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, major_version=None,
               minor_version=None, os_family=None):
        self.wait_until_element(locators["operatingsys.new"]).click()
        if self.wait_until_element(locators["operatingsys.name"]):
            self.find_element(locators["operatingsys.name"]).send_keys(name)
            if self.wait_until_element(locators["operatingsys.major_version"]):
                self.find_element(locators["operatingsys.major_version"]).send_keys(major_version)
            if minor_version:
                if self.wait_until_element(locators["operatingsys.minor_version"]):
                    self.find_element(locators["operatingsys.minor_version"]).send_keys(minor_version)
            if os_family:
                if self.wait_until_element(locators["operatingsys.family"]):
                    select = self.browser.find_element_by_tag_name("select")
                    allOptions = select.find_elements_by_tag_name("option")
                    for option in allOptions:
                        if option.get_attribute("value") == os_family:
                            option.click()
                            break
            self.find_element(locators["operatingsys.submit"]).click()

    def delete(self, osname, really):
        element = self.wait_until_element((locators["operatingsys.delete"][0], locators["operatingsys.delete"][1] % osname))
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss(self)
