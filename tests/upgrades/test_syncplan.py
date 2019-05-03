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
from requests.exceptions import HTTPError

from nailgun import entities
from robottelo.constants import SYNC_INTERVAL
from robottelo.datafactory import valid_cron_expressions
from robottelo.decorators import skip_if_bug_open
from robottelo.test import APITestCase
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict, get_entity_data


class ScenarioSyncPlan(APITestCase):
    """The test class contains pre-upgrade and post-upgrade scenarios to test
    sync_plan migration from pulp to katello

    Test Steps:

    1. Before Satellite upgrade, Create Sync plan and assign repo to sync plan
    2. Upgrade satellite.
    3. Post upgrade, verify the sync plan exists and performs same as pre-upgrade.

    """
    @skip_if_bug_open('bugzilla', 1646988)
    @pre_upgrade
    def test_pre_sync_plan_migration(self):
        """Pre-upgrade scenario that creates sync plan and assigns repo to sync plan

        :id: badaeec2-d42f-41d5-bd85-4b23d6d5a724

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
        self.assertEqual(product.sync_plan.id, sync_plan.id)
        sync_plan = sync_plan.read()
        scenario_dict = {self.__class__.__name__: {
            'sync_plan_name': sync_plan_name,
            'interval': sync_plan.interval,
            'sync_date': sync_plan.sync_date,
            'product_id': product.id,
            'sync_plan_id': sync_plan.id,
            'org_id': org.id
        }}
        create_dict(scenario_dict)

    @skip_if_bug_open('bugzilla', 1646988)
    @post_upgrade(depend_on=test_pre_sync_plan_migration)
    def test_post_sync_plan_migration(self):
        """Post-upgrade scenario that tests existing sync plans are working as
        expected after satellite upgrade with migrating from pulp to katello

        :id: badaeec2-d42f-41d5-bd85-4b23d6d5a724

        :steps:
            1. Verify sync plan exists and works as earlier

        :expectedresults: Post Upgrade, Sync plans exists and works as earlier.

         """
        entity_data = get_entity_data(self.__class__.__name__)
        org = entities.Organization(id=entity_data.get('org_id'))
        product = entities.Product(id=entity_data.get("product_id")).read()
        sync_plan = entities.SyncPlan(id=entity_data.get("sync_plan_id"),
                                      organization=org).read()
        self.assertEqual(product.sync_plan.id, sync_plan.id)
        self.assertEqual(sync_plan.name, entity_data.get("sync_plan_name"))
        self.assertEqual(sync_plan.interval, entity_data.get("interval"))
        self.assertEqual(sync_plan.sync_date, entity_data.get("sync_date"))
        # checking sync plan update on upgraded satellite
        sync_plan.interval = SYNC_INTERVAL['custom']
        sync_plan.cron_expression = gen_choice(valid_cron_expressions())
        self.assertEqual(
            sync_plan.update(['interval', 'cron_expression']).interval,
            SYNC_INTERVAL['custom']
        )
        # checking sync plan delete on upgraded satellite
        sync_plan.delete()
        product = product.read()
        self.assertIsNone(product.sync_plan)
        with self.assertRaises(HTTPError):
            sync_plan.read()
