"""Test class for Host Collection CLI

:Requirement: Host collection

:CaseAutomation: Automated

:CaseComponent: HostCollections

:team: Phoenix-subscriptions

:CaseImportance: High

"""

from broker import Broker
from fauxfactory import gen_string
import pytest

from robottelo.constants import DEFAULT_CV, ENVIRONMENT
from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError
from robottelo.hosts import ContentHost
from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
    valid_data_list,
)


def _make_fake_host_helper(module_org, sat):
    """Make a new fake host"""
    library = sat.cli.LifecycleEnvironment.info(
        {'organization-id': module_org.id, 'name': ENVIRONMENT}
    )
    default_cv = sat.cli.ContentView.info({'organization-id': module_org.id, 'name': DEFAULT_CV})
    return sat.cli_factory.make_fake_host(
        {
            'content-view-id': default_cv['id'],
            'lifecycle-environment-id': library['id'],
            'name': gen_string('alpha', 15),
            'organization-id': module_org.id,
        }
    )


@pytest.mark.upgrade
@pytest.mark.e2e
def test_positive_end_to_end(module_org, module_target_sat):
    """Check if host collection can be created with name and description,
    content host can be added and removed, host collection can be listed,
    updated and deleted

    :id: 2d3b718e-6f57-4c83-aedb-15604cc8a4bd

    :expectedresults: Host collection is created and has expected name and
        description, content-host is added and removed, host collection is
        updated and deleted.

    :CaseImportance: Critical
    """
    name = list(valid_data_list().values())[0]
    desc = list(valid_data_list().values())[0]
    new_host_col = module_target_sat.cli_factory.make_host_collection(
        {'description': desc, 'name': name, 'organization-id': module_org.id}
    )
    assert new_host_col['name'] == name
    assert new_host_col['description'] == desc

    # add host
    new_system = _make_fake_host_helper(module_org, module_target_sat)
    no_of_content_host = new_host_col['total-hosts']
    module_target_sat.cli.HostCollection.add_host(
        {'host-ids': new_system['id'], 'id': new_host_col['id']}
    )
    result = module_target_sat.cli.HostCollection.info({'id': new_host_col['id']})
    assert result['total-hosts'] > no_of_content_host

    # list hosts
    result = module_target_sat.cli.HostCollection.hosts(
        {'name': name, 'organization-id': module_org.id}
    )
    assert new_system['name'].lower() == result[0]['name']
    # List all host collections within organization
    result = module_target_sat.cli.HostCollection.list({'organization': module_org.name})
    assert len(result) >= 1
    # Filter list by name
    result = module_target_sat.cli.HostCollection.list(
        {'name': name, 'organization-id': module_org.id}
    )
    assert len(result) == 1
    assert result[0]['id'] == new_host_col['id']
    # Filter list by associated host name
    result = module_target_sat.cli.HostCollection.list(
        {'organization': module_org.name, 'host': new_system['name']}
    )
    assert len(result) == 1
    assert result[0]['name'] == new_host_col['name']

    # remove host
    no_of_content_host = module_target_sat.cli.HostCollection.info({'id': new_host_col['id']})[
        'total-hosts'
    ]
    module_target_sat.cli.HostCollection.remove_host(
        {'host-ids': new_system['id'], 'id': new_host_col['id']}
    )
    result = module_target_sat.cli.HostCollection.info({'id': new_host_col['id']})
    assert no_of_content_host > result['total-hosts']

    # update
    new_name = list(valid_data_list().values())[0]
    new_desc = list(valid_data_list().values())[0]
    module_target_sat.cli.HostCollection.update(
        {'description': new_desc, 'id': new_host_col['id'], 'new-name': new_name}
    )
    result = module_target_sat.cli.HostCollection.info({'id': new_host_col['id']})
    assert result['name'] == new_name
    assert result['description'] == new_desc

    # delete
    module_target_sat.cli.HostCollection.delete({'id': new_host_col['id']})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.HostCollection.info({'id': new_host_col['id']})


def test_positive_create_with_limit(module_org, module_target_sat):
    """Check if host collection can be created with correct limits

    :id: 682b5624-1095-48e6-a0dd-c76e70ca6540

    :expectedresults: Host collection is created and has expected limits

    :CaseImportance: Critical
    """
    for limit in ('1', '3', '5', '10', '20'):
        new_host_col = module_target_sat.cli_factory.make_host_collection(
            {'max-hosts': limit, 'organization-id': module_org.id}
        )
        assert new_host_col['limit'] == limit


def test_positive_update_to_unlimited_hosts(module_org, module_target_sat):
    """Create Host Collection with a limit and update it to unlimited hosts

    :id: d688fd4a-88eb-484e-9e90-854e0595edd0

    :expectedresults: Host Collection is created and updated to unlimited hosts

    :CaseImportance: High
    """
    host_collection = module_target_sat.cli_factory.make_host_collection(
        {
            'max-hosts': 1,
            'organization-id': module_org.id,
        }
    )
    result = module_target_sat.cli.HostCollection.info(
        {'name': host_collection['name'], 'organization-id': module_org.id}
    )
    assert result['limit'] == '1'
    module_target_sat.cli.HostCollection.update(
        {
            'name': host_collection['name'],
            'organization-id': module_org.id,
            'unlimited-hosts': True,
        }
    )
    result = module_target_sat.cli.HostCollection.info(
        {'name': host_collection['name'], 'organization-id': module_org.id}
    )
    assert result['limit'] == 'None'


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_name(module_org, name, module_target_sat):
    """Attempt to create host collection with invalid name of different
    types

    :id: 92a9eff0-693f-4ab8-b2c4-de08e5f709a7

    :parametrized: yes

    :expectedresults: Host collection is not created and error is raised

    :CaseImportance: Critical
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.make_host_collection(
            {'name': name, 'organization-id': module_org.id}
        )


def test_positive_update_limit(module_org, module_target_sat):
    """Check if host collection limits can be updated

    :id: 4c0e0c3b-82ac-4aa2-8378-6adc7946d4ec

    :expectedresults: Host collection limits is updated

    :BZ: 1245334

    :CaseImportance: Critical
    """
    new_host_col = module_target_sat.cli_factory.make_host_collection(
        {'organization-id': module_org.id}
    )
    for limit in ('3', '6', '9', '12', '15', '17', '19'):
        module_target_sat.cli.HostCollection.update({'id': new_host_col['id'], 'max-hosts': limit})
        result = module_target_sat.cli.HostCollection.info({'id': new_host_col['id']})
        assert result['limit'] == limit


def test_positive_list_by_org_id(module_org, module_target_sat):
    """Check if host collection list can be filtered by organization id

    :id: afbe077a-0de1-432c-a0c4-082129aab92e

    :expectedresults: Only host-collection within specific org is listed
    """
    # Create two host collections within different organizations
    module_target_sat.cli_factory.make_host_collection({'organization-id': module_org.id})
    new_org = module_target_sat.cli_factory.make_org()
    new_host_col = module_target_sat.cli_factory.make_host_collection(
        {'organization-id': new_org['id']}
    )
    # List all host collections
    assert len(module_target_sat.cli.HostCollection.list()) >= 2
    # Filter list by org id
    result = module_target_sat.cli.HostCollection.list({'organization-id': new_org['id']})
    assert len(result) == 1
    assert result[0]['id'] == new_host_col['id']


def test_positive_host_collection_host_pagination(module_org, module_target_sat):
    """Check if pagination configured on per-page param defined in hammer
    host-collection hosts command overrides global configuration defined
    on /etc/hammer/cli_config.yml, which default is 20 per page

    :BZ: 1343583

    :id: bbe1108b-bfb2-4a03-94ef-8fd1b5a0ec82

    :expectedresults: Number of host per page follows per_page
        configuration restriction
    """
    host_collection = module_target_sat.cli_factory.make_host_collection(
        {'organization-id': module_org.id}
    )
    host_ids = ','.join(
        _make_fake_host_helper(module_org, module_target_sat)['id'] for _ in range(2)
    )
    module_target_sat.cli.HostCollection.add_host(
        {'host-ids': host_ids, 'id': host_collection['id']}
    )
    for number in range(1, 3):
        listed_hosts = module_target_sat.cli.HostCollection.hosts(
            {
                'id': host_collection['id'],
                'organization-id': module_org.id,
                'per-page': number,
            }
        )
        assert len(listed_hosts) == number


def test_positive_copy_by_id(module_org, module_target_sat):
    """Check if host collection can be cloned by id

    :id: fd7cea50-bc56-4938-a81d-4f7a60711814

    :customerscenario: true

    :expectedresults: Host collection is cloned successfully

    :BZ: 1328925
    """
    host_collection = module_target_sat.cli_factory.make_host_collection(
        {'name': gen_string('alpha', 15), 'organization-id': module_org.id}
    )
    new_name = gen_string('numeric')
    new_host_collection = module_target_sat.cli.HostCollection.copy(
        {'id': host_collection['id'], 'new-name': new_name}
    )
    result = module_target_sat.cli.HostCollection.info({'id': new_host_collection[0]['id']})
    assert result['name'] == new_name


@pytest.mark.upgrade
def test_positive_register_host_ak_with_host_collection(module_org, module_ak_with_cv, target_sat):
    """Attempt to register a host using activation key with host collection

    :id: 62459e8a-0cfa-44ff-b70c-7f55b4757d66

    :expectedresults: Host successfully registered and listed in host collection

    :BZ: 1385814
    """
    host_info = _make_fake_host_helper(module_org, target_sat)

    hc = target_sat.cli_factory.make_host_collection({'organization-id': module_org.id})
    target_sat.cli.ActivationKey.add_host_collection(
        {
            'id': module_ak_with_cv.id,
            'organization-id': module_org.id,
            'host-collection-id': hc['id'],
        }
    )
    # add the registered instance host to collection
    target_sat.cli.HostCollection.add_host(
        {'id': hc['id'], 'organization-id': module_org.id, 'host-ids': host_info['id']}
    )

    with Broker(nick='rhel7', host_class=ContentHost) as client:
        # register the client host with the current activation key
        client.register(module_org, None, module_ak_with_cv.name, target_sat)
        assert client.subscribed
        # note: when registering the host, it should be automatically added to the host-collection
        client_host = target_sat.cli.Host.info({'name': client.hostname})
        hosts = target_sat.cli.HostCollection.hosts(
            {'id': hc['id'], 'organization-id': module_org.id}
        )
        assert len(hosts) == 2
        expected_hosts_ids = {host_info['id'], client_host['id']}
        hosts_ids = {host['id'] for host in hosts}
        assert hosts_ids == expected_hosts_ids
