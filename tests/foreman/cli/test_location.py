# -*- encoding: utf-8 -*-
"""Test class for Location CLI

:Requirement: Location

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: OrganizationsLocations

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from robottelo.cleanup import capsule_cleanup, location_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_location,
    make_medium,
    make_proxy,
)
from nailgun import entities
from robottelo.cli.location import Location
from robottelo.decorators import (
    run_in_one_thread,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import CLITestCase


class LocationTestCase(CLITestCase):
    """Tests for Location via Hammer CLI"""

    def _make_proxy(self, options=None):
        """Create a Proxy and register the cleanup function"""
        proxy = make_proxy(options=options)
        # Add capsule to cleanup list
        self.addCleanup(capsule_cleanup, proxy['id'])
        return proxy

    @classmethod
    def setUpClass(cls):
        """Set up reusable entities for tests."""
        super(LocationTestCase, cls).setUpClass()
        cls.subnet = entities.Subnet().create()
        cls.env = entities.Environment().create()
        cls.env2 = entities.Environment().create()
        cls.domain = entities.Domain().create()
        cls.domain2 = entities.Domain().create()
        cls.medium = make_medium()
        cls.host_group = entities.HostGroup().create()
        cls.host_group2 = entities.HostGroup().create()
        cls.host_group3 = entities.HostGroup().create()
        cls.comp_resource = entities.LibvirtComputeResource().create()
        cls.template = entities.ConfigTemplate().create()
        cls.user = entities.User().create()

    @tier2
    @upgrade
    def test_positive_create_update_delete(self):
        """Create new location with attributes, update and delete it

        :id: e1844d9d-ec4a-44b3-9743-e932cc70020d

        :bz: 1233612, 1234287

        :expectedresults: Location created successfully and has expected and
            correct attributes. Attributes can be updated and the location
            can be deleted.

        :CaseImportance: Critical
        """
        # Create
        description = gen_string('utf8')
        loc = make_location({
            'description': description,
            'subnet-ids': self.subnet.id,
            'puppet-environment-ids': self.env.id,
            'domain-ids': [self.domain.id, self.domain2.id],
            'hostgroup-ids': [self.host_group.id, self.host_group2.id],
            'medium-ids': self.medium["id"],
            'compute-resource-ids': self.comp_resource.id,
            'config-templates': self.template.name,
            'user-ids': self.user.id
        })

        self.assertEqual(loc['description'], description)
        self.assertIn(self.subnet.name, loc['subnets'][0])
        self.assertIn(self.subnet.network, loc['subnets'][0])
        self.assertEqual(loc['environments'][0], self.env.name)
        self.assertIn(self.domain.name, loc['domains'])
        self.assertIn(self.domain2.name, loc['domains'])
        self.assertIn(self.host_group.name, loc['hostgroups'])
        self.assertIn(self.host_group2.name, loc['hostgroups'])
        self.assertGreater(len(loc['installation-media']), 0)
        self.assertEqual(loc['installation-media'][0], self.medium['name'])
        self.assertEqual(loc['compute-resources'][0], self.comp_resource.name)
        self.assertGreaterEqual(len(loc['templates']), 1)
        # templates are returned as `name (type)` or just `name` if type is unset
        if self.template.template_kind is None:
            template_search = self.template.name
        else:
            template_search = '{0} ({1})'.format(self.template.name, self.template.template_kind)
        self.assertIn(template_search, loc['templates'])
        self.assertEqual(loc['users'][0], self.user.login)

        # Update
        Location.update({
            'id': loc['id'],
            'puppet-environment-ids': [self.env.id, self.env2.id],
            'domain-ids': self.domain2.id,
            'hostgroup-ids': [self.host_group2.id, self.host_group3.id],
        })
        loc = Location.info({'id': loc['id']})
        self.assertIn(self.host_group2.name, loc['hostgroups'])
        self.assertIn(self.host_group3.name, loc['hostgroups'])
        self.assertEqual(loc['domains'][0], self.domain2.name)
        self.assertIn(self.env.name, loc['environments'])
        self.assertIn(self.env2.name, loc['environments'])

        # Delete
        Location.delete({'id': loc['id']})
        with self.assertRaises(CLIReturnCodeError):
            Location.info({'id': loc['id']})

    @tier1
    def test_positive_create_with_parent(self):
        """Create new location with parent location specified

        :id: 49b34733-103a-4fee-818b-6a3386253af1

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location created successfully and has correct and
            expected parent location set

        """
        parent_loc = make_location()
        loc = make_location({'parent-id': parent_loc['id']})
        self.assertEqual(loc['parent'], parent_loc['name'])

    @tier1
    def test_negative_create_with_same_name(self):
        """Try to create location using same name twice

        :id: 4fbaea41-9775-40a2-85a5-4dc05cc95134

        :expectedresults: Second location is not created

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        loc = make_location({'name': name})
        self.assertEqual(loc['name'], name)
        with self.assertRaises(CLIFactoryError):
            make_location({'name': name})

    @tier1
    def test_negative_create_with_user_by_name(self):
        """Try to create new location with incorrect user assigned to it
        Use user login as a parameter

        :id: fa892edf-8c42-44dc-8f36-bed50798b59b

        :expectedresults: Location is not created

        :CaseImportance: Critical
        """
        with self.assertRaises(CLIFactoryError):
            make_location({'users': gen_string('utf8', 80)})

    @run_in_one_thread
    @tier2
    @upgrade
    def test_positive_add_and_remove_capsule(self):
        """Add a capsule to location and remove it

        :id: 15e3c1e6-4fa3-4965-8808-a9ba01d1c050

        :expectedresults: Capsule is added to the org

        :bz: 1398695

        :CaseLevel: Integration
        """
        loc = make_location()
        proxy = self._make_proxy()
        self.addCleanup(location_cleanup, loc['id'])

        Location.add_smart_proxy({
            'name': loc['name'],
            'smart-proxy-id': proxy['id'],
        })
        loc = Location.info({'name': loc['name']})
        self.assertIn(proxy['name'], loc['smart-proxies'])
        Location.remove_smart_proxy({
            'name': loc['name'],
            'smart-proxy': proxy['name'],
        })
        loc = Location.info({'name': loc['name']})
        self.assertNotIn(proxy['name'], loc['smart-proxies'])

    @tier1
    def test_positive_add_update_remove_parameter(self):
        """Add, update and remove parameter to location

        :id: 61b564f2-a42a-48de-833d-bec3a127d0f5

        :expectedresults: Parameter is added to the location

        :CaseImportance: Critical
        """
        # Create
        param_name = gen_string('alpha')
        param_value = gen_string('alpha')
        param_new_value = gen_string('alpha')
        location = make_location()
        Location.set_parameter({
            'name': param_name,
            'value': param_value,
            'location-id': location['id'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 1)
        self.assertEqual(
            param_value, location['parameters'][param_name.lower()])

        # Update
        Location.set_parameter({
            'name': param_name,
            'value': param_new_value,
            'location': location['name'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 1)
        self.assertEqual(
            param_new_value, location['parameters'][param_name.lower()])

        # Remove
        Location.delete_parameter({
            'name': param_name,
            'location': location['name'],
        })
        location = Location.info({'id': location['id']})
        self.assertEqual(len(location['parameters']), 0)
        self.assertNotIn(param_name.lower(), location['parameters'])

    @tier2
    def test_positive_update_parent(self):
        """Update location's parent location

        :id: 34522d1a-1190-48d8-9285-fc9a9bcf6c6a

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location was updated successfully

        :CaseImportance: High
        """
        parent_loc = make_location()
        loc = make_location({'parent-id': parent_loc['id']})
        new_parent_loc = make_location()
        Location.update({
            'id': loc['id'],
            'parent-id': new_parent_loc['id'],
        })
        loc = Location.info({'id': loc['id']})
        self.assertEqual(loc['parent'], new_parent_loc['name'])

    @tier1
    def test_negative_update_parent_with_child(self):
        """Attempt to set child location as a parent and vice versa

        :id: fd4cb1cf-377f-4b48-b7f4-d4f6ca56f544

        :customerscenario: true

        :BZ: 1299802

        :expectedresults: Location was not updated

        :CaseImportance: High
        """
        parent_loc = make_location()
        loc = make_location({'parent-id': parent_loc['id']})

        # set parent as child
        with self.assertRaises(CLIReturnCodeError):
            Location.update({
                'id': parent_loc['id'],
                'parent-id': loc['id'],
            })
        parent_loc = Location.info({'id': parent_loc['id']})
        self.assertIsNone(parent_loc.get('parent'))

        # set child as parent
        with self.assertRaises(CLIReturnCodeError):
            Location.update({
                'id': loc['id'],
                'parent-id': loc['id'],
            })
        loc = Location.info({'id': loc['id']})
        self.assertEqual(loc['parent'], parent_loc['name'])
