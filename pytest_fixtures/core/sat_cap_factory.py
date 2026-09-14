from contextlib import contextmanager, suppress
from functools import lru_cache

from broker import Broker
from packaging.version import Version
import pytest
from wait_for import wait_for

from robottelo.config import configure_airgun, configure_nailgun, settings
from robottelo.exceptions import ContentHostError
from robottelo.hosts import (
    Capsule,
    IPAHost,
    Satellite,
    get_sat_rhel_version,
    lru_sat_ready_rhel,
)
from robottelo.logging import logger


def resolve_deploy_args(args_dict):
    # TODO: https://github.com/rochacbruno/dynaconf/issues/690
    for key, val in args_dict.copy().to_dict().items():
        if isinstance(val, str) and val.startswith('this.'):
            # Args transformed into small letters and existing capital args removed
            args_dict[key.lower()] = settings.get(args_dict.pop(key).replace('this.', ''))
    return args_dict


def prepare_capsule_checkout(satellite=None, workflow=None, **broker_args):
    """Return (workflow, broker_args) for a Capsule Broker checkout.

    Foremanctl uses ``deploy-foreman-proxy`` and requires the Satellite FQDN at
    checkout time. Installer keeps ``capsule.deploy_workflows.product``.
    """
    if satellite is not None:
        install_method = str(satellite.install_method)
    else:
        install_method = str(settings.server.get('install_method', 'auto'))

    if workflow is None and install_method == 'foremanctl':
        workflows = settings.capsule.deploy_workflows
        workflow = workflows.get('foremanctl') or 'deploy-foreman-proxy'
        deploy_args = settings.capsule.get('deploy_arguments') or {}
        if hasattr(deploy_args, 'to_dict'):
            deploy_args = deploy_args.to_dict()
        broker_args = {**deploy_args, **broker_args}
        sat_fqdn = (
            broker_args.get('foreman_proxy_foreman_fqdn')
            or getattr(satellite, 'hostname', None)
            or settings.server.hostname
        )
        if not sat_fqdn:
            raise ValueError(
                'deploy-foreman-proxy requires a Satellite hostname '
                '(satellite= or settings.server.hostname).'
            )
        broker_args['foreman_proxy_foreman_fqdn'] = sat_fqdn
        return workflow, broker_args

    if settings.capsule.deploy_arguments:
        broker_args.update(settings.capsule.deploy_arguments)
    return workflow or settings.capsule.deploy_workflows.product, broker_args


def _bind_satellite_and_wait_for_capsule(capsule_host, satellite, *, run_setup):
    """Bind the Capsule to Satellite and wait until Katello lists it."""
    capsule_host._satellite = satellite
    if run_setup:
        capsule_host.capsule_setup(sat_host=satellite)

    def _capsule_registered():
        with suppress(IndexError, ContentHostError):
            _ = capsule_host.nailgun_capsule
            return True
        return False

    wait_for(
        _capsule_registered,
        timeout=600,
        delay=15,
        handle_exception=True,
        fail_condition=False,
    )
    return capsule_host


@contextmanager
def _target_satellite_host(request, satellite_factory):
    if 'sanity' not in request.config.option.markexpr:
        new_sat = satellite_factory()
        new_sat.enable_satellite_ipv6_http_proxy()
        yield new_sat
        new_sat.teardown()
        Broker(hosts=[new_sat]).checkin()
    else:
        yield


@lru_cache
def cached_capsule_cdn_register(hostname=None):
    cap = Capsule.get_host_by_hostname(hostname=hostname)
    cap.register_to_cdn()
    cap.setup_rhel_repos()
    cap.setup_capsule_repos()


@contextmanager
def _target_capsule_host(request, capsule_factory, sat_host=None):
    if 'sanity' not in request.config.option.markexpr and not request.config.option.n_minus:
        new_cap = capsule_factory(satellite=sat_host)
        new_cap.enable_ipv6_dnf_and_rhsm_proxy()
        yield new_cap
        new_cap.teardown()
        Broker(hosts=[new_cap]).checkin()
    elif request.config.option.n_minus:
        if not settings.capsule.hostname:
            hosts = Capsule.get_hosts_from_inventory(filter="'cap' in @inv.name")
            settings.capsule.hostname = hosts[0].hostname
            cap = hosts[0]
        else:
            cap = Capsule.get_host_by_hostname(settings.capsule.hostname)
        # Capsule needs RHEL contents for some tests
        cached_capsule_cdn_register(hostname=settings.capsule.hostname)
        yield cap
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
            workflow=workflow or settings.server.deploy_workflows.product,
            **broker_args,
        )
        timeout = (1200 + delay) * retry_limit
        sat = wait_for(
            vmb.checkout, timeout=timeout, delay=delay, handle_exception=True, raise_original=True
        )
        return sat.out

    return factory


@pytest.fixture
def large_capsule_host(capsule_factory, target_sat):
    """A fixture that provides a Capsule based on config settings"""
    new_cap = capsule_factory(satellite=target_sat, deploy_flavor=settings.flavors.custom_db)
    new_cap.enable_ipv6_dnf_and_rhsm_proxy()
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

    def factory(retry_limit=3, delay=300, workflow=None, satellite=None, **broker_args):
        workflow, broker_args = prepare_capsule_checkout(
            satellite=satellite, workflow=workflow, **broker_args
        )
        logger.debug('Checking out Capsule with workflow %s and args %s', workflow, broker_args)
        vmb = Broker(
            host_class=Capsule,
            workflow=workflow,
            **broker_args,
        )
        timeout = (1200 + delay) * retry_limit
        cap = wait_for(
            vmb.checkout, timeout=timeout, delay=delay, handle_exception=True, raise_original=True
        )
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


@pytest.fixture(scope='module')
def module_satellite_mqtt(module_target_sat):
    """Configure satellite with MQTT broker enabled"""
    module_target_sat.set_rex_script_mode_provider('pull-mqtt')
    # lower the mqtt_resend_interval interval
    module_target_sat.set_mqtt_resend_interval('30')
    result = module_target_sat.execute('systemctl status mosquitto')
    assert result.status == 0, 'MQTT broker is not running'
    result = module_target_sat.execute('firewall-cmd --permanent --add-port="1883/tcp"')
    assert result.status == 0, 'Failed to open mqtt port on capsule'
    module_target_sat.execute('firewall-cmd --reload')
    return module_target_sat


@pytest.fixture
def capsule_host(request, capsule_factory, target_sat):
    """A fixture that provides a Capsule based on config settings"""
    with _target_capsule_host(request, capsule_factory, sat_host=target_sat) as cap:
        yield cap


@pytest.fixture(scope='module')
def module_capsule_host(request, capsule_factory, module_target_sat):
    """A fixture that provides a Capsule based on config settings"""
    with _target_capsule_host(request, capsule_factory, sat_host=module_target_sat) as cap:
        yield cap


@pytest.fixture(scope='session')
def session_capsule_host(request, capsule_factory, session_target_sat):
    """A fixture that provides a Capsule based on config settings"""
    with _target_capsule_host(request, capsule_factory, sat_host=session_target_sat) as cap:
        yield cap


@pytest.fixture
def capsule_configured(request, capsule_host, target_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    run_setup = not request.config.option.n_minus
    return _bind_satellite_and_wait_for_capsule(capsule_host, target_sat, run_setup=run_setup)


@pytest.fixture
def large_capsule_configured(large_capsule_host, target_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    large_capsule_host.capsule_setup(sat_host=target_sat)
    return large_capsule_host


@pytest.fixture(scope='module')
def module_capsule_configured(request, module_capsule_host, module_target_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    # Sanity reuses the Capsule from the installer test; _target_capsule_host yields None.
    if 'build_sanity' in request.config.option.markexpr:
        return Capsule.get_host_by_hostname(settings.capsule.hostname)
    run_setup = not request.config.option.n_minus
    return _bind_satellite_and_wait_for_capsule(
        module_capsule_host, module_target_sat, run_setup=run_setup
    )


@pytest.fixture(scope='module')
def module_unconfigured_satellite():
    deploy_args = settings.server.deploy_arguments
    with Broker(
        workflow=settings.server.deploy_workflows.unconfigured, **deploy_args, host_class=Satellite
    ) as host:
        yield host


def get_iop_deploy_args():
    """Get deploy arguments for IoP workflow"""
    image_args = {
        f'iop_{service}_image': path for service, path in settings.rh_cloud.iop.image_paths.items()
    }
    return settings.server.deploy_arguments.to_dict() | image_args


@pytest.fixture(scope='module')
def module_satellite_iop(module_target_sat):
    """Provide a Satellite with Red Hat Lightspeed (IoP) enabled.

    If IoP is already enabled on the Satellite, use it as-is without modification.
    If IoP is not enabled, configure it and uninstall during teardown.
    """
    satellite = module_target_sat
    was_already_enabled = satellite.iop_enabled

    if not was_already_enabled:
        satellite.configure_iop()

    yield satellite

    if not was_already_enabled:
        satellite.uninstall_iop()


@pytest.fixture(scope='module')
def module_capsule_configured_mqtt(request, module_capsule_configured_ansible):
    """Configure the capsule instance with the satellite from settings.server.hostname,
    enable MQTT broker"""
    module_capsule_configured_ansible.set_rex_script_mode_provider('pull-mqtt')
    # lower the mqtt_resend_interval interval
    module_capsule_configured_ansible.set_mqtt_resend_interval('30')
    result = module_capsule_configured_ansible.execute('systemctl status mosquitto')
    assert result.status == 0, 'MQTT broker is not running'
    result = module_capsule_configured_ansible.execute(
        'firewall-cmd --permanent --add-port="1883/tcp"'
    )
    assert result.status == 0, 'Failed to open mqtt port on capsule'
    module_capsule_configured_ansible.execute('firewall-cmd --reload')
    yield module_capsule_configured_ansible
    if request.config.option.n_minus:
        raise TypeError('The teardown is missed for MQTT configuration undo for nminus testing')


@pytest.fixture(scope='module')
def module_lb_capsules(module_target_sat, retry_limit=3, delay=300, **broker_args):
    """A fixture that spins 2 capsule for loadbalancer
    :return: List of capsules
    """
    if str(module_target_sat.install_method) == 'foremanctl':
        pytest.skip(
            'Capsule load-balancer setup uses satellite-installer '
            'and is not supported on foremanctl.'
        )
    if settings.capsule.get('deploy_arguments'):
        resolved = resolve_deploy_args(settings.capsule.deploy_arguments)
        settings.set('capsule.deploy_arguments', resolved)
        broker_args.update(settings.capsule.deploy_arguments)
        timeout = (1200 + delay) * retry_limit
        hosts = Broker(
            host_class=Capsule,
            workflow=settings.capsule.deploy_workflows.product,
            _count=2,
            **broker_args,
        )
        cap_hosts = wait_for(
            hosts.checkout, timeout=timeout, delay=delay, handle_exception=True, raise_original=True
        )

    [cap.enable_ipv6_dnf_and_rhsm_proxy() for cap in cap_hosts.out]
    yield cap_hosts.out

    [cap.teardown() for cap in cap_hosts.out]
    Broker(hosts=cap_hosts.out).checkin()


@pytest.fixture(scope='module')
def module_capsule_configured_ansible(module_capsule_configured):
    """Configure the capsule instance with Ansible feature enabled"""
    result = module_capsule_configured.install(
        cmd_args=[
            'enable-foreman-proxy-plugin-ansible',
        ]
    )
    assert result.status == 0, 'Installer failed to enable ansible plugin.'
    return module_capsule_configured


@pytest.fixture(scope='module', params=['IDM', 'AD'])
def parametrized_enrolled_sat(
    request,
    satellite_factory,
    ad_data,
):
    """Yields a Satellite enrolled into [IDM, AD] as parameter."""
    new_sat = satellite_factory()
    new_sat.enable_satellite_ipv6_http_proxy()
    ipa_host = IPAHost(new_sat)
    new_sat.register_to_cdn()
    if 'IDM' in request.param:
        ipa_host.enroll_idm_and_configure_external_auth()
        yield new_sat
        ipa_host.disenroll_idm()
    else:
        shortened_hostname = new_sat.enroll_ad_and_configure_external_auth(ad_data)
        if shortened_hostname is not None:
            new_sat.shortened_hostname = shortened_hostname
        yield new_sat
    new_sat.unregister()
    new_sat.teardown()
    Broker(hosts=[new_sat]).checkin()


def get_sat_deploy_args(request):
    """Get deploy arguments for Satellite base OS deployment."""
    rhel_version = get_sat_rhel_version()
    deploy_args = (
        settings.content_host[f'rhel{rhel_version.major}'].vm
        | settings.server.deploy_arguments
        | {
            'deploy_rhel_version': rhel_version.base_version,
            'deploy_flavor': settings.flavors.default,
            'workflow': settings.server.deploy_workflows.os,
        }
    )
    if hasattr(request, 'param'):
        if isinstance(request.param, dict):
            deploy_args.update(request.param)
        else:
            deploy_args['deploy_rhel_version'] = request.param
    return deploy_args


def get_cap_deploy_args():
    """Get deploy arguments for Capsule base OS deployment."""
    rhel_version = Version(settings.capsule.version.rhel_version)
    return (
        settings.content_host[f'rhel{rhel_version.major}'].vm
        | settings.capsule.deploy_arguments
        | {
            'deploy_rhel_version': rhel_version.base_version,
            'deploy_flavor': settings.flavors.default,
            'workflow': settings.capsule.deploy_workflows.os,
        }
    )


@pytest.fixture
def sat_ready_rhel(request):
    deploy_args = get_sat_deploy_args(request)
    with Broker(**deploy_args, host_class=Satellite) as host:
        yield host


@pytest.fixture(scope='module')
def module_sat_ready_rhels(request, module_target_sat):
    deploy_args = get_sat_deploy_args(request)
    if 'build_sanity' not in request.config.option.markexpr:
        with Broker(**deploy_args, host_class=Satellite, _count=3) as hosts:
            yield hosts
    else:
        yield [module_target_sat]


@pytest.fixture
def cap_ready_rhel():
    """Deploy bare RHEL system ready for Capsule installation."""
    deploy_args = get_cap_deploy_args()

    with Broker(**deploy_args, host_class=Capsule) as host:
        host.enable_ipv6_dnf_and_rhsm_proxy()
        yield host


@pytest.fixture(scope='session')
def installer_satellite(request):
    """A fixture to freshly install Satellite using auto-detected installation method

    This is a pure / virgin / nontemplate based satellite.
    Uses install_satellite() which auto-detects between satellite-installer and foremanctl.

    :params request: A pytest request object and this fixture is looking for
        broker object of class satellite
    """
    if 'sanity' in request.config.option.markexpr:
        sat = Satellite(settings.server.hostname)
    else:
        sat = lru_sat_ready_rhel(getattr(request, 'param', None))

    # Use unified installation method with auto-detection
    sat.install_satellite()

    sat.enable_satellite_ipv6_http_proxy()
    if 'sanity' in request.config.option.markexpr:
        configure_nailgun()
        configure_airgun()
    yield sat
    if 'sanity' not in request.config.option.markexpr:
        sat = Satellite.get_host_by_hostname(sat.hostname)
        sat.unregister()
        Broker(hosts=[sat]).checkin()


@pytest.fixture(scope='session')
def satellite_with_install_method(request):
    """Install Satellite using specified or auto-detected method.

    Can be parameterized:
    @pytest.mark.parametrize('satellite_with_install_method',
                             ['installer', 'foremanctl', 'auto'],
                             indirect=True)

    :param request: pytest request object with optional param for install method
    """
    install_method = getattr(request, 'param', 'auto')

    if 'sanity' in request.config.option.markexpr:
        sat = Satellite(settings.server.hostname)
        configure_nailgun()
        configure_airgun()
    else:
        sat = lru_sat_ready_rhel(None)
        sat.install_satellite(installer_method=install_method)
        sat.enable_satellite_ipv6_http_proxy()

    yield sat

    if 'sanity' not in request.config.option.markexpr:
        sat = Satellite.get_host_by_hostname(sat.hostname)
        sat.unregister()
        Broker(hosts=[sat]).checkin()
