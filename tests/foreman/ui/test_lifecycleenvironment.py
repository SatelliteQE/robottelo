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
from robottelo.api.utils import create_role_permissions
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
)
from robottelo.test import UITestCase
from robottelo.ui.base import UINoSuchElementError
from robottelo.ui.factory import make_lifecycle_environment
from robottelo.ui.locators import menu_locators
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

    @skip_if_bug_open('bugzilla', 1420511)
    @run_only_on('sat')
    @tier2
    def test_positive_custom_user_view_lce(self):
        """As a custom user attempt to view a lifecycle environment created
        by admin user

        @id: 768b647b-c530-4eca-9caa-38cf8622f36d

        @BZ: 1420511

        @Steps:

        As an admin user:

        1. Create an additional lifecycle environments other than Library
        2. Create a user without administrator privileges
        3. Create a role with the the following permissions:

        * (Miscellaneous): access_dashboard
        * Lifecycle Environment:

          * edit_lifecycle_environments
          * promote_or_remove_content_views_to_environment
          * view_lifecycle_environments

        * Location: view_locations
        * Organization: view_organizations

        4. Assign the created role to the custom user

        As a custom user:

        1. Log in
        2. Navigate to Content -> Lifecycle Environments

        @Assert: The additional lifecycle environment is viewable
        and accessible by the custom user.

        @CaseLevel: Integration
        """
        role_name = gen_string('alpha')
        env_name = gen_string('alpha')
        user_login = gen_string('alpha')
        user_password = gen_string('alpha')
        org = entities.Organization().create()
        role = entities.Role(name=role_name).create()
        permissions_types_names = {
            None: ['access_dashboard'],
            'Organization': ['view_organizations'],
            'Location': ['view_locations'],
            'Katello::KTEnvironment': [
                'view_lifecycle_environments',
                'edit_lifecycle_environments',
                'promote_or_remove_content_views_to_environments'
            ]
        }
        create_role_permissions(role, permissions_types_names)
        entities.User(
            default_organization=org,
            organization=[org],
            role=[role],
            login=user_login,
            password=user_password
        ).create()
        # create a life cycle environment as admin user and ensure it's visible
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session, org=org.name, name=env_name)
            self.assertIsNotNone(self.lifecycleenvironment.search(env_name))

        # ensure the created user also can find the created life cycle
        # environment link
        with Session(self.browser, user=user_login, password=user_password):
            # to ensure that the created user has only the assigned
            # permissions, check that hosts menu tab does not exist
            self.assertIsNone(
                self.content_views.wait_until_element(
                    menu_locators['menu.hosts'], timeout=1)
            )
            # assert that the created user is not a global admin user
            # check administer->users page
            with self.assertRaises(UINoSuchElementError):
                session.nav.go_to_users()
            # assert that the user can view the lvce created by admin user
            self.assertIsNotNone(self.lifecycleenvironment.search(env_name))
