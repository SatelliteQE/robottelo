# -*- encoding: utf-8 -*-

"""Implements Content Search UI"""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators


class ContentSearch(Base):
    """Manipulates Content Search from UI"""

    ft_locator = None

    def select_filter_type(self, filter_type):
        """Specify a content type to select from the 'Content' menu.

        The following content types are currently supported:

        1. Content Views
        2. Products
        3. Repositories
        4(a). Packages
        4(b). Puppet Modules

        It is advisable to respect the list ordering as shown above, because
        when using the Content Search UI, proceeding lower in the list causes
        more UI elements to be added to the panel.

        """
        self.wait_until_element(
            locators['contentsearch.open_filter_dropdown']
        ).click()
        strategy = locators['contentsearch.select_filter'][0]
        value = locators['contentsearch.select_filter'][1]
        self.wait_until_element((strategy, value % filter_type)).click()
        self.ft_locator = (filter_type.lower()).replace(' ', '_')

    def add_filter(self, filter_type, filter_value, auto_complete=None):
        """Add necessary amount of filters ('autocomplete' fields)
        At that moment we support next filters:
        'Content Views'
        'Products'
        'Repositories' (second radiobutton)

        Specify exact string that you want to be chosen from suggestions box in
        auto_complete parameter. For example, you input 'MyRepo' into field and
        see 'MyRepo01' and 'MyRepo02' in suggestion box, so it is necessary to
        pass corresponding value into mentioned parameter (like auto_complete=
        'MyRepo01')

        """
        self.select_filter_type(filter_type)
        if filter_type == 'Repositories':
            self.wait_until_element(
                locators['contentsearch.repositories_auto_radio']
            ).click()
        self.field_update(
            'contentsearch.{}'.format(self.ft_locator),
            filter_value
        )
        strategy = locators['contentsearch.autocomplete_field'][0]
        value = locators['contentsearch.autocomplete_field'][1]
        self.wait_until_element((strategy, value % filter_value))
        if auto_complete is not None:
            self.wait_until_element((strategy, value % auto_complete)).click()
        self.wait_for_ajax()
        add_button = self.wait_until_element_is_clickable(
            locators['contentsearch.add_{}_filter'.format(self.ft_locator)]
        )
        if add_button is None:
            raise UIError(
                'There is no "{0}" entity in the system'.format(filter_value)
            )
        add_button.click()

    def add_search_criteria(self, filter_type, filter_value):
        """Add search criteria (normal search fields)
        At that moment we support next criterias:
        'Repositories' (first radiobutton)
        'Packages'
        'Puppet Modules'

        """
        self.select_filter_type(filter_type)
        if filter_type == 'Repositories':
            self.wait_until_element(
                locators['contentsearch.repositories_search_radio']
            ).click()
        self.field_update(
            'contentsearch.{}_search'.format(self.ft_locator),
            filter_value
        )

    def search(self, expected_result_list, result_view=None):
        """Start searching procedure according to provided information
        It is necessary to pass expected result to that function. For example,
        you have next result on your page in browser:
        TestContentView_01
        --TestProduct01
        ----TestRepository01
        ------TestPackage01

        In that case, you should have next parameter:
        [
            ['Content View', 'TestContentView_01', True],
            ['Product', 'TestProduct01', True],
            ['Repository', 'TestRepository01', True],
            ['Package', 'TestPackage01', False]
        ]

        Boolean parameter here specify whether you want to collapse your
        current entity in search result to get the list of next level entities,
        of course, if you have them

        result_view can have next values:
        'Union', 'Intersection', 'Difference'

        """
        self.wait_until_element(locators['contentsearch.search']).click()
        self.scroll_page()
        if result_view is not None:
            self.wait_until_element(
                locators['contentsearch.open_view_dropdown']
            ).click()
            strategy = locators['contentsearch.select_view'][0]
            value = locators['contentsearch.select_view'][1]
            self.wait_until_element((strategy, value % result_view)).click()

        for entity_name, entity_value, collapse in expected_result_list:
            strategy = locators['contentsearch.result_entity'][0]
            value = locators['contentsearch.result_entity'][1]
            found = self.wait_until_element((strategy, value % entity_value))
            if found is None:
                raise UIError(
                    'Could not find {0} "{1}" according to search parameters'
                    .format(entity_name, entity_value)
                )
            if collapse:
                strategy = locators['contentsearch.result_entity_open_list'][0]
                value = locators['contentsearch.result_entity_open_list'][1]
                state = self.is_element_visible(
                    (strategy, value % entity_value)
                )
                if state:
                    self.wait_until_element(
                        (strategy, value % entity_value)
                    ).click()
                    self.wait_for_ajax()
