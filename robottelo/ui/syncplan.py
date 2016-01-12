"""Implements Sync Plans for UI."""
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class Syncplan(Base):
    """Manipulates Sync Plans from UI."""
    is_katello = True
    result_timeout = 20

    def navigate_to_entity(self):
        """Navigate to Sync Plan entity page"""
        Navigator(self.browser).go_to_sync_plans()

    def _search_locator(self):
        """Specify locator for Sync Plan entity search procedure"""
        return locators['sp.select']

    def add_remove_products(self, products=None, tab_locator=None,
                            select_locator=None):
        """Add and Remove product association to Sync plans."""
        strategy, value = locators['sp.prd_select']
        self.click(tab_locators['sp.tab_products'])
        self.click(tab_locator)
        for prd in products:
            self.click((strategy, value % prd))
        self.click(select_locator)

    def create(self, name, description=None, startdate=None,
               sync_interval=None, start_hour=None, start_minute=None,):
        """Creates new Sync Plans from UI."""
        self.click(locators['sp.new'])
        self.text_field_update(common_locators['name'], name)
        if sync_interval:
            type_ele = self.find_element(locators['sp.interval'])
            Select(type_ele).select_by_visible_text(sync_interval)
        if description:
            self.text_field_update(common_locators['description'], description)
            self.wait_for_ajax()
        if start_hour and start_minute:
            self.text_field_update(locators['sp.start_hour'], start_hour)
            self.text_field_update(locators['sp.start_minutes'], start_minute)
        if startdate:
            self.text_field_update(locators['sp.start_date'], startdate)
            self.wait_for_ajax()
        self.click(common_locators['name'])
        self.click(common_locators['create'])

    def update(self, name, new_name=None, new_desc=None,
               new_sync_interval=None, add_products=None,
               rm_products=None):
        """Updates Sync Plans from UI."""
        sp_element = self.search(name)
        if sp_element is None:
            raise UIError(
                'Unable to find the sync_plan "{0}" for update.'.format(name)
            )
        sp_element.click()
        self.wait_for_ajax()
        self.click(tab_locators['sp.tab_details'])
        if new_name:
            self.click(locators['sp.name_edit'])
            self.text_field_update(locators['sp.name_update'], new_name)
            self.click(common_locators['save'])
        if new_desc:
            self.click(locators['sp.desc_edit'])
            self.text_field_update(locators['sp.desc_update'], new_name)
            self.click(common_locators['save'])
        if new_sync_interval:
            self.click(locators['sp.sync_interval_edit'])
            type_ele = self.wait_until_element(
                locators['sp.sync_interval_update'])
            Select(type_ele).select_by_visible_text(new_sync_interval)
            self.click(common_locators['save'])
        if add_products:
            tab_loc = tab_locators['sp.add_prd']
            select_loc = locators['sp.add_selected']
            self.add_remove_products(
                products=add_products,
                tab_locator=tab_loc,
                select_locator=select_loc
            )
        if rm_products:
            tab_loc = tab_locators['sp.list_prd']
            select_loc = locators['sp.remove_selected']
            self.add_remove_products(
                products=rm_products,
                tab_locator=tab_loc,
                select_locator=select_loc
            )

    def delete(self, name, really=True):
        """Deletes a sync_plan from UI."""
        self.delete_entity(
            name,
            really,
            locators['sp.remove'],
        )
