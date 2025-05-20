"""
This module is intended to be used for upgrade tests that have a single run stage.
"""

import datetime
import os

from box import Box
from broker import Broker
import pytest

from robottelo.config import settings
from robottelo.hosts import Capsule, Satellite
from robottelo.utils.shared_resource import SharedResource

pre_upgrade_failed_tests = []


PRE_UPGRADE_TESTS_FILE_OPTION = 'pre_upgrade_tests_file'
PRE_UPGRADE_TESTS_FILE_PATH = '/var/tmp/robottelo_pre_upgrade_failed_tests.json'
PRE_UPGRADE = False
POST_UPGRADE = False
PRE_UPGRADE_MARK = 'pre_upgrade'
POST_UPGRADE_MARK = 'post_upgrade'
TEST_NODE_ID_NAME = '__pytest_node_id'


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
        "content_upgrades: Upgrade tests that run under .",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def shared_checkout(shared_name):
    Satellite(hostname="blank")._swap_nailgun(f"{settings.UPGRADE.FROM_VERSION}.z")
    bx_inst = Broker(
        workflow=settings.SERVER.deploy_workflows.product,
        deploy_sat_version=settings.UPGRADE.FROM_VERSION,
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
        "content_upgrade_tests",
        shared_checkin,
        sat_instance=sat_instance,
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
        "hostgroup_upgrade_tests",
        shared_checkin,
        sat_instance=sat_instance,
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
        "fdi_upgrade_tests",
        shared_checkin,
        sat_instance=sat_instance,
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


@pytest.fixture(scope='session')
def capsule_upgrade_shared_satellite():
    """Mark tests using this fixture with pytest.mark.capsule_upgrades."""
    sat_instance = shared_checkout("capsule_upgrade")
    with SharedResource(
        "capsule_upgrade_tests_satellite", shared_checkin, sat_instance=sat_instance
    ) as test_duration:
        yield sat_instance
        test_duration.ready()


@pytest.fixture(scope='session')
def capsule_upgrade_shared_capsule():
    """Mark tests using this fixture with pytest.mark.capsule_upgrades."""
    cap_instance = shared_cap_checkout("capsule_upgrade")
    with SharedResource(
        "capsule_upgrade_tests_capsule", shared_checkin, sat_instance=cap_instance
    ) as test_duration:
        yield cap_instance
        test_duration.ready()


@pytest.fixture(scope='session')
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
