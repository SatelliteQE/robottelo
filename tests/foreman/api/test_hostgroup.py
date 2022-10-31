"""Tests for the ``hostgroups`` paths.

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: HostGroup

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint

import pytest
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities
from nailgun import entity_fields
from requests.exceptions import HTTPError

from robottelo.api.utils import one_to_one_names
from robottelo.config import get_credentials
from robottelo.utils.datafactory import invalid_values_list
from robottelo.utils.datafactory import parametrized
from robottelo.utils.datafactory import valid_hostgroups_list


@pytest.fixture
def hostgroup(module_org, module_location):
    return entities.HostGroup(location=[module_location], organization=[module_org]).create()


@pytest.fixture
def puppet_hostgroup(module_puppet_org, module_puppet_loc, session_puppet_enabled_sat):
    return session_puppet_enabled_sat.api.HostGroup(
        location=[module_puppet_loc], organization=[module_puppet_org]
    ).create()


class TestHostGroup:
    """Tests for host group entity."""

    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_inherit_puppetclass(self, session_puppet_enabled_sat):
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
        org = session_puppet_enabled_sat.api.Organization(name=gen_string('alpha')).create()
        location = session_puppet_enabled_sat.api.Location(organization=[org]).create()

        # Working with 'api_test_classparameters' module as we know for sure that it contains
        # at least few puppet classes, the name of the repo is the same as the name of puppet_class
        repo = puppet_class = 'api_test_classparameters'
        env_name = session_puppet_enabled_sat.create_custom_environment(repo=repo)
        content_view = session_puppet_enabled_sat.api.ContentView(
            name=gen_string('alpha'), organization=org
        ).create()
        content_view.publish()
        content_view = content_view.read()
        lc_env = session_puppet_enabled_sat.api.LifecycleEnvironment(
            name=gen_string('alpha'), organization=org
        ).create()
        content_view.version[0].promote(data={'environment_ids': lc_env.id, 'force': False})
        content_view = content_view.read()
        assert len(content_view.version) == 1

        # Get environments that contains chosen puppet module
        environment = session_puppet_enabled_sat.api.Environment().search(
            query={'search': f'name={env_name}'}
        )
        assert len(environment) == 1
        environment = environment[0]
        environment.location = [location]
        environment.organization = [org]
        environment.update()

        # Create a host group and it dependencies.
        mac = entity_fields.MACAddressField().gen_value()
        root_pass = entity_fields.StringField(length=(8, 30)).gen_value()
        domain = session_puppet_enabled_sat.api.Domain().create()
        architecture = session_puppet_enabled_sat.api.Architecture().create()
        ptable = session_puppet_enabled_sat.api.PartitionTable().create()
        operatingsystem = session_puppet_enabled_sat.api.OperatingSystem(
            architecture=[architecture], ptable=[ptable]
        ).create()
        medium = session_puppet_enabled_sat.api.Media(operatingsystem=[operatingsystem]).create()
        hostgroup = session_puppet_enabled_sat.api.HostGroup(
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
        assert len(hostgroup.read_json()['all_puppetclasses']) == 0

        # Get puppet class id for ntp module
        response = client.get(
            environment.path('self') + '/puppetclasses',
            auth=get_credentials(),
            verify=False,
        )
        response.raise_for_status()
        results = response.json()['results']
        puppet_class_id = results[puppet_class][0]['id']

        # Assign puppet class
        client.post(
            hostgroup.path('self') + '/puppetclass_ids',
            data={'puppetclass_id': puppet_class_id},
            auth=get_credentials(),
            verify=False,
        ).raise_for_status()
        hostgroup_attrs = hostgroup.read_json()
        assert len(hostgroup_attrs['all_puppetclasses']) == 1
        assert hostgroup_attrs['all_puppetclasses'][0]['name'] == puppet_class

        # Create Host entity using HostGroup
        host = session_puppet_enabled_sat.api.Host(
            hostgroup=hostgroup,
            mac=mac,
            root_pass=root_pass,
            environment=environment,
            location=location,
            organization=org,
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lc_env.id,
            },
            name=gen_string('alpha'),
        ).create(False)
        host_attrs = host.read_json()
        assert len(host_attrs['all_puppetclasses']) == 1
        assert host_attrs['all_puppetclasses'][0]['name'] == puppet_class

    @pytest.mark.upgrade
    @pytest.mark.tier3
    def test_rebuild_config(self, module_org, module_location, hostgroup):
        """'Rebuild orchestration config' of an existing host group

        :id: 58bf7015-18fc-4d25-9b64-7f2dd6dde425

        :expectedresults: rebuild hostgroup orchestration configs successfully.

        :CaseImportance: Medium

        :CaseLevel: System
        """
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        content_view = entities.ContentView(organization=module_org).create()
        content_view.publish()
        content_view = content_view.read()
        content_view.version[0].promote(data={'environment_ids': lce.id, 'force': False})
        entities.Host(
            hostgroup=hostgroup,
            location=module_location,
            organization=module_org,
            managed=True,
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': lce.id,
            },
        ).create()
        # TODO: use host that can also rebuild the SSH_Nic, SSH_Host, and Content_Host_Status
        # config
        assert (
            hostgroup.rebuild_config(data={'only': 'DNS,DHCP,TFTP'})['message']
            == 'Configuration successfully rebuilt.'
        )

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_hostgroups_list()))
    def test_positive_create_with_name(self, name, module_org, module_location):
        """Create a hostgroup with different names

        :id: fd5d353c-fd0c-4752-8a83-8f399b4c3416

        :parametrized: yes

        :expectedresults: A hostgroup is created with expected name

        :CaseImportance: Critical
        """
        hostgroup = entities.HostGroup(
            location=[module_location], name=name, organization=[module_org]
        ).create()
        assert name == hostgroup.name

    @pytest.mark.tier1
    def test_positive_clone(self, hostgroup):
        """Create a hostgroup by cloning an existing one

        :id: 44ac8b3b-9cb0-4a9e-ad9b-2c67b2411922

        :expectedresults: A hostgroup is cloned with same parameters

        :CaseImportance: Critical
        """
        hostgroup_cloned_name = gen_string('alpha')
        hostgroup_cloned = entities.HostGroup(id=hostgroup.id).clone(
            data={'name': hostgroup_cloned_name}
        )
        hostgroup_origin = hostgroup.read_json()

        # remove unset and unique values before comparison
        unique_keys = ('updated_at', 'created_at', 'title', 'id', 'name')
        hostgroup_cloned_reduced = {
            k: v
            for k, v in hostgroup_cloned.items()
            if k in hostgroup_origin and k not in unique_keys
        }

        assert hostgroup_cloned_reduced.items() <= hostgroup_origin.items()

    @pytest.mark.tier1
    def test_positive_create_with_properties(
        self, module_puppet_org, module_puppet_loc, session_puppet_enabled_sat
    ):
        """Create a hostgroup with properties

        :id: 528afd01-356a-4082-9e88-a5b2a715a792

        :expectedresults: A hostgroup is created with expected properties,
            updated and deleted

        :CaseLevel: Integration

        :CaseImportance: High
        """
        env = session_puppet_enabled_sat.api.Environment(
            location=[module_puppet_loc], organization=[module_puppet_org]
        ).create()
        parent_hostgroup = session_puppet_enabled_sat.api.HostGroup(
            location=[module_puppet_loc], organization=[module_puppet_org]
        ).create()
        arch = session_puppet_enabled_sat.api.Architecture().create()
        ptable = session_puppet_enabled_sat.api.PartitionTable().create()
        os = session_puppet_enabled_sat.api.OperatingSystem(
            architecture=[arch], ptable=[ptable]
        ).create()
        media = session_puppet_enabled_sat.api.Media(
            operatingsystem=[os], location=[module_puppet_loc], organization=[module_puppet_org]
        ).create()
        proxy = session_puppet_enabled_sat.api.SmartProxy().search(
            query={'search': f'url = {session_puppet_enabled_sat.url}:9090'}
        )[0]
        subnet = session_puppet_enabled_sat.api.Subnet(
            location=[module_puppet_loc], organization=[module_puppet_org]
        ).create()
        domain = session_puppet_enabled_sat.api.Domain(
            location=[module_puppet_loc], organization=[module_puppet_org]
        ).create()
        content_view = session_puppet_enabled_sat.api.ContentView(
            organization=module_puppet_org
        ).create()
        content_view.publish()
        content_view = content_view.read()
        lce = session_puppet_enabled_sat.api.LifecycleEnvironment(
            organization=module_puppet_org
        ).create()
        content_view.version[0].promote(data={'environment_ids': lce.id, 'force': False})
        hostgroup = session_puppet_enabled_sat.api.HostGroup(
            architecture=arch,
            content_source=proxy,
            content_view=content_view,
            domain=domain,
            environment=env,
            lifecycle_environment=lce,
            location=[module_puppet_loc],
            medium=media,
            operatingsystem=os,
            organization=[module_puppet_org],
            parent=parent_hostgroup,
            ptable=ptable,
            puppet_ca_proxy=proxy,
            puppet_proxy=proxy,
            subnet=subnet,
        ).create()
        assert hostgroup.environment.read().name == env.name
        assert hostgroup.parent.read().name == parent_hostgroup.name
        assert hostgroup.architecture.read().name == arch.name
        assert hostgroup.operatingsystem.read().name == os.name
        assert hostgroup.medium.read().name == media.name
        assert hostgroup.ptable.read().name == ptable.name
        assert hostgroup.puppet_ca_proxy.read().name == proxy.name
        assert hostgroup.subnet.read().name == subnet.name
        assert hostgroup.domain.read().name == domain.name
        assert hostgroup.puppet_proxy.read().name == proxy.name
        assert hostgroup.content_source.read().name == proxy.name
        assert hostgroup.content_view.read().name == content_view.name
        assert hostgroup.lifecycle_environment.read().name == lce.name

        # create new properties for update
        new_org = session_puppet_enabled_sat.api.Organization().create()
        new_loc = session_puppet_enabled_sat.api.Location(organization=[new_org]).create()
        new_arch = session_puppet_enabled_sat.api.Architecture().create()
        new_ptable = session_puppet_enabled_sat.api.PartitionTable().create()
        new_parent = session_puppet_enabled_sat.api.HostGroup(
            location=[new_loc], organization=[new_org]
        ).create()
        new_env = session_puppet_enabled_sat.api.Environment(
            location=[new_loc], organization=[new_org]
        ).create()
        new_os = session_puppet_enabled_sat.api.OperatingSystem(
            architecture=[new_arch], ptable=[new_ptable]
        ).create()
        new_subnet = session_puppet_enabled_sat.api.Subnet(
            location=[new_loc], organization=[new_org]
        ).create()
        new_domain = session_puppet_enabled_sat.api.Domain(
            location=[new_loc], organization=[new_org]
        ).create()
        new_cv = session_puppet_enabled_sat.api.ContentView(organization=new_org).create()
        new_cv.publish()
        new_cv = new_cv.read()
        new_lce = session_puppet_enabled_sat.api.LifecycleEnvironment(organization=new_org).create()
        new_media = session_puppet_enabled_sat.api.Media(
            operatingsystem=[os], location=[new_loc], organization=[new_org]
        ).create()
        new_cv.version[0].promote(data={'environment_ids': new_lce.id, 'force': False})

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
        hostgroup = hostgroup.update(
            [
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
                'medium',
            ]
        )
        assert hostgroup.parent.read().name == new_parent.name
        assert hostgroup.environment.read().name == new_env.name
        assert hostgroup.operatingsystem.read().name == new_os.name
        assert hostgroup.architecture.read().name == new_arch.name
        assert hostgroup.ptable.read().name == new_ptable.name
        assert hostgroup.subnet.read().name == new_subnet.name
        assert hostgroup.domain.read().name == new_domain.name
        assert hostgroup.content_view.read().name == new_cv.name
        assert hostgroup.lifecycle_environment.read().name == new_lce.name
        assert new_loc.name in [location.read().name for location in hostgroup.location]
        assert new_org.name in [org.read().name for org in hostgroup.organization]
        assert hostgroup.medium.read().name == new_media.name

        # delete
        hostgroup.delete()
        with pytest.raises(HTTPError):
            hostgroup.read()

    @pytest.mark.stubbed('Remove stub once proper infrastructure will be created')
    @pytest.mark.tier2
    def test_positive_create_with_realm(self, module_org, module_location, target_sat):
        """Create a hostgroup with realm specified

        :id: 4f07ff8d-746f-4ab5-ae0b-03d629f6296c

        :CaseImportance: Medium

        :expectedresults: A hostgroup is created with expected realm assigned

        :CaseLevel: Integration
        """
        realm = entities.Realm(
            location=[module_location],
            organization=[module_org],
            realm_proxy=entities.SmartProxy().search(
                query={'search': f'url = {target_sat.url}:9090'}
            )[0],
        ).create()
        hostgroup = entities.HostGroup(
            location=[module_location], organization=[module_org], realm=realm
        ).create()
        assert hostgroup.realm.read().name == realm.name

    @pytest.mark.tier2
    def test_positive_create_with_locs(self, module_org):
        """Create a hostgroup with multiple locations specified

        :id: 0c2ee2ff-9e7a-4931-8cea-f4eecbd8c4c0

        :CaseImportance: Medium

        :expectedresults: A hostgroup is created with expected multiple
            locations assigned

        :CaseLevel: Integration
        """
        locs = [entities.Location(organization=[module_org]).create() for _ in range(randint(3, 5))]
        hostgroup = entities.HostGroup(location=locs, organization=[module_org]).create()
        assert {loc.name for loc in locs} == {loc.read().name for loc in hostgroup.location}

    @pytest.mark.tier2
    def test_positive_create_with_orgs(self):
        """Create a hostgroup with multiple organizations specified

        :id: 09642238-cf0d-469a-a0b5-c167b1b8edf5

        :CaseImportance: Medium

        :expectedresults: A hostgroup is created with expected multiple
            organizations assigned

        :CaseLevel: Integration
        """
        orgs = [entities.Organization().create() for _ in range(randint(3, 5))]
        hostgroup = entities.HostGroup(organization=orgs).create()
        assert {org.name for org in orgs}, {org.read().name for org in hostgroup.organization}

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_hostgroups_list()))
    def test_positive_update_name(self, name, hostgroup):
        """Update a hostgroup with a new name

        :id: 8abb151f-a058-4f47-a1c1-f60a32cd7572

        :parametrized: yes

        :expectedresults: A hostgroup is updated with expected name

        :CaseImportance: Critical
        """
        hostgroup.name = name
        hostgroup = hostgroup.update(['name'])
        assert name == hostgroup.name

    @pytest.mark.tier2
    def test_positive_update_puppet_ca_proxy(self, puppet_hostgroup, session_puppet_enabled_sat):
        """Update a hostgroup with a new puppet CA proxy

        :id: fd13ab0e-1a5b-48a0-a852-3fff8306271f

        :expectedresults: A hostgroup is updated with expected puppet CA proxy

        :CaseImportance: Medium

        :CaseLevel: Integration
        """
        new_proxy = session_puppet_enabled_sat.api.SmartProxy().search(
            query={'search': f'url = {session_puppet_enabled_sat.url}:9090'}
        )[0]
        puppet_hostgroup.puppet_ca_proxy = new_proxy
        puppet_hostgroup = puppet_hostgroup.update(['puppet_ca_proxy'])
        assert puppet_hostgroup.puppet_ca_proxy.read().name == new_proxy.name

    @pytest.mark.stubbed('Remove stub once proper infrastructure will be created')
    @pytest.mark.tier2
    def test_positive_update_realm(self, module_org, module_location, target_sat):
        """Update a hostgroup with a new realm

        :id: fd9d141f-7a71-4439-92c7-1dbc1eea4772

        :CaseImportance: Medium

        :expectedresults: A hostgroup is updated with expected realm

        :CaseLevel: Integration
        """
        realm = entities.Realm(
            location=[module_location],
            organization=[module_org],
            realm_proxy=entities.SmartProxy().search(
                query={'search': f'url = {target_sat.url}:9090'}
            )[0],
        ).create()
        hostgroup = entities.HostGroup(
            location=[module_location], organization=[module_org], realm=realm
        ).create()
        new_realm = entities.Realm(
            location=[module_location],
            organization=[module_org],
            realm_proxy=entities.SmartProxy().search(
                query={'search': f'url = {target_sat.url}:9090'}
            )[0],
        ).create()
        hostgroup.realm = new_realm
        hostgroup = hostgroup.update(['realm'])
        assert hostgroup.realm.read().name == new_realm.name

    @pytest.mark.tier2
    def test_positive_update_puppet_proxy(self, puppet_hostgroup, session_puppet_enabled_sat):
        """Update a hostgroup with a new puppet proxy

        :id: 86eca603-2cdd-4563-b6f6-aaa5cea1a723

        :CaseImportance: Medium

        :expectedresults: A hostgroup is updated with expected puppet proxy

        :CaseLevel: Integration
        """
        new_proxy = session_puppet_enabled_sat.api.SmartProxy().search(
            query={'search': f'url = {session_puppet_enabled_sat.url}:9090'}
        )[0]
        puppet_hostgroup.puppet_proxy = new_proxy
        puppet_hostgroup = puppet_hostgroup.update(['puppet_proxy'])
        assert puppet_hostgroup.puppet_proxy.read().name == new_proxy.name

    @pytest.mark.tier2
    def test_positive_update_content_source(self, hostgroup, target_sat):
        """Update a hostgroup with a new puppet proxy

        :id: 02ef1340-a21e-41b7-8aa7-d6fdea196c16

        :CaseImportance: Medium

        :expectedresults: A hostgroup is updated with expected puppet proxy

        :CaseLevel: Integration
        """
        new_content_source = entities.SmartProxy().search(
            query={'search': f'url = {target_sat.url}:9090'}
        )[0]
        hostgroup.content_source = new_content_source
        hostgroup = hostgroup.update(['content_source'])
        assert hostgroup.content_source.read().name == new_content_source.name

    @pytest.mark.tier2
    def test_positive_update_locs(self, module_org, hostgroup):
        """Update a hostgroup with new multiple locations

        :id: b045f7e8-d7c0-428b-a29c-8d54e53742e2

        :CaseImportance: Medium

        :expectedresults: A hostgroup is updated with expected locations

        :CaseLevel: Integration
        """
        new_locs = [
            entities.Location(organization=[module_org]).create() for _ in range(randint(3, 5))
        ]
        hostgroup.location = new_locs
        hostgroup = hostgroup.update(['location'])
        assert {loc.name for loc in new_locs}, {loc.read().name for loc in hostgroup.location}

    @pytest.mark.tier2
    def test_positive_update_orgs(self, hostgroup):
        """Update a hostgroup with new multiple organizations

        :id: 5f6bd4f9-4bd6-4d7e-9a91-de824299020e

        :CaseImportance: Medium

        :expectedresults: A hostgroup is updated with expected organizations

        :CaseLevel: Integration
        """
        new_orgs = [entities.Organization().create() for _ in range(randint(3, 5))]
        hostgroup.organization = new_orgs
        hostgroup = hostgroup.update(['organization'])
        assert {org.name for org in new_orgs} == {org.read().name for org in hostgroup.organization}

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_name(self, name, module_org, module_location):
        """Attempt to create a hostgroup with invalid names

        :id: 3f5aa17a-8db9-4fe9-b309-b8ec5e739da1

        :parametrized: yes

        :expectedresults: A hostgroup is not created

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            entities.HostGroup(
                location=[module_location], name=name, organization=[module_org]
            ).create()

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
    def test_negative_update_name(self, new_name, hostgroup):
        """Attempt to update a hostgroup with invalid names

        :id: 6d8c4738-a0c4-472b-9a71-27c8a3832335

        :parametrized: yes

        :expectedresults: A hostgroup is not updated

        :CaseImportance: Critical
        """
        original_name = hostgroup.name
        hostgroup.name = new_name
        with pytest.raises(HTTPError):
            hostgroup.update(['name'])
        assert hostgroup.read().name == original_name

    @pytest.mark.tier2
    def test_positive_create_with_group_parameters(self, module_org):
        """Create a hostgroup with 'group parameters' specified

        :id: 0959e2a2-d635-482b-9b2e-d33990d6f0dc

        :CaseImportance: Medium

        :expectedresults: A hostgroup is created with assigned group parameters

        :customerscenario: true

        :CaseLevel: Integration

        :BZ: 1710853
        """
        group_params = {'name': gen_string('alpha'), 'value': gen_string('alpha')}
        hostgroup = entities.HostGroup(
            organization=[module_org], group_parameters_attributes=[group_params]
        ).create()
        assert group_params['name'] == hostgroup.group_parameters_attributes[0]['name']
        assert group_params['value'] == hostgroup.group_parameters_attributes[0]['value']


class TestHostGroupMissingAttr:
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. The ``one_to_*_names`` functions know what names
    Satellite may assign to fields.
    """

    @pytest.mark.tier2
    def test_positive_get_content_source(self, hostgroup):
        """Read a host group. Inspect the server's response.

        :id: 9d42f47a-2f08-45ad-97d0-de94f0f1de2f

        :CaseImportance: Medium

        :expectedresults: The response contains both values for the
            ``content_source`` field.

        :CaseLevel: Integration
        """
        names = one_to_one_names('content_source')
        hostgroup_attrs = set(hostgroup.read_json().keys())
        assert names.issubset(
            hostgroup_attrs
        ), f'{names.difference(hostgroup_attrs)} not found in {hostgroup_attrs}'

    @pytest.mark.tier2
    def test_positive_get_cv(self, hostgroup):
        """Read a host group. Inspect the server's response.

        :id: 7d36f33e-f161-4d2a-9ee4-8eb949ed4cbf

        :CaseImportance: Medium

        :expectedresults: The response contains both values for the
            ``content_view`` field.

        :CaseLevel: Integration
        """
        names = one_to_one_names('content_view')
        hostgroup_attrs = set(hostgroup.read_json().keys())
        assert names.issubset(
            hostgroup_attrs
        ), f'{names.difference(hostgroup_attrs)} not found in {hostgroup_attrs}'

    @pytest.mark.tier2
    def test_positive_get_lce(self, hostgroup):
        """Read a host group. Inspect the server's response.

        :id: efa17f59-47f9-40c6-821d-c348c4d852ff

        :CaseImportance: Medium

        :expectedresults: The response contains both values for the
            ``lifecycle_environment`` field.

        :CaseLevel: Integration
        """
        names = one_to_one_names('lifecycle_environment')
        hostgroup_attrs = set(hostgroup.read_json().keys())
        assert names.issubset(
            hostgroup_attrs
        ), f'{names.difference(hostgroup_attrs)} not found in {hostgroup_attrs}'

    @pytest.mark.tier2
    def test_positive_read_puppet_proxy_name(self, session_puppet_enabled_sat):
        """Read a hostgroup created with puppet proxy and inspect server's
        response

        :id: f93d0866-0073-4577-8777-6d645b63264f

        :CaseImportance: Medium

        :expectedresults: Field 'puppet_proxy_name' is returned

        :BZ: 1371900

        :CaseLevel: Integration
        """
        proxy = session_puppet_enabled_sat.api.SmartProxy().search(
            query={'search': f'url = {session_puppet_enabled_sat.url}:9090'}
        )[0]
        hg = session_puppet_enabled_sat.api.HostGroup(puppet_proxy=proxy).create().read_json()
        assert 'puppet_proxy_name' in hg
        assert proxy.name == hg['puppet_proxy_name']

    @pytest.mark.tier2
    def test_positive_read_puppet_ca_proxy_name(self, session_puppet_enabled_sat):
        """Read a hostgroup created with puppet ca proxy and inspect server's
        response

        :id: ab151e09-8e64-4377-95e8-584629750659

        :CaseImportance: Medium

        :expectedresults: Field 'puppet_ca_proxy_name' is returned

        :BZ: 1371900

        :CaseLevel: Integration
        """
        proxy = session_puppet_enabled_sat.api.SmartProxy().search(
            query={'search': f'url = {session_puppet_enabled_sat.url}:9090'}
        )[0]
        hg = session_puppet_enabled_sat.api.HostGroup(puppet_ca_proxy=proxy).create().read_json()
        assert 'puppet_ca_proxy_name' in hg
        assert proxy.name == hg['puppet_ca_proxy_name']
