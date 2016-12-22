# -*- encoding: utf-8 -*-
"""Implements Puppet Module UI"""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators, tab_locators
from robottelo.ui.navigator import Navigator


class PuppetModule(Base):
    """Manipulates Puppet Modules from UI"""

    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Puppet Module entity page"""
        Navigator(self.browser).go_to_puppet_modules()

    def _search_locator(self):
        """Specify locator for Puppet Module entity search procedure"""
        return locators['puppet.module_name']

    def check_puppet_details(self, name, parameter_list=None):
        """Check whether puppet module detail section contains expected values
        or raise exception otherwise.
        All values should be passed in absolute correspondence to UI. For
        example, we have 'Author' or 'Project Page' fields, so next parameter
        list should be passed::

            [
                ['Author', 'Expected author'],
                ['Project Page', 'Expected URL'],
            ]

        """
        self.click(self.search(name))
        for parameter_name, parameter_value in parameter_list:
            param_locator = '.'.join((
                'puppet',
                (parameter_name.lower()).replace(' ', '_')
            ))
            actual_text = self.wait_until_element(locators[param_locator]).text
            if actual_text != parameter_value:
                raise UIError(
                    'Actual text for "{0}" parameter is "{1}", but it is'
                    ' expected to have "{2}"'.format(
                        parameter_name, actual_text, parameter_value)
                )

    def check_repo(self, name, repos_list):
        """Check whether puppet module is present in necessary
        repository/repositories
        """
        self.click(self.search(name))
        self.click(tab_locators['puppet_module.tab_library_repositories'])
        for repo in repos_list:
            searchbox = self.wait_until_element(locators['repo.search'])
            if searchbox:
                searchbox.clear()
                searchbox.send_keys(repo)
                self.wait_until_element(locators['repo.select'] % repo)
