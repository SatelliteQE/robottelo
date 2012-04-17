#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from common import find_element, wait_until_element
from selenium import webdriver
from selenium.webdriver.common.by import By
from robot.api import logger
from robot.utils import asserts


class login(object):

    ROBOT_LIBRARY_SCOPE = 'TEST_CASE'
    __version__ = '0.1'


    def start_browser(self, login_url, browser):

        if browser == "firefox":
            # Create a new instance of the Firefox driver
            self.driver = webdriver.Firefox()
        else:
            # Create a new instance of the Chrome driver
            self.driver = webdriver.Chrome()

        # TODO: verify the url was successfully loaded.
        # go to the url
        self.driver.get(login_url)


    def stop_browser(self):
        # Quit the browser.
        self.driver.quit()

    def login_user(self, username, password):
        # find the element that's name attribute is 'username'
        usernameElement = wait_until_element(self.driver, "username", By.ID)
        asserts.assert_true(usernameElement.is_displayed())
        # type in the username
        usernameElement.clear()
        usernameElement.send_keys(username)
        # find the element that's name attribute is 'password'
        passwordElement = find_element(self.driver, "password", By.ID)
        asserts.assert_true(passwordElement.is_displayed())
        # type in the password
        passwordElement.send_keys(password)
        # find the submit button
        inputElement = find_element(self.driver, "commit", By.NAME)
        # submit the form
        inputElement.click()


    def logout_user(self):
        logout_link = wait_until_element(self.driver, "Logout", By.LINK_TEXT)
        asserts.fail_if_none(logout_link)
        asserts.assert_true(logout_link.is_enabled())
        asserts.assert_true(logout_link.is_displayed())
        # Log out
        logout_link.click()

        # find the 'username' field in the login form.
        usernameElement = wait_until_element(self.driver, "username", By.NAME)
        asserts.fail_if_none(usernameElement)
        asserts.assert_true(usernameElement.is_displayed())


    def user_logged_in(self):

        is_logged = wait_until_element(self.driver, "li.hello", By.CSS_SELECTOR)

        asserts.fail_if_none(is_logged)
        asserts.assert_true(is_logged.is_displayed(), "Failed to login with valid credentials!")

    def user_not_logged_in(self):

        not_logged = wait_until_element(self.driver, "li.hello", By.CSS_SELECTOR)
        asserts.fail_unless_none(not_logged, "Was able to login with invalid credentials!")
