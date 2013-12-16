#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from time import sleep


class PartitionTable(Base):

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, layout=None, os_family=None):
        self.wait_until_element(locators["ptable.new"]).click()
        if self.wait_until_element(locators["ptable.name"]):
            self.find_element(locators["ptable.name"]).send_keys(name)
            if self.wait_until_element(locators["ptable.layout"]):
                self.find_element(locators["ptable.layout"]).send_keys(layout)
            if os_family:
                Select(self.find_element(locators
                                         ["ptable.os_family"]
                                         )).select_by_visible_text(os_family)
            self.find_element(locators["submit"]).click()
            self.wait_for_ajax()


    def remove(self, name, really):
        element = self.wait_until_element((locators
                                           ["ptable.delete"][0],
                                           locators
                                           ["ptable.delete"][1] % name))
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
            ptable = self.wait_until_element((locators
                                              ["ptable.ptable_name"][0],
                                              locators
                                              ["ptable.ptable_name"][1]
                                              % name))
            if ptable:
                ptable.click()
        return ptable

    def update(self, oldname, new_name=None,
               new_layout=None, new_os_family=None):
        element = self.wait_until_element((locators
                                           ["ptable.ptable_name"][0],
                                           locators
                                           ["ptable.ptable_name"][1]
                                           % oldname))
        if element:
            element.click()
        if self.wait_until_element(locators["ptable.name"]):
            txt_field = self.find_element(locators["ptable.name"])
            txt_field.clear()
            txt_field.send_keys(new_name)
        if new_layout:
            if self.wait_until_element(locators["ptable.layout"]):
                txt_field = self.find_element(locators["ptable.layout"])
                txt_field.clear()
                txt_field.send_keys(new_layout)
        if new_os_family:
            Select(self.find_element(locators
                                     ["ptable.os_family"]
                                     )).select_by_visible_text(new_os_family)
        self.find_element(locators["submit"]).click()
        self.wait_for_ajax()
