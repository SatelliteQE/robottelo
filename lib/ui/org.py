#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from locators import *

class Org(Base):

    def __init__(self, browser):
        self.browser = browser

    def create_org(self, org_name, org_label, org_desc):
        if self.wait_until_element(locators["orgs.new"]):
            self.find_element(locators["orgs.new"]).click()
        if self.wait_until_element(locators["orgs.name"]):
            name_field = self.find_element(locators["orgs.name"])
            name_field.click()
            name_field.send_keys(org_name)
            desc_field = self.find_element(locators["orgs.description"])
            desc_field.click()
            desc_field.send_keys(org_desc)
            label_field = self.find_element(locators["orgs.label"])
            label_field.clear()
            label_field.send_keys(org_label)
            self.find_element(locators["org.new_org_save_button"]).click()



