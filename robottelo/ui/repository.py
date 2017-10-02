"""Implements Repos UI."""
from robottelo.constants import CHECKSUM_TYPE, REPO_TYPE
from robottelo.ui.base import Base, UINoSuchElementError
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
               upstream_repo_name=None, upstream_username=None,
               upstream_password=None, repo_type=REPO_TYPE['yum'],
               repo_checksum=CHECKSUM_TYPE['default'], download_policy=None):
        """Creates new repository from UI."""
        self.click(locators['repo.new'])
        self.assign_value(common_locators['name'], name)
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
            self.assign_value(locators['repo.url'], url)
        if download_policy:
            self.select(
                locators['repo.download_policy'],
                download_policy
            )
        if upstream_repo_name:
            self.assign_value(
                locators['repo.upstream_name'], upstream_repo_name)
        if upstream_username:
            self.assign_value(
                locators['repo.upstream_username'], upstream_username)
        if upstream_password:
            self.assign_value(
                locators['repo.upstream_password'], upstream_password)
        if http:
            self.click(locators['repo.via_http'])
        self.click(common_locators['create'])

    def update(self, name, new_name=None, new_url=None,
               new_repo_checksum=None, new_gpg_key=None, http=None,
               new_upstream_name=None, new_upstream_username=None,
               new_upstream_password=None, download_policy=None):
        """Updates repositories from UI."""
        self.search_and_click(name)
        if new_name:
            self.click(locators['repo.name_edit'])
            self.assign_value(locators['repo.name_update'], new_name)
            self.click(common_locators['save'])
        if new_url:
            self.click(locators['repo.url_edit'])
            self.assign_value(locators['repo.url_update'], new_url)
            self.click(common_locators['save'])
        if new_repo_checksum:
            self.click(locators['repo.checksum_edit'])
            self.select(locators['repo.checksum_update'], new_repo_checksum)
            self.click(common_locators['save'])
        if new_gpg_key:
            self.click(locators['repo.gpg_key_edit'])
            self.select(locators['repo.gpg_key_update'], new_gpg_key)
            self.click(common_locators['save'])
        if http is not None:
            self.click(locators['repo.via_http_edit'])
            self.assign_value(locators['repo.via_http_toggle'], http)
            self.click(common_locators['save'])
        if new_upstream_name:
            self.click(locators['repo.upstream_edit'])
            self.assign_value(
                locators['repo.upstream_update'], new_upstream_name)
            self.click(common_locators['save'])
        if new_upstream_username is not None:
            self.click(locators['repo.upstream_username_edit'])
            self.assign_value(
                locators['repo.upstream_username_update'],
                new_upstream_username
            )
            self.click(common_locators['save'])
        if new_upstream_password:
            self.click(locators['repo.upstream_password_edit'])
            self.assign_value(
                locators['repo.upstream_password_update'],
                new_upstream_password
            )
            self.click(common_locators['save'])
        if download_policy:
            self.click(locators['repo.download_policy_edit'])
            self.select(
                locators['repo.download_policy_update'],
                download_policy
            )
            self.click(common_locators['save'])

    def search(self, element_name):
        """Uses the search box to locate an element from a list of elements.
        Repository entity is located inside of Product entity and has another
        appearance, so it is necessary to use custom search there.
        """
        self.navigate_to_entity()
        self.assign_value(locators['repo.search'], element_name)
        self.click(common_locators['kt_search_button'])
        return self.wait_until_element(self._search_locator() % element_name)

    def discover_repo(self, url_to_discover, discovered_urls,
                      product, new_product=False, gpg_key=None):
        """Discovers all repos from the given URL and creates selected repos.
        Here if new_product=True; then it creates New Product instead of adding
        repos under existing product.
        """
        self.click(locators['repo.repo_discover'])
        self.assign_value(locators['repo.discover_url'], url_to_discover)
        self.click(locators['repo.discover_button'])
        discover_cancel = self.wait_until_element(
            locators['repo.cancel_discover'])
        while discover_cancel:
            discover_cancel = self.wait_until_element(
                locators['repo.cancel_discover'])
        self.wait_for_ajax()
        for url in discovered_urls:
            self.click(locators['repo.discovered_url_checkbox'] % url)
        self.click(locators['repo.create_selected'])
        if new_product:
            self.select(locators['repo.product'], 'New Product')
            self.assign_value(locators['repo.new_product_name'], product)
            if gpg_key:
                self.select(locators['repo.gpgkey_in_discover'], gpg_key)
        else:
            self.select(locators['repo.product'], 'Existing Product')
            self.select(locators['repo.select_exist_product'], product)
        self.click(locators['repo.create'])

    def validate_field(self, name, field_name, expected_field_value):
        """Check that repository field has expected value"""
        self.search_and_click(name)
        if field_name in [
            'checksum', 'errata', 'gpgkey', 'package_groups', 'packages',
            'upstream', 'url', 'download_policy', 'upstream_username',
            'upstream_password'
        ]:
            return (self.wait_until_element(locators[
                'repo.fetch_' + field_name]).text == expected_field_value)
        return False

    def fetch_content_count(self, repo_name, content_type):
        """Fetch content count for specific repo and content type.

        :param repo_name: Name of repository that should be fetched.
        :param content_type: Type of repository content. Supported values are:

            * packages
            * errata
            * package_groups
            * puppet

        :returns: Content count.
        :rtype: int
        :raises: ``ValueError`` if passed ``content_type`` is not supported.
        :raises robottelo.ui.base.UINoSuchElementError: If content is not
            found.
        """
        self.search_and_click(repo_name)
        if content_type == 'packages':
            locator = locators['repo.fetch_packages']
        elif content_type == 'errata':
            locator = locators['repo.fetch_errata']
        elif content_type == 'package_groups':
            locator = locators['repo.fetch_package_groups']
        elif content_type == 'puppet':
            locator = locators['repo.fetch_puppet_modules']
        else:
            raise ValueError("Please provide supported content_type value")
        number = self.find_element(locator)
        if number:
            return int(number.text)
        else:
            raise UINoSuchElementError("Content count not found")

    def remove_content(self, repo_name):
        """Remove content from a repository."""
        self.search_and_click(repo_name)
        self.click(locators['repo.manage_content'])
        # fixme: Should be replaced with conditional loop for >100 packages
        self.assign_value(common_locators['table_per_page'], '100')
        self.click(locators['repo.content.select_all'])
        self.click(locators['repo.content.remove'])
        self.click(locators['repo.content.confirm_remove'])

    def upload_content(self, repo_name, file_path):
        """Upload content to a repository."""
        self.search_and_click(repo_name)
        self.assign_value(locators['repo.upload.file_path'], file_path)
        self.click(locators['repo.upload'])
