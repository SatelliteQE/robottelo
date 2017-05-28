"""Implements Hardware Models CRUD in UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class HardwareModel(Base):
    """Provides the CRUD functionality for Hardware-Models."""

    def navigate_to_entity(self):
        """Navigate to Hardware-Models entity page"""
        Navigator(self.browser).go_to_hardware_models()

    def _search_locator(self):
        """Specify locator for Hardware-Models entity search procedure"""
        return locators['hwmodels.select_name']

    def create(self, name, hw_model=None, vendor_class=None, info=None):
        """Creates the Hardware-Models.

        :param str name: Hardware-Model name.
        :param str hw_model: The Hardware-Model type.
        :param str vendor_class: The Hardware-Model's vendor-class.
        :param str info: some information related to Hardware-Models.
        """
        self.click(locators['hwmodels.new'])
        self.assign_value(locators['hwmodels.name'], name)
        if hw_model:
            self.assign_value(locators['hwmodels.model'], hw_model)
        if vendor_class:
            self.assign_value(locators['hwmodels.vclass'], vendor_class)
        if info:
            self.assign_value(locators['hwmodels.info'], info)
        self.click(common_locators['submit'])

    def update(self, old_name, new_name):
        """Updates the Hardware-Models.

        :param str old_name: Hardware-Model's old-name.
        :param str new_name: The Hardware-Model's new-name.
        """
        self.search_and_click(old_name)
        self.assign_value(locators['hwmodels.name'], new_name)
        self.click(common_locators['submit'])
