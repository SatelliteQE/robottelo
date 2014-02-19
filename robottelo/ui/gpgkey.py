# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements GPG keys UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators


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
            else:
                self.wait_until_element(locators["gpgkey.content"]).click()
                self.find_element(locators
                                  ["gpgkey.content"]
                                  ).send_keys(key_content)
            self.wait_until_element(common_locators["create"]).click()
            self.wait_for_ajax()
        else:
            raise Exception(
                "Could not create new gpg key '%s'" % name)

    def search(self, element_name):
        """
        Uses the search box to locate an element from a list of elements.
        """

        element = None
        strategy = locators["gpgkey.key_name"][0]
        value = locators["gpg.key_name"][1]
        searchbox = self.wait_until_element(common_locators["kt_search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(element_name)
            self.wait_for_ajax()
            self.find_element(common_locators["kt_search_button"]).click()
            element = self.wait_until_element((strategy, value % element_name))
            return element

    def delete(self, name, really):
        """
        Deletes an existing gpg key.
        """

        strategy = locators["gpgkey.key_name"][0]
        value = locators["gpgkey.key_name"][1]
        searchbox = self.wait_until_element(common_locators["kt_search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(name)
            self.wait_for_ajax()
            self.find_element(common_locators["kt_search_button"]).click()
            element = self.wait_until_element((strategy, value % name))
            if element:
                element.click()
                self.wait_until_element(locators["gpgkey.remove"]).click()
                if really:
                    self.wait_until_element(common_locators
                                            ["confirm_remove"]
                                            ).click()
                else:
                    raise Exception(
                        "Could not delete the selected key '%s'." % name)
