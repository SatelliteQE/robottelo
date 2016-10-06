# -*- encoding: utf-8 -*-
from robottelo.ui.base import Base, UINoSuchElementError
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
        self.wait_until_element(locators['profile.name']).send_keys(name)
        self.wait_for_ajax()
        self.click(common_locators['submit'])

    def update(self, old_name, new_name):
        """Updates existing compute profile entity"""
        element = self.get_entity(old_name)
        if element is None:
            raise UINoSuchElementError(
                'Could not find compute profile {0}'.format(old_name))
        if element:
            strategy, value = locators['profile.dropdown']
            self.click((strategy, value % old_name))
            strategy, value = locators['profile.rename']
            self.click((strategy, value % old_name))
            self.field_update('profile.name', new_name)
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
        profile = self.get_entity(profile_name)
        if profile is None:
            raise UINoSuchElementError(
                u'Could not find the profile {0}'.format(profile_name))
        profile.click()
        resource = u'{0} ({1})'.format(res_name, res_type)
        strategy, value = locators['profile.resource_name']
        self.click((strategy, value % resource))
        return self.wait_until_element(locators['profile.resource_form'])
