# -*- encoding: utf-8 -*-
"""Test class for Location CLI"""

from ddt import ddt
from fauxfactory import gen_string
from random import randint
from robottelo.cli.factory import (
    CLIFactoryError,
    make_compute_resource,
    make_domain,
    make_environment,
    make_hostgroup,
    make_location,
    make_medium,
    make_subnet,
    make_template,
    make_user,
)
from robottelo.cli.location import Location
from robottelo.decorators import data, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class TestLocation(CLITestCase):
    """Tests for Location via Hammer CLI"""
    # TODO Add coverage for smart_proxy and realm once we can create ssh tunnel

    @data(
        gen_string('alphanumeric', randint(1, 246)),
        gen_string('alpha', randint(1, 246)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 246)),
        gen_string('numeric', randint(1, 246)),
        gen_string('utf8', randint(1, 85)),
        gen_string('html', randint(1, 85)),
    )
    def test_create_location_with_different_names_positive(self, name):
        """@Test: Try to create location using different value types as a name

        @Feature: Location

        @Assert: Location is created successfully and has proper name

        """
        loc = make_location({'name': name})
        self.assertEqual(loc['name'], name)

    @skip_if_bug_open('bugzilla', 1233612)
    def test_create_location_with_description(self):
        """@Test: Create new location with custom description

        @Feature: Location

        @Assert: Location created successfully and has expected and correct
        description

        """
        description = gen_string('utf8')
        loc = make_location({'description': description})
        self.assertEqual(loc['description'], description)

    def test_create_location_with_user_by_id(self):
        """@Test: Create new location with assigned user to it. Use user id as
        a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct user assigned to
        it with expected login name

        """
        user = make_user()
        loc = make_location({'user-ids': user['id']})
        self.assertEqual(loc['users'][0], user['login'])

    def test_create_location_with_user_by_name(self):
        """@Test: Create new location with assigned user to it. Use user login
        as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct user assigned to
        it with expected login name

        """
        user = make_user()
        loc = make_location({'users': user['login']})
        self.assertEqual(loc['users'][0], user['login'])

    def test_create_location_with_comp_resource_by_id(self):
        """@Test: Create new location with compute resource assigned to it. Use
        compute resource id as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct compute resource
        assigned to it

        """
        comp_resource = make_compute_resource()
        loc = make_location({'compute-resource-ids': comp_resource['id']})
        self.assertEqual(loc['compute-resources'][0], comp_resource['name'])

    def test_create_location_with_comp_resource_by_name(self):
        """@Test: Create new location with compute resource assigned to it. Use
        compute resource name as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct compute resource
        assigned to it

        """
        comp_resource = make_compute_resource()
        loc = make_location({'compute-resources': comp_resource['name']})
        self.assertEqual(loc['compute-resources'][0], comp_resource['name'])

    def test_create_location_with_template_by_id(self):
        """@Test: Create new location with config template assigned to it. Use
        config template id as a parameter

        @Feature: Location

        @Assert: Location created successfully and list of config templates
        assigned to that location should contain expected one

        """
        template = make_template()
        loc = make_location({'config-template-ids': template['id']})
        self.assertGreaterEqual(len(loc['templates']), 1)
        self.assertIn(
            u'{0} ({1})'. format(template['name'], template['type']),
            loc['templates']
        )

    def test_create_location_with_template_by_name(self):
        """@Test: Create new location with config template assigned to it. Use
        config template name as a parameter

        @Feature: Location

        @Assert: Location created successfully and list of config templates
        assigned to that location should contain expected one

        """
        template = make_template()
        loc = make_location({'config-templates': template['name']})
        self.assertGreaterEqual(len(loc['templates']), 1)
        self.assertIn(
            u'{0} ({1})'. format(template['name'], template['type']),
            loc['templates']
        )

    def test_create_location_with_domain_by_id(self):
        """@Test: Create new location with assigned domain to it. Use domain id
        as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct and expected
        domain assigned to it

        """
        domain = make_domain()
        loc = make_location({'domain-ids': domain['id']})
        self.assertEqual(loc['domains'][0], domain['name'])

    def test_create_location_with_domain_by_name(self):
        """@Test: Create new location with assigned domain to it. Use domain
        name as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct and expected
        domain assigned to it

        """
        domain = make_domain()
        loc = make_location({'domains': domain['name']})
        self.assertEqual(loc['domains'][0], domain['name'])

    def test_create_location_with_subnet_by_id(self):
        """@Test: Create new location with assigned subnet to it. Use subnet id
        as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct subnet with
        expected network address assigned to it

        """
        subnet = make_subnet()
        loc = make_location({'subnet-ids': subnet['id']})
        self.assertIn(subnet['name'], loc['subnets'][0])
        self.assertIn(subnet['network'], loc['subnets'][0])

    def test_create_location_with_subnet_by_name(self):
        """@Test: Create new location with assigned subnet to it. Use subnet
        name as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct subnet with
        expected network address assigned to it

        """
        subnet = make_subnet()
        loc = make_location({'subnets': subnet['name']})
        self.assertIn(subnet['name'], loc['subnets'][0])
        self.assertIn(subnet['network'], loc['subnets'][0])

    def test_create_location_with_environment_by_id(self):
        """@Test: Create new location with assigned environment to it. Use
        environment id as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct and expected
        environment assigned to it

        """
        env = make_environment()
        loc = make_location({'environment-ids': env['id']})
        self.assertEqual(loc['environments'][0], env['name'])

    def test_create_location_with_environment_by_name(self):
        """@Test: Create new location with assigned environment to it. Use
        environment name as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct and expected
        environment assigned to it

        """
        env = make_environment()
        loc = make_location({'environments': env['name']})
        self.assertEqual(loc['environments'][0], env['name'])

    def test_create_location_with_host_group_by_id(self):
        """@Test: Create new location with assigned host group to it. Use host
        group id as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct and expected
        host group assigned to it

        """
        host_group = make_hostgroup()
        loc = make_location({'hostgroup-ids': host_group['id']})
        self.assertEqual(loc['hostgroups'][0], host_group['name'])

    def test_create_location_with_host_group_by_name(self):
        """@Test: Create new location with assigned host group to it. Use host
        group name as a parameter

        @Feature: Location

        @Assert: Location created successfully and has correct and expected
        host group assigned to it

        """
        host_group = make_hostgroup()
        loc = make_location({'hostgroups': host_group['name']})
        self.assertEqual(loc['hostgroups'][0], host_group['name'])

    @skip_if_bug_open('bugzilla', 1234287)
    def test_create_location_with_medium(self):
        """@Test: Create new location with assigned media to it.

        @Feature: Location

        @Assert: Location created successfully and has correct and expected
        media assigned to it

        """
        medium = make_medium()
        loc = make_location({'medium-ids': medium['id']})
        self.assertGreater(len(loc['installation-media']), 0)
        self.assertEqual(loc['installation-media'][0], medium['name'])

    def test_create_location_with_multiple_environments_by_id(self):
        """@Test: Basically, verifying that location with multiple entities
        assigned to it by id can be created in the system. Environments were
        chosen for that purpose.

        @Feature: Location

        @Assert: Location created successfully and has correct environments
        assigned to it

        """
        envs_amount = randint(3, 5)
        envs = [make_environment() for _ in range(envs_amount)]
        loc = make_location({'environment-ids': [env['id'] for env in envs]})
        self.assertEqual(len(loc['environments']), envs_amount)
        for env in envs:
            self.assertIn(env['name'], loc['environments'])

    def test_create_location_with_multiple_domains_by_name(self):
        """@Test: Basically, verifying that location with multiple entities
        assigned to it by name can be created in the system. Domains were
        chosen for that purpose.

        @Feature: Location

        @Assert: Location created successfully and has correct domains assigned
        to it

        """
        domains_amount = randint(3, 5)
        domains = [make_domain() for _ in range(domains_amount)]
        loc = make_location({
            'domains': [domain['name'] for domain in domains],
        })
        self.assertEqual(len(loc['domains']), domains_amount)
        for domain in domains:
            self.assertIn(domain['name'], loc['domains'])

    @data(
        '',
        ' ',
        gen_string('alphanumeric', 300),
        gen_string('alpha', 300),
        gen_string('cjk', 300),
        gen_string('latin1', 300),
        gen_string('numeric', 300),
        gen_string('utf8', 300),
        gen_string('html', 300),
    )
    def test_create_location_with_different_names_negative(self, name):
        """@Test: Try to create location using invalid names only

        @Feature: Location

        @Assert: Location is not created

        """
        with self.assertRaises(CLIFactoryError):
            make_location({'name': name})

    def test_create_location_with_same_names_negative(self):
        """@Test: Try to create location using same name twice

        @Feature: Location

        @Assert: Second location is not created

        """
        name = gen_string('utf8')
        loc = make_location({'name': name})
        self.assertEqual(loc['name'], name)
        with self.assertRaises(CLIFactoryError):
            make_location({'name': name})

    def test_create_location_with_comp_resource_by_id_negative(self):
        """@Test: Try to create new location with incorrect compute resource
        assigned to it. Use compute resource id as a parameter

        @Feature: Location

        @Assert: Location is not created

        """
        with self.assertRaises(CLIFactoryError):
            make_location({'compute-resource-ids': gen_string('numeric', 6)})

    def test_create_location_with_user_by_name_negative(self):
        """@Test: Try to create new location with incorrect user assigned to it
        Use user login as a parameter

        @Feature: Location

        @Assert: Location is not created

        """
        with self.assertRaises(CLIFactoryError):
            make_location({'users': gen_string('utf8', 80)})

    @data(
        gen_string('alphanumeric', randint(1, 246)),
        gen_string('alpha', randint(1, 246)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 246)),
        gen_string('numeric', randint(1, 246)),
        gen_string('utf8', randint(1, 85)),
        gen_string('html', randint(1, 85)),
    )
    def test_update_location_with_different_names(self, name):
        """@Test: Try to update location using different value types as a name

        @Feature: Location

        @Assert: Location is updated successfully and has proper and expected
        name

        """
        loc = make_location()
        self.assertNotEqual(loc['name'], name)

        result = Location.update({
            'id': loc['id'],
            'new-name': name,
        })
        self.assertEqual(result.return_code, 0)

        result = Location.info({'id': loc['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['name'], name)

    def test_update_location_with_user_by_id(self):
        """@Test: Create new location with assigned user to it. Try to update
        that location and change assigned user on another one. Use user id as a
        parameter

        @Feature: Location

        @Assert: Location is updated successfully and has correct user assigned
        to it

        """
        user = [make_user() for _ in range(2)]
        loc = make_location({'user-ids': user[0]['id']})
        self.assertEqual(loc['users'][0], user[0]['login'])

        result = Location.update({
            'id': loc['id'],
            'user-ids': user[1]['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = Location.info({'id': loc['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['users'][0], user[1]['login'])

    def test_update_location_with_subnet_by_name(self):
        """@Test: Create new location with assigned subnet to it. Try to update
        that location and change assigned subnet on another one. Use subnet
        name as a parameter

        @Feature: Location

        @Assert: Location is updated successfully and has correct subnet with
        expected network address assigned to it

        """
        subnet = [make_subnet() for _ in range(2)]
        loc = make_location({'subnets': subnet[0]['name']})
        self.assertIn(subnet[0]['name'], loc['subnets'][0])
        self.assertIn(subnet[0]['network'], loc['subnets'][0])

        result = Location.update({
            'id': loc['id'],
            'subnets': subnet[1]['name'],
        })
        self.assertEqual(result.return_code, 0)

        result = Location.info({'id': loc['id']})
        self.assertEqual(result.return_code, 0)
        self.assertIn(subnet[1]['name'], result.stdout['subnets'][0])
        self.assertIn(subnet[1]['network'], result.stdout['subnets'][0])

    def test_update_location_with_multiple_comp_resources_to_single(self):
        """@Test: Create location with multiple (not less than three) compute
        resources assigned to it. Try to update location and overwrite all
        compute resources with a new single compute resource. Use compute
        resource id as a parameter

        @Feature: Location

        @Assert: Location updated successfully and has correct compute resource
        assigned to it

        """
        resources_amount = randint(3, 5)
        resources = [make_compute_resource() for _ in range(resources_amount)]
        loc = make_location({
            'compute-resource-ids': [resource['id'] for resource in resources],
        })
        self.assertEqual(len(loc['compute-resources']), resources_amount)
        for resource in resources:
            self.assertIn(resource['name'], loc['compute-resources'])

        new_resource = make_compute_resource()
        result = Location.update({
            'id': loc['id'],
            'compute-resource-ids': new_resource['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = Location.info({'id': loc['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['compute-resources']), 1)
        self.assertEqual(
            result.stdout['compute-resources'][0], new_resource['name'])

    def test_update_location_with_multiple_host_group_to_multiple(self):
        """@Test: Create location with multiple (three) host groups assigned to
        it. Try to update location and overwrite all host groups by new
        multiple (two) host groups. Use host groups name as a parameter

        @Feature: Location

        @Assert: Location updated successfully and has correct and expected
        host groups assigned to it

        """

        host_groups = [make_hostgroup() for _ in range(3)]
        loc = make_location({
            'hostgroups': [hg['name'] for hg in host_groups],
            })
        self.assertEqual(len(loc['hostgroups']), 3)
        for host_group in host_groups:
            self.assertIn(host_group['name'], loc['hostgroups'])

        new_host_groups = [make_hostgroup() for _ in range(2)]
        result = Location.update({
            'id': loc['id'],
            'hostgroups': [hg['name'] for hg in new_host_groups],
        })
        self.assertEqual(result.return_code, 0)

        result = Location.info({'id': loc['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['hostgroups']), 2)
        for host_group in new_host_groups:
            self.assertIn(host_group['name'], result.stdout['hostgroups'])

    @data(
        '',
        ' ',
        gen_string('alphanumeric', 300),
        gen_string('alpha', 300),
        gen_string('cjk', 300),
        gen_string('latin1', 300),
        gen_string('numeric', 300),
        gen_string('utf8', 300),
        gen_string('html', 300),
    )
    def test_update_location_with_different_names_negative(self, name):
        """@Test: Try to update location using invalid names only

        @Feature: Location

        @Assert: Location is not updated

        """
        loc = make_location()

        result = Location.update({
            'id': loc['id'],
            'new-name': name,
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    def test_update_location_with_domain_by_id_negative(self):
        """@Test: Try to update existing location with incorrect domain. Use
        domain id as a parameter

        @Feature: Location

        @Assert: Location is not updated

        """
        loc = make_location()
        result = Location.update({
            'id': loc['id'],
            'domain-ids': gen_string('numeric', 6),
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    def test_update_location_with_template_by_name_negative(self):
        """@Test: Try to update existing location with incorrect config
        template. Use template name as a parameter

        @Feature: Location

        @Assert: Location is not updated

        """
        loc = make_location()
        result = Location.update({
            'id': loc['id'],
            'config-templates': gen_string('utf8', 80),
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    @data(
        gen_string('alphanumeric', randint(1, 246)),
        gen_string('alpha', randint(1, 246)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 246)),
        gen_string('numeric', randint(1, 246)),
        gen_string('utf8', randint(1, 85)),
        gen_string('html', randint(1, 85)),
    )
    def test_delete_location_by_name(self, name):
        """@Test: Try to delete location using name of that location as a
        parameter. Use different value types for testing.

        @Feature: Location

        @Assert: Location is deleted successfully

        """
        loc = make_location({'name': name})
        self.assertEqual(loc['name'], name)
        result = Location.delete({'name': loc['name']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Location.info({'id': loc['id']})
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)

    def test_delete_location_by_id(self):
        """@Test: Try to delete location using id of that location as a
        parameter

        @Feature: Location

        @Assert: Location is deleted successfully

        """
        loc = make_location()
        result = Location.delete({'id': loc['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Location.info({'id': loc['id']})
        self.assertNotEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stderr), 0)
