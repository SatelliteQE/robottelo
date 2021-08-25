import pytest
from broker.broker import VMBroker
from wait_for import wait_for

from robottelo.config import settings
from robottelo.hosts import Capsule
from robottelo.hosts import Satellite


@pytest.fixture(scope='session')
def default_sat(align_to_satellite):
    """Returns a Satellite object for settings.server.hostname"""
    if settings.server.hostname:
        return Satellite()


@pytest.fixture(scope='session')
def satellite_factory():
    def factory(retry_limit=3, delay=300, **broker_args):
        vmb = VMBroker(
            host_classes={'host': Satellite},
            workflow=settings.server.deploy_workflow,
            **broker_args,
        )
        timeout = (1200 + delay) * retry_limit
        sat = wait_for(
            vmb.checkout, func_kwargs=broker_args, timeout=timeout, delay=delay, fail_condition=[]
        )
        return sat.out

    return factory


@pytest.fixture(scope='session')
def capsule_factory():
    def factory(retry_limit=3, delay=300, **broker_args):
        vmb = VMBroker(
            host_classes={'host': Capsule}, workflow=settings.capsule.deploy_workflow, **broker_args
        )
        timeout = (1200 + delay) * retry_limit
        cap = wait_for(
            vmb.checkout, func_kwargs=broker_args, timeout=timeout, delay=delay, fail_condition=[]
        )
        return cap.out

    return factory


@pytest.fixture
def satellite_latest(default_sat):
    """A fixture that provides a latest Satellite"""
    version_args = dict(
        deploy_sat_version=default_sat.version or settings.server.version.get('release', ''),
        deploy_snap_version=settings.server.version.get('snap', ''),
    )

    with VMBroker(
        host_classes={'host': Satellite}, workflow=settings.server.deploy_workflow, **version_args
    ) as sat:
        yield sat


@pytest.fixture
def capsule_latest(default_sat):
    """A fixture that provides an unconfigured latest Capsule"""
    version_args = dict(
        deploy_sat_version=getattr(default_sat, 'version', None)
        or settings.server.version.get('release', ''),
        deploy_snap_version=settings.server.version.get('snap', ''),
    )

    with VMBroker(
        host_classes={'host': Capsule},
        workflow=str(settings.capsule.deploy_workflow),
        **version_args,
    ) as cap:
        yield cap


@pytest.fixture
def capsule_configured(capsule_latest, default_sat):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    capsule_latest.install_katello_ca(default_sat)
    capsule_latest.register_contenthost()
    capsule_latest.capsule_setup()
    yield capsule_latest


@pytest.fixture
def destructive_sat(satellite_latest):
    """Destructive tests require changing settings.server.hostname for now"""
    with satellite_latest as sat:
        yield sat
