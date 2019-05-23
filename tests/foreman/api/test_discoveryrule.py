# -*- encoding: utf-8 -*-
"""API Tests for foreman discovery feature

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseComponent: DiscoveryPlugin

:TestType: Functional

:CaseLevel: Acceptance

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_choice, gen_integer, gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_only_on, tier1, tier2
from robottelo.test import APITestCase


class DiscoveryRuleTestCase(APITestCase):
    """Tests for ``katello/api/v2/discovery_rules``."""

    @classmethod
    def setUpClass(cls):
        """Create a hostgroup which can be re-used in tests."""
        super(DiscoveryRuleTestCase, cls).setUpClass()
        cls.hostgroup = entities.HostGroup().create()

    def setUp(self):
        """Instantiate a ``DiscoveryRule`` and give it several default attrs.

        Instantiate a ``DiscoveryRule`` object in memory, but do not create it
        on the Satellite server. This allows the object to be customized. Save
        it as ``self.discovery_rule``, set its ``hostgroup`` and ``search_``
        fields, and give its ``hostname`` field a default value.
        """
        super(DiscoveryRuleTestCase, self).setUp()
        searches = [
            'CPU_Count = 1',
            'disk_count < 5',
            'memory > 500',
            'model = KVM',
            'Organization = Default_Organization',
        ]
        self.discovery_rule = entities.DiscoveryRule(
            hostgroup=self.hostgroup,
            search_=gen_choice(searches),
        )
        self.discovery_rule._fields['hostname'].default = (
            'myhost-<%= rand(99999) %>'
        )

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create a new discovery rule.

        Set query as (e.g CPU_Count = 1)

        :id: b8ae7a80-b9a8-4924-808c-482a2b4102c4

        :expectedresults: Rule should be created with given name and query

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                self.discovery_rule.name = name
                discovery_rule = self.discovery_rule.create()
                self.assertEqual(self.discovery_rule.name, discovery_rule.name)
                self.assertEqual(
                    self.discovery_rule.search_,
                    discovery_rule.search_,
                )

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_org_loc(self):
        """Create discovery rule by associating org and location

        :id: 121e0a30-8a24-47d7-974d-998886ed1ea7

        :expectedresults: Rule was created and with given org & location.

        :CaseLevel: Component
        """
        org = entities.Organization().create()
        loc = entities.Location().create()
        hostgroup = entities.HostGroup(organization=[org]).create()
        discovery_rule = entities.DiscoveryRule(
            hostgroup=hostgroup,
            search_='cpu_count = 1',
            organization=[org],
            location=[loc],
        ).create()
        self.assertEqual(org.name, discovery_rule.organization[0].read().name)
        self.assertEqual(loc.name, discovery_rule.location[0].read().name)

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Delete a discovery rule

        :id: 9fdba953-dcc7-4532-9204-17a45b0d9e05

        :expectedresults: Rule should be deleted successfully

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                self.discovery_rule.name = name
                discovery_rule = self.discovery_rule.create()
                discovery_rule.delete()
                with self.assertRaises(HTTPError):
                    discovery_rule.read()

    @tier1
    def test_negative_create_with_too_long_name(self):
        """Create a discovery rule with more than 255 char in name

        :id: 415379b7-0134-40b9-adb1-2fe0adb1ac36

        :expectedresults: Validation error should be raised
        """
        for name in (
                gen_string(str_type, 256)
                for str_type in ('alpha', 'numeric', 'alphanumeric')):
            with self.subTest(name):
                self.discovery_rule.name = name
                with self.assertRaises(HTTPError):
                    self.discovery_rule.create()

    @tier1
    def test_negative_create_with_invalid_host_limit(self):
        """Create a discovery rule with invalid host limit

        :id: 84503d8d-86f6-49bf-ab97-eff418d3e3d0

        :expectedresults: Validation error should be raised
        """
        self.discovery_rule.max_count = gen_string('alpha')
        with self.assertRaises(HTTPError):
            self.discovery_rule.create()

    @tier1
    def test_negative_create_with_invalid_priority(self):
        """Create a discovery rule with invalid priority

        :id: 4ec7d76a-22ba-4c3e-952c-667a6f0a5728

        :expectedresults: Validation error should be raised
        """
        self.discovery_rule.priority = gen_string('alpha')
        with self.assertRaises(HTTPError):
            self.discovery_rule.create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Update an existing discovery rule name

        :id: 769c0739-538b-4451-af7b-deb2ecd3dc0d

        :expectedresults: User should be able to update the rule

        :CaseImportance: Critical
        """
        discovery_rule = self.discovery_rule.create()
        for name in valid_data_list():
            with self.subTest(name):
                discovery_rule.name = name
                discovery_rule = discovery_rule.update(['name'])
                self.assertEqual(discovery_rule.name, name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_org_loc(self):
        """Update org and location of selected discovery rule

        :id: 0f8ec302-f9de-4713-87b7-0f1aca515149

        :expectedresults: Rule was updated and with given org & location
        """
        org = entities.Organization().create()
        loc = entities.Location().create()
        hostgroup = entities.HostGroup(organization=[org]).create()
        discovery_rule = self.discovery_rule.create()
        discovery_rule.organization = [org]
        discovery_rule.location = [loc]
        discovery_rule.hostgroup = hostgroup
        discovery_rule = discovery_rule.update([
            'organization',
            'location',
            'hostgroup',
        ])
        self.assertEqual(org.name, discovery_rule.organization[0].read().name)
        self.assertEqual(loc.name, discovery_rule.location[0].read().name)

    @tier1
    def test_positive_update_search_rule(self):
        """Update an existing discovery search rule

        :id: 2c5ecb7e-87bc-4980-9620-7ae00e3f360e

        :expectedresults: User should be able to update the rule
        """
        discovery_rule = self.discovery_rule.create()
        discovery_rule.search_ = 'Location = Default_Location'
        self.assertEqual(
            discovery_rule.search_,
            discovery_rule.update(['search_']).search_,
        )

    @tier1
    def test_positive_update_host_limit(self):
        """Update an existing rule with valid host limit.

        :id: 33084060-2866-46b9-bfab-23d91aea73d8

        :expectedresults: User should be able to update the rule
        """
        discovery_rule = self.discovery_rule.create()
        discovery_rule.max_count = gen_integer(1, 100)
        self.assertEqual(
            discovery_rule.max_count,
            discovery_rule.update(['max_count']).max_count,
        )

    @tier1
    def test_positive_disable(self):
        """Disable an existing enabled discovery rule.

        :id: 330aa943-167b-46dd-b434-1a6e5fe8f283

        :expectedresults: User should be able to update the rule
        """
        discovery_rule = self.discovery_rule.create()
        self.assertEqual(discovery_rule.enabled, True)
        discovery_rule.enabled = False
        self.assertEqual(
            discovery_rule.enabled,
            discovery_rule.update(['enabled']).enabled,
        )

    @tier2
    def test_positive_update_rule_hostgroup(self):
        """Update host group of an existing rule.

        :id: dcf15e83-c529-462a-b5da-fd45bb457fde

        :expectedresults: User should be able to update the rule

        :CaseLevel: Integration
        """
        discovery_rule = self.discovery_rule.create()
        discovery_rule.hostgroup = entities.HostGroup().create()
        self.assertEqual(
            discovery_rule.hostgroup.id,
            discovery_rule.update(['hostgroup']).hostgroup.id,
        )
