# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Base class for all UI operations
"""
import logging
from robottelo.ui.locators import locators, common_locators
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from robottelo.common.helpers import escape_search
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class UINoSuchElementError(Exception):
    """
    Indicates that UI Element is not found.
    """


class UIPageSubmitionFailed(Exception):
    """Indicates that UI Page submition Failed."""


class Base(object):
    """
    Base class for UI
    """

    logger = logging.getLogger("robottelo")

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def find_element(self, locator):
        """
        Wrapper around Selenium's WebDriver that allows you to search for an
        element in the web page.
        """
        try:
            _webelement = self.browser.find_element(*locator)
            if _webelement.is_displayed():
                return _webelement
            else:
                return None
        except NoSuchElementException as e:
            logging.debug("%s: Could not locate element %s.",
                          type(e).__name__,
                          locator[1])
            return None
        except Exception, error:
            logging.debug("Failed to locate element. ERROR: %s", str(error))
            return None

    def search_entity(self, element_name, element_locator, search_key=None,
                      katello=None, timeout=None):
        """
        Uses the search box to locate an element from a list of elements.
        """

        search_key = search_key or "name"
        element = None

        if katello:
            searchbox = self.wait_until_element(common_locators["kt_search"])
            search_button = self.wait_until_element(common_locators
                                                    ["kt_search_button"])
        else:
            searchbox = self.wait_until_element(common_locators["search"])
            search_button = self.wait_until_element(common_locators
                                                    ["search_button"])

        # Do not proceed if searchbox is not found
        if searchbox is None:
            raise Exception("Search box not found.")
        else:
            searchbox.clear()
            if search_button:
                searchbox.send_keys(search_key + " = " +
                                    escape_search(element_name))
                search_button.click()
            else:
                searchbox.send_keys(escape_search(element_name))
            if timeout:
                element = self.wait_until_element(
                    (element_locator[0], element_locator[1] % element_name),
                    delay=timeout)
            else:
                element = self.wait_until_element(
                    (element_locator[0], element_locator[1] % element_name))
        return element

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
        """
        Function to select and deselect entity like OS, Partition Table, Arch
        from selection list or by selecting relevant checkbox.
        """
        for entity in entity_list:
            strategy, value = common_locators["filter"]
            txt_field = self.wait_until_element((strategy, value % filter_key))
            if txt_field:
                txt_field.clear()
                txt_field.send_keys(entity)
                strategy, value = loc
                select_element = self.wait_until_element((strategy,
                                                          value % entity))
                if select_element:
                    select_element.click()
                else:
                    raise UINoSuchElementError(
                        "Couldn't find element from selection list")
            else:
                strategy1, value1 = common_locators["entity_checkbox"]
                checkbox_element = self.wait_until_element((strategy1,
                                                            value1 % entity))
                if checkbox_element:
                    checkbox_element.click()
                else:
                    raise UINoSuchElementError(
                        "Couldn't find element from checkbox list.")

    def configure_entity(self, entity_list, filter_key, tab_locator=None,
                         new_entity_list=None, entity_select=True):
        """
        Configures entities like orgs, OS, ptable, Archs, Users, Usergroups.
        """
        if entity_list is None:
            entity_list = []
        if new_entity_list is None:
            new_entity_list = []
        if entity_list:
            if tab_locator:
                self.wait_until_element(tab_locator).click()
            if entity_select:
                entity_locator = common_locators["entity_select"]
            else:
                entity_locator = common_locators["entity_deselect"]
            self.select_deselect_entity(filter_key,
                                        entity_locator, entity_list)
        if new_entity_list:
            if tab_locator:
                self.wait_until_element(tab_locator).click()
            entity_locator = common_locators["entity_select"]
            self.select_deselect_entity(filter_key,
                                        entity_locator, new_entity_list)

    def delete_entity(self, name, really, name_locator, del_locator,
                      drop_locator=None, search_key=None):
        """
        Delete an added entity, handles both with and without dropdown.
        """
        searched = self.search_entity(name, name_locator,
                                      search_key=search_key)
        if searched:
            if drop_locator:
                strategy = drop_locator[0]
                value = drop_locator[1]
                dropdown = self.wait_until_element((strategy, value % name))
                dropdown.click()
            strategy1 = del_locator[0]
            value1 = del_locator[1]
            element = self.wait_until_element((strategy1, value1 % name))
            if element is None:
                raise UINoSuchElementError(
                    "Could not select the entity '%s' for deletion." % name)
            element.click()
            self.handle_alert(really)
        else:
            raise Exception("Could not search the entity '%s'" % name)

    def wait_until_element(self, locator, delay=12):
        """
        Wrapper around Selenium's WebDriver that allows you to pause your test
        until an element in the web page is present.
        """
        try:
            element = WebDriverWait(self.browser, delay).until(
                EC.visibility_of_element_located(locator)
            )
            return element
        except TimeoutException as e:
            logging.debug("%s: Timed out waiting for element '%s' to display.",
                          type(e).__name__, locator[1])
            return None
        except Exception, error:
            logging.debug("Failed to locate element. ERROR: %s",
                          type(error).__name__)
            return None

    def ajax_complete(self, driver):
        """
        Checks whether an ajax call is completed.
        """

        jquery_active = False
        angular_active = False

        try:
            jquery_active = driver.execute_script("return jQuery.active") > 0
        except WebDriverException:
            pass

        try:
            angular_active = driver.execute_script(
                'return angular.element(document).injector().get("$http")'
                '.pendingRequests.length') > 0
        except WebDriverException:
            pass

        return not (jquery_active or angular_active)

    def wait_for_ajax(self, timeout=30):
        """
        Waits for an ajax call to complete until timeout.
        """

        WebDriverWait(
            self.browser, timeout
        ).until(
            self.ajax_complete, "Timeout waiting for page to load"
        )

    def scroll_page(self):
        """
        Scrolls page up
        """
        self.browser.execute_script("scroll(350, 0);")

    def scroll_right_pane(self):
        """
        Scrolls right pane down to find the save/submit button
        """
        self.browser.execute_script("$('#panel_main').\
                                    data('jsp').scrollBy(0, 100);")

    def field_update(self, loc_string, newtext):
        """
        Function to replace the existing/default text from textbox
        """
        txt_field = self.find_element(locators[loc_string])
        txt_field.clear()
        txt_field.send_keys(newtext)

    def text_field_update(self, locator, newtext):
        """
        Function to replace text from textbox using a common locator
        """
        txt_field = self.wait_until_element(locator)
        txt_field.clear()
        txt_field.send_keys(newtext)

    def set_parameter(self, param_name, param_value):
        """
        Function to set parameters for different
        entities like OS and Domain
        """
        self.wait_until_element(common_locators["parameter_tab"]).click()
        self.wait_until_element(common_locators["add_parameter"]).click()
        if self.wait_until_element(common_locators["parameter_name"]):
            pname = self.find_element(common_locators["parameter_name"])
            pname.send_keys(param_name)
        if self.wait_until_element(common_locators["parameter_value"]):
            pvalue = self.find_element(common_locators["parameter_value"])
            pvalue.send_keys(param_value)
        self.find_element(common_locators["submit"]).click()
        self.wait_for_ajax()

    def remove_parameter(self, param_name):
        """
        Function to remove parameters for different
        entities like OS and Domain
        """
        self.wait_until_element(common_locators["parameter_tab"]).click()
        strategy = common_locators["parameter_remove"][0]
        value = common_locators["parameter_remove"][1]
        remove_element = self.wait_until_element((strategy,
                                                  value % param_name))
        if remove_element:
            remove_element.click()
        self.find_element(common_locators["submit"]).click()

    def edit_entity(self, edit_loc, edit_text_loc, entity_value, save_loc):
        """
        Function to edit the selected entity's  text and save it
        """

        self.wait_until_element(locators[edit_loc]).click()
        self.field_update(edit_text_loc, entity_value)
        self.wait_until_element(locators[save_loc]).click()
        self.wait_for_ajax()

    def auto_complete_search(self, go_to_page, entity_locator, partial_name,
                             name, search_key):
        """
        Auto complete search by giving partial name of any entity.

        :param go_to_page: Navigates to the entities page.
        :param entity_locator: The locator of the entity.
        :param str partial_name: The partial name of the entity.
        :param str name: The name of the entity. Ex: org, loc
        :param str search_key: The search key for searching an entity. Ex: name
        :return: Returns the searched element.

        """
        go_to_page()
        strategy1, value1 = entity_locator
        searchbox = self.wait_until_element(common_locators["search"])
        if searchbox is None:
            raise UINoSuchElementError("Search box not found.")
        searchbox.clear()
        searchbox.send_keys(search_key + " = " + partial_name)
        self.wait_for_ajax()
        strategy, value = common_locators["auto_search"]
        element = self.wait_until_element((strategy, value % name))
        if element is None:
            raise UINoSuchElementError(
                "Entity not found via auto search completion.")
        element.click()
        self.wait_for_ajax()
        search_button = self.wait_until_element(
            common_locators['search_button'])
        if search_button is None:
            raise UINoSuchElementError("Search button not found.")
        search_button.click()
        entity_elem = self.wait_until_element((strategy1, value1 % name))
        return entity_elem

    def check_all_values(self, go_to_page, entity_name, entity_locator,
                         tab_locator, context=None):
        """
        Checks whether the 'All values' checkbox is checked/selected.

        :param go_to_page: Navigates to the entities page.
        :param str entity_name: The name of the entity. Ex: org, loc
        :param entity_locator: The locator of the entity.
        :param tab_locator: The tab locator to switch to the entity's tab.
        :return: Returns whether the element is checked/selected or not.
        :rtype: boolean value
        :raises robottelo.ui.base.UINoSuchElementError: If the entity is not
            found via search.

        """
        go_to_page()
        strategy, value = common_locators['all_values']
        searched = self.search_entity(entity_name, entity_locator)
        if searched is None:
            raise UINoSuchElementError("Entity not found via search.")
        searched.click()
        self.wait_until_element(tab_locator).click()
        selected = self.find_element((strategy,
                                      value % context)).is_selected()
        return selected

    def submit_and_validate(self, locator, validation=True):
        """
        Submit the page and validate.

        :param str locator: The locator used to submit the page.
        :param boolean validation: Helps enable or disable validation.
            Needs to be set to False for the negative tests.

        """
        self.wait_until_element(locator).click()
        self.wait_for_ajax()
        if self.wait_until_element(locator) and validation:
            raise UIPageSubmitionFailed("Page submission failed.")
