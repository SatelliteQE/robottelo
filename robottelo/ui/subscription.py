"""Implements Subscriptions/Manifest handling for the UI"""
import os

from robottelo.decorators import bz_bug_is_open
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

    def upload(self, manifest, repo_url=None):
        """Uploads Manifest/subscriptions via UI.

        :param Manifest manifest: The manifest to upload.
        :param str repo_url: The RedHat URL to sync content from.

        """
        self.click(locators['subs.manage_manifest'])
        if repo_url:
            self.click(locators['subs.repo_url_edit'])
            self.text_field_update(locators['subs.repo_url_update'], repo_url)
            self.click(common_locators['save'])
        browse_element = self.wait_until_element(locators['subs.file_path'])
        # File fields requires a file path in order to upload it. Create an
        # actual file on filesystem and fill the path on the file field.
        with open(manifest.filename, 'wb') as handler:
            handler.write(manifest.content.read())
        browse_element.send_keys(manifest.filename)
        self.click(locators['subs.upload'])
        timeout = 900 if bz_bug_is_open(1339696) else 300
        self.wait_until_element(locators['subs.manifest_exists'], timeout)
        os.remove(manifest.filename)

    def delete(self):
        """Deletes Manifest/subscriptions via UI."""
        self.click(locators['subs.manage_manifest'])
        self.click(locators['subs.delete_manifest'])
        timeout = 900 if bz_bug_is_open(1339696) else 300
        self.wait_until_element_is_not_visible(
            locators['subs.manifest_exists'], timeout)

    def refresh(self):
        """Refreshes Manifest/subscriptions via UI."""
        self.click(locators['subs.manage_manifest'])
        self.click(locators['subs.refresh_manifest'])
