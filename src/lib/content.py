#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

from base import Base
from common import get_manifest_file, wait_until_element
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from robot.api import logger
from robot.utils import asserts


class content(object):

    #ROBOT_LIBRARY_SCOPE = 'TEST_CASE'
    __version__ = '0.1'


    # Locators
    _HEADER_CONTENT_MANAGEMENT = "//li[@id='content']/a"
    _SUB_HEADER_CONTENT_PROVIDER = "//li[@id='providers']/a"
    _NEW_ORG_LINK = "//div[@id='list-title']/header/a"
    _ORG_NAME = "//form[@id='new_organization']/fieldset/div[2]/input"
    _ORG_SUBMIT = "//form[@id='new_organization']/div[2]/div/input"
    _NEW_ORG = "//div[@id='organization_%s']/div"


    def __init__(self):
        self.base = Base()


    def go_to_content_tab(self):
        """
        Takes user to the Content Management tab in the ui.
        """

        # Organizations tab
        content_tab = wait_until_element(self.base.driver, self._HEADER_CONTENT_MANAGEMENT, By.XPATH)
        asserts.fail_if_none(content_tab, "Could not find the Organizations tab.")
        content_tab.click()


    def select_content_provider(self, content_provider_type):
        """
        Selects the content provider type
        """

        # Hover over the Content Provider link
        content_provider_link = wait_until_element(self.base.driver, self._SUB_HEADER_CONTENT_PROVIDER, By.XPATH)
        try:
            hover = ActionChains(self.base.driver).move_to_element(content_provider_link)
            asserts.fail_if_none(hover, "Failed to move the mouse over the Contant Providers link.")
            hover.perform()
            provider = wait_until_element(self.base.driver, "//li[@id='%s']/a" % content_provider_type, By.XPATH)
            asserts.fail_if_none(provider, "Could not locate the content provider type.")
            provider.click()
        except WebDriverException, e:
            logger.debug("Cannot perform native interaction! See https://groups.google.com/group/webdriver/browse_thread/thread/f7130084c623f337/568fe9e85b6fd658?lnk=raot&pli=1 for more information. Error: %s" % str(e))
            # TODO: Find a better way to handle this if bug above is not fixed soon!!!
            if "custom" in content_provider_type:
                url = self.base.driver.current_url
            elif "redhat" in content_provider_type:
                url = "%s/redhat_provider" % self.base.driver.current_url
            elif "filters" in content_provider_type:
                url = "%s/filters" % self.base.base_url
            else:
                url = "%s/gpg_keys" % self.base.base_url

            self.base.driver.get(url)
        except NoSuchElementException, e:
            asserts.fail("Could not select the '%s' content type" % content_provider_type)


    def red_hat_provider(self, manifest, provider_type, force=True):
        """
        Uploads a Red Hat manifest file.
        """

        # Select Contents tab
        self.go_to_content_tab()

        # Select Red Hat content type
        self.select_content_provider(provider_type)

        manifest_file = get_manifest_file(manifest)

        # Check for the manifest field
        manifest_field = wait_until_element(self.base.driver, "//form[@id='upload_manifest']/div[2]/input", By.XPATH)
        asserts.fail_if_none(manifest_field, "Could not locate the manifest field.")
        # This is the path to the manifest file
        logger.debug(manifest_file)
        manifest_field.send_keys(manifest_file)

        # Force it?
        if force:
            # Locate the Force checkbox
            force_checkbox = wait_until_element(self.base.driver, "//div[@id='force_checkbox']/input", By.XPATH)
            asserts.fail_if_none(force_checkbox, "Could not locate the Force checkbox.")
            force_checkbox.click()

        # Find the import link
        submit_button = wait_until_element(self.base.driver, "//div[@id='upload_button']/a", By.XPATH)
        submit_button.click()

        # TODO: Find a way to improve validation. count("//table[@id='redhatSubscriptionTable']/tbody/tr")?
        subscriptions = wait_until_element(self.base.driver, "//table[@id='redhatSubscriptionTable']/tbody/tr", By.XPATH)
        asserts.fail_if_none(subscriptions, "Could not find a subscription.")


    def enabled_repository(self, provider_type, product, version, arch, component):
        """
        Enables the repository specified.
        """

        # Select Contents tab
        self.go_to_content_tab()

        # Select Red Hat content type
        self.select_content_provider(provider_type)

        # Locate the Enable Repo tab
        enable_repos_tab = wait_until_element(self.base.driver, "//div[@id='tabs']/nav/ul/li[2]/a", By.XPATH)
        asserts.fail_if_none(enable_repos_tab, "Could not locate the Enable Repo tab.")
        enable_repos_tab.click()

        # Select the product
        product_span= wait_until_element(self.base.driver, "//tr/td[contains(., '%s')]" % product, By.XPATH)
        asserts.fail_if_none(product_span, "Could not locate the '%s' product." % product)
        product_node = wait_until_element(self.base.driver, "//tr[contains(., '%s')]" % product, By.XPATH)
        product_id = product_node.get_attribute("id")
        product_span.click()

        # Select the version
        version_span = wait_until_element(self.base.driver, "//tr[@id='%s-%s']/td/span" % (product_id, version), By.XPATH)
        asserts.fail_if_none(version_span, "Could not locate the '%s' version." % version)
        version_span.click()

        # Select the arch
        arch_span = wait_until_element(self.base.driver, "//tr[@id='%s-%s-%s']/td/span" % (product_id, version, arch), By.XPATH)
        asserts.fail_if_none(arch_span, "Could not locate the '%s' arch." % arch)
        arch_span.click()

        # Select the component
        repo = wait_until_element(self.base.driver, "//tr[contains(@class, 'child-of-%s-%s-%s')]/td[contains(., '%s')]/input" % (product_id, version, arch, component), By.XPATH)
        asserts.fail_if_none(repo, "Could not locate the repository '%s'." % component)
        repo.click()
