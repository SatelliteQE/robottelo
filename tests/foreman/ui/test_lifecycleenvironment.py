# -*- encoding: utf-8 -*-
"""Test class for Life cycle environments UI"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import run_only_on, tier1, tier2
from robottelo.test import UITestCase
from robottelo.ui.factory import make_lifecycle_environment
from robottelo.ui.session import Session


class LifeCycleEnvironmentTestCase(UITestCase):
    """Implements Lifecycle environment tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(LifeCycleEnvironmentTestCase, cls).setUpClass()
        cls.org_name = entities.Organization().create().name

    @run_only_on('sat')
    @tier1
    def test_positive_create(self):
        """Create content environment with minimal input parameters

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_lifecycle_environment(
                        session,
                        org=self.org_name,
                        name=name,
                        description=gen_string('alpha'),
                    )
                    self.assertIsNotNone(
                        self.lifecycleenvironment.search(name))

    @run_only_on('sat')
    @tier2
    def test_positive_create_chain(self):
        """Create Content Environment in a chain

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created
        """
        env1_name = gen_string('alpha')
        env2_name = gen_string('alpha')
        description = gen_string('alpha')
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session,
                org=self.org_name,
                name=env1_name,
                description=description
            )
            self.assertIsNotNone(self.lifecycleenvironment.search(env1_name))
            make_lifecycle_environment(
                session,
                org=self.org_name,
                name=env2_name,
                description=description,
                prior=env1_name,
            )
            self.assertIsNotNone(self.lifecycleenvironment.search(env2_name))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create Content Environment and delete it

        @Feature: Content Environment - Positive Delete

        @Assert: Environment is deleted
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session,
                org=self.org_name,
                name=name,
                description=gen_string('alpha'),
            )
            self.assertIsNotNone(self.lifecycleenvironment.search(name))
            self.lifecycleenvironment.delete(name)
            self.assertIsNone(self.lifecycleenvironment.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Create Content Environment and update it

        @Feature: Content Environment - Positive Update

        @Assert: Environment is updated
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session, org=self.org_name, name=name)
            self.assertIsNotNone(self.lifecycleenvironment.search(name))
            self.lifecycleenvironment.update(
                name,
                new_name,
                gen_string('alpha')
            )
            self.assertIsNotNone(self.lifecycleenvironment.search(new_name))
