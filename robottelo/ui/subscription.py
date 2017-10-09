"""Implements Subscriptions/Manifest handling for the UI"""
import os

from robottelo.decorators import bz_bug_is_open
from robottelo.ui.base import Base, UIError, UINoSuchElementError
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.navigator import Navigator


class Subscriptions(Base):
    """Manipulates Subscriptions from UI"""
    is_katello = True

    def navigate_to_entity(self):
        """Navigate to Subscription entity page"""
        Navigator(self.browser).go_to_red_hat_subscriptions()

    def _search_locator(self):
        """Specify locator for Subscription entity search procedure"""
        return locators['subs.select']

    def upload(self, manifest, repo_url=None):
        """Uploads Manifest/subscriptions via UI.

        :param Manifest manifest: The manifest to upload.
        :param str repo_url: The RedHat URL to sync content from.

        """
        self.navigate_to_entity()
        if not self.wait_until_element(locators.subs.upload, timeout=1):
            self.click(locators.base.locators.subs.manage_manifest)
        if repo_url:
            self.click(locators['subs.repo_url_edit'])
            self.assign_value(locators['subs.repo_url_update'], repo_url)
            self.click(common_locators['save'])
        browse_element = self.wait_until_element(locators['subs.file_path'])
        # File fields requires a file path in order to upload it. Create an
        # actual file on filesystem and fill the path on the file field.
        with open(manifest.filename, 'wb') as handler:
            handler.write(manifest.content.read())
        browse_element.send_keys(manifest.filename)
        self.click(locators['subs.upload'])
        timeout = 300
        if bz_bug_is_open(1339696):
            timeout = 1500
        self.wait_until_element(locators['subs.manifest_exists'], timeout)
        os.remove(manifest.filename)

    def delete(self, name=DEFAULT_SUBSCRIPTION_NAME, really=True):
        """Deletes Manifest/subscriptions via UI."""
        self.navigate_to_entity()
        if not self.wait_until_element(locators.subs.upload, timeout=1):
            self.click(locators.subs.manage_manifest)
        self.click(locators['subs.delete_manifest'])
        if really:
            self.click(common_locators['confirm_remove'])
            timeout = 300
            if bz_bug_is_open(1339696):
                timeout = 1500
            self.wait_until_element(common_locators['alert.success'], timeout)
        else:
            self.click(common_locators['close'])
        # if no subscriptions are present, user is automatically redirected to
        # manifest upload page, meaning search will fail with
        # UINoSuchElementError as searchbox can't be found there
        searched = None
        try:
            searched = self.search(name)
        except UINoSuchElementError:
            pass
        if bool(searched) == really:
            raise UIError(
                'An error occurred while attempting to delete {}'.format(name))

    def refresh(self):
        """Refreshes Manifest/subscriptions via UI."""
        self.navigate_to_entity()
        if not self.wait_until_element(locators.subs.upload, timeout=1):
            self.click(locators.subs.manage_manifest)
        self.click(locators['subs.refresh_manifest'])

    def get_provided_products(self, subscription_name):
        """Return a list of product names provided by the subscription name"""
        self.search_and_click(subscription_name)
        self.click(tab_locators['subs.sub.tab_details'])
        return [element.text
                for element in
                self.find_elements(locators['subs.sub.provided_products'])]

    def get_content_products(self, subscription_name):
        """Return a list of product names consumed by the subscription name"""
        self.search_and_click(subscription_name)
        self.click(tab_locators['subs.sub.product_content'])
        return [element.text
                for element in
                self.find_elements(locators['subs.sub.content_products'])]

    def get_guests_provided_products(
            self, subscription_name, hypervisor_hostname):
        """Return a list of product names provided to hypervisor guests by the
        subscription name"""
        self.search(subscription_name)
        self.click(locators['subs.select_guests_of'] % (
            subscription_name, hypervisor_hostname))
        self.click(tab_locators['subs.sub.tab_details'])
        return [element.text
                for element in
                self.find_elements(locators['subs.sub.provided_products'])]

    def get_guests_content_products(
            self, subscription_name, hypervisor_hostname):
        """Return a list of hypervisor guests consumed products of
        subscription name"""
        self.search(subscription_name)
        self.click(locators['subs.select_guests_of'] % (
            subscription_name, hypervisor_hostname))
        self.click(tab_locators['subs.sub.product_content'])
        return [element.text
                for element in
                self.find_elements(locators['subs.sub.content_products'])]
