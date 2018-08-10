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

from robottelo.api.utils import create_role_permissions
from robottelo.constants import (
    ENVIRONMENT,
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_0_PUPPET_REPO,
    FAKE_0_YUM_REPO,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    REPO_TYPE,
)
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import (
    run_only_on,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.base import UINoSuchElementError
from robottelo.ui.factory import (
    make_contentview,
    make_lifecycle_environment,
    set_context,
)
from robottelo.ui.locators import common_locators, locators, menu_locators
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

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_add_puppet_module(self):
        """Promote content view with puppet module to a new environment

        :id: 12bed99d-8f96-48ca-843a-b77e123e8e2e

        :steps:
            1. Create Product/puppet repo and sync it
            2. Create CV and add puppet module from created repo
            3. Publish and promote CV to new environment

        :expectedresults: Puppet modules can be listed successfully from
            lifecycle environment interface

        :BZ: 1408264

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        env_name = gen_string('alpha')
        puppet_module = 'httpd'
        product = entities.Product(organization=self.organization).create()
        repo_id = entities.Repository(
            product=product,
            content_type=REPO_TYPE['puppet'],
            url=FAKE_0_PUPPET_REPO
        ).create().id
        entities.Repository(id=repo_id).sync()
        with Session(self) as session:
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_puppet_module(
                cv_name,
                puppet_module,
                filter_term='Latest',
            )
            self.content_views.publish(cv_name)
            self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIsNotNone(self.lifecycleenvironment.fetch_puppet_module(
                env_name, puppet_module, cv_name=cv_name))

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

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_custom_user_view_lce(self):
        """As a custom user attempt to view a lifecycle environment created
        by admin user

        :id: 768b647b-c530-4eca-9caa-38cf8622f36d

        :BZ: 1420511

        :Steps:

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

        :expectedresults: The additional lifecycle environment is viewable and
            accessible by the custom user.

        :CaseLevel: Integration
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
        with Session(self) as session:
            make_lifecycle_environment(
                session, org=org.name, name=env_name)
            self.assertIsNotNone(self.lifecycleenvironment.search(env_name))

        # ensure the created user also can find the created life cycle
        # environment link
        with Session(self, user=user_login, password=user_password) as session:
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

    @run_only_on('sat')
    @tier3
    def test_positive_search_lce_content_view_packages_by_full_name(self):
        """Search Lifecycle Environment content view packages by full name

        Note: if package full name looks like "bear-4.1-1.noarch",
            eg. name-version-release-arch, the package name is "bear"

        :id: fad05fe9-b673-4384-b65a-926d4a0d2598

        :customerscenario: true

        :steps:
            1. Create a product with a repository synchronized
                - The repository must contain at least two package names P1 and
                  P2
                - P1 has only one package
                - P2 has two packages
            2. Create a content view with the repository and publish it
            3. Go to Lifecycle Environment > Library > Packages
            4. Select the content view
            5. Search by packages using full names

        :expectedresults: only the searched packages where found

        :BZ: 1432155

        :CaseLevel: System
        """
        packages = [
            {'name': FAKE_0_CUSTOM_PACKAGE_NAME,
             'full_names': [FAKE_0_CUSTOM_PACKAGE]},
            {'name': FAKE_1_CUSTOM_PACKAGE_NAME,
             'full_names': [FAKE_1_CUSTOM_PACKAGE, FAKE_2_CUSTOM_PACKAGE]},
        ]
        product = entities.Product(organization=self.organization).create()
        repository = entities.Repository(
            product=product, url=FAKE_0_YUM_REPO).create()
        repository.sync()
        content_view = entities.ContentView(
            organization=self.organization, repository=[repository]).create()
        content_view.publish()
        with Session(self) as session:
            set_context(session, org=self.organization.name)
            for package in packages:
                for package_full_name in package['full_names']:
                    names_found = self.lifecycleenvironment.get_package_names(
                        ENVIRONMENT,
                        package_full_name,
                        cv_name=content_view.name
                    )
                    self.assertEqual(len(names_found), 1)
                    self.assertEqual(names_found[0], package['name'])

    @run_only_on('sat')
    @tier3
    def test_positive_search_lce_content_view_packages_by_name(self):
        """Search Lifecycle Environment content view packages by name

        Note: if package full name looks like "bear-4.1-1.noarch",
            eg. name-version-release-arch, the package name is "bear"

        :id: f8dec2a8-8971-44ad-a4d5-1eb5d2eb62f6

        :customerscenario: true

        :steps:
            1. Create a product with a repository synchronized
                - The repository must contain at least two package names P1 and
                  P2
                - P1 has only one package
                - P2 has two packages
            2. Create a content view with the repository and publish it
            3. Go to Lifecycle Environment > Library > Packages
            4. Select the content view
            5. Search by package names

        :expectedresults: only the searched packages where found

        :BZ: 1432155

        :CaseLevel: System
        """
        packages = [
            {'name': FAKE_0_CUSTOM_PACKAGE_NAME,
             'packages_count': 1},
            {'name': FAKE_1_CUSTOM_PACKAGE_NAME,
             'packages_count': 2},
        ]
        product = entities.Product(organization=self.organization).create()
        repository = entities.Repository(
            product=product, url=FAKE_0_YUM_REPO).create()
        repository.sync()
        content_view = entities.ContentView(
            organization=self.organization, repository=[repository]).create()
        content_view.publish()
        with Session(self) as session:
            set_context(session, org=self.organization.name)
            for package in packages:
                names_found = self.lifecycleenvironment.get_package_names(
                    ENVIRONMENT,
                    package['name'],
                    cv_name=content_view.name
                )
                self.assertEqual(
                    len(names_found), package['packages_count'])
                for name_found in names_found:
                    self.assertTrue(
                        name_found.startswith(package['name']))
