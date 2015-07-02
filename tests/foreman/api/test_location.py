"""Unit tests for the ``locations`` paths.

A full API reference for locations can be found here:
http://theforeman.org/api/apidoc/v2/locations.html

"""
from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.common.decorators import data
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
