#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from login import login
from common import find_element, wait_until_element
from selenium import webdriver
from selenium.webdriver.common.by import By
from robot.api import logger
from robot.utils import asserts


class org(login):

    ROBOT_LIBRARY_SCOPE = 'TEST_CASE'
    __version__ = '0.1'


    # Locators
    _HEADER_ORGANIZATIONS = "//li[@id='organizations']/a"
    _NEW_ORG_LINK = "//div[@id='list-title']/header/a"
    _ORG_NAME = "//form[@id='new_organization']/fieldset/div[2]/input"
    _ORG_SUBMIT = "//form[@id='new_organization']/div[2]/div/input"
    _NEW_ORG = "//div[@id='organization_Seattle']/div"


    def __init__(self, base_url, browser=None):
        login.__init__(self, base_url, browser)


    def create_org(self, name):
        """
        Creates a new organization with the provided name.
        """

        # go to the url
        self.driver.get(self.base_url)

        organizations_tab = wait_until_element(self.driver, self._HEADER_ORGANIZATIONS, By.XPATH)
        asserts.fail_if_none(organizations_tab, "Could not find the Organizations tab.")
        organizations_tab.click()
