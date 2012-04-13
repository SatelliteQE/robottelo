#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0

from robot.utils import asserts
import time

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

        # go to the google home page
        self.driver.get(login_url)


    def stop_browser(self):
        # Quit the browser.
        self.driver.quit()

    def login_user(self, username, password):
        # find the element that's name attribute is 'username'
        usernameElement = self.driver.find_element_by_name("username")
        # type in the username
        usernameElement.send_keys(username)
        # find the element that's name attribute is 'password'
        passwordElement = self.driver.find_element_by_name("password")
        # type in the password
        passwordElement.send_keys(password)
        # find the submit button
        inputElement = self.driver.find_element_by_name("commit")
        # submit the form
        inputElement.click()

    def success_login(self):
        success = self.driver.find_element_by_css("div.jnotify-notification.jnotify-notification-success")

