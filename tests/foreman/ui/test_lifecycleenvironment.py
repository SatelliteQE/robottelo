# -*- encoding: utf-8 -*-
"""Test class for Life cycle environments UI

@Requirement: Lifecycleenvironment

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import run_only_on, stubbed, tier1, tier2
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

        @id: 2c3a9c4c-3508-4d75-8f60-8bc6f7c0717f

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

        @id: ed3d2c88-ef0a-4a1a-9f11-5bdb2119fc18

        @Assert: Environment is created

        @CaseLevel: Integration
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

        @id: fe2d9b10-fc46-47e3-827c-6f87d725ed8f

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

        @id: 5cf64c5b-2105-4384-8630-965d9b8e3024

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

    @tier2
    @stubbed('Implement once BZ1348727 is fixed')
    def test_positive_create_environment_after_host_register(self):
        """Verify that no error is thrown when creating an evironment after
        registering a host to Library.

        @id: feab2298-4faf-470b-b906-8b50d148f52a

        @BZ: 1348727

        @Setup:

        1. Create an organization.
        2. Create a new content host.
        3. Register the content host to the Library environment.

        @Steps:

        1. Create a new environment.

        @Assert: The environment is created without any errors.

        @CaseLevel: Integration

        @caseautomation: notautomated
        """
