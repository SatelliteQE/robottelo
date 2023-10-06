from fauxfactory import gen_string
import pytest

from robottelo.config import settings


@pytest.fixture(scope='module')
def module_vmware_cr(module_provisioning_sat, module_sca_manifest_org, module_location):
    vmware_cr = module_provisioning_sat.sat.api.VMWareComputeResource(
        name=gen_string('alpha'),
        provider='Vmware',
        url=settings.vmware.vcenter,
        user=settings.vmware.username,
        password=settings.vmware.password,
        datacenter=settings.vmware.datacenter,
        organization=[module_sca_manifest_org],
        location=[module_location],
    ).create()
    return vmware_cr


@pytest.fixture
def module_vmware_hostgroup(
    module_vmware_cr,
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    default_architecture,
    module_provisioning_rhel_content,
    module_lce_library,
    default_partitiontable,
    module_provisioning_capsule,
    pxe_loader,
):
    return module_provisioning_sat.sat.api.HostGroup(
        name=gen_string('alpha'),
        organization=[module_sca_manifest_org],
        location=[module_location],
        architecture=default_architecture,
        domain=module_provisioning_sat.domain,
        content_source=module_provisioning_capsule.id,
        content_view=module_provisioning_rhel_content.cv,
        compute_resource=module_vmware_cr,
        kickstart_repository=module_provisioning_rhel_content.ksrepo,
        lifecycle_environment=module_lce_library,
        root_pass=settings.provisioning.host_root_password,
        operatingsystem=module_provisioning_rhel_content.os,
        ptable=default_partitiontable,
        subnet=module_provisioning_sat.subnet,
        pxe_loader=pxe_loader.pxe_loader,
        group_parameters_attributes=[
            # assign AK in order the hosts to be subscribed
            {
                'name': 'kt_activation_keys',
                'parameter_type': 'string',
                'value': module_provisioning_rhel_content.ak.name,
            },
        ],
    ).create()
