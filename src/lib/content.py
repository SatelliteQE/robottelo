#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from login import login
from common import find_element, get_manifest_file, wait_until_element
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import Select
from robot.api import logger
from robot.utils import asserts


class content(login):

    #ROBOT_LIBRARY_SCOPE = 'TEST_CASE'
    __version__ = '0.1'


    # Locators
    _HEADER_CONTENT_MANAGEMENT = "//li[@id='content']/a"
    _SUB_HEADER_CONTENT_PROVIDER = "//li[@id='providers']/a"
    _NEW_ORG_LINK = "//div[@id='list-title']/header/a"
    _ORG_NAME = "//form[@id='new_organization']/fieldset/div[2]/input"
    _ORG_SUBMIT = "//form[@id='new_organization']/div[2]/div/input"
    _NEW_ORG = "//div[@id='organization_%s']/div"


    def __init__(self, base_url, browser=None):
        login.__init__(self, base_url, browser)


    def go_to_content_tab(self):
        """
        Takes user to the Content Management tab in the ui.
        """

        # Organizations tab
        content_tab = wait_until_element(self.driver, self._HEADER_CONTENT_MANAGEMENT, By.XPATH)
        asserts.fail_if_none(content_tab, "Could not find the Organizations tab.")
        content_tab.click()


    def select_content_provider(self, content_provider_type):
        """
        Selects the content provider type
        """

        # Hover over the Content Provider link
        content_provider_link = wait_until_element(self.driver, self._SUB_HEADER_CONTENT_PROVIDER, By.XPATH)
        try:
            hover = ActionChains(drv).move_to_element(content_provider_link)
            asserts.fail_if_none(hover, "Failed to move the mouse over the Contant Providers link.")
            hover.perform()
            provider = wait_until_element(drv, "//li[@id='%s']/a" % content_provider_type, By.XPATH)
            asserts.fail_if_none(provider, "Could not locate the content provider type.")
            provider.click()
        except WebDriverException, e:
            logger.error("Cannot perform native interaction! See https://groups.google.com/group/webdriver/browse_thread/thread/f7130084c623f337/568fe9e85b6fd658?lnk=raot&pli=1 for more information. Error: %s" % str(e))
            drv.get("%s/%s" % (drv.current_url, content_provider_type))
        except NoSuchElementException, e:
            asserts.fail("Could not select the '%s' content type" % content_provider_type)


    def red_hat_provider(self, manifest_url, force=True):
        """
        Uploads a Red Hat manifest file.
        """

        manifest_file = get_manifest_file(manifest_url)

        # Check for the manifest field
        manifest_field = wait_until_element(self.driver, "//form[@id='upload_manifest']/div[2]/input", By.XPATH)
        asserts.fail_if_none(manifest_field, "Could not locate the manifest field.")
        # This is the path to the manifest file
        manifest_field.send_keys(filename)

        # Force it?
        if force:
            # Locate the Force checkbox
            force_checkbox = wait_until_element(self.driver, "//div[@id='force_checkbox']/input", By.XPATH)
            asserts.fail_if_none(force_checkbox, "Could not locate the Force checkbox.")
            force_checkbox.click()

        # Find the import link
        submit_button = wait_until_element(self.driver, "//div[@id='upload_button']/a", By.XPATH)
        submit_button.click()

        # TODO: Find a way to improve validation. count("//table[@id='redhatSubscriptionTable']/tbody/tr")?
        subscriptions = wait_until_element(self.driver, "//table[@id='redhatSubscriptionTable']/tbody/tr", By.XPATH)
        asserts.fail_if_none(subscriptions, "Could not find a subscription.")


    def enabled_repository(self, product, version, arch, component):
        """
        Enables the repository specified.
        """

        # Locate the Enable Repo tab
        enable_repos_tab = wait_until_element(self.driver, "//div[@id='tabs']/nav/ul/li[2]/a", By.XPATH)
        asserts.fail_if_none(enable_repos_tab, "Could not locate the Enable Repo tab.")
        enable_repos_tab.click()

        # Select the product
        product_span= wait_until_element(self.driver, "//tr/td[contains(., '%s')]" % product, By.XPATH)
        asserts.fail_if_none(product_span, "Could not locate the '%s' product." % product)
        product_node = wait_until_element(self.driver, "//tr[contains(., '%s')]" % product, By.XPATH)
        product_id = product_node.get_attribute("id")
        product_span.click()

        # Select the version
        version_span = wait_until_element(self.driver, "//tr[@id='%s-%s']/td/span" % (product_id, version), By.XPATH)
        asserts.fail_if_none(version_span, "Could not locate the '%s' version." % version)
        version_span.click()

        # Select the arch
        arch_span = wait_until_element(self.driver, "//tr[@id='%s-%s-%s']/td/span" % (product_id, version, arch), By.XPATH)
        asserts.fail_if_none(arch_span, "Could not locate the '%s' arch." % arch)
        arch_span.click()

        # Select the component
        repo = wait_until_element(self.driver, "//tr[contains(@class, 'child-of-%s-%s-%s')]/td[contains(., '%s')]/input" % (product_id, version, arch, component), By.XPATH)
        asserts.fail_if_none(repo, "Could not locate the repository '%s'." % component)
        repo.click()


    def select_org(self, org_name):
        """
        Switch the ui context to the provided org name.
        """

        # go to the url
        self.driver.get(self.base_url)

        # Check for the Organizations selector
        orgbox = wait_until_element(self.driver, "//a[@id='switcherButton']/div", By.XPATH)
        asserts.fail_if_none(orgbox, "Could not locate the Organizations selector.")
        orgbox.click()

        # Select the organization
        org = wait_until_element(self.driver, "//a[contains(., '%s')]" % org_name.replace(" ", "_"), By.XPATH)
        asserts.fail_if_none(org, "Could not locate the '%s' organization." % org_name)
        org.click()

        # Validate organization changed
        orgbox = wait_until_element(self.driver, "//a[@id='switcherButton']/div", By.XPATH)
        asserts.fail_if_none(orgbox, "Could not locate the Organizations selector.")
        asserts.assert_equal(orgbox.text, org_name, "Failed to swith to the '%s' organization." % org_name)


    def create_org(self, name):
        """
        Creates a new organization with the provided name.
        """

        # go to the url
        self.driver.get(self.base_url)

        # Select the Organizations tab
        self.go_to_organizations_tab()

        # Orgs List link
        org_list_link = wait_until_element(self.driver, "//li[@id='org_list']/a", By.XPATH)
        asserts.fail_if_none(org_list_link, "Could not find the Orgs List link.")
        org_list_link.click()

        # Verify that org doesn't exist
        org = wait_until_element(self.driver, self._NEW_ORG % name.replace(" ", "_"), By.XPATH)
        asserts.fail_unless_none(org, "An organization named '%s' already exists." % name)

        # New Organization link
        new_org_link = wait_until_element(self.driver, self._NEW_ORG_LINK, By.XPATH)
        asserts.fail_if_none(new_org_link, "could not find the new organization link.")
        new_org_link.click()

        # New org form
        org_name = wait_until_element(self.driver, self._ORG_NAME, By.XPATH)
        asserts.fail_if_none(org_name, "Could not enter the organization name.")
        org_name.send_keys(name)

        submit_button = wait_until_element(self.driver, self._ORG_SUBMIT, By.XPATH)
        submit_button.click()

        # Orgs List link
        org_list_link = wait_until_element(self.driver, "//li[@id='org_list']/a", By.XPATH)
        asserts.fail_if_none(org_list_link, "Could not find the Orgs List link.")
        org_list_link.click()

        # Verify that new org exists
        org = wait_until_element(self.driver, self._NEW_ORG % name.replace(" ", "_"), By.XPATH)
        asserts.fail_if_none(org, "Could not locate the newly created organization named '%s'." % name)


    def delete_org(self, name):
        """
        Creates a new organization with the provided name.
        """

        # go to the url
        self.driver.get(self.base_url)

        # Select the Organizations tab
        self.go_to_organizations_tab()

        # Orgs List link
        org_list_link = wait_until_element(self.driver, "//li[@id='org_list']/a", By.XPATH)
        asserts.fail_if_none(org_list_link, "Could not find the Orgs List link.")
        org_list_link.click()

        # Verify that org exists
        org = wait_until_element(self.driver, self._NEW_ORG % name.replace(" ", "_"), By.XPATH)
        asserts.fail_if_none(org, "Could not locate an organization named '%s'." % name)
        org.click()

        # Remove Org link
        remove_org_link = wait_until_element(self.driver, "//div[@id='panel']/div/div[2]/div/a", By.XPATH)
        asserts.fail_if_none(remove_org_link, "Could not find the Remove Org link.")
        remove_org_link.click()

        # Find the Yes button
        yes_button = wait_until_element(self.driver, "//button[@type='button']", By.XPATH)
        asserts.fail_if_none(yes_button, "Could not find the Yes button to remove role.")
        yes_button.click()

        # Orgs List link
        org_list_link = wait_until_element(self.driver, "//li[@id='org_list']/a", By.XPATH)
        asserts.fail_if_none(org_list_link, "Could not find the Orgs List link.")
        org_list_link.click()

        # Verify that org doesn't exist
        org = wait_until_element(self.driver, self._NEW_ORG % name.replace(" ", "_"), By.XPATH)
        asserts.fail_unless_none(org, "Could not delete organization named '%s'." % name)


    def add_env_to_org(self, org_name, prior_env_name, new_env_name):
        """
        Adds a new environment to an existing organization.
        """

        # go to the url
        self.driver.get(self.base_url)

        # Select the Organizations tab
        self.go_to_organizations_tab()

        # Orgs List link
        org_list_link = wait_until_element(self.driver, "//li[@id='org_list']/a", By.XPATH)
        asserts.fail_if_none(org_list_link, "Could not find the Orgs List link.")
        org_list_link.click()

        # Verify that org exists
        org = wait_until_element(self.driver, self._NEW_ORG % org_name.replace(" ", "_"), By.XPATH)
        asserts.fail_if_none(org, "Could not locate an organization named '%s'." % org_name)
        org.click()

        # New env should not be found yet
        env = wait_until_element(self.driver, "//a[contains(@class, 'subpanel_element')]/div[contains(.,'%s')]" % new_env_name, By.XPATH)
        asserts.fail_unless_none(env, "There is an environment with this name already.")

        # Locate the New Environment button
        new_env_button = wait_until_element(self.driver, "//div[contains(@class, 'button subpanel_element')]", By.XPATH)
        asserts.fail_if_none(new_env_button, "Could not find the New Env button.")
        new_env_button.click()

        # Locate the Environment Name field
        env_name_field = wait_until_element(self.driver, "//form[@id='new_subpanel']/fieldset/div/input", By.XPATH)
        asserts.fail_if_none(env_name_field, "Could not locate the Environment Name field.")
        env_name_field.send_keys(new_env_name)

        prior_env_list = wait_until_element(self.driver, "//form[@id='new_subpanel']/fieldset[3]/div/select", By.XPATH)
        asserts.fail_if_none(prior_env_list, "Could not locate the Previous Environment dropdown.")
        try:
            Select(prior_env_list).select_by_visible_text(prior_env_name)
        except NoSuchElementException, e:
            asserts.fail("Could not locate prior environment named '%s'" % prior_env_name)

        # Locate the Submit button
        submit_button = wait_until_element(self.driver, "//form[@id='new_subpanel']/div[2]/input", By.XPATH)
        asserts.fail_if_none(submit_button, "Could not locate the Submit button")
        submit_button.click()


    def delete_env_from_org(self, org_name, env_name):
        """
        Adds a new environment to an existing organization.
        """

        # go to the url
        self.driver.get(self.base_url)

        # Select the Organizations tab
        self.go_to_organizations_tab()

        # Orgs List link
        org_list_link = wait_until_element(self.driver, "//li[@id='org_list']/a", By.XPATH)
        asserts.fail_if_none(org_list_link, "Could not find the Orgs List link.")
        org_list_link.click()

        # Verify that org exists
        org = wait_until_element(self.driver, self._NEW_ORG % org_name.replace(" ", "_"), By.XPATH)
        asserts.fail_if_none(org, "Could not locate an organization named '%s'." % org_name)
        org.click()

        # Locate existing env
        env = wait_until_element(self.driver, "//a[contains(@class, 'subpanel_element')]/div[contains(.,'%s')]" % env_name, By.XPATH)
        asserts.fail_unless_none(env, "There is an environment with this name already.")
        env.click()

        # Locate the Remove Environment link
        remove_link = wait_until_element(self.driver, "//div[@id='subpanel']/div/div[2]/div/a", By.XPATH)
        asserts.fail_if_none(remove_link, "Could not locate the Remove Environment link")
        remove_link.click()

        # Find the Yes button
        yes_button = wait_until_element(self.driver, "//button[@type='button']", By.XPATH)
        asserts.fail_if_none(yes_button, "Could not find the Yes button to remove role.")
        yes_button.click()

