# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Environment UI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.common.decorators import data, run_only_on, skip_if_bug_open
from robottelo.test import UITestCase
from robottelo.ui.factory import make_env
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class Environment(UITestCase):
    """Implements environment tests in UI.

    Please note that, Environment will accept only alphanumeric chars as name.

    """

    @data(
        gen_string('alpha', 8),
        gen_string('numeric', 8),
        gen_string('alphanumeric', 8)
    )
    def test_create_env_positive_1(self, name):
        """@Test: Create new environment

        @Feature: Environment - Positive Create

        @Assert: Environment is created

        """
        with Session(self.browser) as session:
            make_env(session, name=name)
            search = self.environment.search(name)
            self.assertIsNotNone(search)

    @data(
        gen_string('alpha', 255),
        gen_string('numeric', 255),
        gen_string('alphanumeric', 255)
    )
    def test_create_env_positive_2(self, name):
        """@Test: Create new environment with 255 chars

        @Feature: Environment - Positive Create

        @Assert: Environment is created

        """
        with Session(self.browser) as session:
            make_env(session, name=name)
            search = self.environment.search(name)
            self.assertIsNotNone(search)

    @data(
        gen_string('alpha', 256),
        gen_string('numeric', 256),
        gen_string('alphanumeric', 256)
    )
    def test_create_env_negative_1(self, name):
        """@Test: Create new environment with 256 chars

        @Feature: Environment - Negative Create

        @Assert: Environment is not created

        """
        with Session(self.browser) as session:
            make_env(session, name=name)
            search = self.environment.search(name)
            self.assertIsNone(search)

    @data("", "  ")
    def test_create_env_negative_2(self, name):
        """@Test: Create new environment with blank and whitespace in name

        @Feature: Environment - Negative Create

        @Assert: Environment is not created

        """
        with Session(self.browser) as session:
            make_env(session, name=name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @skip_if_bug_open('bugzilla', 1126033)
    @data({'name': gen_string('alpha', 8),
           'new_name': gen_string('alpha', 8)},
          {'name': gen_string('numeric', 8),
           'new_name': gen_string('numeric', 8)},
          {'name': gen_string('alphanumeric', 8),
           'new_name': gen_string('alphanumeric', 8)})
    def test_update_env(self, testdata):
        """@Test: Update an environment and associated OS

        @Feature: Environment - Positive Update

        @Assert: Environment is updated

        @BZ: 1126033

        """
        name = testdata['name']
        new_name = testdata['new_name']
        with Session(self.browser) as session:
            make_env(session, name=name)
            self.environment.update(name, new_name=new_name)
            search = self.environment.search(new_name)
            self.assertIsNotNone(search)

    @skip_if_bug_open('bugzilla', 1126033)
    @data(
        gen_string('alpha', 8),
        gen_string('numeric', 8),
        gen_string('alphanumeric', 8)
    )
    def test_remove_env(self, name):
        """@Test: Delete an environment

        @Feature: Environment - Positive Delete

        @Assert: Environment is deleted

        """
        with Session(self.browser) as session:
            make_env(session, name=name)
            self.environment.delete(name, really=True)
            notif = session.nav.wait_until_element(
                common_locators["notif.success"])
            self.assertTrue(notif)
