"""Fixtures specific to or relating to pytest's xdist plugin"""
import logging
import random

import pytest
from broker import helpers as broker_helpers
from broker.broker import VMBroker
from broker.exceptions import BrokerError
from xdist import get_xdist_worker_id

import robottelo
from pytest_fixtures.broker import satellite_factory
from robottelo.config import settings

logger = logging.getLogger('robottelo')


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Attempt to align a Satellite to the current xdist worker

    Sets settings.server.hostname in the settings cache, since that's what the framework resolves
    """
    cache_proxy = robottelo.config.settings_proxy._cache  # noqa
    # clear any hostname that may have been previously set
    cache_proxy['server.hostname'] = on_demand_sat = None

    worker_id = get_xdist_worker_id(session)
    worker_pos = 0 if worker_id == 'master' else int(worker_id.replace('gw', ''))

    # attempt to add potential satellites from the broker inventory file
    if settings.server.inventory_filter:
        settings.server.hostnames  # need to prime the cache
        hosts = VMBroker().from_inventory(filter=settings.server.inventory_filter)
        # update the cache_proxy for server.hostnames in case its empty
        cache_proxy['server.hostnames'] = cache_proxy['server.hostnames'] or []
        cache_proxy['server.hostnames'].extend([host.hostname for host in hosts])

    # attempt to align a worker to a satellite
    if settings.server.xdist_behavior == 'run-on-one' and settings.server.hostnames:
        target_satellite_fqdn = settings.server.hostnames[0]
    elif settings.server.hostnames and worker_pos < len(settings.server.hostnames):
        target_satellite_fqdn = settings.server.hostnames[worker_pos]
    elif settings.server.xdist_behavior == 'balance' and settings.server.hostnames:
        target_satellite_fqdn = random.choice(settings.server.hostnames)
    # get current satellite information
    elif settings.server.xdist_behavior == "on-demand":
        on_demand_sat = satellite_factory()
        if on_demand_sat.hostname:
            session.config.cache.set('on_demand_sat', on_demand_sat.hostname)
            target_satellite_fqdn = on_demand_sat.hostname
        # if no satellite was received, fallback to balance
        if not settings.server.hostname:
            target_satellite_fqdn = random.choice(settings.server.hostnames)
    cache_proxy['server.hostname'] = target_satellite_fqdn
    logger.info(f"xdist worker {worker_id} " f"was assigned hostname {settings.server.hostname}")
    settings.configure_airgun()
    settings.configure_nailgun()


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    # TODO store the deployed sat in the session so we can check it in here.
    stored_session_hostname = session.config.cache.get('on_demand_sat')
    if stored_session_hostname and settings.server.auto_checkin:
        logger.info(
            'Stored on-demand host found with auto_checkin set, '
            f'checking in {stored_session_hostname}'
        )
        try:
            inventory = broker_helpers.load_inventory(filter=f'hostname={stored_session_hostname}')
            VMBroker().reconstruct_host(inventory[0]).checkin()
        except IndexError:
            logger.exception(
                f'Stored on-demand hostname {stored_session_hostname} '
                'not found in inventory, cannot check in'
            )
        except BrokerError:
            logger.exception(
                f'Stored on-demand host {stored_session_hostname} encountered an'
                'exception on checkin'
            )
