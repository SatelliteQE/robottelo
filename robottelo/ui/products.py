"""
Implements Products UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from selenium.webdriver.support.select import Select


class Products(Base):
    """
    Manipulates Products from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, name, description=None, provider=None,
               create_provider=False, sync_plan=None, create_sync_plan=False,
               gpg_key=None, sync_interval=None, startdate=None):
        """
        Creates new product from UI
        """
        self.find_element(locators["prd.new"]).click()
        self.wait_for_ajax()
        self.text_field_update(common_locators["name"], name)
        if provider and not create_provider:
            type_ele = self.find_element(locators["prd.provider"])
            Select(type_ele).select_by_visible_text(provider)
        elif provider and create_provider:
            self.find_element(locators["prd.new_provider"]).click()
            self.text_field_update(common_locators["name"], name)
            self.find_element(common_locators["create"]).click()
            self.wait_for_ajax()
        if sync_plan and not create_sync_plan:
            type_ele = self.find_element(locators["prd.sync_plan"])
            Select(type_ele).select_by_visible_text(sync_plan)
        elif sync_plan and create_sync_plan:
            self.find_element(locators["prd.new_sync_plan"]).click()
            self.text_field_update(common_locators["name"], name)
            if sync_interval:
                type_ele = self.find_element(locators["prd.sync_interval"])
                Select(type_ele).select_by_visible_text(sync_interval)
            self.text_field_update(locators["prd.sync_startdate"], startdate)
            self.find_element(common_locators["create"]).click()
            self.wait_for_ajax()
        if gpg_key:
            type_ele = self.find_element(common_locators["gpg_key"])
            Select(type_ele).select_by_visible_text(gpg_key)
        self.text_field_update(common_locators["description"], description)
        self.find_element(common_locators["create"]).click()

    def delete(self, product, really):
        """
        Delete a product from UI
        """
        strategy = locators["prd.select"][0]
        value = locators["prd.select"][1]
        self.wait_until_element((strategy, value % product)).click()
        self.wait_until_element(locators["prd.remove"]).click()
        if really:
            self.wait_until_element(common_locators["confirm_remove"]).click()
        else:
            self.wait_until_element(common_locators["cancel"]).click()

    def search(self, name):
        """
        Searches existing product from UI
        """
        element = self.search_entity(name, locators["prd.select"],
                                     katello=True)
        return element
