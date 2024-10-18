"""Usage::

    hammer compute_resource [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a compute resource.
    info                          Show an compute resource.
    list                          List all compute resources.
    update                        Update a compute resource.
    delete                        Delete a compute resource.
    image                         View and manage compute resource's images


:Requirement: Computeresource Libvirt

:CaseAutomation: Automated

:CaseComponent: ComputeResources-libvirt

:Team: Rocket

:CaseImportance: High

"""

import random

from fauxfactory import gen_string, gen_url
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS, LIBVIRT_RESOURCE_URL
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import parametrized

LIBVIRT_URL = LIBVIRT_RESOURCE_URL % settings.libvirt.libvirt_hostname


def valid_name_desc_data():
    """Random data for valid name and description"""
    return {
        'numeric': {'name': gen_string('numeric'), 'description': gen_string('numeric')},
        'alpha_long_name': {
            'name': gen_string('alphanumeric', 255),
            'description': gen_string('alphanumeric'),
        },
        'alpha_long_descr': {
            'name': gen_string('alphanumeric'),
            'description': gen_string('alphanumeric', 255),
        },
        'utf8': {'name': gen_string('utf8'), 'description': gen_string('utf8')},
        'html': {
            'name': f'<html>{gen_string("alpha")}</html>',
            'description': f'<html>{gen_string("alpha")}</html>',
        },
        'non_letters': {
            'name': f"{gen_string('utf8')}[]@#$%^&*(),./?\\\"{{}}><|''",
            'description': "{gen_string('alpha')}[]@#$%^&*(),./?\\\"{{}}><|''",
        },
    }


def invalid_create_data():
    """Random data for invalid name and url"""
    return {
        'long_name': {'name': gen_string('alphanumeric', 256)},
        'empty_name': {'name': ''},
        'invalid_url': {'url': 'invalid url'},
        'empty_url': {'url': ''},
    }


def valid_update_data():
    """Random data for valid update"""
    return {
        'utf8_name': {'new-name': gen_string('utf8', 255)},
        'alpha_name': {'new-name': gen_string('alphanumeric')},
        'white_space_name': {'new-name': f'white spaces {gen_string("alphanumeric")}'},
        'utf8_descr': {'description': gen_string('utf8', 255)},
        'alpha_descr': {'description': gen_string('alphanumeric')},
        'gen_url': {'url': gen_url()},
        'local_url': {'url': 'qemu+tcp://localhost:16509/system'},
    }


def invalid_update_data():
    """Random data for invalid update"""
    return {
        'long_name': {'new-name': gen_string('utf8', 256)},
        'empty_name': {'new-name': ''},
        'invalid_url': {'url': 'invalid url'},
        'empty_url': {'url': ''},
    }


@pytest.fixture(scope="module")
def libvirt_url():
    return LIBVIRT_RESOURCE_URL % settings.libvirt.libvirt_hostname


@pytest.mark.e2e
@pytest.mark.upgrade
def test_positive_crud_libvirt_cr(module_target_sat, module_org, module_location, libvirt_url):
    """CRUD compute resource libvirt

    :id: a2f99c0e-53b6-435d-9b59-c6cbbcabca1e

    :expectedresults: All crud operations are performed successfully

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    desc = gen_string('alpha')
    provider = FOREMAN_PROVIDERS['libvirt']
    # CREATE
    cr = module_target_sat.cli.ComputeResource.create(
        {
            'name': name,
            'provider': 'Libvirt',
            'url': libvirt_url,
            'description': desc,
            'location-ids': module_location.id,
            'organization-ids': module_org.id,
        }
    )
    assert cr['name'] == name
    assert cr['provider'] == provider
    assert cr['description'] == desc
    assert cr['url'] == libvirt_url
    assert cr['locations'][0] == module_location.name
    assert cr['organizations'][0] == module_org.name
    # UPDATE
    new_name = gen_string('alphanumeric')
    new_desc = gen_string('alphanumeric')
    new_org = module_target_sat.cli.Org.create({'name': gen_string('alpha')})
    new_loc = module_target_sat.cli.Location.create({'name': gen_string('alpha')})
    cr_update = module_target_sat.cli.ComputeResource.update(
        {
            'id': cr['id'],
            'new-name': new_name,
            'description': new_desc,
            'location-ids': new_loc['id'],
            'organization-ids': new_org['id'],
        }
    )
    # READ
    cr_read = module_target_sat.cli.ComputeResource.info({'id': cr_update[0]['id']})
    assert cr_read['name'] == new_name
    assert cr_read['description'] == new_desc
    assert cr_read['provider'] == provider
    assert cr_read['url'] == libvirt_url
    assert cr_read['locations'][0] == new_loc['name']
    assert cr_read['organizations'][0] == new_org['name']
    # LIST
    cr_list = module_target_sat.cli.ComputeResource.list({'search': f'name={cr_read["name"]}'})
    assert len(cr_list) == 1
    assert cr_list[0]['id'] == cr['id']
    assert cr_list[0]['name'] == new_name
    assert cr_list[0]['provider'] == provider
    # DELETE
    module_target_sat.cli.ComputeResource.delete({'name': cr_list[0]['name']})
    assert not module_target_sat.cli.ComputeResource.exists(search=('name', cr_list[0]['name']))


@pytest.mark.tier1
@pytest.mark.upgrade
@pytest.mark.parametrize('options', **parametrized(valid_name_desc_data()))
def test_positive_create_with_libvirt(libvirt_url, options, target_sat):
    """Test Compute Resource create

    :id: adc6f4f8-6420-4044-89d1-c69e0bfeeab9

    :expectedresults: Compute Resource created

    :CaseImportance: Critical

    :parametrized: yes
    """
    target_sat.cli.ComputeResource.create(
        {
            'description': options['description'],
            'name': options['name'],
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': gen_url(),
        }
    )


@pytest.mark.tier2
def test_positive_create_with_locs(libvirt_url, module_target_sat):
    """Create Compute Resource with multiple locations

    :id: f665c586-39bf-480a-a0fc-81d9e1eb7c54

    :expectedresults: Compute resource is created and has multiple
        locations assigned

    :CaseImportance: High
    """
    locations_amount = random.randint(3, 5)
    locations = [module_target_sat.cli_factory.make_location() for _ in range(locations_amount)]
    comp_resource = module_target_sat.cli_factory.compute_resource(
        {
            'location-ids': [location['id'] for location in locations],
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': libvirt_url,
        }
    )
    assert len(comp_resource['locations']) == locations_amount
    for location in locations:
        assert location['name'] in comp_resource['locations']


# Negative create


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_create_data()))
def test_negative_create_with_name_url(libvirt_url, options, target_sat):
    """Compute Resource negative create with invalid values

    :id: cd432ff3-b3b9-49cd-9a16-ed00d81679dd

    :expectedresults: Compute resource not created

    :CaseImportance: High

    :parametrized: yes
    """
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.ComputeResource.create(
            {
                'name': options.get('name', gen_string(str_type='alphanumeric')),
                'provider': FOREMAN_PROVIDERS['libvirt'],
                'url': options.get('url', gen_url()),
            }
        )


@pytest.mark.tier2
def test_negative_create_with_same_name(libvirt_url, module_target_sat):
    """Compute Resource negative create with the same name

    :id: ddb5c45b-1ea3-46d0-b248-56c0388d2e4b

    :expectedresults: Compute resource not created

    :CaseImportance: High
    """
    comp_res = module_target_sat.cli_factory.compute_resource(
        {'provider': FOREMAN_PROVIDERS['libvirt'], 'url': libvirt_url}
    )
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ComputeResource.create(
            {
                'name': comp_res['name'],
                'provider': FOREMAN_PROVIDERS['libvirt'],
                'url': gen_url(),
            }
        )


# Update Positive


@pytest.mark.tier1
@pytest.mark.parametrize('options', **parametrized(valid_update_data()))
def test_positive_update_name(libvirt_url, options, module_target_sat):
    """Compute Resource positive update

    :id: 213d7f04-4c54-4985-8ca0-d2a1a9e3b305

    :expectedresults: Compute Resource successfully updated

    :CaseImportance: Critical

    :parametrized: yes
    """
    comp_res = module_target_sat.cli_factory.compute_resource(
        {'provider': FOREMAN_PROVIDERS['libvirt'], 'url': libvirt_url}
    )
    options.update({'name': comp_res['name']})
    # update Compute Resource
    module_target_sat.cli.ComputeResource.update(options)
    # check updated values
    result = module_target_sat.cli.ComputeResource.info({'id': comp_res['id']})
    assert result['description'] == options.get('description', comp_res['description'])
    assert result['name'] == options.get('new-name', comp_res['name'])
    assert result['url'] == options.get('url', comp_res['url'])
    assert result['provider'].lower() == comp_res['provider'].lower()


# Update Negative


@pytest.mark.tier2
@pytest.mark.parametrize('options', **parametrized(invalid_update_data()))
def test_negative_update(libvirt_url, options, module_target_sat):
    """Compute Resource negative update

    :id: e7aa9b39-dd01-4f65-8e89-ff5a6f4ee0e3

    :expectedresults: Compute Resource not updated

    :CaseImportance: High

    :parametrized: yes
    """
    comp_res = module_target_sat.cli_factory.compute_resource(
        {'provider': FOREMAN_PROVIDERS['libvirt'], 'url': libvirt_url}
    )
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.ComputeResource.update(dict({'name': comp_res['name']}, **options))
    result = module_target_sat.cli.ComputeResource.info({'id': comp_res['id']})
    # check attributes have not changed
    assert result['name'] == comp_res['name']
    options.pop('new-name', None)
    for key in options:
        assert comp_res[key] == result[key]


@pytest.mark.tier2
@pytest.mark.parametrize('set_console_password', ['true', 'false'])
def test_positive_create_with_console_password_and_name(
    libvirt_url, set_console_password, module_target_sat
):
    """Create a compute resource with ``--set-console-password``.

    :id: 5b4c838a-0265-4c71-a73d-305fecbe508a

    :expectedresults: No error is returned.

    :BZ: 1100344

    :CaseImportance: High

    :parametrized: yes
    """
    module_target_sat.cli.ComputeResource.create(
        {
            'name': gen_string('utf8'),
            'provider': 'Libvirt',
            'set-console-password': set_console_password,
            'url': gen_url(),
        }
    )


@pytest.mark.tier2
@pytest.mark.parametrize('set_console_password', ['true', 'false'])
def test_positive_update_console_password(libvirt_url, set_console_password, module_target_sat):
    """Update a compute resource with ``--set-console-password``.

    :id: ef09351e-dcd3-4b4f-8d3b-995e9e5873b3

    :expectedresults: No error is returned.

    :BZ: 1100344

    :CaseImportance: High

    :parametrized: yes
    """
    cr_name = gen_string('utf8')
    module_target_sat.cli.ComputeResource.create(
        {'name': cr_name, 'provider': 'Libvirt', 'url': gen_url()}
    )
    module_target_sat.cli.ComputeResource.update(
        {'name': cr_name, 'set-console-password': set_console_password}
    )


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
def test_positive_provision_end_to_end(
    request,
    setting_update,
    module_libvirt_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    provisioning_hostgroup,
    module_provisioning_rhel_content,
):
    """Provision a host on Libvirt compute resource with the help of hostgroup.

    :id: b003faa9-2810-4176-94d2-ea84bed248ec

    :setup: Hostgroup and provisioning setup like domain, subnet etc.

    :steps:
        1. Create a Libvirt compute resource.
        2. Create a host on Libvirt compute resource using the Hostgroup
        3. Use compute-attributes parameter to specify key-value parameters
           regarding the virtual machine.
        4. Provision the host.

    :expectedresults: Host should be provisioned with hostgroup

    :parametrized: yes

    :BZ: 2236693

    :Verifies: SAT-22491

    :customerscenario: true
    """
    sat = module_libvirt_provisioning_sat.sat
    cr_name = gen_string('alpha')
    hostname = gen_string('alpha').lower()
    libvirt_cr = sat.cli.ComputeResource.create(
        {
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'url': LIBVIRT_URL,
            'organizations': module_sca_manifest_org.name,
            'locations': module_location.name,
        }
    )
    assert libvirt_cr['name'] == cr_name
    host = sat.cli.Host.create(
        {
            'name': hostname,
            'location': module_location.name,
            'organization': module_sca_manifest_org.name,
            'hostgroup': provisioning_hostgroup.name,
            'compute-resource-id': libvirt_cr['id'],
            'ip': None,
            'mac': None,
            'compute-attributes': 'cpus=1, memory=6442450944, start=1',
            'interface': f'compute_type=bridge,compute_bridge=br-{settings.provisioning.vlan_id}',
            'volume': 'capacity=10',
            'provision-method': 'build',
        }
    )
    # teardown
    request.addfinalizer(lambda: sat.provisioning_cleanup(host['name'], interface='CLI'))

    # checks
    hostname = f'{hostname}.{module_libvirt_provisioning_sat.domain.name}'
    assert hostname == host['name']
    host_info = sat.cli.Host.info({'name': hostname})
    # Check on Libvirt, if VM exists
    result = sat.execute(
        f'su foreman -s /bin/bash -c "virsh -c {LIBVIRT_URL} list --state-running"'
    )
    assert hostname in result.stdout

    wait_for(
        lambda: sat.cli.Host.info({'name': hostname})['status']['build-status']
        != 'Pending installation',
        timeout=1800,
        delay=30,
    )
    host_info = sat.cli.Host.info({'id': host['id']})
    assert host_info['status']['build-status'] == 'Installed'
