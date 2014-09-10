# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Medium UI"""

from ddt import ddt
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string, generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc,
                                  make_media)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


@ddt
class Medium(UITestCase):
    """Implements all Installation Media tests"""

    org_name = None
    loc_name = None

    def setUp(self):
        super(Medium, self).setUp()
        #  Make sure to use the Class' org_name instance
        if (Medium.org_name is None and Medium.loc_name is None):
            Medium.org_name = generate_string("alpha", 8)
            Medium.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Medium.org_name)
                make_loc(session, name=Medium.loc_name)

    @data(*generate_strings_list(len1=4))
    def test_positive_create_medium_1(self, name):
        """@Test: Create a new media

        @Feature:  Media - Positive Create

        @Assert: Media is created

        """

        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))

    @data(
        generate_string('alphanumeric', 255),
        generate_string('alpha', 255),
        generate_string('numeric', 255),
        generate_string('latin1', 255),
        generate_string('utf8', 255)
    )
    def test_positive_create_medium_2(self, name):
        """@Test: Create a new media with 255 characters in name

        @Feature:  Media - Positive Create

        @Assert: Media is created

        """

        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=name,
                       path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))

    def test_negative_create_medium_1(self):
        """@Test: Create a new install media with 256 characters in name

        @Feature:  Media - Negative Create

        @Assert: Media is not created

        """

        name = generate_string("alpha", 256)
        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators["name_haserror"]))
            self.assertIsNone(self.medium.search(name))

    def test_negative_create_medium_2(self):
        """@Test: Create a new install media with whitespace in name

        @Feature:  Media - Negative Create

        @Assert: Media is not created

        """

        name = " "
        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators["name_haserror"]))

    def test_negative_create_medium_3(self):
        """@Test: Create a new install media with blank name

        @Feature:  Media - Negative Create

        @Assert: Media is not created

        """

        name = ""
        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators["name_haserror"]))

    def test_negative_create_medium_4(self):
        """@Test: Create a new install media with same name

        @Feature:  Media - Negative Create

        @Assert: Media is not created

        """

        name = generate_string("alpha", 6)
        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators["name_haserror"]))

    def test_negative_create_medium_5(self):
        """@Test: Create a new install media without media URL

        @Feature:  Media - Negative Create

        @Assert: Media is not created

        """

        name = generate_string("alpha", 6)
        path = ""
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators["haserror"]))
            self.assertIsNone(self.medium.search(name))

    def test_negative_create_medium_6(self):
        """@Test: Create an install media with an existing URL

        @Feature:  Media - Negative Create

        @Assert: Media is not created

        """

        name = generate_string("alpha", 6)
        new_name = generate_string("alpha", 6)
        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))
            make_media(session, name=new_name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators["haserror"]))
            self.assertIsNone(self.medium.search(new_name))

    def test_remove_medium(self):
        """@Test: Delete a media

        @Feature: Media - Delete

        @Assert: Media is deleted

        """
        name = generate_string("alpha", 6)
        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))
            self.medium.delete(name, True)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators["notif.success"]))
            self.assertIsNone(self.medium.search(name))

    def test_update_medium(self):
        """@Test: Updates Install media with name, path, OS family

        @Feature: Media - Update

        @Assert: Media is updated

        """
        name = generate_string("alpha", 6)
        newname = generate_string("alpha", 4)
        path = URL % generate_string("alpha", 6)
        newpath = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        new_os_family = "Debian"
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))
            self.medium.update(name, newname, newpath, new_os_family)
            self.assertTrue(self, self.medium.search(newname))
