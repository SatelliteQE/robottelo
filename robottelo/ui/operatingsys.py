# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Operating System UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from selenium.webdriver.support.select import Select
from robottelo.common.constants import FILTER


class OperatingSys(Base):
    """
    Manipulates Foreman's operating system from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def _configure_os(self, archs, ptables, mediums, select,
                      minor_version=None, os_family=None, template=None,
                      arch_list=None, ptable_list=None, medium_list=None):
        """
        Configures the operating system details
        """
        tab_primary_locator = tab_locators["tab_primary"]
        tab_ptable_locator = tab_locators["operatingsys.tab_ptable"]
        tab_medium_locator = tab_locators["operatingsys.tab_medium"]

        if minor_version:
            if self.wait_until_element(locators
                                       ["operatingsys.minor_version"]):
                self.field_update("operatingsys.minor_version", minor_version)
        if os_family:
            Select(self.find_element(locators
                                     ["operatingsys.family"]
                                     )).select_by_visible_text(os_family)
        if archs or arch_list:
            self.configure_entity(archs, FILTER['os_arch'],
                                  tab_locator=tab_primary_locator,
                                  new_entity_list=arch_list,
                                  entity_select=select)
        if ptables or ptable_list:
            self.configure_entity(ptables, FILTER['os_ptable'],
                                  tab_locator=tab_ptable_locator,
                                  new_entity_list=ptable_list,
                                  entity_select=select)
        if mediums or medium_list:
            self.configure_entity(mediums, FILTER['os_medium'],
                                  tab_locator=tab_medium_locator,
                                  new_entity_list=medium_list,
                                  entity_select=select)
        if template:
            self.wait_until_element(tab_locators
                                    ["operatingsys.tab_templates"]).click()
            Select(self.find_element(locators
                                     ["operatingsys.template"]
                                     )).select_by_visible_text(template)

    def create(self, name, major_version=None,
               minor_version=None, os_family=None,
               archs=None, ptables=None, mediums=None, select=True,
               template=None):
        """
        Create operating system from UI
        """
        new_os = self.wait_until_element(locators["operatingsys.new"])
        if new_os:
            new_os.click()
            os_name_locator = locators["operatingsys.name"]
            os_major_locator = locators["operatingsys.major_version"]
            if self.wait_until_element(os_name_locator):
                self.find_element(os_name_locator).send_keys(name)
            if self.wait_until_element(os_major_locator):
                self.find_element(os_major_locator).send_keys(major_version)
                self._configure_os(archs, ptables, mediums, select,
                                   minor_version, os_family, template,
                                   arch_list=None, ptable_list=None,
                                   medium_list=None)
                self.find_element(common_locators["submit"]).click()
                self.wait_for_ajax()
            else:
                raise Exception(
                    "Could not create OS without major_version")
        else:
            raise Exception(
                "Could not create new operating system '%s'" % name)

    def search(self, name):
        """
        Searches existing operating system from UI
        """
        element = self.search_entity(name,
                                     locators['operatingsys.operatingsys_name'])  # @IgnorePep8
        return element

    def delete(self, os_name, really):
        """
        Delete operating system from UI
        """

        self.delete_entity(os_name, really,
                           locators['operatingsys.operatingsys_name'],
                           locators['operatingsys.delete'])

    def update(self, os_name, new_name=None,
               major_version=None, minor_version=None,
               os_family=None, archs=None,
               ptables=None, mediums=None, new_archs=None,
               new_ptables=None, new_mediums=None, select=False,
               template=None):
        """
        Update all entities(arch, Partition table, medium) of OS from UI
        """
        element = self.search(os_name)

        if element:
            element.click()
            if new_name:
                if self.wait_until_element(locators["operatingsys.name"]):
                    self.field_update("operatingsys.name", new_name)
            if major_version:
                if self.wait_until_element(locators
                                           ["operatingsys.major_version"]):
                    self.field_update("operatingsys.major_version",
                                      major_version)
            self._configure_os(archs, ptables, mediums, select,
                               minor_version, os_family, template,
                               arch_list=new_archs, ptable_list=new_ptables,
                               medium_list=new_mediums)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not update the operating system '%s'" % os_name)

    def set_os_parameter(self, os_name, param_name, param_value):
        """
        Add new OS parameter
        """
        element = self.search(os_name)
        if element:
            element.click()
            self.set_parameter(param_name, param_value)
        else:
            raise Exception("Could not set parameter '%s'" % param_name)

    def remove_os_parameter(self, os_name, param_name):
        """
        Remove selected OS parameter
        """
        element = self.search(os_name)
        if element:
            element.click()
            self.remove_parameter(param_name)
        else:
            raise Exception("Could not remove parameter '%s'" % param_name)
