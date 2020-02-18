"""Unit tests for the ``environments`` paths.

Documentation for these paths is available here:
http://www.katello.org/docs/api/apidoc/lifecycle_environments.html


:Requirement: Lifecycleenvironment

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: LifecycleEnvironments

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.constants import ENVIRONMENT
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.test import APITestCase


class LifecycleEnvironmentTestCase(APITestCase):
    """Tests for ``katello/api/v2/environments``."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(LifecycleEnvironmentTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create lifecycle environment with valid name only

        :id: ec1d985a-6a39-4de6-b635-c803ecedd832

        :expectedresults: Lifecycle environment is created and has proper name

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                lc_env = entities.LifecycleEnvironment(organization=self.org, name=name).create()
                self.assertEqual(lc_env.name, name)

    @tier1
    def test_positive_create_with_description(self):
        """Create lifecycle environment with valid description

        :id: 0bc05510-afc7-4087-ab75-1065ab5ba1d3

        :expectedresults: Lifecycle environment is created and has proper
            description

        :CaseImportance: Critical
        """
        description = gen_string('utf8')
        lc_env = entities.LifecycleEnvironment(
            organization=self.org, description=description
        ).create()
        self.assertEqual(lc_env.description, description)

    @tier1
    def test_positive_create_prior(self):
        """Create lifecycle environment with valid name, prior to
        Library

        :id: 66d34781-8210-4282-8b5e-4be811d5c756

        :expectedresults: Lifecycle environment is created with Library as
            prior

        :CaseImportance: Critical
        """
        lc_env = entities.LifecycleEnvironment(organization=self.org).create()
        self.assertEqual(lc_env.prior.read().name, ENVIRONMENT)

    @tier3
    def test_negative_create_with_invalid_name(self):
        """Create lifecycle environment providing an invalid name

        :id: 7e8ea2e6-5927-4e86-8ea8-04c3feb524a6

        :expectedresults: Lifecycle environment is not created

        :CaseImportance: Low
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.LifecycleEnvironment(name=name).create()

    @tier1
    def test_positive_update_name(self):
        """Create lifecycle environment providing the initial name, then
        update its name to another valid name.

        :id: b6715e02-f15e-4ab8-8b13-18a3619fee9e

        :expectedresults: Lifecycle environment is created and updated properly

        """
        lc_env = entities.LifecycleEnvironment(organization=self.org).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                lc_env = entities.LifecycleEnvironment(id=lc_env.id, name=new_name).update(
                    ['name']
                )
                self.assertEqual(lc_env.name, new_name)

    @tier2
    def test_positive_update_description(self):
        """Create lifecycle environment providing the initial
        description, then update its description to another one.

        :id: e946b1fc-f79f-4e57-9d4a-3181a276222b

        :expectedresults: Lifecycle environment is created and updated properly

        :CaseLevel: Integration

        :CaseImportance: Low
        """
        lc_env = entities.LifecycleEnvironment(
            organization=self.org, description=gen_string('alpha')
        ).create()
        new_description = gen_string('utf8')
        lc_env = entities.LifecycleEnvironment(id=lc_env.id, description=new_description).update(
            ['description']
        )
        self.assertEqual(lc_env.description, new_description)

    @tier1
    def test_negative_update_name(self):
        """Update lifecycle environment providing an invalid name

        :id: 55723382-9d98-43c8-85fb-df4702ca7478

        :expectedresults: Lifecycle environment is not updated and
            corresponding error is raised

        :CaseImportance: Low
        """
        name = gen_string('alpha')
        lc_env = entities.LifecycleEnvironment(organization=self.org, name=name).create()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.LifecycleEnvironment(id=lc_env.id, name=new_name).update(['name'])
                    self.assertEqual(lc_env.read().name, name)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create lifecycle environment and then delete it.

        :id: cd5a97ca-c1e8-41c7-8d6b-f908916b24e1

        :expectedresults: Lifecycle environment is deleted successfully

        :CaseImportance: Critical
        """
        lc_env = entities.LifecycleEnvironment(organization=self.org).create()
        lc_env.delete()
        with self.assertRaises(HTTPError):
            lc_env.read()

    @tier2
    def test_positive_search_in_org(self):
        """Search for a lifecycle environment and specify an org ID.

        :id: 110e4777-c374-4365-b676-b1db4552fe51

        :Steps:

            1. Create an organization.
            2. Create a lifecycle environment belonging to the organization.
            3. Search for lifecycle environments in the organization.

        :expectedresults: Only "Library" and the lifecycle environment just
            created are in the search results.

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        lc_envs = lc_env.search({'organization'})
        self.assertEqual(len(lc_envs), 2)
        self.assertEqual({lc_env_.name for lc_env_ in lc_envs}, {u'Library', lc_env.name})

    @tier2
    @stubbed('Implement once BZ1348727 is fixed')
    def test_positive_create_environment_after_host_register(self):
        """Verify that no error is thrown when creating an evironment after
        registering a host to Library.

        :id: ceedf88d-1ad1-47ff-aab1-04587a8121ee

        :BZ: 1348727

        :Setup:
            1. Create an organization.
            2. Create a new content host.
            3. Register the content host to the Library environment.

        :Steps: Create a new environment.

        :expectedresults: The environment is created without any errors.

        :CaseLevel: Integration

        :CaseAutomation: notautomated
        """
