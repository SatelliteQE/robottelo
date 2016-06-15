# -*- encoding: utf-8 -*-
"""API Tests for foreman discovery feature"""
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

        @Feature: Foreman Discovery

        @Assert: Rule should be created with given name and query
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

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Delete a discovery rule

        @Feature: Foreman Discovery

        @Assert: Rule should be deleted successfully
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

        @Feature: Foreman Discovery

        @Assert: Validation error should be raised
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

        @Feature: Foreman Discovery

        @Assert: Validation error should be raised
        """
        self.discovery_rule.max_count = gen_string('alpha')
        with self.assertRaises(HTTPError):
            self.discovery_rule.create()

    @tier1
    def test_negative_create_with_invalid_priority(self):
        """Create a discovery rule with invalid priority

        @Feature: Foreman Discovery

        @Assert: Validation error should be raised
        """
        self.discovery_rule.priority = gen_string('alpha')
        with self.assertRaises(HTTPError):
            self.discovery_rule.create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Update an existing discovery rule name

        @Feature: Foreman Discovery

        @Assert: User should be able to update the rule
        """
        discovery_rule = self.discovery_rule.create()
        for name in valid_data_list():
            with self.subTest(name):
                discovery_rule.name = name
                discovery_rule = discovery_rule.update(['name'])
                self.assertEqual(discovery_rule.name, name)

    @tier1
    def test_positive_update_search_rule(self):
        """Update an existing discovery search rule

        @Feature: Foreman Discovery

        @Assert: User should be able to update the rule
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

        @Feature: Foreman Discovery

        @Assert: User should be able to update the rule
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

        @Feature: Foreman Discovery

        @Assert: User should be able to update the rule
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

        @Feature: Foreman Discovery

        @Assert: User should be able to update the rule
        """
        discovery_rule = self.discovery_rule.create()
        discovery_rule.hostgroup = entities.HostGroup().create()
        self.assertEqual(
            discovery_rule.hostgroup.id,
            discovery_rule.update(['hostgroup']).hostgroup.id,
        )
