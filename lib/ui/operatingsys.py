#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import *

from selenium.webdriver.common.alert import Alert


class OperatingSys(Base):
    
    def __init__(self, browser):
        self.browser = browser
        
    def create(self, osname, major_version=None, minor_version=None, os_family=None):
        self.wait_until_element(locators["operatingsys.new"]).click()
        
        if self.wait_until_element(locators["operatingsys.name"]):
            self.find_element(locators["operatingsys.name"]).send_keys(osname)
        
            if self.wait_until_element(locators["operatingsys.majorversion"]):
                self.find_element(locators["operatingsys.majorversion"]).send_keys(major_version)     
            
            if minor_version:
                if self.wait_until_element(locators["operatingsys.minorversion"]):
                    self.find_element(locators["operatingsys.minorversion"]).send_keys(minor_version)
                 
            if os_family:
                if self.wait_until_element(locators["operatingsys.family"]):
                    select = self.browser.find_element_by_tag_name("select")
                    allOptions = select.find_elements_by_tag_name("option")
                    for option in allOptions:
                        if option.get_attribute("value") == os_family:
                            option.click()
                            break
            self.find_element(locators["operatingsys.submit"]).click()
            
            