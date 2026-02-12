# Compute resource - OCP-V entities
from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS_MODEL
from robottelo.utils.installer import InstallerCommand


@pytest.fixture(scope='module')
def module_ocpv_sat(module_target_sat):
    installer_result = module_target_sat.execute(
        InstallerCommand(
            installer_args=[
                'enable-foreman-plugin-kubevirt',
                'enable-foreman-cli-kubevirt',
            ]
        ).get_command(),
        timeout='20m',
    )
    assert installer_result.status == 0
    assert 'Success!' in installer_result.stdout
    return module_target_sat


@pytest.fixture(scope='module')
def module_ocpv_cr(module_ocpv_sat, module_org, module_location):
    """Create a OCP-V/Kubevirt compute resource for the module."""
    return module_ocpv_sat.api.OCPVComputeResource(
        name=gen_string('alpha'),
        provider=FOREMAN_PROVIDERS_MODEL['ocp-v'],
        hostname=settings.ocpv.hostname,
        api_port=settings.ocpv.api_port,
        namespace=settings.ocpv.namespace,
        token=settings.ocpv.token,
        ca_cert=settings.ocpv.ca_cert,
        organization=[module_org],
        location=[module_location],
    ).create()
