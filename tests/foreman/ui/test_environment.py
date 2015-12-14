# -*- encoding: utf-8 -*-
"""Test class for Environment UI"""

from fauxfactory import gen_string
from robottelo.datafactory import invalid_values_list, valid_environments_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_env
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class EnvironmentTestCase(UITestCase):
    """Implements environment tests in UI.

    Please note that, Environment will accept only alphanumeric chars as name.

    """

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create new environment

        @Feature: Environment - Positive Create

        @Assert: Environment is created
        """
        with Session(self.browser) as session:
            for name in valid_environments_list():
                with self.subTest(name):
                    make_env(session, name=name)
                    self.assertIsNotNone(self.environment.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_long_name(self):
        """@Test: Create new environment with 255 chars

        @Feature: Environment - Positive Create

        @Assert: Environment is created
        """
        # TODO: This test can be removed by adding the value
        # gen_string('alphanumeric', 255) to valid_env_names().  But since
        # valid_env_names() is being used by the delete tests too, this value
        # will fail since environment.delete() uses base.delete_entity() which
        # uses base.search_entity().  environment.search() specifically
        # overrides this logic to make longer strings searchable.  Once the
        # UI search improvements are done, this problem should go away and at
        # that point, this test can be merged to the previous one.
        name = gen_string('alphanumeric', 255)
        with Session(self.browser) as session:
            make_env(session, name=name)
            self.assertIsNotNone(self.environment.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create(self):
        """@Test: Try to create environment and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        @Feature: Environment - Negative Create

        @Assert: Environment is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_env(session, name=name)
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['name_haserror'])
                    )

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """@Test: Update an environment and associated OS

        @Feature: Environment - Positive Update

        @Assert: Environment is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_env(session, name=name)
            for new_name in valid_environments_list():
                with self.subTest(new_name):
                    self.environment.update(name, new_name=new_name)
                    self.assertIsNotNone(self.environment.search(new_name))
                    name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """@Test: Delete an environment

        @Feature: Environment - Positive Delete

        @Assert: Environment is deleted
        """
        with Session(self.browser) as session:
            for name in valid_environments_list():
                with self.subTest(name):
                    make_env(session, name=name)
                    self.environment.delete(name)
