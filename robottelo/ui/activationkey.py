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

    def create(self, name, description=None, content_view=None):
        """
        Creates new activation key from UI
        """

        self.wait_until_element(locators["ak.new"]).click()

        if self.wait_until_element(locators["ak.name"]):
            self.field_update("ak.name", name)
            if description:
                if self.wait_until_element(locators
                                           ["ak.description"]):
                    self.field_update("ak.description", description)
            if content_view:
                Select(self.find_element
                       (locators["ak.content_view"]
                        )).select_by_visible_text(content_view)
            self.scroll_right_pane()
            self.wait_until_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new activation key '%s'" % name)
