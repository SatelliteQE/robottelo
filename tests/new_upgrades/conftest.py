"""
This module is intended to be used for upgrade tests that have a single run stage.
"""

import json
from tempfile import mkstemp

from box import Box
from broker import Broker
from broker.exceptions import ProviderError
import pytest
from wrapanapi.systems.google import GoogleCloudSystem

from robottelo.config import settings
from robottelo.constants import (
    GCE_RHEL_CLOUD_PROJECTS,
    GCE_TARGET_RHEL_IMAGE_NAME,
)
from robottelo.exceptions import GCECertNotFoundError, SatelliteHostError
from robottelo.hosts import Capsule, Satellite
from robottelo.logging import logger
from robottelo.utils.shared_resource import SharedResource


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    markers = [
        "upgrade: Upgrade tests that use SharedResource.",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def shared_checkout(shared_name):
    Satellite(hostname="blank")._swap_nailgun(settings.upgrade.from_version)
    broker_instance = Broker(
        workflow=settings.server.deploy_workflows.product,
        deploy_sat_version=settings.upgrade.from_version,
        deploy_network_type=settings.server.network_type,
        host_class=Satellite,
        upgrade_group=f"{shared_name}_shared_checkout",
    )
    with SharedResource(
        resource_name=f"{shared_name}_sat_checkout",
        action=broker_instance.checkout,
        action_validator=lambda result: isinstance(result, Satellite),
    ) as sat_checkout:
        sat_checkout.ready()
        sat_instance = broker_instance.from_inventory(
            filter=f'@inv._broker_args.upgrade_group == "{shared_name}_shared_checkout" |'
            '@inv._broker_args.workflow == "deploy-satellite"'
        )
    return sat_instance[-1]


def shared_cap_checkout(shared_name):
    broker_instance = Broker(
        workflow=settings.capsule.deploy_workflows.product,
        deploy_sat_version=settings.upgrade.from_version,
        deploy_network_type=settings.capsule.network_type,
        host_class=Capsule,
        upgrade_group=f'{shared_name}_shared_checkout',
    )
    with SharedResource(
        resource_name=f'{shared_name}_cap_checkout',
        action=broker_instance.checkout,
        action_validator=lambda result: isinstance(result, Capsule),
    ) as cap_checkout:
        cap_checkout.ready()
        cap_instance = broker_instance.from_inventory(
            filter=f'@inv._broker_args.upgrade_group == "{shared_name}_shared_checkout" |'
            '@inv._broker_args.workflow == "deploy-capsule"'
        )
    return cap_instance[-1]


def shared_checkin(host_instance):
    host_instance.teardown()
    with SharedResource(
        resource_name=f"{host_instance.hostname}_checkin",
        action=Broker(hosts=[host_instance]).checkin,
    ) as host_checkin:
        logger.debug(f'Running host_checkin.ready() for {host_instance.hostname}')
        host_checkin.ready()


@pytest.fixture(scope='session')
def upgrade_action():
    def _upgrade_action(target_sat):

        result = Broker(
            job_template=settings.upgrade.satellite_upgrade_job_template,
            target_vm=target_sat.name,
            sat_version=settings.upgrade.to_version,
            upgrade_path="ystream",
            tower_inventory=target_sat.tower_inventory,
        ).execute()

        # Broker catches ProviderError and returns it instead of raising.
        # We need to re-raise so that the error propagates correctly.
        if isinstance(result, ProviderError):
            # extract the message from Broker
            broker_msg = getattr(result, 'message', str(result))
            raise SatelliteHostError(f"Satellite upgrade job failed:\n{broker_msg}") from result

        return result

    return _upgrade_action


@pytest.fixture
def shared_satellite(request):
    """Fixture for shared Satellite deployment in upgrade tests.

    Use with @pytest.mark.upgrade(arg)
    The shared resource name will be f"{arg}_upgrade".
    """
    mark = request.node.get_closest_marker("upgrade")
    shared_name = f"{mark.args[0]}_upgrade"

    sat_instance = shared_checkout(shared_name)

    if mark.kwargs.get("use_cdn"):
        sat_instance.register_to_cdn()

    with SharedResource(
        f"{shared_name}_tests_satellite", shared_checkin, host_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def shared_capsule(request):
    """Fixture for shared Capsule deployment in upgrade tests.

    Use with @pytest.mark.upgrade(arg)
    The shared resource name will be f"{arg}_upgrade".
    """
    mark = request.node.get_closest_marker("upgrade")
    shared_name = f"{mark.args[0]}_upgrade"

    cap_instance = shared_cap_checkout(shared_name)

    with SharedResource(
        f"{shared_name}_tests_capsule", shared_checkin, host_instance=cap_instance
    ) as test_duration:
        yield cap_instance
        test_duration.ready()


@pytest.fixture
def integrated_sat_cap(shared_satellite, shared_capsule):
    """Return a Satellite and Capsule that have been set up"""
    setup_data = Box(
        {
            "satellite": None,
            "capsule": None,
            "cap_smart_proxy": None,
        }
    )
    with SharedResource(
        "capsule_setup",
        action=shared_capsule.capsule_setup,
        sat_host=shared_satellite,
        release=shared_capsule.version,
    ) as cap_setup:
        cap_setup.ready()
    cap_smart_proxy = shared_satellite.api.SmartProxy().search(
        query={'search': f'name = {shared_capsule.hostname}'}
    )[0]
    cap_smart_proxy.organization = []
    setup_data.satellite = shared_satellite
    setup_data.capsule = shared_capsule
    setup_data.cap_smart_proxy = cap_smart_proxy
    return setup_data


@pytest.fixture
def puppet_upgrade_shared_satellite(shared_satellite):
    sat_instance = shared_satellite
    with SharedResource(
        "puppet_upgrade_enable_puppet",
        action=sat_instance.enable_puppet_satellite,
        action_is_recoverable=True,
    ) as enable_puppet:
        enable_puppet.ready()
        yield sat_instance


@pytest.fixture
def puppet_upgrade_integrated_sat_cap(puppet_upgrade_shared_satellite, shared_capsule):
    """Return a Satellite and Capsule that have been set up"""
    setup_data = Box(
        {
            "satellite": None,
            "capsule": None,
        }
    )
    with (
        SharedResource(
            "capsule_setup",
            action=shared_capsule.capsule_setup,
            sat_host=puppet_upgrade_shared_satellite,
            release=shared_capsule.version,
        ) as cap_setup,
        SharedResource(
            "puppet_upgrade_enable_puppet_capsule",
            action=shared_capsule.enable_puppet_capsule,
            action_is_recoverable=True,
            satellite=puppet_upgrade_shared_satellite,
        ) as enable_puppet,
    ):
        cap_setup.ready()
        enable_puppet.ready()
    setup_data.satellite = puppet_upgrade_shared_satellite
    setup_data.capsule = shared_capsule
    return setup_data


# GCE Provisioning Fixtures


@pytest.fixture
def shared_googleclient(shared_gce_cert):
    gceclient = GoogleCloudSystem(
        project=shared_gce_cert['project_id'],
        zone=settings.gce.zone,
        file_path=shared_gce_cert['local_path'],
        file_type='json',
    )
    yield gceclient
    gceclient.disconnect()


@pytest.fixture
def shared_gce_domain(sat_gce_org, sat_gce_loc, gce_cert, sat_gce):
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


@pytest.fixture
def shared_gce_latest_rhel_uuid(shared_googleclient):
    templates = shared_googleclient.find_templates(
        include_public=True,
        public_projects=GCE_RHEL_CLOUD_PROJECTS,
        filter_expr=f'name:{GCE_TARGET_RHEL_IMAGE_NAME}*',
    )
    latest_template_name = max(tpl.name for tpl in templates)
    return next(tpl for tpl in templates if tpl.name == latest_template_name).uuid


@pytest.fixture
def shared_gce_cert(puppet_upgrade_shared_satellite):
    _, gce_cert_file = mkstemp(suffix='.json')
    cert = json.loads(settings.gce.cert)
    cert['local_path'] = gce_cert_file
    with open(gce_cert_file, 'w') as f:
        json.dump(cert, f)
    puppet_upgrade_shared_satellite.put(gce_cert_file, settings.gce.cert_path)
    if puppet_upgrade_shared_satellite.execute(f'[ -f {settings.gce.cert_path} ]').status != 0:
        raise GCECertNotFoundError(
            f"The GCE certificate in path {settings.gce.cert_path} is not found in satellite."
        )
    return cert
