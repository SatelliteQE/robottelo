# -*- encoding: utf-8 -*-
"""Implements Operating System UI."""
from robottelo.constants import FILTER
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class OperatingSys(Base):
    """Manipulates Foreman's operating system from UI."""

    def navigate_to_entity(self):
        """Navigate to OS entity page"""
        Navigator(self.browser).go_to_operating_systems()

    def _search_locator(self):
        """Specify locator for OS entity search procedure"""
        return locators['operatingsys.operatingsys_name']

    def _configure_os(self, archs, ptables, mediums, select,
                      minor_version=None, description=None, os_family=None,
                      template=None, arch_list=None, ptable_list=None,
                      medium_list=None):
        """Configures the operating system details."""
        tab_primary_locator = tab_locators['tab_primary']
        tab_ptable_locator = tab_locators['operatingsys.tab_ptable']
        tab_medium_locator = tab_locators['operatingsys.tab_medium']

        if minor_version:
            self.assign_value(
                locators['operatingsys.minor_version'], minor_version)
        if description:
            self.assign_value(
                locators['operatingsys.description'], description)
        if os_family:
            self.select(locators['operatingsys.family'], os_family)
        if archs or arch_list:
            self.configure_entity(
                archs,
                FILTER['os_arch'],
                tab_locator=tab_primary_locator,
                new_entity_list=arch_list,
                entity_select=select
            )
        if ptables or ptable_list:
            self.configure_entity(
                ptables,
                FILTER['os_ptable'],
                tab_locator=tab_ptable_locator,
                new_entity_list=ptable_list,
                entity_select=select
            )
        if mediums or medium_list:
            self.configure_entity(
                mediums,
                FILTER['os_medium'],
                tab_locator=tab_medium_locator,
                new_entity_list=medium_list,
                entity_select=select
            )
        if template:
            self.click(tab_locators['operatingsys.tab_templates'])
            self.select(locators['operatingsys.template'], template)

    def create(self, name, major_version=None,
               minor_version=None, description=None, os_family=None,
               archs=None, ptables=None, mediums=None, select=True,
               template=None):
        """Create operating system from UI."""
        self.click(locators['operatingsys.new'])
        self.assign_value(locators['operatingsys.name'], name)
        self.assign_value(
            locators['operatingsys.major_version'], major_version)
        self._configure_os(
            archs,
            ptables,
            mediums,
            select,
            minor_version,
            description,
            os_family,
            template,
            arch_list=None,
            ptable_list=None,
            medium_list=None
        )
        self.click(common_locators['submit'])

    def update(self, os_name, new_name=None,
               major_version=None, minor_version=None,
               description=None, os_family=None, archs=None,
               ptables=None, mediums=None, new_archs=None,
               new_ptables=None, new_mediums=None, select=False,
               template=None):
        """Update all entities(arch, Partition table, medium) of OS from UI."""
        self.search_and_click(os_name)
        if new_name:
            self.assign_value(locators['operatingsys.name'], new_name)
        if major_version:
            self.assign_value(
                locators['operatingsys.major_version'], major_version)
        self._configure_os(
            archs,
            ptables,
            mediums,
            select,
            minor_version,
            description,
            os_family,
            template,
            arch_list=new_archs,
            ptable_list=new_ptables,
            medium_list=new_mediums
        )
        self.click(common_locators['submit'])

    def set_os_parameter(self, os_name, param_name, param_value):
        """Add new OS parameter."""
        self.search_and_click(os_name)
        self.set_parameter(param_name, param_value)

    def remove_os_parameter(self, os_name, param_name):
        """Remove selected OS parameter."""
        self.search_and_click(os_name)
        self.remove_parameter(param_name)

    def get_selected_entities(self):
        """Function to get selected elements (either it is a check-box or
        selection list).
        """
        selected_element = self.wait_until_element(
            common_locators['selected_entity'])
        checked_element = self.find_element(common_locators['checked_entity'])
        if selected_element:
            entity_value = selected_element.text
        else:
            entity_value = checked_element.text
        return entity_value

    def get_os_entities(self, os_name, entity_name=None):
        """Assert OS name, minor, major_version, os_family, template, media,
        and partition table to validate results.
        """
        name_loc = locators['operatingsys.name']
        major_ver_loc = locators['operatingsys.major_version']
        minor_ver_loc = locators['operatingsys.minor_version']
        os_family_loc = locators['operatingsys.fetch_family']

        self.search_and_click(os_name)
        if self.wait_until_element(locators['operatingsys.name']):
            result = dict([('name', None), ('major', None),
                           ('minor', None), ('os_family', None),
                           ('ptable', None), ('template', None),
                           ('medium', None)])
            result['name'] = self.find_element(name_loc).get_attribute('value')
            result['major'] = self.find_element(
                major_ver_loc).get_attribute('value')
            result['minor'] = self.find_element(
                minor_ver_loc).get_attribute('value')
            result['os_family'] = self.find_element(os_family_loc).text
            if entity_name == 'ptable':
                self.click(tab_locators['operatingsys.tab_ptable'])
                result['ptable'] = self.get_selected_entities()
            elif entity_name == 'medium':
                self.click(tab_locators['operatingsys.tab_medium'])
                result['medium'] = self.get_selected_entities()
            elif entity_name == 'template':
                self.click(tab_locators['operatingsys.tab_templates'])
                result['template'] = self.find_element(
                    locators['operatingsys.fetch_template']).text
            return result
        else:
            raise UIError(
                u'Could not find the OS name "{0}"'.format(os_name)
            )
