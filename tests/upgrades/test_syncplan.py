"""Test for Sync-Plan related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SyncPlans

:Assignee: swadeley

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_choice
from nailgun import entities

from robottelo.constants import SYNC_INTERVAL
from robottelo.datafactory import valid_cron_expressions


class TestSyncPlan:
    """
    The test class contains pre-upgrade and post-upgrade scenario to test
    sync_plan migration from pulp to katello
    """

    @pytest.mark.pre_upgrade
    def test_pre_sync_plan_migration(self, request):
        """Pre-upgrade scenario that creates sync plan and assigns repo to sync plan

        :id: preupgrade-badaeec2-d42f-41d5-bd85-4b23d6d5a724

        :steps:
            1. Create Product and Repository
            2. Create Sync Plan
            3. Assign sync plan to product and sync the repo

        :expectedresults: Run sync plan create, get, assign and verify it should pass

        """
        org = entities.Organization(name=f'{request.node.name}_org').create()
        sync_plan = entities.SyncPlan(
            organization=org, name=f'{request.node.name}_syncplan', interval="hourly"
        ).create()
        product = entities.Product(organization=org, name=f'{request.node.name}_prod').create()
        entities.Repository(product=product, name=f'{request.node.name}_repos').create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        product.sync()
        product = product.read()
        assert product.sync_plan.id == sync_plan.id

    @pytest.mark.pre_upgrade
    def test_pre_disabled_sync_plan_logic(self, request):
        """Pre-upgrade scenario that creates a sync plan with both disabled and enabled recurring logic.

        :id: preupgrade-c75bd43d-d868-461a-9fc3-a1fc7dccc77a

        :steps:
            1. Create Product
            2. Create Sync Plan
            3. Assign sync plan to product
            4. Disable the sync plan's recurring logic
            5. Re enable the sync plan

        :expectedresults: Sync plan is created and assigned to a product. The associated recurring
        logic is cancelled and then the plan is re-enabled so that it gets a new recurring logic.

        :BZ: 1887511

        :customerscenario: true
        """
        org = entities.Organization(name=f'{request.node.name}_org').create()
        sync_plan = entities.SyncPlan(
            organization=org, name=f'{request.node.name}_syncplan', interval="weekly"
        ).create()
        product = entities.Product(organization=org, name=f'{request.node.name}_prod').create()
        entities.Repository(product=product, name=f'{request.node.name}_repos').create()
        sync_plan.add_products(data={'product_ids': [product.id]})
        product.sync()
        product = product.read()
        assert product.sync_plan.id == sync_plan.id
        # Note the recurring logic ID for later assert a new one was created
        old_id = sync_plan.foreman_tasks_recurring_logic.id
        # Cancel the recurring logic
        entities.RecurringLogic(id=old_id).read()
        entities.RecurringLogic(id=old_id).cancel()
        # Re-enable the sync plan (it will get a new recurring logic)
        sync_plan.enabled = True
        sync_plan.update(['enabled'])
        sync_plan = sync_plan.read()
        assert sync_plan.enabled
        # Assert a new recurring logic was assigned
        assert sync_plan.foreman_tasks_recurring_logic.id != old_id

    @pytest.mark.post_upgrade(depend_on=test_pre_sync_plan_migration)
    def test_post_sync_plan_migration(self, request, dependent_scenario_name):
        """After upgrade, Sync interval update should work on existing sync plan(created before
        upgrade)

        :id: postupgrade-badaeec2-d42f-41d5-bd85-4b23d6d5a724

        :steps:
            1. Verify sync plan exists and works as earlier
            2. Check the all available sync_interval type update with pre-created sync_plan

        :expectedresults: After upgrade, the sync plan should remain the same with their all
        entities and sync_interval updated with their all supported sync interval type.

        """
        pre_test_name = dependent_scenario_name
        org = entities.Organization().search(query={'search': f'name="{pre_test_name}_org"'})[0]
        request.addfinalizer(org.delete)
        product = entities.Product(organization=org.id).search(
            query={'search': f'name="{pre_test_name}_prod"'}
        )[0]
        request.addfinalizer(product.delete)
        sync_plan = entities.SyncPlan(organization=org.id).search(
            query={'search': f'name="{pre_test_name}_syncplan"'}
        )[0]
        request.addfinalizer(sync_plan.delete)
        assert product.sync_plan.id == sync_plan.id
        assert sync_plan.name == f'{pre_test_name}_syncplan'
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

    @pytest.mark.post_upgrade(depend_on=test_pre_disabled_sync_plan_logic)
    def test_post_disabled_sync_plan_logic(self, request, dependent_scenario_name):
        """Upgrade proceedes without RecurringLogicCancelledExceptionerror.
        After upgrade, Sync interval should still be enabled.

        :id: postupgrade-c75bd43d-d868-461a-9fc3-a1fc7dccc77a

        :steps:
            1. Verify sync plan exists and works.
            2. Check the all available sync_interval type update with pre-created sync_plan.

        :expectedresults: Update proceedes without any errors. After upgrade, the sync plan
        should remain the same with all entities.

        :BZ: 1887511

        :customerscenario: true

        """
        pre_test_name = dependent_scenario_name
        org = entities.Organization().search(query={'search': f'name="{pre_test_name}_org"'})[0]
        request.addfinalizer(org.delete)
        product = entities.Product(organization=org.id).search(
            query={'search': f'name="{pre_test_name}_prod"'}
        )[0]
        request.addfinalizer(product.delete)
        sync_plan = entities.SyncPlan(organization=org.id).search(
            query={'search': f'name="{pre_test_name}_syncplan"'}
        )[0]
        request.addfinalizer(sync_plan.delete)
        assert product.sync_plan.id == sync_plan.id
        assert sync_plan.name == f'{pre_test_name}_syncplan'
        assert sync_plan.interval == 'weekly'
        assert sync_plan.enabled
