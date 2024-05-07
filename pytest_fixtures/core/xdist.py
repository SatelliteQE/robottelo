"""Fixtures specific to or relating to pytest's xdist plugin"""

import random

from broker import Broker
import pytest

from robottelo.config import configure_airgun, configure_nailgun, settings
from robottelo.hosts import Satellite
from robottelo.logging import logger


@pytest.fixture(scope="session", autouse=True)
def align_to_satellite(request, worker_id, satellite_factory):
    """Attempt to align a Satellite to the current xdist worker"""
    if 'build_sanity' in request.config.option.markexpr:
        yield
        if settings.server.hostname:
            sanity_sat = Satellite(settings.server.hostname)
            sanity_sat.unregister()
            broker_sat = Satellite.get_host_by_hostname(sanity_sat.hostname)
            Broker(hosts=[broker_sat]).checkin()
    else:
        # clear any hostname that may have been previously set
        settings.set("server.hostname", None)
        on_demand_sat = None

        worker_pos = 0 if worker_id in ["master", "local"] else int(worker_id.replace("gw", ""))

        # attempt to add potential satellites from the broker inventory file
        if settings.server.inventory_filter:
            logger.info(
                f'{worker_id=}: Attempting to add Satellite hosts using inventory filter: '
                f'{settings.server.inventory_filter}'
            )
            hosts = Satellite.get_hosts_from_inventory(filter=settings.server.inventory_filter)
            settings.server.hostnames += [host.hostname for host in hosts]

        logger.debug(
            f'{worker_id=}: {settings.server.xdist_behavior=}, '
            f'{settings.server.hostnames=}, {settings.server.auto_checkin=}'
        )
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
                logger.info(
                    f'{worker_id=}: No Satellite hostnames were available, '
                    'falling back to balance behavior'
                )
                settings.set("server.hostname", random.choice(settings.server.hostnames))
        if settings.server.hostname:
            logger.info(f'{worker_id=}: Worker was assigned hostname {settings.server.hostname}')
            configure_airgun()
            configure_nailgun()
        yield
        if on_demand_sat and settings.server.auto_checkin:
            logger.info(
                f'{worker_id=}: Checking in on-demand Satellite ' f'{on_demand_sat.hostname}'
            )
            on_demand_sat.teardown()
            Broker(hosts=[on_demand_sat]).checkin()
