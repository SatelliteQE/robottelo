"""Test class for Sync Plan UI

:Requirement: Syncplan

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import time

from datetime import timedelta
from fauxfactory import gen_choice
from nailgun import entities
from pytest import raises
from robottelo import manifests
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    wait_for_tasks,
    wait_for_syncplan_tasks
)
from robottelo.constants import PRDS, REPOS, REPOSET, SYNC_INTERVAL
from robottelo.datafactory import (
    gen_string,
    valid_cron_expressions
)
from robottelo.decorators import (
    fixture,
    skip_if_bug_open,
    tier2,
    tier3,
    upgrade,
)


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


def validate_repo_content(repo, content_types, after_sync=True):
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
            assert repo.last_sync, 'Repository was not synced.'
            assert repo.content_counts[content] > 0, (
                'Repository contains invalid number of content entities.')
        else:
            assert not repo.last_sync, 'Repository was unexpectedly synced.'
            assert repo.content_counts[content] == 0, (
                'Repository contains invalid number of content entities.')


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@tier2
def test_positive_end_to_end(session):
    """Perform end to end scenario for sync plan component

    :id: 39c140a6-ca65-4b6a-a640-4a023a2f0f12

    :expectedresults: All CRUD actions for component finished successfully

    :CaseLevel: Integration
    """
    plan_name = gen_string('alpha')
    description = gen_string('alpha')
    new_description = gen_string('alpha')
    with session:
        startdate = (
                session.browser.get_client_datetime() + timedelta(minutes=10))
        # Create new sync plan and check all values in entity that was created
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['day'],
            'description': description,
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        syncplan_values = session.syncplan.read(plan_name)
        assert syncplan_values['details']['name'] == plan_name
        assert syncplan_values['details']['description'] == description
        assert syncplan_values['details']['enabled'] == 'Yes'
        assert syncplan_values['details']['interval'] == SYNC_INTERVAL['day']
        time = syncplan_values['details']['date_time'].rpartition(':')[0]
        assert time == startdate.strftime("%Y/%m/%d %H:%M")
        # Update sync plan with new description
        session.syncplan.update(
            plan_name,
            {'details.description': new_description}
        )
        syncplan_values = session.syncplan.read(plan_name)
        assert syncplan_values['details']['description'] == new_description
        # Delete sync plan
        session.syncplan.delete(plan_name)
        assert not session.syncplan.search(plan_name)


@tier2
def test_positive_end_to_end_custom_cron(session):
    """Perform end to end scenario for sync plan component with custom cron

    :id: 48c88529-6318-47b0-97bc-eb46aae0294a

    :expectedresults: All CRUD actions for component finished successfully

    :CaseLevel: Integration
    """
    plan_name = gen_string('alpha')
    description = gen_string('alpha')
    cron_expression = gen_choice(valid_cron_expressions())
    with session:
        startdate = (
                session.browser.get_client_datetime() + timedelta(minutes=10))
        # Create new sync plan and check all values in entity that was created
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['custom'],
            'description': description,
            'cron_expression': cron_expression,
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        syncplan_values = session.syncplan.read(plan_name)
        assert syncplan_values['details']['interval'] == SYNC_INTERVAL['custom']
        assert syncplan_values['details']['cron_expression'] == cron_expression
        assert syncplan_values['details']['recurring_logic'].isdigit()
        time = syncplan_values['details']['date_time'].rpartition(':')[0]
        assert time == startdate.strftime("%Y/%m/%d %H:%M")
        # Update sync plan with new description
        session.syncplan.update(
            plan_name,
            {'details.interval': SYNC_INTERVAL['day']
             }
        )
        syncplan_values = session.syncplan.read(plan_name)
        assert syncplan_values['details']['interval'] == SYNC_INTERVAL['day']
        assert not syncplan_values['details']['cron_expression']
        # Delete sync plan
        session.syncplan.delete(plan_name)
        assert not session.syncplan.search(plan_name)


@tier3
def test_negative_synchronize_custom_product_past_sync_date(
        session, module_org):
    """Verify product won't get synced immediately after adding association
    with a sync plan which has already been started

    :id: b56fccb9-8f84-4676-a777-b3c6458c909e

    :expectedresults: Repository was not synchronized

    :BZ: 1279539

    :CaseLevel: System
    """
    plan_name = gen_string('alpha')
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    with session:
        startdate = session.browser.get_client_datetime()
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['day'],
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, product.name)
        with raises(AssertionError) as context:
            validate_task_status(repo.id, max_tries=2)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert repo_values['content_counts'][repo_type] == '0'


@tier3
def test_positive_synchronize_custom_product_past_sync_date(
        session, module_org):
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
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    with session:
        startdate = (
            session.browser.get_client_datetime()
            - timedelta(seconds=(interval - delay))
        )
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['hour'],
            'description': 'sync plan create with start time',
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, product.name)
        # Waiting part of delay and check that product was not synced
        time.sleep(delay/4)
        with raises(AssertionError) as context:
            validate_task_status(repo.id, max_tries=2)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Waiting part of delay that left and check that product was synced
        time.sleep(delay * 3/4)
        validate_task_status(repo.id, repo_backend_id=repo.backend_identifier)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'])
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert int(repo_values['content_counts'][repo_type]) > 0


@tier3
@skip_if_bug_open('bugzilla', 1655595)
def test_positive_synchronize_custom_product_future_sync_date(
        session, module_org):
    """Create a sync plan with sync date in a future and sync one custom
    product with it automatically.

    :id: fdd3b2a2-8d8e-4a18-b6a5-363e8dd5f998

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System
    """
    delay = 5 * 60  # delay for sync date in seconds
    plan_name = gen_string('alpha')
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    with session:
        startdate = (
            session.browser.get_client_datetime() + timedelta(seconds=delay))
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['week'],
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, product.name)
        # Waiting part of delay and check that product was not synced
        time.sleep(delay/2)
        with raises(AssertionError) as context:
            validate_task_status(repo.id, max_tries=2)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert repo_values['content_counts'][repo_type] == '0'
        # Waiting part of delay that left and check that product was synced
        time.sleep(delay/2)
        validate_task_status(repo.id, repo_backend_id=repo.backend_identifier)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'])
        session.syncplan.search(plan_name)
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert int(repo_values['content_counts'][repo_type]) > 0


@tier3
@skip_if_bug_open('bugzilla', 1655595)
def test_positive_synchronize_custom_products_future_sync_date(
        session, module_org):
    """Create a sync plan with sync date in a future and sync multiple
    custom products with multiple repos automatically.

    :id: 9564e726-59c6-4d24-bb3d-f0ab3c4b26a5

    :expectedresults: Products are synchronized successfully.

    :CaseLevel: System
    """
    delay = 5 * 60  # delay for sync date in seconds
    plan_name = gen_string('alpha')
    products = [
        entities.Product(organization=module_org).create()
        for _ in range(3)
    ]
    repos = [
        entities.Repository(product=product).create()
        for product in products
        for _ in range(2)
    ]
    with session:
        startdate = (
            session.browser.get_client_datetime() + timedelta(seconds=delay))
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['week'],
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(
            plan_name, [product.name for product in products])
        time.sleep(delay / 4)
        # Verify that repositories in products have not been synced yet
        for repo in repos:
            with raises(AssertionError) as context:
                validate_task_status(repo.id, max_tries=2)
            assert 'No task was found using query' in str(context.value)
            validate_repo_content(
                repo,
                ['erratum', 'package', 'package_group'],
                after_sync=False
            )
        # Waiting part of delay that left and check that products were synced
        time.sleep(delay * 3 / 4)
        for repo in repos:
            validate_task_status(
                repo.id, repo_backend_id=repo.backend_identifier)
            validate_repo_content(
                repo, ['erratum', 'package', 'package_group'])


@tier3
@upgrade
@skip_if_bug_open('bugzilla', 1655595)
def test_positive_synchronize_rh_product_future_sync_date(session):
    """Create a sync plan with sync date in a future and sync one RH
    product with it automatically.

    :id: 193d0159-d4a7-4f50-b037-7289f4576ade

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System
    """
    delay = 5 * 60  # delay for sync date in seconds
    plan_name = gen_string('alpha')
    org = entities.Organization().create()
    manifests.upload_manifest_locked(org.id)
    repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    repo = entities.Repository(id=repo_id).read()
    with session:
        session.organization.select(org_name=org.name)
        startdate = (
            session.browser.get_client_datetime() + timedelta(seconds=delay))
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['week'],
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, PRDS['rhel'])
        # Waiting part of delay and check that product was not synced
        time.sleep(delay / 4)
        with raises(AssertionError) as context:
            validate_task_status(repo.id, max_tries=2)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Waiting part of delay that left and check that product was synced
        time.sleep(delay * 3 / 4)
        validate_task_status(repo.id, repo_backend_id=repo.backend_identifier)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'])
        repo_values = session.repository.read(PRDS['rhel'], repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert int(repo_values['content_counts'][repo_type]) > 0


@tier3
def test_positive_synchronize_custom_product_daily_recurrence(
        session, module_org):
    """Create a daily sync plan with past datetime as a sync date,
    add a custom product and verify the product gets synchronized
    on the next sync occurrence

    :id: c29b99d5-b032-4e70-bb6d-c86f807e6adb

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System
    """
    delay = 5 * 60
    plan_name = gen_string('alpha')
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    with session:
        startdate = (
            session.browser.get_client_datetime()
            - timedelta(days=1) + timedelta(seconds=delay)
        )
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['day'],
            'description': 'sync plan create with start time',
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, product.name)
        # Waiting part of delay and check that product was not synced
        time.sleep(delay/4)
        with raises(AssertionError) as context:
            validate_task_status(repo.id, max_tries=2)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Waiting part of delay that left and check that product was synced
        time.sleep(delay * 3/4)
        validate_task_status(repo.id, repo_backend_id=repo.backend_identifier)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'])
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert int(repo_values['content_counts'][repo_type]) > 0


@tier3
def test_positive_synchronize_custom_product_weekly_recurrence(
        session, module_org):
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
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    with session:
        startdate = (
                session.browser.get_client_datetime()
                - timedelta(weeks=1) + timedelta(seconds=delay)
        )
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['week'],
            'description': 'sync plan create with start time',
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, product.name)
        # Waiting part of delay and check that product was not synced
        time.sleep(delay / 4)
        with raises(AssertionError) as context:
            validate_task_status(repo.id, max_tries=2)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Waiting part of delay that left and check that product was synced
        time.sleep(delay * 3 / 4)
        validate_task_status(repo.id, repo_backend_id=repo.backend_identifier)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'])
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert int(repo_values['content_counts'][repo_type]) > 0


@tier3
def test_positive_synchronize_custom_product_custom_cron_real_time(
        session, module_org):
    """Create a sync plan with real datetime as a sync date,
    add a custom product and verify the product gets synchronized
    on the next sync occurrence based on custom cron interval

    :id: c551ef9a-6e5a-435a-b24d-e86de203a2bb

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System
    """
    plan_name = gen_string('alpha')
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    with session:
        start_date = session.browser.get_client_datetime()
        next_sync = (3 * 60)
        # forming cron expression sync repo after 3 min
        expected_next_run_time = start_date + timedelta(seconds=next_sync)
        cron_expression = '{} * * * *'.format(expected_next_run_time.minute)
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['custom'],
            'cron_expression': cron_expression,
            'description': 'sync plan create with start time',
            'date_time.start_date': start_date.strftime("%Y-%m-%d"),
            'date_time.hours': start_date.strftime('%H'),
            'date_time.minutes': start_date.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, product.name)
        with raises(AssertionError) as context:
            validate_task_status(repo.id, max_tries=2)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Waiting part of delay that left and check that product was synced
        time.sleep(next_sync)
        validate_task_status(repo.id, repo_backend_id=repo.backend_identifier)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'])
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert int(repo_values['content_counts'][repo_type]) > 0
        # Delete sync plan
        session.syncplan.delete(plan_name)
        assert not session.syncplan.search(plan_name)


@tier3
def test_positive_synchronize_custom_product_custom_cron_past_sync_date(
        session, module_org):
    """Create a sync plan with past datetime as a sync date,
    add a custom product and verify the product gets synchronized
    on the next sync occurrence based on custom cron interval

    :id: 4d9ed0bf-a63c-44de-846d-7cf302273bcc

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System
    """
    interval = 60 * 60  # 'hourly' sync interval in seconds
    delay = 5 * 60
    plan_name = gen_string('alpha')
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    with session:
        startdate = (
            session.browser.get_client_datetime()
            - timedelta(seconds=(interval - delay))
        )
        session.syncplan.create({
            'name': plan_name,
            'interval': SYNC_INTERVAL['custom'],
            'cron_expression': '*/5 * * * *',
            'description': 'sync plan create with start time',
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, product.name)
        # Waiting part of delay and check that product was not synced
        time.sleep(delay/4)
        with raises(AssertionError) as context:
            validate_task_status(repo.id, max_tries=2)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(
            repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Waiting part of delay that left and check that product was synced
        time.sleep(delay * 3/4)
        validate_task_status(repo.id, repo_backend_id=repo.backend_identifier)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'])
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert int(repo_values['content_counts'][repo_type]) > 0
        # Delete sync plan
        session.syncplan.delete(plan_name)
        assert not session.syncplan.search(plan_name)
