"""
Implements Hardware Models CRUD in UI
"""

from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators, common_locators
from robottelo.ui.navigator import Navigator


class HardwareModel(Base):
    """Provides the CRUD functionality for Hardware-Models."""

    def create(self, name, hw_model=None, vendor_class=None, info=None):
        """Creates the Hardware-Models.

        :param str name: Hardware-Model name.
        :param str hw_model: The Hardware-Model type.
        :param str vendor_class: The Hardware-Model's vendor-class.
        :param str info: some information related to Hardware-Models.

        """
        self.wait_until_element(locators["hwmodels.new"]).click()
        if self.wait_until_element(locators["hwmodels.name"]):
            self.find_element(locators["hwmodels.name"]).send_keys(name)
        if hw_model:
            self.find_element(
                locators['hwmodels.model']).send_keys(hw_model)
        if vendor_class:
            self.find_element(
                locators["hwmodels.vclass"]).send_keys(vendor_class)
        if info:
            self.find_element(
                locators["hwmodels.info"]).send_keys(info)
        self.find_element(common_locators["submit"]).click()
        self.wait_for_ajax()

    def update(self, old_name, new_name=None):
        """Updates the Hardware-Models.

        :param str old_name: Hardware-Model's old-name.
        :param str new_name: The Hardware-Model's new-name.

        """
        element = self.search(old_name)
        if element:
            element.click()
            if (self.wait_until_element(locators["hwmodels.name"]) and
                    new_name):
                self.field_update("hwmodels.name", new_name)
            self.find_element(common_locators["submit"]).click()
            self.wait_for_ajax()
        else:
            raise UINoSuchElementError(
                "Could not find hardware-model '%s'" % old_name)

    def search(self, name, timeout=None):
        """Searches existing Hardware-Models from UI.

        :param str name: Hardware-Model's name to search.

        """
        Navigator(self.browser).go_to_hardware_models()
        element = self.search_entity(name,
                                     locators["hwmodels.select_name"],
                                     timeout=timeout)
        return element

    def delete(self, name, really):
        """Deletes the Hardware-Models.

        :param str name: Hardware-Model's name to search.
        :param boolean really: Value required for negative tests.

        """

        self.delete_entity(name, really, locators["hwmodels.select_name"],
                           locators['hwmodels.delete'])
