from contextlib import contextmanager

import pytest
from box import Box
from broker import Broker
from wait_for import wait_for

from robottelo.config import settings
from robottelo.hosts import Capsule
from robottelo.hosts import Satellite
from robottelo.logging import logger


def _resolve_deploy_args(args_dict):
    # TODO: https://github.com/rochacbruno/dynaconf/issues/690
    for key, val in args_dict.copy().to_dict().items():
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


@pytest.fixture(scope='module')
def module_discovery_sat(
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
):
    """Creates a Satellite with discovery installed and configured"""
    sat = module_provisioning_sat.sat
    # Register to CDN and install discovery image
    sat.register_to_cdn()
    sat.execute('yum -y --disableplugin=foreman-protector install foreman-discovery-image')
    sat.unregister()
    # Symlink image so it can be uploaded for KEXEC
    disc_img_path = sat.execute(
        'find /usr/share/foreman-discovery-image -name "foreman-discovery-image-*.iso"'
    ).stdout[:-1]
    disc_img_name = disc_img_path.split("/")[-1]
    sat.execute(f'ln -s {disc_img_path} /var/www/html/pub/{disc_img_name}')
    # Change 'Default PXE global template entry'
    pxe_entry = sat.api.Setting().search(query={'search': 'Default PXE global template entry'})[0]
    if pxe_entry.value != "discovery":
        pxe_entry.value = "discovery"
        pxe_entry.update(['value'])
    # Build PXE default template to get default PXE file
    sat.api.ProvisioningTemplate().build_pxe_default()

    # Update discovery taxonomies settings
    discovery_loc = sat.api.Setting().search(query={'search': 'name=discovery_location'})[0]
    discovery_loc.value = module_location.name
    discovery_loc.update(['value'])
    discovery_org = sat.api.Setting().search(query={'search': 'name=discovery_organization'})[0]
    discovery_org.value = module_sca_manifest_org.name
    discovery_org.update(['value'])

    # Enable flag to auto provision discovered hosts via discovery rules
    discovery_auto = sat.api.Setting().search(query={'search': 'name=discovery_auto'})[0]
    discovery_auto.value = 'true'
    discovery_auto.update(['value'])

    return Box(sat=sat, iso=disc_img_name)
