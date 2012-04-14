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
        self.driver.close()

    def login_user(self, username, password):
        # find the element that's name attribute is 'username'
        usernameElement = find_element(self.driver, "username", By.NAME)
        # type in the username
        usernameElement.send_keys(username)
        # find the element that's name attribute is 'password'
        passwordElement = find_element(self.driver, "password", By.NAME)
        # type in the password
        passwordElement.send_keys(password)
        # find the submit button
        inputElement = find_element(self.driver, "commit", By.NAME)
        # submit the form
        inputElement.click()

    def success_login(self):

        success = wait_until_element(self.driver, "div.jnotify-notification.jnotify-notification-success", By.CSS_SELECTOR)
        asserts.assert_true(success.is_displayed(), "Failed to login with valid credentials!")

    def failed_login(self):

        failed = wait_until_element(self.driver, "div.jnotify-notification.jnotify-notification-error", By.CSS_SELECTOR)
        asserts.assert_true(failed.is_displayed(), "Was able to login with invalid credentials!")
