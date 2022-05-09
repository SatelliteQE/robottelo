# Google Cloud Engine Entities
import json
from tempfile import mkstemp

import pytest
from fauxfactory import gen_string
from nailgun import entities
from wrapanapi.systems.google import GoogleCloudSystem

from robottelo.config import settings
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
