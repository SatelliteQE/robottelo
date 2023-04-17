import pytest
from broker import Broker

from robottelo.hosts import Capsule
from robottelo.logging import logger


@pytest.fixture(scope="function")
def dependent_scenario_name(request):
    """
    This fixture is used to collect the dependent test case name.
    """
    depend_test_name = [
        mark.kwargs['depend_on'].__name__
        for mark in request.node.own_markers
        if 'depend_on' in mark.kwargs
    ][0]
    yield depend_test_name


@pytest.fixture(scope="session")
def pre_configured_capsule(worker_id, session_target_sat):
    """
    This fixture returns the Capsule object matching the pre-configured capsule

    This fixture assumes that the Capsule is already integrated with Satellite and
    the Capsule host is present in the broker inventory.
    """
    inventory = {h.hostname for h in Broker().from_inventory()}
    capsules = {h.name for h in session_target_sat.api.Capsule().search()}
    logger.debug(
        f'Hosts in the inventory: {inventory}. Capsules attached to Satellite: {capsules}.'
    )
    # do an intersection of both sets to just select those hosts that we have in the capsules
    # from that intersection take the Capsule that is not Satellite and return it
    intersect = inventory.intersection(capsules)
    intersect.discard(session_target_sat.hostname)
    logger.debug(f'Capsules found: {intersect}')
    assert len(intersect) == 1, "More than one Capsule found in the inventory"
    target_capsule = intersect.pop()
    hosts = Broker(host_class=Capsule).from_inventory(filter=f'hostname={target_capsule}')
    # hosts = Broker(host_class=Capsule).from_inventory(
    #     filter=f'@inv.hostname == "{target_capsule}"'
    # )  # broker 0.3.0 syntax
    logger.info(f'xdist worker {worker_id} was assigned pre-configured Capsule {target_capsule}')
    return hosts[0]
