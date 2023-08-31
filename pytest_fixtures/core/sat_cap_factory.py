from contextlib import contextmanager

import pytest
from broker import Broker
from wait_for import wait_for

from robottelo.config import configure_airgun
from robottelo.config import configure_nailgun
from robottelo.config import settings
from robottelo.hosts import Capsule
from robottelo.hosts import get_sat_rhel_version
from robottelo.hosts import IPAHost
from robottelo.hosts import lru_sat_ready_rhel
from robottelo.hosts import Satellite
from robottelo.logging import logger
from robottelo.utils.installer import InstallerCommand


def resolve_deploy_args(args_dict):
    # TODO: https://github.com/rochacbruno/dynaconf/issues/690
    for key, val in args_dict.copy().to_dict().items():
        if isinstance(val, str) and val.startswith('this.'):
            # Args transformed into small letters and existing capital args removed
            args_dict[key.lower()] = settings.get(args_dict.pop(key).replace('this.', ''))
    return args_dict


@contextmanager
def _target_satellite_host(request, satellite_factory):
    if 'sanity' not in request.config.option.markexpr:
        new_sat = satellite_factory()
        yield new_sat
        new_sat.teardown()
        Broker(hosts=[new_sat]).checkin()
    else:
        yield


@contextmanager
def _target_capsule_host(request, capsule_factory):
    if 'sanity' not in request.config.option.markexpr:
        new_cap = capsule_factory()
        yield new_cap
        new_cap.teardown()
        Broker(hosts=[new_cap]).checkin()
    else:
        yield


@pytest.fixture(scope='session')
def satellite_factory():
    if settings.server.get('deploy_arguments'):
        logger.debug(f'Original deploy arguments for sat: {settings.server.deploy_arguments}')
        resolved = resolve_deploy_args(settings.server.deploy_arguments)
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


@pytest.fixture
def large_capsule_host(capsule_factory):
    """A fixture that provides a Capsule based on config settings"""
    new_cap = capsule_factory(deploy_flavor=settings.flavors.custom_db)
    yield new_cap
    new_cap.teardown()
    Broker(hosts=[new_cap]).checkin()


@pytest.fixture(scope='session')
def capsule_factory():
    if settings.capsule.get('deploy_arguments'):
        logger.debug(f'Original deploy arguments for cap: {settings.capsule.deploy_arguments}')
        resolved = resolve_deploy_args(settings.capsule.deploy_arguments)
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
def satellite_host(request, satellite_factory):
    """A fixture that provides a Satellite based on config settings"""
    with _target_satellite_host(request, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='module')
def module_satellite_host(request, satellite_factory):
    """A fixture that provides a Satellite based on config settings"""
    with _target_satellite_host(request, satellite_factory) as sat:
        yield sat


@pytest.fixture(scope='session')
def session_satellite_host(request, satellite_factory):
    """A fixture that provides a Satellite based on config settings"""
    with _target_satellite_host(request, satellite_factory) as sat:
        yield sat


@pytest.fixture
def capsule_host(request, capsule_factory):
    """A fixture that provides a Capsule based on config settings"""
    with _target_capsule_host(request, capsule_factory) as cap:
        yield cap


@pytest.fixture(scope='module')
def module_capsule_host(request, capsule_factory):
    """A fixture that provides a Capsule based on config settings"""
    with _target_capsule_host(request, capsule_factory) as cap:
        yield cap


@pytest.fixture(scope='session')
def session_capsule_host(request, capsule_factory):
    """A fixture that provides a Capsule based on config settings"""
    with _target_capsule_host(request, capsule_factory) as cap:
        yield cap


@pytest.fixture
def capsule_configured(capsule_host, target_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    capsule_host.capsule_setup(sat_host=target_sat)
    yield capsule_host


@pytest.fixture
def large_capsule_configured(large_capsule_host, target_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    large_capsule_host.capsule_setup(sat_host=target_sat)
    yield large_capsule_host


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
        resolved = resolve_deploy_args(settings.capsule.deploy_arguments)
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


def get_deploy_args(request):
    deploy_args = {
        'deploy_rhel_version': get_sat_rhel_version().base_version,
        'deploy_flavor': settings.flavors.default,
        'promtail_config_template_file': 'config_sat.j2',
        'workflow': 'deploy-rhel',
    }
    if hasattr(request, 'param'):
        if isinstance(request.param, dict):
            deploy_args.update(request.param)
        else:
            deploy_args['deploy_rhel_version'] = request.param
    return deploy_args


@pytest.fixture
def sat_ready_rhel(request):
    deploy_args = get_deploy_args(request)
    with Broker(**deploy_args, host_class=Satellite) as host:
        yield host


@pytest.fixture(scope='module')
def module_sat_ready_rhels(request):
    deploy_args = get_deploy_args(request)
    with Broker(**deploy_args, host_class=Satellite, _count=2) as hosts:
        yield hosts


@pytest.fixture
def cap_ready_rhel():
    rhel8 = settings.content_host.rhel8.vm
    deploy_args = {
        'deploy_rhel_version': rhel8.deploy_rhel_version,
        'deploy_flavor': 'satqe-ssd.standard.std',
        'workflow': rhel8.workflow,
    }
    with Broker(**deploy_args, host_class=Capsule) as host:
        yield host


@pytest.fixture(scope='session')
def installer_satellite(request):
    """A fixture to freshly install the satellite using installer on RHEL machine

    This is a pure / virgin / nontemplate based satellite

    :params request: A pytest request object and this fixture is looking for
        broker object of class satellite
    """
    sat_version = settings.server.version.release
    if 'sanity' in request.config.option.markexpr:
        sat = Satellite(settings.server.hostname)
    else:
        sat = lru_sat_ready_rhel(getattr(request, 'param', None))
    sat.setup_firewall()
    # # Register for RHEL8 repos, get Ohsnap repofile, and enable and download satellite
    sat.register_to_cdn()
    sat.download_repofile(product='satellite', release=settings.server.version.release)
    sat.execute('dnf -y module enable satellite:el8 && dnf -y install satellite')
    installed_version = sat.execute('rpm --query satellite').stdout
    assert sat_version in installed_version
    # Install Satellite
    sat.execute(
        InstallerCommand(
            installer_args=[
                'scenario satellite',
                f'foreman-initial-admin-password {settings.server.admin_password}',
            ]
        ).get_command(),
        timeout='30m',
    )
    if 'sanity' in request.config.option.markexpr:
        configure_nailgun()
        configure_airgun()
    yield sat
    if 'sanity' not in request.config.option.markexpr:
        sanity_sat = Satellite(sat.hostname)
        sanity_sat.unregister()
        broker_sat = Satellite.get_host_by_hostname(sanity_sat.hostname)
        Broker(hosts=[broker_sat]).checkin()
