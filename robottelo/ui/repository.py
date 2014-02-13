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

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def create(self, name, product=None, gpg_key=None, http=True, url=None,
               repo_type=REPO_TYPE['yum']):
        """
        Creates new repository from UI
        """
        prd_element = self.search_entity(product, locators["prd.select"],
                                         katello=True)
        if prd_element:
            prd_element.click()
        self.find_element(locators["repo.new"]).click()
        self.wait_for_ajax()
        self.text_field_update(common_locators["name"], name)
        if repo_type != REPO_TYPE['yum']:
            type_ele = self.find_element(locators["repo.type"])
            Select(type_ele).select_by_visible_text(repo_type)
        if gpg_key:
            type_ele = self.find_element(common_locators["gpg_key"])
            Select(type_ele).select_by_visible_text(gpg_key)
        self.text_field_update(locators["repo.url"], url)
        if http:
            self.find_element(locators["repo.via_http"]).click()
        self.find_element(common_locators["create"]).click()

    def delete(self, repo, really):
        """
        Delete a repository from UI
        """
        strategy = locators["repo.select_checkox"][0]
        value = locators["repo.select_checbox"][1]
        self.wait_until_element((strategy, value % repo)).click()
        self.wait_until_element(locators["repo.remove"]).click()
        if really:
            self.wait_until_element(common_locators["confirm_remove"]).click()
        else:
            self.wait_until_element(common_locators["cancel"]).click()

    def search(self, name):
        """
        Searches existing repository from UI
        """
        element = self.search_entity(name, locators["repo.select"],
                                     katello=True)
        return element
