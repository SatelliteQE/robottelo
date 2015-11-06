"""Implements Subscriptions/Manifest handling for the UI"""

from robottelo.ui.base import Base
from robottelo.ui.locators import common_locators, locators
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

    def upload(self, path, repo_url=None):
        """Uploads Manifest/subscriptions via UI.

        :param str path: The manifest path to upload.
        :param str repo_url: The RedHat URL to sync content from.

        """
        self.click(locators['subs.manage_manifest'])
        if repo_url:
            self.click(locators['subs.repo_url_edit'])
            self.text_field_update(locators['subs.repo_url_update'], repo_url)
            self.click(common_locators['save'])
        browse_element = self.wait_until_element(locators['subs.file_path'])
        browse_element.send_keys(path)
        self.click(locators['subs.upload'])
        # Waits till the below locator is visible or until 180 seconds.
        self.wait_until_element(locators['subs.manifest_exists'], 180)

    def delete(self):
        """Uploads Manifest/subscriptions via UI."""
        self.click(locators['subs.manage_manifest'])
        self.click(locators['subs.delete_manifest'])

    def refresh(self):
        """Refreshes Manifest/subscriptions via UI."""
        self.click(locators['subs.manage_manifest'])
        self.click(locators['subs.refresh_manifest'])
