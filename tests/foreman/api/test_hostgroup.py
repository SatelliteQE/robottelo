# -*- encoding: utf-8 -*-
"""Tests for the ``hostgroups`` paths."""
from fauxfactory import gen_string
from nailgun import client, entities, entity_fields
from robottelo.api.utils import promote, one_to_one_names
from robottelo.config import settings
from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.decorators import (
    skip_if_bug_open,
    tier1,
    tier3,
)
from robottelo.helpers import get_data_file
from robottelo.test import APITestCase


class HostGroupTestCase(APITestCase):
    """Tests for host group entity."""

    @tier3
    @skip_if_bug_open('bugzilla', 1222118)
    def test_verify_bugzilla_1107708(self):
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
            auth=settings.server.get_credentials(),
            verify=False,
        )
        response.raise_for_status()
        results = response.json()['results']
        puppet_class_id = results['ntp'][0]['id']

        # Assign puppet class
        client.post(
            host_group.path('self') + '/puppetclass_ids',
            data={u'puppetclass_id': puppet_class_id},
            auth=settings.server.get_credentials(),
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
class HostGroupMissingAttrTestCase(APITestCase):
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. The ``one_to_*_names`` functions know what names
    Satellite may assign to fields.
    """

    @classmethod
    def setUpClass(cls):
        """Create a ``HostGroup``."""
        super(HostGroupMissingAttrTestCase, cls).setUpClass()
        host_group = entities.HostGroup().create()
        cls.host_group_attrs = set(host_group.read_json().keys())

    @tier1
    def test_positive_get_content_source(self):
        """@Test: Read a host group. Inspect the server's response.

        @Assert: The response contains some value for the ``content_source``
        field.

        @Feature: HostGroup
        """
        names = one_to_one_names('content_source')
        self.assertGreater(
            len(names & self.host_group_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.host_group_attrs)
        )

    @tier1
    def test_positive_get_cv(self):
        """@Test: Read a host group. Inspect the server's response.

        @Assert: The response contains some value for the ``content_view``
        field.

        @Feature: HostGroup
        """
        names = one_to_one_names('content_view')
        self.assertGreater(
            len(names & self.host_group_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.host_group_attrs)
        )

    @tier1
    def test_positive_get_lce(self):
        """@Test: Read a host group. Inspect the server's response.

        @Assert: The response contains some value for the
        ``lifecycle_environment`` field.

        @Feature: HostGroup
        """
        names = one_to_one_names('lifecycle_environment')
        self.assertGreater(
            len(names & self.host_group_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.host_group_attrs)
        )
