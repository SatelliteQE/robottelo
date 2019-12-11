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
    def test_inherit_puppetclass(self):
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

    @tier1
    def test_positive_create_with_properties(self):
        """Create a hostgroup with properties

        :id: 528afd01-356a-4082-9e88-a5b2a715a792

        :expectedresults: A hostgroup is created with expected properties,
            updated and deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        env = entities.Environment(
            location=[self.loc],
            organization=[self.org],
        ).create()
        parent_hostgroup = entities.HostGroup(
            location=[self.loc],
            organization=[self.org],
        ).create()
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
        proxy = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })[0]
        subnet = entities.Subnet(
            location=[self.loc],
            organization=[self.org],
        ).create()
        domain = entities.Domain(
            location=[self.loc],
            organization=[self.org],
        ).create()
        content_view = entities.ContentView(organization=self.org).create()
        content_view.publish()
        content_view = content_view.read()
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(content_view.version[0], lce.id)
        hostgroup = entities.HostGroup(
            architecture=arch,
            content_source=proxy,
            content_view=content_view,
            domain=domain,
            environment=env,
            lifecycle_environment=lce,
            location=[self.loc],
            medium=media,
            operatingsystem=os,
            organization=[self.org],
            parent=parent_hostgroup,
            ptable=ptable,
            puppet_ca_proxy=proxy,
            puppet_proxy=proxy,
            subnet=subnet,
        ).create()
        self.assertEqual(hostgroup.environment.read().name, env.name)
        self.assertEqual(hostgroup.parent.read().name, parent_hostgroup.name)
        self.assertEqual(hostgroup.architecture.read().name, arch.name)
        self.assertEqual(hostgroup.operatingsystem.read().name, os.name)
        self.assertEqual(hostgroup.medium.read().name, media.name)
        self.assertEqual(hostgroup.ptable.read().name, ptable.name)
        self.assertEqual(hostgroup.puppet_ca_proxy.read().name, proxy.name)
        self.assertEqual(hostgroup.subnet.read().name, subnet.name)
        self.assertEqual(hostgroup.domain.read().name, domain.name)
        self.assertEqual(hostgroup.puppet_proxy.read().name, proxy.name)
        self.assertEqual(hostgroup.content_source.read().name, proxy.name)
        self.assertEqual(hostgroup.content_view.read().name, content_view.name)
        self.assertEqual(hostgroup.lifecycle_environment.read().name, lce.name)

        # create new properties for update
        new_org = entities.Organization().create()
        new_loc = entities.Location(organization=[new_org]).create()
        new_arch = entities.Architecture().create()
        new_ptable = entities.PartitionTable().create()
        new_parent = entities.HostGroup(
            location=[new_loc],
            organization=[new_org],
        ).create()
        new_env = entities.Environment(
            location=[new_loc],
            organization=[new_org],
        ).create()
        new_os = entities.OperatingSystem(
            architecture=[new_arch],
            ptable=[new_ptable],
        ).create()
        new_subnet = entities.Subnet(
            location=[new_loc],
            organization=[new_org],
        ).create()
        new_domain = entities.Domain(
            location=[new_loc],
            organization=[new_org],
        ).create()
        new_cv = entities.ContentView(organization=new_org).create()
        new_cv.publish()
        new_cv = new_cv.read()
        new_lce = entities.LifecycleEnvironment(organization=new_org).create()
        promote(new_cv.version[0], new_lce.id)
        new_media = entities.Media(
            operatingsystem=[os],
            location=[new_loc],
            organization=[new_org],
        ).create()
        # update itself
        hostgroup.organization = [new_org]
        hostgroup.location = [new_loc]
        hostgroup.lifecycle_environment = new_lce
        hostgroup.content_view = new_cv
        hostgroup.domain = new_domain
        hostgroup.architecture = new_arch
        hostgroup.operatingsystem = new_os
        hostgroup.environment = new_env
        hostgroup.parent = new_parent
        hostgroup.ptable = new_ptable
        hostgroup.subnet = new_subnet
        hostgroup.medium = new_media
        hostgroup = hostgroup.update([
            'parent',
            'environment',
            'operatingsystem',
            'architecture',
            'ptable',
            'subnet',
            'domain',
            'content_view',
            'lifecycle_environment',
            'location',
            'organization',
            'medium'
            ])
        self.assertEqual(hostgroup.parent.read().name, new_parent.name)
        self.assertEqual(hostgroup.environment.read().name, new_env.name)
        self.assertEqual(hostgroup.operatingsystem.read().name, new_os.name)
        self.assertEqual(hostgroup.architecture.read().name, new_arch.name)
        self.assertEqual(hostgroup.ptable.read().name, new_ptable.name)
        self.assertEqual(hostgroup.subnet.read().name, new_subnet.name)
        self.assertEqual(hostgroup.domain.read().name, new_domain.name)
        self.assertEqual(hostgroup.content_view.read().name, new_cv.name)
        self.assertEqual(hostgroup.lifecycle_environment.read().name, new_lce.name)
        self.assertEqual(hostgroup.location[0].read().name, new_loc.name)
        self.assertEqual(hostgroup.organization[0].read().name, new_org.name)
        self.assertEqual(hostgroup.medium.read().name, new_media.name)

        # delete
        hostgroup.delete()
        with self.assertRaises(HTTPError):
            hostgroup.read()

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

    @tier2
    def test_positive_create_with_group_parameters(self):
        """Create a hostgroup with 'group parameters' specified

        :id: 0959e2a2-d635-482b-9b2e-d33990d6f0dc

        :expectedresults: A hostgroup is created with assigned group parameters

        :CaseLevel: Integration

        :BZ: 1710853
        """
        group_params = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
        hostgroup = entities.HostGroup(
            organization=[self.org],
            group_parameters_attributes=[group_params]
        ).create()
        self.assertEqual(group_params['name'],
                         hostgroup.group_parameters_attributes[0]['name'])
        self.assertEqual(group_params['value'],
                         hostgroup.group_parameters_attributes[0]['value'])


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
