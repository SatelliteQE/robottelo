# -*- encoding: utf-8 -*-
"""Implements GPG keys UI."""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import locators, common_locators, tab_locators
from robottelo.ui.navigator import Navigator
from selenium.webdriver.support.select import Select


class GPGKey(Base):
    """Manipulates GPG keys from UI."""

    def navigate_to_entity(self):
        """Navigate to GPG key entity page"""
        Navigator(self.browser).go_to_gpg_keys()

    def _search_locator(self):
        """Specify locator for GPG key entity search procedure"""
        return locators["gpgkey.key_name"]

    def _search_init(self):
        """Specify that GPG key entity has katello type"""
        return super(GPGKey, self)._search_init(is_katello=True)

    def create(self, name, upload_key=False, key_path=None, key_content=None):
        """Creates a gpg key from UI."""
        self.click(locators["gpgkey.new"])

        if self.wait_until_element(common_locators["name"]):
            self.find_element(
                common_locators["name"]).send_keys(name)
            if upload_key:
                self.click(locators["gpgkey.upload"])
                self.find_element(
                    locators["gpgkey.file_path"]).send_keys(key_path)
            elif key_content:
                self.click(locators["gpgkey.content"])
                self.find_element(
                    locators["gpgkey.content"]).send_keys(key_content)
            else:
                raise UIError(
                    u'Could not create new gpgkey "{0}" without contents'
                    .format(name)
                )
            self.click(common_locators["create"])
            self.wait_until_element_is_not_visible(locators["gpgkey.new_form"])
        else:
            raise UIError(
                'Could not create new gpg key "{0}"'.format(name)
            )

    def delete(self, name, really):
        """Deletes an existing gpg key."""
        element = self.search(name)

        if element:
            element.click()
            self.wait_for_ajax()
            self.click(locators["gpgkey.remove"])
            if really:
                self.click(common_locators["confirm_remove"])
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
                self.click(locators["gpgkey.upload_button"])
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
                self.click(tab_locators["gpgkey.tab_products"])
            else:
                self.click(tab_locators["gpgkey.tab_repos"])
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
        Navigator(self.browser).go_to_products()
        prd_element = self.search_entity(
            product, locators["prd.select"], katello=True)
        if prd_element:
            prd_element.click()
            self.wait_for_ajax()
            if repo is not None:
                self.click(tab_locators["prd.tab_repos"])
                strategy = locators["repo.select"][0]
                value = locators["repo.select"][1]
                self.click((strategy, value % repo))
                self.click(locators["repo.gpg_key_edit"])
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
                self.click(tab_locators["prd.tab_details"])
                self.click(locators["prd.gpg_key_edit"])
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
