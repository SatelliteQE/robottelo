#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import locators
from selenium.webdriver.common.keys import Keys


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
                if self.wait_until_element(locators["medium.os_family"]):
                    select = self.browser.find_element_by_tag_name("select")
                    all_options = select.find_elements_by_tag_name("option")
                    for option in all_options:
                        if option.get_attribute("value") == os_family:
                            option.click()
                            break
            self.find_element(locators["submit"]).click()
     
    def remove(self, name, really):
        element = self.wait_until_element((locators["medium.delete"][0], locators["medium.delete"][1] % name))
        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss()
  
    def search(self, name):
        searchbox = self.wait_until_element(locators["search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(name)
            searchbox.send_keys(Keys.RETURN)
            arch = self.wait_until_element((locators["medium.medium_name"][0], locators["medium.medium_name"][1] % name))
            if arch:
                arch.click()
        return arch
 
    def update(self, oldname, newname=None, newpath=None, new_os_family=None):
        element = self.wait_until_element((locators["medium.medium_name"][0], locators["medium.medium_name"][1] % oldname))
        if element:
            element.click()
        if self.wait_until_element(locators["medium.name"]):
            txt_field = self.find_element(locators["medium.name"])
            txt_field.clear()
            txt_field.send_keys(newname)
        if newpath:
            if self.wait_until_element(locators["medium.path"]):
                txt_field = self.find_element(locators["medium.path"])
                txt_field.clear()
                txt_field.send_keys(newpath)
        if new_os_family:
            if self.wait_until_element(locators["medium.os_family"]):
                select = self.browser.find_element_by_tag_name("select")
                all_options = select.find_elements_by_tag_name("option")
                for option in all_options:
                    if option.get_attribute("value") == new_os_family:
                        option.click()
                        break
        self.find_element(locators["submit"]).click()
