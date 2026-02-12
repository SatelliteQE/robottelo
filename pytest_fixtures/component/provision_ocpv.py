# Compute resource - OCP-V entities
from box import Box
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


@pytest.fixture
def module_ocpv_image(
    module_ocpv_sat,
    module_ocpv_cr,
    default_architecture,
    default_partitiontable,
    module_org,
):
    """Create an OS and image for OCP-V compute resource."""
    medium = module_ocpv_sat.api.Media(organization=[module_org]).create()
    image_os = module_ocpv_sat.api.OperatingSystem(
        name=(gen_string('alpha')),
        description=gen_string('alpha'),
        minor=settings.ocpv.image_os.split()[1].split('.')[1],
        major=settings.ocpv.image_os.split()[1].split('.')[0],
        family='Rhcos',
        release_name=gen_string('alpha'),
        architecture=[default_architecture],
        ptable=[default_partitiontable],
        medium=[medium],
    ).create()
    image = module_ocpv_sat.api.Image(
        architecture=default_architecture,
        compute_resource=module_ocpv_cr,
        name=gen_string('alpha'),
        operatingsystem=image_os,
        username=settings.ocpv.image_username,
        uuid=settings.ocpv.image_name,
        password=settings.ocpv.image_password,
        user_data=True,
    ).create()
    yield Box(image=image, os=image_os)
    image.delete()
    image_os.delete()
    medium.delete()


@pytest.fixture
def module_ocpv_hostgroup(
    module_ocpv_cr,
    module_ocpv_sat,
    module_org,
    module_location,
    default_architecture,
    module_lce_library,
    module_provisioning_capsule,
    module_ocpv_image,
):
    """Create a hostgroup for OCP-V provisioning."""
    provisioning_domain_name = f"{gen_string('alpha').lower()}.foo"
    domain = module_ocpv_sat.api.Domain(
        organization=[module_org], location=[module_location], name=provisioning_domain_name
    ).create()

    hg = module_ocpv_sat.api.HostGroup(
        name=gen_string('alpha'),
        organization=[module_org],
        location=[module_location],
        architecture=default_architecture,
        content_source=module_provisioning_capsule.id,
        content_view=module_org.default_content_view,
        compute_resource=module_ocpv_cr,
        domain=domain,
        lifecycle_environment=module_lce_library,
        root_pass=settings.provisioning.host_root_password,
        operatingsystem=module_ocpv_image.os,
    ).create()
    yield hg
    hg.delete()
    domain.delete()
