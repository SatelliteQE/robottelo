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
from fauxfactory import gen_choice
from fauxfactory import gen_integer
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.datafactory import valid_data_list
from robottelo.decorators import tier1
from robottelo.test import APITestCase


class DiscoveryRuleTestCase(APITestCase):
    """Tests for ``katello/api/v2/discovery_rules``."""

    @tier1
    def test_positive_end_to_end(self):
        """Create a new discovery rule with several attributes, update them
        and delete the rule itself.

        :id: 25366930-b7f4-4db8-a9c3-a470fe4f3583

        :expectedresults: Rule should be created, modified and deleted successfully
        with given attributes.

        :CaseImportance: Critical
        """
        searches = [
            'CPU_Count = 1',
            'disk_count < 5',
            'memory > 500',
            'model = KVM',
            'Organization = Default_Organization',
        ]
        name = gen_choice(valid_data_list())

        with self.subTest(name):
            # Create discovery rule
            search = gen_choice(searches)
            hostname = 'myhost-<%= rand(99999) %>'
            org = entities.Organization().create()
            loc = entities.Location().create()
            hostgroup = entities.HostGroup(organization=[org]).create()
            discovery_rule = entities.DiscoveryRule(
                name=name, search_=search, hostname=hostname,
                organization=[org], location=[loc], hostgroup=hostgroup
            ).create()
            self.assertEqual(name, discovery_rule.name)
            self.assertEqual(hostname, discovery_rule.hostname)
            self.assertEqual(search, discovery_rule.search_)
            self.assertEqual(org.name, discovery_rule.organization[0].read().name)
            self.assertEqual(loc.name, discovery_rule.location[0].read().name)
            self.assertEqual(True, discovery_rule.enabled)
            # Update discovery rule
            name = gen_choice(valid_data_list())
            search = 'Location = Default_Location'
            org = entities.Organization().create()
            loc = entities.Location().create()
            hostgroup = entities.HostGroup(organization=[org]).create()
            max_count = gen_integer(1, 100)
            enabled = False
            discovery_rule.name = name
            discovery_rule.search_ = search
            discovery_rule.organization = [org]
            discovery_rule.location = [loc]
            discovery_rule.hostgroup = hostgroup
            discovery_rule.max_count = max_count
            discovery_rule.enabled = enabled
            discovery_rule = discovery_rule.update(
                [
                    'name', 'organization', 'location', 'hostgroup',
                    'search_', 'max_count', 'enabled'
                ]
            )
            self.assertEqual(name, discovery_rule.name)
            self.assertEqual(search, discovery_rule.search_)
            self.assertEqual(org.name, discovery_rule.organization[0].read().name)
            self.assertEqual(loc.name, discovery_rule.location[0].read().name)
            self.assertEqual(hostgroup.id, discovery_rule.hostgroup.id)
            self.assertEqual(max_count, discovery_rule.max_count)
            self.assertEqual(enabled, discovery_rule.enabled)
            # Delete discovery rule
            discovery_rule.delete()
            with self.assertRaises(HTTPError):
                discovery_rule.read()

    @tier1
    def test_negative_create_with_invalid_host_limit_and_priority(self):
        """Create a discovery rule with invalid host limit and priority

        :id: e3c7acb1-ac56-496b-ac04-2a83f66ec290

        :expectedresults: Validation error should be raised
        """
        with self.assertRaises(HTTPError):
            entities.DiscoveryRule(max_count=gen_string('alpha')).create()
        with self.assertRaises(HTTPError):
            entities.DiscoveryRule(priority=gen_string('alpha')).create()
