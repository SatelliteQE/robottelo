"""Test class for Sync Plan UI"""

from datetime import datetime, timedelta
from fauxfactory import gen_string
from nailgun import entities
from random import randint
from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.constants import PRDS, REPOS, REPOSET, SYNC_INTERVAL
from robottelo.datafactory import (
    datacheck,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    tier4,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_syncplan
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session
from time import sleep


@datacheck
def valid_sync_intervals():
    """Returns a list of valid sync intervals"""
    return [
        SYNC_INTERVAL['hour'],
        SYNC_INTERVAL['day'],
        SYNC_INTERVAL['week'],
    ]


class SyncPlanTestCase(UITestCase):
    """Implements Sync Plan tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(SyncPlanTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    def validate_repo_content(self, product, repo, content_types,
                              after_sync=True, max_attempts=10):
        """Check whether corresponding content is present in repository before
        or after synchronization is performed

        :param product: Name of product, repo of which to validate
        :param repo: Name of repository to be validated
        :param content_types: List of repository content entities that should
            be validated (e.g. packages, errata, package_groups)
        :param bool after_sync: Specify whether you perform validation before
            synchronization procedure is happened or after
        :param int max_attempts: Specify how many times to check for content
            presence. Delay between each attempt is 10 seconds. Default is 10
            attempts.

        """
        self.products.search(product).click()
        for _ in range(max_attempts):
            try:
                for content in content_types:
                    if after_sync:
                        self.assertFalse(
                            self.repository.validate_field(repo, content, '0'))

                    else:
                        self.assertTrue(
                            self.repository.validate_field(repo, content, '0'))
                break
            except AssertionError:
                sleep(30)
        else:
            raise AssertionError(
                'Repository contains invalid number of content entities')

    @tier1
    def test_positive_create_with_name(self):
        """Create Sync Plan with valid name values

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=gen_string('utf8'),
                        sync_interval=valid_sync_intervals()[randint(0, 2)],
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @tier1
    def test_positive_create_with_description(self):
        """Create Sync Plan with valid desc values

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created
        """
        with Session(self.browser) as session:
            for desc in generate_strings_list():
                with self.subTest(desc):
                    name = gen_string('utf8')
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=desc,
                        sync_interval=valid_sync_intervals()[randint(0, 2)],
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @tier1
    def test_positive_create_with_sync_interval(self):
        """Create Sync Plan with valid sync intervals

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created
        """
        with Session(self.browser) as session:
            for interval in valid_sync_intervals():
                with self.subTest(interval):
                    name = gen_string('alphanumeric')
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=name,
                        sync_interval=interval,
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @skip_if_bug_open('bugzilla', 1335133)
    @tier2
    def test_positive_create_with_start_time(self):
        """Create Sync plan with specified start time

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created with the specified time.
        """
        plan_name = gen_string('alpha')
        startdate = datetime.now() + timedelta(minutes=10)
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            self.assertIsNotNone(self.syncplan.search(plan_name))
            self.syncplan.search(plan_name).click()
            starttime_text = self.syncplan.wait_until_element(
                locators['sp.fetch_startdate']).text
            # Removed the seconds info as it would be too quick
            # to validate via UI.
            self.assertEqual(
                str(starttime_text).rpartition(':')[0],
                startdate.strftime("%m/%d/%Y %I:%M")
            )

    @skip_if_bug_open('bugzilla', 1335133)
    @tier2
    def test_positive_create_with_start_date(self):
        """Create Sync plan with specified start date

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan is created with the specified date
        """
        plan_name = gen_string('alpha')
        startdate = datetime.now() + timedelta(days=10)
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start date',
                startdate=startdate.strftime("%Y-%m-%d"),
            )
            self.assertIsNotNone(self.syncplan.search(plan_name))
            self.syncplan.search(plan_name).click()
            startdate_text = self.syncplan.wait_until_element(
                locators['sp.fetch_startdate']).text
            self.assertEqual(
                str(startdate_text).partition(' ')[0],
                startdate.strftime("%m/%d/%Y")
            )

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Sync Plan with invalid names

        @Feature: Content Sync Plan - Negative Create

        @Assert: Sync Plan is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description='invalid name',
                    )
                    self.assertIsNotNone(self.syncplan.wait_until_element(
                        common_locators['common_invalid']))

    @tier1
    def test_negative_create_with_same_name(self):
        """Create Sync Plan with an existing name

        @Feature: Content Sync Plan - Positive Create

        @Assert: Sync Plan cannot be created with existing name
        """
        name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_syncplan(session, org=self.organization.name, name=name)
            self.assertIsNotNone(self.syncplan.search(name))
            make_syncplan(
                session,
                org=self.organization.name,
                name=name,
                description='with same name',
            )
            self.assertIsNotNone(self.syncplan.wait_until_element(
                common_locators['common_invalid']))

    @tier1
    def test_positive_update_name(self):
        """Update Sync plan's name

        @Feature: Content Sync Plan - Positive Update name

        @Assert: Sync Plan's name is updated
        """
        plan_name = gen_string('alpha')
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            for new_plan_name in generate_strings_list():
                with self.subTest(new_plan_name):
                    self.syncplan.update(plan_name, new_name=new_plan_name)
                    self.assertIsNotNone(self.syncplan.search(new_plan_name))
                    plan_name = new_plan_name  # for next iteration

    @tier1
    def test_positive_update_interval(self):
        """Update Sync plan's interval

        @Feature: Content Sync Plan - Positive Update interval

        @Assert: Sync Plan's interval is updated
        """
        name = gen_string('alpha')
        entities.SyncPlan(
            name=name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
            enabled=True,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            for new_interval in valid_sync_intervals():
                with self.subTest(new_interval):
                    self.syncplan.update(name, new_sync_interval=new_interval)
                    self.syncplan.search(name).click()
                    # Assert updated sync interval
                    interval_text = self.syncplan.wait_until_element(
                        locators['sp.fetch_interval']
                    ).text
                    self.assertEqual(interval_text, new_interval)

    @tier2
    def test_positive_update_product(self):
        """Update Sync plan and associate products

        @Feature: Content Sync Plan - Positive Update add products

        @Assert: Sync Plan has the associated product
        """
        strategy, value = locators['sp.prd_select']
        product = entities.Product(organization=self.organization).create()
        plan_name = gen_string('alpha')
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['week'],
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.syncplan.update(
                plan_name, add_products=[product.name])
            self.syncplan.search(plan_name).click()
            # Assert product is associated with sync plan
            self.syncplan.click(tab_locators['sp.tab_products'])
            element = self.syncplan.wait_until_element(
                (strategy, value % product.name))
            self.assertIsNotNone(element)

    @tier2
    def test_positive_update_and_disassociate_product(self):
        """Update Sync plan and disassociate products

        @Feature: Content Sync Plan - Positive Update remove products

        @Assert: Sync Plan does not have the associated product
        """
        plan_name = gen_string('utf8')
        strategy, value = locators['sp.prd_select']
        product = entities.Product(organization=self.organization).create()
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['week'],
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.syncplan.update(plan_name, add_products=[product.name])
            self.syncplan.search(plan_name).click()
            self.syncplan.click(tab_locators['sp.tab_products'])
            element = self.syncplan.wait_until_element(
                (strategy, value % product.name))
            self.assertIsNotNone(element)
            # Dis-associate the product from sync plan and the selected product
            # should automatically move from 'List/Remove` tab to 'Add' tab
            self.syncplan.update(plan_name, rm_products=[product.name])
            self.syncplan.search(plan_name).click()
            self.syncplan.click(tab_locators['sp.tab_products'])
            self.syncplan.click(tab_locators['sp.add_prd'])
            element = self.syncplan.wait_until_element(
                (strategy, value % product.name))
            self.assertIsNotNone(element)

    @tier1
    def test_positive_delete(self):
        """Delete an existing Sync plan

        @Feature: Content Sync Plan - Positive Delete

        @Assert: Sync Plan is deleted successfully
        """
        with Session(self.browser) as session:
            for plan_name in generate_strings_list():
                with self.subTest(plan_name):
                    entities.SyncPlan(
                        name=plan_name,
                        interval=SYNC_INTERVAL['day'],
                        organization=self.organization,
                    ).create()
                    session.nav.go_to_select_org(self.organization.name)
                    self.syncplan.delete(plan_name)

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_ostree_sync_plan(self):
        """Create a sync plan for ostree contents.

        @Feature: ostree sync plan

        @Assert: sync plan should be created successfully

        @Status: Manual
        """

    # This Bugzilla bug is private. It is impossible to fetch info about it.
    @stubbed('Unstub when BZ1279539 is fixed')
    @tier4
    def test_negative_synchronize_custom_product_current_sync_date(self):
        """Verify product won't get synced immediately after adding association
        with a sync plan which has already been started

        @Feature: Sync Plan

        @Assert: Repository was not synchronized

        @BZ: 1279539
        """
        plan_name = gen_string('alpha')
        product = entities.Product(organization=self.organization).create()
        repo = entities.Repository(product=product).create()
        startdate = datetime.now()
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            self.syncplan.update(
                plan_name, add_products=[product.name])
            with self.assertRaises(AssertionError):
                self.validate_repo_content(
                    product.name,
                    repo.name,
                    ['errata', 'package_groups', 'packages'],
                    max_attempts=5,
                )

    # This Bugzilla bug is private. It is impossible to fetch info about it.
    @stubbed('Unstub when BZ1279539 is fixed')
    @tier4
    def test_positive_synchronize_custom_product_current_sync_date(self):
        """Create a sync plan with current datetime as a sync date, add a
        custom product and verify the product gets synchronized on the next
        sync occurrence

        @Assert: Product is synchronized successfully.

        @Feature: SyncPlan

        @BZ: 1279539
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        plan_name = gen_string('alpha')
        product = entities.Product(organization=self.organization).create()
        repo = entities.Repository(product=product).create()
        startdate = datetime.now()
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
                sync_interval='hourly',
            )
            # Associate sync plan with product
            self.syncplan.update(
                plan_name, add_products=[product.name])
            # Wait half of expected time
            sleep(interval / 2)
            # Verify product has not been synced yet
            self.validate_repo_content(
                product.name, repo.name,
                ['errata', 'package_groups', 'packages'],
                after_sync=False,
            )
            # Wait the rest of expected time
            sleep(interval / 2)
            # Verify product was synced successfully
            self.validate_repo_content(
                product.name,
                repo.name,
                ['errata', 'package_groups', 'packages'],
            )

    @tier4
    def test_positive_synchronize_custom_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one custom
        product with it automatically.

        @Assert: Product is synchronized successfully.

        @Feature: SyncPlan
        """
        delay = 10 * 60  # delay for sync date in seconds
        plan_name = gen_string('alpha')
        product = entities.Product(organization=self.organization).create()
        repo = entities.Repository(product=product).create()
        startdate = datetime.now() + timedelta(seconds=delay)
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            # Verify product is not synced and doesn't have any content
            self.validate_repo_content(
                product.name,
                repo.name,
                ['errata', 'package_groups', 'packages'],
                after_sync=False,
            )
            # Associate sync plan with product
            self.syncplan.update(plan_name, add_products=[product.name])
            # Wait half of expected time
            sleep(delay/2)
            # Verify product has not been synced yet
            self.validate_repo_content(
                product.name,
                repo.name,
                ['errata', 'package_groups', 'packages'],
                after_sync=False,
            )
            # Wait the rest of expected time
            sleep(delay/2)
            # Verify product was synced successfully
            self.validate_repo_content(
                product.name,
                repo.name,
                ['errata', 'package_groups', 'packages'],
            )

    @tier4
    def test_positive_synchronize_custom_products_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync multiple
        custom products with multiple repos automatically.

        @Assert: Products are synchronized successfully.

        @Feature: SyncPlan
        """
        delay = 10 * 60  # delay for sync date in seconds
        plan_name = gen_string('alpha')
        products = [
            entities.Product(organization=self.organization).create()
            for _ in range(randint(3, 5))
        ]
        repos = [
            entities.Repository(product=product).create()
            for product in products
            for _ in range(randint(2, 3))
        ]
        startdate = datetime.now() + timedelta(seconds=delay)
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            #  Verify products have not been synced yet
            for repo in repos:
                self.validate_repo_content(
                    repo.product.read().name,
                    repo.name,
                    ['errata', 'package_groups', 'packages'],
                    after_sync=False,
                )
            # Associate sync plan with products
            self.syncplan.update(
                plan_name, add_products=[product.name for product in products])
            # Wait half of expected time
            sleep(delay/2)
            # Verify products has not been synced yet
            for repo in repos:
                self.validate_repo_content(
                    repo.product.read().name,
                    repo.name,
                    ['errata', 'package_groups', 'packages'],
                    after_sync=False,
                )
            # Wait the rest of expected time
            sleep(delay/2)
            # Verify product was synced successfully
            for repo in repos:
                self.validate_repo_content(
                    repo.product.read().name,
                    repo.name,
                    ['errata', 'package_groups', 'packages'],
                )

    # This Bugzilla bug is private. It is impossible to fetch info about it.
    @run_in_one_thread
    @stubbed('Unstub when BZ1279539 is fixed')
    @tier4
    def test_positive_synchronize_rh_product_current_sync_date(self):
        """Create a sync plan with current datetime as a sync date, add a
        RH product and verify the product gets synchronized on the next sync
        occurrence

        @Assert: Product is synchronized successfully.

        @Feature: SyncPlan

        @BZ: 1279539
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        plan_name = gen_string('alpha')
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            entities.Subscription().upload(
                data={'organization_id': org.id},
                files={'content': manifest.content},
            )
        repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        repo = entities.Repository(id=repo_id).read()
        startdate = datetime.now()
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=org.name,
                name=plan_name,
                description='sync plan create with start time',
                interval=u'hourly',
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            # Associate sync plan with product
            self.syncplan.update(
                plan_name, add_products=[PRDS['rhel']])
            # Wait half of expected time
            sleep(interval / 2)
            # Verify product has not been synced yet
            self.validate_repo_content(
                PRDS['rhel'],
                repo.name,
                ['errata', 'package_groups', 'packages'],
                after_sync=False,
            )
            # Wait the rest of expected time
            sleep(interval / 2)
            # Verify product was synced successfully
            self.validate_repo_content(
                PRDS['rhel'],
                repo.name,
                ['errata', 'package_groups', 'packages'],
            )

    @run_in_one_thread
    @tier4
    def test_positive_synchronize_rh_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one RH
        product with it automatically.

        @Assert: Product is synchronized successfully.

        @Feature: SyncPlan
        """
        delay = 10 * 60  # delay for sync date in seconds
        plan_name = gen_string('alpha')
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            entities.Subscription().upload(
                data={'organization_id': org.id},
                files={'content': manifest.content},
            )
        repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        repo = entities.Repository(id=repo_id).read()
        startdate = datetime.now() + timedelta(seconds=delay)
        with Session(self.browser) as session:
            make_syncplan(
                session,
                org=org.name,
                name=plan_name,
                description='sync plan create with start time',
                interval=u'hourly',
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            # Associate sync plan with product
            self.syncplan.update(
                plan_name, add_products=[PRDS['rhel']])
            # Wait half of expected time
            sleep(delay / 2)
            # Verify product has not been synced yet
            self.validate_repo_content(
                PRDS['rhel'],
                repo.name,
                ['errata', 'package_groups', 'packages'],
                after_sync=False,
            )
            # Wait the rest of expected time
            sleep(delay / 2)
            # Verify product was synced successfully
            self.validate_repo_content(
                PRDS['rhel'],
                repo.name,
                ['errata', 'package_groups', 'packages'],
            )
