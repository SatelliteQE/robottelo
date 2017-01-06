# -*- encoding: utf-8 -*-
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class ComputeProfile(Base):
    """Provides the CRUD functionality for Compute Profiles."""

    def navigate_to_entity(self):
        """Navigate to Compute Profile entity page"""
        Navigator(self.browser).go_to_compute_profiles()

    def _search_locator(self):
        """Specify locator for Compute Profile entity search procedure"""
        return locators['profile.select_name']

    def create(self, name):
        """Creates new compute profile entity"""
        self.click(locators['profile.new'])
        self.assign_value(locators['profile.name'], name)
        self.click(common_locators['submit'])

    def update(self, old_name, new_name):
        """Updates existing compute profile entity"""
        self.search(old_name)
        self.click(locators['profile.rename'] % old_name)
        self.assign_value(locators['profile.name'], new_name)
        self.click(common_locators['submit'])

    def delete(self, name, really=True):
        """Deletes existing compute profile entity"""
        self.delete_entity(
            name,
            really,
            locators['profile.delete'],
            drop_locator=locators['profile.dropdown'],
        )

    def select_resource(self, profile_name, res_name, res_type):
        """Select necessary compute resource from specific compute profile

        :param profile_name: Name of profile that contains required compute
        resource (e.g. '2-Medium' or '1-Small')
        :param res_name: Name of compute resource to select from the list
        :param res_type: Type of compute resource (e.g. 'Libvirt' or 'Docker')
        """
        self.search_and_click(profile_name)
        resource = u'{0} ({1})'.format(res_name, res_type)
        self.click(locators['profile.resource_name'] % resource)
        return self.wait_until_element(locators['profile.resource_form'])
