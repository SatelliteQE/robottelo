# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Medium UI
"""

from robottelo.common.helpers import generate_name
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


class Medium(BaseUI):
    """
    Implements all Installation Media tests
    """

    def create_medium(self, name=None, path=None, os_family=None):
        "Create Installation media with navigation steps"
        name = name or generate_name(6)
        path = path or URL % generate_name(6)
        self.navigator.go_to_installation_media()  # go to media page
        self.medium.create(name, path, os_family)
        self.assertIsNotNone(self.medium.search(name))

    def test_create_medium(self):
        """
        @Feature: Media - Create
        @Test: Create a new media
        @Assert: Media is created
        """
        name = generate_name(6)
        path = URL % generate_name(6)
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_medium(name, path, os_family)

    def test_remove_medium(self):
        """
        @Feature: Media - Delete
        @Test: Delete a media
        @Assert: Media is deleted
        """
        name = generate_name(6)
        path = URL % generate_name(6)
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_medium(name, path, os_family)
        self.medium.delete(name, True)
        self.assertTrue(self.medium.wait_until_element
                        (common_locators["notif.success"]))
        self.assertIsNone(self.medium.search(name))

    def test_update_medium(self):
        """
        @Feature: Media - Update
        @Test: Update a media with name, path, OS family
        @Assert: Media is updated
        """
        name = generate_name(6)
        newname = generate_name(4)
        path = URL % generate_name(6)
        newpath = URL % generate_name(6)
        os_family = "Red Hat"
        new_os_family = "Debian"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_medium(name, path, os_family)
        self.medium.update(name, newname, newpath, new_os_family)
        self.assertTrue(self, self.medium.search(newname))
