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
        if method == By.CSS_SELECTOR:
            return _find_element_by_css_selector(drv, element)
        elif method == By.ID:
            return _find_element_by_id(drv, element)
        elif method == By.NAME:
            return _find_element_by_name(drv, element)
        elif method == By.XPATH:
            return _find_element_by_xpath(drv, element)
    except NoSuchElementException, e:
        logger.warn("Could not locate element '%s'." % element)
    except Exception, e:
        logger.warn("Failed to locate element '%s'. ERROR: %s" % (item, str(e)))


def wait_until_element(drv, element, method=By.NAME, delay=10):

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
        if method == By.CSS_SELECTOR:
            return _wait_until_element_by_css_selector(drv, element, delay)
        elif method == By.ID:
            return _wait_until_element_by_id(drv, element, delay)
        elif method == By.NAME:
            return _wait_until_element_by_name(drv, element, delay)
        elif method == By.XPATH:
            return _wait_until_element_by_xpath(drv, element, delay)
    except TimeoutException, e:
        logger.warn("Timed out waiting for element '%s' to display." % element)
    except NoSuchElementException, e:
        logger.warn("Could not locate element '%s'." % element)
    except Exception, e:
        logger.warn("Failed to locate element '%s'. ERROR: %s" % (element, str(e)))


def _find_element_by_css_selector(drv, element):

    return drv.find_element_by_css_selector(element)


def _find_element_by_id(drv, element):

    return drv.find_element_by_id(element)


def _find_element_by_name(drv, element):

    return drv.find_element_by_name(element)


def _find_element_by_xpath(drv, element):

    return drv.find_element_by_xpath(element)


def _wait_until_element_by_css_selector(drv, element, delay):

    return WebDriverWait(drv, delay).until(lambda driver : _find_element_by_css_selector(driver, element))

def _wait_until_element_by_id(drv, element, delay):

    return WebDriverWait(drv, delay).until(lambda driver : _find_element_by_id(driver, element))

def _wait_until_element_by_name(drv, element, delay):

    return WebDriverWait(drv, delay).until(lambda driver : _find_element_by_name(driver, element))

def _wait_until_element_by_xpath(drv, element, delay):

    return WebDriverWait(drv, delay).until(lambda driver : _find_element_by_xpath(driver, element))
