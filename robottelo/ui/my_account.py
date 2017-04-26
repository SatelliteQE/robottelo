# -*- encoding: utf-8 -*-
"""Implements My Account UI."""
from robottelo.ui.base import Base, UINoSuchElementError, UIError
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.navigator import Navigator

_property_locator_dct = {
        'first_name': locators['users.firstname'],
        'email': locators['users.email'],
        'language': locators['users.language_dropdown'],
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

    def update(self, **kwargs):
        """Update my account properties

        :param kwargs: Properties to be update. Available: first_name,
            last_name, email, language, password or password_confirmation
        """
        self.navigate_to_entity()
        for property_name, new_value in kwargs.items():
            input_locator = _property_locator_dct[property_name]
            self.assign_value(input_locator, new_value)
        self.click(common_locators['submit'])
        # success update message overlap menu so waiting is necessary before
        # navigating to My Account
        self.wait_until_element_is_not_visible(
            common_locators["notif.success"])

    def validate_logged_user(self, field_name, field_value):
        """Checks if logged user has field_value. Exception is raised in
        case there is no web ui related to field_name or value present on
        element differs from field_value

        :param field_name: one of: first_name,
            last_name, email, language, password or password_confirmation
        :param field_value: expected field value
        """
        value_locator = _value_locator_dct[field_name]
        element = self.find_element(value_locator)
        if element is None:
            raise UINoSuchElementError(
                'Unable to find the field for "{0}".'.format(field_name)
            )
        element_value = element.get_attribute('value')
        if element_value != field_value:
            raise UIError(
                'MyAccount "{0}" field has value "{1}" which is different '
                'from "{2}"'.format(field_name, element_value, field_value)
            )
