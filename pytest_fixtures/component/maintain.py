# Satellite-maintain fixtures
import datetime

import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.exceptions import SatelliteHostError
from robottelo.hosts import Capsule, Satellite
from robottelo.logging import logger

synced_repos = pytest.StashKey[dict]


def _get_satellite_host(request):
    """Return the correct Satellite host depending on settings. Ensures IPv6 proxy and CDN registration."""
    if settings.remotedb.server:
        logger.info(f'Creating Satellite with remotedb.server: {settings.remotedb.server}')
        infra_sat_host = Satellite(settings.remotedb.server)
    else:
        logger.info('Using module_target_sat fallback')
        infra_sat_host = request.getfixturevalue('module_target_sat')
    infra_sat_host.enable_satellite_ipv6_http_proxy()
    infra_sat_host.register_to_cdn()
    return infra_sat_host


@pytest.fixture(scope='module')
def module_stash(request):
    """Module scoped stash for storing data between tests"""
    # Please refer the documentation for more details on stash
    # https://docs.pytest.org/en/latest/reference/reference.html#stash
    request.node.stash[synced_repos] = {}
    return request.node.stash


@pytest.fixture(scope='module')
def module_capsule_maintain(request, module_capsule_host):
    """Configure the capsule instance with the satellite."""
    infra_sat_host = _get_satellite_host(request)
    module_capsule_host.capsule_setup(sat_host=infra_sat_host)
    return module_capsule_host


@pytest.fixture(scope='module')
def sat_maintain(request):
    """
    Returns the correct host (Satellite, Capsule, or Satellite IOP) based on request.param.
    Handles podman login for Satellite IOP if needed.
    """
    host_type = getattr(request, 'param', 'satellite')

    if host_type == 'capsule':
        infra_host = request.getfixturevalue('module_capsule_maintain')
    elif host_type == 'satellite_iop':
        infra_host = request.getfixturevalue('module_satellite_iop')
    else:
        infra_host = _get_satellite_host(request)

    yield infra_host

    if host_type == 'satellite_iop':
        iop_settings = settings.rh_cloud.iop_advisor_engine
        if not infra_host.is_podman_logged_in(iop_settings.stage_registry):
            infra_host.podman_login(
                iop_settings.stage_username,
                iop_settings.stage_token,
                iop_settings.stage_registry,
            )


def _sync_repositories(sat_host, manifest):
    """Helper to upload manifest, sync custom and RH repos."""
    if type(sat_host) is Satellite:
        satellite = sat_host
        logger.info(f'Using Satellite object directly, hostname: {satellite.hostname}')
    else:
        satellite = sat_host.satellite
        logger.info(f"Using Capsule's satellite property, satellite hostname: {satellite.hostname}")

    org = satellite.api.Organization().create()
    satellite.upload_manifest(org.id, manifest.content)

    # Sync custom repo
    cust_prod = satellite.api.Product(organization=org).create()
    cust_repo = satellite.api.Repository(url=settings.repos.yum_1.url, product=cust_prod).create()
    cust_repo.sync()

    # Sync RH repo
    product = satellite.api.Product(name=constants.PRDS['rhae'], organization=org.id).search()[0]
    r_set = satellite.api.RepositorySet(name=constants.REPOSET['rhae2'], product=product).search()[
        0
    ]
    payload = {'basearch': constants.DEFAULT_ARCHITECTURE, 'product_id': product.id}
    r_set.enable(data=payload)
    result = satellite.api.Repository(name=constants.REPOS['rhae2']['name']).search(
        query={'organization_id': org.id}
    )
    rh_repo = satellite.api.Repository(id=result[0].id).read()
    rh_repo.sync()

    return {'org': org, 'cust_repo': cust_repo, 'rh_repo': rh_repo}


@pytest.fixture
def start_satellite_services(sat_maintain):
    """Teardown for satellite-maintain tests to ensure that all Satellite services are started"""
    yield
    logger.info('Ensuring that all %s services are running', sat_maintain.__class__.__name__)
    result = sat_maintain.cli.Service.start()
    if result.status != 0:
        logger.error('Unable to start all %s services', sat_maintain.__class__.__name__)
        raise SatelliteHostError('Failed to start Satellite services')


@pytest.fixture
def setup_backup_tests(request, sat_maintain):
    """Teardown for backup/restore tests"""
    assert sat_maintain.execute('rm -rf /tmp/backup-*').status == 0

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.execute('rm -rf /tmp/backup-*').status == 0


@pytest.fixture(scope='module')
def module_synced_repos(sat_maintain, module_sca_manifest, module_stash):
    """
    Syncs custom and RH repositories if not already synced.
    Assigns Library LCE to Capsule if applicable and ensures Capsule sync.
    """
    if not module_stash[synced_repos]:
        synced = _sync_repositories(sat_maintain, module_sca_manifest)
        module_stash[synced_repos].update(synced)

    if type(sat_maintain) is Capsule:
        org = module_stash[synced_repos]['org']
        lce = sat_maintain.satellite.api.LifecycleEnvironment(organization=org).search(
            query={'search': f'name={constants.ENVIRONMENT}'}
        )[0]

        sat_maintain.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        envs = sat_maintain.nailgun_capsule.content_lifecycle_environments()
        assert lce.id in [e['id'] for e in envs['results']]

        sync_status = sat_maintain.nailgun_capsule.content_sync()
        assert sync_status['result'] == 'success'

    return {
        'custom': module_stash[synced_repos]['cust_repo'],
        'rh': module_stash[synced_repos]['rh_repo'],
    }


@pytest.fixture
def setup_sync_plan(request, sat_maintain):
    """This fixture is used to create/delete sync-plan.
    It is used by tests test_positive_sync_plan_disable_enable and test_positive_maintenance_mode.
    """
    org = sat_maintain.api.Organization().create()
    # Setup sync-plan
    new_sync_plan = sat_maintain.cli_factory.sync_plan(
        {
            'enabled': 'true',
            'interval': 'weekly',
            'organization-id': org.id,
            'sync-date': datetime.datetime.today().strftime('%Y-%m-%d'),
        }
    )

    yield sat_maintain.api.SyncPlan(organization=org.label).search(query={'search': 'enabled=true'})

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.cli.MaintenanceMode.stop().status == 0
        result = sat_maintain.cli.SyncPlan.delete(
            {'name': new_sync_plan.name, 'organization-id': org.id}
        )
        assert 'Sync plan destroyed' in result
        sat_maintain.cli.Org.delete({'id': org.id})
