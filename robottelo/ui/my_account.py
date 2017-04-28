# -*- encoding: utf-8 -*-
"""Implements My Account UI."""
from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator

_property_locator_dct = {
        'first_name': locators['users.firstname'],
        'email': locators['users.email'],
        'language': locators['users.language_dropdown'],
        'current_password': locators['users.current_password'],
        'password': locators['users.password'],
        'password_confirmation': locators['users.password_confirmation'],
        'last_name': locators['users.lastname']
    }

# It can be a chain map once we move to python 3
_value_locator_dct = dict(_property_locator_dct.items())
_value_locator_dct['language'] = locators['users.selected_lang']


class MyAccount(Base):
    """Implements navigation to My Account."""

    def navigate_to_entity(self):
        """Navigate to My Account page"""
        Navigator(self.browser).go_to_my_account()

    def update(self, first_name=None, last_name=None, language=None,
               current_password=None, password=None,
               password_confirmation=None, email=None):
        """Update my account properties"""
        kwargs = {
            'first_name': first_name, 'last_name': last_name,
            'language': language, 'current_password': current_password,
            'password': password, 'email': email,
            'password_confirmation': password_confirmation
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        self.navigate_to_entity()
        for property_name, new_value in kwargs.items():
            input_locator = _property_locator_dct[property_name]
            self.assign_value(input_locator, new_value)
        self.click(common_locators['submit'])
        # success update message overlap menu so waiting is necessary before
        # navigating to My Account
        self.wait_until_element_is_not_visible(
            common_locators["notif.success"])

    def get_field_value(self, field_name):
        """Return value present on input element respective to field_name

        :param str field_name: one of ["first_name", "last_name", "email",
            "language", "password", "password_confirmation"]
        :return str
        """
        self.navigate_to_entity()
        value_locator = _value_locator_dct[field_name]
        element = self.wait_until_element_exists(value_locator)
        if element is None:
            raise UINoSuchElementError(
                'Unable to find the field for "{0}".'.format(field_name)
            )
        return element.get_attribute('value')
