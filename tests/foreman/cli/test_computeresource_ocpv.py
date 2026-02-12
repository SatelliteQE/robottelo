"""
:Requirement: Computeresource OCP-V

:CaseAutomation: Automated

:CaseComponent: ComputeResources-OCP-V

:Team: Rocket

:CaseImportance: High

"""

import random

from fauxfactory import gen_domain, gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS, FOREMAN_PROVIDERS_MODEL
from robottelo.exceptions import CLIReturnCodeError
from robottelo.hosts import ContentHost
from robottelo.utils.datafactory import parametrized


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
        'invalid_hostname': {'hostname': 'invalid hostname'},
        'empty_hostname': {'hostname': ''},
    }


def valid_update_data():
    """Random data for valid update"""
    return {
        'utf8_name': {'new-name': gen_string('utf8', 255)},
        'alpha_name': {'new-name': gen_string('alphanumeric')},
        'white_space_name': {'new-name': f'white spaces {gen_string("alphanumeric")}'},
        'utf8_descr': {'description': gen_string('utf8', 255)},
        'alpha_descr': {'description': gen_string('alphanumeric')},
    }


def invalid_update_data():
    """Random data for invalid update"""
    return {
        'long_name': {'new-name': gen_string('utf8', 256)},
        'empty_name': {'new-name': ''},
        'invalid_hostname': {'hostname': 'invalid hostname'},
        'empty_hostname': {'hostname': ''},
    }


@pytest.mark.e2e
@pytest.mark.upgrade
def test_positive_crud_ocpv_cr(module_ocpv_sat, module_org, module_location):
    """CRUD compute resource OCP-v

    :id: a2f99c0e-53b6-435d-9b59-c6cbbcabca1g

    :expectedresults: All crud operations are performed successfully
    """
    name = gen_string('alpha')
    description = gen_string('alpha')
    # CREATE
    cr = module_ocpv_sat.cli.ComputeResource.create(
        {
            'name': name,
            'description': description,
            'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
            'location-ids': module_location.id,
            'organization-ids': module_org.id,
            'hostname': settings.ocpv.hostname,
            'api-port': settings.ocpv.api_port,
            'namespace': settings.ocpv.namespace,
            'token': settings.ocpv.token,
            'ca-cert': settings.ocpv.ca_cert,
        }
    )
    assert cr['name'] == name
    assert cr['provider'] == FOREMAN_PROVIDERS['ocp-v']
    assert cr['description'] == description
    assert cr['hostname'] == settings.ocpv.hostname
    assert cr['locations'][0] == module_location.name
    assert cr['organizations'][0] == module_org.name
    # UPDATE
    new_name = gen_string('alphanumeric')
    new_description = gen_string('alphanumeric')
    new_org = module_ocpv_sat.cli.Org.create({'name': gen_string('alpha')})
    new_loc = module_ocpv_sat.cli.Location.create({'name': gen_string('alpha')})
    cr_update = module_ocpv_sat.cli.ComputeResource.update(
        {
            'id': cr['id'],
            'new-name': new_name,
            'description': new_description,
            'location-ids': new_loc['id'],
            'organization-ids': new_org['id'],
        }
    )
    # READ
    cr_read = module_ocpv_sat.cli.ComputeResource.info({'id': cr_update[0]['id']})
    assert cr_read['name'] == new_name
    assert cr_read['description'] == new_description
    assert cr_read['provider'] == FOREMAN_PROVIDERS['ocp-v']
    assert cr_read['hostname'] == settings.ocpv.hostname
    assert cr_read['locations'][0] == new_loc['name']
    assert cr_read['organizations'][0] == new_org['name']
    # LIST
    cr_list = module_ocpv_sat.cli.ComputeResource.list({'search': f'name={cr_read["name"]}'})
    assert len(cr_list) == 1
    assert cr_list[0]['id'] == cr['id']
    assert cr_list[0]['name'] == new_name
    assert cr_list[0]['provider'] == FOREMAN_PROVIDERS['ocp-v']
    # DELETE
    module_ocpv_sat.cli.ComputeResource.delete({'name': cr_list[0]['name']})
    assert not module_ocpv_sat.cli.ComputeResource.exists(search=('name', cr_list[0]['name']))


@pytest.mark.upgrade
@pytest.mark.parametrize('options', **parametrized(valid_name_desc_data()))
def test_positive_create_with_ocpv(options, module_ocpv_sat):
    """Test Compute Resource create

    :id: adc6f4f8-6420-4044-89d1-c69e0bfeeabz

    :expectedresults: Compute Resource created

    :parametrized: yes
    """
    module_ocpv_sat.cli.ComputeResource.create(
        {
            'description': options['description'],
            'name': options['name'],
            'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
            'hostname': settings.ocpv.hostname,
            'api-port': settings.ocpv.api_port,
            'namespace': settings.ocpv.namespace,
            'token': settings.ocpv.token,
            'ca-cert': settings.ocpv.ca_cert,
        }
    )


def test_positive_create_with_locs(module_ocpv_sat):
    """Create Compute Resource with multiple locations

    :id: f665c586-39bf-480a-a0fc-81d9e1eb7c55

    :expectedresults: Compute resource is created and has multiple
        locations assigned
    """
    locations_amount = random.randint(3, 5)
    locations = [module_ocpv_sat.cli_factory.make_location() for _ in range(locations_amount)]
    comp_resource = module_ocpv_sat.cli_factory.compute_resource(
        {
            'location-ids': [location['id'] for location in locations],
            'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
            'hostname': settings.ocpv.hostname,
            'api-port': settings.ocpv.api_port,
            'namespace': settings.ocpv.namespace,
            'token': settings.ocpv.token,
            'ca-cert': settings.ocpv.ca_cert,
        }
    )
    assert len(comp_resource['locations']) == locations_amount
    for location in locations:
        assert location['name'] in comp_resource['locations']


### Negative create


@pytest.mark.parametrize('options', **parametrized(invalid_create_data()))
def test_negative_create_with_name_hostname(options, module_ocpv_sat):
    """Compute Resource negative create with invalid values

    :id: cd432ff3-b3b9-49cd-9a16-ed00d81679de

    :expectedresults: Compute resource not created

    :parametrized: yes
    """
    with pytest.raises(CLIReturnCodeError):
        module_ocpv_sat.cli.ComputeResource.create(
            {
                'name': options.get('name', gen_string(str_type='alphanumeric')),
                'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
                'hostname': options.get('hostname', gen_domain()),
                'api-port': settings.ocpv.api_port,
                'namespace': settings.ocpv.namespace,
                'token': settings.ocpv.token,
                'ca-cert': settings.ocpv.ca_cert,
            }
        )


def test_negative_create_with_same_name(module_ocpv_sat):
    """Compute Resource negative create with the same name

    :id: ddb5c45b-1ea3-46d0-b248-56c0388d2e4c

    :expectedresults: Compute resource not created
    """
    comp_res = module_ocpv_sat.cli_factory.compute_resource(
        {
            'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
            'hostname': settings.ocpv.hostname,
            'api-port': settings.ocpv.api_port,
            'namespace': settings.ocpv.namespace,
            'token': settings.ocpv.token,
            'ca-cert': settings.ocpv.ca_cert,
        }
    )
    with pytest.raises(CLIReturnCodeError):
        module_ocpv_sat.cli.ComputeResource.create(
            {
                'name': comp_res['name'],
                'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
                'hostname': settings.ocpv.hostname,
                'api-port': settings.ocpv.api_port,
                'namespace': settings.ocpv.namespace,
                'token': settings.ocpv.token,
                'ca-cert': settings.ocpv.ca_cert,
            }
        )


def test_negative_create_ocpv_with_hostname(module_location, module_org, module_ocpv_sat):
    """OCP-V compute resource negative create with invalid values

    :id: 1f318a4b-8dca-491b-b56d-cff773ed624g

    :expectedresults: Compute resource is not created
    """
    cr_name = gen_string('alpha')
    with pytest.raises(CLIReturnCodeError):
        module_ocpv_sat.cli.ComputeResource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
                'hostname': 'invalid hostname',
                'organizations': module_org.name,
                'locations': module_location.name,
                'api-port': settings.ocpv.api_port,
                'namespace': settings.ocpv.namespace,
                'token': settings.ocpv.token,
                'ca-cert': settings.ocpv.ca_cert,
            }
        )


### Update Positive


@pytest.mark.parametrize('options', **parametrized(valid_update_data()))
def test_positive_update_name(options, module_ocpv_sat):
    """Compute Resource positive update

    :id: 213d7f04-4c54-4985-8ca0-d2a1a9e3b309

    :expectedresults: Compute Resource successfully updated

    :parametrized: yes
    """
    comp_res = module_ocpv_sat.cli_factory.compute_resource(
        {
            'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
            'hostname': settings.ocpv.hostname,
            'api-port': settings.ocpv.api_port,
            'namespace': settings.ocpv.namespace,
            'token': settings.ocpv.token,
            'ca-cert': settings.ocpv.ca_cert,
        }
    )
    options.update({'name': comp_res['name']})
    # update Compute Resource
    module_ocpv_sat.cli.ComputeResource.update(options)
    # check updated values
    result = module_ocpv_sat.cli.ComputeResource.info({'id': comp_res['id']})
    assert result['description'] == options.get('description', comp_res['description'])
    assert result['name'] == options.get('new-name', comp_res['name'])
    assert result['hostname'] == options.get('hostname', comp_res['hostname'])
    assert result['provider'].lower() == comp_res['provider'].lower()


### Update Negative


@pytest.mark.parametrize('options', **parametrized(invalid_update_data()))
def test_negative_update(options, module_ocpv_sat):
    """Compute Resource negative update

    :id: e7aa9b39-dd01-4f65-8e89-ff5a6f4ee0e0

    :expectedresults: Compute Resource not updated

    :parametrized: yes
    """
    comp_res = module_ocpv_sat.cli_factory.compute_resource(
        {
            'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
            'hostname': settings.ocpv.hostname,
            'api-port': settings.ocpv.api_port,
            'namespace': settings.ocpv.namespace,
            'token': settings.ocpv.token,
            'ca-cert': settings.ocpv.ca_cert,
        }
    )
    with pytest.raises(CLIReturnCodeError):
        module_ocpv_sat.cli.ComputeResource.update(dict({'name': comp_res['name']}, **options))
    result = module_ocpv_sat.cli.ComputeResource.info({'id': comp_res['id']})
    # check attributes have not changed
    assert result['name'] == comp_res['name']
    options.pop('new-name', None)
    for key in options:
        assert comp_res[key] == result[key]


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.rhel_ver_match('9')
@pytest.mark.parametrize('pxe_loader', ['uefi', 'secureboot'], indirect=True)
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
@pytest.mark.skip(reason='Skipping this until we have OCP-V provisioning support')
def test_positive_provision_end_to_end(
    request,
    pxe_loader,
    setting_update,
    module_ocpv_sat,
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    provisioning_hostgroup,
    module_provisioning_rhel_content,
):
    """Provision a host on OCP-V compute resource with the help of hostgroup.

    :id: b003faa9-2810-4176-94d2-ea84bed248eh

    :setup: Hostgroup and provisioning setup like domain, subnet etc.

    :steps:
        1. Create a Libvirt compute resource.
        2. Create a host on Libvirt compute resource using the Hostgroup
        3. Use compute-attributes parameter to specify key-value parameters
           regarding the virtual machine.
        4. Provision the host.

    :expectedresults: Host should be provisioned with hostgroup

    :parametrized: yes

    :customerscenario: true
    """
    sat = module_provisioning_sat.sat
    cr_name = gen_string('alpha')
    hostname = gen_string('alpha').lower()
    cr = sat.cli.ComputeResource.create(
        {
            'name': cr_name,
            'provider': FOREMAN_PROVIDERS_MODEL['ocp-v'],
            'hostname': settings.ocpv.hostname,
            'organizations': module_sca_manifest_org.name,
            'locations': module_location.name,
            'api-port': settings.ocpv.api_port,
            'namespace': settings.ocpv.namespace,
            'token': settings.ocpv.token,
            'ca-cert': settings.ocpv.ca_cert,
        }
    )
    assert cr['name'] == cr_name

    host = sat.cli.Host.create(
        {
            'name': hostname,
            'location': module_location.name,
            'organization': module_sca_manifest_org.name,
            'hostgroup': provisioning_hostgroup.name,
            'compute-resource-id': cr['id'],
            'ip': None,
            'mac': None,
            'compute-attributes': f'cpus=1, memory=6442450944, start=1, firmware={pxe_loader.vm_firmware}',
            'interface': f'compute_cni_provider=multus,compute_network=nad-vlan-{settings.provisioning.vlan_id}',
            'volume': 'capacity=10,storage_class="trident-nfs (csi.trident.netapp.io)"',
            'parameters': 'name=remote_execution_connect_by_ip,type=boolean,value=true',
            'provision-method': 'build',
        }
    )
    # teardown
    request.addfinalizer(lambda: sat.provisioning_cleanup(host['name'], interface='CLI'))

    # checks
    hostname = f'{hostname}.{module_provisioning_sat.domain.name}'
    assert hostname == host['name']
    host_info = sat.cli.Host.info({'name': hostname})

    wait_for(
        lambda: (
            sat.cli.Host.info({'name': hostname})['status']['build-status']
            != 'Pending installation'
        ),
        timeout=1800,
        delay=30,
    )
    host_info = sat.cli.Host.info({'id': host['id']})
    assert host_info['status']['build-status'] == 'Installed'

    # Verify SecureBoot is enabled on host after provisioning is completed successfully
    if pxe_loader.vm_firmware == 'uefi_secure_boot':
        provisioning_host = ContentHost(host_info['network']['ipv4-address'])
        # Wait for the host to be rebooted and SSH daemon to be started.
        provisioning_host.wait_for_connection()
        assert 'SecureBoot enabled' in provisioning_host.execute('mokutil --sb-state').stdout


@pytest.mark.stubbed
def test_positive_provision_ocpv_without_host_group():
    """Provision a host on OCP-V compute resource without
    the help of hostgroup.

    :id: 861940cb-1550-4f00-9df2-5a45683635b9

    :steps:
        1. Create a OCP-V compute resource.
        2. Create a host on OCP-V compute resource.
        3. Use compute-attributes parameter to specify key-value parameters
           regarding the virtual machine.
        4. Provision the host.

    :expectedresults: The host should be provisioned successfully

    :CaseAutomation: NotAutomated
    """


@pytest.mark.stubbed
def test_positive_provision_ocpv_image_based_and_disassociate():
    """Provision a host on OCP-V compute resource using image-based provisioning

    :id: ba78858f-5cff-462e-a35d-f5aa4d11db59

    :steps:
        1. Create a OCP-V CR
        1. Create an image on that CR
        2. Create a new host using that CR and image
        3. Disassociate the host from the CR

    :expectedresults: Host should be provisioned with image, associated to CR, then disassociated

    :CaseAutomation: NotAutomated
    """
