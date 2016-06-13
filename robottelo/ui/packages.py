# -*- encoding: utf-8 -*-
"""Implements Packages UI"""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class Package(Base):
    """Manipulates Packages from UI"""

    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Package entity page"""
        Navigator(self.browser).go_to_packages()

    def _search_locator(self):
        """Specify locator for Package entity search procedure"""
        return locators['package.rpm_name']

    def check_package_details(self, name, parameter_list=None):
        """Check whether package detail section contains expected values or
        raise exception otherwise.
        All values should be passed in absolute correspondence to UI. For
        example, we have 'Description' or 'Checksum Type' fields, so next
        parameter list should be passed::
            [
                ['Description', 'Expected description'],
                ['Checksum Type', 'sha256'],
            ]
        """
        self.click(self.search(name))
        for parameter_name, parameter_value in parameter_list:
            param_locator = '.'.join((
                'package',
                (parameter_name.lower()).replace(' ', '_')
            ))
            actual_text = self.wait_until_element(locators[param_locator]).text
            if actual_text != parameter_value:
                raise UIError(
                    'Actual text for "{0}" parameter is "{1}", but it is'
                    ' expected to have "{2}"'.format(
                        parameter_name, actual_text, parameter_value)
                )
