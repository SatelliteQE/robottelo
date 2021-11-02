"""Fixtures specific to or relating to pytest's xdist plugin"""
import random

import pytest
from broker import VMBroker

from robottelo.config import configure_airgun
from robottelo.config import configure_nailgun
from robottelo.config import settings
from robottelo.hosts import Satellite
from robottelo.logging import logger


@pytest.fixture(scope="session", autouse=True)
def worker_default_host(worker_id):
    """Define the session scoped default satellite hostname for a worker

    Accounts for settings.server.xdist_behavior

    Basis for the 'default_sat' fixture with no modifications like destructive
    """
    # clear any hostname that may have been previously set
    settings.set("server.hostname", None)
    on_demand_sat = None

    if worker_id in ['master', 'local']:
        worker_pos = 0
    else:
        worker_pos = int(worker_id.replace('gw', ''))

    # attempt to add potential satellites from the broker inventory file
    if settings.server.inventory_filter:
        hosts = VMBroker().from_inventory(filter=settings.server.inventory_filter)
        settings.server.hostnames += [host.hostname for host in hosts]

    # attempt to align a worker to a satellite
    # TODO don't set settings.server.hostname, just return it (helpers refactor)
    if settings.server.xdist_behavior == 'run-on-one' and settings.server.hostnames:
        settings.set("server.hostname", settings.server.hostnames[0])
    elif settings.server.hostnames and worker_pos < len(settings.server.hostnames):
        settings.set("server.hostname", settings.server.hostnames[worker_pos])
    elif settings.server.xdist_behavior == 'balance' and settings.server.hostnames:
        settings.set("server.hostname", random.choice(settings.server.hostnames))
    # get current satellite information
    elif settings.server.xdist_behavior == 'on-demand':
        on_demand_sat = Satellite.factory()
        if on_demand_sat.hostname:
            settings.set("server.hostname", on_demand_sat.hostname)
        else:
            pytest.fail('Unable to deploy a Satellite instance on-demand, check broker logs')

    logger.info(f'xdist worker {worker_id} was assigned hostname {settings.server.hostname}')
    target_sat = on_demand_sat or Satellite(hostname=settings.server.hostname)
    configure_airgun(host=target_sat)
    configure_nailgun(host=target_sat)
    yield target_sat
    if on_demand_sat and settings.server.auto_checkin:
        VMBroker(hosts=[on_demand_sat]).checkin()


@pytest.fixture(scope="function", autouse=True)
def align_to_satellite(worker_default_host, request):
    """Identify whether the default satellite should be used for the requesting test case

    Test cases marked destructive should have a new satellite deployed on demand as a target
    """
    target_sat = worker_default_host
    replaced = False
    if request.node.get_closest_marker('destructive') is not None:
        if settings.server.xdist_behavior in ['run-on-one', 'balance']:
            pytest.skip('destructive test requires on-demand settings.server.xdist_behavior')
        logger.info(f'Deploying Satellite instance for destructive test: {request.node_id}')
        target_sat = Satellite.factory()
        logger.info(f'Destructive Satellite instance deployed: {target_sat.hostname}')
        replaced = True
        configure_airgun(host=target_sat)
        configure_nailgun(host=target_sat)
    yield target_sat
    if replaced:
        configure_airgun(host=worker_default_host)
        configure_nailgun(host=worker_default_host)
