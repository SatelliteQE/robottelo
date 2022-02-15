import pytest
from broker import VMBroker
from wait_for import wait_for

from robottelo.config import settings
from robottelo.hosts import Capsule
from robottelo.hosts import Satellite


def _resolve_deploy_args(args_dict):
    for key, val in args_dict.items():
        if isinstance(val, str) and val.startswith('this.'):
            # Args transformed into small letters and existing capital args removed
            args_dict[key.lower()] = settings.get(args_dict.pop(key).replace('this.', ''))


@pytest.fixture(scope='session')
def default_sat(align_to_satellite):
    """Returns a Satellite object for settings.server.hostname"""
    if settings.server.hostname:
        return Satellite()


@pytest.fixture(scope='session')
def satellite_factory():
    if settings.server.get('deploy_arguments'):
        _resolve_deploy_args(settings.server.deploy_arguments)

    def factory(retry_limit=3, delay=300, workflow=None, **broker_args):
        if settings.server.deploy_arguments:
            broker_args.update(settings.server.deploy_arguments)
        vmb = VMBroker(
            host_classes={'host': Satellite},
            workflow=workflow or settings.server.deploy_workflow,
            **broker_args,
        )
        timeout = (1200 + delay) * retry_limit
        sat = wait_for(vmb.checkout, timeout=timeout, delay=delay, fail_condition=[])
        return sat.out

    return factory


@pytest.fixture(scope='session')
def capsule_factory():
    if settings.capsule.get('deploy_arguments'):
        _resolve_deploy_args(settings.capsule.deploy_arguments)

    def factory(retry_limit=3, delay=300, workflow=None, **broker_args):
        if settings.capsule.deploy_arguments:
            broker_args.update(settings.capsule.deploy_arguments)
        vmb = VMBroker(
            host_classes={'host': Capsule},
            workflow=workflow or settings.capsule.deploy_workflow,
            **broker_args,
        )
        timeout = (1200 + delay) * retry_limit
        cap = wait_for(vmb.checkout, timeout=timeout, delay=delay, fail_condition=[])
        return cap.out

    return factory


@pytest.fixture
def satellite_host(satellite_factory):
    """A fixture that provides a Satellite based on config settings"""
    new_sat = satellite_factory()
    yield new_sat
    VMBroker(hosts=[new_sat]).checkin()


@pytest.fixture(scope='module')
def module_satellite_host(satellite_factory):
    """A fixture that provides a Satellite based on config settings"""
    new_sat = satellite_factory()
    yield new_sat
    VMBroker(hosts=[new_sat]).checkin()


@pytest.fixture(scope='session')
def session_satellite_host(satellite_factory):
    """A fixture that provides a Satellite based on config settings"""
    new_sat = satellite_factory()
    yield new_sat
    VMBroker(hosts=[new_sat]).checkin()


@pytest.fixture
def capsule_host(capsule_factory):
    """A fixture that provides a Capsule based on config settings"""
    new_cap = capsule_factory()
    yield new_cap
    VMBroker(hosts=[new_cap]).checkin()


@pytest.fixture
def capsule_configured(capsule_host, default_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    capsule_host.capsule_setup(sat_host=default_sat)
    yield capsule_host


@pytest.fixture
def destructive_sat(satellite_host):
    """Destructive tests require changing settings.server.hostname for now"""
    with satellite_host as sat:
        yield sat


@pytest.fixture(scope='module')
def module_destructive_sat(module_satellite_host):
    """Destructive tests require changing settings.server.hostname for now"""
    with module_satellite_host as sat:
        yield sat


@pytest.fixture
def destructive_caps(capsule_host, destructive_sat):
    """Configure the capsule instance with the destructive satellite"""
    capsule_host.capsule_setup(sat_host=destructive_sat)
    yield capsule_host
