#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from common import find_element, wait_until_element
from selenium import webdriver
from selenium.webdriver.common.by import By
from robot.api import logger
from robot.utils import asserts


class login(object):

    ROBOT_LIBRARY_SCOPE = 'TEST_CASE'
    __version__ = '0.1'


    # Locators
    _LOGIN_USERNAME = ("//form[@id='login_form']/fieldset/input")
    _LOGIN_PASSWORD = ("//form[@id='login_form']/fieldset[2]/input")
    _LOGIN_SUBMIT = ("//form[@id='login_form']/input")
    _HEADER_USERNAME = ("//div[@id='head']/header/div[2]/ul/li/a/strong")
    _HEADER_LOGOUT = ("//a[contains(text(),'Logout')]")


    def __init__(self, base_url, browser=None):

        self.browser = browser
        self.base = Base()
        self.base.base_url = base_url


    def login_user(self, username, password, org=None):
        """
        Login as user with provided credentials.
        """

        if self.browser == "firefox":
            # Create a new instance of the Firefox driver
            self.base.driver = webdriver.Firefox()
        elif self.browser == "remote":
            # Create a new instance of the Chrome driver
            self.base.driver = webdriver.Remote("http://localhost:4444/wd/hub", webdriver.DesiredCapabilities.HTMLUNITWITHJS)
        else:
            # Sorry, we can't help you right now.
            asserts.fail("Support for Firefox or Remote only!")

        # go to the url
        self.base.driver.get(self.base.base_url)

        # find the element that's name attribute is 'username'
        usernameElement = wait_until_element(self.base.driver, self._LOGIN_USERNAME, By.XPATH)
        asserts.fail_if_none(usernameElement, "Failed to locate the Username field")
        # type in the username
        usernameElement.send_keys(username)
        # find the element that's name attribute is 'password'
        passwordElement = wait_until_element(self.base.driver, self._LOGIN_PASSWORD, By.XPATH)
        asserts.fail_if_none(passwordElement, "Failed to locate the Password field")
        # type in the password
        passwordElement.send_keys(password)
        # find the submit button
        inputElement = find_element(self.base.driver, self._LOGIN_SUBMIT, By.XPATH)
        asserts.fail_if_none(inputElement, "Failed to locate the Login button")
        # submit the form
        inputElement.click()

        # If an organization was passed, try to select it
        if org is not None:
            #org_filter =  wait_until_element(self.base.driver, ("//div[@id='orgbox']/div"), By.XPATH)
            org_filter =  wait_until_element(self.base.driver, ("//div[@id='orgbox']/div/div[@class='jspPane']"), By.XPATH)
            asserts.fail_if_none(org_filter, "Organization filter was not specified.")

            # Type the org name into filter box
            filter_box = wait_until_element(self.base.driver, ("//input[@id='orgfilter_input']"), By.XPATH)
            asserts.fail_if_none(filter_box, "Could not locate the filter box field.")
            filter_box.send_keys(org)

            # Select the organization from list and click it
            filtered_org = wait_until_element(self.base.driver, ("//a[contains(text(),'%s')]" % org), By.XPATH)
            asserts.fail_if_none(filtered_org, "Could not select organization %s." % org)
            filtered_org.click()

            # Assert that we've landed in the org dashboard page
            selected_org = wait_until_element(self.base.driver, ("//a[@id='switcherButton']"), By.XPATH)
            asserts.fail_if_none(selected_org, "Could not find the org selector widget.")
            asserts.assert_equals(org, selected_org.text, "Could not open the dashboard for organization %s" % org)


    def logout_user(self):
        """
        Logs out the user.
        """

        #TODO: WebDriver is not honoring the click event for the URL!
        logout_link = wait_until_element(self.base.driver, self._HEADER_LOGOUT, By.XPATH)
        asserts.fail_if_none(logout_link)
        asserts.assert_true(logout_link.is_displayed())
        # Log out
        logout_link.click()

        # find the 'username' field in the login form.
        usernameElement = wait_until_element(self.base.driver, self._LOGIN_USERNAME, By.XPATH)
        asserts.fail_if_none(usernameElement)
        asserts.assert_true(usernameElement.is_displayed())


    def user_logged_in(self, username):
        """
        Checks if the user is logged.
        """

        # Verify that the username is displayed in the web page
        is_logged = wait_until_element(self.base.driver, "//a[contains(., '%s')]" % username, By.XPATH)
        asserts.fail_if_none(is_logged, "User is not logged in.")
        asserts.assert_true(is_logged.is_displayed(), "Failed to login with valid credentials!")


    def user_not_logged_in(self, username):
        """
        Checks if the user is not logged.
        """

        not_logged = wait_until_element(self.base.driver, "//a[contains(., '%s')]" % username, By.XPATH)
        asserts.fail_unless_none(not_logged, "Should not be able to login with invalid credentials!")

    def stop_browser(self):
        """
        Closes the web browser window (if any) and quits.
        """

        # Quit the browser.
        self.base.driver.quit()
