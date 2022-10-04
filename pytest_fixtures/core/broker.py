from contextlib import contextmanager

import pytest
from broker import Broker
from wait_for import wait_for

from robottelo.config import settings
from robottelo.hosts import Capsule
from robottelo.hosts import Satellite
from robottelo.logging import logger


def _resolve_deploy_args(args_dict):
    # TODO: https://github.com/rochacbruno/dynaconf/issues/690
    args_dict = args_dict.copy().to_dict()
    for key, val in args_dict.items():
        if isinstance(val, str) and val.startswith('this.'):
            # Args transformed into small letters and existing capital args removed
            args_dict[key.lower()] = settings.get(args_dict.pop(key).replace('this.', ''))
    return args_dict


@pytest.fixture(scope='session')
def _default_sat(align_to_satellite):
    """Returns a Satellite object for settings.server.hostname"""
    if settings.server.hostname:
        hosts = Broker(host_class=Satellite).from_inventory(
            filter=f'hostname={settings.server.hostname}'
        )
        if hosts:
            return hosts[0]
        else:
            return Satellite()


@contextmanager
def _target_sat_imp(request, _default_sat, satellite_factory):
    """This is the actual working part of the following target_sat fixtures"""
    if request.node.get_closest_marker(name='destructive'):
        new_sat = satellite_factory()
        yield new_sat
        new_sat.teardown()
        Broker(hosts=[new_sat]).checkin()
    else:
        yield _default_sat


@pytest.fixture
def target_sat(request, _default_sat, satellite_factory):
    with _target_sat_imp(request, _default_sat, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='module')
def module_target_sat(request, _default_sat, satellite_factory):
    with _target_sat_imp(request, _default_sat, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='session')
def session_target_sat(request, _default_sat, satellite_factory):
    with _target_sat_imp(request, _default_sat, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='class')
def class_target_sat(request, _default_sat, satellite_factory):
    with _target_sat_imp(request, _default_sat, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='session')
def satellite_factory():
    if settings.server.get('deploy_arguments'):
        logger.debug(f'Original deploy arguments for sat: {settings.server.deploy_arguments}')
        resolved = _resolve_deploy_args(settings.server.deploy_arguments)
        settings.set('server.deploy_arguments', resolved)
        logger.debug(f'Resolved deploy arguments for sat: {settings.server.deploy_arguments}')

    def factory(retry_limit=3, delay=300, workflow=None, **broker_args):
        if settings.server.deploy_arguments:
            broker_args.update(settings.server.deploy_arguments)
            logger.debug(f'Updated broker args for sat: {broker_args}')

        vmb = Broker(
            host_class=Satellite,
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
        logger.debug(f'Original deploy arguments for cap: {settings.capsule.deploy_arguments}')
        resolved = _resolve_deploy_args(settings.capsule.deploy_arguments)
        settings.set('capsule.deploy_arguments', resolved)
        logger.debug(f'Resolved deploy arguments for cap: {settings.capsule.deploy_arguments}')

    def factory(retry_limit=3, delay=300, workflow=None, **broker_args):
        if settings.capsule.deploy_arguments:
            broker_args.update(settings.capsule.deploy_arguments)
        vmb = Broker(
            host_class=Capsule,
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
    new_sat.teardown()
    Broker(hosts=[new_sat]).checkin()


@pytest.fixture(scope='module')
def module_satellite_host(satellite_factory):
    """A fixture that provides a Satellite based on config settings"""
    new_sat = satellite_factory()
    yield new_sat
    new_sat.teardown()
    Broker(hosts=[new_sat]).checkin()


@pytest.fixture(scope='session')
def session_satellite_host(satellite_factory):
    """A fixture that provides a Satellite based on config settings"""
    new_sat = satellite_factory()
    yield new_sat
    new_sat.teardown()
    Broker(hosts=[new_sat]).checkin()


@pytest.fixture
def capsule_host(capsule_factory):
    """A fixture that provides a Capsule based on config settings"""
    new_cap = capsule_factory()
    yield new_cap
    new_cap.teardown()
    Broker(hosts=[new_cap]).checkin()


@pytest.fixture(scope='module')
def module_capsule_host(capsule_factory):
    """A fixture that provides a Capsule based on config settings"""
    new_cap = capsule_factory()
    yield new_cap
    new_cap.teardown()
    Broker(hosts=[new_cap]).checkin()


@pytest.fixture
def capsule_configured(capsule_host, target_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    capsule_host.capsule_setup(sat_host=target_sat)
    yield capsule_host


@pytest.fixture(scope='module')
def module_capsule_configured(module_capsule_host, module_target_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    module_capsule_host.capsule_setup(sat_host=module_target_sat)
    yield module_capsule_host


@pytest.fixture(scope='module')
def module_capsule_configured_mqtt(module_capsule_configured):
    """Configure the capsule instance with the satellite from settings.server.hostname,
    enable MQTT broker"""
    module_capsule_configured.enable_mqtt()
    result = module_capsule_configured.execute('systemctl status mosquitto')
    assert result.status == 0, 'MQTT broker is not running'
    result = module_capsule_configured.execute('firewall-cmd --permanent --add-port="1883/tcp"')
    assert result.status == 0, 'Failed to open mqtt port on capsule'
    module_capsule_configured.execute('firewall-cmd --reload')
    yield module_capsule_configured


@pytest.fixture(scope='module')
def module_lb_capsule(retry_limit=3, delay=300, **broker_args):
    """A fixture that spins 2 capsule for loadbalancer
    :return: List of capsules
    """
    if settings.capsule.get('deploy_arguments'):
        resolved = _resolve_deploy_args(settings.capsule.deploy_arguments)
        settings.capsule.deploy_arguments = resolved
        broker_args.update(settings.capsule.deploy_arguments)
        timeout = (1200 + delay) * retry_limit
        hosts = Broker(
            host_class=Capsule,
            workflow=settings.capsule.deploy_workflow,
            _count=2,
            **broker_args,
        )
        cap_hosts = wait_for(hosts.checkout, timeout=timeout, delay=delay)

    return cap_hosts
