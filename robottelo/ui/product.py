#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements Product UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from time import sleep


class Product(Base):

    def __init__(self, browser):
        self.browser = browser

    def create(self, name, label=None, provider=None, provider_name=None,
               gpg_key=None, description='Automated'):
        self.wait_until_element(locators["product.new"]).click()

        if self.wait_until_element(locators["product.name"]):
            self.find_element(locators["product.name"]).send_keys(name)

            if label:
                if self.wait_until_element(locators["product.label"]):
                    self.find_element(locators["product.label"]).send_keys(label)

            if self.wait_until_element(locators["product.description"]):
                self.find_element(locators["product.description"]).send_keys(description)

            if provider_name:
                self.wait_until_element(locators["provider.new"]).click()
                sleep(5)
                if self.wait_until_element(locators["provider.name"]):
                    self.find_element(locators["provider.name"]).send_keys(provider_name)
                self.find_element(locators["provider.save"]).click()

            sleep(5)
            self.find_element(locators["product.save"]).click()

    def search(self, name):
        # Make sure the product is present

        pass

    def delete(self, name, really=False):
        pass

    def update(self):
        pass
