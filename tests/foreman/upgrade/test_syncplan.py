"""Test for Sync-Plan related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_choice, gen_string
from pytest import raises
from requests.exceptions import HTTPError

from nailgun import entities
from robottelo.constants import SYNC_INTERVAL
from robottelo.datafactory import valid_cron_expressions
from upgrade_tests import post_upgrade, pre_upgrade


@pre_upgrade
def test_pre_sync_plan_migration(save_test_data):
    """Pre-upgrade scenario that creates sync plan and assigns repo to sync plan

    :id: 0e8e993a-43d2-41e3-b7e3-72f9d5578270

    :steps:
        1. Create Product and Repository
        2. Create Sync Plan
        3. Assign sync plan to product and sync the repo

    :expectedresults: Run sync plan create, get, assign and verify it should pass

     """
    org = entities.Organization().create()
    sync_plan_name = "Test_Sync_plan_Migration_{0}".format(gen_string('alpha'))
    sync_plan = entities.SyncPlan(
        organization=org,
        name=sync_plan_name).create()
    product = entities.Product(organization=org).create()
    entities.Repository(product=product).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    product.sync()
    product = product.read()
    assert product.sync_plan.id == sync_plan.id
    sync_plan = sync_plan.read()
    save_test_data({
        'sync_plan_name': sync_plan_name,
        'interval': sync_plan.interval,
        'sync_date': sync_plan.sync_date,
        'product_id': product.id,
        'sync_plan_id': sync_plan.id,
        'org_id': org.id
    })


@post_upgrade(depend_on=test_pre_sync_plan_migration)
def test_post_sync_plan_migration(pre_upgrade_data):
    """Post-upgrade scenario that tests existing sync plans are working as
    expected after satellite upgrade with migrating from pulp to katello

    :id: 61f65f5d-351c-4aa4-83dc-71afae5dc1e0

    :steps:
        1. Verify sync plan exists and works as earlier

    :expectedresults: Post Upgrade, Sync plans exists and works as earlier.

     """
    org = entities.Organization(id=pre_upgrade_data.get('org_id'))
    product = entities.Product(id=pre_upgrade_data.get("product_id")).read()
    sync_plan = entities.SyncPlan(id=pre_upgrade_data.get("sync_plan_id"),
                                  organization=org).read()
    assert product.sync_plan.id == sync_plan.id
    assert sync_plan.name == pre_upgrade_data.get("sync_plan_name")
    assert sync_plan.interval == pre_upgrade_data.get("interval")
    assert sync_plan.sync_date == pre_upgrade_data.get("sync_date")
    # checking sync plan update on upgraded satellite
    sync_plan.interval = SYNC_INTERVAL['custom']
    sync_plan.cron_expression = gen_choice(valid_cron_expressions())
    assert (sync_plan.update(['interval', 'cron_expression']).interval
            == SYNC_INTERVAL['custom'])
    # checking sync plan delete on upgraded satellite
    sync_plan.delete()
    product = product.read()
    assert product.sync_plan is None
    with raises(HTTPError):
        sync_plan.read()
