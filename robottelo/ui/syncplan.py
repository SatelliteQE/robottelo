"""
Implements Sync Plans for UI
"""

from robottelo.ui.base import Base
from robottelo.common.constants import SYNC_INTERVAL
from robottelo.ui.locators import locators, common_locators, tab_locators
from selenium.webdriver.support.select import Select


class Products(Base):
    """
    Manipulates Sync Plans from UI
    """

    def create(self, name, description=None, startdate=None,
               sync_interval=SYNC_INTERVAL["hour"], start_hour=None,
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
               new_sync_interval=None):
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
                type_ele = self.find_element(interval_update_loc)
                Select(type_ele).select_by_visible_text(new_sync_interval)
                self.wait_for_ajax()
                self.find_element(common_locators["save"]).click()

    def delete(self, sync_plan, really):
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
