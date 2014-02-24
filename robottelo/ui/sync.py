"""
Implements Synchronization for the Repos in the UI
"""
import time
from robottelo.ui.base import Base
from robottelo.ui.locators import locators
from robottelo.ui.navigator import Navigator


class Sync(Base):
    """
    Synchronizes products and repos from UI.
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def assert_sync(self, product, repos):
        """
        Asserts the sync of Repos.
        """
        nav = Navigator(self.browser)
        nav.go_to_sync_status()
        repos_result = []
        strategy = locators["sync.prd_expander"][0]
        value = locators["sync.prd_expander"][1]
        strategy1 = locators["sync.fetch_result"][0]
        value1 = locators["sync.fetch_result"][1]
        strategy2 = locators["sync.cancel"][0]
        value2 = locators["sync.cancel"][1]
        prd_exp = self.wait_until_element((strategy, value % product))
        if prd_exp:
            prd_exp.click()
        for repo in repos:
            timeout = time.time() + 60 * 10
            sync_cancel = self.wait_until_element((strategy2,
                                                   value2 % repo))
            while sync_cancel:
                if time.time() > timeout:
                    break
                sync_cancel = self.wait_until_element((strategy2,
                                                   value2 % repo))
            result = self.wait_until_element((strategy1, value1 % repo)).text
            repos_result.append(result)
        if all([str(result) == "Sync complete." \
                for result in repos_result]):
            return True

    def sync_custom_repos(self, product, repos):
        """
        Selects or De-Selects Custom Repos to Synchronize from UI.
        """
        strategy = locators["sync.prd_expander"][0]
        value = locators["sync.prd_expander"][1]
        strategy1 = locators["sync.repo_checkbox"][0]
        value1 = locators["sync.repo_checkbox"][1]
        prd_exp = self.wait_until_element((strategy, value % product))
        if prd_exp:
            prd_exp.click()
        for repo in repos:
            repo_select = self.wait_until_element((strategy1, value1 % repo))
            if repo_select:
                repo_select.click()
        self.wait_until_element(locators["sync.sync_now"]).click()
        self.wait_for_ajax()
