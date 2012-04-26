#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from login import login
from common import find_element, wait_until_element
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from robot.api import logger
from robot.utils import asserts


class administration(login):

    __version__ = '0.1'

    # Locators

    def __init__(self, base_url, browser=None):
        login.__init__(self, base_url, browser)

    def go_to_administration_tab(self):
        # Administration tab
        admin_tab = wait_until_element(self.driver, "//li[@id='admin']/a", By.XPATH)
        asserts.fail_if_none(admin_tab, "Could not fine the Administration tab.")
        admin_tab.click()


    def create_role(self, role_name):
        """
        Creates a new role.
        """

        # go to the url
        self.driver.get(self.base_url)

        # Select the Administration tab
        self.go_to_administration_tab()

        # Roles submenu
        roles_link = wait_until_element(self.driver, "//li[@id='roles']/a", By.XPATH)
        asserts.fail_if_none(roles_link, "Could not find the Roles menu.")
        roles_link.click()

        # New Role link
        new_role_link = wait_until_element(self.driver, "//div[@id='list-title']/header/a", By.XPATH)
        asserts.fail_if_none(new_role_link, "Could not find the New Role link.")
        new_role_link.click()

        # Role name field
        role_name_field = wait_until_element(self.driver, "//form[@id='new_role']/fieldset/div[2]/input", By.XPATH)
        asserts.fail_if_none(role_name_field, "Could not find the role name field.")
        role_name.send_keys(role_name)

        # Submit button
        submit_button = wait_until_element(self.driver, "//form[@id='new_role']/div[2]/div/input", By.XPATH)
        asserts.fail_if_none(submit_button, "Could not find submiot button")
        submit_button.click()

        # Check if new Role exists in list
        role = wait_until_element(self.driver, "//span[contains(., '%s')]" % role_name, By.XPATH)
        asserts.fail_if_none(role, "Was not able to locate the newly created role.")


    def add_permission_to_role(self, role_name, permission_level, permission_type, verb, permission_name):
        """
        Adds a permission to an existing role.
        """

        # go to the url
        self.driver.get(self.base_url)

        # Select the Administration tab
        self.go_to_administration_tab()

        # Roles submenu
        roles_link = wait_until_element(self.driver, "//li[@id='roles']/a", By.XPATH)
        asserts.fail_if_none(roles_link, "Could not find the Roles menu.")
        roles_link.click()

        # Find the role
        role = wait_until_element(self.driver, "//span[contains(., '%s')]" % role_name, By.XPATH)
        asserts.fail_if_none(role, "Could not find existing role with name '%s'." % role_name)
        role.click()

        # Permissions section
        permissions = wait_until_element(self.driver, "//div[@id='role_permissions']/span", By.XPATH)
        permissions.click()

        # Select the permission type
        selected_permission = wait_until_element(self.driver, "//div[@id='%s']/span" % permission_level, By.XPATH)
        selected_permission.click()

        # Add new permission button
        add_button = wait_until_element(self.driver, "//div[@id='add_permission']/span[2]", By.XPATH)
        add_button.click()

        # Select the permission type
        permissions_list = wait_until_element(self.driver, "//div[@id='resource_type_container']/select", By.XPATH)
        Select(permissions_list).select_by_visible_text("%s" % permission_type)

        next_button = wait_until_element(self.driver, "//div[@id='permission_button_bar']/div[2]", By.XPATH)
        next_button.click()

        # All Verbs
        verbs = wait_until_element(self.driver, "//select[@id='verbs']", By.XPATH)

        # Add provided verb
        Select(verbs).select_by_visible_text("%s" % verb)

        next_button = wait_until_element(self.driver, "//div[@id='permission_button_bar']/div[2]", By.XPATH)
        next_button.click()

        # New permission name
        permission_name = wait_until_element(self.driver, "//div[@id='details_container']/input", By.XPATH)
        permission_name.send_keys("%s" % permission_name)

        # Save
        save_button = wait_until_element(self.driver, "//div[@id='permission_button_bar']/div[3]", By.XPATH)
        save_button.click()

        # Check that the newly created permission shows up
        new_permission = wait_until_element(self.driver, "//span[contains(., '%s')]" % permission_name, By.XPATH)
        asserts.fail_if_none(new_permission, "Permission '%s' was not created." % permission_name)

