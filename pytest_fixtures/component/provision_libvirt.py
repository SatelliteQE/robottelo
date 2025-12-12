# Compute resource - Libvirt entities
from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import COMPUTE_PROFILE_SMALL, FOREMAN_PROVIDERS, LIBVIRT_RESOURCE_URL

LIBVIRT_URL = LIBVIRT_RESOURCE_URL % settings.libvirt.libvirt_hostname


@pytest.fixture(scope='module')
def module_cr_libvirt(module_target_sat, module_org, module_location):
    """Create a Libvirt compute resource for the module."""
    return module_target_sat.api.LibvirtComputeResource(
        name=gen_string('alpha'),
        provider=FOREMAN_PROVIDERS['libvirt'],
        display_type='VNC',
        organization=[module_org],
        location=[module_location],
        url=LIBVIRT_URL,
    ).create()


@pytest.fixture(scope='module')
def module_libvirt_image(module_target_sat, module_cr_libvirt):
    return module_target_sat.api.Image(compute_resource=module_cr_libvirt).create()


@pytest.fixture(scope='module')
def module_libvirt_provisioning_sat(module_provisioning_sat):
    # Configure Libvirt CR for provisioning
    module_provisioning_sat.sat.configure_libvirt_cr()
    return module_provisioning_sat


@pytest.fixture(scope='module')
def module_libvirt_compute_profile(module_target_sat, module_cr_libvirt):
    """Create compute attributes for Libvirt compute profile."""
    return module_target_sat.api.ComputeAttribute(
        compute_profile=COMPUTE_PROFILE_SMALL,
        compute_resource=module_cr_libvirt,
        vm_attrs={
            'cpus': 1,
            'memory': 6442450944,
            'firmware': 'Automatic',
            'volumes_attributes': {'0': {'capacity': '10G', 'format_type': 'qcow2'}},
            'nics_attributes': {
                '0': {
                    'type': 'bridge',
                    'bridge': f'br-{settings.provisioning.vlan_id}',
                },
            },
        },
    ).create()
