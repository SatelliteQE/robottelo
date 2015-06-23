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
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.test import CLITestCase


@ddt
class TestLocation(CLITestCase):
    """Tests for Location via Hammer CLI"""
    # TODO Add coverage for smart_proxy and realm once we can create ssh tunnel

    @data(
        gen_string('alphanumeric', randint(1, 255)),
        gen_string('alpha', randint(1, 255)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 255)),
        gen_string('numeric', randint(1, 255)),
        gen_string('utf8', randint(1, 85)),
        gen_string('html', 85),
    )
    def test_create_location_with_different_names(self, name):
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
        env_ids = ','.join(env['id'] for env in envs)
        loc = make_location({'environment-ids': env_ids})
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
        domain_names = ','.join(domain['name'] for domain in domains)
        loc = make_location({'domains': domain_names})
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
            make_location({'compute-resource-ids': gen_string('numeric', 150)})

    def test_create_location_with_user_by_name_negative(self):
        """@Test: Try to create new location with incorrect user assigned to it
        Use user login as a parameter

        @Feature: Location

        @Assert: Location is not created

        """
        with self.assertRaises(CLIFactoryError):
            make_location({'users': gen_string('utf8', 80)})
