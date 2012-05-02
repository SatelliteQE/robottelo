#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai


import os
import tempfile

from urllib import urlopen

from robot.api import logger
from robot.utils import asserts

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait


def get_manifest_file(manifest_url):
    """
    Downloads a manifest file locally to the file system.

    @type manifest_file: string
    @param manifest_file: The url to a valid manifest file.

    @rtype: string
    @return: The absolute path to the downloaded file.
    """

    try:
        remote_file = urlopen(manifest_url)
    except Exception, e:
        asserts.assert_fail("Failed to download the manifest file at %s." % manifest_url)

    (fd, filename) = tempfile.mkstemp()
    for line in remote_file.readlines():
        f.write(line)
    f.close()

    return filename


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
        _webelement = drv.find_element(method, element)
        if _webelement.is_displayed():
            return _webelement
        else:
            return None
    except NoSuchElementException, e:
        logger.debug("Could not locate element '%s'." % element)
        return None
    except Exception, e:
        logger.debug("Failed to locate element '%s'. ERROR: %s" % (element, str(e)))
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
        logger.debug("Timed out waiting for element '%s' to display." % element)
        return None
    except NoSuchElementException, e:
        logger.debug("Could not locate element '%s'." % element)
        return None
    except Exception, e:
        logger.warn("Failed to locate element '%s'. ERROR: %s" % (element, str(e)))
        return None
