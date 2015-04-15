# -*- encoding: utf-8 -*-
"""Implements GPG keys UI."""

from robottelo.common.helpers import escape_search
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class GPGKey(Base):
    """Manipulates GPG keys from UI."""

    def create(self, name, upload_key=False, key_path=None, key_content=None):
        """Creates a gpg key from UI."""
        self.wait_until_element(locators["gpgkey.new"]).click()

        if self.wait_until_element(common_locators["name"]):
            self.find_element(
                common_locators["name"]).send_keys(name)
            if upload_key:
                self.wait_until_element(locators["gpgkey.upload"]).click()
                self.find_element(
                    locators["gpgkey.file_path"]).send_keys(key_path)
            elif key_content:
                self.find_element(locators["gpgkey.content"]).click()
                self.find_element(
                    locators["gpgkey.content"]).send_keys(key_content)
            else:
                raise UIError(
                    'Could not create new gpgkey "{0}" without contents'
                    .format(name)
                )
            self.wait_until_element(common_locators["create"]).click()
            self.wait_for_ajax()
        else:
            raise UIError(
                'Could not create new gpg key "{0}"'.format(name)
            )

    def search(self, element_name):
        """Uses the search box to locate an element from a list of elements."""
        Navigator(self.browser).go_to_gpg_keys()
        self.wait_for_ajax()
        element = None
        strategy, value = locators["gpgkey.key_name"]
        searchbox = self.wait_until_element(common_locators["kt_search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(escape_search(element_name))
            self.wait_for_ajax()
            self.wait_until_element(
                common_locators["kt_search_button"]
            ).click()
            element = self.wait_until_element((strategy, value % element_name))
            return element

    def delete(self, name, really):
        """Deletes an existing gpg key."""
        element = self.search(name)

        if element:
            element.click()
            self.wait_for_ajax()
            self.wait_until_element(locators["gpgkey.remove"]).click()
            self.wait_for_ajax()
            if really:
                self.wait_until_element(
                    common_locators["confirm_remove"]).click()
            else:
                raise UIError(
                    'Could not delete the selected key "{0}".'.format(name)
                )

    def update(self, name, new_name=None, new_key=None):
        """Updates an existing GPG key."""
        element = self.search(name)

        if element:
            element.click()
            self.wait_for_ajax()
            if new_name:
                self.edit_entity(
                    locators["gpgkey.edit_name"],
                    locators["gpgkey.edit_name_text"],
                    new_name,
                    locators["gpgkey.save_name"]
                )
                self.wait_for_ajax()
            if new_key:
                self.wait_until_element(
                    locators["gpgkey.file_path"]).send_keys(new_key)
                self.wait_until_element(
                    locators["gpgkey.upload_button"]).click()
        else:
            raise UIError('Could not update the gpg key "{0}"'.format(name))

    def assert_product_repo(self, key_name, product):
        """To validate product and repo association with gpg keys.

        Here product is a boolean variable when product = True; validation
        assert product tab otherwise assert repo tab.

        """
        element = self.search(key_name)

        if element:
            element.click()
            self.wait_for_ajax()
            if product:
                self.find_element(
                    tab_locators["gpgkey.tab_products"]).click()
            else:
                self.find_element(tab_locators["gpgkey.tab_repos"]).click()
            if self.wait_until_element(locators["gpgkey.product_repo"]):
                element = self.find_element(
                    locators["gpgkey.product_repo"]).get_attribute('innerHTML')
                string = element.strip(' \t\n\r')
                return string
        else:
            raise UIError(
                'Could not search the given gpg key "{0}"'.format(key_name)
            )

    def assert_key_from_product(self, name, product, repo=None):
        """Assert the key association after deletion from product tab."""
        nav = Navigator(self.browser)
        nav.go_to_products()
        self.wait_for_ajax()
        prd_element = self.search_entity(
            product, locators["prd.select"], katello=True)
        if prd_element:
            prd_element.click()
            self.wait_for_ajax()
            if repo is not None:
                self.wait_until_element(tab_locators["prd.tab_repos"]).click()
                strategy = locators["repo.select"][0]
                value = locators["repo.select"][1]
                self.wait_until_element((strategy, value % repo)).click()
                self.wait_for_ajax()
                self.wait_until_element(locators["repo.gpg_key_edit"]).click()
                self.wait_for_ajax()
                element = Select(
                    self.find_element(locators["repo.gpg_key_update"])
                ).first_selected_option.text
                if element == '':
                    return None
                else:
                    raise UIError(
                        'GPGKey "{0}" is still assoc with selected repo'
                        .format(name)
                    )
            else:
                self.wait_until_element(
                    tab_locators["prd.tab_details"]).click()
                self.wait_for_ajax()
                self.wait_until_element(locators["prd.gpg_key_edit"]).click()
                self.wait_for_ajax()
                element = Select(
                    self.find_element(locators["prd.gpg_key_update"])
                ).first_selected_option.text
                if element == '':
                    return None
                else:
                    raise UIError(
                        'GPG key "{0}" is still assoc with product'
                        .format(name)
                    )
        else:
            raise UIError(
                'Could not find the product "{0}"'.format(product)
            )
