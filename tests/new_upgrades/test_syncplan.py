"""Test for Sync-Plan related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: SyncPlans

:Team: Artemis

:CaseImportance: High

"""

from datetime import date

from box import Box
from fauxfactory import gen_alpha, gen_choice
import pytest

from robottelo.config import settings
from robottelo.constants import SYNC_INTERVAL
from robottelo.utils.datafactory import valid_cron_expressions
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def sync_plan_migration_setup(sync_plan_upgrade_shared_satellite, upgrade_action):
    """Creates sync plan and assigns repo to sync plan

    :steps:
        1. Create Product and Repository
        2. Create Sync Plan
        3. Assign sync plan to product and sync the repo

    :expectedresults: Run sync plan create, get, assign and verify it should pass
    """
    target_sat = sync_plan_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'sync_plan_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        sync_plan = target_sat.api.SyncPlan(
            organization=org,
            name=f'{test_name}_syncplan',
            interval="hourly",
            sync_date=date.today().isoformat(),
            enabled=1,
        ).create()
        product = target_sat.api.Product(organization=org, name=f'{test_name}_prod').create()
        target_sat.api.Repository(
            product=product.id,
            name=f'{test_name}_repo',
            url=settings.repos.yum_1.url,
            content_type='yum',
        ).create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        product.sync()
        product = product.read()
        assert product.sync_plan.id == sync_plan.id
        test_data = Box(
            {
                'satellite': target_sat,
                'org': org,
                'product': product,
                'sync_plan': sync_plan,
                'test_name': test_name,
            }
        )
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.sync_plan_upgrades
def test_post_sync_plan_migration(request, sync_plan_migration_setup):
    """After upgrade, sync interval update should work on existing sync plan(created before
    upgrade)

    :id: badaeec2-d42f-41d5-bd85-4b23d6d5a724

    :steps:
        1. Verify sync plan exists and works as earlier
        2. Check the all available sync_interval type update with pre-created sync_plan

    :expectedresults: After upgrade, the sync plan should remain the same with their all
        target_sat.api and sync_interval updated with their all supported sync interval type.
    """
    test_name = sync_plan_migration_setup.test_name
    org = sync_plan_migration_setup.org
    product = sync_plan_migration_setup.product
    sync_plan = sync_plan_migration_setup.sync_plan
    request.addfinalizer(org.delete)
    request.addfinalizer(product.delete)
    request.addfinalizer(sync_plan.delete)
    assert product.sync_plan.id == sync_plan.id
    assert sync_plan.name == f'{test_name}_syncplan'
    assert sync_plan.interval == 'hourly'
    for sync_interval in SYNC_INTERVAL:
        if sync_interval == "custom":
            sync_plan.interval = SYNC_INTERVAL['custom']
            sync_plan.cron_expression = gen_choice(valid_cron_expressions())
            sync_plan.update(['interval', 'cron_expression'])
        else:
            sync_plan.interval = SYNC_INTERVAL[sync_interval]
            sync_plan.update(['interval'])
        sync_plan = sync_plan.read()
        assert sync_plan.interval == SYNC_INTERVAL[sync_interval]
