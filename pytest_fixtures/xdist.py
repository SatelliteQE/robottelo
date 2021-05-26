"""Fixtures specific to or relating to pytest's xdist plugin"""
import random

import pytest
from broker import VMBroker

import robottelo
from robottelo.config import settings
from robottelo.logging import logger


@pytest.fixture(scope="session", autouse=True)
def align_to_satellite(worker_id, satellite_factory):
    """Attempt to align a Satellite to the current xdist worker"""
    cache_proxy = robottelo.config.settings_proxy._cache
    # clear any hostname that may have been previously set
    cache_proxy['server.hostname'] = on_demand_sat = None

    if worker_id in ['master', 'local']:
        worker_pos = 0
    else:
        worker_pos = int(worker_id.replace('gw', ''))

    # attempt to add potential satellites from the broker inventory file
    if settings.server.inventory_filter:
        settings.server.hostnames  # need to prime the cache
        hosts = VMBroker().from_inventory(filter=settings.server.inventory_filter)
        # update the cache_proxy for server.hostnames in case its empty
        cache_proxy['server.hostnames'] = cache_proxy['server.hostnames'] or []
        cache_proxy['server.hostnames'].extend([host.hostname for host in hosts])

    # attempt to align a worker to a satellite
    if settings.server.xdist_behavior == 'run-on-one' and settings.server.hostnames:
        cache_proxy['server.hostname'] = settings.server.hostnames[0]
    elif settings.server.hostnames and worker_pos < len(settings.server.hostnames):
        cache_proxy['server.hostname'] = settings.server.hostnames[worker_pos]
    elif settings.server.xdist_behavior == 'balance' and settings.server.hostnames:
        cache_proxy['server.hostname'] = random.choice(settings.server.hostnames)
    # get current satellite information
    elif settings.server.xdist_behavior == "on-demand":
        on_demand_sat = satellite_factory()
        if on_demand_sat.hostname:
            cache_proxy['server.hostname'] = on_demand_sat.hostname
        # if no satellite was received, fallback to balance
        if not settings.server.hostname:
            cache_proxy['server.hostname'] = random.choice(settings.server.hostnames)
    logger.info(f"xdist worker {worker_id} " f"was assigned hostname {settings.server.hostname}")
    settings.configure_airgun()
    settings.configure_nailgun()
    yield
    if on_demand_sat and settings.server.auto_checkin:
        VMBroker(hosts=[on_demand_sat]).checkin()
