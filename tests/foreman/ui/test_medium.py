# -*- encoding: utf-8 -*-
"""Test class for Medium UI"""

from fauxfactory import gen_string
from robottelo.constants import INSTALL_MEDIUM_URL
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_media
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class MediumTestCase(UITestCase):
    """Implements all Installation Media tests"""

    @run_only_on('sat')
    @tier1
    def test_positive_create(self):
        """@Test: Create a new media

        @Feature: Media - Positive Create

        @Assert: Media is created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    path = INSTALL_MEDIUM_URL % gen_string('alpha', 6)
                    make_media(session, name=name, path=path,
                               os_family='Red Hat')
                    self.assertIsNotNone(self.medium.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_too_long_name(self):
        """@Test: Create a new install media with 256 characters in name

        @Feature: Media - Negative Create

        @Assert: Media is not created
        """
        name = gen_string('alpha', 256)
        path = INSTALL_MEDIUM_URL % name
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family='Red Hat')
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators['name_haserror']))
            self.assertIsNone(self.medium.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_blank_name(self):
        """@Test: Create a new install media with blank and whitespace in name

        @Feature: Media - Negative Create

        @Assert: Media is not created
        """
        path = INSTALL_MEDIUM_URL % gen_string('alpha', 6)
        with Session(self.browser) as session:
            for name in '', '  ':
                with self.subTest(name):
                    make_media(session, name=name, path=path,
                               os_family='Red Hat')
                    self.assertIsNotNone(
                        self.medium.wait_until_element(
                            common_locators['name_haserror'])
                    )

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """@Test: Create a new install media with same name

        @Feature: Media - Negative Create

        @Assert: Media is not created
        """
        name = gen_string('alpha', 6)
        path = INSTALL_MEDIUM_URL % name
        os_family = 'Red Hat'
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators['name_haserror']))

    @run_only_on('sat')
    @tier1
    def test_negative_create_without_path(self):
        """@Test: Create a new install media without media URL

        @Feature: Media - Negative Create

        @Assert: Media is not created
        """
        name = gen_string('alpha', 6)
        with Session(self.browser) as session:
            make_media(session, name=name, path='', os_family='Red Hat')
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.medium.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_medium_with_same_path(self):
        """@Test: Create an install media with an existing URL

        @Feature: Media - Negative Create

        @Assert: Media is not created
        """
        name = gen_string('alpha', 6)
        new_name = gen_string('alpha', 6)
        path = INSTALL_MEDIUM_URL % gen_string('alpha', 6)
        os_family = 'Red Hat'
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(name))
            make_media(session, name=new_name, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.medium.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """@Test: Delete a media

        @Feature: Media - Delete

        @Assert: Media is deleted
        """
        name = gen_string('alpha', 6)
        path = INSTALL_MEDIUM_URL % name
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family='Red Hat')
            self.medium.delete(name)

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """@Test: Updates Install media with name, path, OS family

        @Feature: Media - Update

        @Assert: Media is updated
        """
        name = gen_string('alpha', 6)
        newname = gen_string('alpha', 4)
        path = INSTALL_MEDIUM_URL % name
        newpath = INSTALL_MEDIUM_URL % newname
        with Session(self.browser) as session:
            make_media(session, name=name, path=path, os_family='Red Hat')
            self.assertIsNotNone(self.medium.search(name))
            self.medium.update(name, newname, newpath, 'Debian')
            self.assertTrue(self, self.medium.search(newname))
