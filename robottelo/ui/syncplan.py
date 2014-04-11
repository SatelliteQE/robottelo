"""
Implements Sync Plans for UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from selenium.webdriver.support.select import Select


class Syncplan(Base):
    """
    Manipulates Sync Plans from UI
    """

    def add_remove_products(self, products=None, tab_locator=None,
                            select_locator=None):
        strategy = locators["sp.prd_select"][0]
        value = locators["sp.prd_select"][1]
        self.wait_until_element(tab_locators["sp.tab_products"]).\
            click()
        self.wait_for_ajax()
        self.wait_until_element(tab_locator).click()
        self.wait_for_ajax()
        for prd in products:
            self.wait_until_element((strategy, value % prd)).click()
        self.wait_until_element(select_locator).click()
        self.wait_for_ajax()

    def create(self, name, description=None, startdate=None,
               sync_interval=None, start_hour=None,
               start_minute=None):
        """
        Creates new Sync Plans from UI
        """
        self.wait_until_element(locators["sp.new"]).click()
        self.wait_for_ajax()
        self.text_field_update(common_locators["name"], name)
        if sync_interval:
            type_ele = self.find_element(locators["sp.interval"])
            Select(type_ele).select_by_visible_text(sync_interval)
        if description:
            self.text_field_update(common_locators["description"], description)
            self.wait_for_ajax()
        if startdate:
            self.text_field_update(locators["sp.start_date"], name)
        if start_hour and start_minute:
            self.text_field_update(locators["sp.start_hour"], name)
            self.text_field_update(locators["sp.start_minute"], name)
        self.wait_until_element(common_locators["create"]).click()
        self.wait_for_ajax()

    def update(self, name, new_name=None, new_desc=None,
               new_sync_interval=None, add_products=None,
               rm_products=None):
        """
        Updates Sync Plans from UI
        """
        sp_element = self.search_entity(name, locators["sp.select"],
                                        katello=True)
        if sp_element:
            sp_element.click()
            self.wait_for_ajax()
            self.wait_until_element(tab_locators["sp.tab_details"]).click()
            self.wait_for_ajax()
            if new_name:
                self.wait_until_element(locators["sp.name_edit"]).click()
                self.text_field_update(locators["sp.name_update"], new_name)
                self.find_element(common_locators["save"]).click()
                self.wait_for_ajax()
            if new_desc:
                self.wait_until_element(locators["sp.desc_edit"]).click()
                self.text_field_update(locators["sp.desc_update"], new_name)
                self.find_element(common_locators["save"]).click()
            if new_sync_interval:
                self.wait_until_element(locators["sp.sync_interval_edit"]).\
                    click()
                interval_update_loc = locators["sp.sync_interval_update"]
                type_ele = self.wait_until_element(interval_update_loc)
                Select(type_ele).select_by_visible_text(new_sync_interval)
                self.wait_until_element(common_locators["save"]).click()
                self.wait_for_ajax()
            if add_products:
                tab_loc = tab_locators["sp.add_prd"]
                select_loc = locators["sp.add_selected"]
                self.add_remove_products(products=add_products,
                                         tab_locator=tab_loc,
                                         select_locator=select_loc)
            if rm_products:
                tab_loc = tab_locators["sp.list_prd"]
                select_loc = locators["sp.remove_selected"]
                self.add_remove_products(products=rm_products,
                                         tab_locator=tab_loc,
                                         select_locator=select_loc)
        else:
            raise Exception(
                "Unable to find the sync_plan '%s' for update." % name)

    def delete(self, sync_plan, really=True):
        """
        Deletes a sync_plan from UI
        """
        strategy = locators["sp.select"][0]
        value = locators["sp.select"][1]
        self.wait_until_element((strategy, value % sync_plan)).click()
        self.wait_for_ajax()
        self.wait_until_element(locators["sp.remove"]).click()
        if really:
            self.wait_until_element(common_locators["confirm_remove"]).click()
            self.wait_for_ajax()
        else:
            self.wait_until_element(common_locators["cancel"]).click()

    def search(self, name):
        """
        Searches existing sync_plan from UI
        """
        element = self.search_entity(name, locators["sp.select"],
                                     katello=True)
        return element
