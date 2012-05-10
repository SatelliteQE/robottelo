#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from common import *
from locators import *

from robot.api import logger
from robot.utils import asserts

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


class administration(object):
    """
    Perform administrative tasks, such as creating/editing/maintaining users,
    roles, organizations, etc.
    """
    __version__ = '0.1'


    def __init__(self):
        self.base = Base()

    def go_to_administration_tab(self):
        """
        Takes user to the Administration tab.
        """

        return select_tab(self.base.driver, ADMIN_TAB)


    def create_user(self, username, password, email, org=None):
        """
        Creates a new user.
        """

        # go to the url
        self.base.driver.get(self.base.base_url)

        # Select the Administration tab
        asserts.assert_true(self.go_to_administration_tab(), "Could not select the Administration tab.")

        # Users submenu
        users_link = wait_until_element(self.base.driver, USERS_LINK, By.XPATH)
        asserts.fail_if_none(users_link, "Could not find the Users menu.")
        users_link.click()

        # Check if new User exists in list
        user = wait_until_element(self.base.driver, USER % username, By.XPATH)
        asserts.fail_unless_none(user, "A user with this name already exists.")

        # New User link
        new_user_link = wait_until_element(self.base.driver, NEW_USER_LINK, By.XPATH)
        asserts.fail_if_none(new_user_link, "Could not find the New User link.")
        new_user_link.click()

        # Fill out the form
        # Username
        user_name_field = wait_until_element(self.base.driver, USER_NAME_FIELD, By.XPATH)
        asserts.fail_if_none(user_name_field, "Could not find the username field.")
        user_name_field.send_keys(username)
        # Password
        password_field = wait_until_element(self.base.driver, USER_PASSWORD_FIELD, By.XPATH)
        asserts.fail_if_none(password_field, "Could not find the password field.")
        password_field.send_keys(password)
        # Password confirmation
        password_confirmation_field = wait_until_element(self.base.driver, USER_PASSWORD_CONFIRMATION_FIELD, By.XPATH)
        asserts.fail_if_none(password_confirmation_field, "Could not find the password confirmation field.")
        password_confirmation_field.send_keys(password)
        # Email
        email_field = wait_until_element(self.base.driver, USER_EMAIL_FIELD, By.XPATH)
        asserts.fail_if_none(email_field, "Could not find the email field.")
        email_field.send_keys(email)

        if org:
            orgs_list = wait_until_element(self.base.driver, ORGS_LIST, By.XPATH)
            asserts.fail_if_none(orgs_list, "Could not the Organizations list.")
            Select(orgs_list).select_by_visible_text(org)

        # Submit
        submit_button = wait_until_element(self.base.driver, "//form[@id='new_user']/div[4]/div/input", By.XPATH)
        asserts.fail_if_none(submit_button, "Could not find the Submit button.")
        submit_button.click()

        # Users submenu again
        users_link = wait_until_element(self.base.driver, USERS_LINK, By.XPATH)
        asserts.fail_if_none(users_link, "Could not find the Users menu.")
        users_link.click()

        # Check if new User exists in list
        user = wait_until_element(self.base.driver, USER % username, By.XPATH)
        asserts.fail_if_none(user, "Was not able to locate the newly created user.")


    def delete_user(self, username):
        """
        Deletes an existing user.
        """

        # go to the url
        self.base.driver.get(self.base.base_url)

        # Select the Administration tab
        asserts.assert_true(self.go_to_administration_tab(), "Could not select the Administration tab.")

        # Users submenu
        users_link = wait_until_element(self.base.driver, USERS_LINK, By.XPATH)
        asserts.fail_if_none(users_link, "Could not find the Users menu.")
        users_link.click()

        # Check if User exists in list
        user = wait_until_element(self.base.driver, USER % username, By.XPATH)
        asserts.fail_if_none(user, "Was not able to locate the user.")
        user.click()

        # Remove user link
        remove_user_link = wait_until_element(self.base.driver, USER_REMOVE_LINK, By.XPATH)
        asserts.fail_if_none(remove_user_link, "Could not find the Remove User link.")
        remove_user_link.click()

        # Find the Yes button
        yes_button = wait_until_element(self.base.driver, YES_BUTTON, By.XPATH)
        asserts.fail_if_none(yes_button, "Could not find the Yes button to remove role.")
        yes_button.click()

        # Users submenu again
        users_link = wait_until_element(self.base.driver, USERS_LINK, By.XPATH)
        asserts.fail_if_none(users_link, "Could not find the Users menu.")
        users_link.click()

        # Check if new User exists in list
        user = wait_until_element(self.base.driver, USER % username, By.XPATH)
        asserts.fail_unless_none(user, "Could not delete user named '%s'." % username)


    def add_role_to_user(self, role_name, username):
        """
        Adds an existing role to an existing user.
        """

        # go to the url
        self.base.driver.get(self.base.base_url)

        # Select the Administration tab
        asserts.assert_true(self.go_to_administration_tab(), "Could not select the Administration tab.")

        # Users submenu
        users_link = wait_until_element(self.base.driver, USERS_LINK, By.XPATH)
        asserts.fail_if_none(users_link, "Could not find the Users menu.")
        users_link.click()

        # Check if User exists in list
        user = wait_until_element(self.base.driver, USER % username, By.XPATH)
        asserts.fail_if_none(user, "Was not able to locate the user.")
        user.click()

        # Select the user's Role section
        roles_link = wait_until_element(self.base.driver, USER_ROLES_LINK, By.XPATH)
        asserts.fail_if_none(roles_link, "Could not find the Roles link for user.")
        roles_link.click()


        # Add role to user
        role = wait_until_element(self.base.driver, USER_ADD_ROLE % role_name, By.XPATH)
        asserts.fail_if_none(role, "Could not locate the '%s' role. Maybe it was already added to the user." % role_name)
        role.click()

        # Save
        submit_button = wait_until_element(self.base.driver, USER_ROLE_SAVE_BUTTON, By.XPATH)
        asserts.fail_if_none(submit_button, "Could not locate the Submit button.")
        submit_button.click()

        # Role should not be available to add anymore
        #role = wait_until_element(self.base.driver, "//li[contains(@title, '%s')]/a/span[contains(@class, 'ui-icon-minus')]" % role_name, By.XPATH)
        #asserts.fail_unless_none(role, "Role '%s' should not be available for adding anymore." % role_name)


    def remove_role_from_user(self, role_name, username):
        """
        Removes an existing role from an existing user.
        """

        # go to the url
        self.base.driver.get(self.base.base_url)

        # Select the Administration tab
        asserts.assert_true(self.go_to_administration_tab(), "Could not select the Administration tab.")

        # Users submenu
        users_link = wait_until_element(self.base.driver, USERS_LINK, By.XPATH)
        asserts.fail_if_none(users_link, "Could not find the Users menu.")
        users_link.click()

        # Check if User exists in list
        user = wait_until_element(self.base.driver, USER % username, By.XPATH)
        asserts.fail_if_none(user, "Was not able to locate the user.")
        user.click()

        # Select the user's Role section
        roles_link = wait_until_element(self.base.driver, USER_ROLES_LINK, By.XPATH)
        asserts.fail_if_none(roles_link, "Could not find the Roles link for user.")
        roles_link.click()

        # Remove role from user
        role = wait_until_element(self.base.driver, USER_REMOVE_ROLE % role_name, By.XPATH)
        asserts.fail_if_none(role, "Could not locate the '%s' role. Maybe it was already removed from the user." % role_name)
        role.click()

        # Save
        submit_button = wait_until_element(self.base.driver, USER_ROLE_SAVE_BUTTON, By.XPATH)
        asserts.fail_if_none(submit_button, "Could not locate the Submit button.")
        submit_button.click()

        # Role should not be available to add anymore
        #role = wait_until_element(self.base.driver, "//li[contains(@title, '%s')]/a/span[contains(@class, 'ui-icon-plus')]" % role_name, By.XPATH)
        #asserts.fail_unless_none(role, "Role '%s' should not be available for removal anymore." % role_name)


    def create_role(self, role_name):
        """
        Creates a new role.
        """

        # go to the url
        self.base.driver.get(self.base.base_url)

        # Select the Administration tab
        asserts.assert_true(self.go_to_administration_tab(), "Could not select the Administration tab.")

        # Roles submenu
        roles_link = wait_until_element(self.base.driver, ROLES_LINK, By.XPATH)
        asserts.fail_if_none(roles_link, "Could not find the Roles menu.")
        roles_link.click()

        # Check if new Role exists in list
        role = wait_until_element(self.base.driver, ROLE % role_name, By.XPATH)
        asserts.fail_unless_none(role, "A role with this name already exists.")

        # New Role link
        new_role_link = wait_until_element(self.base.driver, NEW_ROLE_LINK, By.XPATH)
        asserts.fail_if_none(new_role_link, "Could not find the New Role link.")
        new_role_link.click()

        # Role name field
        role_name_field = wait_until_element(self.base.driver, ROLE_NAME_FIELD, By.XPATH)
        asserts.fail_if_none(role_name_field, "Could not find the role name field.")
        role_name_field.send_keys(role_name)

        # Submit button
        submit_button = wait_until_element(self.base.driver, ROLE_SAVE_BUTTON, By.XPATH)
        asserts.fail_if_none(submit_button, "Could not find submiot button")
        submit_button.click()

        # Check if new Role exists in list
        role = wait_until_element(self.base.driver, ROLE % role_name, By.XPATH)
        asserts.fail_if_none(role, "Was not able to locate the newly created role.")


    def delete_role(self, role_name):
        """
        Deletes an existing Role.
        """

        # go to the url
        self.base.driver.get(self.base.base_url)

        # Select the Administration tab
        asserts.assert_true(self.go_to_administration_tab(), "Could not select the Administration tab.")

        # Roles submenu
        roles_link = wait_until_element(self.base.driver, ROLES_LINK, By.XPATH)
        asserts.fail_if_none(roles_link, "Could not find the Roles menu.")
        roles_link.click()

        # Find the role
        role = wait_until_element(self.base.driver, ROLE % role_name, By.XPATH)
        asserts.fail_if_none(role, "Could not find existing role with name '%s'." % role_name)
        role.click()

        # Find the remove button
        remove_button = wait_until_element(self.base.driver, ROLE_REMOVE_BUTTON, By.XPATH)
        asserts.fail_if_none(remove_button, "Did not find the remove role button.")
        remove_button.click()

        # Find the Yes button
        yes_button = wait_until_element(self.base.driver, YES_BUTTON, By.XPATH)
        asserts.fail_if_none(yes_button, "Could not find the Yes button to remove role.")
        yes_button.click()

        # Roles submenu
        roles_link = wait_until_element(self.base.driver, ROLES_LINK, By.XPATH)
        asserts.fail_if_none(roles_link, "Could not find the Roles menu.")
        roles_link.click()

        # Look for the role again
        role = wait_until_element(self.base.driver, ROLE % role_name, By.XPATH)
        asserts.fail_unless_none(role, "Could not remove existing role with name '%s'." % role_name)


    def add_permission_to_role(self, role_name, permission_level, permission_type, verb, permission_name):
        """
        Adds a permission to an existing role.
        """

        # go to the url
        self.base.driver.get(self.base.base_url)

        # Select the Administration tab
        asserts.assert_true(self.go_to_administration_tab(), "Could not select the Administration tab.")

        # Roles submenu
        roles_link = wait_until_element(self.base.driver, ROLES_LINK, By.XPATH)
        asserts.fail_if_none(roles_link, "Could not find the Roles menu.")
        roles_link.click()

        # Find the role
        role = wait_until_element(self.base.driver, ROLE % role_name, By.XPATH)
        asserts.fail_if_none(role, "Could not find existing role with name '%s'." % role_name)
        role.click()

        # Permissions section
        permissions = wait_until_element(self.base.driver, ROLE_PERMISSIONS, By.XPATH)
        permissions.click()

        # Select the permission type
        selected_permission = wait_until_element(self.base.driver, ROLE_PERMISSION_TYPE % permission_level, By.XPATH)
        selected_permission.click()

        # Add new permission button
        add_button = wait_until_element(self.base.driver, ROLE_PERMISSION_SAVE_BUTTON, By.XPATH)
        add_button.click()

        # Select the permission type
        permissions_list = wait_until_element(self.base.driver, PERMISSION_TYPES_LIST, By.XPATH)
        Select(permissions_list).select_by_visible_text("%s" % permission_type)

        next_button = wait_until_element(self.base.driver, PERMISSION_TYPES_NEXT_BUTTON, By.XPATH)
        next_button.click()

        # All Verbs
        verbs = wait_until_element(self.base.driver, PERMISSION_VERBS_LIST, By.XPATH)
        asserts.fail_if_none(verbs, "Could not find a list of the available verbs.")

        # Add provided verb
        Select(verbs).select_by_visible_text("%s" % verb)

        next_button = wait_until_element(self.base.driver, PERMISSION_TYPES_NEXT_BUTTON, By.XPATH)
        next_button.click()

        # New permission name
        permission_name_field = wait_until_element(self.base.driver, PERMISSION_NAME_FIELD, By.XPATH)
        permission_name_field.send_keys("%s" % permission_name)

        # Save
        save_button = wait_until_element(self.base.driver, PERMISSION_SAVE_BUTTON, By.XPATH)
        save_button.click()

        # Check that the newly created permission shows up
        new_permission = wait_until_element(self.base.driver, PERMISSION % permission_name, By.XPATH)
        asserts.fail_if_none(new_permission, "Permission '%s' was not created." % permission_name)
