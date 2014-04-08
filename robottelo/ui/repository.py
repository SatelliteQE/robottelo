"""
Implements Repos UI
"""

from robottelo.ui.base import Base
from robottelo.common.constants import REPO_TYPE
from robottelo.ui.locators import locators, common_locators
from selenium.webdriver.support.select import Select


class Repos(Base):
    """
    Manipulates Repos from UI
    """

    def create(self, name, product=None, gpg_key=None, http=False, url=None,
               repo_type=REPO_TYPE['yum']):
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
            if gpg_key:
                type_ele = self.find_element(common_locators["gpg_key"])
                Select(type_ele).select_by_visible_text(gpg_key)
            if url:
                self.text_field_update(locators["repo.url"], url)
            if http:
                self.find_element(locators["repo.via_http"]).click()
            self.find_element(common_locators["create"]).click()
            self.wait_for_ajax()
        else:
            raise Exception("Unable to find the product '%s':" % name)

    def update(self, name, new_url=None, new_gpg_key=None, http=False):
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
