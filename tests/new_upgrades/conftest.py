"""
This module is intended to be used for upgrade tests that have a single run stage.
"""

import datetime
import json
import os
from tempfile import mkstemp

from box import Box
from broker import Broker
import pytest
from wrapanapi.systems.google import GoogleCloudSystem

from robottelo.config import settings
from robottelo.constants import (
    GCE_RHEL_CLOUD_PROJECTS,
    GCE_TARGET_RHEL_IMAGE_NAME,
)
from robottelo.exceptions import GCECertNotFoundError
from robottelo.hosts import Capsule, Satellite
from robottelo.utils.shared_resource import SharedResource


def log(message, level="DEBUG"):
    """Pytest has a limitation to use logging.logger from conftest.py
    so we need to emulate the logger by std-out the output
    """
    now = datetime.datetime.now()
    full_message = "{date} - conftest - {level} - {message}\n".format(
        date=now.strftime("%Y-%m-%d %H:%M:%S"), level=level, message=message
    )
    print(full_message)  # noqa
    with open('robottelo.log', 'a') as log_file:
        log_file.write(full_message)


def pytest_configure(config):
    """Register custom markers to avoid warnings."""
    markers = [
        "content_upgrades: Content upgrade tests that use SharedResource.",
        "search_upgrades: Search upgrade tests that use SharedResource.",
        "hostgroup_upgrades: Host group upgrade tests that use SharedResource.",
        "errata_upgrades: Errata upgrade tests that use SharedResource.",
        "perf_tuning_upgrades: Performance tuning upgrade tests that use SharedResource.",
        "discovery_upgrades: Discovery upgrade tests that use SharedResource.",
        "capsule_upgrades: Capsule upgrade tests that use SharedResource.",
        "puppet_upgrades: Puppet upgrade tests that use SharedResource.",
        "local_insights_upgrades: Local insights(IoP) upgrade tests that use SharedResource.",
        "hosted_insights_upgrades: Hosted insights upgrade tests that use SharedResource.",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def shared_checkout(shared_name):
    Satellite(hostname="blank")._swap_nailgun(f"{settings.UPGRADE.FROM_VERSION}.z")
    bx_inst = Broker(
        workflow=settings.SERVER.deploy_workflows.product,
        deploy_sat_version=settings.UPGRADE.FROM_VERSION,
        deploy_network_type=settings.SERVER.network_type,
        host_class=Satellite,
        upgrade_group=f"{shared_name}_shared_checkout",
    )
    with SharedResource(
        resource_name=f"{shared_name}_sat_checkout",
        action=bx_inst.checkout,
        action_validator=lambda result: isinstance(result, Satellite),
    ) as sat_checkout:
        sat_checkout.ready()
        sat_instance = bx_inst.from_inventory(
            filter=f'@inv._broker_args.upgrade_group == "{shared_name}_shared_checkout" |'
            '@inv._broker_args.workflow == "deploy-satellite"'
        )
    return sat_instance[0]


def shared_cap_checkout(shared_name):
    cap_inst = Broker(
        workflow=settings.CAPSULE.deploy_workflows.product,
        deploy_sat_version=settings.UPGRADE.FROM_VERSION,
        host_class=Capsule,
        upgrade_group=f'{shared_name}_shared_checkout',
    )
    with SharedResource(
        resource_name=f'{shared_name}_cap_checkout',
        action=cap_inst.checkout,
        action_validator=lambda result: isinstance(result, Capsule),
    ) as cap_checkout:
        cap_checkout.ready()
        cap_instance = cap_inst.from_inventory(
            filter=f'@inv._broker_args.upgrade_group == "{shared_name}_shared_checkout" |'
            '@inv._broker_args.workflow == "deploy-capsule"'
        )
    return cap_instance[0]


def shared_checkin(sat_instance):
    log(f'Running sat_instance.teardown() from worker {os.environ.get("PYTEST_XDIST_WORKER")} ')
    sat_instance.teardown()
    with SharedResource(
        resource_name=sat_instance.hostname + "_checkin",
        action=Broker(hosts=[sat_instance]).checkin,
    ) as sat_checkin:
        sat_checkin.ready()


@pytest.fixture(scope='session')
def upgrade_action():
    def _upgrade_action(target_sat):
        Broker(
            job_template=settings.UPGRADE.SATELLITE_UPGRADE_JOB_TEMPLATE,
            target_vm=target_sat.name,
            sat_version=settings.UPGRADE.TO_VERSION,
            upgrade_path="ystream",
            tower_inventory=target_sat.tower_inventory,
        ).execute()

    return _upgrade_action


@pytest.fixture
def content_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.content_upgrades."""
    sat_instance = shared_checkout("content_upgrade")
    with SharedResource(
        "content_upgrade_tests", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def search_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.search_upgrades."""
    sat_instance = shared_checkout("search_upgrade")
    with SharedResource(
        "search_upgrade_tests",
        shared_checkin,
        sat_instance=sat_instance,
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def hostgroup_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.hostgroup_upgrades."""
    sat_instance = shared_checkout("hostgroup_upgrade")
    with SharedResource(
        "hostgroup_upgrade_tests", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def usergroup_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.usergroup_upgrades."""
    sat_instance = shared_checkout("usergroup_upgrade")
    with SharedResource(
        "usergroup_upgrade_tests", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def errata_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.search_upgrades."""
    sat_instance = shared_checkout("errata_upgrade")
    with SharedResource(
        "errata_upgrade_tests",
        shared_checkin,
        sat_instance=sat_instance,
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def fdi_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.discovery_upgrades."""
    sat_instance = shared_checkout("fdi_upgrade")
    with SharedResource(
        "fdi_upgrade_tests", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def perf_tuning_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.perf_tuning_upgrades."""
    sat_instance = shared_checkout("perf_tuning_upgrade")
    with SharedResource(
        "perf_tuning_upgrade_tests", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def subscription_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.subscription_upgrades."""
    sat_instance = shared_checkout("subscription_upgrade")
    with SharedResource(
        "subscription_upgrade_tests", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def sync_plan_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.sync_plan_upgrades."""
    sat_instance = shared_checkout("sync_plan_upgrade")
    with SharedResource(
        "sync_plan_upgrade_tests", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def capsule_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.capsule_upgrades."""
    sat_instance = shared_checkout("capsule_upgrade")
    with SharedResource(
        "capsule_upgrade_tests_satellite", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def capsule_upgrade_shared_capsule():
    """Mark tests using this fixture with pytest.mark.capsule_upgrades."""
    cap_instance = shared_cap_checkout("capsule_upgrade")
    with SharedResource(
        "capsule_upgrade_tests_capsule", shared_checkin, sat_instance=cap_instance
    ) as test_duration:
        yield cap_instance
        test_duration.ready()


@pytest.fixture
def capsule_upgrade_integrated_sat_cap(
    capsule_upgrade_shared_satellite, capsule_upgrade_shared_capsule
):
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
        action=capsule_upgrade_shared_capsule.capsule_setup,
        sat_host=capsule_upgrade_shared_satellite,
    ) as cap_setup:
        cap_setup.ready()
    cap_smart_proxy = capsule_upgrade_shared_satellite.api.SmartProxy().search(
        query={'search': f'name = {capsule_upgrade_shared_capsule.hostname}'}
    )[0]
    cap_smart_proxy.organization = []
    setup_data.satellite = capsule_upgrade_shared_satellite
    setup_data.capsule = capsule_upgrade_shared_capsule
    setup_data.cap_smart_proxy = cap_smart_proxy
    return setup_data


@pytest.fixture
def puppet_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.puppet_upgrades"""
    sat_instance = shared_checkout("puppet_upgrade")
    with (
        SharedResource(
            "puppet_upgrade_enable_puppet",
            action=sat_instance.enable_puppet_satellite,
            action_is_recoverable=True,
        ) as enable_puppet,
        SharedResource(
            "puppet_upgrade_satellite",
            shared_checkin,
            sat_instance=sat_instance,
            action_is_recoverable=True,
        ) as test_duration,
    ):
        enable_puppet.ready()
        yield sat_instance
        test_duration.ready()


@pytest.fixture
def puppet_upgrade_shared_capsule():
    """Mark tests using this fixture with pytest.mark.puppet_upgrades"""
    cap_instance = shared_cap_checkout("puppet_upgrade")
    with (
        SharedResource(
            "puppet_upgrade_capsule",
            shared_checkin,
            sat_instance=cap_instance,
            action_is_recoverable=True,
        ) as test_duration,
    ):
        yield cap_instance
        test_duration.ready()


@pytest.fixture
def puppet_upgrade_integrated_sat_cap(
    puppet_upgrade_shared_satellite, puppet_upgrade_shared_capsule
):
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
            action=puppet_upgrade_shared_capsule.capsule_setup,
            sat_host=puppet_upgrade_shared_satellite,
        ) as cap_setup,
        SharedResource(
            "puppet_upgrade_enable_puppet_capsule",
            action=puppet_upgrade_shared_capsule.enable_puppet_capsule,
            action_is_recoverable=True,
            satellite=puppet_upgrade_shared_satellite,
        ) as enable_puppet,
    ):
        cap_setup.ready()
        enable_puppet.ready()
    setup_data.satellite = puppet_upgrade_shared_satellite
    setup_data.capsule = puppet_upgrade_shared_capsule
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


@pytest.fixture(scope='module')
def local_insights_upgrade():
    """Mark tests using this fixture with pytest.mark.local_insights_upgrades."""
    sat_instance = shared_checkout("local_insights_upgrade")
    with SharedResource(
        "local_insights_upgrade_tests", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        iop_settings = settings.rh_cloud.iop_advisor_engine
        sat_instance.configure_insights_on_prem(
            iop_settings.stage_username, iop_settings.stage_token, iop_settings.stage_registry
        )
        yield sat_instance
        test_duration.ready()


@pytest.fixture(scope='module')
def hosted_insights_upgrade():
    """Mark tests using this fixture with pytest.mark.hosted_insights_upgrades."""
    sat_instance = shared_checkout("hosted_insights_upgrade")
    with SharedResource(
        "hosted_insights_upgrade_tests", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture(scope='module')
def module_target_sat_insights(request):
    """
    A module-level fixture to provide a Satellite configured for Insights.
    By default, it returns hosted_insights_upgrade satellite instance.

    If parametrized with a false value, then it will deploy and return a Satellite with
    iop-advisor-engine (local Insights advisor) configured.
    """
    hosted_insights = getattr(request, 'param', True)
    return (
        request.getfixturevalue('hosted_insights_upgrade')
        if hosted_insights
        else request.getfixturevalue('local_insights_upgrade')
    )
