#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0

from robot.utils import asserts
import time

class Login(object):

    ROBOT_LIBRARY_SCOPE = 'TEST_CASE'
    __version__ = '0.1'


    def __init__(self):
        print "hi"

    def start_browser(self, login_url, browser):

        # Create a new instance of the Firefox driver
        self.driver = webdriver.Firefox()

        # go to the google home page
        self.driver.get(login_url)

    def login_user(self, username, password):
        # find the element that's name attribute is 'username'
        usernameElement = self.driver.find_element_by_name("username")
        # type in the search
        usernameElement.send_keys(username)
        # find the element that's name attribute is 'password'
        passwordElement = self.driver.find_element_by_name("password")
        # find the submit button
        inputElement = self.driver.find_element_by_name("Log In")
        # submit the form
        inputElement.click()
