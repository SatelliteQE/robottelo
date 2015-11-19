"""Implements Repos UI."""
from robottelo.constants import CHECKSUM_TYPE, REPO_TYPE
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators
from selenium.webdriver.support.select import Select


class Repos(Base):
    """Manipulates Repos from UI."""

    def navigate_to_entity(self):
        """Navigate to Repository entity tab"""
        self.click(tab_locators['prd.tab_repos'])

    def _search_locator(self):
        """Specify locator for Repository entity search procedure"""
        return locators['repo.select']

    def create(self, name, gpg_key=None, http=False, url=None,
               upstream_repo_name=None, repo_type=REPO_TYPE['yum'],
               repo_checksum=CHECKSUM_TYPE['default']):
        """Creates new repository from UI."""
        self.click(locators['repo.new'])
        self.text_field_update(common_locators['name'], name)
        # label takes long time for 256 char test, hence timeout of 60 sec
        self.wait_for_ajax(timeout=60)
        if repo_type:
            type_ele = self.find_element(locators['repo.type'])
            Select(type_ele).select_by_visible_text(repo_type)
        repo_checksum_element = self.find_element(locators['repo.checksum'])
        if repo_checksum_element:
            Select(repo_checksum_element).select_by_visible_text(repo_checksum)
        if gpg_key:
            type_ele = self.find_element(common_locators['gpg_key'])
            Select(type_ele).select_by_visible_text(gpg_key)
        if url:
            self.text_field_update(locators['repo.url'], url)
        if upstream_repo_name:
            self.text_field_update(
                locators['repo.upstream_name'], upstream_repo_name)
        if http:
            self.click(locators['repo.via_http'])
        self.click(common_locators['create'])

    def update(self, name, new_name=None, new_url=None, new_repo_checksum=None,
               new_gpg_key=None, http=False, new_upstream_name=None):
        """Updates repositories from UI."""
        repo_element = self.search(name)
        if repo_element is None:
            raise UIError(
                'Unable to find the repository "{0}" for update.'.format(name)
            )
        repo_element.click()
        self.wait_for_ajax()
        if new_name:
            self.click(locators['repo.name_edit'])
            self.text_field_update(locators['repo.name_update'], new_name)
            self.click(common_locators['save'])
        if new_url:
            self.click(locators['repo.url_edit'])
            self.text_field_update(locators['repo.url_update'], new_url)
            self.click(common_locators['save'])
        if new_repo_checksum:
            self.click(locators['repo.checksum_edit'])
            type_ele = self.find_element(locators['repo.checksum_update'])
            Select(type_ele).select_by_visible_text(new_repo_checksum)
            self.click(common_locators['save'])
        if new_gpg_key:
            self.click(locators['repo.gpg_key_edit'])
            gpgkey_update_loc = locators['repo.gpg_key_update']
            type_ele = self.wait_until_element(gpgkey_update_loc)
            Select(type_ele).select_by_visible_text(new_gpg_key)
            self.click(common_locators['save'])
        if http:
            self.click(locators['repo.via_http_edit'])
            self.click(locators['repo.via_http_update'])
            self.click(common_locators['save'])
        if new_upstream_name:
            self.click(locators['repo.upstream_edit'])
            self.text_field_update(
                locators['repo.upstream_update'], new_upstream_name)
            self.click(common_locators['save'])

    def delete(self, repo, really=True):
        """Delete a repository from UI."""
        self.navigate_to_entity()
        strategy, value = locators['repo.select']
        self.click((strategy, value % repo))
        self.click(locators['repo.remove'])
        if really:
            self.click(common_locators['confirm_remove'])
        else:
            self.click(common_locators['cancel'])

    def search(self, element_name):
        """Uses the search box to locate an element from a list of elements.
        Repository entity is located inside of Product entity and has another
        appearance, so it is necessary to use custom search there.

        """
        self.navigate_to_entity()
        strategy, value = self._search_locator()
        searchbox = self.wait_until_element(locators['repo.search'])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(element_name)
            element = self.wait_until_element((strategy, value % element_name))
            return element

    def discover_repo(self, url_to_discover, discovered_urls,
                      product, new_product=False, gpg_key=None):
        """Discovers all repos from the given URL and creates selected repos.
        Here if new_product=True; then it creates New Product instead of adding
        repos under existing product.

        """
        self.click(locators['repo.repo_discover'])
        self.text_field_update(locators['repo.discover_url'], url_to_discover)
        self.click(locators['repo.discover_button'])
        discover_cancel = self.wait_until_element(
            locators['repo.cancel_discover'])
        while discover_cancel:
            discover_cancel = self.wait_until_element(
                locators['repo.cancel_discover'])
        for url in discovered_urls:
            strategy, value = locators['repo.discovered_url_checkbox']
            self.click((strategy, value % url))
        self.click(locators['repo.create_selected'])
        if new_product:
            self.click(locators['repo.new_product'])
            self.text_field_update(locators['repo.new_product_name'], product)
            if gpg_key:
                Select(
                    self.find_element(locators['repo.gpgkey_in_discover'])
                ).select_by_visible_text(gpg_key)
        else:
            self.click(locators['repo.existing_product'])
            Select(
                self.find_element(locators['repo.select_exist_product'])
            ).select_by_visible_text(product)
        self.click(locators['repo.create'])

    def validate_field(self, name, field_name, expected_field_value):
        """Check that repository field has expected value"""
        repo_element = self.search(name)
        if repo_element is None:
            raise UIError(
                'Unable to find the repo "{0}" for validation.'.format(name)
            )
        repo_element.click()
        self.wait_for_ajax()
        if field_name in ['url', 'gpgkey', 'checksum', 'upstream']:
            return (self.wait_until_element(locators[
                'repo.fetch_' + field_name]).text == expected_field_value)
        return False
