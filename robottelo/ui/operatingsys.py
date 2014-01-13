# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Operating System UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators
from selenium.webdriver.support.select import Select


class OperatingSys(Base):
    """
    Manipulates Foreman's operating system from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, name, major_version=None,
               minor_version=None, os_family=None,
               arch=None, ptable=None, medium=None):
        """
        Create operating system from UI
        """

        self.wait_until_element(locators["operatingsys.new"]).click()

        if self.wait_until_element(locators["operatingsys.name"]):
            self.find_element(locators["operatingsys.name"]).send_keys(name)
            if self.wait_until_element(locators["operatingsys.major_version"]):
                self.find_element(locators
                                  ["operatingsys.major_version"]
                                  ).send_keys(major_version)
            if minor_version:
                if self.wait_until_element(locators
                                           ["operatingsys.minor_version"]):
                    self.find_element(locators
                                      ["operatingsys.minor_version"]
                                      ).send_keys(minor_version)
            if os_family:
                Select(self.find_element(locators
                                         ["operatingsys.family"]
                                         )).select_by_visible_text(os_family)
            if arch:
                self.select_entity("operatingsys.arch",
                                   "operatingsys.select_arch", arch, None)
            if ptable:
                self.select_entity("operatingsys.ptable",
                                   "operatingsys.select_ptable", ptable,
                                   "operatingsys.tab_ptable")
            if medium:
                self.select_entity("operatingsys.medium",
                                   "operatingsys.select_medium", medium,
                                   "operatingsys.tab_medium")
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()

    def delete(self, os_name, really):
        """
        Delete operating system from UI
        """

        self.delete_entity(os_name, really,
                           locators['operatingsys.operatingsys_name'],
                           locators['operatingsys.delete'])

    def update(self, os_name, new_name=None,
               new_major_version=None, new_minor_version=None,
               new_os_family=None, new_arch=None,
               new_ptable=None, new_medium=None):
        """
        Update all entities(arch, Partition table, medium) of OS from UI
        """

        element = self.search(
            os_name, locators['operatingsys.operatingsys_name']
        )

        if element:
            element.click()

            if new_name:
                if self.wait_until_element(locators["operatingsys.name"]):
                    self.field_update("operatingsys.name", new_name)
            if new_major_version:
                if self.wait_until_element(
                        locators["operatingsys.major_version"]):
                    self.field_update("operatingsys.major_version",
                                      new_major_version)
            if new_minor_version:
                if self.wait_until_element(
                        locators["operatingsys.minor_version"]):
                    self.field_update("operatingsys.minor_version",
                                      new_minor_version)
            if new_os_family:
                Select(self.find_element(
                    locators["operatingsys.family"])
                ).select_by_visible_text(new_os_family)
            if new_arch:
                self.select_entity("operatingsys.arch",
                                   "operatingsys.select_arch", new_arch, None)
            if new_ptable:
                self.select_entity("operatingsys.ptable",
                                   "operatingsys.select_ptable", new_ptable,
                                   "operatingsys.tab_ptable")
            if new_medium:
                self.select_entity("operatingsys.medium",
                                   "operatingsys.select_medium", new_medium,
                                   "operatingsys.tab_medium")
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()

        else:
            raise Exception(
                "Could not update the operating system '%s'" % os_name)

    def set_os_parameter(self, os_name, param_name, param_value):
        """
        Add new OS parameter
        """

        element = self.search(
            os_name, locators['operatingsys.operatingsys_name']
        )

        if element:
            element.click()
            self.set_parameter(param_name, param_value)
        else:
            raise Exception("Could not set parameter '%s'" % param_name)

    def remove_os_parameter(self, os_name, param_name):
        """
        Remove selected OS parameter
        """

        element = self.search(
            os_name, locators['operatingsys.operatingsys_name']
        )

        if element:
            element.click()
            self.remove_parameter(param_name)
        else:
            raise Exception("Could not remove parameter '%s'" % param_name)
