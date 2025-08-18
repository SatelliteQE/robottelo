# Compute resource - Libvirt entities
from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import COMPUTE_PROFILE_SMALL, FOREMAN_PROVIDERS, LIBVIRT_RESOURCE_URL

LIBVIRT_URL = LIBVIRT_RESOURCE_URL % settings.libvirt.libvirt_hostname


@pytest.fixture(scope='module')
def module_cr_libvirt(module_target_sat, module_org, module_location):
    """Create a Libvirt compute resource for the module.

    :param module_target_sat: Target Satellite instance
    :param module_org: Module-scoped organization
    :param module_location: Module-scoped location
    :return: Created LibvirtComputeResource entity
    """
    return module_target_sat.api.LibvirtComputeResource(
        name=gen_string('alpha'),
        provider=FOREMAN_PROVIDERS['libvirt'],
        display_type='VNC',
        organization=[module_org],
        location=[module_location],
        url=LIBVIRT_URL,
    ).create()


@pytest.fixture(scope='module')
def module_libvirt_image(module_target_sat, module_cr_libvirt, default_architecture):
    """Create a Libvirt image for provisioning.

    :param module_target_sat: Target Satellite instance
    :param module_cr_libvirt: Libvirt compute resource fixture
    :param default_architecture: Default architecture for the image
    :return: Created Image entity associated with the Libvirt compute resource
    """
    return module_target_sat.api.Image(
        compute_resource=module_cr_libvirt,
        name=gen_string('alpha'),
        operatingsystem=settings.libvirt.image_os,
        architecture=default_architecture,
        username=settings.libvirt.image_username,
        password=settings.libvirt.image_password,
        uuid=settings.libvirt.libvirt_image_path,
    ).create()


@pytest.fixture(scope='module')
def module_libvirt_cp(module_target_sat, module_libvirt_image):
    """Create compute attributes for Libvirt compute profile.

    :param module_target_sat: Target Satellite instance
    :param module_libvirt_image: Libvirt image fixture (used to get compute resource)
    :return: Created ComputeAttribute entity with VM specifications for small profile
    """
    cr = module_libvirt_image.compute_resource
    return module_target_sat.api.ComputeAttribute(
        compute_profile=COMPUTE_PROFILE_SMALL,
        compute_resource=cr,
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


@pytest.fixture(scope='module')
def module_libvirt_provisioning_sat(module_provisioning_sat):
    """Configure provisioning Satellite with Libvirt compute resource.

    :param module_provisioning_sat: Base provisioning Satellite fixture
    :return: Provisioning Satellite configured with Libvirt compute resource
    """
    # Configure Libvirt CR for provisioning
    module_provisioning_sat.sat.configure_libvirt_cr()
    return module_provisioning_sat
