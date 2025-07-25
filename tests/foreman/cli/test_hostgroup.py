"""Test class for :class:`robottelo.cli.hostgroup.HostGroup` CLI.

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseComponent: HostGroup

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

from fauxfactory import gen_integer
import pytest

from robottelo.config import settings
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.utils.datafactory import (
    invalid_id_list,
    invalid_values_list,
    parametrized,
    valid_hostgroups_list,
)

pytestmark = [
    pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
]

pc_name = 'generic_1'


@pytest.fixture(scope='module')
def env(module_puppet_org, module_puppet_loc, session_puppet_enabled_sat):
    """Return the puppet environment."""

    env_name = session_puppet_enabled_sat.create_custom_environment(repo=pc_name)
    env = (
        session_puppet_enabled_sat.api.Environment()
        .search(query={'search': f'name={env_name}'})[0]
        .read()
    )
    env.location = [module_puppet_loc]
    env.organization = [module_puppet_org]
    env.update(['location', 'organization'])
    return env


@pytest.fixture(scope='module')
def puppet_classes(env, session_puppet_enabled_sat):
    """Return puppet classes."""
    return [
        session_puppet_enabled_sat.cli.Puppet.info(
            {'name': pc_name, 'puppet-environment': env.name}
        )
    ]


@pytest.fixture(scope='module')
def puppet_content_source(session_puppet_enabled_sat):
    """Return the proxy."""
    return session_puppet_enabled_sat.cli.Proxy.list(
        {'search': f'url = {session_puppet_enabled_sat.url}:9090'}
    )[0]


@pytest.fixture(scope='module')
def content_source(module_target_sat):
    """Return the proxy."""
    return module_target_sat.cli.Proxy.list({'search': f'url = {module_target_sat.url}:9090'})[0]


@pytest.fixture(scope='module')
def hostgroup(content_source, module_org, module_target_sat):
    """Create a host group."""
    return module_target_sat.cli_factory.hostgroup(
        {'content-source-id': content_source['id'], 'organization-ids': module_org.id}
    )


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_name(name, module_target_sat):
    """Don't create an HostGroup with invalid data.

    :id: 853a6d43-129a-497b-94f0-08dc622862f8

    :parametrized: yes

    :expectedresults: HostGroup is not created.
    """
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.HostGroup.create({'name': name})


@pytest.mark.e2e
@pytest.mark.upgrade
def test_positive_create_with_multiple_entities_and_delete(
    module_puppet_org, puppet_content_source, puppet_classes, session_puppet_enabled_sat
):
    """Check if hostgroup with multiple options can be created and deleted

    :id: a3ef4f0e-971d-4307-8d0a-35103dff6586

    :expectedresults: Hostgroup should be created, has all defined
        entities assigned and deleted

    :BZ: 1395254, 1313056

    :CaseImportance: Critical
    """
    with session_puppet_enabled_sat:
        # Common entities
        name = valid_hostgroups_list()[0]
        loc = session_puppet_enabled_sat.cli_factory.make_location()
        org_2 = session_puppet_enabled_sat.api.Organization().create()
        orgs = [module_puppet_org, org_2]
        env = session_puppet_enabled_sat.cli_factory.make_environment(
            {'location-ids': loc['id'], 'organization-ids': org_2.id}
        )
        lce = session_puppet_enabled_sat.cli_factory.make_lifecycle_environment(
            {'organization-id': org_2.id}
        )
        # Content View should be promoted to be used with LC Env
        cv = session_puppet_enabled_sat.cli_factory.make_content_view({'organization-id': org_2.id})
        session_puppet_enabled_sat.cli.ContentView.publish({'id': cv['id']})
        cv = session_puppet_enabled_sat.cli.ContentView.info({'id': cv['id']})
        session_puppet_enabled_sat.cli.ContentView.version_promote(
            {'id': cv['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        # Network
        domain = session_puppet_enabled_sat.cli_factory.make_domain(
            {'location-ids': loc['id'], 'organization-ids': org_2.id}
        )
        subnet = session_puppet_enabled_sat.cli_factory.make_subnet(
            {'domain-ids': domain['id'], 'organization-ids': org_2.id}
        )
        # Operating System
        arch = session_puppet_enabled_sat.cli_factory.make_architecture()
        ptable = session_puppet_enabled_sat.cli_factory.make_partition_table(
            {'location-ids': loc['id'], 'organization-ids': org_2.id}
        )
        os = session_puppet_enabled_sat.cli_factory.make_os(
            {'architecture-ids': arch['id'], 'partition-table-ids': ptable['id']}
        )
        os_full_name = "{} {}.{}".format(os['name'], os['major-version'], os['minor-version'])
        media = session_puppet_enabled_sat.cli_factory.make_medium(
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
            'puppet-environment': env['name'],
            'lifecycle-environment-id': lce['id'],
            'puppet-proxy': puppet_content_source['name'],
            'puppet-ca-proxy': puppet_content_source['name'],
            'content-source-id': puppet_content_source['id'],
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
        hostgroup = session_puppet_enabled_sat.cli_factory.hostgroup(make_hostgroup_params)
        assert hostgroup['name'] == name
        assert {org.name for org in orgs} == set(hostgroup['organizations'])
        assert loc['name'] in hostgroup['locations']
        assert env['name'] == hostgroup['puppet-environment']
        assert puppet_content_source['name'] == hostgroup['puppet-master-proxy']
        assert puppet_content_source['name'] == hostgroup['puppet-ca-proxy']
        assert domain['name'] == hostgroup['network']['domain']
        assert subnet['name'] == hostgroup['network']['subnet-ipv4']
        assert arch['name'] == hostgroup['operating-system']['architecture']
        assert ptable['name'] == hostgroup['operating-system']['partition-table']
        assert media['name'] == hostgroup['operating-system']['medium']
        assert os_full_name == hostgroup['operating-system']['operating-system']
        assert cv['name'] == hostgroup['content-view']['name']
        assert lce['name'] == hostgroup['lifecycle-environment']['name']
        assert puppet_content_source['name'] == hostgroup['content-source']['name']
        assert puppet_classes[0]['name'] in hostgroup['puppetclasses']
        # delete hostgroup
        session_puppet_enabled_sat.cli.HostGroup.delete({'id': hostgroup['id']})
        with pytest.raises(CLIReturnCodeError):
            session_puppet_enabled_sat.cli.HostGroup.info({'id': hostgroup['id']})


def test_negative_create_with_content_source(module_org, module_target_sat):
    """Attempt to create a hostgroup with invalid content source specified

    :id: 9fc1b777-36a3-4940-a9c8-aed7ff725371

    :BZ: 1260697

    :expectedresults: Hostgroup was not created
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.hostgroup(
            {
                'content-source-id': gen_integer(10000, 99999),
                'organization-ids': module_org.id,
            }
        )


@pytest.mark.run_in_one_thread
def test_positive_update_hostgroup_with_puppet(
    request,
    module_puppet_org,
    env,
    puppet_content_source,
    puppet_classes,
    session_puppet_enabled_sat,
    puppet_proxy_port_range,
):
    """Update hostgroup's content source, name and puppet classes

    :id: c22218a1-4d86-4ac1-ad4b-79b10c9adcde

    :customerscenario: true

    :BZ: 1260697, 1313056

    :expectedresults: Hostgroup was successfully updated with new content
        source, name and puppet classes
    """
    with session_puppet_enabled_sat as puppet_sat:
        hostgroup = puppet_sat.cli_factory.hostgroup(
            {
                'content-source-id': puppet_content_source['id'],
                'organization-ids': module_puppet_org.id,
                'puppet-environment-id': env.id,
                'query-organization-id': module_puppet_org.id,
            }
        )
        new_content_source = puppet_sat.cli_factory.make_proxy()

        @request.addfinalizer
        def _cleanup():
            with session_puppet_enabled_sat:
                session_puppet_enabled_sat.cli.HostGroup.delete({'id': hostgroup['id']})
                session_puppet_enabled_sat.cli.Proxy.delete({'id': new_content_source['id']})

        assert len(hostgroup['puppetclasses']) == 0
        new_name = valid_hostgroups_list()[0]
        puppet_class_names = [puppet['name'] for puppet in puppet_classes]
        session_puppet_enabled_sat.cli.HostGroup.update(
            {
                'new-name': new_name,
                'id': hostgroup['id'],
                'content-source-id': new_content_source['id'],
                'puppet-classes': puppet_class_names,
            }
        )
        hostgroup = session_puppet_enabled_sat.cli.HostGroup.info({'id': hostgroup['id']})
        assert hostgroup['name'] == new_name
        assert hostgroup['content-source']['name'] == new_content_source['name']
        for puppet_class_name in puppet_class_names:
            assert puppet_class_name in hostgroup['puppetclasses']


@pytest.mark.run_in_one_thread
def test_positive_update_hostgroup(
    module_target_sat,
    module_org,
    content_source,
):
    """Update hostgroup's content source and name

    :id: a354a90f-8bc5-4aee-accb-40c5537640ca

    :customerscenario: true

    :BZ: 1260697, 1313056

    :expectedresults: Hostgroup was successfully updated with new content
        source and name
    """
    hostgroup = module_target_sat.cli_factory.hostgroup(
        {
            'content-source-id': content_source['id'],
            'organization-ids': module_org.id,
            'query-organization-id': module_org.id,
        }
    )
    new_content_source = module_target_sat.cli_factory.make_proxy()

    new_name = valid_hostgroups_list()[0]
    module_target_sat.cli.HostGroup.update(
        {
            'new-name': new_name,
            'id': hostgroup['id'],
            'content-source-id': new_content_source['id'],
        }
    )
    hostgroup = module_target_sat.cli.HostGroup.info({'id': hostgroup['id']})
    assert hostgroup['name'] == new_name
    assert hostgroup['content-source']['name'] == new_content_source['name']


def test_negative_update_content_source(hostgroup, content_source, module_target_sat):
    """Attempt to update hostgroup's content source with invalid value

    :id: 4ffe6d18-3899-4bf1-acb2-d55ea09b7a26

    :BZ: 1260697, 1313056

    :expectedresults: Host group was not updated. Content source remains
        the same as it was before update
    """
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.HostGroup.update(
            {'id': hostgroup['id'], 'content-source-id': gen_integer(10000, 99999)}
        )
    hostgroup = module_target_sat.cli.HostGroup.info({'id': hostgroup['id']})
    assert hostgroup['content-source']['name'] == content_source['name']


def test_negative_update_name(hostgroup, module_target_sat):
    """Create HostGroup then fail to update its name

    :id: 42d208a4-f518-4ff2-9b7a-311adb460abd

    :expectedresults: HostGroup name is not updated
    """
    new_name = invalid_values_list()[0]
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.HostGroup.update({'id': hostgroup['id'], 'new-name': new_name})
    result = module_target_sat.cli.HostGroup.info({'id': hostgroup['id']})
    assert hostgroup['name'] == result['name']


def test_negative_delete_by_id(module_target_sat):
    """Create HostGroup then delete it by wrong ID

    :id: 047c9f1a-4dd6-4fdc-b7ed-37cc725c68d3

    :expectedresults: HostGroup is not deleted
    """
    entity_id = invalid_id_list()[0]
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.HostGroup.delete({'id': entity_id})


def test_positive_created_nested_hostgroup(module_org, module_target_sat):
    """Create a nested host group using multiple parent hostgroup paths.
    e.g. ` hostgroup create --organization 'org_name' --name new3 --parent-title new_1/new_2`

    :id: 02123cec-cb64-43dd-aafc-19332e2f5de7

    :BZ: 1807536

    :customerscenario: true

    :CaseImportance: Low
    """
    parent_hg = module_target_sat.cli_factory.hostgroup({'organization-ids': module_org.id})
    nested = module_target_sat.cli_factory.hostgroup(
        {'organization-ids': module_org.id, 'parent': parent_hg['name']}
    )
    sub_nested = module_target_sat.cli_factory.hostgroup(
        {'organization-ids': module_org.id, 'parent-title': f'{parent_hg["name"]}/{nested["name"]}'}
    )
    assert sub_nested['title'] == f"{parent_hg['name']}/{nested['name']}/{sub_nested['name']}"


@pytest.mark.stubbed
def test_positive_nested_hostgroup_info():
    """`hammer hostgroup info` for a nested host group shows the assigned puppet classes.

    :id: b49bad08-d93c-4b30-b7f0-504dbf4d9ba2

    :BZ: 1859712

    :customerscenario: true

    :steps:

        1. Create parent hostgroup and nested hostgroup, with puppet environment, classes, and
           parameters on each.
        2. Use hammer to get the parent hostgroup info, and verify that its puppet environment,
           classes, and parameters are visible.
           # hammer hostgroup info --id 1
           Id:                    1
           Name:                  parent_hostgroup
           [...]
           Puppet Environment:    common
           [...]
           Puppetclasses:
           .  my_class_1
           .  my_class_2
           Parameters:
           [...]
        3. Use hammer to get the nested hostgroup info, and verify that the puppet environment,
           classes, and parameters are visible.
           # hammer hostgroup info --id 2
           Id:                    2
           Name:                  nested_hostgroup
           [...]
           Parent:                parent_hostgroup
           [...]
           Puppetclasses:
           .  my_class_1
           .  my_class_2
           .  my_class_3
           [...]

    :expectedresults: Puppet environment, classes, and parameters visible for both parent and
        nested hostgroups.
    """
    pass
