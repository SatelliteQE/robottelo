import pytest
from broker import Broker
from wait_for import wait_for

from pytest_fixtures.core.broker import _resolve_deploy_args
from robottelo.config import settings
from robottelo.hosts import Capsule
from robottelo.hosts import IPAHost


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


@pytest.fixture(scope='session')
def session_capsule_host(capsule_factory):
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


@pytest.fixture(scope='session')
def session_capsule_configured(session_capsule_host, session_target_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    session_capsule_host.capsule_setup(sat_host=session_target_sat)
    yield session_capsule_host


@pytest.fixture(scope='module')
def module_capsule_configured_mqtt(module_capsule_configured):
    """Configure the capsule instance with the satellite from settings.server.hostname,
    enable MQTT broker"""
    module_capsule_configured.set_rex_script_mode_provider('pull-mqtt')
    # lower the mqtt_resend_interval interval
    module_capsule_configured.set_mqtt_resend_interval('30')
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
        settings.set('capsule.deploy_arguments', resolved)
        broker_args.update(settings.capsule.deploy_arguments)
        timeout = (1200 + delay) * retry_limit
        hosts = Broker(
            host_class=Capsule,
            workflow=settings.capsule.deploy_workflow,
            _count=2,
            **broker_args,
        )
        cap_hosts = wait_for(hosts.checkout, timeout=timeout, delay=delay)

    yield cap_hosts.out

    [cap.teardown() for cap in cap_hosts.out]
    Broker(hosts=cap_hosts.out).checkin()


@pytest.fixture(scope='module')
def module_capsule_configured_async_ssh(module_capsule_configured):
    """Configure the capsule instance with the satellite from settings.server.hostname,
    enable MQTT broker"""
    module_capsule_configured.set_rex_script_mode_provider('ssh-async')
    yield module_capsule_configured


@pytest.fixture(scope='module')
def rhcloud_sat_host(satellite_factory):
    """A module level fixture that provides a Satellite based on config settings"""
    new_sat = satellite_factory()
    yield new_sat
    new_sat.teardown()
    Broker(hosts=[new_sat]).checkin()


@pytest.fixture(scope='module', params=['IDM', 'AD'])
def parametrized_enrolled_sat(
    request,
    satellite_factory,
    ad_data,
):
    """Yields a Satellite enrolled into [IDM, AD] as parameter."""
    new_sat = satellite_factory()
    ipa_host = IPAHost(new_sat)
    new_sat.register_to_cdn()
    if 'IDM' in request.param:
        ipa_host.enroll_idm_and_configure_external_auth()
        yield new_sat
        ipa_host.disenroll_idm()
    else:
        new_sat.enroll_ad_and_configure_external_auth(ad_data)
        yield new_sat
    new_sat.unregister()
    new_sat.teardown()
    Broker(hosts=[new_sat]).checkin()
