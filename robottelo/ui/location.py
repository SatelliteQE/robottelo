# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Locations UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from robottelo.common.constants import FILTER
from selenium.webdriver.support.select import Select


class Location(Base):
    """
    Implements CRUD functions for UI
    """

    def __init__(self, browser):
        """
        Sets the browser object
        """
        self.browser = browser

    def create(self, name, parent=None, user_names=None):
        """
        Creates new Location from UI
        """

        self.wait_until_element(locators["location.new"]).click()

        if self.wait_until_element(locators["location.name"]):
            self.field_update("location.name", name)
            if parent:
                Select(self.find_element(
                    locators["location.parent"])
                    ).select_by_visible_text(parent)
            self.wait_until_element(common_locators["submit"]).click()
            self.wait_until_element(
                locators["location.proceed_to_edit"]).click()
            if user_names:
                self.configure_entity(user_names, FILTER['location_user'])
            self.wait_until_element(common_locators["submit"]).click()
        else:
            raise Exception("Could not create new location.")
