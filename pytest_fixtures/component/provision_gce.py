# Google Cloud Engine Entities
import json
from tempfile import mkstemp

import pytest
from fauxfactory import gen_string
from wrapanapi.systems.google import GoogleCloudSystem

from robottelo.config import settings
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.exceptions import GCECertNotFoundError


@pytest.fixture(scope='session')
def sat_gce(request, session_puppet_enabled_sat, session_target_sat):
    hosts = {'sat': session_target_sat, 'puppet_sat': session_puppet_enabled_sat}
    yield hosts[getattr(request, 'param', 'sat')]


@pytest.fixture(scope='module')
def sat_gce_org(sat_gce):
    yield sat_gce.api.Organization().create()


@pytest.fixture(scope='module')
def sat_gce_loc(sat_gce):
    yield sat_gce.api.Location().create()


@pytest.fixture(scope='module')
def sat_gce_domain(sat_gce, sat_gce_loc, sat_gce_org):
    yield sat_gce.api.Domain(location=[sat_gce_loc], organization=[sat_gce_org]).create()


@pytest.fixture(scope='module')
def sat_gce_default_os(sat_gce):
    """Default OS on the Satellite"""
    search_string = 'name="RedHat" AND (major="6" OR major="7" OR major="8" OR major="9")'
    return sat_gce.api.OperatingSystem().search(query={'search': search_string})[0].read()


@pytest.fixture(scope='session')
def sat_gce_default_partition_table(sat_gce):
    # Get the Partition table ID
    return sat_gce.api.PartitionTable().search(query={'search': f'name="{DEFAULT_PTABLE}"'})[0]


@pytest.fixture(scope='module')
def sat_gce_default_architecture(sat_gce):
    arch = (
        sat_gce.api.Architecture()
        .search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0]
        .read()
    )
    return arch


@pytest.fixture(scope='session')
def gce_cert(sat_gce):
    _, gce_cert_file = mkstemp(suffix='.json')
    cert = json.loads(settings.gce.cert)
    cert['local_path'] = gce_cert_file
    with open(gce_cert_file, 'w') as f:
        json.dump(cert, f)
    sat_gce.put(gce_cert_file, settings.gce.cert_path)
    if sat_gce.execute(f'[ -f {settings.gce.cert_path} ]').status != 0:
        raise GCECertNotFoundError(
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
def module_gce_compute(sat_gce, sat_gce_org, sat_gce_loc, gce_cert):
    gce_cr = sat_gce.api.GCEComputeResource(
        name=gen_string('alphanumeric'),
        provider='GCE',
        key_path=settings.gce.cert_path,
        zone=settings.gce.zone,
        organization=[sat_gce_org],
        location=[sat_gce_loc],
    ).create()
    return gce_cr


@pytest.fixture(scope='module')
def gce_template(googleclient):
    max_rhel7_template = max(
        img.name for img in googleclient.list_templates(True) if str(img.name).startswith('rhel-7')
    )
    return googleclient.get_template(max_rhel7_template, project='rhel-cloud').uuid


@pytest.fixture(scope='module')
def gce_cloudinit_template(googleclient, gce_cert):
    return googleclient.get_template('customcinit', project=gce_cert['project_id']).uuid


@pytest.fixture(scope='module')
def gce_domain(sat_gce_org, sat_gce_loc, gce_cert, sat_gce):
    domain_name = f'{settings.gce.zone}.c.{gce_cert["project_id"]}.internal'
    domain = sat_gce.api.Domain().search(query={'search': f'name={domain_name}'})
    if domain:
        domain = domain[0]
        domain.organization = [sat_gce_org]
        domain.location = [sat_gce_loc]
        domain.update(['organization', 'location'])
    if not domain:
        domain = sat_gce.api.Domain(
            name=domain_name, location=[sat_gce_loc], organization=[sat_gce_org]
        ).create()
    return domain


@pytest.fixture(scope='module')
def gce_resource_with_image(
    gce_template,
    gce_cloudinit_template,
    gce_cert,
    sat_gce_default_architecture,
    sat_gce_default_os,
    sat_gce_loc,
    sat_gce_org,
    sat_gce,
):
    json_key = json.dumps(gce_cert, indent=2)
    with sat_gce.ui_session() as session:
        session.organization.select(org_name=sat_gce_org.name)
        session.location.select(loc_name=sat_gce_loc.name)
        cr_name = gen_string('alpha')
        vm_user = gen_string('alpha')
        session.computeresource.create(
            {
                'name': cr_name,
                'provider': FOREMAN_PROVIDERS['google'],
                'provider_content.json_key': json_key,
                'provider_content.zone.value': settings.gce.zone,
                'organizations.resources.assigned': [sat_gce_org.name],
                'locations.resources.assigned': [sat_gce_loc.name],
            }
        )
    gce_cr = sat_gce.api.AbstractComputeResource().search(query={'search': f'name={cr_name}'})[0]
    # Finish Image
    sat_gce.api.Image(
        architecture=sat_gce_default_architecture,
        compute_resource=gce_cr,
        name='autogce_img',
        operatingsystem=sat_gce_default_os,
        username=vm_user,
        uuid=gce_template,
    ).create()
    # Cloud-Init Image
    sat_gce.api.Image(
        architecture=sat_gce_default_architecture,
        compute_resource=gce_cr,
        name='autogce_img_cinit',
        operatingsystem=sat_gce_default_os,
        username=vm_user,
        uuid=gce_cloudinit_template,
        user_data=True,
    ).create()
    return gce_cr


@pytest.fixture(scope='module')
def gce_hostgroup(
    sat_gce,
    sat_gce_default_architecture,
    module_gce_compute,
    sat_gce_domain,
    sat_gce_loc,
    sat_gce_default_os,
    sat_gce_org,
    sat_gce_default_partition_table,
    googleclient,
):
    """Sets Hostgroup for GCE Host Provisioning"""
    hgroup = sat_gce.api.HostGroup(
        architecture=sat_gce_default_architecture,
        compute_resource=module_gce_compute,
        domain=sat_gce_domain,
        location=[sat_gce_loc],
        root_pass=gen_string('alphanumeric'),
        operatingsystem=sat_gce_default_os,
        organization=[sat_gce_org],
        ptable=sat_gce_default_partition_table,
    ).create()
    return hgroup


@pytest.fixture(scope='module')
def gce_hostgroup_resource_image(
    sat_gce_org,
    sat_gce_loc,
    sat_gce_default_partition_table,
    sat_gce_default_architecture,
    sat_gce_default_os,
    gce_domain,
    gce_resource_with_image,
    sat_gce,
):
    return sat_gce.api.HostGroup(
        architecture=sat_gce_default_architecture,
        compute_resource=gce_resource_with_image,
        domain=gce_domain,
        location=[sat_gce_loc],
        operatingsystem=sat_gce_default_os,
        organization=[sat_gce_org],
        ptable=sat_gce_default_partition_table,
    ).create()


@pytest.fixture(scope='module')
def module_gce_cloudimg(
    sat_gce_default_architecture,
    module_gce_compute,
    sat_gce_default_os,
    gce_custom_cloudinit_uuid,
    sat_gce,
):
    """Creates cloudinit image on GCE Compute Resource"""
    cloud_image = sat_gce.api.Image(
        architecture=sat_gce_default_architecture,
        compute_resource=module_gce_compute,
        name=gen_string('alpha'),
        operatingsystem=sat_gce_default_os,
        username=gen_string('alpha'),
        uuid=gce_custom_cloudinit_uuid,
        user_data=True,
    ).create()
    return cloud_image


@pytest.fixture(scope='module')
def module_gce_finishimg(
    sat_gce_default_architecture,
    module_gce_compute,
    sat_gce_default_os,
    gce_latest_rhel_uuid,
    sat_gce,
):
    """Creates finish image on GCE Compute Resource"""
    finish_image = sat_gce.api.Image(
        architecture=sat_gce_default_architecture,
        compute_resource=module_gce_compute,
        name=gen_string('alpha'),
        operatingsystem=sat_gce_default_os,
        username=gen_string('alpha'),
        uuid=gce_latest_rhel_uuid,
    ).create()
    return finish_image


@pytest.fixture()
def gce_setting_update(sat_gce):
    sat_gce.update_setting('destroy_vm_on_host_delete', True)
    yield
    sat_gce.update_setting('destroy_vm_on_host_delete', False)
