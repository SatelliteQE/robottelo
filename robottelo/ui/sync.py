"""
Implements Synchronization for the Repos in the UI
"""

import time
from collections import defaultdict
from functools import partial
from robottelo.common.constants import PRDS, REPOSET
from robottelo.ui.base import Base
from robottelo.ui.locators import locators


class Sync(Base):
    """
    Synchronizes products and repos from UI.
    """

    def __init__(self, browser):
        """
        Sets up the browser object.
        """
        self.browser = browser

    def assert_sync(self, repos):
        """
        Asserts the sync of Repos, loops over until cancel is visible,
        while syncing.
        """
        repos_result = []
        strategy1 = locators["sync.fetch_result"][0]
        value1 = locators["sync.fetch_result"][1]
        strategy2 = locators["sync.cancel"][0]
        value2 = locators["sync.cancel"][1]
        for repo in repos:
            timeout = time.time() + 60 * 10
            sync_cancel = self.wait_until_element((strategy2,
                                                   value2 % repo))
            # Waits until sync "cancel" is visible on the UI or times out
            # after 10mins
            while sync_cancel:
                if time.time() > timeout:
                    break
                sync_cancel = self.wait_until_element((strategy2,
                                                       value2 % repo))
            result = self.wait_until_element((strategy1, value1 % repo)).text
            # Updates the result of every sync repo to the repos_result list.
            repos_result.append(result)
        # Checks whether every item(sync result) in the list is "Sync complete"
        # This function returns None if it encounters any of the below:
        # "Error Syncing", "Queued", "None" or "Cancel".
        if all([str(_result) == "Sync complete."
                for _result in repos_result]):
            return True
        else:
            return False

    def sync_custom_repos(self, product, repos):
        """
        Selects multiple custom repos to Synchronize from UI,
        by first expanding the product.
        """
        strategy = locators["sync.prd_expander"][0]
        value = locators["sync.prd_expander"][1]
        strategy1 = locators["sync.repo_checkbox"][0]
        value1 = locators["sync.repo_checkbox"][1]
        prd_exp = self.wait_until_element((strategy, value % product))
        if prd_exp:
            prd_exp.click()
        else:
            raise Exception("Could not find the \
                             product expander: '%s'" % product)
        for repo in repos:
            repo_select = self.wait_until_element((strategy1, value1 % repo))
            if repo_select:
                repo_select.click()
            else:
                raise Exception("Could not find the \
                                 repo: '%s'" % repo)
        self.wait_until_element(locators["sync.sync_now"]).click()
        self.wait_for_ajax()
        return self.assert_sync(repos)

    def create_repos_tree(self, repos):
        """
        Creates a list of dynamic hierarchial dictonary of repositories.
        A sample data which needs to be passed can be fetched from constants:
        RHEL, RHCT e.t.c
        A Simplified Output Example : -
        ({'rhel': ({'rhct6': ({'rhct65': ({'rhct65_a': 'x86_64',
                                           'rhct65_v': '6.5',
                                           'rhct65_n': 'Red Hat CloudForms.'}),
                               'rhct6S': ({'rhct6S_a': 'x86_64',
                                           'rhct6S_n': 'Red Hat CloudForms...',
                                           'rhct6S_v': '6Server'})})})})
        """
        repos_tree = defaultdict(partial(defaultdict,
                                         partial(defaultdict,
                                                 partial(defaultdict, str))))
        # p=prd, rs=reposet, r=repo, ra=repo_attr, value=attr_values
        # Looping over repos_tree gives product, repos_tree[p] gives reposet,
        # repos_tree[p][rs] gives repos and repos_tree[p][rs][r] gives
        # repo attributes.
        for p, rs, r, ra, value in repos:
            repos_tree[p][rs][r][ra] = value
        return repos_tree

    def enable_rh_repos(self, repos_tree):
        """
        Enables Red Hat Repos, after importing a RedHat Manifest.
        """
        strategy = locators["rh.prd_expander"][0]
        value = locators["rh.prd_expander"][1]
        strategy1 = locators["rh.reposet_expander"][0]
        value1 = locators["rh.reposet_expander"][1]
        strategy2 = locators["rh.reposet_checkbox"][0]
        value2 = locators["rh.reposet_checkbox"][1]
        strategy3 = locators["rh.repo_checkbox"][0]
        value3 = locators["rh.repo_checkbox"][1]
        strategy4 = locators["rh.reposet_spinner"][0]
        value4 = locators["rh.reposet_spinner"][1]
        strategy5 = locators["rh.repo_spinner"][0]
        value5 = locators["rh.repo_spinner"][1]
        # I believe the variables names makes it very intuitive as what to
        # expect while looping over repos_tree.
        for prd in repos_tree:
            self.wait_until_element((strategy, value % PRDS[prd])).click()
            for reposet in repos_tree[prd]:
                rs_exp = self.wait_until_element((strategy1,
                                                  value1 % REPOSET[reposet]))
                rs_cb = self.wait_until_element((strategy2,
                                                 value2 % REPOSET[reposet]))
                # Below loop helps when reposet checkbox is already expanded
                # and when selecting multiple repos.
                if rs_exp:
                    rs_exp.click()
                elif rs_cb:
                    rs_cb.click()
                    # Selecting a rs checkbox takes time and spinner is visible
                    # the below code loops for over 2 mins till the spinner is
                    # visible.
                    rs_spinner = self.\
                        wait_until_element((strategy4,
                                            value4 % REPOSET[reposet]))
                    timeout = time.time() + 60 * 2
                    while rs_spinner:
                        if time.time() > timeout:
                            break
                        rs_spinner = self.\
                            wait_until_element((strategy4,
                                                value4 % REPOSET[reposet]))
                for repo in repos_tree[prd][reposet]:
                    repo_values = repos_tree[prd][reposet][repo]
                    repo_name = repo_values['repo_name']
                    self.wait_until_element((strategy3,
                                             value3 % repo_name)).click()
                    # Similar to above reposet checkbox spinner
                    repo_spinner = self.\
                        wait_until_element((strategy5,
                                            value5 % repo_name))
                    timeout = time.time() + 30
                    while repo_spinner:
                        if time.time() > timeout:
                            break
                        repo_spinner = self.\
                            wait_until_element((strategy5,
                                                value5 % repo_name))

    def sync_rh_repos(self, repos_tree):
        """
        Selects Red Hat Repos to Synchronize from UI.
        """
        strategy = locators["sync.prd_expander"][0]
        value = locators["sync.prd_expander"][1]
        strategy1 = locators["sync.verarch_expander"][0]
        value1 = locators["sync.verarch_expander"][1]
        strategy2 = locators["sync.repo_checkbox"][0]
        value2 = locators["sync.repo_checkbox"][1]
        repos = []
        # create_repos_tree returns data needed to be passed to this function.
        for prd in repos_tree:
            prd_exp = self.wait_until_element((strategy, value % PRDS[prd]))
            if prd_exp:
                prd_exp.click()
            for reposet in repos_tree[prd]:
                for repo in repos_tree[prd][reposet]:
                    repo_values = repos_tree[prd][reposet][repo]
                    repo_name = repo_values['repo_name']
                    repo_arch = repo_values['repo_arch']
                    repo_ver = repo_values['repo_ver']
                    repos.append(repo_name)
                    ver_exp = self.wait_until_element((strategy1,
                                                       value1 % repo_ver))
                    if ver_exp:
                        ver_exp.click()
                        self.wait_for_ajax()
                    else:
                        raise Exception("Could not find the \
                                        version expander: '%s'" % repo_ver)
                    arch_exp = self.wait_until_element((strategy1,
                                                        value1 % repo_arch))
                    if arch_exp:
                        arch_exp.click()
                        self.wait_for_ajax()
                    else:
                        raise Exception("Could not find the \
                                        arch expander: '%s'" % repo_arch)
                    repo_select = self.wait_until_element((strategy2,
                                                           value2 % repo_name))
                    if repo_select:
                        repo_select.click()
                        self.wait_for_ajax()
                    else:
                        raise Exception("Could not find the \
                                        repository name: '%s'" % repo_name)
                self.wait_until_element(locators["sync.sync_now"]).click()
                self.wait_for_ajax()
        # Let's assert without navigating away from sync status page to avoid
        # complexities
        return self.assert_sync(repos)
