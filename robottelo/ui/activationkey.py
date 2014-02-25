# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Activation keys UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from selenium.webdriver.support.select import Select


class ActivationKey(Base):
    """
    Manipulates Activation keys from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def set_limit(self, limit):
        """
        Sets the finite limit of activation key
        """
        limit_checkbox_locator = locators["ak.usage_limit_checkbox"]
        unlimited_set = self.find_element(limit_checkbox_locator
                                          ).get_attribute("checked")
        if unlimited_set is None and limit == "Unlimited":
            self.find_element(limit_checkbox_locator).click()
        elif unlimited_set:
            self.find_element(limit_checkbox_locator).click()
            self.field_update("ak.usage_limit", limit)

    def create(self, name, env, limit=None, description=None,
               content_view=None):
        """
        Creates new activation key from UI
        """

        self.wait_for_ajax()
        self.wait_until_element(locators["ak.new"]).click()

        if self.wait_until_element(common_locators["name"]):
            self.text_field_update(common_locators["name"], name)
            if limit:
                self.set_limit(limit)
            if description:
                self.text_field_update(common_locators
                                       ["description"], description)
            if env:
                strategy = locators["ak.env"][0]
                value = locators["ak.env"][1]
                element = self.wait_until_element((strategy, value % env))
                if element:
                    element.click()
                    self.wait_for_ajax()
            else:
                raise Exception(
                    "Could not create new activation key '%s', \
                    without env" % name)
            if content_view:
                Select(self.find_element
                       (locators["ak.content_view"]
                        )).select_by_visible_text(content_view)
            else:
                Select(self.find_element
                       (locators["ak.content_view"]
                        )).select_by_value("0")
            self.wait_until_element(common_locators["create"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new activation key '%s'" % name)

    def search_key(self, element_name):
        """
        Uses the search box to locate an element from a list of elements.
        """

        element = None

        searchbox = self.wait_until_element(common_locators["kt_search"])

        if searchbox:
            searchbox.clear()
            searchbox.send_keys(element_name)
            self.wait_for_ajax()
            self.find_element(common_locators["kt_search_button"]).click()
            strategy = locators["ak.ak_name"][0]
            value = locators["ak.ak_name"][1]
            element = self.wait_until_element((strategy, value % element_name))
        return element

    def update(self, name, new_name=None, description=None,
               limit=None, content_view=None):
        """
        Updates an existing activation key
        """

        element = self.search_key(name)

        if element:
            element.click()
            self.wait_for_ajax()
            if new_name:
                self.edit_entity("ak.edit_name", "ak.edit_name_text",
                                 new_name, "ak.save_name")
            if description:
                self.edit_entity("ak.edit_description",
                                 "ak.edit_description_text",
                                 description, "ak.save_description")
            if limit:
                self.find_element(locators["ak.edit_limit"]).click()
                self.set_limit(limit)
                self.find_element(locators["ak.save_limit"]).click()
            if content_view:
                self.find_element(locators["ak.edit_content_view"]).click()
                Select(self.find_element
                       (locators["ak.edit_content_view_select"]
                        )).select_by_visible_text(content_view)
        else:
            raise Exception("Could not update the activation key '%s'" % name)
