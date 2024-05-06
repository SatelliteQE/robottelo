"""
:Requirement: Computeresource Vmware

:CaseComponent: ComputeResources-VMWare

:Team: Rocket

:CaseImportance: High

:CaseAutomation: Automated

"""

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
@pytest.mark.parametrize('vmware', ['vmware7', 'vmware8'], indirect=True)
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.parametrize('provision_method', ['build', 'bootdisk'])
@pytest.mark.rhel_ver_match('[9]')
def test_positive_provision_end_to_end(
    request,
    setting_update,
    module_provisioning_rhel_content,
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    pxe_loader,
    module_vmware_cr,
    module_vmware_hostgroup,
    provision_method,
    vmware,
    vmwareclient,
):
    """Provision a host on vmware compute resource with
    the help of hostgroup.

    :id: 6985e7c0-d258-4fc4-833b-e680804b55e8

    :steps:

        1. Configure provisioning setup.
        2. Create VMware CR
        3. Configure host group setup.
        4. Provision a host on VMware
        5. Verify created host on VMware with wrapanapi

    :expectedresults: Host is provisioned succesfully with hostgroup

    :CaseImportance: Critical

    :BZ: 2186114
    """
    sat = module_provisioning_sat.sat
    name = gen_string('alpha').lower()
    host = sat.api.Host(
        hostgroup=module_vmware_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        name=name,
        operatingsystem=module_provisioning_rhel_content.os,
        subnet=module_provisioning_sat.subnet,
        compute_attributes={
            'path': '/Datacenters/SatQE-Datacenter/vm/',
            'cpus': 2,
            'memoy_mb': 6000,
            'cluster': f'{settings.vmware.cluster}',
            'start': '1',
            'guest_id': 'rhel8_64Guest',
            'volumes_attributes': {
                '0': {
                    'size_gb': 10,
                    'thin': '1',
                    'storage_pod': f'{settings.vmware.datastore_cluster}',
                },
            },
        },
        interfaces_attributes={
            '0': {
                'type': 'interface',
                'primary': True,
                'managed': True,
                'compute_attributes': {
                    'model': 'VirtualVmxnet3',
                    'network': f'VLAN {settings.provisioning.vlan_id}',
                },
            }
        },
        provision_method=provision_method,
        build=True,
    ).create(create_missing=False)

    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))
    assert host.name == f'{name}.{module_provisioning_sat.domain.name}'
    # check if vm is created on vmware
    assert vmwareclient.does_vm_exist(host.name) is True
    # check the build status
    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=1500,
        delay=10,
    )
    assert host.read().build_status_label == 'Installed'
