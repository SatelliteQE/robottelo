# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Architecture UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators


class Architecture(Base):
    """
    Manipulates architecture from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def _configure_arch(self, os_name=None):
        """
        Configures architecture details like: OS name
        """
        if os_name:
            self.select_entity("arch.os_name", "arch.select_os_name",
                               os_name, None)

    def create(self, name, os_name=None):
        """
        Creates new architecture from UI with existing OS
        """

        self.wait_until_element(locators["arch.new"]).click()

        if self.wait_until_element(locators["arch.name"]):
            self.field_update("arch.name", name)
            self._configure_arch(os_name)
            self.find_element(locators["arch.submit"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new architecture '%s'" % name)

    def delete(self, name, really):
        """
        Delete existing architecture from UI
        """

        element = self.search(name, locators['arch.delete'])

        if element:
            element.click()
            if really:
                alert = self.browser.switch_to_alert()
                alert.accept()
            else:
                alert = self.browser.switch_to_alert()
                alert.dismiss()
        else:
            raise Exception(
                "Could not delete the architecture '%s'" % name)

    def update(self, old_name, new_name=None, os_name=None):
        """
        Update existing arch's name and OS
        """

        element = self.search(old_name, locators['arch.arch_name'])

        if element:
            element.click()
            if self.wait_until_element(locators["arch.name"]):
                self.field_update("arch.name", new_name)
                self._configure_arch(os_name)
                self.find_element(locators["arch.submit"]).click()
                self.wait_for_ajax()
        else:
            raise Exception(
                "Could not update the architecture '%s'" % old_name)
