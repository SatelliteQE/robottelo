"""Implements Repos UI."""
from robottelo.constants import CHECKSUM_TYPE, REPO_TYPE
from robottelo.ui.base import Base, UIError
from robottelo.ui.locators import common_locators, locators, tab_locators


class Repos(Base):
    """Manipulates Repos from UI."""
    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Repository entity tab"""
        self.click(tab_locators['prd.tab_repos'])

    def _search_locator(self):
        """Specify locator for Repository entity search procedure"""
        return locators['repo.select']

    def create(self, name, gpg_key=None, http=False, url=None,
               upstream_repo_name=None, repo_type=REPO_TYPE['yum'],
               repo_checksum=CHECKSUM_TYPE['default'], download_policy=None):
        """Creates new repository from UI."""
        self.click(locators['repo.new'])
        self.text_field_update(common_locators['name'], name)
        # label takes long time for 256 char test, hence timeout of 60 sec
        self.wait_for_ajax(timeout=60)
        if repo_type:
            self.select(locators['repo.type'], repo_type)
        repo_checksum_element = self.find_element(locators['repo.checksum'])
        if repo_checksum_element:
            self.select(locators['repo.checksum'], repo_checksum)
        if gpg_key:
            self.select(common_locators['gpg_key'], gpg_key)
        if url:
            self.text_field_update(locators['repo.url'], url)
        if download_policy:
            self.select(
                locators['repo.download_policy'],
                download_policy
            )
        if upstream_repo_name:
            self.text_field_update(
                locators['repo.upstream_name'], upstream_repo_name)
        if http:
            self.click(locators['repo.via_http'])
        self.click(common_locators['create'])

    def update(self, name, new_name=None, new_url=None,
               new_repo_checksum=None, new_gpg_key=None, http=False,
               new_upstream_name=None, download_policy=None):
        """Updates repositories from UI."""
        repo_element = self.search(name)
        if repo_element is None:
            raise UIError(
                u'Unable to find the repository "{0}" for update.'.format(name)
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
            self.select(locators['repo.checksum_update'], new_repo_checksum)
            self.click(common_locators['save'])
        if new_gpg_key:
            self.click(locators['repo.gpg_key_edit'])
            self.select(locators['repo.gpg_key_update'], new_gpg_key)
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
        if download_policy:
            self.click(locators['repo.download_policy_edit'])
            self.select(
                locators['repo.download_policy_update'],
                download_policy
            )
            self.click(common_locators['save'])

    def delete(self, name, really=True):
        """Delete a repository from UI."""
        self.delete_entity(
            name,
            really,
            locators['repo.remove'],
        )

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
                self.select(locators['repo.gpgkey_in_discover'], gpg_key)
        else:
            self.click(locators['repo.existing_product'])
            self.select(locators['repo.select_exist_product'], product)
        self.click(locators['repo.create'])

    def validate_field(self, name, field_name, expected_field_value):
        """Check that repository field has expected value"""
        repo_element = self.search(name)
        if repo_element is None:
            raise UIError(
                u'Unable to find the repo "{0}" for validation.'.format(name)
            )
        repo_element.click()
        self.wait_for_ajax()
        if field_name in [
            'checksum', 'errata', 'gpgkey', 'package_groups', 'packages',
            'upstream', 'url', 'download_policy'
        ]:
            return (self.wait_until_element(locators[
                'repo.fetch_' + field_name]).text == expected_field_value)
        return False

    def upload_content(self, repo_name, file_path):
        """Upload content to a repository."""
        self.search_and_click(repo_name)
        browse_element = self.wait_until_element(
            locators['repo.upload.file_path'])
        browse_element.send_keys(file_path)
        self.click(locators['repo.upload'])
