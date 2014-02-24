# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Base class for all UI operations
"""
import logging.config

from robottelo.ui.locators import locators, common_locators
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Base(object):
    """
    Base class for UI
    """

    logger = logging.getLogger("robottelo")

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
        except NoSuchElementException:
            self.logger.debug("Could not locate element '%s'." % locator[1])
            return None
        except Exception, error:
            self.logger.debug(
                "Failed to locate element. ERROR: %s" % str(error))
            return None

    def search_entity(self, element_name, element_locator, search_key=None,
                      katello=None):
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
                searchbox.send_keys(search_key + " = " + element_name)
                search_button.click()
            else:
                searchbox.send_keys(element_name)
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
        from selection list or by selecting relevant checkbox
        """
        for entity in entity_list:
            strategy = common_locators["filter"][0]
            value = common_locators["filter"][1]
            txt_field = self.find_element((strategy, value % filter_key))
            if txt_field:
                txt_field.clear()
                txt_field.send_keys(entity)
            strategy = loc[0]
            value = loc[1]
            strategy1 = common_locators["entity_checkbox"][0]
            value1 = common_locators["entity_checkbox"][1]
            checkbox_element = self.find_element((strategy1, value1 % entity))
            select_element = self.find_element((strategy, value % entity))
            if checkbox_element:
                checkbox_element.click()
            elif select_element:
                select_element.click()

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
            if element:
                element.click()
                self.handle_alert(really)
            else:
                raise Exception(
                    "Could not select the entity '%s' for deletion." % name)
        else:
            raise Exception("Could not search the entity '%s'" % name)

    def wait_until_element(self, locator, delay=20):
        """
        Wrapper around Selenium's WebDriver that allows you to pause your test
        until an element in the web page is present.
        """
        try:
            element = WebDriverWait(
                self.browser, delay
            ).until(EC.visibility_of_element_located((locator)))
            return element
        except TimeoutException:
            self.logger.debug(
                "Timed out waiting for element '%s' to display." % locator[1])
            return None
        except NoSuchElementException:
            self.logger.debug("Element '%s' was never found." % locator[1])
            return None
        except Exception, error:
            self.logger.debug(
                "Failed to locate element. ERROR: %s" % str(error))
            return None

    def ajax_complete(self, driver):
        """
        Checks whether an ajax call is completed.
        """

        try:
            return 0 == driver.execute_script("return jQuery.active")
        except WebDriverException:
            pass

    def wait_for_ajax(self):
        """
        Waits for an ajax call to complete.
        """

        WebDriverWait(
            self.browser, 30
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

        self.find_element(locators[edit_loc]).click()
        self.field_update(edit_text_loc, entity_value)
        self.find_element(locators[save_loc]).click()
