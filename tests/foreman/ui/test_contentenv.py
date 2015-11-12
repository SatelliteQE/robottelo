# -*- encoding: utf-8 -*-
"""Test class for Life cycle environments UI"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.factory import make_lifecycle_environment
from robottelo.ui.locators import locators
from robottelo.ui.session import Session


class ContentEnvironment(UITestCase):
    """Implements Life cycle content environment tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(ContentEnvironment, cls).setUpClass()
        cls.org_name = entities.Organization().create().name

    @run_only_on('sat')
    def test_positive_create_content_environment_basic(self):
        """@Test: Create content environment with minimal input parameters

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created

        """
        strategy, value = locators['content_env.select_name']
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_lifecycle_environment(
                        session,
                        org=self.org_name,
                        name=name,
                        description=gen_string('alpha')
                    )
                    self.assertIsNotNone(self.contentenv.wait_until_element((
                        strategy, value % name)))

    @run_only_on('sat')
    def test_positive_create_content_environment_chain(self):
        """@Test: Create Content Environment in a chain

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created

        """
        env1_name = gen_string('alpha')
        env2_name = gen_string('alpha')
        description = gen_string('alpha')
        strategy, value = locators['content_env.select_name']
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session,
                org=self.org_name,
                name=env1_name,
                description=description
            )
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % env1_name)))
            self.contentenv.create(env2_name, description, prior=env1_name)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % env2_name)))

    @run_only_on('sat')
    def test_positive_delete_content_environment(self):
        """@Test: Create Content Environment and delete it

        @Feature: Content Environment - Positive Delete

        @Assert: Environment is deleted

        """
        name = gen_string('alpha')
        strategy, value = locators['content_env.select_name']
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session,
                org=self.org_name,
                name=name,
                description=gen_string('alpha')
            )
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % name)))
            self.contentenv.delete(name)
            session.nav.go_to_life_cycle_environments()
            self.assertIsNone(self.contentenv.wait_until_element
                              ((strategy, value % name), 3))

    @run_only_on('sat')
    def test_positive_update_content_environment(self):
        """@Test: Create Content Environment and update it

        @Feature: Content Environment - Positive Update

        @Assert: Environment is updated

        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        strategy, value = locators['content_env.select_name']
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session, org=self.org_name, name=name)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % name)))
            self.contentenv.update(name, new_name, gen_string('alpha'))
            session.nav.go_to_life_cycle_environments()
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % new_name)))
