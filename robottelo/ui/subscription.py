"""
Implements Subscriptions/Manifest handling for the UI
"""

from robottelo.ui.base import Base
from robottelo.ui.locators import locators, common_locators


class Subscriptions(Base):
    """
    Manipulates Subscriptions from UI
    """

    def upload(self, path, repo_url=None):
        """
        Uploads Manifest/subscriptions via UI
        """

        self.wait_until_element(locators["subs.manage_manifest"]).click()
        self.wait_for_ajax()
        if repo_url:
            self.wait_until_element(locators["subs.repo_url_edit"]).click()
            self.wait_for_ajax()
            self.text_field_update(locators["subs.repo_url_update"], repo_url)
            self.wait_until_element(common_locators["save"]).click()
        browse_element = self.wait_until_element(locators["subs.file_path"])
        browse_element.send_keys(path)
        self.wait_until_element(locators["subs.upload"]).click()
        self.wait_until_element(locators["subs.manifest_exists"], 10)

    def delete(self):
        """
        Uploads Manifest/subscriptions via UI
        """

        self.wait_until_element(locators["subs.manage_manifest"]).click()
        self.wait_for_ajax()
        self.wait_until_element(locators["subs.delete_manifest"]).click()
        self.wait_for_ajax()

    def refresh(self):
        """
        Refreshes Manifest/subscriptions via UI
        """

        self.wait_until_element(locators["subs.manage_manifest"]).click()
        self.wait_for_ajax()
        self.wait_until_element(locators["subs.refresh_manifest"]).click()
        self.wait_for_ajax()
