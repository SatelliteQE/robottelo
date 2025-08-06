# Satellite-maintain fixtures
import datetime

import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import SATELLITE_MAINTAIN_YML
from robottelo.exceptions import SatelliteHostError
from robottelo.hosts import Capsule, Satellite
from robottelo.logging import logger

synced_repos = pytest.StashKey[dict]


@pytest.fixture(scope='module')
def module_stash(request):
    """Module scoped stash for storing data between tests"""
    # Please refer the documentation for more details on stash
    # https://docs.pytest.org/en/latest/reference/reference.html#stash
    request.node.stash[synced_repos] = {}
    return request.node.stash


@pytest.fixture
def sat_maintain(request):
    """Function scoped fixture to be used in satellite_maintain tests. It returns the right host based on request parameters"""
    iop_settings = settings.rh_cloud.iop_advisor_engine
    if settings.remotedb.server:
        logger.info('Using Satellite with external DB server')
        satellite = Satellite(settings.remotedb.server)
        satellite.enable_satellite_ipv6_http_proxy()
        yield satellite
    else:
        infra_host_type = getattr(request, 'param', 'satellite')
        if infra_host_type == 'capsule':
            infra_host = request.getfixturevalue('module_capsule_configured')
        elif infra_host_type == 'satellite_iop':
            infra_host = request.getfixturevalue('module_satellite_iop')
        else:
            infra_host = request.getfixturevalue('module_target_sat')
        infra_host.register_to_cdn()
        yield infra_host
        if infra_host_type == 'satellite_iop' and not infra_host.is_podman_logged_in(
            iop_settings.stage_registry
        ):
            infra_host.podman_login(
                iop_settings.stage_username, iop_settings.stage_token, iop_settings.stage_registry
            )


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
def module_synced_repos(module_capsule_configured, module_sca_manifest, module_stash):
    if not module_stash[synced_repos]:
        org = module_capsule_configured.satellite.api.Organization().create()
        module_capsule_configured.satellite.upload_manifest(org.id, module_sca_manifest.content)
        # sync custom repo
        cust_prod = module_capsule_configured.satellite.api.Product(organization=org).create()
        cust_repo = module_capsule_configured.satellite.api.Repository(
            url=settings.repos.yum_1.url, product=cust_prod
        ).create()
        cust_repo.sync()

        # sync RH repo
        product = module_capsule_configured.satellite.api.Product(
            name=constants.PRDS['rhae'], organization=org.id
        ).search()[0]
        r_set = module_capsule_configured.satellite.api.RepositorySet(
            name=constants.REPOSET['rhae2'], product=product
        ).search()[0]
        payload = {'basearch': constants.DEFAULT_ARCHITECTURE, 'product_id': product.id}
        r_set.enable(data=payload)
        result = module_capsule_configured.satellite.api.Repository(
            name=constants.REPOS['rhae2']['name']
        ).search(query={'organization_id': org.id})
        rh_repo_id = result[0].id
        rh_repo = module_capsule_configured.satellite.api.Repository(id=rh_repo_id).read()
        rh_repo.sync()

        module_stash[synced_repos]['rh_repo'] = rh_repo
        module_stash[synced_repos]['cust_repo'] = cust_repo
        module_stash[synced_repos]['org'] = org

    if type(module_capsule_configured) is Capsule:
        # assign the Library LCE to the Capsule
        lce = module_capsule_configured.satellite.api.LifecycleEnvironment(
            organization=module_stash[synced_repos]['org']
        ).search(query={'search': f'name={constants.ENVIRONMENT}'})[0]
        module_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = module_capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]
        # sync the Capsule
        sync_status = module_capsule_configured.nailgun_capsule.content_sync()
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
            'sync-date': datetime.datetime.today().strftime("%Y-%m-%d"),
        }
    )
    sat_maintain.execute(f'cp {SATELLITE_MAINTAIN_YML} foreman_maintain.yml')
    sat_maintain.execute(f'sed -i "$ a :manage_crond: true" {SATELLITE_MAINTAIN_YML}')

    yield sat_maintain.api.SyncPlan(organization=org.label).search(query={'search': 'enabled=true'})

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.cli.MaintenanceMode.stop().status == 0
        sat_maintain.execute(f'cp foreman_maintain.yml {SATELLITE_MAINTAIN_YML}')
        sat_maintain.execute('rm -rf foreman_maintain.yml')
        result = sat_maintain.cli.SyncPlan.delete(
            {'name': new_sync_plan.name, 'organization-id': org.id}
        )
        assert 'Sync plan destroyed' in result
        sat_maintain.cli.Org.delete({'id': org.id})
