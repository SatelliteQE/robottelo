# -*- encoding: utf-8 -*-
"""API Tests for foreman discovery feature"""
from fauxfactory import gen_choice, gen_integer, gen_string
from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_only_on
from robottelo.test import APITestCase


class DiscoveryRule(APITestCase):
    """Tests for ``katello/api/v2/discovery_rules``."""

    @classmethod
    def setUpClass(cls):
        """Create a hostgroup which can be re-used in tests."""
        super(DiscoveryRule, cls).setUpClass()
        cls.hostgroup = entities.HostGroup().create()

    def setUp(self):
        """Instantiate a ``DiscoveryRule`` and give it several default attrs.

        Instantiate a ``DiscoveryRule`` object in memory, but do not create it
        on the Satellite server. This allows the object to be customized. Save
        it as ``self.discovery_rule``, set its ``hostgroup`` and ``search_``
        fields, and give its ``hostname`` field a default value.

        """
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

    @run_only_on('sat')
    def test_create_discovery_rule_basic(self):
        """@Test: Create a new discovery rule.

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

    @run_only_on('sat')
    def test_delete_discovery_rule(self):
        """@Test: Delete a discovery rule

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

    def test_create_rule_with_invalid_name(self):
        """@Test: Create a discovery rule with more than 255 char in name

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

    def test_create_rule_with_invalid_host_limit(self):
        """@Test: Create a discovery rule with invalid host limit

        @Feature: Foreman Discovery

        @Assert: Validation error should be raised

        """
        self.discovery_rule.max_count = gen_string('alpha')
        with self.assertRaises(HTTPError):
            self.discovery_rule.create()

    def test_create_rule_with_invalid_priority(self):
        """@Test: Create a discovery rule with invalid priority

        @Feature: Foreman Discovery

        @Assert: Validation error should be raised

        """
        self.discovery_rule.priority = gen_string('alpha')
        with self.assertRaises(HTTPError):
            self.discovery_rule.create()

    @run_only_on('sat')
    def test_update_discovery_rule_name(self):
        """@Test: Update an existing discovery rule name

        @Feature: Foreman Discovery

        @Assert: User should be able to update the rule

        """
        discovery_rule = self.discovery_rule.create()
        for name in valid_data_list():
            with self.subTest(name):
                discovery_rule.name = name
                discovery_rule = discovery_rule.update(['name'])
                self.assertEqual(discovery_rule.name, name)

    def test_update_search_rule(self):
        """@Test: Update an existing discovery search rule

        @Feature: Foreman Discovery

        @Assert: User should be able to update the rule

        """
        discovery_rule = self.discovery_rule.create()
        discovery_rule.search_ = 'Location = Default_Location'
        self.assertEqual(
            discovery_rule.search_,
            discovery_rule.update(['search_']).search_,
        )

    def test_update_host_limit(self):
        """@Test: Update an existing rule with valid host limit.

        @Feature: Foreman Discovery

        @Assert: User should be able to update the rule

        """
        discovery_rule = self.discovery_rule.create()
        discovery_rule.max_count = gen_integer(1, 100)
        self.assertEqual(
            discovery_rule.max_count,
            discovery_rule.update(['max_count']).max_count,
        )

    def test_disable_rule(self):
        """@Test: Disable an existing enabled discovery rule.

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

    def test_update_rule_hostgroup(self):
        """@Test: Update host group of an existing rule.

        @Feature: Foreman Discovery

        @Assert: User should be able to update the rule

        """
        discovery_rule = self.discovery_rule.create()
        discovery_rule.hostgroup = entities.HostGroup().create()
        self.assertEqual(
            discovery_rule.hostgroup.id,
            discovery_rule.update(['hostgroup']).hostgroup.id,
        )
