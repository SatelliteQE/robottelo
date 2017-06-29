# -*- encoding: utf-8 -*-
"""Implements Packages UI"""
import time
from robottelo.helpers import escape_search
from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.ui.locators import common_locators, locators, tab_locators
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

    def search(self, element, repository=None,
               _raw_query=None, expecting_results=True):
        """Uses the search box to locate an element from a list of elements.

        :param repository: Repository name
        :param element: either element name or a tuple, containing element name
            as a first element and all the rest variables required for element
            locator.
        :param _raw_query: (optional) custom search query. Can be used to find
            entity by some of its fields (e.g. 'hostgroup = foo' for entity
            named 'bar') or to combine complex queries (e.g.
            'name = foo and os = bar'). Note that this will ignore entity's
            default ``search_key``.
        :param expecting_results: Specify whether we expect to find any entity
            or not
        """
        element_name = element[0] if isinstance(element, tuple) else element
        # Navigate to the page
        self.logger.debug(u'Searching for: %s', element_name)
        self.navigate_to_entity()

        # Filter packages by repository if it is specified
        if repository:
            self.select_repo(repository)

        # Provide search criterions or use default ones
        search_key = self.search_key or 'name'
        element_locator = self._search_locator()

        # Determine search box and search button locators
        prefix = 'kt_'
        searchbox = self.wait_until_element(
            common_locators[prefix + 'search'],
            timeout=self.button_timeout
        )
        search_button_locator = common_locators[prefix + 'search_button']

        # Do not proceed if searchbox is not found
        if searchbox is None:
            # For katello, search box should be always present on the page
            # no matter we have entity on the page or not...
            raise UINoSuchElementError('Search box not found.')

        # Pass the data into search field and push the search button if
        # applicable
        searchbox.clear()
        searchbox.send_keys(_raw_query or u'{0} = {1}'.format(
            search_key, escape_search(element_name)))
        # ensure mouse points at search button and no tooltips are covering it
        # before clicking
        self.perform_action_chain_move(search_button_locator)

        self.click(search_button_locator)

        # In case we expecting that search should not find any entity
        if expecting_results is False:
            return self.wait_until_element(
                common_locators[prefix + 'search_no_results'])

        # Make sure that found element is returned no matter it described by
        # its own locator or common one (locator can transform depending on
        # element name length)
        for _ in range(self.result_timeout):
            for strategy, value in (
                    element_locator,
                    common_locators['select_filtered_entity']
            ):
                result = self.find_element((strategy, value % element))
                if result is not None:
                    return result
            time.sleep(1)
        return None

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
            actual_text = self.wait_until_element(
                locators['package.field_value'] % parameter_name
            ).text
            if actual_text != parameter_value:
                raise UIError(
                    'Actual text for "{0}" parameter is "{1}", but it is'
                    ' expected to have "{2}"'.format(
                        parameter_name, actual_text, parameter_value)
                )

    def check_file_list(self, name, file_list):
        """Check whether necessary file(s) are present in the package"""
        self.click(self.search(name))
        self.click(tab_locators['package.tab_files'])
        for package_file in file_list:
            self.wait_until_element(
                locators['package.content_file'] % package_file)
