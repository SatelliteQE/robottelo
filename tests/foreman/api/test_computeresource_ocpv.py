"""
:Requirement: Computeresource - OCP-V

:CaseAutomation: Automated

:CaseComponent: ComputeResources-OCP-V

:Team: Rocket

:CaseImportance: High
"""

from fauxfactory import gen_string
import pytest
from requests.exceptions import HTTPError
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS, FOREMAN_PROVIDERS_MODEL
from robottelo.hosts import ContentHost
from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
    valid_data_list,
)

pytestmark = [pytest.mark.skip_if_not_set('ocpv')]


@pytest.mark.e2e
def test_positive_crud_ocpv_cr(module_ocpv_sat, module_org, module_location):
    """CRUD test to validate Compute Resource - OCP-V

    :id: 1e545c56-2f53-44c1-a17e-38c83f8fe0c9

    :expectedresults: Compute resources are created with expected names
    """
    name = gen_string('alphanumeric')
    description = gen_string('alphanumeric')

    cr = module_ocpv_sat.api.OCPVComputeResource(
        name=name,
        description=description,
        provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
        organization=[module_org],
        location=[module_location],
        hostname=settings.ocpv.hostname,
        api_port=settings.ocpv.api_port,
        namespace=settings.ocpv.namespace,
        token=settings.ocpv.token,
        ca_cert=settings.ocpv.ca_cert,
    ).create()
    assert cr.name == name
    assert cr.description == description
    assert cr.provider == FOREMAN_PROVIDERS_MODEL['ocp-v']
    assert cr.provider_friendly_name == FOREMAN_PROVIDERS['ocp-v']
    assert cr.hostname == settings.ocpv.hostname
    assert cr.api_port == settings.ocpv.api_port
    assert cr.namespace == settings.ocpv.namespace

    # Update
    new_name = gen_string('alphanumeric')
    new_description = gen_string('alphanumeric')
    new_org = module_ocpv_sat.api.Organization().create()
    new_loc = module_ocpv_sat.api.Location(organization=[new_org]).create()
    cr.name = new_name
    cr.description = new_description
    cr.organization = [new_org]
    cr.location = [new_loc]
    cr.update(['name', 'description', 'organization', 'location'])

    # READ
    updated_cr = module_ocpv_sat.api.OCPVComputeResource(id=cr.id).read()
    assert updated_cr.name == new_name
    assert updated_cr.description == new_description
    assert updated_cr.organization[0].id == new_org.id
    assert updated_cr.location[0].id == new_loc.id
    assert updated_cr.hostname == settings.ocpv.hostname
    assert updated_cr.api_port == settings.ocpv.api_port
    assert updated_cr.namespace == settings.ocpv.namespace

    # DELETE
    updated_cr.delete()
    assert not module_ocpv_sat.api.OCPVComputeResource().search(
        query={'search': f'name={new_name}'}
    )


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
def test_positive_userdata_image_provision_end_to_end(
    request,
    setting_update,
    module_ocpv_cr,
    module_ocpv_sat,
    module_org,
    module_location,
    module_ocpv_image,
    module_ocpv_hostgroup,
):
    """Provision a host on OpenShift Virtualization using image-based provisioning.

    :id: 330e3a16-47bf-4047-90dd-e4a577a34cbc

    :steps:
        1. Create OCP compute resource
        2. Create image for the compute resource
        3. Create userdata provisioning template and associate with OS
        4. Create hostgroup
        5. Provision a host using image-based provisioning
        6. Check if the host status is installed.

    :expectedresults: Host is provisioned successfully on OpenShift Virtualization

    """
    name = gen_string('alpha').lower()
    sat = module_ocpv_sat
    os = module_ocpv_image.os

    USERDATA_TEMPLATE = """\
    #cloud-config
    <%# Contact Foreman to confirm instance is built -%>
    phone_home:
      url: <%= foreman_url('built') %>
      post: []
      tries: 10
    """

    # Get the user_data template kind
    template_kind = sat.api.TemplateKind().search(query={'search': 'name=user_data'})[0]

    # Create custom userdata provisioning template to check host status.
    userdata_template = sat.api.ProvisioningTemplate(
        name=gen_string('alpha'),
        organization=[module_org],
        location=[module_location],
        snippet=False,
        template_kind=template_kind,
        operatingsystem=[os],
        template=USERDATA_TEMPLATE,
    ).create()

    # assign the userdata template to the os
    os.provisioning_template.append(userdata_template)
    os.update(['provisioning_template'])

    sat.api.OSDefaultTemplate(
        operatingsystem=os,
        provisioning_template=userdata_template,
        template_kind=template_kind,
    ).create()

    host = sat.api.Host(
        hostgroup=module_ocpv_hostgroup,
        organization=module_org,
        location=module_location,
        name=name,
        compute_attributes={
            'cpus': 1,
            'image_id': module_ocpv_image.image.uuid,
            'memory': '6442450944',
            'start': '1',
            'volumes_attributes': {
                '0': {
                    'storage_class': 'trident-nfs',
                    'capacity': '25G',
                    'bootable': 'true',
                },
            },
        },
        interfaces_attributes={
            '0': {
                'type': 'interface',
                'primary': True,
                'managed': True,
                'compute_attributes': {
                    'cni_provider': 'multus',
                    'network': f'{settings.ocpv.network}',
                },
            }
        },
        provision_method='image',
    ).create(create_missing=False)

    request.addfinalizer(host.delete)
    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=1500,
        delay=10,
    )
    assert host.name == f'{name}.{module_ocpv_hostgroup.domain.read().name}'
    assert host.build_status_label == 'Installed'


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_create_with_name_description(
    name, request, module_ocpv_sat, module_org, module_location
):
    """Create compute resources with different names and descriptions

    :id: 1e545c56-2f53-44c1-a17e-38c83f8fe0c8

    :expectedresults: Compute resources are created with expected names and descriptions

    :parametrized: yes
    """
    cr = module_ocpv_sat.api.OCPVComputeResource(
        name=name,
        description=name,
        organization=[module_org],
        location=[module_location],
        provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
        hostname=settings.ocpv.hostname,
        api_port=settings.ocpv.api_port,
        namespace=settings.ocpv.namespace,
        token=settings.ocpv.token,
        ca_cert=settings.ocpv.ca_cert,
    ).create()
    request.addfinalizer(cr.delete)
    assert cr.name == name
    assert cr.description == name


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_invalid_name(name, module_ocpv_sat, module_org, module_location):
    """Attempt to create compute resources with invalid names

    :id: f73bf838-3ffd-46d3-869c-81b334b47b15

    :expectedresults: Compute resources are not created

    :parametrized: yes
    """
    with pytest.raises(HTTPError):
        module_ocpv_sat.api.OCPVComputeResource(
            name=name,
            organization=[module_org],
            location=[module_location],
            provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
            hostname=settings.ocpv.hostname,
            api_port=settings.ocpv.api_port,
            namespace=settings.ocpv.namespace,
            token=settings.ocpv.token,
            ca_cert=settings.ocpv.ca_cert,
        ).create()


def test_negative_create_with_same_name(
    request,
    module_ocpv_sat,
    module_org,
    module_location,
):
    """Attempt to create a compute resource with already existing name

    :id: 9376e25c-2aa8-4d99-83aa-2eec160c030g

    :expectedresults: Compute resources is not created
    """
    name = gen_string('alphanumeric')
    cr = module_ocpv_sat.api.OCPVComputeResource(
        name=name,
        organization=[module_org],
        location=[module_location],
        provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
        hostname=settings.ocpv.hostname,
        api_port=settings.ocpv.api_port,
        namespace=settings.ocpv.namespace,
        token=settings.ocpv.token,
        ca_cert=settings.ocpv.ca_cert,
    ).create()

    request.addfinalizer(cr.delete)
    assert cr.name == name
    with pytest.raises(HTTPError):
        module_ocpv_sat.api.OCPVComputeResource(
            name=name,
            organization=[module_org],
            location=[module_location],
            provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
            hostname=settings.ocpv.hostname,
            api_port=settings.ocpv.api_port,
            namespace=settings.ocpv.namespace,
            token=settings.ocpv.token,
            ca_cert=settings.ocpv.ca_cert,
        ).create()


@pytest.mark.parametrize('hostname', **parametrized({'random': gen_string('alpha'), 'empty': ''}))
def test_negative_create_with_hostname(module_ocpv_sat, module_org, module_location, hostname):
    """Attempt to create compute resources with invalid hostname

    :id: 37e9bf39-382e-4f02-af54-d3a17e285c2h

    :expectedresults: Compute resources are not created

    :parametrized: yes
    """
    with pytest.raises(HTTPError):
        module_ocpv_sat.api.OCPVComputeResource(
            organization=[module_org],
            location=[module_location],
            provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
            hostname=hostname,
            api_port=settings.ocpv.api_port,
            namespace=settings.ocpv.namespace,
            token=settings.ocpv.token,
            ca_cert=settings.ocpv.ca_cert,
        ).create()


@pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
def test_negative_update_invalid_name(
    request, module_ocpv_sat, module_org, module_location, new_name
):
    """Attempt to update compute resource with invalid names

    :id: a6554c1f-e52f-4614-9fc3-2127ced31479

    :expectedresults: Compute resource is not updated

    :parametrized: yes
    """
    name = gen_string('alphanumeric')
    cr = module_ocpv_sat.api.OCPVComputeResource(
        name=name,
        organization=[module_org],
        location=[module_location],
        provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
        hostname=settings.ocpv.hostname,
        api_port=settings.ocpv.api_port,
        namespace=settings.ocpv.namespace,
        token=settings.ocpv.token,
        ca_cert=settings.ocpv.ca_cert,
    ).create()
    request.addfinalizer(cr.delete)
    cr.name = new_name
    with pytest.raises(HTTPError):
        cr.update(['name'])
    assert cr.read().name == name


def test_negative_update_same_name(request, module_ocpv_sat, module_org, module_location):
    """Attempt to update a compute resource with already existing name

    :id: 4d7c5eb0-b8cb-414f-aa10-fe464a164abe

    :expectedresults: Compute resources is not updated
    """
    name = gen_string('alphanumeric')
    cr = module_ocpv_sat.api.OCPVComputeResource(
        name=name,
        organization=[module_org],
        location=[module_location],
        provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
        hostname=settings.ocpv.hostname,
        api_port=settings.ocpv.api_port,
        namespace=settings.ocpv.namespace,
        token=settings.ocpv.token,
        ca_cert=settings.ocpv.ca_cert,
    ).create()
    request.addfinalizer(cr.delete)
    new_cr = module_ocpv_sat.api.OCPVComputeResource(
        organization=[module_org],
        location=[module_location],
        provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
        hostname=settings.ocpv.hostname,
        api_port=settings.ocpv.api_port,
        namespace=settings.ocpv.namespace,
        token=settings.ocpv.token,
        ca_cert=settings.ocpv.ca_cert,
    ).create()
    request.addfinalizer(new_cr.delete)
    new_cr.name = name
    with pytest.raises(HTTPError):
        new_cr.update(['name'])
    assert new_cr.read().name != name


@pytest.mark.parametrize('hostname', **parametrized({'random': gen_string('alpha'), 'empty': ''}))
def test_negative_update_hostname(hostname, request, module_ocpv_sat, module_org, module_location):
    """Attempt to update a compute resource with invalid url

    :id: b5256090-2ceb-4976-b54e-60d60419fe59

    :expectedresults: Compute resources is not updated

    :parametrized: yes
    """
    cr = module_ocpv_sat.api.OCPVComputeResource(
        organization=[module_org],
        location=[module_location],
        provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
        hostname=settings.ocpv.hostname,
        api_port=settings.ocpv.api_port,
        namespace=settings.ocpv.namespace,
        token=settings.ocpv.token,
        ca_cert=settings.ocpv.ca_cert,
    ).create()
    request.addfinalizer(cr.delete)
    cr.hostname = hostname
    with pytest.raises(HTTPError):
        cr.update(['hostname'])
    assert cr.read().hostname != hostname


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi', 'secureboot'], indirect=True)
@pytest.mark.rhel_ver_match('8')
@pytest.mark.skip(reason='Skipping this until we have OCP-V provisioning support')
def test_positive_provision_end_to_end(
    request,
    setting_update,
    module_provisioning_rhel_content,
    module_ocpv_sat,
    module_provisioning_sat,
    configure_secureboot_provisioning,
    module_sca_manifest_org,
    module_location,
    module_ssh_key_file,
    pxe_loader,
    provisioning_hostgroup,
):
    """Provision a host on OCP-V compute resource with the help of hostgroup.

    :id: 6985e7c0-d258-4fc4-833b-e680804b55eg

    :steps:
        1. Configure provisioning setup.
        2. Create OCP-V CR
        3. Configure host group setup.
        4. Create a host on OCP-V compute resource using the Hostgroup
        5. Verify created host on OCP-V.

    :expectedresults: Host is provisioned successfully with hostgroup
    """
    sat = module_provisioning_sat.sat
    cr_name = gen_string('alpha')
    host_name = gen_string('alpha').lower()
    cr = sat.api.OCPVComputeResource(
        name=cr_name,
        provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
        organization=[module_sca_manifest_org],
        location=[module_location],
        hostname=settings.ocpv.hostname,
        api_port=settings.ocpv.api_port,
        namespace=settings.ocpv.namespace,
        token=settings.ocpv.token,
        ca_cert=settings.ocpv.ca_cert,
    ).create()
    request.addfinalizer(cr.delete)
    assert cr.name == cr_name

    host = sat.api.Host(
        hostgroup=provisioning_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        name=host_name,
        compute_resource=cr,
        compute_attributes={
            'cpus': 1,
            'memory': 6442450944,
            'firmware': pxe_loader.vm_firmware,
            'start': '1',
            'volumes_attributes': {
                '0': {
                    'capacity': '10G',
                    'storage_class': 'trident-nfs (csi.trident.netapp.io)',
                },
            },
        },
        interfaces_attributes={
            '0': {
                'type': 'interface',
                'primary': True,
                'managed': True,
                'compute_attributes': {
                    'compute_cni_provider': 'multus',
                    'compute_network': f'nad-vlan-{settings.provisioning.vlan_id}',
                },
            }
        },
        provision_method='build',
        host_parameters_attributes=[
            {'name': 'remote_execution_connect_by_ip', 'value': 'true', 'parameter_type': 'boolean'}
        ],
        build=True,
    ).create(create_missing=False)
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))
    assert host.name == f'{host_name}.{module_provisioning_sat.domain.name}'

    # check the build status
    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=1500,
        delay=10,
    )
    assert host.read().build_status_label == 'Installed'

    # Verify SecureBoot is enabled on host after provisioning is completed successfully
    if pxe_loader.vm_firmware == 'uefi_secure_boot':
        provisioning_host = ContentHost(host.ip, auth=module_ssh_key_file)
        # Wait for the host to be rebooted and SSH daemon to be started.
        provisioning_host.wait_for_connection()
        # Enable Root Login
        if int(host.operatingsystem.read().major) >= 9:
            assert (
                provisioning_host.execute(
                    'echo -e "\nPermitRootLogin yes" >> /etc/ssh/sshd_config; systemctl restart sshd'
                ).status
                == 0
            )
        assert 'SecureBoot enabled' in provisioning_host.execute('mokutil --sb-state').stdout
