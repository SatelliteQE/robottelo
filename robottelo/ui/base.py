# -*- encoding: utf-8 -*-
"""Base class for all UI operations"""

import logging
import time

from robottelo.helpers import escape_search
from robottelo.ui.locators import locators, common_locators
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


LOGGER = logging.getLogger(__name__)


class UIError(Exception):
    """Indicates that a UI action could not be done."""


class UINoSuchElementError(UIError):
    """Indicates that UI Element is not found."""


class UIPageSubmitionFailed(Exception):
    """Indicates that UI Page submition Failed."""


class Base(object):
    """Base class for UI"""

    logger = LOGGER

    search_key = None
    is_katello = False
    button_timeout = 15
    result_timeout = 15

    def __init__(self, browser):
        """Sets up the browser object."""
        self.browser = browser

    def find_element(self, locator):
        """Wrapper around Selenium's WebDriver that allows you to search for an
        element in the web page.

        """
        try:
            _webelement = self.browser.find_element(*locator)
            self.wait_for_ajax()
            if _webelement.is_displayed():
                return _webelement
            else:
                return None
        except NoSuchElementException as err:
            self.logger.debug(
                '%s: Could not locate element %s.',
                type(err).__name__,
                locator[1]
            )
        except TimeoutException as err:
            self.logger.debug(
                'Timeout while waiting for locator "%s": "%s"',
                locator[0],
                locator[1]
            )
        return None

    def _search_locator(self):
        """Specify element name locator which should be used in search
        procedure

        """
        raise NotImplementedError(
            'Subclasses must return locator of element to search')

    def navigate_to_entity(self):
        """Perform navigation to main page for specific entity"""
        raise NotImplementedError('Subclasses must implement navigator method')

    def search(self, element_name):
        """Uses the search box to locate an element from a list of elements."""
        # Navigate to the page
        self.logger.debug(u'Searching for: %s', element_name)
        self.navigate_to_entity()

        # Provide search criterions or use default ones
        search_key = self.search_key or 'name'
        element_locator = self._search_locator()

        # Determine search box and search button locators depending on the type
        # of entity
        prefix = 'kt_' if self.is_katello else ''
        searchbox = self.wait_until_element(
            common_locators[prefix + 'search'],
            timeout=self.button_timeout
        )
        search_button_locator = common_locators[prefix + 'search_button']

        # Do not proceed if searchbox is not found
        if searchbox is None:
            # For katello, search box should be always present on the page
            # no matter we have entity on the page or not...
            if self.is_katello:
                raise UINoSuchElementError('Search box not found.')
            # ...but not for foreman
            return None

        # Pass the data into search field and push the search button if
        # applicable
        searchbox.clear()
        searchbox.send_keys(u'{0} = {1}'.format(
            search_key, escape_search(element_name)))
        # ensure mouse points at search button and no tooltips are covering it
        # before clicking
        self.perform_action_chain_move(search_button_locator)

        self.click(search_button_locator)
        # Make sure that found element is returned no matter it described by
        # its own locator or common one (locator can transform depending on
        # element name length)
        strategy, value = element_locator
        strategy2, value2 = common_locators['select_filtered_entity']
        for _ in range(self.result_timeout):
            element = self.find_element((strategy, value % element_name))
            if element is not None:
                return element
            element2 = self.find_element((strategy2, value2 % element_name))
            if element2 is not None:
                return element2
            time.sleep(1)
        return None

    def create_a_bookmark(self, name=None, query=None, public=None,
                          searchbox_query=None):
        """Bookmark a search on current entity page"""
        self.navigate_to_entity()
        prefix = 'kt_' if self.is_katello else ''
        searchbox = self.wait_until_element(
            common_locators[prefix + 'search'],
            timeout=self.button_timeout
        )
        if searchbox is None:
            raise UINoSuchElementError('Search box not found.')
        if searchbox_query is not None:
            searchbox.clear()
            searchbox.send_keys(u'{0}'.format(escape_search(searchbox_query)))
        self.click(common_locators['search_dropdown'])
        self.click(locators['bookmark.new'])
        self.wait_until_element(locators['bookmark.name'])
        if name is not None:
            self.assign_value(locators['bookmark.name'], name)
        if query is not None:
            self.assign_value(locators['bookmark.query'], query)
        if public is not None:
            self.assign_value(locators['bookmark.public'], public)
        self.click(locators['bookmark.create'])

    def handle_alert(self, really):
        """
        Handles any alerts
        """
        if really:
            alert = self.browser.switch_to_alert()
            alert.accept()
        else:
            alert = self.browser.switch_to_alert()
            alert.dismiss()

    def select_deselect_entity(self, filter_key, loc, entity_list):
        """Function to select and deselect entity like OS, Partition Table,
        Arch from selection list or by selecting relevant checkbox.

        """
        for entity in entity_list:
            # Scroll to top
            self.browser.execute_script('window.scroll(0, 0)')
            strategy, value = common_locators['filter']
            txt_field = self.wait_until_element((strategy, value % filter_key))
            self.logger.debug(u'Toggling entity %s select state', entity)
            if txt_field:
                txt_field.clear()
                txt_field.send_keys(entity)
                strategy, value = loc
                self.click((strategy, value % entity))
            else:
                strategy, value = common_locators['entity_checkbox']
                self.click((strategy, value % entity))

    def configure_entity(self, entity_list, filter_key, tab_locator=None,
                         new_entity_list=None, entity_select=True):
        """Configures entities like orgs, OS, ptable, Archs, Users, Usergroups.

        """
        if entity_list is None:
            entity_list = []
        if new_entity_list is None:
            new_entity_list = []
        if entity_list:
            if tab_locator:
                self.click(tab_locator)
            if entity_select:
                entity_locator = common_locators['entity_select']
            else:
                entity_locator = common_locators['entity_deselect']
            self.select_deselect_entity(
                filter_key, entity_locator, entity_list)
        if new_entity_list:
            if tab_locator:
                self.click(tab_locator)
            entity_locator = common_locators['entity_select']
            self.select_deselect_entity(
                filter_key, entity_locator, new_entity_list)

    def delete_entity(self, name, really, del_locator, drop_locator=None):
        """Delete an added entity, handles both with and without dropdown."""
        self.logger.debug(u'Deleting entity %s', name)
        searched = self.search(name)
        if not searched:
            raise UIError(u'Could not search the entity "{0}"'.format(name))
        if self.is_katello:
            searched.click()
            self.wait_for_ajax()
            self.click(del_locator)
            if really:
                self.click(common_locators['confirm_remove'])
            else:
                self.click(common_locators['cancel'])
        else:
            if drop_locator:
                strategy, value = drop_locator
                self.click((strategy, value % name))
            strategy, value = del_locator
            self.click((strategy, value % name), wait_for_ajax=False)
            self.handle_alert(really)
        # Make sure that element is really removed from UI. It is necessary to
        # verify that fact few times as sometimes 1 second is not enough for
        # element to be actually deleted from DB
        self.button_timeout = 3
        self.result_timeout = 1
        try:
            for _ in range(3):
                searched = self.search(name)
                if bool(searched) != really:
                    break
                self.browser.refresh()
            if bool(searched) == really:
                raise UIError(
                    u'Delete functionality works improperly for "{0}" entity'
                    .format(name))
        finally:
            self.button_timeout = 15
            self.result_timeout = 15

    def wait_until_element_exists(
            self, locator, timeout=12, poll_frequency=0.5):
        """Wrapper around Selenium's WebDriver that allows you to pause your
        test until an element in the web page is present.

        """
        try:
            element = WebDriverWait(
                self.browser, timeout, poll_frequency
            ).until(expected_conditions.presence_of_element_located(locator))
            self.wait_for_ajax(poll_frequency=poll_frequency)
            return element
        except TimeoutException as err:
            self.logger.debug(
                "%s: Timed out waiting for element '%s' to exists.",
                type(err).__name__,
                locator[1]
            )
            return None

    def wait_until_element(self, locator, timeout=12, poll_frequency=0.5):
        """Wrapper around Selenium's WebDriver that allows you to pause your
        test until an element in the web page is present and visible.

        """
        try:
            element = WebDriverWait(
                self.browser, timeout, poll_frequency
            ).until(expected_conditions.visibility_of_element_located(locator))
            self.wait_for_ajax(poll_frequency=poll_frequency)
            return element
        except TimeoutException as err:
            self.logger.debug(
                "%s: Timed out waiting for element '%s' to display.",
                type(err).__name__,
                locator[1]
            )
            return None

    def wait_until_element_is_clickable(
            self, locator, timeout=12, poll_frequency=0.5):
        """Wrapper around Selenium's WebDriver that allows you to pause your
        test until an element in the web page is present and can be clicked.

        """
        try:
            element = WebDriverWait(
                self.browser, timeout, poll_frequency
            ).until(expected_conditions.element_to_be_clickable(locator))
            self.wait_for_ajax(poll_frequency=poll_frequency)
            if element.get_attribute('disabled') == u'true':
                return None
            return element
        except TimeoutException as err:
            self.logger.debug(
                '%s: Timed out waiting for element "%s" to display or to be '
                'clickable.',
                type(err).__name__,
                locator[1]
            )
            return None

    def wait_until_element_is_not_visible(
            self, locator, timeout=12, poll_frequency=0.5):
        """Wrapper around Selenium's WebDriver that allows us to pause our test
        until specified element will disappear. That means that it will not be
        present and will not be visible anymore.

        :param locator: Locator of element under test
        :param timeout: How long this method should wait for the element to
            disappear (in seconds)
        :param poll_frequency: How frequently this method should check for the
            presence of the element (in seconds)
        :returns: If the page element still present after timeout expired,
            return None. Otherwise, return True.

        """
        try:
            WebDriverWait(self.browser, timeout, poll_frequency).until(
                expected_conditions.invisibility_of_element_located(locator))
            self.wait_for_ajax(poll_frequency=poll_frequency)
            return True
        except TimeoutException as err:
            self.logger.debug(
                "%s: Timed out waiting for element '%s' to disappear.",
                type(err).__name__,
                locator[1]
            )
            return None

    def ajax_complete(self, driver):
        """
        Checks whether an ajax call is completed.
        """

        jquery_active = False
        angular_active = False

        try:
            jquery_active = driver.execute_script('return jQuery.active') > 0
        except WebDriverException:
            pass

        try:
            angular_active = driver.execute_script(
                'return angular.element(document).injector().get("$http")'
                '.pendingRequests.length') > 0
        except WebDriverException:
            pass

        return not (jquery_active or angular_active)

    def wait_for_ajax(self, timeout=30, poll_frequency=0.5):
        """Waits for an ajax call to complete until timeout."""
        WebDriverWait(
            self.browser, timeout, poll_frequency
        ).until(
            self.ajax_complete, 'Timeout waiting for page to load'
        )

    def scroll_page(self):
        """
        Scrolls page up
        """
        self.browser.execute_script('scroll(350, 0);')

    def scroll_right_pane(self):
        """
        Scrolls right pane down to find the save/submit button
        """
        self.browser.execute_script("$('#panel_main').\
                                    data('jsp').scrollBy(0, 100);")

    def scroll_into_view(self, element):
        """ Scrolls current element into visible area of the browser window."""
        # Here aligntoTop=False option is set.
        self.browser.execute_script(
            'arguments[0].scrollIntoView(false);',
            element,
        )

    def field_update(self, loc_string, newtext):
        """
        Function to replace the existing/default text from textbox
        """
        txt_field = self.find_element(locators[loc_string])
        txt_field.clear()
        self.logger.debug(u'Updating field:%s with:%s', loc_string, newtext)
        txt_field.send_keys(newtext)
        self.wait_for_ajax()

    def text_field_update(self, locator, newtext):
        """
        Function to replace text from textbox using a common locator
        """
        txt_field = self.wait_until_element(locator)
        txt_field.clear()
        self.logger.debug(u'Updating text field:%s with:%s', locator, newtext)
        txt_field.send_keys(newtext)
        self.wait_for_ajax()

    def set_parameter(self, param_name, param_value):
        """
        Function to set parameters for different
        entities like OS and Domain
        """
        self.click(common_locators['parameter_tab'])
        self.click(common_locators['add_parameter'])
        if self.wait_until_element(common_locators['parameter_name']):
            pname = self.find_element(common_locators['parameter_name'])
            pname.send_keys(param_name)
        if self.wait_until_element(common_locators['parameter_value']):
            pvalue = self.find_element(common_locators['parameter_value'])
            pvalue.send_keys(param_value)
        self.click(common_locators['submit'])
        self.logger.debug(u'Param: %s set to: %s', param_name, param_value)

    def remove_parameter(self, param_name):
        """Function to remove parameters for different entities like OS and
        Domain.
        """
        self.click(common_locators['parameter_tab'])
        strategy, value = common_locators['parameter_remove']
        self.click((strategy, value % param_name))
        self.click(common_locators['submit'])
        self.logger.debug(u'Removed param: %s', param_name)

    def edit_entity(self, edit_loc, edit_text_loc, entity_value, save_loc):
        """Function to edit the selected entity's  text and save it."""
        self.click(edit_loc)
        self.text_field_update(edit_text_loc, entity_value)
        self.click(save_loc)

    def set_limit(self, limit):
        """Specify content host limit value for host collection or activation
        key entities.
        """
        self.click(common_locators['usage_limit_checkbox'])
        if limit != 'Unlimited':
            self.text_field_update(common_locators['usage_limit'], limit)

    def select_repo(self, repo_name):
        """Select specific repository for packages or errata search
        functionality
        """
        self.navigate_to_entity()
        self.select(common_locators['select_repo'], repo_name)

    def auto_complete_search(self, go_to_page, entity_locator, partial_name,
                             name, search_key):
        """Auto complete search by giving partial name of any entity.

        :param go_to_page: Navigates to the entities page.
        :param entity_locator: The locator of the entity.
        :param str partial_name: The partial name of the entity.
        :param str name: The name of the entity. Ex: org, loc
        :param str search_key: The search key for searching an entity. Ex: name
        :return: Returns the searched element.

        """
        go_to_page()
        self.text_field_update(
            common_locators['search'],
            search_key + " = " + partial_name
        )
        strategy, value = common_locators['auto_search']
        self.click((strategy, value % name))
        self.click(common_locators['search_button'])
        strategy1, value1 = entity_locator
        return self.wait_until_element((strategy1, value1 % name))

    def check_all_values(self, go_to_page, entity_name, entity_locator,
                         tab_locator, context=None):
        """
        Checks whether the 'All values' checkbox is checked/selected.

        :param go_to_page: Navigates to the entities page.
        :param str entity_name: The name of the entity. Ex: org, loc
        :param entity_locator: The locator of the entity.
        :param tab_locator: The tab locator to switch to the entity's tab.
        :return: Returns whether the element is checked/selected or not.
        :rtype: bool
        :raises robottelo.ui.base.UINoSuchElementError: If the entity is not
            found via search.

        """
        go_to_page()
        searched = self.search(entity_name)
        if searched is None:
            raise UINoSuchElementError('Entity not found via search.')
        searched.click()
        self.click(tab_locator)
        strategy, value = common_locators['all_values']
        selected = self.find_element(
            (strategy, value % context)).is_selected()
        return selected

    def is_element_enabled(self, locator):
        """Check whether UI element is enabled or disabled

        :param locator: The locator of the element.
        :return: Returns True if element is enabled and False otherwise

        """
        element = self.wait_until_element(locator)
        if element is None:
            return False
        self.wait_for_ajax()
        return element.is_enabled()

    def is_element_visible(self, locator):
        """Check whether UI element is visible

        :param locator: The locator of the element.
        :return: Returns True if element is visible and False otherwise

        """
        element = self.wait_until_element_exists(locator)
        if element is None:
            return False
        self.wait_for_ajax()
        return element.is_displayed()

    def element_type(self, locator):
        """Determine UI element type using locator tag

        :param locator: The locator of the element
        :return: Returns element type value
        :rtype: str

        """
        element_type = None
        element = self.wait_until_element(locator)
        if element is not None:
            element_type = element.tag_name.lower()
            if (element_type == 'input' and
                    element.get_attribute('type') == 'checkbox'):
                element_type = 'checkbox'
        return element_type

    def click(self, target, wait_for_ajax=True,
              ajax_timeout=30, waiter_timeout=12, scroll=True):
        """Locate the element described by the ``target`` and click on it.

        :param tuple || WebElement target: Could be either locator that
            describes the element or element itself.
        :param wait_for_ajax: Flag that indicates if should wait for AJAX after
            clicking on the element
        :param ajax_timeout: The amount of time that wait_fox_ajax should wait.
            This will have effect if ``wait_fox_ajax`` parameter is ``True``.
        :param waiter_timeout: The amount of time that wait_until_element
            should wait. That value should be specified when non-default delay
            is needed (e.g. long run procedures)
        :param scroll: Decide whether scroll to element in case it is located
            out of the page
        :raise: UINoSuchElementError if the element could not be found.

        """
        if isinstance(target, tuple):
            element = self.wait_until_element(target, timeout=waiter_timeout)
        else:
            element = target
        if element is None:
            raise UINoSuchElementError(
                u'{0}: element was not found while trying to click'
                .format(type(self).__name__)
            )
        # Required since from selenium 2.48.0. which makes Selenium more
        # closely resemble a user when interacting with elements.
        # Scrolling element into view before attempting to click solves this.
        # Behaviour can be changed with new selenium versions, so it is
        # necessary to validate that functionality in case click method stopped
        # to work as intended
        if scroll:
            self.scroll_into_view(element)
        element.click()
        if wait_for_ajax:
            self.wait_for_ajax(ajax_timeout)

    def select(self, locator, list_value, wait_for_ajax=True, timeout=30,
               scroll=True):
        """Select the element described by the ``locator``. Current method
        supports both classical <select> tags and newer jquery-select elements

        :param locator: The locator that describes the select list element.
        :param list_value: The value to select from the dropdown
        :param wait_for_ajax: Flag that indicates if should wait for AJAX after
            clicking on the element
        :param timeout: The amount of time that wait_fox_ajax should wait. This
            will have effect if ``wait_fox_ajax`` parameter is ``True``.
        :param scroll: Decide whether scroll to element in case it is located
            out of the page

        """
        # Check whether our select list element has <select> tag
        if self.element_type(locator) == 'select':
            element = self.wait_until_element(locator)
            if scroll:
                self.scroll_into_view(element)
            Select(element).select_by_visible_text(list_value)
            if wait_for_ajax:
                self.wait_for_ajax(timeout)
        # If no - treat it like jquery select list
        else:
            self.click(
                locator,
                wait_for_ajax=wait_for_ajax,
                ajax_timeout=timeout,
                scroll=scroll,
            )
            self.text_field_update(
                common_locators['select_list_search_box'], list_value)
            strategy, value = common_locators['entity_select_list']
            self.click(
                (strategy, value % list_value),
                wait_for_ajax=wait_for_ajax,
                ajax_timeout=timeout,
                scroll=scroll,
            )
        self.logger.debug(u'Selected value %s on %s', list_value, locator)

    def perform_action_chain_move(self, locator):
        """Moving the mouse to the middle of an element specified by locator
        parameter

        :param locator: The locator that describes the element.
        :raise: UINoSuchElementError if the element could not be found.

        """
        element = self.wait_until_element(locator)
        if element is None:
            raise UINoSuchElementError(
                u'Cannot move cursor to {0}: element with locator {1}'
                .format(type(self).__name__, locator)
            )
        self.scroll_into_view(element)
        ActionChains(self.browser).move_to_element(element).perform()
        self.wait_for_ajax()

    def perform_action_chain_move_by_offset(self, x=0, y=0):
        """Moving the mouse to an offset from current mouse position

        :param x: X offset to move to
        :param y: Y offset to move to

        """
        ActionChains(self.browser).move_by_offset(x, y).perform()
        self.wait_for_ajax()

    def assign_value(self, locator, value):
        """Assign provided value to page element depending on the type of that
        element

        :param locator: The locator that describes the element.
        :param value: Value that needs to be assigned to the element
        :raise: ValueError if the element type is unknown to our code.

        """
        element_type = self.element_type(locator)
        if element_type == 'input' or element_type == 'textarea':
            self.text_field_update(locator, value)
        elif element_type == 'select' or element_type == 'span':
            self.select(locator, value)
        elif element_type == 'checkbox':
            state = self.wait_until_element(locator).is_selected()
            if value != state:
                self.click(locator)
        else:
            raise ValueError(
                u'Provided locator {0} is not supported by framework'
                .format(locator)
            )
        self.logger.debug(u'Assigned value %s to %s', value, locator)
