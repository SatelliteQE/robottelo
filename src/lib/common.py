#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from robot.api import logger

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait


def find_element(drv, element, method=By.NAME):

    """
    Wrapper around Selenium's WebDriver that allows you to search for an element in
    the web page.

    @type drv: object
    @param drv: A Selenium WebDriver instance.
    @type element: string
    @param element: The string representation of the element.
    Exemples:
        "submit"
        "div.error_message"
        "//button[@id='search_button']"
    @type method: object
    @param method: One of the following: By.CSS_SELECTOR, By.ID, By.NAME, By.XPATH.

    @rtype: object
    @return: A Selenium WebElement object or None if not found.
    """

    try:
        return drv.find_element(method, element)
    except NoSuchElementException, e:
        logger.warn("Could not locate element '%s'." % element)
        return None
    except Exception, e:
        logger.warn("Failed to locate element '%s'. ERROR: %s" % (element, str(e)))
        return None


def wait_until_element(drv, element, method=By.NAME, delay=20):

    """
    Wrapper around Selenium's WebDriver that allows you to pause your test until
    an element in the web page is present.

    @type drv: object
    @param drv: A Selenium WebDriver instance.
    @type element: string
    @param element: The string representation of the element.
    Exemples:
        "submit"
        "div.error_message"
        "//button[@id='search_button']"
    @type method: object
    @param method: One of the following: By.CSS_SELECTOR, By.ID, By.NAME, By.XPATH.
    @type delay: integer
    @param delay: The time to wait in seconds. Default is 10 seconds.

    @rtype: object
    @return: A Selenium WebElement object or None if not found.
    """

    try:
        return WebDriverWait(drv, delay).until(lambda driver : find_element(driver, element, method))
    except TimeoutException, e:
        logger.warn("Timed out waiting for element '%s' to display." % element)
        return None
    except NoSuchElementException, e:
        logger.warn("Could not locate element '%s'." % element)
        return None
    except Exception, e:
        logger.warn("Failed to locate element '%s'. ERROR: %s" % (element, str(e)))
        return None
