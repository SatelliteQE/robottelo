#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

import logging.config

from lib.common import conf
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Base():

    logging.config.fileConfig("%s/logging.conf" % conf.get_root_path())
    logger = logging.getLogger("robottelo")
    logger.setLevel(int(conf.properties['nosetests.verbosity']))

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
