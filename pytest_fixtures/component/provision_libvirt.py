# Compute resource - Libvirt entities
import pytest
from nailgun import entities


@pytest.fixture(scope="module")
def module_cr_libvirt(module_org, module_location):
    return entities.LibvirtComputeResource(
        organization=[module_org], location=[module_location]
    ).create()


@pytest.fixture(scope="module")
def module_libvirt_image(module_cr_libvirt):
    return entities.Image(compute_resource=module_cr_libvirt).create()
