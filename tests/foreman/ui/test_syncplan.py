"""Test class for Sync Plan UI

:Requirement: Syncplan

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SyncPlans

:Assignee: sbible

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import time
from datetime import datetime
from datetime import timedelta

import pytest
from fauxfactory import gen_choice
from nailgun import entities

from robottelo.api.utils import wait_for_tasks
from robottelo.constants import SYNC_INTERVAL
from robottelo.datafactory import gen_string
from robottelo.datafactory import valid_cron_expressions


def validate_task_status(repo_id, org_id, max_tries=10):
    """Wait for foreman_tasks to complete or timeout

    :param repo_id: Repository Id to identify the correct task
    :param max_tries: Max tries to poll for the task creation
    :param org_id: Org ID to ensure valid check on busy Satellite
    """
    wait_for_tasks(
        search_query='Actions::Katello::Repository::Sync'
        f' and organization_id = {org_id}'
        f' and resource_id = {repo_id}',
        max_tries=max_tries,
        search_rate=10,
    )


def validate_repo_content(repo, content_types, after_sync=True):
    """Check whether corresponding content is present in repository before
    or after synchronization is performed

    :param repo: Repository entity instance to be validated
    :param content_types: List of repository content entities that
        should be validated (e.g. package, erratum)
    :param bool after_sync: Specify whether you perform validation before
        synchronization procedure is happened or after
    """
    repo = repo.read()
    for content in content_types:
        if after_sync:
            assert repo.last_sync, 'Repository was not synced.'
            assert (
                repo.content_counts[content] > 0
            ), 'Repository contains invalid number of content entities.'
        else:
            assert not repo.last_sync, 'Repository was unexpectedly synced.'
            assert (
                repo.content_counts[content] == 0
            ), 'Repository contains invalid number of content entities.'


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.mark.tier2
def test_positive_end_to_end(session, module_org):
    """Perform end to end scenario for sync plan component

    :id: 39c140a6-ca65-4b6a-a640-4a023a2f0f12

    :expectedresults: All CRUD actions for component finished successfully

    :customerscenario: true

    :CaseLevel: Integration

    :BZ: 1693795
    """
    plan_name = gen_string('alpha')
    description = gen_string('alpha')
    new_description = gen_string('alpha')
    with session:
        # workaround: force session.browser to point to browser object on next line
        session.contenthost.read_all('current_user')
        startdate = session.browser.get_client_datetime() + timedelta(minutes=10)
        # Create new sync plan and check all values in entity that was created
        session.syncplan.create(
            {
                'name': plan_name,
                'interval': SYNC_INTERVAL['day'],
                'description': description,
                'date_time.start_date': startdate.strftime("%Y-%m-%d"),
                'date_time.hours': startdate.strftime('%H'),
                'date_time.minutes': startdate.strftime('%M'),
            }
        )
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        syncplan_values = session.syncplan.read(plan_name)
        assert syncplan_values['details']['name'] == plan_name
        assert syncplan_values['details']['description'] == description
        assert syncplan_values['details']['enabled'] == 'Yes'
        assert syncplan_values['details']['interval'] == SYNC_INTERVAL['day']
        time = syncplan_values['details']['date_time'].rpartition(':')[0]
        assert time == startdate.strftime("%B %-d, %Y, %I")
        # Update sync plan with new description
        session.syncplan.update(plan_name, {'details.description': new_description})
        syncplan_values = session.syncplan.read(plan_name)
        assert syncplan_values['details']['description'] == new_description
        # Create and add two products to sync plan
        for _ in range(2):
            product = entities.Product(organization=module_org).create()
            session.syncplan.add_product(plan_name, product.name)
        # Remove a product and assert syncplan still searchable
        session.syncplan.remove_product(plan_name, product.name)
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        # Delete sync plan
        session.syncplan.delete(plan_name)
        assert plan_name not in session.syncplan.search(plan_name)


@pytest.mark.tier2
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
        # workaround: force session.browser to point to browser object on next line
        session.contenthost.read_all('current_user')
        startdate = session.browser.get_client_datetime() + timedelta(minutes=10)
        # Create new sync plan and check all values in entity that was created
        session.syncplan.create(
            {
                'name': plan_name,
                'interval': SYNC_INTERVAL['custom'],
                'description': description,
                'cron_expression': cron_expression,
                'date_time.start_date': startdate.strftime("%Y-%m-%d"),
                'date_time.hours': startdate.strftime('%H'),
                'date_time.minutes': startdate.strftime('%M'),
            }
        )
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        syncplan_values = session.syncplan.read(plan_name)
        assert syncplan_values['details']['interval'] == SYNC_INTERVAL['custom']
        assert syncplan_values['details']['cron_expression'] == cron_expression
        assert syncplan_values['details']['recurring_logic'].isdigit()
        time = syncplan_values['details']['date_time'].rpartition(':')[0]
        assert time == startdate.strftime("%B %-d, %Y, %I")
        # Update sync plan with new description
        session.syncplan.update(plan_name, {'details.interval': SYNC_INTERVAL['day']})
        syncplan_values = session.syncplan.read(plan_name)
        assert syncplan_values['details']['interval'] == SYNC_INTERVAL['day']
        assert not syncplan_values['details']['cron_expression']
        # Delete sync plan
        session.syncplan.delete(plan_name)
        assert plan_name not in session.syncplan.search(plan_name)


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_search_scoped(session):
    """Test scoped search for different sync plan parameters

    :id: 3a48513e-205d-47a3-978e-79b764cc74d9

    :customerscenario: true

    :expectedresults: Search functionality provide proper results

    :BZ: 1259374

    :CaseImportance: High
    """
    name = gen_string('alpha')
    start_date = datetime.utcnow() + timedelta(days=10)
    org = entities.Organization().create()
    entities.SyncPlan(
        name=name,
        interval=SYNC_INTERVAL['day'],
        organization=org,
        enabled=True,
        sync_date=start_date,
    ).create()
    with session:
        session.organization.select(org.name)
        for query_type, query_value in [('interval', SYNC_INTERVAL['day']), ('enabled', 'true')]:
            assert session.syncplan.search(f'{query_type} = {query_value}')[0]['Name'] == name
        assert name not in session.syncplan.search('enabled = false')


@pytest.mark.tier3
def test_positive_synchronize_custom_product_custom_cron_real_time(session, module_org):
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
        # workaround: force session.browser to point to browser object on next line
        session.contenthost.read_all('current_user')
        start_date = session.browser.get_client_datetime()
        next_sync = 3 * 60
        # forming cron expression sync repo after 3 min
        expected_next_run_time = start_date + timedelta(seconds=next_sync)
        cron_expression = f'{expected_next_run_time.minute} * * * *'
        session.syncplan.create(
            {
                'name': plan_name,
                'interval': SYNC_INTERVAL['custom'],
                'cron_expression': cron_expression,
                'description': 'sync plan create with start time',
                'date_time.start_date': start_date.strftime("%Y-%m-%d"),
                'date_time.hours': start_date.strftime('%H'),
                'date_time.minutes': start_date.strftime('%M'),
            }
        )
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, product.name)
        # check that product was not synced
        with pytest.raises(AssertionError) as context:
            validate_task_status(repo.id, module_org.id, max_tries=1)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Waiting part of delay that is left and check that product was synced
        time.sleep(next_sync)
        validate_task_status(repo.id, module_org.id)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'])
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert int(repo_values['content_counts'][repo_type]) > 0
        # Delete sync plan
        session.syncplan.delete(plan_name)
        assert plan_name not in session.syncplan.search(plan_name)


@pytest.mark.tier3
def test_positive_synchronize_custom_product_custom_cron_past_sync_date(session, module_org):
    """Create a sync plan with past datetime as a sync date,
    add a custom product and verify the product gets synchronized
    on the next sync occurrence based on custom cron interval

    :id: 4d9ed0bf-a63c-44de-846d-7cf302273bcc

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System
    """
    interval = 60 * 60  # 'hourly' sync interval in seconds
    cron_multiple = 5  # sync event is on every multiple of this value, starting from 00 mins
    delay = (cron_multiple) * 60
    guardtime = 180  # do not start test less than 3 mins before the next sync event
    plan_name = gen_string('alpha')
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    with session:
        # workaround: force session.browser to point to browser object on next line
        session.contenthost.read_all('current_user')
        startdate = session.browser.get_client_datetime() - timedelta(seconds=(interval - delay))
        # if < 3 mins before the target event rather wait 3 mins for the next test window
        if int(startdate.strftime('%M')) % (cron_multiple) > int(guardtime / 60):
            time.sleep(guardtime)
        session.syncplan.create(
            {
                'name': plan_name,
                'interval': SYNC_INTERVAL['custom'],
                'cron_expression': f'*/{cron_multiple} * * * *',
                'description': 'sync plan create with start time',
                'date_time.start_date': startdate.strftime("%Y-%m-%d"),
                'date_time.hours': startdate.strftime('%H'),
                'date_time.minutes': startdate.strftime('%M'),
            }
        )
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        session.syncplan.add_product(plan_name, product.name)
        # Waiting part of delay and check that product was not synced
        time.sleep(delay * 1 / cron_multiple)
        with pytest.raises(AssertionError) as context:
            validate_task_status(repo.id, module_org.id, max_tries=1)
        assert 'No task was found using query' in str(context.value)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'], after_sync=False)
        # Waiting part of delay that is left and check that product was synced
        time.sleep(delay * (cron_multiple - 1) / cron_multiple)
        validate_task_status(repo.id, module_org.id)
        validate_repo_content(repo, ['erratum', 'package', 'package_group'])
        repo_values = session.repository.read(product.name, repo.name)
        for repo_type in ['Packages', 'Errata', 'Package Groups']:
            assert int(repo_values['content_counts'][repo_type]) > 0
        # Delete sync plan
        session.syncplan.delete(plan_name)
        assert plan_name not in session.syncplan.search(plan_name)
