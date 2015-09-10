# -*- encoding: utf-8 -*-
"""Tests for the ``hostgroups`` paths."""
from fauxfactory import gen_string
from nailgun import client, entities, entity_fields
from nailgun.entity_mixins import _get_entity_id
from robottelo.api.utils import promote
from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.decorators import skip_if_bug_open, stubbed
from robottelo.helpers import get_data_file, get_server_credentials
from robottelo.test import APITestCase


class HostGroupTestCase(APITestCase):
    """Tests for host group entity."""

    @skip_if_bug_open('bugzilla', 1222118)
    def test_bz_1107708(self):
        """@Test: Host that created from HostGroup entity with PuppetClass
        assigned to it should inherit such puppet class information under
        'all_puppetclasses' field

        @Feature: HostGroup and Host

        @Assert: Host inherited 'all_puppetclasses' details from HostGroup that
        was used for such Host create procedure

        """
        # Creating entities like organization, content view and lifecycle_env
        # with not utf-8 names for easier interaction with puppet environment
        # further in test
        org = entities.Organization(name=gen_string('alpha')).create()
        location = entities.Location(organization=[org]).create()
        # Creating puppet repository with puppet module assigned to it
        product = entities.Product(organization=org).create()
        puppet_repo = entities.Repository(
            content_type='puppet',
            product=product,
        ).create()
        # Working with 'ntp' module as we know for sure that it contains at
        # least few puppet classes
        with open(get_data_file(PUPPET_MODULE_NTP_PUPPETLABS), 'rb') as handle:
            puppet_repo.upload_content(files={'content': handle})

        content_view = entities.ContentView(
            name=gen_string('alpha'),
            organization=org,
        ).create()

        result = content_view.available_puppet_modules()['results']
        self.assertEqual(len(result), 1)
        entities.ContentViewPuppetModule(
            author=result[0]['author'],
            name=result[0]['name'],
            content_view=content_view,
        ).create()
        content_view.publish()
        content_view = content_view.read()
        lc_env = entities.LifecycleEnvironment(
            name=gen_string('alpha'),
            organization=org,
        ).create()
        promote(content_view.version[0], lc_env.id)
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        self.assertEqual(len(content_view.puppet_module), 1)

        # Form environment name variable for our test
        env_name = 'KT_{0}_{1}_{2}_{3}'.format(
            org.name,
            lc_env.name,
            content_view.name,
            str(content_view.id),
        )

        # Get all environments for current organization.
        # We have two environments (one created after publishing and one more
        # was created after promotion), so we need to select promoted one
        environments = entities.Environment().search(
            query={'organization_id': org.id}
        )
        self.assertEqual(len(environments), 2)
        environments = [
            environment for environment in environments
            if environment.name == env_name
        ]
        self.assertEqual(len(environments), 1)
        environment = environments[0].read()

        # Create a host group and it dependencies.
        mac = entity_fields.MACAddressField().gen_value()
        root_pass = entity_fields.StringField(length=(8, 30)).gen_value()
        domain = entities.Domain().create()
        architecture = entities.Architecture().create()
        ptable = entities.PartitionTable().create()
        operatingsystem = entities.OperatingSystem(
            architecture=[architecture],
            ptable=[ptable],
        ).create()
        medium = entities.Media(operatingsystem=[operatingsystem]).create()
        host_group = entities.HostGroup(
            architecture=architecture,
            domain=domain,
            environment=environment,
            location=[location.id],
            medium=medium,
            name=gen_string('alpha'),
            operatingsystem=operatingsystem,
            organization=[org.id],
            ptable=ptable,
        ).create()
        self.assertEqual(len(host_group.read_json()['all_puppetclasses']), 0)

        # Get puppet class id for ntp module
        response = client.get(
            environment.path('self') + '/puppetclasses',
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()
        results = response.json()['results']
        puppet_class_id = results['ntp'][0]['id']

        # Assign puppet class
        client.post(
            host_group.path('self') + '/puppetclass_ids',
            data={u'puppetclass_id': puppet_class_id},
            auth=get_server_credentials(),
            verify=False
        ).raise_for_status()
        host_group_attrs = host_group.read_json()
        self.assertEqual(len(host_group_attrs['all_puppetclasses']), 1)
        self.assertEqual(
            host_group_attrs['all_puppetclasses'][0]['name'],
            'ntp',
        )

        # Create Host entity using HostGroup
        host = entities.Host(
            hostgroup=host_group,
            mac=mac,
            root_pass=root_pass,
            environment=environment,
            location=location,
            organization=org,
            name=gen_string('alpha')
        ).create(False)
        host_attrs = host.read_json()
        self.assertEqual(len(host_attrs['all_puppetclasses']), 1)
        self.assertEqual(host_attrs['all_puppetclasses'][0]['name'], 'ntp')


@skip_if_bug_open('bugzilla', 1235377)
class MissingAttrTestCase(APITestCase):
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. Satellite may name a given attribute in one of several
    ways, and the ``_get_entity_id`` method knows about all the names that may
    be assigned to an attribute. For example, this will return ``5``::

        _get_entity_id('content_source', {'content_source_id': 5})

    """

    @classmethod
    def setUpClass(cls):
        """Create a ``HostGroup``."""
        host_group = entities.HostGroup().create()
        cls.host_group_attrs = host_group.read_json()

    def test_get_content_source(self):
        """@Test: Read a host group. Inspect the server's response.

        @Assert: The response contains some value for the ``content_source``
        field.

        @Feature: HostGroup

        """
        _get_entity_id('content_source', self.host_group_attrs)

    def test_get_content_view(self):
        """@Test: Read a host group. Inspect the server's response.

        @Assert: The response contains some value for the ``content_view``
        field.

        @Feature: HostGroup

        """
        _get_entity_id('content_view', self.host_group_attrs)

    def test_get_lifecycle_environment(self):
        """@Test: Read a host group. Inspect the server's response.

        @Assert: The response contains some value for the
        ``lifecycle_environment`` field.

        @Feature: HostGroup

        """
        _get_entity_id('lifecycle_environment', self.host_group_attrs)


class HostGroupTestCaseStub(APITestCase):
    """Incomplete tests for host groups.

    When implemented, each of these tests should probably be data-driven. A
    decorator of this form might be used::

        @data(
            name is alpha,
            name is alpha_numeric,
            name is html,
            name is latin1,
            name is numeric,
            name is utf-8,
        )

    """

    @stubbed()
    def test_remove_hostgroup_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        name and hostgroup name
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

    @stubbed()
    def test_remove_hostgroup_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        ID and hostgroup name
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

    @stubbed()
    def test_remove_hostgroup_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        name and hostgroup ID
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

    @stubbed()
    def test_remove_hostgroup_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        ID and hostgroup ID
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

    @stubbed()
    def test_add_hostgroup_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        name and hostgroup name
        @assert: hostgroup is added to organization
        @status: manual
        """

    @stubbed()
    def test_add_hostgroup_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        ID and hostgroup name
        @assert: hostgroup is added to organization
        @status: manual
        """

    @stubbed()
    def test_add_hostgroup_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        name and hostgroup ID
        @assert: hostgroup is added to organization
        @status: manual
        """

    @stubbed()
    def test_add_hostgroup_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        ID and hostgroup ID
        @assert: hostgroup is added to organization
        @status: manual
        """
