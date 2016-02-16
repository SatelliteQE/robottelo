# -*- encoding: utf-8 -*-
"""Tests for the ``hostgroups`` paths."""
from fauxfactory import gen_string
from nailgun import client, entities, entity_fields
from random import randint
from requests.exceptions import HTTPError
from robottelo.api.utils import promote, one_to_one_names
from robottelo.config import settings
from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.datafactory import invalid_values_list, valid_hostgroups_list
from robottelo.decorators import (
    skip_if_bug_open,
    tier1,
    tier2,
    tier3,
)
from robottelo.helpers import get_data_file
from robottelo.test import APITestCase


class HostGroupTestCase(APITestCase):
    """Tests for host group entity."""

    @classmethod
    def setUpClass(cls):
        """Set up organization and location for tests."""
        super(HostGroupTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.loc = entities.Location(organization=[cls.org]).create()

    @tier3
    @skip_if_bug_open('bugzilla', 1222118)
    def test_verify_bugzilla_1107708(self):
        """Host that created from HostGroup entity with PuppetClass
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

    @tier1
    def test_positive_create_with_name(self):
        """Create a hostgroup with different names

        @feature: HostGroup

        @assert: A hostgroup is created with expected name
        """
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup = entities.HostGroup(
                    location=[self.loc],
                    name=name,
                    organization=[self.org],
                ).create()
                self.assertEqual(name, hostgroup.name)

    @tier2
    def test_positive_create_with_parent(self):
        """Create a hostgroup with parent hostgroup specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected parent hostgroup assigned
        """
        parent_hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            parent=parent_hostgroup,
        ).create()
        self.assertEqual(hostgroup.parent.read().name, parent_hostgroup.name)

    @tier2
    def test_positive_create_with_env(self):
        """Create a hostgroup with environment specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected environment assigned
        """
        env = entities.Environment(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            environment=env,
            location=[self.loc],
            organization=[self.org],
        ).create()
        self.assertEqual(hostgroup.environment.read().name, env.name)

    @tier2
    def test_positive_create_with_os(self):
        """Create a hostgroup with operating system specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected operating system assigned
        """
        arch = entities.Architecture().create()
        ptable = entities.PartitionTable().create()
        os = entities.OperatingSystem(
            architecture=[arch],
            ptable=[ptable],
        ).create()
        hostgroup = entities.HostGroup(
            architecture=arch,
            location=[self.loc],
            operatingsystem=os,
            organization=[self.org],
            ptable=ptable,
        ).create()
        self.assertEqual(hostgroup.operatingsystem.read().name, os.name)

    @tier2
    def test_positive_create_with_arch(self):
        """Create a hostgroup with architecture specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected architecture assigned
        """
        arch = entities.Architecture().create()
        hostgroup = entities.HostGroup(
            architecture=arch,
            location=[self.loc],
            organization=[self.org],
        ).create()
        self.assertEqual(hostgroup.architecture.read().name, arch.name)

    @tier2
    def test_positive_create_with_media(self):
        """Create a hostgroup with media specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected media assigned
        """
        arch = entities.Architecture().create()
        ptable = entities.PartitionTable().create()
        os = entities.OperatingSystem(
            architecture=[arch],
            ptable=[ptable],
        ).create()
        media = entities.Media(
            operatingsystem=[os],
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            architecture=arch,
            location=[self.loc],
            medium=media,
            operatingsystem=os,
            organization=[self.org],
            ptable=ptable,
        ).create()
        self.assertEqual(hostgroup.medium.read().name, media.name)

    @tier2
    def test_positive_create_with_ptable(self):
        """Create a hostgroup with partition table specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected partition table assigned
        """
        arch = entities.Architecture().create()
        ptable = entities.PartitionTable().create()
        os = entities.OperatingSystem(
            architecture=[arch],
            ptable=[ptable],
        ).create()
        hostgroup = entities.HostGroup(
            architecture=arch,
            location=[self.loc],
            operatingsystem=os,
            organization=[self.org],
            ptable=ptable,
        ).create()
        self.assertEqual(hostgroup.ptable.read().name, ptable.name)

    @tier1
    def test_positive_create_with_puppet_ca_proxy(self):
        """Create a hostgroup with puppet CA proxy specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected puppet CA proxy assigned
        """
        proxy = entities.SmartProxy().search()[0]
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            puppet_ca_proxy=proxy,
        ).create()
        self.assertEqual(hostgroup.puppet_ca_proxy.read().name, proxy.name)

    @tier2
    def test_positive_create_with_subnet(self):
        """Create a hostgroup with subnet specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected subnet assigned
        """
        subnet = entities.Subnet(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            subnet=subnet,
        ).create()
        self.assertEqual(hostgroup.subnet.read().name, subnet.name)

    @tier2
    def test_positive_create_with_domain(self):
        """Create a hostgroup with domain specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected domain assigned
        """
        domain = entities.Domain(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            domain=domain,
            location=[self.loc],
            organization=[self.org],
        ).create()
        self.assertEqual(hostgroup.domain.read().name, domain.name)

    @tier2
    def test_positive_create_with_realm(self):
        """Create a hostgroup with realm specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected realm assigned
        """
        realm = entities.Realm(
            location=[self.loc],
            organization=[self.org],
            realm_proxy=entities.SmartProxy().search()[0],
        ).create()
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            realm=realm,
        ).create()
        self.assertEqual(hostgroup.realm.read().name, realm.name)

    @tier1
    def test_positive_create_with_puppet_proxy(self):
        """Create a hostgroup with puppet proxy specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected puppet proxy assigned
        """
        proxy = entities.SmartProxy().search()[0]
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            puppet_proxy=proxy,
        ).create()
        self.assertEqual(hostgroup.puppet_proxy.read().name, proxy.name)

    @tier1
    def test_positive_create_with_content_source(self):
        """Create a hostgroup with content source specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected content source assigned
        """
        content_source = entities.SmartProxy().search()[0]
        hostgroup = entities.HostGroup(
            content_source=content_source,
            location=[self.loc],
            organization=[self.org],
        ).create()
        self.assertEqual(
            hostgroup.content_source.read().name, content_source.name)

    @tier2
    def test_positive_create_with_cv(self):
        """Create a hostgroup with content view specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected content view assigned
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.publish()
        content_view = content_view.read()
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(content_view.version[0], lce.id)
        hostgroup = entities.HostGroup(
            content_view=content_view,
            lifecycle_environment=lce,
            location=[self.loc],
            organization=[self.org],
        ).create()
        self.assertEqual(hostgroup.content_view.read().name, content_view.name)

    @tier2
    def test_positive_create_with_lce(self):
        """Create a hostgroup with lifecycle environment specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected lifecycle environment
        assigned
        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        hostgroup = entities.HostGroup(
            lifecycle_environment=lce,
            location=[self.loc],
            organization=[self.org],
        ).create()
        self.assertEqual(hostgroup.lifecycle_environment.read().name, lce.name)

    @tier2
    def test_positive_create_with_locs(self):
        """Create a hostgroup with multiple locations specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected multiple locations
        assigned
        """
        locs = [
            entities.Location(organization=[self.org]).create()
            for _ in range(randint(3, 5))
        ]
        hostgroup = entities.HostGroup(
            location=locs,
            organization=[self.org],
        ).create()
        self.assertEqual(
            set(loc.name for loc in locs),
            set(loc.read().name for loc in hostgroup.location)
        )

    @tier2
    def test_positive_create_with_orgs(self):
        """Create a hostgroup with multiple organizations specified

        @feature: HostGroup

        @assert: A hostgroup is created with expected multiple organizations
        assigned
        """
        orgs = [
            entities.Organization().create()
            for _ in range(randint(3, 5))
        ]
        hostgroup = entities.HostGroup(organization=orgs).create()
        self.assertEqual(
            set(org.name for org in orgs),
            set(org.read().name for org in hostgroup.organization)
        )

    @tier1
    def test_positive_update_name(self):
        """Update a hostgroup with a new name

        @feature: HostGroup

        @assert: A hostgroup is updated with expected name
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup.name = name
                hostgroup = hostgroup.update(['name'])
                self.assertEqual(name, hostgroup.name)

    @tier2
    def test_positive_update_parent(self):
        """Update a hostgroup with a new parent hostgroup

        @feature: HostGroup

        @assert: A hostgroup is updated with expected parent hostgroup
        """
        parent = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            parent=parent,
        ).create()
        new_parent = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup.parent = new_parent
        hostgroup = hostgroup.update(['parent'])
        self.assertEqual(hostgroup.parent.read().name, new_parent.name)

    @tier2
    def test_positive_update_env(self):
        """Update a hostgroup with a new environment

        @feature: HostGroup

        @assert: A hostgroup is updated with expected environment
        """
        env = entities.Environment(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            environment=env,
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_env = entities.Environment(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup.environment = new_env
        hostgroup = hostgroup.update(['environment'])
        self.assertEqual(hostgroup.environment.read().name, new_env.name)

    @tier2
    def test_positive_update_os(self):
        """Update a hostgroup with a new operating system

        @feature: HostGroup

        @assert: A hostgroup is updated with expected operating system
        """
        arch = entities.Architecture().create()
        ptable = entities.PartitionTable().create()
        os = entities.OperatingSystem(
            architecture=[arch],
            ptable=[ptable],
        ).create()
        hostgroup = entities.HostGroup(
            architecture=arch,
            location=[self.loc],
            operatingsystem=os,
            organization=[self.org],
            ptable=ptable,
        ).create()
        new_os = entities.OperatingSystem(
            architecture=[arch],
            ptable=[ptable],
        ).create()
        hostgroup.operatingsystem = new_os
        hostgroup = hostgroup.update(['operatingsystem'])
        self.assertEqual(hostgroup.operatingsystem.read().name, new_os.name)

    @tier2
    def test_positive_update_arch(self):
        """Update a hostgroup with a new architecture

        @feature: HostGroup

        @assert: A hostgroup is updated with expected architecture
        """
        hostgroup = entities.HostGroup(
            architecture=entities.Architecture().create(),
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_arch = entities.Architecture().create()
        hostgroup.architecture = new_arch
        hostgroup = hostgroup.update(['architecture'])
        self.assertEqual(hostgroup.architecture.read().name, new_arch.name)

    @tier2
    def test_positive_update_media(self):
        """Update a hostgroup with a new media

        @feature: HostGroup

        @assert: A hostgroup is updated with expected media
        """
        arch = entities.Architecture().create()
        ptable = entities.PartitionTable().create()
        os = entities.OperatingSystem(
            architecture=[arch],
            ptable=[ptable],
        ).create()
        media = entities.Media(
            operatingsystem=[os],
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            architecture=arch,
            location=[self.loc],
            medium=media,
            operatingsystem=os,
            organization=[self.org],
            ptable=ptable,
        ).create()
        new_media = entities.Media(
            operatingsystem=[os],
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup.medium = new_media
        hostgroup = hostgroup.update(['medium'])
        self.assertEqual(hostgroup.medium.read().name, new_media.name)

    @tier2
    def test_positive_update_ptable(self):
        """Update a hostgroup with a new partition table

        @feature: HostGroup

        @assert: A hostgroup is updated with expected partition table
        """
        arch = entities.Architecture().create()
        ptable = entities.PartitionTable().create()
        os = entities.OperatingSystem(
            architecture=[arch],
            ptable=[ptable],
        ).create()
        hostgroup = entities.HostGroup(
            architecture=arch,
            location=[self.loc],
            operatingsystem=os,
            organization=[self.org],
            ptable=ptable,
        ).create()
        new_ptable = entities.PartitionTable().create()
        os.ptable = [ptable, new_ptable]
        os.update(['ptable'])
        hostgroup.ptable = new_ptable
        hostgroup = hostgroup.update(['ptable'])
        self.assertEqual(hostgroup.ptable.read().name, new_ptable.name)

    @tier1
    def test_positive_update_puppet_ca_proxy(self):
        """Update a hostgroup with a new puppet CA proxy

        @feature: HostGroup

        @assert: A hostgroup is updated with expected puppet CA proxy
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_proxy = entities.SmartProxy().search()[0]
        hostgroup.puppet_ca_proxy = new_proxy
        hostgroup = hostgroup.update(['puppet_ca_proxy'])
        self.assertEqual(hostgroup.puppet_ca_proxy.read().name, new_proxy.name)

    @tier2
    def test_positive_update_subnet(self):
        """Update a hostgroup with a new subnet

        @feature: HostGroup

        @assert: A hostgroup is updated with expected subnet
        """
        subnet = entities.Subnet(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            subnet=subnet,
        ).create()
        new_subnet = entities.Subnet(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup.subnet = new_subnet
        hostgroup = hostgroup.update(['subnet'])
        self.assertEqual(hostgroup.subnet.read().name, new_subnet.name)

    @tier2
    def test_positive_update_domain(self):
        """Update a hostgroup with a new domain

        @feature: HostGroup

        @assert: A hostgroup is updated with expected domain
        """
        domain = entities.Domain(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup = entities.HostGroup(
            domain=domain,
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_domain = entities.Domain(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup.domain = new_domain
        hostgroup = hostgroup.update(['domain'])
        self.assertEqual(hostgroup.domain.read().name, new_domain.name)

    @tier2
    def test_positive_update_realm(self):
        """Update a hostgroup with a new realm

        @feature: HostGroup

        @assert: A hostgroup is updated with expected realm
        """
        realm = entities.Realm(
            location=[self.loc],
            organization=[self.org],
            realm_proxy=entities.SmartProxy().search()[0],
        ).create()
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            realm=realm,
        ).create()
        new_realm = entities.Realm(
            location=[self.loc],
            organization=[self.org],
            realm_proxy=entities.SmartProxy().search()[0],
        ).create()
        hostgroup.realm = new_realm
        hostgroup = hostgroup.update(['realm'])
        self.assertEqual(hostgroup.realm.read().name, new_realm.name)

    @tier1
    def test_positive_update_puppet_proxy(self):
        """Update a hostgroup with a new puppet proxy

        @feature: HostGroup

        @assert: A hostgroup is updated with expected puppet proxy
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_proxy = entities.SmartProxy().search()[0]
        hostgroup.puppet_proxy = new_proxy
        hostgroup = hostgroup.update(['puppet_proxy'])
        self.assertEqual(hostgroup.puppet_proxy.read().name, new_proxy.name)

    @tier1
    def test_positive_update_content_source(self):
        """Update a hostgroup with a new puppet proxy

        @feature: HostGroup

        @assert: A hostgroup is updated with expected puppet proxy
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_content_source = entities.SmartProxy().search()[0]
        hostgroup.content_source = new_content_source
        hostgroup = hostgroup.update(['content_source'])
        self.assertEqual(
            hostgroup.content_source.read().name, new_content_source.name)

    @tier2
    def test_positive_update_cv(self):
        """Update a hostgroup with a new content view

        @feature: HostGroup

        @assert: A hostgroup is updated with expected content view
        """
        content_view = entities.ContentView(organization=self.org).create()
        content_view.publish()
        content_view = content_view.read()
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(content_view.version[0], lce.id)
        hostgroup = entities.HostGroup(
            content_view=content_view,
            lifecycle_environment=lce,
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_cv = entities.ContentView(organization=self.org).create()
        new_cv.publish()
        new_cv = new_cv.read()
        promote(new_cv.version[0], lce.id)
        hostgroup.content_view = new_cv
        hostgroup = hostgroup.update(['content_view'])
        self.assertEqual(hostgroup.content_view.read().name, new_cv.name)

    @tier2
    def test_positive_update_lce(self):
        """Update a hostgroup with a new lifecycle environment

        @feature: HostGroup

        @assert: A hostgroup is updated with expected lifecycle environment
        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        hostgroup = entities.HostGroup(
            lifecycle_environment=lce,
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_lce = entities.LifecycleEnvironment(organization=self.org).create()
        hostgroup.lifecycle_environment = new_lce
        hostgroup = hostgroup.update(['lifecycle_environment'])
        self.assertEqual(
            hostgroup.lifecycle_environment.read().name, new_lce.name)

    @tier2
    def test_positive_update_loc(self):
        """Update a hostgroup with a new location

        @feature: HostGroup

        @assert: A hostgroup is updated with expected location
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_loc = entities.Location(organization=[self.org]).create()
        hostgroup.location = [new_loc]
        hostgroup = hostgroup.update(['location'])
        self.assertEqual(hostgroup.location[0].read().name, new_loc.name)

    @tier2
    def test_positive_update_org(self):
        """Update a hostgroup with a new organization

        @feature: HostGroup

        @assert: A hostgroup is updated with expected organization
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_org = entities.Organization().create()
        hostgroup.organization = [new_org]
        hostgroup = hostgroup.update(['organization'])
        self.assertEqual(hostgroup.organization[0].read().name, new_org.name)

    @tier2
    def test_positive_update_locs(self):
        """Update a hostgroup with new multiple locations

        @feature: HostGroup

        @assert: A hostgroup is updated with expected locations
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_locs = [
            entities.Location(organization=[self.org]).create()
            for _ in range(randint(3, 5))
        ]
        hostgroup.location = new_locs
        hostgroup = hostgroup.update(['location'])
        self.assertEqual(
            set(loc.name for loc in new_locs),
            set(loc.read().name for loc in hostgroup.location)
        )

    @tier2
    def test_positive_update_orgs(self):
        """Update a hostgroup with new multiple organizations

        @feature: HostGroup

        @assert: A hostgroup is updated with expected organizations
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_orgs = [
            entities.Organization().create()
            for _ in range(randint(3, 5))
        ]
        hostgroup.organization = new_orgs
        hostgroup = hostgroup.update(['organization'])
        self.assertEqual(
            set(org.name for org in new_orgs),
            set(org.read().name for org in hostgroup.organization)
        )

    @tier1
    def test_positive_delete(self):
        """Delete a hostgroup

        @feature: HostGroup

        @assert: A hostgroup is deleted
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup.delete()
        with self.assertRaises(HTTPError):
            hostgroup.read()

    @tier1
    def test_negative_create_with_name(self):
        """Attempt to create a hostgroup with invalid names

        @feature: HostGroup

        @assert: A hostgroup is not created
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.HostGroup(
                        location=[self.loc],
                        name=name,
                        organization=[self.org],
                    ).create()

    @tier1
    def test_negative_update_name(self):
        """Attempt to update a hostgroup with invalid names

        @feature: HostGroup

        @assert: A hostgroup is not updated
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        original_name = hostgroup.name
        for new_name in invalid_values_list():
            with self.subTest(new_name):
                hostgroup.name = new_name
                with self.assertRaises(HTTPError):
                    hostgroup.update(['name'])
                self.assertEqual(hostgroup.read().name, original_name)


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
        """Read a host group. Inspect the server's response.

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
        """Read a host group. Inspect the server's response.

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
        """Read a host group. Inspect the server's response.

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
