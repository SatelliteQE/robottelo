# -*- encoding: utf-8 -*-
from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class ComputeProfile(Base):
    """Provides the CRUD functionality for Compute Profiles."""

    def search(self, name):
        """Search for existing compute profile from UI."""
        Navigator(self.browser).go_to_compute_profiles()
        return self.search_entity(name, locators['profile.select_name'])

    def select_resource(self, profile_name, res_name, res_type):
        """Select necessary compute resource from specific compute profile

        :param profile_name: Name of profile that contains required compute
        resource (e.g. '2-Medium' or '1-Small')
        :param res_name: Name of compute resource to select from the list
        :param res_type: Type of compute resource (e.g. 'Libvirt' or 'Docker')

        """
        profile = self.search(profile_name)
        if profile is None:
            raise UINoSuchElementError(
                u'Could not find the profile {0}'.format(profile_name))
        profile.click()
        resource = u'{0} ({1})'.format(res_name, res_type)
        strategy, value = locators['profile.resource_name']
        self.click((strategy, value % resource))
        return self.wait_until_element(locators['profile.resource_form'])
