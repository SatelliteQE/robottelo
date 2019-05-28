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
    skip_if_bug_open,
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
    def test_positive_create_with_comma_separated_name(self):
        """Create new location using name that has comma inside

        :id: 3131e99d-b278-462e-a650-a5a4f4e0a2f1

        :expectedresults: Location created successfully and has expected name
        """
        name = '{0}, {1}'.format(gen_string('alpha'), gen_string('alpha'))
        location = entities.Location(name=name).create()
        self.assertEqual(location.name, name)

    @tier1
    def test_positive_create_with_description(self):
        """Create new location with custom description

        :id: 8d82fe06-895d-4c99-87c0-354124e013fd

        :expectedresults: Location created successfully and has expected and
            correct description

        :CaseImportance: Critical
        """
        description = gen_string('utf8')
        location = entities.Location(description=description).create()
        self.assertEqual(location.description, description)

    @tier2
    def test_positive_create_with_user(self):
        """Create new location with assigned user to it

        :id: d3798742-c05d-4864-8eca-44872b4afdbf

        :expectedresults: Location created successfully and has correct user
            assigned to it with expected login name

        :CaseLevel: Integration
        """
        user = entities.User().create()
        location = entities.Location(user=[user]).create()
        self.assertEqual(location.user[0].id, user.id)
        self.assertEqual(location.user[0].read().login, user.login)

    @tier2
    def test_positive_create_with_libvirt_compresource(self):
        """Create new location with Libvirt compute resource assigned to
        it

        :id: 292033fd-9a13-4537-ad10-095ba621d66b

        :expectedresults: Location created successfully and has correct Libvirt
            compute resource assigned to it

        :CaseLevel: Integration
        """
        test_cr = entities.LibvirtComputeResource().create()
        location = entities.Location(compute_resource=[test_cr]).create()
        self.assertEqual(location.compute_resource[0].id, test_cr.id)
        self.assertEqual(
            location.compute_resource[0].read().provider, 'Libvirt')

    @tier2
    def test_positive_create_with_docker_compresource(self):
        """Create new location with Docker compute resource assigned to
        it

        :id: 0c55292b-d6ff-45e3-a065-d6a2c8ba2469

        :expectedresults: Location created successfully and has correct Docker
            compute resource assigned to it

        :CaseLevel: Integration
        """
        test_cr = entities.DockerComputeResource().create()
        location = entities.Location(compute_resource=[test_cr]).create()
        self.assertEqual(location.compute_resource[0].id, test_cr.id)
        self.assertEqual(
            location.compute_resource[0].read().provider, 'Docker')

    @tier2
    def test_positive_create_with_template(self):
        """Create new location with config template assigned to it

        :id: bf2daa6b-6478-472d-89f1-bfa74a75c349

        :expectedresults: Location created successfully and list of config
            templates assigned to that location should contain expected one

        :CaseLevel: Integration
        """
        template = entities.ConfigTemplate().create()
        location = entities.Location(config_template=[template]).create()
        self.assertGreaterEqual(len(location.config_template), 1)
        self.assertNotEqual(
            [ct for ct in location.config_template if ct.id == template.id],
            []
        )

    @tier2
    def test_positive_create_with_domain(self):
        """Create new location with assigned domain to it

        :id: 3f79a584-e195-4f1d-a978-777bae200251

        :expectedresults: Location created successfully and has correct and
            expected domain assigned to it

        :CaseLevel: Integration
        """
        domain = entities.Domain().create()
        location = entities.Location(domain=[domain]).create()
        self.assertEqual(location.domain[0].id, domain.id)

    @tier2
    def test_positive_create_with_subnet(self):
        """Create new location with assigned subnet to it

        :id: d6104c39-02d8-4051-a35b-334d9f260a33

        :expectedresults: Location created successfully and has correct subnet
            with expected network address assigned to it

        :CaseLevel: Integration
        """
        subnet = entities.Subnet().create()
        location = entities.Location(subnet=[subnet]).create()
        self.assertEqual(location.subnet[0].id, subnet.id)
        self.assertEqual(subnet.network, location.subnet[0].read().network)

    @tier2
    def test_positive_create_with_env(self):
        """Create new location with assigned environment to it

        :id: ac9cd08d-2033-4758-b4d1-c59a41198e92

        :expectedresults: Location created successfully and has correct and
            expected environment assigned to it

        :CaseLevel: Integration
        """
        env = entities.Environment().create()
        location = entities.Location(environment=[env]).create()
        self.assertEqual(location.environment[0].id, env.id)

    @tier2
    def test_positive_create_with_hostgroup(self):
        """Create new location with assigned host group to it

        :id: 154d55f8-41d7-411d-9a35-a2e8c639f144

        :expectedresults: Location created successfully and has correct and
            expected host group assigned to it

        :CaseLevel: Integration
        """
        host_group = entities.HostGroup().create()
        location = entities.Location(hostgroup=[host_group]).create()
        self.assertEqual(location.hostgroup[0].id, host_group.id)

    @tier2
    def test_positive_create_with_org(self):
        """Create new location with assigned organization to it

        :id: 5032a93f-4b37-4c19-b6d3-26e3a868d0f1

        :expectedresults: Location created successfully and has correct
            organization assigned to it with expected title

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        location = entities.Location(organization=[org]).create()
        self.assertEqual(location.organization[0].id, org.id)
        self.assertEqual(location.organization[0].read().title, org.title)

    @tier2
    def test_positive_create_with_orgs(self):
        """Basically, verifying that location with multiple entities
        assigned to it can be created in the system. Organizations were chosen
        for that purpose

        :id: f55ab63f-9c10-4f43-be69-d1f90e26fd51

        :expectedresults: Location created successfully and has correct
            organizations assigned to it

        :CaseLevel: Integration
        """
        orgs_amount = randint(3, 5)
        org_ids = [
            entities.Organization().create().id for _ in range(orgs_amount)
        ]
        location = entities.Location(organization=org_ids).create()
        self.assertEqual(len(location.organization), orgs_amount)
        for org in location.organization:
            self.assertIn(org.id, org_ids)

    @run_in_one_thread
    @tier2
    def test_positive_create_with_capsule(self):
        """Create new location with assigned capsule to it

        :id: 73f07e4b-b180-4906-8189-e9c0345abc5c

        :expectedresults: Location created successfully and has correct capsule
            assigned to it

        :CaseLevel: Integration
        """
        proxy_id = self._make_proxy()['id']

        proxy = entities.SmartProxy(id=proxy_id).read()
        location = entities.Location(smart_proxy=[proxy]).create()
        # Add location to cleanup list
        self.addCleanup(location_cleanup, location.id)

        self.assertEqual(location.smart_proxy[0].id, proxy.id)
        self.assertEqual(location.smart_proxy[0].read().name, proxy.name)

    @tier1
    def test_positive_delete(self):
        """Delete location

        :id: 63691139-45de-4e15-9abb-66c90808cbbb

        :expectedresults: Location was deleted

        :CaseImportance: Critical
        """
        location = entities.Location().create()
        location.delete()
        with self.assertRaises(HTTPError):
            location.read()

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

    @tier1
    def test_positive_update_description(self):
        """Update location with new description

        :id: 1340811a-43db-4aab-93b4-c36e438281a6

        :expectedresults: Location updated successfully and description was
            changed

        :CaseImportance: Critical
        """
        for new_description in valid_loc_data_list():
            with self.subTest(new_description):
                location = entities.Location().create()
                location.description = new_description
                self.assertEqual(
                    location.update(['description']).description,
                    new_description
                )

    @tier2
    def test_positive_update_user(self):
        """Update location with new user

        :id: 83ddb92d-f25d-44c0-87e7-631bdfc1f792

        :expectedresults: Location updated successfully and has correct user
            assigned

        :CaseLevel: Integration
        """
        location = entities.Location(user=[entities.User().create()]).create()
        new_user = entities.User().create()
        location.user = [new_user]
        self.assertEqual(location.update(['user']).user[0].id, new_user.id)

    @tier2
    def test_positive_update_libvirt_compresource(self):
        """Update location with new Libvirt compute resource

        :id: 9d0aef06-25dd-4352-8045-00b24b79b514

        :expectedresults: Location updated successfully and has correct Libvirt
            compute resource assigned

        :CaseLevel: Integration
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

    @tier2
    def test_positive_update_docker_compresource(self):
        """Update location with new Docker compute resource

        :id: 01ee537e-1629-44ab-b8f1-bb9a304050d6

        :expectedresults: Location updated successfully and has correct Docker
            compute resource assigned

        :CaseLevel: Integration
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

    @tier2
    def test_positive_update_template(self):
        """Update location with new config template

        :id: 9c8a1306-b0c7-4f72-8a31-4ff441bf5c75

        :expectedresults: Location updated successfully and has correct config
            template assigned

        :CaseLevel: Integration
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

    @tier2
    def test_positive_update_domain(self):
        """Update location with new domain

        :id: 1016dfb9-8103-45f1-8738-0579fa9754c1

        :expectedresults: Location updated successfully and has correct domain
            assigned

        :CaseLevel: Integration
        """
        location = entities.Location(
            domain=[entities.Domain().create()],
        ).create()
        domain = entities.Domain().create()
        location.domain = [domain]
        self.assertEqual(location.update(['domain']).domain[0].id, domain.id)

    @tier2
    def test_positive_update_subnet(self):
        """Update location with new subnet

        :id: 67e5516a-26e2-4d44-9c62-5bb35486cfa7

        :expectedresults: Location updated successfully and has correct subnet
            assigned

        :CaseLevel: Integration
        """
        location = entities.Location(
            subnet=[entities.Subnet().create()],
        ).create()
        subnet = entities.Subnet().create()
        location.subnet = [subnet]
        self.assertEqual(location.update(['subnet']).subnet[0].id, subnet.id)

    @tier2
    def test_positive_update_env(self):
        """Update location with new environment

        :id: 900a2441-4897-4e44-b8e4-bf7a956292ac

        :expectedresults: Location updated successfully and has correct
            environment assigned

        :CaseLevel: Integration
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

    @tier2
    def test_positive_update_hostgroup(self):
        """Update location with new host group

        :id: 8f3f4569-8f96-46e2-bd01-7712bb9fa4f6

        :expectedresults: Location updated successfully and has correct host
            group assigned

        :CaseLevel: Integration
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

    @tier2
    def test_positive_update_org(self):
        """Update location with new organization

        :id: 4791027f-f236-4152-ba20-b8f9624316c5

        :expectedresults: Location updated successfully and has correct
            organization assigned

        :CaseLevel: Integration
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

    @tier2
    def test_positive_update_orgs(self):
        """Update location with with multiple organizations

        :id: e53a0a93-5c7b-4e5b-99cb-decc123deeb6

        :expectedresults: Location created successfully and has correct
            organizations assigned

        :CaseLevel: Integration
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

    @run_in_one_thread
    @tier2
    def test_positive_update_capsule(self):
        """Update location with new capsule

        :id: 2786146f-f466-4ed8-918a-5f46806558e2

        :expectedresults: Location updated successfully and has correct capsule
            assigned

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

    @tier1
    def test_negative_update_name(self):
        """Try to update location using invalid names only

        :id: dd1e2bf5-44a8-4d15-ac4d-ae1dcc84b7fc

        :expectedresults: Location is not updated

        :CaseImportance: Critical
        """
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                location = entities.Location().create()
                location.name = new_name
                with self.assertRaises(HTTPError):
                    self.assertNotEqual(
                        location.update(['name']).name,
                        new_name
                    )

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

    @run_in_one_thread
    @skip_if_bug_open('bugzilla', 1398695)
    @tier2
    def test_positive_remove_capsule(self):
        """Remove a capsule from location

        :id: 43221ef8-054b-4311-8be0-e02f32e30d98

        :expectedresults: Capsule was removed successfully

        :CaseLevel: Integration
        """
        proxy_id = self._make_proxy()['id']

        proxy = entities.SmartProxy(id=proxy_id).read()
        location = entities.Location(smart_proxy=[proxy]).create()
        # Add location to cleanup list
        self.addCleanup(location_cleanup, location.id)

        location.smart_proxy = []
        location = location.update(['smart_proxy'])
        self.assertEqual(len(location.smart_proxy), 0)

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
