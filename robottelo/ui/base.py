# -*- encoding: utf-8 -*-
"""Base class for all UI operations"""

import logging
import time

from robottelo.helpers import escape_search
from robottelo.ui.locators import (
    common_locators,
    menu_locators,
    locators,
    Locator,
)
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
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
    delete_locator = None
    actions_dropdown_locator = None

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
                u'%s: Could not locate element %s: %s',
                type(err).__name__,
                locator[1],
                err
            )
        except TimeoutException as err:
            self.logger.debug(
                u'%s: Waiting for locator %s: %s',
                type(err).__name__,
                locator[1],
                err
            )
        return None

    def find_elements(self, locator):
        """Wrapper around Selenium's WebDriver that allows you to fetch list of
        elements in the web page.

        """
        try:
            _webelements = self.browser.find_elements(*locator)
            self.wait_for_ajax()
            webelements = []
            for _webelement in _webelements:
                if _webelement.is_displayed():
                    webelements.append(_webelement)
            return webelements
        except NoSuchElementException as err:
            self.logger.debug(
                u'%s: Could not locate the elements of %s: %s',
                type(err).__name__,
                locator[1],
                err
            )
        except TimeoutException as err:
            self.logger.debug(
                u'%s: Waiting for locator "%s": "%s"',
                type(err).__name__,
                locator[1],
                err
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

    def search_and_click(self, element):
        """Helper method to perform the commonly used search then click"""
        return self.click(self.search(element))

    def search(self, element, _raw_query=None, expecting_results=True):
        """Uses the search box to locate an element from a list of elements.

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

    def delete(self, name, really=True, dropdown_present=False,
               search_query=None):
        """Delete an added entity, handles both with and without dropdown."""
        self.logger.debug(u'Deleting entity %s', name)
        # Some overridden search methods do not support search queries,
        # e.g. when page does not have search field. Skip search_query then.
        if search_query:
            searched = self.search(name, _raw_query=search_query)
        else:
            searched = self.search(name)
        if not searched:
            raise UIError(u'Could not search the entity "{0}"'.format(name))
        if self.is_katello:
            self.click(searched)
            if self.delete_locator:
                self.click(self.delete_locator)
            else:
                self.perform_entity_action('Remove')
            if really:
                self.click(common_locators['confirm_remove'])
            else:
                self.click(common_locators['close'])
        else:
            if dropdown_present:
                if self.actions_dropdown_locator:
                    self.click(self.actions_dropdown_locator % name)
                else:
                    self.click(
                        common_locators['select_action_dropdown'] % name)
            if self.delete_locator:
                self.click(self.delete_locator % name, wait_for_ajax=False)
            else:
                self.click(
                    common_locators['delete_button'] % name,
                    wait_for_ajax=False
                )
            self.handle_alert(really)
        # Make sure that element is really removed from UI. It is necessary to
        # verify that fact few times as sometimes 1 second is not enough for
        # element to be actually deleted from DB
        self.button_timeout = 3
        self.result_timeout = 1
        try:
            for _ in range(3):
                if search_query:
                    searched = self.search(name, _raw_query=search_query)
                else:
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

    def clear_search_box(self):
        """Helper to clear text that was inputted into search box using
        application button
        """
        prefix = 'kt_' if self.is_katello else ''
        self.click(common_locators[prefix + 'clear_search'])

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
        """Handles any alerts"""
        alert = self.browser.switch_to_alert()
        if really:
            alert.accept()
        else:
            alert.dismiss()

    def get_alert_text(self):
        """Get alert text"""
        alert = self.browser.switch_to_alert()
        return alert.text

    def select_deselect_entity(self, filter_key, loc, entity_list):
        """Function to select and deselect entity like OS, Partition Table,
        Arch from selection list or by selecting relevant checkbox.

        """
        for entity in entity_list:
            # Scroll to top
            self.browser.execute_script('window.scroll(0, 0)')
            txt_field = self.wait_until_element(
                common_locators['filter'] % filter_key)
            self.logger.debug(u'Toggling entity %s select state', entity)
            if txt_field:
                txt_field.clear()
                txt_field.send_keys(entity)
                self.click(loc % entity)
            else:
                self.click(common_locators['entity_checkbox'] % entity)

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

    def wait_until_element_exists(self, locator, timeout=12,
                                  poll_frequency=0.5):
        """Wrapper around Selenium's WebDriver that allows you to pause your
        test until an element in the web page is present.

        """
        try:
            element = WebDriverWait(
                self.browser, timeout, poll_frequency
            ).until(
                expected_conditions.presence_of_element_located(locator),
                message=u'element %s is not present' % locator[1]
            )
            self.wait_for_ajax(poll_frequency=poll_frequency)
            return element
        except TimeoutException as err:
            self.logger.debug(
                u"%s: Waiting for element '%s' to exists. %s",
                type(err).__name__,
                locator[1],
                err
            )
            return None

    def wait_until_element(self, locator, timeout=12, poll_frequency=0.5):
        """Wrapper around Selenium's WebDriver that allows you to pause your
        test until an element in the web page is present and visible.

        """
        try:
            element = WebDriverWait(
                self.browser, timeout, poll_frequency
            ).until(
                expected_conditions.visibility_of_element_located(locator),
                message=u'element %s is not visible' % locator[1]
            )
            self.wait_for_ajax(poll_frequency=poll_frequency)
            return element
        except TimeoutException as err:
            self.logger.debug(
                u"%s: Waiting for element '%s' to display. %s",
                type(err).__name__,
                locator[1],
                err
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
            ).until(
                expected_conditions.element_to_be_clickable(locator),
                message=u'element %s is not clickable' % locator[1]
            )
            self.wait_for_ajax(poll_frequency=poll_frequency)
            if element.get_attribute('disabled') == u'true':
                return None
            return element
        except TimeoutException as err:
            self.logger.debug(
                u'%s: Waiting for element "%s" to display or to be '
                u'clickable. %s',
                type(err).__name__,
                locator[1],
                err
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
                u"%s: Waiting for element '%s' to disappear. %s",
                type(err).__name__,
                locator[1],
                err
            )
            return None

    def ajax_complete(self, driver):
        """
        Checks whether an ajax call is completed.
        """

        jquery_active = False
        angular_active = False

        try:
            val = driver.execute_script('return jQuery.active')
            jquery_active = isinstance(val, int) and val > 0
        except WebDriverException:
            pass

        try:
            val = driver.execute_script(
                u'return angular.element(document).injector().get("$http")'
                u'.pendingRequests.length')
            angular_active = isinstance(val, int) and val > 0
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

    def execute_js_event(self, element, event='onchange()'):
        """Execute necessary javascript event for provided web element"""
        self.browser.execute_script(
            'arguments[0].{};'.format(event),
            element,
        )

    def scroll_page(self):
        """Scrolls page up"""
        self.browser.execute_script('scroll(350, 0);')

    def scroll_right_pane(self):
        """Scrolls right pane down to find the save/submit button"""
        self.browser.execute_script(
            "$('#panel_main').data('jsp').scrollBy(0, 100);")

    def scroll_into_view(self, element):
        """ Scrolls current element into visible area of the browser window."""
        # Here aligntoTop=False option is set.
        self.browser.execute_script(
            'arguments[0].scrollIntoView(false);',
            element,
        )

    def input(self, target, newtext):
        """Function to replace text from textbox using a common locator or
        WebElement

        :param tuple || Locator || WebElement target: Either locator that
            describes the element or element itself.
        """
        if isinstance(target, (tuple, Locator)):
            txt_field = self.wait_until_element(target)
        else:
            txt_field = target
        txt_field.clear()
        txt_field.send_keys(newtext)
        self.wait_for_ajax()

    def get_parameter(self, param_name):
        """Function to get parameter value for different entities like OS and
        Domain
        """
        self.click(common_locators['parameter_tab'])
        value_elem = self.find_element(
            common_locators['parameter_value'] % param_name)
        return value_elem.text if value_elem else None

    def set_parameter(self, param_name, param_value, submit=True):
        """Function to set parameters for different entities like OS and Domain
        """
        self.click(common_locators['parameter_tab'])
        self.click(common_locators['add_parameter'])
        self.assign_value(common_locators['new_parameter_name'], param_name)
        self.assign_value(common_locators['new_parameter_value'], param_value)
        if submit:
            self.click(common_locators['submit'])
        self.logger.debug(u'Param: %s set to: %s', param_name, param_value)

    def remove_parameter(self, param_name):
        """Function to remove parameters for different entities like OS and
        Domain.
        """
        self.click(common_locators['parameter_tab'])
        self.click(common_locators['parameter_remove'] % param_name)
        self.click(common_locators['submit'])
        self.logger.debug(u'Removed param: %s', param_name)

    def edit_entity(self, edit_loc, edit_text_loc, entity_value, save_loc):
        """Function to edit the selected entity's  text and save it."""
        self.click(edit_loc)
        self.assign_value(edit_text_loc, entity_value)
        self.click(save_loc)

    def set_limit(self, limit):
        """Specify content host limit value for host collection or activation
        key entities.
        """
        self.click(common_locators['usage_limit_checkbox'])
        if limit != 'Unlimited':
            self.assign_value(common_locators['usage_limit'], limit)

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
        self.assign_value(
            common_locators['search'],
            search_key + " = " + partial_name
        )
        self.click(common_locators['auto_search'] % name)
        self.click(common_locators['search_button'])
        return self.wait_until_element(entity_locator % name)

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
        selected = self.find_element(
            common_locators['all_values'] % context).is_selected()
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

    def element_type(self, target):
        """Determine UI element type using locator/element tag

        :param tuple || Locator || WebElement target: Either locator that
            describes the element or element itself.
        :return: Returns element type value
        :rtype: str

        """
        element_type = None
        if isinstance(target, (tuple, Locator)):
            element = self.wait_until_element(target)
        else:
            element = target
        if element is not None:
            element_type = element.tag_name.lower()
            if (element_type == 'input' and
                    element.get_attribute('type') == 'checkbox'):
                element_type = 'checkbox'
            elif (element_type == 'input' and
                    element.get_attribute('type') == 'radio'):
                element_type = 'radio'
            elif (element_type == 'div' and
                    'ace_editor' in element.get_attribute('class')):
                element_type = 'ace_editor'
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
        if isinstance(target, (tuple, Locator)):
            element = self.wait_until_element(target, timeout=waiter_timeout)
        else:
            element = target
        if element is None:
            raise UINoSuchElementError(
                '{0}: element {1} was not found while trying to click'
                .format(type(self).__name__, str(target))
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

    def select(self, target, list_value, wait_for_ajax=True, timeout=30,
               scroll=True, select_by='visible_text'):
        """Select the element. Current method supports both classical <select>
        tags and newer jquery-select elements

        :param tuple || Locator || WebElement target: Either locator that
            describes the element or element itself.
        :param list_value: The value to select from the dropdown
        :param wait_for_ajax: Flag that indicates if should wait for AJAX after
            clicking on the element
        :param timeout: The amount of time that wait_fox_ajax should wait. This
            will have effect if ``wait_fox_ajax`` parameter is ``True``.
        :param scroll: Decide whether scroll to element in case it is located
            out of the page
        :param select_by: method for select element in the list of options
            visible_text, index, value

        """
        # Check whether our select list element has <select> tag
        if self.element_type(target) == 'select':
            if isinstance(target, (tuple, Locator)):
                element = self.wait_until_element(target)
            else:
                element = target
            if scroll:
                self.scroll_into_view(element)
            select_element = Select(element)
            getattr(select_element, 'select_by_%s' % select_by)(list_value)
            if wait_for_ajax:
                self.wait_for_ajax(timeout)
        # If no - treat it like jquery select list
        else:
            self.click(
                target,
                wait_for_ajax=wait_for_ajax,
                ajax_timeout=timeout,
                scroll=scroll,
            )
            self.assign_value(
                common_locators['select_list_search_box'], list_value)
            self.click(
                common_locators['entity_select_list'] % list_value,
                wait_for_ajax=wait_for_ajax,
                ajax_timeout=timeout,
                scroll=scroll,
            )
        self.logger.debug(u'Selected value %s on %s', list_value, str(target))

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

    def assign_value(self, target, value):
        """Assign provided value to page element depending on the type of that
        element

        :param tuple || Locator || WebElement target: Either locator that
            describes the element or element itself.
        :param value: Value that needs to be assigned to the element
        :raise: ValueError if the element type is unknown to our code.

        """
        element_type = self.element_type(target)
        if element_type == 'input' or element_type == 'textarea':
            self.input(target, value)
        elif element_type == 'select' or element_type == 'span':
            self.select(target, value)
        elif element_type == 'checkbox' or element_type == 'radio':
            if isinstance(target, (tuple, Locator)):
                state = self.wait_until_element(target).is_selected()
            else:
                state = target.is_selected()
            if value != state:
                self.click(target)
        elif element_type == 'ace_editor':
            if isinstance(target, (tuple, Locator)):
                ace_edit_element = self.wait_until_element(target)
            else:
                ace_edit_element = target
            ace_edit_id = ace_edit_element.get_attribute("id")
            self.browser.execute_script(
                "ace.edit('{0}').setValue('{1}');".format(ace_edit_id, value))
        else:
            raise ValueError(
                u'Provided target {0} is not supported by framework'
                .format(str(target))
            )
        self.logger.debug(u'Assigned value %s to %s', value, str(target))

    def get_element_value(self, target):
        """Get page element value depending on the type of that element

        :param tuple || Locator || WebElement target: Either locator that
            describes the element or element itself.
        :raise: ValueError if the element type is unknown to our code.

        """
        element_type = self.element_type(target)
        if isinstance(target, (tuple, Locator)):
            element = self.wait_until_element(target)
        else:
            element = target
        if element_type == 'input':
            value = element.get_attribute('value')
        elif element_type == 'span':
            value = element.text
        elif element_type == 'select':
            value = Select(element).first_selected_option.text
        elif element_type == 'checkbox' or element_type == 'radio':
            value = element.is_selected()
        else:
            raise ValueError(
                u'Provided target {0} is not supported by framework'
                .format(str(target))
            )
        return value

    def clear_entity_value(self, target):
        """Clear current value for provided page element

        :param tuple || Locator || WebElement target: Either locator that
            describes the element or element itself.

        """
        element_type = self.element_type(target)
        if element_type == 'input' or element_type == 'textarea':
            self.input(target, '')
        elif element_type == 'abbr':
            self.click(target)

    def perform_entity_action(self, action_name):
        """Execute specified action from katello entity 'Select Action'
        dropdown

        :param action_name: Name of action to be executed (e.g.
            'Remove Product')
        """
        self.click(common_locators['kt_select_action_dropdown'])
        self.click(common_locators['select_action'] % action_name)

    def sort_table_by_column(self, column_name):
        """Sort entity table by specific column name

        :param str column_name: Name of the column which is used for sorting
        :return: List of cell values after table is reordered
        """
        self.click(common_locators['table_column_title'] % column_name)
        self.wait_until_element_is_not_visible(menu_locators['navbar.spinner'])
        self.wait_for_ajax()
        cell_values = [
            element.text for element in self.find_elements(
                common_locators['table_column_values'] % column_name)
        ]
        return cell_values

    def perform_action_send_keys_to_browser(self, keys):
        """Send some key(s) to browser.

        :param keys: Key(s) to send to browser. Keys may be several keys
            including special, like ``control+shift+q``, single special or
            simple key, e.g. ``escape``, ``q``.
        """
        keys_to_send = ''.join(
            getattr(Keys, key.upper()) if key.upper() in dir(Keys) else
            key for key in keys.split('+'))
        ActionChains(self.browser).send_keys(keys_to_send).perform()
        self.wait_for_ajax()
