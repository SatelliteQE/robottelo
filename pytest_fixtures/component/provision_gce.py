# Google Cloud Engine Entities
import json
from tempfile import mkstemp

import pytest
from fauxfactory import gen_string
from nailgun import entities
from wrapanapi.systems.google import GoogleCloudSystem

from robottelo.config import settings
from robottelo.constants import DEFAULT_PTABLE
from robottelo.errors import GCECertNotFoundError


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


@pytest.fixture(scope='module')
def module_gce_compute(module_org, module_location, gce_cert):
    gce_cr = entities.GCEComputeResource(
        name=gen_string('alphanumeric'),
        provider='GCE',
        email=gce_cert['client_email'],
        key_path=settings.gce.cert_path,
        project=gce_cert['project_id'],
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
        email=gce_cert_puppet['client_email'],
        key_path=settings.gce.cert_path,
        project=gce_cert_puppet['project_id'],
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
