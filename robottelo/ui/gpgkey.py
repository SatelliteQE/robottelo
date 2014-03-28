# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements GPG keys UI
"""

from robottelo.common.helpers import sleep_for_seconds
from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator


class GPGKey(Base):
    """
    Manipulates GPG keys from UI
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, name, upload_key=False, key_path=None, key_content=None):
        """
        Creates a gpg key from UI.
        """
        self.wait_until_element(locators["gpgkey.new"]).click()

        if self.wait_until_element(common_locators["name"]):
            self.find_element(common_locators
                              ["name"]).send_keys(name)
            if upload_key:
                self.wait_until_element(locators["gpgkey.upload"]).click()
                self.find_element(locators
                                  ["gpgkey.file_path"]
                                  ).send_keys(key_path)
            elif key_content:
                self.find_element(locators["gpgkey.content"]).click()
                self.find_element(locators
                                  ["gpgkey.content"]
                                  ).send_keys(key_content)
            else:
                raise Exception(
                    "Could not create new gpgkey '%s' without contents" % name)
            self.wait_until_element(common_locators["create"]).click()
            sleep_for_seconds(2)
        else:
            raise Exception(
                "Could not create new gpg key '%s'" % name)

    def search(self, element_name):
        """
        Uses the search box to locate an element from a list of elements.
        """

        element = None
        strategy = locators["gpgkey.key_name"][0]
        value = locators["gpgkey.key_name"][1]
        searchbox = self.wait_until_element(common_locators["kt_search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys('"' + element_name + '"')
            sleep_for_seconds(5)
            self.find_element(common_locators["kt_search_button"]).click()
            element = self.wait_until_element((strategy, value % element_name))
            return element

    def delete(self, name, really):
        """
        Deletes an existing gpg key.
        """
        element = self.search(name)

        if element:
            element.click()
            sleep_for_seconds(3)
            self.wait_until_element(locators["gpgkey.remove"]).click()
            sleep_for_seconds(2)
            if really:
                self.wait_until_element(common_locators["confirm_remove"]
                                        ).click()
            else:
                raise Exception(
                    "Could not delete the selected key '%s'." % name)

    def update(self, name, new_name=None, new_key=None):
        """
        Updates an existing GPG key
        """

        element = self.search(name)

        if element:
            element.click()
            sleep_for_seconds(5)
            if new_name:
                self.edit_entity("gpgkey.edit_name", "gpgkey.edit_name_text",
                                 new_name, "gpgkey.save_name")
                self.wait_for_ajax()
            if new_key:
                self.wait_until_element(locators["gpgkey.file_path"]
                                        ).send_keys(new_key)
                self.wait_until_element(locators
                                        ["gpgkey.upload_button"]).click()
        else:
            raise Exception("Could not update the gpg key '%s'" % name)

    def assert_product_repo(self, key_name, product):
        """
        To validate product and repo association with gpg keys

        Here product is a boolean variable
        when product = True; validation assert product tab
        otherwise assert repo tab
        """

        element = self.search(key_name)

        if element:
            element.click()
            self.wait_for_ajax()
            if product:
                self.find_element(tab_locators
                                  ["gpgkey.tab_products"]).click()
            else:
                self.find_element(tab_locators
                                  ["gpgkey.tab_repos"]).click()
            if self.wait_until_element(locators["gpgkey.product_repo"]):
                element = self.find_element(locators
                                            ["gpgkey.product_repo"]
                                            ).get_attribute('innerHTML')
                string = element.strip(' \t\n\r')
                return string
        else:
            raise Exception(
                "Couldn't search the given gpg key '%s'" % key_name)

    def assert_key_from_product(self, name, product, repo=None):
        """
        Assert the key association after deletion from product tab
        """

        nav = Navigator(self.browser)
        nav.go_to_products()
        prd_element = self.search_entity(product, locators["prd.select"],
                                         katello=True)
        if prd_element:
            prd_element.click()
            sleep_for_seconds(3)
            if repo is not None:
                self.wait_until_element(tab_locators["prd.tab_repos"]).click()
                strategy = locators["repo.select"][0]
                value = locators["repo.select"][1]
                self.wait_until_element((strategy, value % repo)).click()
                sleep_for_seconds(3)
                element = self.wait_until_element(locators
                                                  ["repo.gpg_key"]
                                                  ).get_attribute('innerHTML')
                if element == '':
                    return None
                else:
                    raise Exception(
                        "GPGKey '%s' is still assoc with selected repo" % name)
            else:
                self.wait_until_element(tab_locators
                                        ["prd.tab_details"]).click()
                element = self.find_element(locators
                                            ["prd.gpg_key"]
                                            ).get_attribute('innerHTML')
                if element == '':
                    return None
                else:
                    raise Exception(
                        "GPG key '%s' is still assoc with product" % name)
        else:
            raise Exception(
                "Couldn't find the product '%s'" % product)
