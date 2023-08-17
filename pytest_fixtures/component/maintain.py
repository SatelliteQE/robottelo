# Satellite-maintain fixtures
import datetime

import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import SATELLITE_MAINTAIN_YML
from robottelo.hosts import Capsule
from robottelo.hosts import Satellite

synced_repos = pytest.StashKey[dict]


@pytest.fixture(scope='module')
def module_stash(request):
    """Module scoped stash for storing data between tests"""
    # Please refer the documentation for more details on stash
    # https://docs.pytest.org/en/latest/reference/reference.html#stash
    request.node.stash[synced_repos] = {}
    yield request.node.stash


@pytest.fixture(scope='session')
def sat_maintain(request, session_target_sat, session_capsule_configured):
    if settings.remotedb.server:
        yield Satellite(settings.remotedb.server)
    else:
        session_target_sat.register_to_cdn(pool_ids=settings.subscription.fm_rhn_poolid.split())
        hosts = {'satellite': session_target_sat, 'capsule': session_capsule_configured}
        yield hosts[request.param]


@pytest.fixture
def setup_backup_tests(request, sat_maintain):
    """Teardown for backup/restore tests"""
    assert sat_maintain.execute('rm -rf /tmp/backup-*').status == 0

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.execute('rm -rf /tmp/backup-*').status == 0


@pytest.fixture(scope='module')
def module_synced_repos(
    sat_maintain, session_capsule_configured, module_sca_manifest, module_stash
):
    if not module_stash[synced_repos]:
        org = sat_maintain.satellite.api.Organization().create()
        sat_maintain.satellite.upload_manifest(org.id, module_sca_manifest.content)
        # sync custom repo
        cust_prod = sat_maintain.satellite.api.Product(organization=org).create()
        cust_repo = sat_maintain.satellite.api.Repository(
            url=settings.repos.yum_1.url, product=cust_prod
        ).create()
        cust_repo.sync()

        # sync RH repo
        product = sat_maintain.satellite.api.Product(
            name=constants.PRDS['rhae'], organization=org.id
        ).search()[0]
        r_set = sat_maintain.satellite.api.RepositorySet(
            name=constants.REPOSET['rhae2'], product=product
        ).search()[0]
        payload = {'basearch': constants.DEFAULT_ARCHITECTURE, 'product_id': product.id}
        r_set.enable(data=payload)
        result = sat_maintain.satellite.api.Repository(
            name=constants.REPOS['rhae2']['name']
        ).search(query={'organization_id': org.id})
        rh_repo_id = result[0].id
        rh_repo = sat_maintain.satellite.api.Repository(id=rh_repo_id).read()
        rh_repo.sync()

        module_stash[synced_repos]['rh_repo'] = rh_repo
        module_stash[synced_repos]['cust_repo'] = cust_repo
        module_stash[synced_repos]['org'] = org

    if type(sat_maintain) is Capsule:
        # assign the Library LCE to the Capsule
        lce = sat_maintain.satellite.api.LifecycleEnvironment(
            organization=module_stash[synced_repos]['org']
        ).search(query={'search': f'name={constants.ENVIRONMENT}'})[0]
        session_capsule_configured.nailgun_capsule.content_add_lifecycle_environment(
            data={'environment_id': lce.id}
        )
        result = session_capsule_configured.nailgun_capsule.content_lifecycle_environments()
        assert lce.id in [capsule_lce['id'] for capsule_lce in result['results']]
        # sync the Capsule
        sync_status = session_capsule_configured.nailgun_capsule.content_sync()
        assert sync_status['result'] == 'success'

    yield {
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
    new_sync_plan = sat_maintain.cli_factory.make_sync_plan(
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
