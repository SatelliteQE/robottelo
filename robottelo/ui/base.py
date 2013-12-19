#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging.config

from robottelo.common import conf
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from robottelo.ui.locators import locators


class Base():

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
        except NoSuchElementException, e:
            self.logger.debug("Could not locate element '%s'." % locator[1])
            return None
        except Exception, e:
            self.logger.debug("Failed to locate element. ERROR: %s" % str(e))
            return None

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
        except TimeoutException, e:
            self.logger.debug(
                "Timed out waiting for element '%s' to display." % locator[1])
            return None
        except NoSuchElementException, e:
            self.logger.debug("Element '%s' was never found." % locator[1])
            return None
        except Exception, e:
            self.logger.debug("Failed to locate element. ERROR: %s" % str(e))
            return None

    def ajax_complete(self, driver):
        try:
            return 0 == driver.execute_script("return jQuery.active")
        except WebDriverException:
            pass

    def wait_for_ajax(self):
        WebDriverWait(
            self.browser, 30
        ).until(
            self.ajax_complete, "Timeout waiting for page to load"
        )

    def field_update(self, loc_string, newtext):
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
            self.wait_until_element(locators[loc_tab]).click()
        check_element = self.find_element((locators
                                           [loc_string][0],
                                           locators
                                           [loc_string][1]
                                           % loc_value))
        select_element = self.find_element((locators
                                            [loc_select_string][0],
                                            locators
                                            [loc_select_string][1]
                                            % loc_value))
        if check_element:
            check_element.click()
        elif select_element:
            select_element.click()

    def set_parameter(self, param_name, param_value):

        """
        Function to set parameters for different entities like OS and Domain
        """

        self.wait_until_element(locators["parameter_tab"]).click()
        self.wait_until_element(locators["add_parameter"]).click()
        if self.wait_until_element(locators
                                   ["parameter_name"]):
            self.find_element(locators
                              ["parameter_name"]
                              ).send_keys(param_name)
        if self.wait_until_element(locators
                                   ["parameter_value"]):
            self.find_element(locators
                              ["parameter_value"]
                              ).send_keys(param_value)
        self.find_element(locators["submit"]).click()
        self.wait_for_ajax()

    def remove_parameter(self, param_name):

        """
        Function to remove parameters for different entities like OS and Domain
        """

        self.wait_until_element(locators["parameter_tab"]).click()
        remove_element = self.wait_until_element((locators
                                                  ["parameter_remove"][0],
                                                  locators
                                                  ["parameter_remove"][1]
                                                  % param_name))
        if remove_element:
            remove_element.click()
        self.find_element(locators["submit"]).click()
