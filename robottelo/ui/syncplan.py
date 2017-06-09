"""Implements Sync Plans for UI."""
import datetime

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


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
        self.assign_value(common_locators['name'], name)
        if sync_interval:
            self.assign_value(locators['sp.interval'], sync_interval)
        if description:
            self.assign_value(common_locators['description'], description)
        if start_hour and start_minute:
            self.assign_value(locators['sp.start_hour'], start_hour)
            self.assign_value(locators['sp.start_minutes'], start_minute)
        if not startdate:
            # start date is mandatory
            startdate = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        self.assign_value(locators['sp.start_date'], startdate)
        self.click(common_locators['name'])
        self.click(common_locators['create'])

    def update(self, name, new_name=None, new_desc=None,
               new_sync_interval=None, add_products=None,
               rm_products=None):
        """Updates Sync Plans from UI."""
        self.search_and_click(name)
        self.click(tab_locators['sp.tab_details'])
        if new_name:
            self.click(locators['sp.name_edit'])
            self.assign_value(locators['sp.name_update'], new_name)
            self.click(common_locators['save'])
        if new_desc:
            self.click(locators['sp.desc_edit'])
            self.assign_value(locators['sp.desc_update'], new_name)
            self.click(common_locators['save'])
        if new_sync_interval:
            self.click(locators['sp.sync_interval_edit'])
            self.assign_value(
                locators['sp.sync_interval_update'], new_sync_interval)
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
