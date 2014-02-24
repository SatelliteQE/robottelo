"""
Implements Synchronization for the Repos in the UI
"""
import time
from collections import defaultdict
from functools import partial
from robottelo.common.constants import PRDS, REPOSET
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
        if all([str(result) == "Sync complete."
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

    def create_repos_tree(self, repos):
        """
        Creates an hierarchial dict of repos.
        """
        repos_tree = defaultdict(partial(defaultdict,
                                         partial(defaultdict,
                                                 partial(defaultdict, str))))
        for p, rs, r, ra, value in repos:
            repos_tree[p][rs][r][ra] = value
        return repos_tree

    def enable_rh_repos(self, repos_tree):
        """
        Enables Red Hat Repos.
        """
        strategy = locators["rh.prd_expander"][0]
        value = locators["rh.prd_expander"][1]
        strategy1 = locators["rh.reposet_expander"][0]
        value1 = locators["rh.reposet_expander"][1]
        strategy2 = locators["rh.reposet_checkbox"][0]
        value2 = locators["rh.reposet_checkbox"][1]
        strategy3 = locators["rh.repo_checkbox"][0]
        value3 = locators["rh.repo_checkbox"][1]
        for prd in repos_tree:
            self.wait_until_element((strategy, value % PRDS[prd])).click()
            for reposet in repos_tree[prd]:
                rs_exp = self.wait_until_element((strategy1,
                                                  value1 % REPOSET[reposet]))
                rs_cb = self.wait_until_element((strategy2,
                                                 value2 % REPOSET[reposet]))
                if rs_exp:
                    rs_exp.click()
                elif rs_cb:
                    rs_cb.click()
                    rs_exp.click()
                for repo in repos_tree[prd][reposet]:
                    repo_values = repos_tree[prd][reposet][repo]
                    repo_name = repo_values[repo + "_n"]
                    repo_select = self.wait_until_element((strategy3,
                                                           value3 % repo_name))
                    if repo_select:
                        repo_select.click()

    def sync_rh_repos(self, repos_tree):
        """
        Selects or De-Selects Red Hat Repos to Synchronize from UI.
        """
        strategy = locators["sync.prd_expander"][0]
        value = locators["sync.prd_expander"][1]
        strategy1 = locators["sync.verarch_expander"][0]
        value1 = locators["sync.verarch_expander"][1]
        strategy2 = locators["sync.verarch_expander"][0]
        value2 = locators["sync.verarch_expander"][1]
        strategy3 = locators["sync.repo_checkbox"][0]
        value3 = locators["sync.repo_checkbox"][1]
        for prd in repos_tree:
            prd_exp = self.wait_until_element((strategy, value % PRDS[prd]))
            if prd_exp:
                prd_exp.click()
            for reposet in repos_tree[prd]:
                for repo in repos_tree[prd][reposet]:
                    repo_values = repos_tree[prd][reposet][repo]
                    repo_name = repo_values[repo + "_n"]
                    repo_arch = repo_values[repo + "_a"]
                    repo_ver = repo_values[repo + "_v"]
                    ver_exp = self.wait_until_element((strategy1,
                                                       value1 % repo_ver))
                    if ver_exp:
                        ver_exp.click()
                    arch_exp = self.wait_until_element((strategy2,
                                                        value2 % repo_arch))
                    if arch_exp:
                        arch_exp.click()
                    repo_select = self.wait_until_element((strategy3,
                                                           value3 % repo_name))
                    if repo_select:
                        repo_select.click()
