"""Fixtures specific to or relating to pytest's xdist plugin"""
import random

import pytest
from broker import Broker

from robottelo.config import configure_airgun
from robottelo.config import configure_nailgun
from robottelo.config import settings
from robottelo.logging import logger


@pytest.fixture(scope="session", autouse=True)
def align_to_satellite(worker_id, satellite_factory):
    """Attempt to align a Satellite to the current xdist worker"""
    # clear any hostname that may have been previously set
    settings.set("server.hostname", None)
    on_demand_sat = None

    if worker_id in ['master', 'local']:
        worker_pos = 0
    else:
        worker_pos = int(worker_id.replace('gw', ''))

    # attempt to add potential satellites from the broker inventory file
    if settings.server.inventory_filter:
        hosts = Broker().from_inventory(filter=settings.server.inventory_filter)
        settings.server.hostnames += [host.hostname for host in hosts]

    # attempt to align a worker to a satellite
    if settings.server.xdist_behavior == 'run-on-one' and settings.server.hostnames:
        settings.set("server.hostname", settings.server.hostnames[0])
    elif settings.server.hostnames and worker_pos < len(settings.server.hostnames):
        settings.set("server.hostname", settings.server.hostnames[worker_pos])
    elif settings.server.xdist_behavior == 'balance' and settings.server.hostnames:
        settings.set("server.hostname", random.choice(settings.server.hostnames))
    # get current satellite information
    elif settings.server.xdist_behavior == 'on-demand':
        on_demand_sat = satellite_factory()
        if on_demand_sat.hostname:
            settings.set("server.hostname", on_demand_sat.hostname)
        # if no satellite was received, fallback to balance
        if not settings.server.hostname:
            settings.set("server.hostname", random.choice(settings.server.hostnames))
    logger.info(f'xdist worker {worker_id} was assigned hostname {settings.server.hostname}')
    configure_airgun()
    configure_nailgun()
    yield
    if on_demand_sat and settings.server.auto_checkin:
        Broker(hosts=[on_demand_sat]).checkin()
