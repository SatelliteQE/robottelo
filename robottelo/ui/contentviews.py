# -*- encoding: utf-8 -*-

"""
Implements Content Views UI
"""

from robottelo.common.helpers import escape_search
from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators


class ContentViews(Base):
    """
    Manipulates Content Views from UI
    """

    def create(self, name, label=None, description=None, is_composite=False):
        """Creates a content view"""

        self.wait_until_element(locators["contentviews.new"]).click()

        if self.wait_until_element(common_locators["name"]):
            self.find_element(common_locators
                              ["name"]).send_keys(name)
            timeout = 60 if len(name) > 50 else 30
            self.wait_for_ajax(timeout)

            if label is not None:
                self.find_element(common_locators["label"]).send_keys(label)

            if description is not None:
                self.find_element(
                    common_locators["description"]).send_keys(description)

            if is_composite:
                self.find_element(
                    locators["contentviews.composite"]).click()

            self.wait_for_ajax()
            self.wait_until_element(common_locators["create"]).click()
            self.wait_for_ajax()
            self.wait_until_element(locators['contentviews.publish'])
        else:
            raise Exception(
                "Could not create new content view '%s'" % name)

    def search(self, element_name):
        """Uses the search box to locate an element from a list of elements """

        element = None
        strategy = locators["contentviews.key_name"][0]
        value = locators["contentviews.key_name"][1]
        searchbox = self.wait_until_element(common_locators["kt_search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(escape_search(element_name))
            self.wait_for_ajax()
            self.find_element(common_locators["kt_search_button"]).click()
            element = self.wait_until_element((strategy, value % element_name))
            return element

    def update(self, name, new_name=None, new_description=None):
        """Updates an existing content view"""

        element = self.search(name)

        if element:
            element.click()
            self.wait_for_ajax()
            self.find_element(tab_locators['contentviews.info']).click()

            if new_name:
                self.edit_entity(
                    "contentviews.edit_name",
                    "contentviews.edit_name_text", new_name,
                    "contentviews.save_name")
                self.wait_for_ajax()

            if new_description:
                self.edit_entity(
                    "contentviews.edit_description",
                    "contentviews.edit_description_text", new_description,
                    "contentviews.save_description")
                self.wait_for_ajax()
        else:
            raise Exception("Could not update the content view '%s'" % name)
