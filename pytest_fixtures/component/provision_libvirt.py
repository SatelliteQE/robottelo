# Compute resource - Libvirt entities
from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS, LIBVIRT_RESOURCE_URL

LIBVIRT_URL = LIBVIRT_RESOURCE_URL % settings.libvirt.libvirt_hostname


@pytest.fixture(scope='module')
def module_cr_libvirt(module_target_sat, module_org, module_location):
    return module_target_sat.api.LibvirtComputeResource(
        name=gen_string('alpha'),
        provider=FOREMAN_PROVIDERS['libvirt'],
        display_type='VNC',
        organization=[module_org],
        location=[module_location],
        url=LIBVIRT_URL,
    ).create()


@pytest.fixture(scope='module')
def module_libvirt_image(
    module_target_sat, module_provisioning_rhel_content, module_cr_libvirt, default_architecture
):
    return module_target_sat.api.Image(
        compute_resource=module_cr_libvirt,
        name=gen_string('alpha'),
        operatingsystem=module_provisioning_rhel_content.os,
        architecture=default_architecture,
        username=settings.server.SSH_USERNAME,
        password=settings.server.SSH_PASSWORD,
        user_data=False,
        uuid=settings.libvirt.LIBVIRT_IMAGE_PATH,
    ).create()


@pytest.fixture(scope='module')
def module_libvirt_provisioning_sat(module_provisioning_sat):
    # Configure Libvirt CR for provisioning
    module_provisioning_sat.sat.configure_libvirt_cr()
    return module_provisioning_sat
