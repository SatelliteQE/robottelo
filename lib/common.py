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
    """

    try:
        remote_file = urlopen(manifest_url)
    except Exception, e:
        asserts.assert_fail("Failed to download the manifest file at %s." % manifest_url)

    (fd, filename) = tempfile.mkstemp()
    f = os.fdopen(fd, "w")

    for line in remote_file.readlines():
        f.write(line)
    f.close()

    return filename


def find_element(drv, element, method=By.NAME):

    """
    Wrapper around Selenium's WebDriver that allows you to search for an element in
    the web page.
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
