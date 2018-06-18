"""Test class for Sync Plan UI

:Requirement: Syncplan

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from datetime import datetime, timedelta
from fauxfactory import gen_string
from nailgun import entities
from random import choice
from robottelo import manifests
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    wait_for_tasks,
    wait_for_syncplan_tasks
)
from robottelo.constants import PRDS, REPOS, REPOSET, SYNC_INTERVAL
from robottelo.datafactory import (
    filtered_datapoint,
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
    tier3,
    tier4,
    upgrade,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_syncplan
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session
from time import sleep


@filtered_datapoint
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

    @staticmethod
    def validate_task_status(repo_id, max_tries=10, repo_backend_id=None):
        """Wait for Pulp and foreman_tasks to complete or timeout

        :param repo_id: Repository Id to identify the correct task
        :param max_tries: Max tries to poll for the task creation
        :param repo_backend_id: Backend identifier of repository to filter the
            pulp tasks
        """
        if repo_backend_id:
            wait_for_syncplan_tasks(repo_backend_id)
        wait_for_tasks(
            search_query='resource_type = Katello::Repository'
                         ' and owner.login = foreman_admin'
                         ' and resource_id = {}'.format(repo_id),
            max_tries=max_tries
        )

    def validate_repo_content(self, repo, content_types, after_sync=True):
        """Check whether corresponding content is present in repository before
        or after synchronization is performed

        :param repo: Repository entity instance to be validated
        :param content_types: List of repository content entities that
            should be validated (e.g. package, erratum, puppet_module)
        :param bool after_sync: Specify whether you perform validation before
            synchronization procedure is happened or after
        """
        repo = repo.read()
        for content in content_types:
            if after_sync:
                self.assertIsNotNone(
                    repo.last_sync, 'Repository unexpectedly was not synced.')
                self.assertGreater(
                    repo.content_counts[content],
                    0,
                    'Repository contains invalid number of content entities.'
                )
            else:
                self.assertIsNone(
                    repo.last_sync, 'Repository was unexpectedly synced.')
                self.assertFalse(
                    repo.content_counts[content],
                    'Repository contains invalid number of content entities.'
                )

    def get_client_datetime(self, browser):
        """Make Javascript call inside of browser session to get exact current
        date and time. In that way, we will be isolated from any issue that can
        happen due different environments where test automation code is
        executing and where browser session is opened. That should help us to
        have successful run for docker containers or separated virtual machines
        When calling .getMonth() you need to add +1 to display the correct
        month. Javascript count always starts at 0, so calling .getMonth() in
        May will return 4 and not 5.

        :param browser: Webdriver browser object.

        :return: Datetime object that contains data for current date and time
            on a client
        """
        script = ('var currentdate = new Date(); return ({0} + "-" + {1} + '
                  '"-" + {2} + " : " + {3} + ":" + {4});').format(
            'currentdate.getFullYear()',
            '(currentdate.getMonth()+1)',
            'currentdate.getDate()',
            'currentdate.getHours()',
            'currentdate.getMinutes()',
        )
        client_datetime = browser.execute_script(script)
        return datetime.strptime(client_datetime, '%Y-%m-%d : %H:%M')

    @tier1
    def test_positive_create_with_name(self):
        """Create Sync Plan with valid name values

        :id: ceb125a4-449a-4a86-a94f-2a28884e3a41

        :expectedresults: Sync Plan is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=gen_string('utf8'),
                        sync_interval=choice(valid_sync_intervals()),
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @tier1
    def test_positive_create_with_description(self):
        """Create Sync Plan with valid desc values

        :id: 6ccd2229-dcc3-4090-9ec9-84fea837c50c

        :expectedresults: Sync Plan is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for desc in generate_strings_list():
                with self.subTest(desc):
                    name = gen_string('utf8')
                    make_syncplan(
                        session,
                        org=self.organization.name,
                        name=name,
                        description=desc,
                        sync_interval=choice(valid_sync_intervals()),
                    )
                    self.assertIsNotNone(self.syncplan.search(name))

    @tier1
    def test_positive_create_with_sync_interval(self):
        """Create Sync Plan with valid sync intervals

        :id: 8916285a-c8d2-415a-b694-c32727e93ac0

        :expectedresults: Sync Plan is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

    @skip_if_bug_open('bugzilla', 1460146)
    @tier2
    def test_positive_create_with_start_time(self):
        """Create Sync plan with specified start time

        :id: a4709229-325c-4027-b4dc-10a226c4d7bf

        :expectedresults: Sync Plan is created with the specified time.

        :BZ: 1460146

        :CaseLevel: Integration
        """
        plan_name = gen_string('alpha')
        with Session(self) as session:
            startdate = (self.get_client_datetime(session.browser)
                         + timedelta(minutes=10))
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            self.assertIsNotNone(self.syncplan.search(plan_name))
            self.syncplan.click(self.syncplan.search(plan_name))
            starttime_text = self.syncplan.wait_until_element(
                locators['sp.fetch_startdate']).text
            # Removed the seconds info as it would be too quick
            # to validate via UI.
            self.assertEqual(
                str(starttime_text).rpartition(':')[0],
                startdate.strftime("%Y/%m/%d %H:%M")
            )

    @skip_if_bug_open('bugzilla', 1460146)
    @tier2
    def test_positive_create_with_start_date(self):
        """Create Sync plan with specified start date

        :id: 020b3aff-7216-4ad6-b95e-8ffaf68cba20

        :expectedresults: Sync Plan is created with the specified date

        :BZ: 1460146

        :CaseLevel: Integration
        """
        plan_name = gen_string('alpha')
        with Session(self) as session:
            startdate = (self.get_client_datetime(session.browser)
                         + timedelta(days=10))
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start date',
                startdate=startdate.strftime("%Y-%m-%d"),
            )
            self.assertIsNotNone(self.syncplan.search(plan_name))
            self.syncplan.click(self.syncplan.search(plan_name))
            startdate_text = self.syncplan.wait_until_element(
                locators['sp.fetch_startdate']).text
            self.assertEqual(
                str(startdate_text).partition(' ')[0],
                startdate.strftime("%Y/%m/%d")
            )

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Sync Plan with invalid names

        :id: 64724669-0289-4e8a-a44d-eb47e094ef18

        :expectedresults: Sync Plan is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: 6d042f9b-82f2-4795-aa48-4603c1698aaa

        :expectedresults: Sync Plan cannot be created with existing name

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        with Session(self) as session:
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
    @upgrade
    def test_positive_search_scoped(self):
        """Test scoped search for different sync plan parameters

        :id: 3a48513e-205d-47a3-978e-79b764cc74d9

        :customerscenario: true

        :expectedresults: Proper Sync Plan is found

        :BZ: 1259374

        :CaseImportance: High
        """
        name = gen_string('alpha')
        start_date = datetime.utcnow() + timedelta(days=10)
        entities.SyncPlan(
            name=name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
            enabled=True,
            sync_date=start_date,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            for query_type, query_value in [
                ('interval', SYNC_INTERVAL['day']),
                ('enabled', 'true'),
            ]:
                self.assertIsNotNone(
                    self.syncplan.search(
                        name,
                        _raw_query='{} = {}'.format(query_type, query_value)
                    )
                )

    @skip_if_bug_open('bugzilla', 1460146)
    @tier1
    def test_positive_update_name(self):
        """Update Sync plan's name

        :id: 6b22468f-6abc-4a63-b283-28c7816a5e86

        :expectedresults: Sync Plan's name is updated

        :BZ: 1460146

        :CaseImportance: Critical
        """
        plan_name = gen_string('alpha')
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            for new_plan_name in generate_strings_list():
                with self.subTest(new_plan_name):
                    self.syncplan.update(plan_name, new_name=new_plan_name)
                    self.assertIsNotNone(self.syncplan.search(new_plan_name))
                    plan_name = new_plan_name  # for next iteration

    @skip_if_bug_open('bugzilla', 1460146)
    @tier1
    @upgrade
    def test_positive_update_interval(self):
        """Update Sync plan's interval

        :id: 35820efd-099e-45dd-8298-77d5f35c26db

        :expectedresults: Sync Plan's interval is updated and no error raised

        :BZ: 1460146, 1387543

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        start_date = datetime.utcnow() + timedelta(days=1)
        entities.SyncPlan(
            name=name,
            interval=SYNC_INTERVAL['day'],
            organization=self.organization,
            enabled=True,
            sync_date=start_date,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            for new_interval in valid_sync_intervals():
                with self.subTest(new_interval):
                    self.syncplan.update(name, new_sync_interval=new_interval)
                    self.assertIsNone(self.user.wait_until_element(
                        common_locators['haserror'], timeout=3))
                    self.syncplan.click(self.syncplan.search(name))
                    # Assert updated sync interval
                    interval_text = self.syncplan.wait_until_element(
                        locators['sp.fetch_interval']).text
                    self.assertEqual(interval_text, new_interval)
                    # Assert that start date was not changed after interval
                    # changed
                    startdate_text = self.syncplan.wait_until_element(
                        locators['sp.fetch_startdate']).text
                    self.assertNotEqual(startdate_text, 'Invalid Date')
                    self.assertIn(
                        start_date.strftime("%Y/%m/%d"), startdate_text)

    @tier2
    def test_positive_update_product(self):
        """Update Sync plan and associate products

        :id: 19bdb36a-ed2a-4bbb-9d8d-9ad9f6a800a2

        :expectedresults: Sync Plan has the associated product

        :CaseLevel: Integration
        """
        strategy, value = locators['sp.prd_select']
        product = entities.Product(organization=self.organization).create()
        plan_name = gen_string('alpha')
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['week'],
            organization=self.organization,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.syncplan.update(
                plan_name, add_products=[product.name])
            self.syncplan.click(self.syncplan.search(plan_name))
            # Assert product is associated with sync plan
            self.syncplan.click(tab_locators['sp.tab_products'])
            element = self.syncplan.wait_until_element(
                (strategy, value % product.name))
            self.assertIsNotNone(element)

    @tier2
    @upgrade
    def test_positive_update_and_disassociate_product(self):
        """Update Sync plan and disassociate products

        :id: 860bd88e-a425-4218-b02c-64402ee8af9d

        :expectedresults: Sync Plan does not have the associated product

        :CaseLevel: Integration
        """
        plan_name = gen_string('utf8')
        strategy, value = locators['sp.prd_select']
        product = entities.Product(organization=self.organization).create()
        entities.SyncPlan(
            name=plan_name,
            interval=SYNC_INTERVAL['week'],
            organization=self.organization,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.syncplan.update(plan_name, add_products=[product.name])
            self.syncplan.click(self.syncplan.search(plan_name))
            self.syncplan.click(tab_locators['sp.tab_products'])
            element = self.syncplan.wait_until_element(
                (strategy, value % product.name))
            self.assertIsNotNone(element)
            # Disassociate the product from sync plan and the selected product
            # should automatically move from 'List/Remove` tab to 'Add' tab
            self.syncplan.update(plan_name, rm_products=[product.name])
            self.syncplan.click(self.syncplan.search(plan_name))
            self.syncplan.click(tab_locators['sp.tab_products'])
            self.syncplan.click(tab_locators['sp.add_prd'])
            element = self.syncplan.wait_until_element(
                (strategy, value % product.name))
            self.assertIsNotNone(element)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete an existing Sync plan

        :id: 81beec05-e38c-48bc-8f01-10cb1e10a3f6

        :expectedresults: Sync Plan is deleted successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: bf01f23f-ba55-4c88-baad-85603fce57a4

        :expectedresults: sync plan should be created successfully

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @tier4
    def test_negative_synchronize_custom_product_past_sync_date(self):
        """Verify product won't get synced immediately after adding association
        with a sync plan which has already been started

        :id: b56fccb9-8f84-4676-a777-b3c6458c909e

        :expectedresults: Repository was not synchronized

        :BZ: 1279539

        :CaseLevel: System
        """
        plan_name = gen_string('alpha')
        product = entities.Product(organization=self.organization).create()
        repo = entities.Repository(product=product).create()
        with Session(self) as session:
            startdate = self.get_client_datetime(session.browser)
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                startdate=startdate.strftime('%Y-%m-%d'),
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            self.syncplan.update(
                plan_name, add_products=[product.name])
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
                self.validate_repo_content(
                    repo,
                    ['erratum', 'package', 'package_group'],
                    max_attempts=5,
                )

    @tier4
    def test_positive_synchronize_custom_product_past_sync_date(self):
        """Create a sync plan with past datetime as a sync date, add a
        custom product and verify the product gets synchronized on the next
        sync occurrence

        :id: d65e91c4-a0b6-4588-a3ff-fe9cd3762556

        :expectedresults: Product is synchronized successfully.

        :BZ: 1279539

        :CaseLevel: System
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        delay = 5 * 60
        plan_name = gen_string('alpha')
        product = entities.Product(organization=self.organization).create()
        repo = entities.Repository(product=product).create()
        with Session(self) as session:
            startdate = (self.get_client_datetime(session.browser)
                         - timedelta(seconds=(interval - delay)))
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                startdate=startdate.strftime('%Y-%m-%d'),
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
                sync_interval='hourly',
            )
            # Associate sync plan with product
            self.syncplan.update(
                plan_name, add_products=[product.name])
            # Verify product has not been synced yet
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was not synced'.format(delay/4, product.name))
            sleep(delay/4)
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
                after_sync=False,
            )
            # Wait until the next recurrence
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was synced'.format(delay, product.name))
            sleep(delay * 3/4)
            # Verify product was synced successfully
            self.validate_task_status(repo.id,
                                      repo_backend_id=repo.backend_identifier
                                      )
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
            )

    @tier4
    def test_positive_synchronize_custom_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one custom
        product with it automatically.

        :id: fdd3b2a2-8d8e-4a18-b6a5-363e8dd5f998

        :expectedresults: Product is synchronized successfully.

        :CaseLevel: System
        """
        delay = 5 * 60  # delay for sync date in seconds
        plan_name = gen_string('alpha')
        product = entities.Product(organization=self.organization).create()
        repo = entities.Repository(product=product).create()
        with Session(self) as session:
            startdate = (self.get_client_datetime(session.browser)
                         + timedelta(seconds=delay))
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
            )
            # Verify product is not synced and doesn't have any content
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
                after_sync=False,
            )
            # Associate sync plan with product
            self.syncplan.update(plan_name, add_products=[product.name])
            # Wait half of expected time
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was not synced'.format(delay/2, product.name))
            sleep(delay / 4)
            # Verify product has not been synced yet
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
                after_sync=False,
            )
            # Wait the rest of expected time
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was synced'.format(delay/2, product.name))
            sleep(delay * 3/4)
            # Verify product was synced successfully
            self.validate_task_status(repo.id,
                                      repo_backend_id=repo.backend_identifier
                                      )
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
            )

    @tier4
    def test_positive_synchronize_custom_products_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync multiple
        custom products with multiple repos automatically.

        :id: 9564e726-59c6-4d24-bb3d-f0ab3c4b26a5

        :expectedresults: Products are synchronized successfully.

        :CaseLevel: System
        """
        delay = 5 * 60  # delay for sync date in seconds
        plan_name = gen_string('alpha')
        products = [
            entities.Product(organization=self.organization).create()
            for _ in range(3)
        ]
        repos = [
            entities.Repository(product=product).create()
            for product in products
            for _ in range(2)
        ]
        with Session(self) as session:
            startdate = (self.get_client_datetime(session.browser)
                         + timedelta(seconds=delay))
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
                with self.assertRaises(AssertionError):
                    self.validate_task_status(repo.id, max_tries=2)
            # Associate sync plan with products
            self.syncplan.update(
                plan_name, add_products=[product.name for product in products])
            # Wait third part of expected time, because it will take a while to
            # verify each product and repository
            self.logger.info('Waiting {0} seconds to check products'
                             ' were not synced'.format(delay/3))
            sleep(delay / 4)
            # Verify products has not been synced yet
            for repo in repos:
                with self.assertRaises(AssertionError):
                    self.validate_task_status(repo.id, max_tries=2)
            # Wait the rest of expected time
            self.logger.info('Waiting {0} seconds to check products'
                             ' were synced'.format(delay*2/3))
            sleep(delay * 3/4)
            # Verify product was synced successfully
            self.validate_task_status(repo.id,
                                      repo_backend_id=repo.backend_identifier
                                      )
            for repo in repos:
                self.validate_repo_content(
                    repo,
                    ['erratum', 'package', 'package_group'],
                )

    @run_in_one_thread
    @tier4
    def test_positive_synchronize_rh_product_past_sync_date(self):
        """Create a sync plan with past datetime as a sync date, add a
        RH product and verify the product gets synchronized on the next sync
        occurrence

        :id: 73a456fb-ad17-4921-b57c-27fc8e432a83

        :expectedresults: Product is synchronized successfully.

        :BZ: 1279539

        :CaseLevel: System
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        delay = 5 * 60
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
        with Session(self) as session:
            startdate = (self.get_client_datetime(session.browser)
                         - timedelta(seconds=(interval - delay)))
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
            # Verify product has not been synced yet
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was not synced'.format(delay/4, PRDS['rhel']))
            sleep(delay/4)
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
                after_sync=False,
            )
            # Wait until the first recurrence
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was synced'.format(delay, PRDS['rhel']))
            sleep(delay * 3/4)
            # Verify product was synced successfully
            self.validate_task_status(repo.id,
                                      repo_backend_id=repo.backend_identifier
                                      )
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
            )

    @run_in_one_thread
    @tier4
    def test_positive_synchronize_rh_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one RH
        product with it automatically.

        :id: 193d0159-d4a7-4f50-b037-7289f4576ade

        :expectedresults: Product is synchronized successfully.

        :CaseLevel: System
        """
        delay = 5 * 60  # delay for sync date in seconds
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
        with Session(self) as session:
            startdate = (self.get_client_datetime(session.browser)
                         + timedelta(seconds=delay))
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
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was not synced'.format(delay/2, PRDS['rhel']))
            sleep(delay / 4)
            # Verify product has not been synced yet
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
                after_sync=False,
            )
            # Wait the rest of expected time
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was synced'.format(delay/2, PRDS['rhel']))
            sleep(delay * 3/4)
            # Verify product was synced successfully
            self.validate_task_status(repo.id,
                                      repo_backend_id=repo.backend_identifier
                                      )
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
            )

    @tier3
    def test_positive_synchronize_custom_product_daily_recurrence(self):
        """Create a daily sync plan with past datetime as a sync date,
        add a custom product and verify the product gets synchronized
        on the next sync occurrence

        :id: c29b99d5-b032-4e70-bb6d-c86f807e6adb

        :expectedresults: Product is synchronized successfully.

        :CaseLevel: System
        """
        delay = 5 * 60
        plan_name = gen_string('alpha')
        product = entities.Product(organization=self.organization).create()
        repo = entities.Repository(product=product).create()
        with Session(self) as session:
            startdate = (self.get_client_datetime(session.browser)
                         - timedelta(days=1) + timedelta(seconds=delay))
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                startdate=startdate.strftime('%Y-%m-%d'),
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
                sync_interval='daily',
            )
            # Associate sync plan with product
            self.syncplan.update(
                plan_name, add_products=[product.name])
            # Verify product has not been synced yet
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was not synced'.format(delay/4, product.name))
            sleep(delay/4)
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
                after_sync=False,
            )
            # Wait until the next recurrence
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was synced'.format(delay, product.name))
            sleep(delay * 3/4)
            # Verify product was synced successfully
            self.validate_task_status(repo.id,
                                      repo_backend_id=repo.backend_identifier
                                      )
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
            )

    @skip_if_bug_open('bugzilla', '1396647')
    @skip_if_bug_open('bugzilla', '1460146')
    @tier3
    def test_positive_synchronize_custom_product_weekly_recurrence(self):
        """Create a daily sync plan with past datetime as a sync date,
        add a custom product and verify the product gets synchronized
        on the next sync occurrence

        :id: eb92b785-384a-4d0d-b8c2-6c900ed8b87e

        :expectedresults: Product is synchronized successfully.

        :BZ: 1396647, 1498793

        :CaseLevel: System
        """
        delay = 5 * 60
        plan_name = gen_string('alpha')
        product = entities.Product(organization=self.organization).create()
        repo = entities.Repository(product=product).create()
        with Session(self) as session:
            startdate = (self.get_client_datetime(session.browser)
                         - timedelta(weeks=1) + timedelta(seconds=delay))
            make_syncplan(
                session,
                org=self.organization.name,
                name=plan_name,
                description='sync plan create with start time',
                startdate=startdate.strftime('%Y-%m-%d'),
                start_hour=startdate.strftime('%H'),
                start_minute=startdate.strftime('%M'),
                sync_interval='weekly',
            )
            # Associate sync plan with product
            self.syncplan.update(
                plan_name, add_products=[product.name])
            # Verify product has not been synced yet
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was not synced'.format(delay/4, product.name))
            sleep(delay/4)
            with self.assertRaises(AssertionError):
                self.validate_task_status(repo.id, max_tries=2)
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
                after_sync=False,
            )
            # Wait until the next recurrence
            self.logger.info('Waiting {0} seconds to check product {1}'
                             ' was synced'.format(delay, product.name))
            sleep(delay * 3/4)
            # Verify product was synced successfully
            self.validate_task_status(repo.id,
                                      repo_backend_id=repo.backend_identifier
                                      )
            self.validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
            )
