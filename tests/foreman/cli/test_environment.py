# -*- encoding: utf-8 -*-
"""Test for Environment  CLI

:Requirement: Environment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice

from fauxfactory import gen_string
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.environment import Environment
from robottelo.cli.factory import (
    make_environment,
    make_location,
    make_org,
    publish_puppet_module,
)
from robottelo.cli.puppet import Puppet
from robottelo.cli.scparams import SmartClassParameter
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.datafactory import (
    invalid_id_list,
    invalid_values_list,
    valid_environments_list,
)
from robottelo.decorators import (
    tier1,
    tier2,
    upgrade,
)
from robottelo.test import CLITestCase


class EnvironmentTestCase(CLITestCase):
    """Test class for Environment CLI"""

    @classmethod
    def setUpClass(cls):
        super(EnvironmentTestCase, cls).setUpClass()
        cls.org = make_org()
        # Setup for puppet class related tests
        puppet_modules = [
            {'author': 'robottelo', 'name': 'generic_1'},
        ]
        cls.cv = publish_puppet_module(
            puppet_modules, CUSTOM_PUPPET_REPO, cls.org['id'])
        cls.env = Environment.list({
            'search': u'content_view="{0}"'.format(cls.cv['name'])})[0]
        cls.puppet_class = Puppet.info({
            'name': puppet_modules[0]['name'],
            'environment': cls.env['name'],
        })

    @tier2
    def test_positive_list_with_name(self):
        """Test Environment List

        :id: 8a81f853-929c-4eaa-8ae0-4c92ebf1f250

        :expectedresults: Environment list is displayed

        :CaseLevel: Integration
        """
        for name in valid_environments_list():
            with self.subTest(name):
                Environment.create({'name': name})
                result = Environment.list({
                    'search': 'name={0}'.format(name)
                })
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]['name'], name)

    @tier2
    def test_positive_list_with_org_and_loc_by_id(self):
        """Test Environment List filtering.

        :id: 643f7cb5-0817-4b0a-ba5e-434df2033a40

        :expectedresults: Results that match both organization and location are
            returned

        :CaseLevel: Integration

        :BZ: 1337947
        """
        # Create 2 envs with the same organization but different locations
        org = make_org()
        locs = [make_location() for _ in range(2)]
        envs = [make_environment({
            'organization-ids': org['id'],
            'location-ids': loc['id'],
        }) for loc in locs]
        results = Environment.list({'organization-id': org['id']})
        # List environments for the whole organization
        self.assertEqual(len(results), 2)
        self.assertEqual(
            {env['id'] for env in envs},
            {result['id'] for result in results}
        )
        # List environments with additional location filtering
        results = Environment.list({
            'organization-id': org['id'],
            'location-id': locs[0]['id'],
        })
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], envs[0]['id'])

    @tier2
    def test_positive_list_with_org_and_loc_by_name(self):
        """Test Environment List filtering.

        :id: 962c6750-f203-4478-8827-651db208ff92

        :expectedresults: Results that match both organization and location are
            returned

        :CaseLevel: Integration

        :BZ: 1337947
        """
        # Create 2 envs with the same organization but different locations
        org = make_org()
        locs = [make_location() for _ in range(2)]
        envs = [make_environment({
            'organizations': org['name'],
            'locations': loc['name'],
        }) for loc in locs]
        results = Environment.list({'organization': org['name']})
        # List environments for the whole organization
        self.assertEqual(len(results), 2)
        self.assertEqual(
            {env['name'] for env in envs},
            {result['name'] for result in results}
        )
        # List environments with additional location filtering
        results = Environment.list({
            'organization': org['name'],
            'location': locs[0]['name'],
        })
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], envs[0]['name'])

    @tier2
    def test_negative_list_with_org_and_loc_by_id(self):
        """Test Environment List filtering.

        :id: b1659c48-302b-4fe3-a38b-cd34c0fd4878

        :expectedresults: Server returns empty result as there is no
            environment associated with location or organization

        :CaseLevel: Integration

        :BZ: 1337947
        """
        # Create env with specified organization and location
        org = make_org()
        locs = [make_location() for _ in range(2)]
        make_environment({
            'organization-ids': org['id'],
            'location-ids': locs[0]['id'],
        })
        # But filter by another location
        results = Environment.list({
            'organization-id': org['id'],
            'location-id': locs[1]['id'],
        })
        self.assertEqual(len(results), 0)

    @tier2
    def test_negative_list_with_org_and_loc_by_name(self):
        """Test Environment List filtering.

        :id: b8382ebb-ffa3-4637-b3b4-444af6c2fe9b

        :expectedresults: Server returns empty result as there is no
            environment associated with location or organization

        :CaseLevel: Integration

        :BZ: 1337947
        """
        # Create env with specified organization and location
        org = make_org()
        locs = [make_location() for _ in range(2)]
        make_environment({
            'organizations': org['name'],
            'locations': locs[0]['name'],
        })
        # But filter by another location
        results = Environment.list({
            'organization': org['name'],
            'location': locs[1]['name'],
        })
        self.assertEqual(len(results), 0)

    @tier2
    def test_negative_list_with_non_existing_org_and_loc_by_id(self):
        """Test Environment List filtering parameters validation.

        :id: 97872953-e1aa-44bd-9ce0-a04bccbc9e94

        :expectedresults: Server returns empty result as there is no
            environment associated with location

        :CaseLevel: Integration

        :BZ: 1337947
        """
        # Create env with specified organization and location
        org = make_org()
        loc = make_location()
        make_environment({
            'organization-ids': org['id'],
            'location-ids': loc['id'],
        })
        # Filter by non-existing location and existing organization
        with self.assertRaises(CLIReturnCodeError):
            Environment.list({
                'organization-id': org['id'],
                'location-id': gen_string('numeric')
            })
        # Filter by non-existing organization and existing location
        with self.assertRaises(CLIReturnCodeError):
            Environment.list({
                'organization-id': gen_string('numeric'),
                'location-id': loc['id']
            })

    @tier2
    def test_negative_list_with_non_existing_org_and_loc_by_name(self):
        """Test Environment List filtering parameters validation.

        :id: 38cb48e3-a836-47d0-b8a8-9acd33a30546

        :expectedresults: Server returns empty result as there is no
            environment associated with location

        :CaseLevel: Integration

        :BZ: 1337947
        """
        # Create env with specified organization and location
        org = make_org()
        loc = make_location()
        make_environment({
            'organizations': org['name'],
            'locations': loc['name'],
        })
        # Filter by non-existing location and existing organization
        with self.assertRaises(CLIReturnCodeError):
            Environment.list({
                'organization': org['name'],
                'location': gen_string('alpha')
            })
        # Filter by non-existing organization and existing location
        with self.assertRaises(CLIReturnCodeError):
            Environment.list({
                'organization': gen_string('alpha'),
                'location': loc['name']
            })

    @tier1
    def test_positive_create_with_name(self):
        """Successfully creates an Environment.

        :id: 3b22f035-ee3a-489e-89c5-e54571584af1

        :expectedresults: Environment is created.

        :CaseImportance: Critical
        """
        for name in valid_environments_list():
            with self.subTest(name):
                environment = make_environment({'name': name})
                self.assertEqual(environment['name'], name)

    @tier1
    def test_negative_create_with_name(self):
        """Don't create an Environment with invalid data.

        :id: 8a4141b0-3bb9-47e5-baca-f9f027086d4c

        :expectedresults: Environment is not created.

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.create({'name': name})

    @tier1
    def test_positive_create_with_loc(self):
        """Check if Environment with Location can be created

        :id: d2187971-86b2-40c9-a93c-66f37691ae2b

        :expectedresults: Environment is created and has new Location assigned


        :CaseImportance: Critical
        """
        new_loc = make_location()
        new_environment = make_environment({
            'location-ids': new_loc['id'],
            'name': gen_string('alpha'),
        })
        self.assertIn(new_loc['name'], new_environment['locations'])

    @tier1
    def test_positive_create_with_org(self):
        """Check if Environment with Organization can be created

        :id: 9fd9d2d5-db46-40a7-b341-41cdbde4356a

        :expectedresults: Environment is created and has new Organization
            assigned


        :CaseImportance: Critical
        """
        new_org = make_org()
        new_environment = make_environment({
            'name': gen_string('alpha'),
            'organization-ids': new_org['id'],
        })
        self.assertIn(new_org['name'], new_environment['organizations'])

    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Create Environment with valid values then delete it
        by ID

        :id: e25af73a-d4ef-4287-83bf-625337d91392

        :expectedresults: Environment is deleted

        :CaseImportance: Critical
        """
        for name in valid_environments_list():
            with self.subTest(name):
                environment = make_environment({'name': name})
                Environment.delete({'id': environment['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Environment.info({'id': environment['id']})

    @tier1
    def test_negative_delete_by_id(self):
        """Create Environment then delete it by wrong ID

        :id: fe77920c-62fd-4e0e-b960-a940a1370d10

        :expectedresults: Environment is not deleted

        :CaseImportance: Critical
        """
        for entity_id in invalid_id_list():
            with self.subTest(entity_id):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.delete({'id': entity_id})

    @tier1
    def test_positive_delete_by_name(self):
        """Delete the environment by its name.

        :id: 48765173-6086-4b91-9da7-594135f68751

        :expectedresults: Environment is deleted.

        :CaseImportance: Critical
        """
        environment = make_environment()
        Environment.delete({'name': environment['name']})
        with self.assertRaises(CLIReturnCodeError):
            Environment.info({'name': environment['name']})

    @tier1
    def test_positive_update_name(self):
        """Update the environment

        :id: 7b34ce64-24be-4b3b-8f7e-1de07daafdd9

        :expectedresults: Environment Update is displayed

        :CaseImportance: Critical
        """
        environment = make_environment()
        for new_name in valid_environments_list():
            with self.subTest(new_name):
                Environment.update({
                    'id': environment['id'],
                    'new-name': new_name,
                })
                environment = Environment.info({'id': environment['id']})
                self.assertEqual(environment['name'], new_name)

    @tier1
    def test_negative_update_name(self):
        """Update the Environment with invalid values

        :id: adc5ad73-0547-40f9-b4d4-649780cfb87a

        :expectedresults: Environment is not updated

        :CaseImportance: Critical
        """
        environment = make_environment()
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                with self.assertRaises(CLIReturnCodeError):
                    Environment.update({
                        'id': environment['id'],
                        'new-name': new_name,
                    })
                result = Environment.info({'id': environment['id']})
                self.assertEqual(environment['name'], result['name'])

    @tier1
    def test_positive_update_loc(self):
        """Update environment location with new value

        :id: d58d6dc5-a820-4c61-bd69-0c631c2d3f2e

        :expectedresults: Environment Update finished and new location is
            assigned


        :CaseImportance: Critical
        """
        old_loc = make_location()
        new_loc = make_location()
        new_env = make_environment({'location-ids': old_loc['id']})
        self.assertIn(old_loc['name'], new_env['locations'])
        Environment.update({
            'location-ids': new_loc['id'],
            'name': new_env['name'],
        })
        new_env = Environment.info({'name': new_env['name']})
        self.assertIn(new_loc['name'], new_env['locations'])
        self.assertNotIn(old_loc['name'], new_env['locations'])

    @tier1
    def test_positive_update_org(self):
        """Update environment organization with new value

        :id: 2c40caf9-95a0-4b87-bd97-0a4448746052

        :expectedresults: Environment Update finished and new organization is
            assigned


        :CaseImportance: Critical
        """
        old_org = make_org()
        new_org = make_org()
        env_name = gen_string('alphanumeric', 10)
        env = make_environment({
            'name': env_name,
            'organization-ids': old_org['id'],
        })
        self.assertIn(old_org['name'], env['organizations'])
        Environment.update({
            'name': env_name,
            'organization-ids': new_org['id']
        })
        env = Environment.info({'name': env_name})
        self.assertIn(new_org['name'], env['organizations'])
        self.assertNotIn(old_org['name'], env['organizations'])

    @tier1
    def test_positive_sc_params_by_id(self):
        """Check if environment sc-param subcommand works passing
        an environment id

        :id: 32de4f0e-7b52-411c-a111-9ed472c3fc34

        :expectedresults: The command runs without raising an error

        :CaseImportance: Critical
        """
        # Override one of the sc-params from puppet class
        sc_params_list = SmartClassParameter.list({
            'environment': self.env['name'],
            'search': u'puppetclass="{0}"'.format(self.puppet_class['name'])
        })
        scp_id = choice(sc_params_list)['id']
        SmartClassParameter.update({'id': scp_id, 'override': 1})
        # Verify that affected sc-param is listed
        env_scparams = Environment.sc_params(
            {'environment-id': self.env['id']})
        self.assertIn(scp_id, [scp['id'] for scp in env_scparams])

    @tier1
    def test_positive_sc_params_by_name(self):
        """Check if environment sc-param subcommand works passing
        an environment name

        :id: e2fdd262-9b09-4252-8a5a-4e578e3b8547

        :expectedresults: The command runs without raising an error

        :CaseImportance: Critical
        """
        sc_params_list = SmartClassParameter.list({
            'environment': self.env['name'],
            'search': u'puppetclass="{0}"'.format(self.puppet_class['name'])
        })
        scp_id = choice(sc_params_list)['id']
        SmartClassParameter.update({'id': scp_id, 'override': 1})
        # Verify that affected sc-param is listed
        env_scparams = Environment.sc_params(
            {'environment': self.env['name']})
        self.assertIn(scp_id, [scp['id'] for scp in env_scparams])
