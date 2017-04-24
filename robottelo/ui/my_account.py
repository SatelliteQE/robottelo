# -*- encoding: utf-8 -*-
"""Implements My Account UI."""
from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator


class MyAccount(Base):
    """Implements navigation to My Account."""
    _property_locator_dct = {
        'first_name': locators['users.firstname'],
        'email': locators['users.email'],
        'language': locators['users.language_dropdown'],
        'password': locators['users.password'],
        'password_confirmation': locators['users.password_confirmation'],
        'last_name': locators['users.lastname']
    }

    def navigate_to_entity(self):
        """Navigate to My Account page"""
        Navigator(self.browser).go_to_my_account()

    def update(self, **kwargs):
        """Update my account properties

        :param kwargs: Properties to be update. Available: first_name,
            last_name, email, language, password or password_confirmation
        """
        self.navigate_to_entity()
        for property_name, new_value in kwargs.items():
            input_locator = self._property_locator_dct[property_name]
            self.assign_value(input_locator, new_value)
        self.click(common_locators['submit'])
        # success update message overlap menu so waiting is necessary before
        # navigating to My Account
        self.wait_until_element_is_not_visible(
            common_locators["notif.success"])

    def update_and_find_element(self, property_name, new_value):
        """ Update property and returns respective web ui element

        :param property_name: one of first_name,
            last_name, email, language, password or password_confirmation
        :param new_value: new property's value
        :return: web ui element
        """
        kwargs = {property_name: new_value}
        self.update(**kwargs)
        self.navigate_to_entity()
        if property_name == 'language':
            value_locator = locators['users.selected_lang']
        else:
            value_locator = self._property_locator_dct[property_name]
        return self.wait_until_element_exists(value_locator)
