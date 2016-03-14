"""Implements Products UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Products(Base):
    """Manipulates Products from UI"""
    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Product entity page"""
        Navigator(self.browser).go_to_products()

    def _search_locator(self):
        """Specify locator for Product key entity search procedure"""
        return locators['prd.select']

    def create(self, name, description=None, sync_plan=None, startdate=None,
               create_sync_plan=False, gpg_key=None, sync_interval=None):
        """Creates new product from UI"""
        self.click(locators['prd.new'])
        self.text_field_update(common_locators['name'], name)
        if sync_plan and not create_sync_plan:
            self.select(locators['prd.sync_plan'], sync_plan)
        elif sync_plan and create_sync_plan:
            self.click(locators['prd.new_sync_plan'])
            self.text_field_update(common_locators['name'], name)
            if sync_interval:
                self.select(locators['prd.sync_interval'], sync_interval)
            self.text_field_update(locators['prd.sync_startdate'], startdate)
            self.click(common_locators['create'])
        if gpg_key:
            self.select(common_locators['gpg_key'], gpg_key)
        if description:
            self.text_field_update(common_locators['description'], description)
            self.wait_for_ajax()
        self.click(common_locators['create'])

    def update(self, name, new_name=None, new_desc=None,
               new_sync_plan=None, new_gpg_key=None):
        """Updates product from UI"""
        prd_element = self.search(name)
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
                self.click(common_locators['save'])
            if new_gpg_key:
                self.click(locators['prd.gpg_key_edit'])
                self.select(locators['prd.gpg_key_update'], new_gpg_key)
                self.click(common_locators['save'])
            if new_sync_plan:
                self.click(locators['prd.sync_plan_edit'])
                self.select(locators['prd.sync_plan_update'], new_sync_plan)
                self.click(common_locators['save'])

    def delete(self, name, really=True):
        """Delete a product from UI"""
        self.delete_entity(
            name,
            really,
            locators['prd.remove'],
        )
