#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

class Login():

    locators = {
        "login.username": "username",
        "login.password": "password",
        "login.submit": "commit",
        "login.gravatar": "span.gravatar-span",
        "login.user": "span.ng-binding",
        "login.error": "div.jnotify-message",
        "login.interstitial": "interstitial",
        "login.logout": "logout",
        }

    def __init__(self, browser):
        self.browser = browser

    def login(self, username, password, organization=None):

        organization = organization or 'ACME_Corporation'

        if self.browser.is_element_present_by_id(self.locators["login.username"]):
            self.browser.fill(self.locators["login.username"], username)
            self.browser.fill(self.locators["login.password"], password)
            self.browser.find_by_name(self.locators["login.submit"]).click()

            if self.browser.is_element_present_by_css(self.locators["login.error"]):
                return

            if self.browser.is_element_present_by_id(self.locators["login.interstitial"]):
                self.browser.find_link_by_partial_text(organization).click()

    def logout(self):

        if self.browser.is_element_present_by_css(self.locators["login.gravatar"]):
            self.browser.find_by_css(self.locators["login.gravatar"]).click()
            self.browser.find_link_by_partial_href(self.locators["login.logout"]).click()

    def is_logged(self, username):
        # Headpin?
        if self.browser.is_element_present_by_css(self.locators["login.gravatar"]):
            return True
        # Katello?
        elif self.browser.is_element_present_by_css(self.locators["login.user"]):
            return True
        else:
            return False
