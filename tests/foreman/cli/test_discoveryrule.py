"""Test class for Foreman Discovery Rules

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: DiscoveryPlugin

:Assignee: rplevka

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from fauxfactory import gen_alphanumeric
from fauxfactory import gen_choice
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.discoveryrule import DiscoveryRule
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_discoveryrule
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_user
from robottelo.cli.user import User
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import valid_data_list
from robottelo.test import CLITestCase


class DiscoveryRuleTestCase(CLITestCase):
    """Implements Foreman discovery Rules tests in CLI."""

    @classmethod
    def setUpClass(cls):
        """Tests for discovery rules via Hammer CLI"""
        super().setUpClass()
        cls.org = make_org()
        cls.loc = make_location()
        cls.hostgroup = make_hostgroup(
            {'organization-ids': cls.org['id'], 'location-ids': cls.loc['id']}
        )

    def _make_discoveryrule(self, options=None):
        """Makes a new discovery rule and asserts its success"""
        if options is None:
            options = {}

        searches = [
            'cpu_count = 1',
            'disk_count < 5',
            'memory > 500',
            'model = KVM',
            'Organization = Default_Organization',
            'last_report = Today',
            'subnet =  192.168.100.0',
            'facts.architecture != x86_64',
        ]

        if not any(options.get(key) for key in ['organizations', 'organization-ids']):
            options['organization-ids'] = self.org['id']
        if not any(options.get(key) for key in ['locations', 'locations-ids']):
            options['location-ids'] = self.loc['id']
        if not any(options.get(key) for key in ['hostgroup', 'hostgroup-ids']):
            options['hostgroup-id'] = self.hostgroup['id']
        if options.get('search') is None:
            options['search'] = gen_choice(searches)

        return make_discoveryrule(options)

    @filtered_datapoint
    def invalid_hostnames_list(self):
        """Generates a list of invalid host names.

        :return: Returns the invalid host names list
        """
        return [
            {'name': gen_string('cjk')},
            {'name': gen_string('latin1')},
            {'name': gen_string('numeric')},
            {'name': gen_string('utf8')},
            {'name': '$#@!*'},
            {'name': '" "'},
            {'name': '-1'},
        ]

    @pytest.mark.tier1
    def test_positive_create_with_name(self):
        """Create Discovery Rule using different names

        :id: 066e66bc-c572-4ae9-b458-90daf83bab54

        :expectedresults: Rule should be successfully created

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                rule = self._make_discoveryrule({'name': name})
                self.assertEqual(rule['name'], name)

    @pytest.mark.tier1
    def test_positive_create_with_search(self):
        """Create Discovery Rule using different search queries

        :id: 2383e898-a968-4183-a270-55e9350e0596

        :expectedresults: Rule should be successfully created and has expected
            search value

        :CaseImportance: Critical
        """
        search_query = 'cpu_count = 2'
        rule = self._make_discoveryrule({'search': search_query})
        self.assertEqual(rule['search'], search_query)

    @pytest.mark.tier2
    def test_positive_create_with_hostname(self):
        """Create Discovery Rule using valid hostname

        :id: deee22c3-dcfd-4940-b27c-cca137ec9a92

        :expectedresults: Rule should be successfully created and has expected
            hostname value

        :CaseLevel: Component
        """
        host_name = 'myhost'
        rule = self._make_discoveryrule({'hostname': host_name})
        self.assertEqual(rule['hostname-template'], host_name)

    @pytest.mark.tier1
    def test_positive_create_with_org_loc_id(self):
        """Create discovery rule by associating org and location ids

        :id: bdb4c581-d27a-4d1a-920b-89689e68a57f

        :expectedresults: Rule was created and with given org & location names.

        :BZ: 1377990, 1523221

        :CaseImportance: Critical
        """
        rule = self._make_discoveryrule(
            {
                'hostgroup-id': self.hostgroup['id'],
                'organization-ids': self.org['id'],
                'location-ids': self.loc['id'],
            }
        )
        self.assertIn(self.org['name'], rule['organizations'])
        self.assertIn(self.loc['name'], rule['locations'])

    @pytest.mark.tier2
    def test_positive_create_with_org_loc_name(self):
        """Create discovery rule by associating org and location names

        :id: f0d550ae-16d8-48ec-817e-d2e5b7405b46

        :expectedresults: Rule was created and with given org & location names.

        :BZ: 1377990
        """
        rule = self._make_discoveryrule(
            {
                'hostgroup-id': self.hostgroup['id'],
                'organizations': self.org['name'],
                'locations': self.loc['name'],
            }
        )
        self.assertIn(self.org['name'], rule['organizations'])
        self.assertIn(self.loc['name'], rule['locations'])

    @pytest.mark.tier2
    def test_positive_create_with_hosts_limit(self):
        """Create Discovery Rule providing any number from range 1..100 for
        hosts limit option

        :id: c28422c2-1f6a-4045-b722-f9f9d864e963

        :expectedresults: Rule should be successfully created and has expected
            hosts limit value

        :CaseLevel: Component
        """
        hosts_limit = '5'
        rule = self._make_discoveryrule({'hosts-limit': hosts_limit})
        self.assertEqual(rule['hosts-limit'], hosts_limit)

    @pytest.mark.tier1
    def test_positive_create_with_max_count(self):
        """Create Discovery Rule providing any number from range 1..100 for
        max count option

        :id: 590ca353-d3d7-4700-be34-13de00f46276

        :expectedresults: Rule should be successfully created and has max_count
            set as per given value

        :CaseLevel: Component
        """
        max_count = '10'
        rule = self._make_discoveryrule({'max-count': max_count})
        self.assertEqual(rule['hosts-limit'], max_count)

    @pytest.mark.tier1
    def test_positive_create_with_priority(self):
        """Create Discovery Rule providing any number from range 1..100 for
        priority option

        :id: 8ef58279-0ad3-41a4-b8dd-65594afdb655

        :expectedresults: Rule should be successfully created and has expected
            priority value

        :CaseImportance: Critical
        """
        available = set(range(1, 1000)) - {r['priority'] for r in DiscoveryRule.list()}
        rule_priority = random.sample(available, 1)
        rule = self._make_discoveryrule({'priority': rule_priority[0]})
        self.assertEqual(rule['priority'], str(rule_priority[0]))

    @pytest.mark.tier2
    def test_positive_create_disabled_rule(self):
        """Create Discovery Rule in disabled state

        :id: 8837a0c6-e19a-4c33-8b87-07b6f69dbb0f

        :expectedresults: Disabled rule should be successfully created

        :CaseLevel: Component
        """
        rule = self._make_discoveryrule({'enabled': 'false'})
        self.assertEqual(rule['enabled'], 'false')

    @pytest.mark.tier3
    def test_negative_create_with_invalid_name(self):
        """Create Discovery Rule with invalid names

        :id: a0350dc9-8f5b-4673-be88-a5e35d1f8ca7

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Medium

        :CaseLevel: Component
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_discoveryrule({'name': name})

    @pytest.mark.tier3
    def test_negative_create_with_invalid_hostname(self):
        """Create Discovery Rule with invalid hostname

        :id: 0ae51085-30d0-44f9-9e49-abe928a8a4b7

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Medium

        :CaseLevel: Component

        :BZ: 1378427
        """
        for name in self.invalid_hostnames_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_discoveryrule({'hostname': name})

    @pytest.mark.tier3
    def test_negative_create_with_too_long_limit(self):
        """Create Discovery Rule with too long host limit value

        :id: 12dbb023-c963-4ead-a81e-ad53033de947

        :expectedresults: Validation error should be raised and rule should not
            be created

        :CaseImportance: Medium
        """
        with self.assertRaises(CLIFactoryError):
            self._make_discoveryrule({'hosts-limit': '9999999999'})

    @pytest.mark.tier1
    def test_negative_create_with_same_name(self):
        """Create Discovery Rule with name that already exists

        :id: 0906cf64-ed0b-49af-844f-1af22f81ab94

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        self._make_discoveryrule({'name': name})
        with self.assertRaises(CLIFactoryError):
            self._make_discoveryrule({'name': name})

    @pytest.mark.tier1
    def test_positive_delete(self):
        """Delete existing Discovery Rule

        :id: c9b88a94-13c4-496f-a5c1-c088187250dc

        :expectedresults: Rule should be successfully deleted

        :CaseImportance: Critical
        """
        rule = self._make_discoveryrule()
        DiscoveryRule.delete({'id': rule['id']})
        with self.assertRaises(CLIReturnCodeError):
            DiscoveryRule.info({'id': rule['id']})

    @pytest.mark.tier3
    def test_positive_update_name(self):
        """Update discovery rule name

        :id: 1045e2c4-e1f7-42c9-95f7-488fc79bf70b

        :expectedresults: Rule name is updated

        :CaseLevel: Component

        :CaseImportance: Medium
        """
        rule = self._make_discoveryrule()
        new_name = gen_string('numeric')
        DiscoveryRule.update({'id': rule['id'], 'name': new_name})
        rule = DiscoveryRule.info({'id': rule['id']})
        self.assertEqual(rule['name'], new_name)

    @pytest.mark.tier2
    def test_positive_update_org_loc_by_id(self):
        """Update org and location of selected discovery rule using org/loc ids

        :id: 26da79aa-30e5-4052-98ae-141de071a68a

        :expectedresults: Rule was updated and with given org & location.

        :BZ: 1377990

        :CaseLevel: Component
        """
        new_org = make_org()
        new_loc = make_location()
        new_hostgroup = make_hostgroup(
            {'organization-ids': new_org['id'], 'location-ids': new_loc['id']}
        )
        rule = self._make_discoveryrule()
        DiscoveryRule.update(
            {
                'id': rule['id'],
                'organization-ids': new_org['id'],
                'location-ids': new_loc['id'],
                'hostgroup-id': new_hostgroup['id'],
            }
        )
        rule = DiscoveryRule.info({'id': rule['id']})
        self.assertIn(new_org['name'], rule['organizations'])
        self.assertIn(new_loc['name'], rule['locations'])

    @pytest.mark.tier3
    def test_positive_update_org_loc_by_name(self):
        """Update org and location of selected discovery rule using org/loc
        names

        :id: 7a5d61ac-6a2d-48f6-a00d-df437a7dc3c4

        :expectedresults: Rule was updated and with given org & location.

        :BZ: 1377990

        :CaseLevel: Component

        :CaseImportance: Medium
        """
        new_org = make_org()
        new_loc = make_location()
        new_hostgroup = make_hostgroup(
            {'organization-ids': new_org['id'], 'location-ids': new_loc['id']}
        )
        rule = self._make_discoveryrule()
        DiscoveryRule.update(
            {
                'id': rule['id'],
                'organizations': new_org['name'],
                'locations': new_loc['name'],
                'hostgroup-id': new_hostgroup['id'],
            }
        )
        rule = DiscoveryRule.info({'id': rule['id']})
        self.assertIn(new_org['name'], rule['organizations'])
        self.assertIn(new_loc['name'], rule['locations'])

    @pytest.mark.tier2
    def test_positive_update_query(self):
        """Update discovery rule search query

        :id: 86943095-acc5-40ff-8e3c-88c76b36333d

        :expectedresults: Rule search field is updated

        :CaseLevel: Component
        """
        rule = self._make_discoveryrule()
        new_query = 'model = KVM'
        DiscoveryRule.update({'id': rule['id'], 'search': new_query})
        rule = DiscoveryRule.info({'id': rule['id']})
        self.assertEqual(rule['search'], new_query)

    @pytest.mark.tier2
    def test_positive_update_hostgroup(self):
        """Update discovery rule host group

        :id: 07992a3f-2aa9-4e45-b2e8-ef3d2f255292

        :expectedresults: Rule host group is updated

        :CaseLevel: Component
        """
        new_hostgroup = make_hostgroup({'organization-ids': self.org['id']})
        rule = self._make_discoveryrule()
        DiscoveryRule.update({'id': rule['id'], 'hostgroup': new_hostgroup['name']})
        rule = DiscoveryRule.info({'id': rule['id']})
        self.assertEqual(rule['host-group'], new_hostgroup['name'])

    @pytest.mark.tier2
    def test_positive_update_hostname(self):
        """Update discovery rule hostname value

        :id: 4c123488-92df-42f6-afe3-8a88cd90ffc2

        :expectedresults: Rule host name is updated

        :CaseLevel: Component
        """
        new_hostname = gen_string('alpha')
        rule = self._make_discoveryrule()
        DiscoveryRule.update({'id': rule['id'], 'hostname': new_hostname})
        rule = DiscoveryRule.info({'id': rule['id']})
        self.assertEqual(rule['hostname-template'], new_hostname)

    @pytest.mark.tier2
    def test_positive_update_limit(self):
        """Update discovery rule limit value

        :id: efa6f5bc-4d56-4449-90f5-330affbcfb09

        :expectedresults: Rule host limit field is updated

        :CaseLevel: Component
        """
        rule = self._make_discoveryrule({'hosts-limit': '5'})
        new_limit = '10'
        DiscoveryRule.update({'id': rule['id'], 'hosts-limit': new_limit})
        rule = DiscoveryRule.info({'id': rule['id']})
        self.assertEqual(rule['hosts-limit'], new_limit)

    @pytest.mark.tier1
    def test_positive_update_priority(self):
        """Update discovery rule priority value

        :id: 0543cc73-c692-4bbf-818b-37353ec98986

        :expectedresults: Rule priority is updated

        :CaseImportance: Critical
        """
        available = set(range(1, 1000)) - {r['priority'] for r in DiscoveryRule.list()}
        rule_priority = random.sample(available, 1)
        rule = self._make_discoveryrule({'priority': rule_priority[0]})
        self.assertEqual(rule['priority'], str(rule_priority[0]))
        available = set(range(1, 1000)) - {r['priority'] for r in DiscoveryRule.list()}
        rule_priority = random.sample(available, 1)
        DiscoveryRule.update({'id': rule['id'], 'priority': rule_priority[0]})
        rule = DiscoveryRule.info({'id': rule['id']})
        self.assertEqual(rule['priority'], str(rule_priority[0]))

    @pytest.mark.tier1
    def test_positive_update_disable_enable(self):
        """Update discovery rule enabled state. (Disabled->Enabled)

        :id: 64e8b21b-2ab0-49c3-a12d-02dbdb36647a

        :expectedresults: Rule is successfully enabled

        :CaseImportance: Critical
        """
        rule = self._make_discoveryrule({'enabled': 'false'})
        self.assertEqual(rule['enabled'], 'false')
        DiscoveryRule.update({'id': rule['id'], 'enabled': 'true'})
        rule = DiscoveryRule.info({'id': rule['id']})
        self.assertEqual(rule['enabled'], 'true')

    @pytest.mark.tier3
    def test_negative_update_name(self):
        """Update discovery rule name using invalid names only

        :id: 8293cc6a-d983-460a-b76e-221ad02b54b7

        :expectedresults: Rule name is not updated

        :CaseLevel: Component

        :CaseImportance: Medium
        """
        rule = self._make_discoveryrule()
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIReturnCodeError):
                    DiscoveryRule.update({'id': rule['id'], 'name': name})

    @pytest.mark.tier3
    def test_negative_update_hostname(self):
        """Update discovery rule host name using number as a value

        :id: c382dbc7-9509-4060-9038-1617f7fef038

        :expectedresults: Rule host name is not updated

        :CaseImportance: Medium

        :CaseLevel: Component
        """
        rule = self._make_discoveryrule()
        with self.assertRaises(CLIReturnCodeError):
            DiscoveryRule.update({'id': rule['id'], 'hostname': '$#@!*'})

    @pytest.mark.tier3
    def test_negative_update_limit(self):
        """Update discovery rule host limit using invalid values

        :id: e3257d8a-91b9-406f-bd74-0fd1fb05bb77

        :expectedresults: Rule host limit is not updated

        :CaseLevel: Component

        :CaseImportance: Medium
        """
        rule = self._make_discoveryrule()
        host_limit = gen_string('alpha')
        with self.assertRaises(CLIReturnCodeError):
            DiscoveryRule.update({'id': rule['id'], 'hosts-limit': host_limit})

    @pytest.mark.tier3
    def test_negative_update_priority(self):
        """Update discovery rule priority using invalid values

        :id: 0778dd00-aa19-4062-bdf3-752e1b546ec2

        :expectedresults: Rule priority is not updated

        :CaseLevel: Component

        :CaseImportance: Medium
        """
        rule = self._make_discoveryrule()
        priority = gen_string('alpha')
        with self.assertRaises(CLIReturnCodeError):
            DiscoveryRule.update({'id': rule['id'], 'priority': priority})


class DiscoveryRuleRoleTestCase(CLITestCase):
    """Implements Foreman discovery Rules tests along with roles from CLI."""

    @classmethod
    def setUpClass(cls):
        """Tests for discovery rules via Hammer CLI"""
        super().setUpClass()
        cls.org = make_org()
        cls.loc = make_location()
        cls.hostgroup = make_hostgroup(
            {'organization-ids': cls.org['id'], 'location-ids': cls.loc['id']}
        )
        cls.password = gen_alphanumeric()
        cls.user = make_user(
            {
                'organization-ids': cls.org['id'],
                'location-ids': cls.loc['id'],
                'password': cls.password,
            }
        )
        cls.user['password'] = cls.password
        User.add_role({'login': cls.user['login'], 'role': 'Discovery Manager'})
        cls.user_reader = make_user(
            {
                'organization-ids': cls.org['id'],
                'location-ids': cls.loc['id'],
                'password': cls.password,
            }
        )
        cls.user_reader['password'] = cls.password
        User.add_role({'login': cls.user_reader['login'], 'role': 'Discovery Reader'})

    @pytest.mark.tier2
    def test_positive_create_rule_with_non_admin_user(self):
        """Create rule with non-admin user by associating discovery_manager role

        :id: 056535aa-3338-4c1e-8a4b-ebfc8bd6e456

        :expectedresults: Rule should be created successfully.

        :CaseLevel: Integration
        """
        rule_name = gen_string('alpha')
        rule = DiscoveryRule.with_user(self.user['login'], self.user['password']).create(
            {
                'name': rule_name,
                'search': 'cpu_count = 5',
                'organizations': self.org['name'],
                'locations': self.loc['name'],
                'hostgroup-id': self.hostgroup['id'],
            }
        )
        rule = DiscoveryRule.with_user(self.user['login'], self.user['password']).info(
            {'id': rule['id']}
        )
        self.assertEqual(rule['name'], rule_name)

    @pytest.mark.tier2
    def test_positive_delete_rule_with_non_admin_user(self):
        """Delete rule with non-admin user by associating discovery_manager role

        :id: 87ab969b-7d92-478d-a5c0-1c0d50e9bdd6

        :expectedresults: Rule should be deleted successfully.

        :CaseLevel: Integration
        """
        rule_name = gen_string('alpha')
        rule = DiscoveryRule.with_user(self.user['login'], self.user['password']).create(
            {
                'name': rule_name,
                'search': 'cpu_count = 5',
                'organizations': self.org['name'],
                'locations': self.loc['name'],
                'hostgroup-id': self.hostgroup['id'],
            }
        )
        rule = DiscoveryRule.with_user(self.user['login'], self.user['password']).info(
            {'id': rule['id']}
        )
        DiscoveryRule.with_user(self.user['login'], self.user['password']).delete(
            {'id': rule['id']}
        )
        with self.assertRaises(CLIReturnCodeError):
            DiscoveryRule.info({'id': rule['id']})

    @pytest.mark.tier2
    def test_positive_view_existing_rule_with_non_admin_user(self):
        """Existing rule should be viewed to non-admin user by associating
        discovery_reader role.

        :id: 7b1d90b9-fc2d-4ccb-93d3-605c2da876f7

        :Steps:

            1. create a rule with admin user
            2. create a non-admin user and assign 'Discovery Reader' role
            3. Login with non-admin user

        :expectedresults: Rule should be visible to non-admin user.

        :CaseLevel: Integration
        """
        rule_name = gen_string('alpha')
        rule = make_discoveryrule(
            {
                'name': rule_name,
                'enabled': 'false',
                'search': "last_report = Today",
                'organizations': self.org['name'],
                'locations': self.loc['name'],
                'hostgroup-id': self.hostgroup['id'],
            }
        )
        rule = DiscoveryRule.with_user(
            self.user_reader['login'], self.user_reader['password']
        ).info({'id': rule['id']})
        self.assertEqual(rule['name'], rule_name)

    @pytest.mark.tier2
    def test_negative_delete_rule_with_non_admin_user(self):
        """Delete rule with non-admin user by associating discovery_reader role

        :id: f7f9569b-916e-46f3-bd89-a05e33483741

        :expectedresults: User should validation error and rule should not be
            deleted successfully.

        :CaseLevel: Integration
        """
        rule = make_discoveryrule(
            {
                'enabled': 'false',
                'search': "last_report = Today",
                'organizations': self.org['name'],
                'locations': self.loc['name'],
                'hostgroup-id': self.hostgroup['id'],
            }
        )
        rule = DiscoveryRule.with_user(
            self.user_reader['login'], self.user_reader['password']
        ).info({'id': rule['id']})
        with self.assertRaises(CLIReturnCodeError):
            DiscoveryRule.with_user(
                self.user_reader['login'], self.user_reader['password']
            ).delete({'id': rule['id']})
