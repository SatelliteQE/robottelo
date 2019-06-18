# -*- encoding: utf-8 -*-
"""Tests for the ``hostgroups`` paths.

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: HostGroup

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint

from fauxfactory import gen_string
from nailgun import client, entities, entity_fields
from requests.exceptions import HTTPError

from robottelo.api.utils import promote, one_to_one_names
from robottelo.config import settings
from robottelo.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.datafactory import invalid_values_list, valid_hostgroups_list
from robottelo.decorators import (
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
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

    @upgrade
    @tier3
    def test_verify_bugzilla_1107708(self):
        """Host that created from HostGroup entity with PuppetClass
        assigned to it should inherit such puppet class information under
        'all_puppetclasses' field

        :id: 7b840f3d-413c-40bb-9a7d-cd9dad3c0737

        :expectedresults: Host inherited 'all_puppetclasses' details from
            HostGroup that was used for such Host create procedure

        :BZ: 1107708, 1222118, 1487586

        :CaseLevel: System
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
        environment.location = [location]
        environment.update()

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
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lc_env.id,
            },
            name=gen_string('alpha')
        ).create(False)
        host_attrs = host.read_json()
        self.assertEqual(len(host_attrs['all_puppetclasses']), 1)
        self.assertEqual(host_attrs['all_puppetclasses'][0]['name'], 'ntp')

    @upgrade
    @tier3
    def test_rebuild_config(self):
        """ 'Rebuild orchestration config' of an existing host group

        :id: 58bf7015-18fc-4d25-9b64-7f2dd6dde425

        :expectedresults: rebuild hostgroup orchestration configs successfully.

        :BZ: 1686493

        :CaseLevel: System
        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        content_view = entities.ContentView(organization=self.org).create()
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], environment_id=lce.id)
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        entities.Host(
            hostgroup=hostgroup,
            location=self.loc,
            organization=self.org,
            managed=True,
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lce.id,
            },
            ).create()
        hostgroup = hostgroup.read()
        self.assertEqual(hostgroup.rebuild_config()['message'],
                         'Configuration successfully rebuilt.')

    @tier1
    def test_positive_create_with_name(self):
        """Create a hostgroup with different names

        :id: fd5d353c-fd0c-4752-8a83-8f399b4c3416

        :expectedresults: A hostgroup is created with expected name

        :CaseImportance: Critical
        """
        for name in valid_hostgroups_list():
            with self.subTest(name):
                hostgroup = entities.HostGroup(
                    location=[self.loc],
                    name=name,
                    organization=[self.org],
                ).create()
                self.assertEqual(name, hostgroup.name)

    @tier1
    def test_positive_clone(self):
        """Create a hostgroup by cloning an existing one

        :id: 44ac8b3b-9cb0-4a9e-ad9b-2c67b2411922

        :expectedresults: A hostgroup is cloned with same parameters

        :CaseImportance: Critical
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        hostgroup_cloned_name = gen_string('alpha')
        hostgroup_cloned = entities.HostGroup(
            id=hostgroup.id
        ).clone(data={'name': hostgroup_cloned_name})
        hostgroup_origin = hostgroup.read_json()

        # remove unset values before comparison
        unset_keys = set(hostgroup_cloned) - set(hostgroup_origin)
        for key in unset_keys:
            del hostgroup_cloned[key]

        # remove unique values before comparison
        uniqe_keys = (u'updated_at', u'created_at', u'title', u'id', u'name')
        for key in uniqe_keys:
            del hostgroup_cloned[key]

        self.assertDictContainsSubset(hostgroup_cloned, hostgroup_origin)
        self.assertEqual(hostgroup_cloned, hostgroup_cloned)

    @tier2
    def test_positive_create_with_parent(self):
        """Create a hostgroup with parent hostgroup specified

        :id: 308d6921-0bf1-4fae-8bcf-7b312208e27c

        :expectedresults: A hostgroup is created with expected parent hostgroup
            assigned
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

        :id: 528afd01-356a-4082-9e88-a5b2a715a792

        :expectedresults: A hostgroup is created with expected environment
            assigned

        :CaseLevel: Integration
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

        :id: ca443d3f-2b99-4f0e-b92e-37c3e9fcc460

        :expectedresults: A hostgroup is created with expected operating system
            assigned

        :CaseLevel: Integration
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

        :id: c2f50b94-fa80-49c9-8279-76cfe458bc74

        :expectedresults: A hostgroup is created with expected architecture
            assigned

        :CaseLevel: Integration
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

        :id: b0b93207-a8bc-4af7-8ccd-d0bbf46dc0b0

        :expectedresults: A hostgroup is created with expected media assigned

        :CaseLevel: Integration
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

        :id: f161fd59-fa38-4c4e-a641-489f754d5977

        :expectedresults: A hostgroup is created with expected partition table
            assigned

        :CaseLevel: Integration
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

    @tier2
    def test_positive_create_with_puppet_ca_proxy(self):
        """Create a hostgroup with puppet CA proxy specified

        :id: 5c715ee8-2fd6-42c6-aece-037733f67454

        :expectedresults: A hostgroup is created with expected puppet CA proxy
            assigned

        :CaseLevel: Integration
        """
        proxy = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            puppet_ca_proxy=proxy,
        ).create()
        self.assertEqual(hostgroup.puppet_ca_proxy.read().name, proxy.name)

    @tier2
    def test_positive_create_with_subnet(self):
        """Create a hostgroup with subnet specified

        :id: affcaa2e-e22f-4601-97b2-4ca516f6ad2b

        :expectedresults: A hostgroup is created with expected subnet assigned

        :CaseLevel: Integration
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

        :id: 4f4aee5d-1f43-45e6-ac60-0573083dbcee

        :expectedresults: A hostgroup is created with expected domain assigned

        :CaseLevel: Integration
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

    @stubbed('Remove stub once proper infrastructure will be created')
    @tier2
    def test_positive_create_with_realm(self):
        """Create a hostgroup with realm specified

        :id: 4f07ff8d-746f-4ab5-ae0b-03d629f6296c

        :expectedresults: A hostgroup is created with expected realm assigned

        :CaseLevel: Integration
        """
        realm = entities.Realm(
            location=[self.loc],
            organization=[self.org],
            realm_proxy=entities.SmartProxy().search(
                query={'search': 'url = https://{0}:9090'.format(
                    settings.server.hostname)}
            )[0]
        ).create()
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            realm=realm,
        ).create()
        self.assertEqual(hostgroup.realm.read().name, realm.name)

    @tier2
    def test_positive_create_with_puppet_proxy(self):
        """Create a hostgroup with puppet proxy specified

        :id: 4f39f246-d12f-468c-a33b-66486c3806fe

        :expectedresults: A hostgroup is created with expected puppet proxy
            assigned

        :CaseLevel: Integration
        """
        proxy = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            puppet_proxy=proxy,
        ).create()
        self.assertEqual(hostgroup.puppet_proxy.read().name, proxy.name)

    @tier2
    def test_positive_create_with_content_source(self):
        """Create a hostgroup with content source specified

        :id: 39a6273e-8301-449a-a9d3-e3b61cda1e81

        :expectedresults: A hostgroup is created with expected content source
            assigned

        :CaseLevel: Integration
        """
        content_source = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
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

        :id: 43dfd2e9-68fe-4682-9cac-61c622c11126

        :expectedresults: A hostgroup is created with expected content view
            assigned

        :CaseLevel: Integration
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

        :id: 92215990-0754-429a-8fa2-c47806ece8a6

        :expectedresults: A hostgroup is created with expected lifecycle
            environment assigned

        :CaseLevel: Integration
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

        :id: 0c2ee2ff-9e7a-4931-8cea-f4eecbd8c4c0

        :expectedresults: A hostgroup is created with expected multiple
            locations assigned

        :CaseLevel: Integration
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

        :id: 09642238-cf0d-469a-a0b5-c167b1b8edf5

        :expectedresults: A hostgroup is created with expected multiple
            organizations assigned

        :CaseLevel: Integration
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

        :id: 8abb151f-a058-4f47-a1c1-f60a32cd7572

        :expectedresults: A hostgroup is updated with expected name

        :CaseImportance: Critical
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
    @upgrade
    def test_positive_update_parent(self):
        """Update a hostgroup with a new parent hostgroup

        :id: 6766d2e6-2305-49db-8db5-8417cf00b0a8

        :expectedresults: A hostgroup is updated with expected parent hostgroup
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

        :id: 24f3852d-a94a-4d85-ab7b-afe845832d94

        :expectedresults: A hostgroup is updated with expected environment

        :CaseLevel: Integration
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

        :id: c52cdc4f-499b-4a5e-ab7b-a172db42b038

        :expectedresults: A hostgroup is updated with expected operating system

        :CaseLevel: Integration
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

        :id: 57890ca6-dec7-43fe-ae4b-336cc2268d01

        :expectedresults: A hostgroup is updated with expected architecture

        :CaseLevel: Integration
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

        :id: 9b6ffbb8-0518-4900-95fd-49fc1d90a4be

        :expectedresults: A hostgroup is updated with expected media

        :CaseLevel: Integration
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

        :id: 95fccc76-33c6-45a3-842e-61917cce40fc

        :expectedresults: A hostgroup is updated with expected partition table

        :CaseLevel: Integration
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

    @tier2
    def test_positive_update_puppet_ca_proxy(self):
        """Update a hostgroup with a new puppet CA proxy

        :id: fd13ab0e-1a5b-48a0-a852-3fff8306271f

        :expectedresults: A hostgroup is updated with expected puppet CA proxy

        :CaseLevel: Integration
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_proxy = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup.puppet_ca_proxy = new_proxy
        hostgroup = hostgroup.update(['puppet_ca_proxy'])
        self.assertEqual(hostgroup.puppet_ca_proxy.read().name, new_proxy.name)

    @tier2
    def test_positive_update_subnet(self):
        """Update a hostgroup with a new subnet

        :id: 2b539fd9-5fcf-4d74-9cd8-3b3997bac992

        :expectedresults: A hostgroup is updated with expected subnet

        :CaseLevel: Integration
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

        :id: db7b79e9-a833-4d93-96e2-d9adc9f35c21

        :expectedresults: A hostgroup is updated with expected domain

        :CaseLevel: Integration
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

    @stubbed('Remove stub once proper infrastructure will be created')
    @tier2
    def test_positive_update_realm(self):
        """Update a hostgroup with a new realm

        :id: fd9d141f-7a71-4439-92c7-1dbc1eea4772

        :expectedresults: A hostgroup is updated with expected realm

        :CaseLevel: Integration
        """
        realm = entities.Realm(
            location=[self.loc],
            organization=[self.org],
            realm_proxy=entities.SmartProxy().search(
                query={'search': 'url = https://{0}:9090'.format(
                    settings.server.hostname)}
            )[0]
        ).create()
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
            realm=realm,
        ).create()
        new_realm = entities.Realm(
            location=[self.loc],
            organization=[self.org],
            realm_proxy=entities.SmartProxy().search(
                query={'search': 'url = https://{0}:9090'.format(
                    settings.server.hostname)}
            )[0]
        ).create()
        hostgroup.realm = new_realm
        hostgroup = hostgroup.update(['realm'])
        self.assertEqual(hostgroup.realm.read().name, new_realm.name)

    @tier2
    def test_positive_update_puppet_proxy(self):
        """Update a hostgroup with a new puppet proxy

        :id: 86eca603-2cdd-4563-b6f6-aaa5cea1a723

        :expectedresults: A hostgroup is updated with expected puppet proxy

        :CaseLevel: Integration
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_proxy = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup.puppet_proxy = new_proxy
        hostgroup = hostgroup.update(['puppet_proxy'])
        self.assertEqual(hostgroup.puppet_proxy.read().name, new_proxy.name)

    @tier2
    def test_positive_update_content_source(self):
        """Update a hostgroup with a new puppet proxy

        :id: 02ef1340-a21e-41b7-8aa7-d6fdea196c16

        :expectedresults: A hostgroup is updated with expected puppet proxy

        :CaseLevel: Integration
        """
        hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
        new_content_source = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hostgroup.content_source = new_content_source
        hostgroup = hostgroup.update(['content_source'])
        self.assertEqual(
            hostgroup.content_source.read().name, new_content_source.name)

    @tier2
    def test_positive_update_cv(self):
        """Update a hostgroup with a new content view

        :id: 5fa39bc9-c780-49c5-b580-b973e2d25226

        :expectedresults: A hostgroup is updated with expected content view

        :CaseLevel: Integration
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

        :id: df89d8e3-bd36-4ad9-bde8-1872ae3dd918

        :expectedresults: A hostgroup is updated with expected lifecycle
            environment

        :CaseLevel: Integration
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

        :id: 62d88bb0-34d1-447f-ae69-b2122d8142b4

        :expectedresults: A hostgroup is updated with expected location

        :CaseLevel: Integration
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

        :id: 8f83983b-398f-40e4-8917-47b3205137d7

        :expectedresults: A hostgroup is updated with expected organization

        :CaseLevel: Integration
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

        :id: b045f7e8-d7c0-428b-a29c-8d54e53742e2

        :expectedresults: A hostgroup is updated with expected locations

        :CaseLevel: Integration
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

        :id: 5f6bd4f9-4bd6-4d7e-9a91-de824299020e

        :expectedresults: A hostgroup is updated with expected organizations

        :CaseLevel: Integration
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

        :id: bef6841b-5077-4b84-842e-a286bfbb92d2

        :expectedresults: A hostgroup is deleted

        :CaseImportance: Critical
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

        :id: 3f5aa17a-8db9-4fe9-b309-b8ec5e739da1

        :expectedresults: A hostgroup is not created

        :CaseImportance: Critical
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

        :id: 6d8c4738-a0c4-472b-9a71-27c8a3832335

        :expectedresults: A hostgroup is not updated

        :CaseImportance: Critical
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

    @tier2
    def test_positive_get_content_source(self):
        """Read a host group. Inspect the server's response.

        :id: 9d42f47a-2f08-45ad-97d0-de94f0f1de2f

        :expectedresults: The response contains both values for the
            ``content_source`` field.

        :CaseLevel: Integration
        """
        names = one_to_one_names('content_source')
        self.assertTrue(
            names.issubset(self.host_group_attrs),
            '{0} not found in {1}'.format(
                names.difference(self.host_group_attrs),
                self.host_group_attrs
            )
        )

    @tier2
    def test_positive_get_cv(self):
        """Read a host group. Inspect the server's response.

        :id: 7d36f33e-f161-4d2a-9ee4-8eb949ed4cbf

        :expectedresults: The response contains both values for the
            ``content_view`` field.

        :CaseLevel: Integration
        """
        names = one_to_one_names('content_view')
        self.assertTrue(
            names.issubset(self.host_group_attrs),
            '{0} not found in {1}'.format(
                names.difference(self.host_group_attrs),
                self.host_group_attrs
            )
        )

    @tier2
    def test_positive_get_lce(self):
        """Read a host group. Inspect the server's response.

        :id: efa17f59-47f9-40c6-821d-c348c4d852ff

        :expectedresults: The response contains both values for the
            ``lifecycle_environment`` field.

        :CaseLevel: Integration
        """
        names = one_to_one_names('lifecycle_environment')
        self.assertTrue(
            names.issubset(self.host_group_attrs),
            '{0} not found in {1}'.format(
                names.difference(self.host_group_attrs),
                self.host_group_attrs
            )
        )

    @tier2
    def test_positive_read_puppet_proxy_name(self):
        """Read a hostgroup created with puppet proxy and inspect server's
        response

        :id: f93d0866-0073-4577-8777-6d645b63264f

        :expectedresults: Field 'puppet_proxy_name' is returned

        :BZ: 1371900

        :CaseLevel: Integration
        """
        proxy = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hg = entities.HostGroup(puppet_proxy=proxy).create().read_json()
        self.assertIn('puppet_proxy_name', hg)
        self.assertEqual(proxy.name, hg['puppet_proxy_name'])

    @tier2
    def test_positive_read_puppet_ca_proxy_name(self):
        """Read a hostgroup created with puppet ca proxy and inspect server's
        response

        :id: ab151e09-8e64-4377-95e8-584629750659

        :expectedresults: Field 'puppet_ca_proxy_name' is returned

        :BZ: 1371900

        :CaseLevel: Integration
        """
        proxy = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        hg = entities.HostGroup(puppet_ca_proxy=proxy).create().read_json()
        self.assertIn('puppet_ca_proxy_name', hg)
        self.assertEqual(proxy.name, hg['puppet_ca_proxy_name'])
