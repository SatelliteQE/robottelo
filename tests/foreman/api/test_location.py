"""Unit tests for the ``locations`` paths.

A full API reference for locations can be found here:
http://theforeman.org/api/apidoc/v2/locations.html

"""
from ddt import ddt
from fauxfactory import gen_integer, gen_string
from nailgun import entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.decorators import data
from robottelo.test import APITestCase


@ddt
class LocationTestCase(APITestCase):
    """Tests for the ``locations`` path."""
    # TODO Add coverage for media, smart_proxy, realms once they implemented

    @data(
        gen_string('alphanumeric', randint(1, 246)),
        gen_string('alpha', randint(1, 246)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 246)),
        gen_string('numeric', randint(1, 246)),
        gen_string('utf8', randint(1, 85)),
    )
    def test_create_location_with_different_names(self, name):
        """@Test: Create new locations using different inputs as a name

        @Assert: Location created successfully and has expected and correct
        name

        @Feature: Location

        """
        location = entities.Location(name=name).create()
        self.assertEqual(location.name, name)

    def test_create_location_with_description(self):
        """@Test: Create new location with custom description

        @Assert: Location created successfully and has expected and correct
        description

        @Feature: Location

        """
        description = gen_string('utf8')
        location = entities.Location(description=description).create()
        self.assertEqual(location.description, description)

    def test_create_location_with_user(self):
        """@Test: Create new location with assigned user to it

        @Assert: Location created successfully and has correct user assigned to
        it with expected login name

        @Feature: Location

        """
        user = entities.User().create()
        location = entities.Location(user=[user]).create()
        self.assertEqual(location.user[0].id, user.id)
        self.assertEqual(location.user[0].read().login, user.login)

    def test_create_location_with_comp_resource_libvirt(self):
        """@Test: Create new location with Libvirt compute resource assigned to
        it

        @Assert: Location created successfully and has correct Libvirt compute
        resource assigned to it

        @Feature: Location

        """
        test_cr = entities.LibvirtComputeResource().create()
        location = entities.Location(compute_resource=[test_cr]).create()
        self.assertEqual(location.compute_resource[0].id, test_cr.id)
        self.assertEqual(
            location.compute_resource[0].read().provider, 'Libvirt')

    def test_create_location_with_comp_resource_docker(self):
        """@Test: Create new location with Docker compute resource assigned to
        it

        @Assert: Location created successfully and has correct Docker compute
        resource assigned to it

        @Feature: Location

        """
        test_cr = entities.DockerComputeResource().create()
        location = entities.Location(compute_resource=[test_cr]).create()
        self.assertEqual(location.compute_resource[0].id, test_cr.id)
        self.assertEqual(
            location.compute_resource[0].read().provider, 'Docker')

    def test_create_location_with_template(self):
        """@Test: Create new location with config template assigned to it

        @Assert: Location created successfully and list of config templates
        assigned to that location should contain expected one

        @Feature: Location

        """
        template = entities.ConfigTemplate().create()
        location = entities.Location(config_template=[template]).create()
        self.assertGreaterEqual(len(location.config_template), 1)
        self.assertNotEqual(
            filter(lambda ct: ct.id == template.id, location.config_template),
            []
        )

    def test_create_location_with_domain(self):
        """@Test: Create new location with assigned domain to it

        @Assert: Location created successfully and has correct and expected
        domain assigned to it

        @Feature: Location

        """
        domain = entities.Domain().create()
        location = entities.Location(domain=[domain]).create()
        self.assertEqual(location.domain[0].id, domain.id)

    def test_create_location_with_subnet(self):
        """@Test: Create new location with assigned subnet to it

        @Assert: Location created successfully and has correct subnet with
        expected network address assigned to it

        @Feature: Location

        """
        subnet = entities.Subnet().create()
        location = entities.Location(subnet=[subnet]).create()
        self.assertEqual(location.subnet[0].id, subnet.id)
        self.assertEqual(subnet.network, location.subnet[0].read().network)

    def test_create_location_with_environment(self):
        """@Test: Create new location with assigned environment to it

        @Assert: Location created successfully and has correct and expected
        environment assigned to it

        @Feature: Location

        """
        env = entities.Environment().create()
        location = entities.Location(environment=[env]).create()
        self.assertEqual(location.environment[0].id, env.id)

    def test_create_location_with_host_group(self):
        """@Test: Create new location with assigned host group to it

        @Assert: Location created successfully and has correct and expected
        host group assigned to it

        @Feature: Location

        """
        host_group = entities.HostGroup().create()
        location = entities.Location(hostgroup=[host_group]).create()
        self.assertEqual(location.hostgroup[0].id, host_group.id)

    def test_create_location_with_organization(self):
        """@Test: Create new location with assigned organization to it

        @Assert: Location created successfully and has correct organization
        assigned to it with expected title

        @Feature: Location

        """
        org = entities.Organization().create()
        location = entities.Location(organization=[org]).create()
        self.assertEqual(location.organization[0].id, org.id)
        self.assertEqual(location.organization[0].read().title, org.title)

    def test_create_location_with_multiple_organization(self):
        """@Test: Basically, verifying that location with multiple entities
        assigned to it can be created in the system. Organizations were chosen
        for that purpose

        @Assert: Location created successfully and has correct organizations
        assigned to it

        @Feature: Location

        """
        orgs_amount = randint(3, 5)
        org_ids = [
            entities.Organization().create().id for _ in range(orgs_amount)
        ]
        location = entities.Location(organization=org_ids).create()
        self.assertEqual(len(location.organization), orgs_amount)
        for org in location.organization:
            self.assertIn(org.id, org_ids)

    def test_delete_location(self):
        """@Test: Delete location

        @Assert: Location was deleted

        @Feature: Location - Delete

        """
        location = entities.Location().create()
        location.delete()
        with self.assertRaises(HTTPError):
            location.read()

    @data(
        gen_string('alphanumeric', randint(1, 246)),
        gen_string('alpha', randint(1, 246)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 246)),
        gen_string('numeric', randint(1, 246)),
        gen_string('utf8', randint(1, 85)),
    )
    def test_update_location_with_new_name(self, new_name):
        """@Test: Update location with new name

        @Assert: Location updated successfully and name was changed

        @Feature: Location - Update

        """
        location = entities.Location().create()
        location.name = new_name
        self.assertEqual(location.update(['name']).name, new_name)

    @data(
        gen_string('alphanumeric', randint(1, 246)),
        gen_string('alpha', randint(1, 246)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 246)),
        gen_string('numeric', randint(1, 246)),
        gen_string('utf8', randint(1, 85)),
    )
    def test_update_location_with_new_description(self, new_description):
        """@Test: Update location with new description

        @Assert: Location updated successfully and description was changed

        @Feature: Location - Update

        """
        location = entities.Location().create()
        location.description = new_description
        self.assertEqual(
            location.update(['description']).description,
            new_description
        )

    def test_update_location_with_new_user(self):
        """@Test: Update location with new user

        @Assert: Location updated successfully and has correct user assigned

        @Feature: Location - Update

        """
        location = entities.Location(user=[entities.User().create()]).create()
        new_user = entities.User().create()
        location.user = [new_user]
        self.assertEqual(location.update(['user']).user[0].id, new_user.id)

    def test_update_location_with_new_comp_resource_libvirt(self):
        """@Test: Update location with new Libvirt compute resource

        @Assert: Location updated successfully and has correct Libvirt compute
        resource assigned

        @Feature: Location - Update

        """
        location = entities.Location(
            compute_resource=[entities.LibvirtComputeResource().create()],
        ).create()
        test_cr = entities.LibvirtComputeResource().create()
        location.compute_resource = [test_cr]
        self.assertEqual(
            location.update(['compute_resource']).compute_resource[0].id,
            test_cr.id
        )
        self.assertEqual(
            location.compute_resource[0].read().provider, 'Libvirt')

    def test_update_location_with_new_comp_resource_docker(self):
        """@Test: Update location with new Docker compute resource

        @Assert: Location updated successfully and has correct Docker compute
        resource assigned

        @Feature: Location - Update

        """
        location = entities.Location(
            compute_resource=[entities.DockerComputeResource().create()],
        ).create()
        test_cr = entities.DockerComputeResource().create()
        location.compute_resource = [test_cr]
        self.assertEqual(
            location.update(['compute_resource']).compute_resource[0].id,
            test_cr.id
        )
        self.assertEqual(
            location.compute_resource[0].read().provider, 'Docker')

    def test_update_location_with_new_template(self):
        """@Test: Update location with new config template

        @Assert: Location updated successfully and has correct config template
        assigned

        @Feature: Location - Update

        """
        location = entities.Location(
            config_template=[entities.ConfigTemplate().create()],
        ).create()
        template = entities.ConfigTemplate().create()
        location.config_template = [template]
        ct_list = [
            ct
            for ct
            in location.update(['config_template']).config_template
            if ct.id == template.id
        ]
        self.assertEqual(len(ct_list), 1)

    def test_update_location_with_new_domain(self):
        """@Test: Update location with new domain

        @Assert: Location updated successfully and has correct domain assigned

        @Feature: Location - Update

        """
        location = entities.Location(
            domain=[entities.Domain().create()],
        ).create()
        domain = entities.Domain().create()
        location.domain = [domain]
        self.assertEqual(location.update(['domain']).domain[0].id, domain.id)

    def test_update_location_with_new_subnet(self):
        """@Test: Update location with new subnet

        @Assert: Location updated successfully and has correct subnet assigned

        @Feature: Location - Update

        """
        location = entities.Location(
            subnet=[entities.Subnet().create()],
        ).create()
        subnet = entities.Subnet().create()
        location.subnet = [subnet]
        self.assertEqual(location.update(['subnet']).subnet[0].id, subnet.id)

    def test_update_location_with_new_environment(self):
        """@Test: Update location with new environment

        @Assert: Location updated successfully and has correct environment
        assigned

        @Feature: Location - Update

        """
        location = entities.Location(
            environment=[entities.Environment().create()],
        ).create()
        env = entities.Environment().create()
        location.environment = [env]
        self.assertEqual(
            location.update(['environment']).environment[0].id,
            env.id
        )

    def test_update_location_with_new_host_group(self):
        """@Test: Update location with new host group

        @Assert: Location updated successfully and has correct host group
        assigned

        @Feature: Location - Update

        """
        location = entities.Location(
            hostgroup=[entities.HostGroup().create()],
        ).create()
        host_group = entities.HostGroup().create()
        location.hostgroup = [host_group]
        self.assertEqual(
            location.update(['hostgroup']).hostgroup[0].id,
            host_group.id
        )

    def test_update_location_with_new_organization(self):
        """@Test: Update location with new organization

        @Assert: Location updated successfully and has correct organization
        assigned

        @Feature: Location - Update

        """
        location = entities.Location(
            organization=[entities.Organization().create()],
        ).create()
        org = entities.Organization().create()
        location.organization = [org]
        self.assertEqual(
            location.update(['organization']).organization[0].id,
            org.id
        )

    def test_update_location_with_multiple_organizations(self):
        """@Test: Update location with with multiple organizations

        @Assert: Location created successfully and has correct organizations
        assigned

        @Feature: Location - Update

        """
        location = entities.Location(
            organization=[entities.Organization().create()],
        ).create()
        orgs = [entities.Organization().create() for _ in range(randint(3, 5))]
        location.organization = orgs
        location = location.update(['organization'])
        self.assertEqual(
            set([org.id for org in orgs]),
            set([org.id for org in location.organization]),
        )

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
    def test_update_location_with_different_names_negative(self, new_name):
        """@Test: Try to update location using invalid names only

        @Assert: Location is not updated

        @Feature: Location - Update

        """
        location = entities.Location().create()
        location.name = new_name
        with self.assertRaises(HTTPError):
            self.assertNotEqual(location.update(['name']).name, new_name)

    def test_update_location_with_domain_by_id_negative(self):
        """@Test: Try to update existing location with incorrect domain. Use
        domain id

        @Assert: Location is not updated

        @Feature: Location - Update

        """
        location = entities.Location(
            domain=[entities.Domain().create()],
        ).create()
        domain = entities.Domain().create()
        location.domain[0].id = gen_integer(10000, 99999)
        with self.assertRaises(HTTPError):
            self.assertNotEqual(
                location.update(['domain']).domain[0].id,
                domain.id
            )
