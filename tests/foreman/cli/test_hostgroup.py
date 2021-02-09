"""Test class for :class:`robottelo.cli.hostgroup.HostGroup` CLI.

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: HostGroup

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_integer
from nailgun import entities

from robottelo.cleanup import capsule_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.environment import Environment
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_architecture
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_domain
from robottelo.cli.factory import make_environment
from robottelo.cli.factory import make_hostgroup
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_location
from robottelo.cli.factory import make_medium
from robottelo.cli.factory import make_os
from robottelo.cli.factory import make_partition_table
from robottelo.cli.factory import make_proxy
from robottelo.cli.factory import make_subnet
from robottelo.cli.factory import publish_puppet_module
from robottelo.cli.hostgroup import HostGroup
from robottelo.cli.proxy import Proxy
from robottelo.cli.puppet import Puppet
from robottelo.config import settings
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.datafactory import invalid_id_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_hostgroups_list


pytestmark = [
    pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
]
PUPPET_MODULES = [
    {'author': 'robottelo', 'name': 'generic_1'},
    {'author': 'robottelo', 'name': 'generic_2'},
]


@pytest.fixture(scope='module')
def cv(module_org):
    """Create puppet repo and content view, and return the content view."""
    return publish_puppet_module(PUPPET_MODULES, CUSTOM_PUPPET_REPO, module_org.id)


@pytest.fixture(scope='module')
def env(cv):
    """Return the puppet environment."""
    return Environment.list({'search': f"content_view=\"{cv['name']}\""})[0]


@pytest.fixture(scope='module')
def puppet_classes(env):
    """Return puppet classes."""
    return [
        Puppet.info({'name': mod['name'], 'puppet-environment': env['name']})
        for mod in PUPPET_MODULES
    ]


@pytest.fixture(scope='module')
def content_source():
    """Return the proxy."""
    return Proxy.list({'search': f'url = https://{settings.server.hostname}:9090'})[0]


@pytest.fixture(scope='module')
def hostgroup(content_source, module_org):
    """Create a host group."""
    return make_hostgroup(
        {'content-source-id': content_source['id'], 'organization-ids': module_org.id}
    )


@pytest.mark.tier2
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_name(name):
    """Don't create an HostGroup with invalid data.

    :id: 853a6d43-129a-497b-94f0-08dc622862f8

    :parametrized: yes

    :expectedresults: HostGroup is not created.
    """
    with pytest.raises(CLIReturnCodeError):
        HostGroup.create({'name': name})


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_create_with_multiple_entities_and_delete(
    module_org, content_source, puppet_classes
):
    """Check if hostgroup with multiple options can be created and deleted

    :id: a3ef4f0e-971d-4307-8d0a-35103dff6586

    :expectedresults: Hostgroup should be created, has all defined
        entities assigned and deleted

    :BZ: 1395254, 1313056

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    # Common entities
    name = valid_hostgroups_list()[0]
    loc = make_location()
    org_2 = entities.Organization().create()
    orgs = [module_org, org_2]
    env = make_environment({'location-ids': loc['id'], 'organization-ids': org_2.id})
    lce = make_lifecycle_environment({'organization-id': org_2.id})
    # Content View should be promoted to be used with LC Env
    cv = make_content_view({'organization-id': org_2.id})
    ContentView.publish({'id': cv['id']})
    cv = ContentView.info({'id': cv['id']})
    ContentView.version_promote(
        {'id': cv['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
    )
    # Network
    domain = make_domain({'location-ids': loc['id'], 'organization-ids': org_2.id})
    subnet = make_subnet({'domain-ids': domain['id'], 'organization-ids': org_2.id})
    # Operating System
    arch = make_architecture()
    ptable = make_partition_table({'location-ids': loc['id'], 'organization-ids': org_2.id})
    os = make_os({'architecture-ids': arch['id'], 'partition-table-ids': ptable['id']})
    os_full_name = f"{os['name']} {os['major-version']}.{os['minor-version']}"
    media = make_medium(
        {
            'operatingsystem-ids': os['id'],
            'location-ids': loc['id'],
            'organization-ids': org_2.id,
        }
    )
    # Note: in the current hammer version there is no content source name
    # option
    make_hostgroup_params = {
        'name': name,
        'organization-ids': [org.id for org in orgs],
        'locations': loc['name'],
        'environment': env['name'],
        'lifecycle-environment': lce['name'],
        'puppet-proxy': content_source['name'],
        'puppet-ca-proxy': content_source['name'],
        'content-source-id': content_source['id'],
        'content-view': cv['name'],
        'domain': domain['name'],
        'subnet': subnet['name'],
        'architecture': arch['name'],
        'partition-table': ptable['name'],
        'medium': media['name'],
        'operatingsystem': os_full_name,
        'puppet-classes': puppet_classes[0]['name'],
        'query-organization': org_2.name,
    }
    hostgroup = make_hostgroup(make_hostgroup_params)
    assert hostgroup['name'] == name
    assert {org.name for org in orgs} == set(hostgroup['organizations'])
    assert loc['name'] in hostgroup['locations']
    assert env['name'] == hostgroup['puppet-environment']
    assert content_source['name'] == hostgroup['puppet-master-proxy']
    assert content_source['name'] == hostgroup['puppet-ca-proxy']
    assert domain['name'] == hostgroup['network']['domain']
    assert subnet['name'] == hostgroup['network']['subnet-ipv4']
    assert arch['name'] == hostgroup['operating-system']['architecture']
    assert ptable['name'] == hostgroup['operating-system']['partition-table']
    assert media['name'] == hostgroup['operating-system']['medium']
    assert os_full_name == hostgroup['operating-system']['operating-system']
    assert cv['name'] == hostgroup['content-view']['name']
    assert lce['name'] == hostgroup['lifecycle-environment']['name']
    assert content_source['name'] == hostgroup['content-source']['name']
    assert puppet_classes[0]['name'] in hostgroup['puppetclasses']
    # delete hostgroup
    HostGroup.delete({'id': hostgroup['id']})
    with pytest.raises(CLIReturnCodeError):
        HostGroup.info({'id': hostgroup['id']})


@pytest.mark.tier2
def test_negative_create_with_content_source(module_org):
    """Attempt to create a hostgroup with invalid content source specified

    :id: 9fc1b777-36a3-4940-a9c8-aed7ff725371

    :BZ: 1260697

    :expectedresults: Hostgroup was not created

    :CaseLevel: Integration
    """
    with pytest.raises(CLIFactoryError):
        make_hostgroup(
            {
                'content-source-id': gen_integer(10000, 99999),
                'organization-ids': module_org.id,
            }
        )


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_positive_update_hostgroup(request, module_org, env, cv, content_source, puppet_classes):
    """Update hostgroup's content source, name and puppet classes

    :id: c22218a1-4d86-4ac1-ad4b-79b10c9adcde

    :customerscenario: true

    :BZ: 1260697, 1313056

    :expectedresults: Hostgroup was successfully updated with new content
        source, name and puppet classes

    :CaseLevel: Integration
    """
    hostgroup = make_hostgroup(
        {
            'content-source-id': content_source['id'],
            'organization-ids': module_org.id,
            'environment-id': env['id'],
            'content-view-id': cv['id'],
            'query-organization-id': module_org.id,
        }
    )
    new_content_source = make_proxy()

    @request.addfinalizer
    def _cleanup():
        HostGroup.delete({'id': hostgroup['id']})
        capsule_cleanup(new_content_source['id'])

    assert len(hostgroup['puppetclasses']) == 0
    new_name = valid_hostgroups_list()[0]
    puppet_class_names = [puppet['name'] for puppet in puppet_classes]
    HostGroup.update(
        {
            'new-name': new_name,
            'id': hostgroup['id'],
            'content-source-id': new_content_source['id'],
            'puppet-classes': puppet_class_names,
        }
    )
    hostgroup = HostGroup.info({'id': hostgroup['id']})
    assert hostgroup['name'] == new_name
    assert hostgroup['content-source']['name'] == new_content_source['name']
    assert set(puppet_class_names) == set(hostgroup['puppetclasses'])


@pytest.mark.tier2
def test_negative_update_content_source(hostgroup, content_source):
    """Attempt to update hostgroup's content source with invalid value

    :id: 4ffe6d18-3899-4bf1-acb2-d55ea09b7a26

    :BZ: 1260697, 1313056

    :expectedresults: Host group was not updated. Content source remains
        the same as it was before update

    :CaseLevel: Integration
    """
    with pytest.raises(CLIReturnCodeError):
        HostGroup.update({'id': hostgroup['id'], 'content-source-id': gen_integer(10000, 99999)})
    hostgroup = HostGroup.info({'id': hostgroup['id']})
    assert hostgroup['content-source']['name'] == content_source['name']


@pytest.mark.tier2
def test_negative_update_name(hostgroup):
    """Create HostGroup then fail to update its name

    :id: 42d208a4-f518-4ff2-9b7a-311adb460abd

    :expectedresults: HostGroup name is not updated
    """
    new_name = invalid_values_list()[0]
    with pytest.raises(CLIReturnCodeError):
        HostGroup.update({'id': hostgroup['id'], 'new-name': new_name})
    result = HostGroup.info({'id': hostgroup['id']})
    assert hostgroup['name'] == result['name']


@pytest.mark.tier2
def test_negative_delete_by_id():
    """Create HostGroup then delete it by wrong ID

    :id: 047c9f1a-4dd6-4fdc-b7ed-37cc725c68d3

    :expectedresults: HostGroup is not deleted

    :CaseLevel: Integration
    """
    entity_id = invalid_id_list()[0]
    with pytest.raises(CLIReturnCodeError):
        HostGroup.delete({'id': entity_id})
