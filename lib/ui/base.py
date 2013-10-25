#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Base():

    def find_element(self, locator):
        """
        Wrapper around Selenium's WebDriver that allows you to search for an element in
        the web page.
        """

        try:
            _webelement = self.browser.find_element(*locator)
            if _webelement.is_displayed():
                return _webelement
            else:
                return None
        except NoSuchElementException, e:
            #self.logger.debug("Could not locate element.")
            return None
        except Exception, e:
            #self.logger.debug("Failed to locate element. ERROR: %s" % str(e))
            return None

    def wait_until_element(self, locator, delay=20):

        """
        Wrapper around Selenium's WebDriver that allows you to pause your test until
        an element in the web page is present.
        """

        try:
            element = WebDriverWait(self.browser, delay).until(EC.visibility_of_element_located((locator)))
            return element
        except TimeoutException, e:
            #self.logger.debug("Timed out waiting for element to display.")
            return None
        except NoSuchElementException, e:
            #self.logger.debug("Could not locate element.")
            return None
        except Exception, e:
            #self.logger.warn("Failed to locate element. ERROR: %s" % str(e))
            return None
