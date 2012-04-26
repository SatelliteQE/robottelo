#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from login import login
from common import find_element, wait_until_element
from selenium import webdriver
from selenium.webdriver.common.by import By
from robot.api import logger
from robot.utils import asserts


class administration(login):

    __version__ = '0.1'

    # Locators

    def __init__(self, base_url, browser=None):
        login.__init__(self, base_url, browser)

    def create_role(self, role_name):
        """
        Creates a new role.
        """

        # go to the url
        self.driver.get(self.base_url)

        # Administration tab
        admin_tab = wait_until_element(drv, "//li[@id='admin']/a", By.XPATH)
        asserts.fail_if_none(admin_tab, "Could not fine the Administration tab.")
        admin_tab.click()

        # Roles submenu
        roles_link = wait_until_element(drv, "//li[@id='roles']/a", By.XPATH)
        asserts.fail_if_none(roles_link, "Could not find the Roles menu.")
        roles_link.click()

        # New Role link
        new_role_link = wait_until_element(drv, "//div[@id='list-title']/header/a", By.XPATH)
        asserts.fail_if_none(new_role_link, "Could not find the New Role link.")
        new_role_link.click()

        # Role name field
        role_name_field = wait_until_element(drv, "//form[@id='new_role']/fieldset/div[2]/input", By.XPATH)
        asserts.fail_if_none(role_name_field, "Could not find the role name field.")
        role_name.send_keys(role_name)

        # Submit button
        submit_button = wait_until_element(drv, "//form[@id='new_role']/div[2]/div/input", By.XPATH)
        asserts.fail_if_none(submit_button, "Could not find submiot button")
        submit_button.click()

        # Check if new Role exists in list
        role = wait_until_element(drv, "//span[contains(., '%s')]" % role_name, By.XPATH)
        asserts.fail_if_none(role, "Was not able to locate the newly created role.")
