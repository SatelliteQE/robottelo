# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Base class for all UI operations
"""

import logging.config

from robottelo.ui.locators import locators
from robottelo.ui.locators import common_locators
from robottelo.ui.locators import tab_locators
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
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

    def search(self, element_name, element_locator, search_key=None):
        """
        Uses the search box to locate an element from a list of elements.
        """

        search_key = search_key or "name"
        element = None

        searchbox = self.wait_until_element(common_locators["search"])

        if searchbox:
            searchbox.clear()
            searchbox.send_keys(search_key + " = " + element_name)
            searchbox.send_keys(Keys.RETURN)
            element = self.wait_until_element(
                (element_locator[0], element_locator[1] % element_name))

        return element

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

    def field_update(self, loc_string, newtext):
        """
        Function to replace the existing/default text from textbox
        """
        txt_field = self.find_element(locators[loc_string])
        txt_field.clear()
        txt_field.send_keys(newtext)

    def select_entity(self, loc_string, loc_select_string,
                      loc_value, loc_tab=None):
        """
        Function to select an entity like OS, Partition Table, Arch
        from selection list or by selecting relevant checkbox
        """
        if loc_tab:
            self.wait_until_element(tab_locators[loc_tab]).click()
        strategy = locators[loc_string][0]
        value = locators[loc_string][1]
        check_element = self.find_element((strategy, value % loc_value))
        strategy1 = locators[loc_select_string][0]
        value1 = locators[loc_select_string][1]
        select_element = self.find_element((strategy1, value1 % loc_value))
        if check_element:
            check_element.click()
        elif select_element:
            select_element.click()

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
