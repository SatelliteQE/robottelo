# -*- encoding: utf-8 -*-
"""Test class for Life cycle environments UI

:Requirement: Lifecycleenvironment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from itertools import chain

from fauxfactory import gen_string
from nailgun import entities

from robottelo.datafactory import generate_strings_list
from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_lifecycle_environment
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


class LifeCycleEnvironmentTestCase(UITestCase):
    """Implements Lifecycle environment tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(LifeCycleEnvironmentTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_create(self):
        """Create content environment with minimal input parameters

        :id: 2c3a9c4c-3508-4d75-8f60-8bc6f7c0717f

        :expectedresults: Environment is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_lifecycle_environment(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=gen_string('alpha'),
                    )
                    self.assertIsNotNone(
                        self.lifecycleenvironment.search(name))

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create Content Environment and delete it

        :id: fe2d9b10-fc46-47e3-827c-6f87d725ed8f

        :expectedresults: Environment is deleted

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_lifecycle_environment(
                session,
                org=self.organization.name,
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

        :id: 5cf64c5b-2105-4384-8630-965d9b8e3024

        :expectedresults: Environment is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        with Session(self) as session:
            make_lifecycle_environment(
                session, org=self.organization.name, name=name)
            self.assertIsNotNone(self.lifecycleenvironment.search(name))
            self.lifecycleenvironment.update(
                name,
                new_name,
                gen_string('alpha')
            )
            self.assertIsNotNone(self.lifecycleenvironment.search(new_name))

    @tier2
    @stubbed('Implement once BZ1348727 is fixed')
    def test_positive_create_environment_after_host_register(self):
        """Verify that no error is thrown when creating an evironment after
        registering a host to Library.

        :id: feab2298-4faf-470b-b906-8b50d148f52a

        :BZ: 1348727

        :Setup:

            1. Create an organization.
            2. Create a new content host.
            3. Register the content host to the Library environment.

        :Steps: Create a new environment.

        :expectedresults: The environment is created without any errors.

        :CaseLevel: Integration

        :caseautomation: notautomated
        """

    @tier1
    def test_positive_env_list_fits_browser_screen(self):
        """Check if long list of lifecycle environments fits into screen

        :id: 63b985b0-c847-11e6-92ad-68f72889dc7f

        :Setup: save 8+ chained lifecycles environments

        :BZ: 1295922

        :expectedresults: lifecycle environments table fits screen

        :CaseImportance: Critical
        """
        with Session(self) as session:
            env_names = [gen_string('alpha') for _ in range(11)]
            for name, prior in zip(env_names, chain([None], env_names)):
                make_lifecycle_environment(
                    session,
                    org=self.organization.name,
                    name=name,
                    prior=prior
                )
            envs_table = session.nav.wait_until_element(
                locator=locators['content_env.table']
            )
            table_width = envs_table.size['width']
            body = session.nav.find_element(common_locators['body'])
            body_width = body.size['width']
            self.assertGreaterEqual(body_width - table_width, 0)
