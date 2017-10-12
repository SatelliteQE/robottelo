# -*- encoding: utf-8 -*-
"""Implements GPG keys UI."""

from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class GPGKey(Base):
    """Manipulates GPG keys from UI."""
    is_katello = True
    delete_locator = locators['gpgkey.remove']

    def navigate_to_entity(self):
        """Navigate to GPG key entity page"""
        Navigator(self.browser).go_to_gpg_keys()

    def _search_locator(self):
        """Specify locator for GPG key entity search procedure"""
        return locators['gpgkey.key_name']

    def create(self, name, upload_key=False, key_path=None, key_content=None):
        """Creates a gpg key from UI."""
        self.click(locators['gpgkey.new'])
        self.assign_value(common_locators['name'], name)
        if upload_key:
            self.assign_value(locators['gpgkey.file_path'], key_path)
        elif key_content:
            self.click(locators['gpgkey.content'])
            self.assign_value(locators['gpgkey.content'], key_content)
        self.click(common_locators['create'])
        self.wait_until_element_is_not_visible(locators['gpgkey.new_form'])

    def update(self, name, new_name=None, new_key=None):
        """Updates an existing GPG key."""
        self.search_and_click(name)
        if new_name:
            self.edit_entity(
                locators['gpgkey.edit_name'],
                locators['gpgkey.edit_name_text'],
                new_name,
                locators['gpgkey.save_name']
            )
        if new_key:
            self.edit_entity(
                locators['gpgkey.edit_content'],
                locators['gpgkey.file_path'],
                new_key,
                locators['gpgkey.save_content']
            )

    def get_product_repo(self, key_name, entity_name, entity_type='Product'):
        """To validate whether product and repo associated with gpg keys.

        :param str key_name: Name of gpg key to be validated
        :param str entity_name: Product or repository name to be validated
        :param str entity_type: Specify type of entity to be validated (e.g.
            'Product' or 'Repository')
        :return: Return found entity or None otherwise
        """
        self.search_and_click(key_name)
        if entity_type == 'Product':
            self.click(tab_locators['gpgkey.tab_products'])
            self.assign_value(
                locators['gpgkey.product_repo_search'], entity_name)
            return self.wait_until_element(
                locators['gpgkey.product'] % entity_name)
        elif entity_type == 'Repository':
            self.click(tab_locators['gpgkey.tab_repos'])
            self.assign_value(
                locators['gpgkey.product_repo_search'], entity_name)
            return self.wait_until_element(
                locators['gpgkey.repo'] % entity_name)

    def assert_key_from_product(self, name, prd_element, repo=None):
        """Assert the key association after deletion from product tab."""
        self.click(prd_element)
        if repo is not None:
            self.click(tab_locators['prd.tab_repos'])
            self.click(locators['repo.select'] % repo)
            self.click(locators['repo.gpg_key_edit'])
            element = self.get_element_value(locators['repo.gpg_key_update'])
            if element != '':
                raise UIError(
                    'GPGKey "{0}" is still assoc with selected repo'
                    .format(name)
                )
        else:
            self.click(tab_locators['prd.tab_details'])
            self.click(locators['prd.gpg_key_edit'])
            element = self.get_element_value(locators['prd.gpg_key_update'])
            if element != '':
                raise UIError(
                    'GPG key "{0}" is still assoc with product'
                    .format(name)
                )
        return None
