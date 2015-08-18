"""
Implements Synchronization for the Repos in the UI
"""

import time
from collections import defaultdict
from functools import partial
from robottelo.common.constants import PRDS, REPOSET
from robottelo.ui.base import Base, UINoSuchElementError
from robottelo.ui.locators import locators


class Sync(Base):
    """Synchronizes products and repos from UI."""

    def assert_sync(self, repos, product=None):
        """Asserts sync status of the Repositories.

        Asserts the sync of Repositories, loops over while cancel is visible,
        during the syncing process.

        :param repos: A list of repositories names to assert sync status.
        :param str product: product is required only when syncing via
            repository page.
        :return: Returns True if sync is successful.
        :rtype: bool

        """
        repos_result = []
        strategy1, value1 = locators["sync.fetch_result"]
        strategy2, value2 = locators["sync.cancel"]
        strategy3, value3 = locators["sync.prd_expander"]
        if product:
            prd_exp = self.wait_until_element((strategy3, value3 % product))
            if not prd_exp:
                raise UINoSuchElementError(
                    "Could not find the product expander: '{0}'"
                    .format(product))
            prd_exp.click()
        for repo in repos:
            timeout = time.time() + 60 * 10
            sync_cancel = self.wait_until_element(
                (strategy2, value2 % repo),
                timeout=6,
                poll_frequency=2,
            )
            # Waits until sync "cancel" is visible on the UI or times out
            # after 10 mins
            while sync_cancel:
                if time.time() > timeout:
                    break
                sync_cancel = self.wait_until_element(
                    (strategy2, value2 % repo),
                    timeout=6,
                    poll_frequency=2,
                )
            result = self.wait_until_element((strategy1,
                                              value1 % repo), 5).text
            # Updates the result of every sync repo to the repos_result list.
            repos_result.append(result)
        # Checks whether every item(sync result) in the list is
        # "Syncing Complete."
        # This function returns False if it encounters any of the below:
        # "Error Syncing", "Queued", "None", "Never Synced" or "Cancel".
        if all([str(r) == "Syncing Complete." for r in repos_result]):
            return True
        else:
            return False

    def sync_custom_repos(self, product, repos):
        """Syncs Repositories from Custom Product.

        Selects multiple custom repos to Synchronize from UI,
        by first expanding the product.

        :param str product: The product which repositories belongs to.
        :param repos: The list of repositories to sync.

        """
        strategy, value = locators["sync.prd_expander"]
        strategy1, value1 = locators["sync.repo_checkbox"]
        prd_exp = self.wait_until_element((strategy, value % product))
        if prd_exp:
            prd_exp.click()
        else:
            raise UINoSuchElementError(
                "Could not find the product expander: '%s'" % product)
        for repo in repos:
            repo_select = self.wait_until_element((strategy1, value1 % repo))
            if repo_select:
                repo_select.click()
            else:
                raise UINoSuchElementError(
                    "Could not find the repo: '%s'" % repo)
        self.wait_until_element(locators["sync.sync_now"]).click()
        self.wait_for_ajax()
        return self.assert_sync(repos)

    def create_repos_tree(self, repos):
        """Creates list of dictionary.

        Creates a list of dynamic hierarchial dictonary of repositories.  A
        sample data which needs to be passed can be fetched from constants::

            RHEL, RHCT e.t.c

        A Simplified Output Example::

            ({'rhel': ({'rhct6': ({
                'rhct65': ({
                    'rhct65_a': 'x86_64',
                    'rhct65_v': '6.5',
                    'rhct65_n': 'Red Hat CloudForms.'
                }),
                'rhct6S': ({
                    'rhct6S_a': 'x86_64',
                    'rhct6S_n': 'Red Hat CloudForms...',
                    'rhct6S_v': '6Server'
                })
            })})})

        :param repos: A list of tuples.
        :returns: A list of dicts.

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
        """Enables Red Hat Repos, after importing a RedHat Manifest.

        We need to first select the PRD to enable, then the reposet
        and then the repos. A Product could have multiple reposets and
        each reposet could have multiple repos.

        :param repos_tree: Repositories to enable which is a List of dictionary
        :return: None.

        """
        strategy, value = locators["rh.prd_expander"]
        strategy1, value1 = locators["rh.reposet_expander"]
        strategy2, value2 = locators["rh.reposet_checkbox"]
        strategy3, value3 = locators["rh.repo_checkbox"]
        strategy4, value4 = locators["rh.reposet_spinner"]
        strategy5, value5 = locators["rh.repo_spinner"]
        for prd in repos_tree:
            # UI is slow here. Hence timeout is 120 seconds.
            prd_element = self.wait_until_element(
                (strategy, value % PRDS[prd]), 120)
            if prd_element:
                prd_element.click()
            else:
                raise UINoSuchElementError(
                    "Could not select the product: '{0}'".format(PRDS[prd]))
            for reposet in repos_tree[prd]:
                rs_exp = self.wait_until_element(
                    (strategy1, value1 % REPOSET[reposet]), 5)
                rs_cb = self.wait_until_element(
                    (strategy2, value2 % REPOSET[reposet]), 5)
                # Below loop helps when reposet checkbox is already expanded
                # and when selecting multiple repos.
                if rs_exp:
                    rs_exp.click()
                elif rs_cb:
                    rs_cb.click()
                    # Selecting a rs checkbox takes time and spinner is visible
                    # the below code loops for over 2 mins till the spinner is
                    # visible.
                    rs_spinner = self.wait_until_element(
                        (strategy4, value4 % REPOSET[reposet]),
                        timeout=6,
                        poll_frequency=2,
                    )
                    timeout = time.time() + 60 * 2
                    while rs_spinner:
                        if time.time() > timeout:
                            break
                        rs_spinner = self.wait_until_element(
                            (strategy4, value4 % REPOSET[reposet]),
                            timeout=6,
                            poll_frequency=2,
                        )
                for repo in repos_tree[prd][reposet]:
                    repo_values = repos_tree[prd][reposet][repo]
                    repo_name = repo_values['repo_name']
                    # UI is very slow here. Hence timeout is 120 seconds.
                    repo_element = self.wait_until_element(
                        (strategy3, value3 % repo_name), 120)
                    if repo_element:
                        repo_element.click()
                    else:
                        raise UINoSuchElementError(
                            "Could not select the repo: '{0}'"
                            "".format(repo_name))
                    # Similar to above reposet checkbox spinner
                    repo_spinner = self.wait_until_element(
                        (strategy5, value5 % repo_name),
                        timeout=6,
                        poll_frequency=2,
                    )
                    timeout = time.time() + 60
                    while repo_spinner:
                        if time.time() > timeout:
                            break
                        repo_spinner = self.wait_until_element(
                            (strategy5, value5 % repo_name),
                            timeout=6,
                            poll_frequency=2,
                        )

    def sync_noversion_rh_repos(self, prd, repos):
        """Syncs RedHat repositories which do not have version.

        Selects Red Hat non version Repos to Synchronize from UI.

        :param prd: The product which repositories belongs to.
        :param repos: List of repositories to sync.
        :return: Returns True if the sync was successful.
        :rtype: bool

        """
        return self.sync_custom_repos(prd, repos)

    def sync_rh_repos(self, repos_tree):
        """Syncs RedHat repositories.

        Selects Red Hat Repos to Synchronize from UI.

        :param repos_tree: Repositories to choose which is a List of dictionary
        :return: Returns True if the sync was successful.
        :rtype: bool

        """
        strategy, value = locators["sync.prd_expander"]
        strategy1, value1 = locators["sync.verarch_expander"]
        strategy2, value2 = locators["sync.repo_checkbox"]
        repos = []
        # create_repos_tree returns data needed to be passed to this function.
        for prd in repos_tree:
            prd_exp = self.wait_until_element(
                (strategy, value % PRDS[prd]))
            if prd_exp:
                prd_exp.click()
            for reposet in repos_tree[prd]:
                for repo in repos_tree[prd][reposet]:
                    repo_values = repos_tree[prd][reposet][repo]
                    repo_name = repo_values['repo_name']
                    repo_arch = repo_values['repo_arch']
                    repo_ver = repo_values['repo_ver']
                    repos.append(repo_name)
                    ver_exp = self.wait_until_element(
                        (strategy1, value1 % repo_ver))
                    if ver_exp:
                        ver_exp.click()
                        self.wait_for_ajax()
                    else:
                        raise UINoSuchElementError(
                            "Could not find the version expander: '%s'" %
                            repo_ver)
                    arch_exp = self.wait_until_element(
                        (strategy1, value1 % repo_arch))
                    if arch_exp:
                        arch_exp.click()
                        self.wait_for_ajax()
                    else:
                        raise UINoSuchElementError(
                            "Could not find the arch expander: '%s'" %
                            repo_arch)
                    repo_select = self.wait_until_element(
                        (strategy2, value2 % repo_name))
                    if repo_select:
                        repo_select.click()
                        self.wait_for_ajax()
                    else:
                        raise UINoSuchElementError(
                            "Could not find the repository name: '%s'" %
                            repo_name)
                self.wait_until_element(locators["sync.sync_now"]).click()
                self.wait_for_ajax()
        # Let's assert without navigating away from sync status page to avoid
        # complexities
        return self.assert_sync(repos)
