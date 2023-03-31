# Google Cloud Engine Entities
import json
from tempfile import mkstemp

import pytest
from airgun.session import Session
from fauxfactory import gen_string
from nailgun import entities
from wrapanapi.systems.google import GoogleCloudSystem

from robottelo.config import settings
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.exceptions import GCECertNotFoundError


@pytest.fixture(scope='session')
def gce_cert(session_target_sat):
    _, gce_cert_file = mkstemp(suffix='.json')
    cert = json.loads(settings.gce.cert)
    cert['local_path'] = gce_cert_file
    with open(gce_cert_file, 'w') as f:
        json.dump(cert, f)
    session_target_sat.put(gce_cert_file, settings.gce.cert_path)
    if session_target_sat.execute(f'[ -f {settings.gce.cert_path} ]').status != 0:
        raise GCECertNotFoundError(
            f"The GCE certificate in path {settings.gce.cert_path} is not found in satellite."
        )
    return cert


@pytest.fixture(scope='session')
def gce_cert_puppet(session_puppet_enabled_sat):
    _, gce_cert_file = mkstemp(suffix='.json')
    cert = json.loads(settings.gce.cert)
    cert['local_path'] = gce_cert_file
    with open(gce_cert_file, 'w') as f:
        json.dump(cert, f)
    session_puppet_enabled_sat.put(gce_cert_file, settings.gce.cert_path)
    if session_puppet_enabled_sat.execute(f'[ -f {settings.gce.cert_path} ]').status != 0:
        pytest.fail(
            f"The GCE certificate in path {settings.gce.cert_path} is not found in satellite."
        )
    return cert


@pytest.fixture(scope='session')
def googleclient(gce_cert):
    gceclient = GoogleCloudSystem(
        project=gce_cert['project_id'],
        zone=settings.gce.zone,
        file_path=gce_cert['local_path'],
        file_type='json',
    )
    yield gceclient
    gceclient.disconnect()


@pytest.fixture(scope='session')
def gce_latest_rhel_uuid(googleclient):
    template_names = [img.name for img in googleclient.list_templates(True)]
    latest_rhel7_template = max(name for name in template_names if name.startswith('rhel-7'))
    latest_rhel7_uuid = googleclient.get_template(latest_rhel7_template, project='rhel-cloud').uuid
    return latest_rhel7_uuid


@pytest.fixture(scope='session')
def gce_custom_cloudinit_uuid(googleclient, gce_cert):
    cloudinit_uuid = googleclient.get_template('customcinit', project=gce_cert['project_id']).uuid
    return cloudinit_uuid


@pytest.fixture(scope='session')
def session_default_os(session_target_sat):
    """Default OS on the Satellite"""
    search_string = 'name="RedHat" AND (major="6" OR major="7" OR major="8")'
    return (
        session_target_sat.api.OperatingSystem().search(query={'search': search_string})[0].read()
    )


@pytest.fixture(scope='module')
def module_gce_compute(module_org, module_location, gce_cert):
    gce_cr = entities.GCEComputeResource(
        name=gen_string('alphanumeric'),
        provider='GCE',
        key_path=settings.gce.cert_path,
        zone=settings.gce.zone,
        organization=[module_org],
        location=[module_location],
    ).create()
    return gce_cr


@pytest.fixture(scope='module')
def module_gce_compute_puppet(
    session_puppet_enabled_sat, module_puppet_org, module_puppet_loc, gce_cert_puppet
):
    gce_cr = session_puppet_enabled_sat.api.GCEComputeResource(
        name=gen_string('alphanumeric'),
        provider='GCE',
        key_path=settings.gce.cert_path,
        zone=settings.gce.zone,
        organization=[module_puppet_org],
        location=[module_puppet_loc],
    ).create()
    return gce_cr


@pytest.fixture(scope='session')
def session_puppet_default_partition_table(session_puppet_enabled_sat):
    ptable = (
        session_puppet_enabled_sat.api.PartitionTable()
        .search(query={'search': f'name="{DEFAULT_PTABLE}"'})[0]
        .read()
    )
    return ptable


@pytest.fixture
def gce_template(googleclient):
    max_rhel7_template = max(
        img.name for img in googleclient.list_templates(True) if str(img.name).startswith('rhel-7')
    )
    return googleclient.get_template(max_rhel7_template, project='rhel-cloud').uuid


@pytest.fixture
def gce_cloudinit_template(googleclient, gce_cert):
    return googleclient.get_template('customcinit', project=gce_cert['project_id']).uuid


@pytest.fixture
def gce_domain(module_org, smart_proxy_location, gce_cert, target_sat):
    domain_name = f'{settings.gce.zone}.c.{gce_cert["project_id"]}.internal'
    domain = target_sat.api.Domain().search(query={'search': f'name={domain_name}'})
    if domain:
        domain = domain[0]
        domain.organization = [module_org]
        domain.location = [smart_proxy_location]
        domain.update(['organization', 'location'])
    if not domain:
        domain = target_sat.api.Domain(
            name=domain_name, location=[smart_proxy_location], organization=[module_org]
        ).create()
    return domain


@pytest.fixture
def gce_resource_with_image(
    gce_template,
    gce_cloudinit_template,
    gce_cert,
    default_architecture,
    default_os,
    smart_proxy_location,
    module_org,
    target_sat,
):
    json_key = json.dumps(gce_cert, indent=2)
    with Session('gce_tests') as session:
        # Until the CLI and API support is added for GCE,
        # creating GCE CR from UI
        cr_name = gen_string('alpha')
        vm_user = gen_string('alpha')
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['google'],
                'provider_content.json_key': json_key,
                'provider_content.zone.value': settings.gce.zone,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [smart_proxy_location.name],
            }
        )
    gce_cr = target_sat.api.AbstractComputeResource().search(query={'search': f'name={cr_name}'})[0]
    # Finish Image
    target_sat.api.Image(
        architecture=default_architecture,
        compute_resource=gce_cr,
        name='autogce_img',
        operatingsystem=default_os,
        username=vm_user,
        uuid=gce_template,
    ).create()
    # Cloud-Init Image
    target_sat.api.Image(
        architecture=default_architecture,
        compute_resource=gce_cr,
        name='autogce_img_cinit',
        operatingsystem=default_os,
        username=vm_user,
        uuid=gce_cloudinit_template,
        user_data=True,
    ).create()
    return gce_cr


@pytest.fixture(scope='module')
def module_gce_finishimg(
    session_target_sat,
    default_architecture,
    module_gce_compute,
    session_default_os,
    gce_latest_rhel_uuid,
):
    """Creates finish image on GCE Compute Resource"""
    finish_image = session_target_sat.api.Image(
        architecture=default_architecture,
        compute_resource=module_gce_compute,
        name=gen_string('alpha'),
        operatingsystem=session_default_os,
        username=gen_string('alpha'),
        uuid=gce_latest_rhel_uuid,
    ).create()
    return finish_image


@pytest.fixture
def gce_hostgroup(
    module_org,
    smart_proxy_location,
    default_partition_table,
    default_architecture,
    default_os,
    gce_domain,
    gce_resource_with_image,
    module_lce,
    module_cv_repo,
    target_sat,
):
    return target_sat.api.HostGroup(
        architecture=default_architecture,
        compute_resource=gce_resource_with_image,
        domain=gce_domain,
        lifecycle_environment=module_lce,
        content_view=module_cv_repo,
        location=[smart_proxy_location],
        operatingsystem=default_os,
        organization=[module_org],
        ptable=default_partition_table,
    ).create()


@pytest.fixture
def remove_vm_on_delete(target_sat, setting_update):
    setting_update.value = 'true'
    setting_update.update({'value'})
    assert (
        target_sat.api.Setting().search(query={'search': 'name=destroy_vm_on_host_delete'})[0].value
    )
    yield
