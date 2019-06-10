"""Unit tests for the ``locations`` paths.

A full API reference for locations can be found here:
http://theforeman.org/api/apidoc/v2/locations.html


:Requirement: Location

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_integer, gen_string
from nailgun import entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.cleanup import capsule_cleanup, location_cleanup
from robottelo.constants import DEFAULT_LOC
from robottelo.cli.factory import make_proxy
from robottelo.decorators import (
    run_in_one_thread,
    tier1,
    tier2,
)
from robottelo.datafactory import filtered_datapoint, invalid_values_list
from robottelo.test import APITestCase


@filtered_datapoint
def valid_loc_data_list():
    """List of valid data for input testing.

    Note: The maximum allowed length of location name is 246 only. This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)

    """
    return [
        gen_string('alphanumeric', randint(1, 246)),
        gen_string('alpha', randint(1, 246)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 246)),
        gen_string('numeric', randint(1, 246)),
        gen_string('utf8', randint(1, 85)),
        gen_string('html', randint(1, 85)),
    ]


class LocationTestCase(APITestCase):
    """Tests for the ``locations`` path."""
    # TODO Add coverage for media, realms as soon as they're implemented

    def _make_proxy(self, options=None):
        """Create a Proxy and register the cleanup function"""
        proxy = make_proxy(options=options)
        # Add capsule to cleanup list
        self.addCleanup(capsule_cleanup, proxy['id'])
        return proxy

    @classmethod
    def setUpClass(cls):
        """Set up reusable entities for tests."""
        cls.org = entities.Organization().create()
        cls.org2 = entities.Organization().create()
        cls.domain = entities.Domain().create()
        cls.subnet = entities.Subnet().create()
        cls.env = entities.Environment().create()
        cls.host_group = entities.HostGroup().create()
        cls.template = entities.ConfigTemplate().create()
        cls.test_cr = entities.LibvirtComputeResource().create()
        cls.new_user = entities.User().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create new locations using different inputs as a name

        :id: 90bb90a3-120f-4ea6-89a9-62757be42486

        :expectedresults: Location created successfully and has expected and
            correct name

        :CaseImportance: Critical
        """
        for name in valid_loc_data_list():
            with self.subTest(name):
                location = entities.Location(name=name).create()
                self.assertEqual(location.name, name)

    @tier1
    def test_positive_create_and_delete_with_comma_separated_name(self):
        """Create new location using name that has comma inside, delete location

        :id: 3131e99d-b278-462e-a650-a5a4f4e0a2f1

        :expectedresults: Location created successfully and has expected name
        """
        name = '{0}, {1}'.format(gen_string('alpha'), gen_string('alpha'))
        location = entities.Location(name=name).create()
        self.assertEqual(location.name, name)
        location.delete()
        with self.assertRaises(HTTPError):
            location.read()

    @tier2
    def test_positive_create_and_update_with_org(self):
        """Create new location with assigned organization to it

        :id: 5032a93f-4b37-4c19-b6d3-26e3a868d0f1

        :expectedresults: Location created successfully and has correct
            organization assigned to it with expected title

        :CaseLevel: Integration
        """
        location = entities.Location(organization=[self.org]).create()
        self.assertEqual(location.organization[0].id, self.org.id)
        self.assertEqual(location.organization[0].read().title, self.org.title)

        orgs = [self.org, self.org2]
        location.organization = orgs
        location = location.update(['organization'])
        self.assertEqual(
            set([org.id for org in orgs]),
            set([org.id for org in location.organization]),
        )

    @tier1
    def test_negative_create_with_name(self):
        """Attempt to create new location using invalid names only

        :id: 320e6bca-5645-423b-b86a-2b6f35c8dae3

        :expectedresults: Location is not created and expected error is raised

        :CaseImportance: Critical
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Location(name=name).create()

    @tier1
    def test_negative_create_with_same_name(self):
        """Attempt to create new location using name of existing entity

        :id: bc09acb3-9ecf-4d23-b3ef-94f24e16e6db

        :expectedresults: Location is not created and expected error is raised

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        location = entities.Location(name=name).create()
        self.assertEqual(location.name, name)
        with self.assertRaises(HTTPError):
            entities.Location(name=name).create()

    @tier1
    def test_negative_create_with_domain(self):
        """Attempt to create new location using non-existent domain identifier

        :id: 5449532d-7959-4547-ba05-9e194eea495d

        :expectedresults: Location is not created and expected error is raised

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.Location(domain=[gen_integer(10000, 99999)]).create()

    @tier1
    def test_positive_update_name(self):
        """Update location with new name

        :id: 73ff6dab-e12a-4f7d-9c1f-6984fc076329

        :expectedresults: Location updated successfully and name was changed

        :CaseImportance: Critical
        """
        for new_name in valid_loc_data_list():
            with self.subTest(new_name):
                location = entities.Location().create()
                location.name = new_name
                self.assertEqual(location.update(['name']).name, new_name)

    @tier2
    def test_positive_update_entities(self):
        """Update location with new domain

        :id: 1016dfb9-8103-45f1-8738-0579fa9754c1

        :expectedresults: Location updated successfully and has correct domain
            assigned

        :CaseLevel: Integration
        """
        location = entities.Location().create()

        location.domain = [self.domain]
        location.subnet = [self.subnet]
        location.environment = [self.env]
        location.hostgroup = [self.host_group]
        location.config_template = [self.template]
        location.compute_resource = [self.test_cr]
        location.user = [self.new_user]

        self.assertEqual(location.update(['domain']).domain[0].id, self.domain.id)
        self.assertEqual(location.update(['subnet']).subnet[0].id, self.subnet.id)
        self.assertEqual(
            location.update(['environment']).environment[0].id,
            self.env.id
        )
        self.assertEqual(
            location.update(['hostgroup']).hostgroup[0].id,
            self.host_group.id
        )
        ct_list = [
            ct
            for ct
            in location.update(['config_template']).config_template
            if ct.id == self.template.id
        ]
        self.assertEqual(len(ct_list), 1)
        self.assertEqual(
            location.update(['compute_resource']).compute_resource[0].id,
            self.test_cr.id
        )
        self.assertEqual(
            location.compute_resource[0].read().provider, 'Libvirt')
        self.assertEqual(location.update(['user']).user[0].id, self.new_user.id)

    @run_in_one_thread
    @tier2
    def test_positive_create_update_and_remove_capsule(self):
        """Update location with new capsule

        :id: 2786146f-f466-4ed8-918a-5f46806558e2

        :expectedresults: Location updated successfully and has correct capsule
            assigned

        :bz: 1398695

        :CaseLevel: Integration
        """
        proxy_id_1 = self._make_proxy()['id']
        proxy_id_2 = self._make_proxy()['id']

        proxy = entities.SmartProxy(id=proxy_id_1).read()
        location = entities.Location(smart_proxy=[proxy]).create()
        # Add location to cleanup list
        self.addCleanup(location_cleanup, location.id)

        new_proxy = entities.SmartProxy(id=proxy_id_2).read()
        location.smart_proxy = [new_proxy]
        location = location.update(['smart_proxy'])
        self.assertEqual(location.smart_proxy[0].id, new_proxy.id)
        self.assertEqual(location.smart_proxy[0].read().name, new_proxy.name)

        location.smart_proxy = []
        location = location.update(['smart_proxy'])
        self.assertEqual(len(location.smart_proxy), 0)

    @tier2
    def test_negative_update_domain(self):
        """Try to update existing location with incorrect domain. Use
        domain id

        :id: e26c92f2-42cb-4706-9e03-3e00a134cb9f

        :expectedresults: Location is not updated

        :CaseLevel: Integration
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

    @tier1
    def test_default_loc_id_check(self):
        """test to check the default_location id

        :id: 3c89d63b-d5fb-4f05-9efb-f560f0194c85

        :BZ: 1713269

        :expectedresults: The default_location ID remain 2.

        :CaseImportance: Critical
        """
        default_loc_id = entities.Location().search(
            query={'search': 'name="{}"'.format(DEFAULT_LOC)})[0].id
        self.assertEqual(default_loc_id, 2)
