"""
Implements Repos UI
"""

from robottelo.ui.base import Base
from robottelo.common.constants import REPO_TYPE, CHECKSUM_TYPE
from robottelo.ui.locators import locators, common_locators
from selenium.webdriver.support.select import Select


class Repos(Base):
    """
    Manipulates Repos from UI
    """

    def create(self, name, product=None, gpg_key=None, http=False, url=None,
               upstream_repo_name=None, repo_type=REPO_TYPE['yum'],
               repo_checksum=CHECKSUM_TYPE['default']):
        """
        Creates new repository from UI
        """
        prd_element = self.search_entity(product, locators["prd.select"],
                                         katello=True)
        if prd_element:
            prd_element.click()
            self.wait_for_ajax()
            self.wait_until_element(locators["repo.new"]).click()
            self.wait_for_ajax()
            self.text_field_update(common_locators["name"], name)
            # label takes long time for 256 char test, hence timeout of 60 sec
            self.wait_for_ajax(timeout=60)
            if repo_type:
                type_ele = self.find_element(locators["repo.type"])
                Select(type_ele).select_by_visible_text(repo_type)
            if self.find_element(locators["repo.checksum"]):
                type_ele = self.find_element(locators["repo.checksum"])
                Select(type_ele).select_by_visible_text(repo_checksum)
            if gpg_key:
                type_ele = self.find_element(common_locators["gpg_key"])
                Select(type_ele).select_by_visible_text(gpg_key)
            if url:
                self.text_field_update(locators["repo.url"], url)
            if upstream_repo_name:
                self.text_field_update(
                    locators["repo.upstream_name"], upstream_repo_name)
            if http:
                self.find_element(locators["repo.via_http"]).click()
            self.find_element(common_locators["create"]).click()
            self.wait_for_ajax()
        else:
            raise Exception("Unable to find the product '%s':" % name)

    def update(self, name, new_url=None, new_repo_checksum=None,
               new_gpg_key=None, http=False):
        """
        Updates repositories from UI
        """
        repo_element = self.search(name)
        if repo_element:
            repo_element.click()
            self.wait_for_ajax()
            if new_url:
                self.wait_until_element(locators["repo.url_edit"]).click()
                self.text_field_update(locators["repo.url_update"], new_url)
                self.find_element(common_locators["save"]).click()
            if new_repo_checksum:
                self.wait_until_element(locators["repo.checksum_edit"]).click()
                self.wait_for_ajax()
                type_ele = self.find_element(locators["repo.checksum_update"])
                Select(type_ele).select_by_visible_text(new_repo_checksum)
                self.wait_until_element(common_locators["save"]).click()
            if new_gpg_key:
                self.wait_until_element(locators["repo.gpg_key_edit"]).click()
                self.wait_for_ajax()
                gpgkey_update_loc = locators["repo.gpg_key_update"]
                type_ele = self.wait_until_element(gpgkey_update_loc)
                Select(type_ele).select_by_visible_text(new_gpg_key)
                self.wait_until_element(common_locators["save"]).click()
            if http:
                self.wait_until_element(locators["repo.via_http_edit"]).click()
                self.wait_until_element(locators["repo.via_http_update"]).\
                    click()
                self.find_element(common_locators["save"]).click()
        else:
            raise Exception(
                "Unable to find the repository '%s' for update." % name)

    def delete(self, repo, really=True):
        """
        Delete a repository from UI
        """
        strategy = locators["repo.select"][0]
        value = locators["repo.select"][1]
        self.wait_until_element((strategy, value % repo)).click()
        self.wait_for_ajax()
        self.wait_until_element(locators["repo.remove"]).click()
        if really:
            self.wait_until_element(common_locators["confirm_remove"]).click()
        else:
            self.wait_until_element(common_locators["cancel"]).click()

    def search(self, element_name):
        """
        Uses the search box to locate an element from a list of elements.
        """
        element = None
        strategy = locators["repo.select"][0]
        value = locators["repo.select"][1]
        searchbox = self.wait_until_element(locators["repo.search"])
        if searchbox:
            searchbox.clear()
            searchbox.send_keys(element_name)
            element = self.wait_until_element((strategy, value % element_name))
            return element

    def discover_repo(self, url_to_discover, discovered_urls,
                      product, new_product=False, gpg_key=None):
        """
        Discovers all repos from the given URL and creates selected repos.
        Here if new_product=True; then it creates New Product instead
        of adding repos under existing product.
        """

        self.wait_until_element(locators["repo.repo_discover"]).click()
        self.text_field_update(locators["repo.discover_url"], url_to_discover)
        self.find_element(locators["repo.discover_button"]).click()
        self.wait_for_ajax()
        discover_cancel = self.wait_until_element(locators
                                                  ["repo.cancel_discover"])
        while discover_cancel:
            discover_cancel = self.wait_until_element(locators
                                                      ["repo.cancel_discover"])
        for url in discovered_urls:
            strategy, value = locators["repo.discovered_url_checkbox"]
            url_element = self.wait_until_element((strategy, value % url))
            if url_element:
                url_element.click()
            else:
                raise Exception(
                    "Couldn't select the provided URL '%s'" % url)
        self.find_element(locators["repo.create_selected"]).click()
        self.wait_for_ajax()
        if new_product:
            self.find_element(locators["repo.new_product"]).click()
            self.text_field_update(locators["repo.new_product_name"], product)
            if gpg_key:
                Select(self.find_element(locators
                                         ["repo.gpgkey_in_discover"]
                                         )).select_by_visible_text(gpg_key)
        else:
            self.wait_until_element(locators["repo.existing_product"]).click()
            Select(self.find_element(locators
                                     ["repo.select_exist_product"]
                                     )).select_by_visible_text(product)
        self.wait_until_element(locators["repo.create"]).click()
        self.wait_for_ajax()
