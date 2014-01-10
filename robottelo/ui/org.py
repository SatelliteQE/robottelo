# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Org UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators


class Org(Base):
    """
    Provides the CRUD functionality for Organization
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, org_name=None,):
        """
        Create Organization in UI
        """
        if self.wait_until_element(locators["org.new"]):
            self.wait_until_element(locators["org.new"]).click()
            self.wait_until_element(locators["org.name"])
            self.field_update("org.name", org_name)
            self.wait_until_element(common_locators["submit"]).click()
            self.wait_until_element(locators["org.proceed_to_edit"]).click()
            self.wait_until_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Unable to create the Organization '%s'" % org_name)

    def update(self, org_name, new_name=None,):
        """
        Update Organization in UI
        """
        org_object = self.search(org_name, locators["org.org_name"])
        self.wait_for_ajax()
        if org_object:
            org_object.click()
            if new_name:
                if self.wait_until_element(locators["org.name"]):
                    self.field_update("org.name", new_name)
            self.wait_until_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Unable to find the organization '%s' for update." % org_name)

    def remove(self, org_name, really):
        """
        Remove Organization in UI
        """
        self.search(org_name, locators["org.org_name"])
        self.wait_until_element(locators["org.dropdown"])
        dropdown = self.find_element(locators["org.dropdown"])
        if dropdown:
            dropdown.click()
            self.wait_for_ajax()
            element = self.wait_until_element(
                (locators["org.delete"][0],
                 locators["org.delete"][1] % org_name))
            if element:
                element.click()
                if really:
                    alert = self.browser.switch_to_alert()
                    alert.accept()
                else:
                    alert = self.browser.switch_to_alert()
                    alert.dismiss()
                self.wait_for_ajax()
            else:
                raise Exception(
                    "Unable to find the organization '%s'" % org_name)
        else:
            raise Exception(
                "Unable to find the organization dropdown for '%s'" % org_name)
