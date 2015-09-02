"""Implements Products UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from selenium.webdriver.support.select import Select


class Products(Base):
    """Manipulates Products from UI"""

    def create(self, name, description=None, sync_plan=None, startdate=None,
               create_sync_plan=False, gpg_key=None, sync_interval=None):
        """Creates new product from UI"""
        self.click(locators['prd.new'])
        self.text_field_update(common_locators['name'], name)
        if sync_plan and not create_sync_plan:
            type_ele = self.find_element(locators['prd.sync_plan'])
            Select(type_ele).select_by_visible_text(sync_plan)
        elif sync_plan and create_sync_plan:
            self.click(locators['prd.new_sync_plan'])
            self.text_field_update(common_locators['name'], name)
            if sync_interval:
                type_ele = self.find_element(locators['prd.sync_interval'])
                Select(type_ele).select_by_visible_text(sync_interval)
            self.text_field_update(locators['prd.sync_startdate'], startdate)
            self.click(common_locators['create'])
        if gpg_key:
            type_ele = self.find_element(common_locators['gpg_key'])
            Select(type_ele).select_by_visible_text(gpg_key)
        if description:
            self.text_field_update(common_locators['description'], description)
            self.wait_for_ajax()
        self.click(common_locators['create'])

    def update(self, name, new_name=None, new_desc=None,
               new_sync_plan=None, new_gpg_key=None):
        """Updates product from UI"""
        prd_element = self.search_entity(
            name, locators['prd.select'], katello=True)
        if prd_element:
            prd_element.click()
            self.wait_for_ajax()
            self.click(tab_locators['prd.tab_details'])
            if new_name:
                self.click(locators['prd.name_edit'])
                self.text_field_update(locators['prd.name_update'], new_name)
                self.click(common_locators['save'])
            if new_desc:
                self.click(locators['prd.desc_edit'])
                self.text_field_update(locators['prd.desc_update'], new_name)
                self.click(common_locators['create'])
            if new_gpg_key:
                self.click(locators['prd.gpg_key_edit'])
                type_ele = self.find_element(locators['prd.gpg_key_update'])
                Select(type_ele).select_by_visible_text(new_gpg_key)
                self.wait_for_ajax()
                self.click(common_locators['create'])
            if new_sync_plan:
                self.click(locators['prd.sync_plan_edit'])
                type_ele = self.find_element(locators['prd.sync_plan_update'])
                Select(type_ele).select_by_visible_text(new_sync_plan)
                self.click(common_locators['create'])

    def delete(self, product, really=True):
        """Delete a product from UI"""
        strategy, value = locators['prd.select']
        self.click((strategy, value % product))
        self.click(locators['prd.remove'])
        if really:
            self.click(common_locators['confirm_remove'])
        else:
            self.click(common_locators['cancel'])

    def search(self, name):
        """Searches existing product from UI"""
        element = self.search_entity(
            name, locators['prd.select'], katello=True)
        return element
