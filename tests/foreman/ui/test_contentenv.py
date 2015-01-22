# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Life cycle environments UI"""

from fauxfactory import gen_string
from robottelo import entities
from robottelo.common.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.factory import make_lifecycle_environment
from robottelo.ui.locators import locators
from robottelo.ui.session import Session


@run_only_on('sat')
class ContentEnvironment(UITestCase):
    """Implements Life cycle content environment tests in UI"""

    @classmethod
    def setUpClass(cls):
        cls.org_name = entities.Organization().create()['name']

        super(ContentEnvironment, cls).setUpClass()

    def test_positive_create_content_environment_1(self):
        """@Test: Create content environment with minimal input parameters

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created

        """
        name = gen_string("alpha", 6)
        description = gen_string("alpha", 6)
        strategy, value = locators["content_env.select_name"]
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=name, description=description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % name)))

    def test_positive_create_content_environment_2(self):
        """@Test: Create Content Environment in a chain

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created

        """
        env1_name = gen_string("alpha", 6)
        env2_name = gen_string("alpha", 6)
        description = gen_string("alpha", 6)
        strategy, value = locators["content_env.select_name"]
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=env1_name,
                                       description=description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % env1_name)))
            self.contentenv.create(env2_name, description, prior=env1_name)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % env2_name)))

    def test_positive_delete_content_environment_1(self):
        """@Test: Create Content Environment and delete it

        @Feature: Content Environment - Positive Delete

        @Assert: Environment is deleted

        """
        name = gen_string("alpha", 6)
        description = gen_string("alpha", 6)
        strategy, value = locators["content_env.select_name"]
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=name, description=description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % name)))
            self.contentenv.delete(name)
            session.nav.go_to_life_cycle_environments()
            self.assertIsNone(self.contentenv.wait_until_element
                              ((strategy, value % name), 3))

    def test_positive_update_content_environment_1(self):
        """@Test: Create Content Environment and update it

        @Feature: Content Environment - Positive Update

        @Assert: Environment is updated

        """
        name = gen_string("alpha", 6)
        new_name = gen_string("alpha", 6)
        description = gen_string("alpha", 6)
        strategy, value = locators["content_env.select_name"]
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=name)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % name)))
            self.contentenv.update(name, new_name, description)
            session.nav.go_to_life_cycle_environments()
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 ((strategy, value % new_name)))
