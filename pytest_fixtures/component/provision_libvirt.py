# Compute resource - Libvirt entities
import pytest


@pytest.fixture(scope='module')
def module_cr_libvirt(module_target_sat, module_org, module_location):
    return module_target_sat.api.LibvirtComputeResource(
        organization=[module_org], location=[module_location]
    ).create()


@pytest.fixture(scope='module')
def module_libvirt_image(module_target_sat, module_cr_libvirt):
    return module_target_sat.api.Image(compute_resource=module_cr_libvirt).create()
