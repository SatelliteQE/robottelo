# -*- encoding: utf-8 -*-
"""Test class for Environment UI"""

from ddt import ddt, data
from fauxfactory import gen_string
from robottelo.decorators import run_only_on, skip_if_bug_open
from robottelo.helpers import invalid_values_list
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
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric')
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

    @data(*invalid_values_list())
    def test_create_env_negative(self, name):
        """@Test: Try to create environment and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        @Feature: Environment - Negative Create

        @Assert: Environment is not created

        """
        with Session(self.browser) as session:
            make_env(session, name=name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @skip_if_bug_open('bugzilla', 1126033)
    @data(
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    )
    def test_update_env(self, new_name):
        """@Test: Update an environment and associated OS

        @Feature: Environment - Positive Update

        @Assert: Environment is updated

        @BZ: 1126033

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_env(session, name=name)
            self.environment.update(name, new_name=new_name)
            search = self.environment.search(new_name)
            self.assertIsNotNone(search)

    @data(
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    )
    def test_remove_env(self, name):
        """@Test: Delete an environment

        @Feature: Environment - Positive Delete

        @Assert: Environment is deleted

        """
        with Session(self.browser) as session:
            make_env(session, name=name)
            self.environment.delete(name)
