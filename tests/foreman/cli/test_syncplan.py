"""Test class for Sync Plan CLI

:Requirement: Syncplan

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SyncPlans

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import logging
from datetime import datetime
from datetime import timedelta
from time import sleep

import pytest
from fauxfactory import gen_string

from robottelo import manifests
from robottelo.api.utils import wait_for_syncplan_tasks
from robottelo.api.utils import wait_for_tasks
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_org
from robottelo.cli.factory import make_product
from robottelo.cli.factory import make_repository
from robottelo.cli.factory import make_sync_plan
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.cli.syncplan import SyncPlan
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.ssh import upload_file


@filtered_datapoint
def valid_name_interval_create_tests():
    """Returns a list of valid data for interval create tests."""
    return [
        {'name': gen_string('alpha', 15), 'interval': 'hourly'},
        {'name': gen_string('alphanumeric', 15), 'interval': 'hourly'},
        {'name': gen_string('numeric', 15), 'interval': 'hourly'},
        {'name': gen_string('latin1', 15), 'interval': 'hourly'},
        {'name': gen_string('utf8', 15), 'interval': 'hourly'},
        {'name': gen_string('html', 15), 'interval': 'hourly'},
        {'name': gen_string('alpha', 15), 'interval': 'daily'},
        {'name': gen_string('alphanumeric', 15), 'interval': 'daily'},
        {'name': gen_string('numeric', 15), 'interval': 'daily'},
        {'name': gen_string('latin1', 15), 'interval': 'daily'},
        {'name': gen_string('utf8', 15), 'interval': 'daily'},
        {'name': gen_string('html', 15), 'interval': 'daily'},
        {'name': gen_string('alpha', 15), 'interval': 'weekly'},
        {'name': gen_string('alphanumeric', 15), 'interval': 'weekly'},
        {'name': gen_string('numeric', 15), 'interval': 'weekly'},
        {'name': gen_string('latin1', 15), 'interval': 'weekly'},
        {'name': gen_string('utf8', 15), 'interval': 'weekly'},
        {'name': gen_string('html', 15), 'interval': 'weekly'},
    ]


@filtered_datapoint
def valid_name_interval_update_tests():
    """Returns a list of valid data for interval update tests."""
    return [
        {'name': gen_string('alpha', 15), 'interval': 'daily', 'new-interval': 'hourly'},
        {'name': gen_string('alphanumeric', 15), 'interval': 'daily', 'new-interval': 'hourly'},
        {'name': gen_string('numeric', 15), 'interval': 'daily', 'new-interval': 'hourly'},
        {'name': gen_string('latin1', 15), 'interval': 'daily', 'new-interval': 'hourly'},
        {'name': gen_string('utf8', 15), 'interval': 'daily', 'new-interval': 'hourly'},
        {'name': gen_string('html', 15), 'interval': 'daily', 'new-interval': 'hourly'},
        {'name': gen_string('alpha', 15), 'interval': 'weekly', 'new-interval': 'daily'},
        {'name': gen_string('alphanumeric', 15), 'interval': 'weekly', 'new-interval': 'daily'},
        {'name': gen_string('numeric', 15), 'interval': 'weekly', 'new-interval': 'daily'},
        {'name': gen_string('latin1', 15), 'interval': 'weekly', 'new-interval': 'daily'},
        {'name': gen_string('utf8', 15), 'interval': 'weekly', 'new-interval': 'daily'},
        {'name': gen_string('html', 15), 'interval': 'weekly', 'new-interval': 'daily'},
        {'name': gen_string('alpha', 15), 'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': gen_string('alphanumeric', 15), 'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': gen_string('numeric', 15), 'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': gen_string('latin1', 15), 'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': gen_string('utf8', 15), 'interval': 'hourly', 'new-interval': 'weekly'},
        {'name': gen_string('html', 15), 'interval': 'hourly', 'new-interval': 'weekly'},
    ]


logger = logging.getLogger('robottelo')


def validate_task_status(repo_id, max_tries=6, repo_name=None):
    """Wait for Pulp and foreman_tasks to complete or timeout

    :param repo_id: Repository Id to identify the correct task
    :param max_tries: Max tries to poll for the task creation
    :param repo_name: Repository name of repository to filter the
        pulp tasks
    """
    if repo_name:
        wait_for_syncplan_tasks(repo_name=repo_name)
    wait_for_tasks(
        search_query='resource_type = Katello::Repository'
        ' and owner.login = foreman_admin'
        ' and resource_id = {}'.format(repo_id),
        max_tries=max_tries,
    )


def validate_repo_content(repo, content_types, after_sync=True):
    """Check whether corresponding content is present in repository before
    or after synchronization is performed

    :param repo: Repository instance to be validated
    :param content_types: List of repository content entities that should
        be validated (e.g. package, erratum, puppet_module)
    :param bool after_sync: Specify whether you perform validation before
        synchronization procedure is happened or after
    """
    repo = Repository.info({'id': repo['id']})
    for content in content_types:
        if after_sync:
            assert int(repo['content-counts'][content]) > 0
        else:
            assert not int(repo['content-counts'][content])


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_name(module_org, name):
    """Check if syncplan can be created with random names

    :id: dc0a86f7-4219-427e-92fd-29352dbdbfce

    :parametrized: yes

    :expectedresults: Sync plan is created and has random name

    :CaseImportance: Critical
    """
    sync_plan = make_sync_plan({'name': name, 'organization-id': module_org.id})
    result = SyncPlan.info({'id': sync_plan['id']})
    assert result['name'] == name


@pytest.mark.parametrize('desc', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_description(module_org, desc):
    """Check if syncplan can be created with random description

    :id: a1bbe81b-60f5-4a19-b400-a02a23fa1dfa

    :parametrized: yes

    :expectedresults: Sync plan is created and has random description

    :CaseImportance: Critical
    """
    new_sync_plan = make_sync_plan({'description': desc, 'organization-id': module_org.id})
    result = SyncPlan.info({'id': new_sync_plan['id']})
    assert result['description'] == desc


@pytest.mark.parametrize('test_data', **parametrized(valid_name_interval_create_tests()))
@pytest.mark.tier1
def test_positive_create_with_interval(module_org, test_data):
    """Check if syncplan can be created with varied intervals

    :id: 32eb0c1d-0c9a-4fb5-a185-68d0d705fbce

    :parametrized: yes

    :expectedresults: Sync plan is created and has selected interval

    :CaseImportance: Critical
    """
    new_sync_plan = make_sync_plan(
        {
            'interval': test_data['interval'],
            'name': test_data['name'],
            'organization-id': module_org.id,
        }
    )
    result = SyncPlan.info({'id': new_sync_plan['id']})
    assert result['name'] == test_data['name']
    assert result['interval'] == test_data['interval']


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_create_with_name(module_org, name):
    """Check if syncplan can be created with random invalid names

    :id: 4c1aee35-271e-4ed8-9369-d2abfea8cfd9

    :parametrized: yes

    :expectedresults: Sync plan is not created

    :CaseImportance: Critical
    """
    with pytest.raises(CLIFactoryError, match='Could not create the sync plan:'):
        make_sync_plan({'name': name, 'organization-id': module_org.id})


@pytest.mark.parametrize('new_desc', **parametrized(valid_data_list()))
@pytest.mark.tier2
def test_positive_update_description(module_org, new_desc):
    """Check if syncplan description can be updated

    :id: 00a279cd-1f49-4ebb-a59a-6f0b4e4cb83c

    :parametrized: yes

    :expectedresults: Sync plan is created and description is updated
    """
    new_sync_plan = make_sync_plan({'organization-id': module_org.id})
    SyncPlan.update({'description': new_desc, 'id': new_sync_plan['id']})
    result = SyncPlan.info({'id': new_sync_plan['id']})
    assert result['description'] == new_desc


@pytest.mark.parametrize('test_data', **parametrized(valid_name_interval_update_tests()))
@pytest.mark.tier1
def test_positive_update_interval(module_org, test_data):
    """Check if syncplan interval can be updated

    :id: d676d7f3-9f7c-4375-bb8b-277d71af94b4

    :parametrized: yes

    :expectedresults: Sync plan interval is updated

    :CaseImportance: Critical
    """
    new_sync_plan = make_sync_plan(
        {
            'interval': test_data['interval'],
            'name': test_data['name'],
            'organization-id': module_org.id,
        }
    )
    SyncPlan.update({'id': new_sync_plan['id'], 'interval': test_data['new-interval']})
    result = SyncPlan.info({'id': new_sync_plan['id']})
    assert result['interval'] == test_data['new-interval']


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_update_sync_date(module_org):
    """Check if syncplan sync date can be updated

    :id: f0c17d7d-3e86-4b64-9747-6cba6809815e

    :expectedresults: Sync plan is created and sync plan is updated

    :BZ: 1336790

    :CaseImportance: Critical
    """
    # Set the sync date to today/right now
    today = datetime.now()
    sync_plan_name = gen_string('alphanumeric')
    new_sync_plan = make_sync_plan(
        {
            'name': sync_plan_name,
            'sync-date': today.strftime("%Y-%m-%d %H:%M:%S"),
            'organization-id': module_org.id,
        }
    )
    # Assert that sync date matches data passed
    assert new_sync_plan['start-date'] == today.strftime("%Y/%m/%d %H:%M:%S")
    # Set sync date 5 days in the future
    future_date = today + timedelta(days=5)
    # Update sync interval
    SyncPlan.update(
        {'id': new_sync_plan['id'], 'sync-date': future_date.strftime("%Y-%m-%d %H:%M:%S")}
    )
    # Fetch it
    result = SyncPlan.info({'id': new_sync_plan['id']})
    assert result['start-date'] != new_sync_plan['start-date']
    assert datetime.strptime(result['start-date'], '%Y/%m/%d %H:%M:%S') > datetime.strptime(
        new_sync_plan['start-date'], '%Y/%m/%d %H:%M:%S'
    ), 'Sync date was not updated'


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete_by_id(module_org, name):
    """Check if syncplan can be created and deleted

    :id: b5d97c6b-aead-422b-8d9f-4a192bbe4a3b

    :parametrized: yes

    :expectedresults: Sync plan is created and then deleted

    :CaseImportance: Critical
    """
    new_sync_plan = make_sync_plan({'name': name, 'organization-id': module_org.id})
    SyncPlan.delete({'id': new_sync_plan['id']})
    with pytest.raises(CLIReturnCodeError):
        SyncPlan.info({'id': new_sync_plan['id']})


@pytest.mark.tier1
def test_positive_info_enabled_field_is_displayed(module_org):
    """Check if Enabled field is displayed in sync-plan info output

    :id: 54e3a4ea-315c-4026-8101-c4605ca6b874

    :expectedresults: Sync plan Enabled state is displayed

    :CaseImportance: Critical
    """
    new_sync_plan = make_sync_plan({'organization-id': module_org.id})
    result = SyncPlan.info({'id': new_sync_plan['id']})
    assert result.get('enabled') is not None


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_info_with_assigned_product(module_org):
    """Verify that sync plan info command returns list of products which
    are assigned to that sync plan

    :id: 7a7e5e40-7776-4d26-9173-73f00de6e8e9

    :customerscenario: true

    :expectedresults: Expected product information is returned in info
        command

    :BZ: 1390545

    :CaseImportance: Critical

    :CaseLevel: Integration
    """
    prod1 = gen_string('alpha')
    prod2 = gen_string('alpha')
    sync_plan = make_sync_plan(
        {
            'enabled': 'false',
            'organization-id': module_org.id,
            'sync-date': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    for prod_name in [prod1, prod2]:
        product = make_product({'organization-id': module_org.id, 'name': prod_name})
        Product.set_sync_plan({'id': product['id'], 'sync-plan-id': sync_plan['id']})
    updated_plan = SyncPlan.info({'id': sync_plan['id']})
    assert len(updated_plan['products']) == 2
    assert {prod['name'] for prod in updated_plan['products']} == {prod1, prod2}


@pytest.mark.tier4
@pytest.mark.upgrade
def test_negative_synchronize_custom_product_past_sync_date(module_org):
    """Verify product won't get synced immediately after adding association
    with a sync plan which has already been started

    :id: c80f5c0c-3863-47da-8d7b-7d65c73664b0

    :expectedresults: Repository was not synchronized

    :BZ: 1279539

    :CaseLevel: System
    """
    sync_plan = make_sync_plan(
        {
            'enabled': 'true',
            'organization-id': module_org.id,
            'sync-date': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    product = make_product({'organization-id': module_org.id})
    repo = make_repository({'product-id': product['id']})
    Product.set_sync_plan({'id': product['id'], 'sync-plan-id': sync_plan['id']})
    with pytest.raises(AssertionError):
        validate_task_status(repo['id'], max_tries=2)


@pytest.mark.stubbed
@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_synchronize_custom_product_custom_cron(module_org):
    """Create a sync plan with custom cron with 1 min interval, add a
    custom product and verify the product gets synchronized on the next
    sync occurrence

    :id: 5f398103-7c36-4524-a1cb-c258d97cecba

    :expectedresults: Product is synchronized successfully.
    """


@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_synchronize_custom_product_past_sync_date(module_org):
    """Create a sync plan with a past datetime as a sync date, add a
    custom product and verify the product gets synchronized on the next
    sync occurrence

    :id: 21efdd08-698c-443c-a681-edce19a4c83a

    :expectedresults: Product is synchronized successfully.

    :BZ: 1279539

    :CaseLevel: System
    """
    interval = 60 * 60  # 'hourly' sync interval in seconds
    delay = 2 * 60
    product = make_product({'organization-id': module_org.id})
    repo = make_repository({'product-id': product['id']})
    sync_plan = make_sync_plan(
        {
            'enabled': 'true',
            'interval': 'hourly',
            'organization-id': module_org.id,
            'sync-date': (datetime.utcnow() - timedelta(seconds=interval - delay)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
    )
    # Associate sync plan with product
    Product.set_sync_plan({'id': product['id'], 'sync-plan-id': sync_plan['id']})
    # Wait quarter of expected time
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was not synced'.format(delay / 4, product['name'])
    )
    sleep(delay / 4)
    # Verify product has not been synced yet
    with pytest.raises(AssertionError):
        validate_task_status(repo['id'], max_tries=1)
    validate_repo_content(repo, ['errata', 'packages'], after_sync=False)
    # Wait until the first recurrence
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was synced'.format((delay * 3 / 4), product['name'])
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo['id'], repo_name=repo['name'])
    validate_repo_content(repo, ['errata', 'package-groups', 'packages'])


@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_synchronize_custom_product_future_sync_date(module_org):
    """Create a sync plan with sync date in a future and sync one custom
    product with it automatically.

    :id: 635bffe2-df98-4971-8950-40edc89e479e

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System

    :BZ: 1655595
    """
    delay = 2 * 60  # delay for sync date in seconds
    product = make_product({'organization-id': module_org.id})
    repo = make_repository({'product-id': product['id']})
    sync_plan = make_sync_plan(
        {
            'enabled': 'true',
            'organization-id': module_org.id,
            'sync-date': (datetime.utcnow().replace(second=0) + timedelta(seconds=delay)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            'cron-expression': ["*/4 * * * *"],
        }
    )
    # Verify product is not synced and doesn't have any content
    validate_repo_content(repo, ['errata', 'packages'], after_sync=False)
    # Associate sync plan with product
    Product.set_sync_plan({'id': product['id'], 'sync-plan-id': sync_plan['id']})
    # Wait quarter of expected time
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was not synced'.format(delay / 4, product['name'])
    )
    sleep(delay / 4)
    # Verify product has not been synced yet
    with pytest.raises(AssertionError):
        validate_task_status(repo['id'], max_tries=1)
    validate_repo_content(repo, ['errata', 'packages'], after_sync=False)
    # Wait the rest of expected time
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was synced'.format((delay * 3 / 4), product['name'])
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo['id'], repo_name=repo['name'])
    validate_repo_content(repo, ['errata', 'package-groups', 'packages'])


@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_synchronize_custom_products_future_sync_date(module_org):
    """Create a sync plan with sync date in a future and sync multiple
    custom products with multiple repos automatically.

    :id: dd262cf3-b836-422c-baca-b3adbc532478

    :expectedresults: Products are synchronized successfully.

    :CaseLevel: System

    :BZ: 1655595
    """
    delay = 2 * 60  # delay for sync date in seconds
    products = [make_product({'organization-id': module_org.id}) for _ in range(3)]
    repos = [
        make_repository({'product-id': product['id']}) for product in products for _ in range(2)
    ]
    sync_plan = make_sync_plan(
        {
            'enabled': 'true',
            'organization-id': module_org.id,
            'sync-date': (datetime.utcnow().replace(second=0) + timedelta(seconds=delay)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            'cron-expression': ["*/4 * * * *"],
        }
    )
    # Verify products have not been synced yet
    for repo in repos:
        with pytest.raises(AssertionError):
            validate_task_status(repo['id'], max_tries=1)
    # Associate sync plan with products
    for product in products:
        Product.set_sync_plan({'id': product['id'], 'sync-plan-id': sync_plan['id']})
    # Wait quarter of expected time
    logger.info(f'Waiting {delay / 4} seconds to check products were not synced')
    sleep(delay / 4)
    # Verify products has not been synced yet
    for repo in repos:
        with pytest.raises(AssertionError):
            validate_task_status(repo['id'], max_tries=1)
    # Wait the rest of expected time
    logger.info(f'Waiting {delay * 3 / 4} seconds to check products were synced')
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    for repo in repos:
        validate_task_status(repo['id'], repo_name=repo['name'])
        validate_repo_content(repo, ['errata', 'package-groups', 'packages'])


@pytest.mark.run_in_one_thread
@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_synchronize_rh_product_past_sync_date(module_org):
    """Create a sync plan with past datetime as a sync date, add a
    RH product and verify the product gets synchronized on the next sync
    occurrence

    :id: 47280ef4-3936-4dbc-8ed0-1076aa8d40df

    :expectedresults: Product is synchronized successfully.

    :BZ: 1279539

    :CaseLevel: System
    """
    interval = 60 * 60  # 'hourly' sync interval in seconds
    delay = 2 * 60
    org = make_org()
    with manifests.clone() as manifest:
        upload_file(manifest.content, manifest.filename)
    Subscription.upload({'file': manifest.filename, 'organization-id': org['id']})
    RepositorySet.enable(
        {
            'name': REPOSET['rhva6'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
            'basearch': 'x86_64',
        }
    )
    product = Product.info({'name': PRDS['rhel'], 'organization-id': org['id']})
    repo = Repository.info(
        {'name': REPOS['rhva6']['name'], 'product': product['name'], 'organization-id': org['id']}
    )
    sync_plan = make_sync_plan(
        {
            'enabled': 'true',
            'interval': 'hourly',
            'organization-id': module_org.id,
            'sync-date': (datetime.utcnow() - timedelta(seconds=interval - delay)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
    )
    # Associate sync plan with product
    Product.set_sync_plan({'id': product['id'], 'sync-plan-id': sync_plan['id']})
    # Wait quarter of expected time
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was not synced'.format(delay / 4, product['name'])
    )
    sleep(delay / 4)
    # Verify product has not been synced yet
    with pytest.raises(AssertionError):
        validate_task_status(repo['id'], max_tries=1)
    validate_repo_content(repo, ['errata', 'packages'], after_sync=False)
    # Wait the rest of expected time
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was synced'.format((delay * 3 / 4), product['name'])
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo['id'], repo_name=repo['name'])
    validate_repo_content(repo, ['errata', 'packages'])


@pytest.mark.run_in_one_thread
@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_synchronize_rh_product_future_sync_date(module_org):
    """Create a sync plan with sync date in a future and sync one RH
    product with it automatically.

    :id: 6ce2f777-f230-4bb8-9822-2cf3580c21aa

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System

    :BZ: 1655595
    """
    delay = 2 * 60  # delay for sync date in seconds
    org = make_org()
    with manifests.clone() as manifest:
        upload_file(manifest.content, manifest.filename)
    Subscription.upload({'file': manifest.filename, 'organization-id': org['id']})
    RepositorySet.enable(
        {
            'name': REPOSET['rhva6'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
            'basearch': 'x86_64',
        }
    )
    product = Product.info({'name': PRDS['rhel'], 'organization-id': org['id']})
    repo = Repository.info(
        {'name': REPOS['rhva6']['name'], 'product': product['name'], 'organization-id': org['id']}
    )
    sync_plan = make_sync_plan(
        {
            'enabled': 'true',
            'organization-id': module_org.id,
            'sync-date': (datetime.utcnow().replace(second=0) + timedelta(seconds=delay)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            'cron-expression': ["*/4 * * * *"],
        }
    )
    # Verify product is not synced and doesn't have any content
    with pytest.raises(AssertionError):
        validate_task_status(repo['id'], max_tries=1)
    validate_repo_content(repo, ['errata', 'packages'], after_sync=False)
    # Associate sync plan with product
    Product.set_sync_plan({'id': product['id'], 'sync-plan-id': sync_plan['id']})
    # Wait quarter of expected time
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was not synced'.format(delay / 4, product['name'])
    )
    sleep(delay / 4)
    # Verify product has not been synced yet
    with pytest.raises(AssertionError):
        validate_task_status(repo['id'], max_tries=1)
    validate_repo_content(repo, ['errata', 'packages'], after_sync=False)
    # Wait the rest of expected time
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was synced'.format((delay * 3 / 4), product['name'])
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo['id'], repo_name=repo['name'])
    validate_repo_content(repo, ['errata', 'packages'])


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_synchronize_custom_product_daily_recurrence(module_org):
    """Create a daily sync plan with a past datetime as a sync date,
    add a custom product and verify the product gets synchronized on
    the next sync occurrence

    :id: 8d882e8b-b5c1-4449-81c6-0efd31ad75a7

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System
    """
    delay = 2 * 60
    product = make_product({'organization-id': module_org.id})
    repo = make_repository({'product-id': product['id']})
    start_date = datetime.utcnow() - timedelta(days=1) + timedelta(seconds=delay)
    sync_plan = make_sync_plan(
        {
            'enabled': 'true',
            'interval': 'daily',
            'organization-id': module_org.id,
            'sync-date': start_date.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    # Associate sync plan with product
    Product.set_sync_plan({'id': product['id'], 'sync-plan-id': sync_plan['id']})
    # Wait quarter of expected time
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was not synced'.format(delay / 4, product['name'])
    )
    sleep(delay / 4)
    # Verify product has not been synced yet
    with pytest.raises(AssertionError):
        validate_task_status(repo['id'], max_tries=1)
    validate_repo_content(repo, ['errata', 'packages'], after_sync=False)
    # Wait until the first recurrence
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was synced'.format((delay * 3 / 4), product['name'])
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo['id'], repo_name=repo['name'])
    validate_repo_content(repo, ['errata', 'package-groups', 'packages'])


@pytest.mark.tier3
def test_positive_synchronize_custom_product_weekly_recurrence(module_org):
    """Create a weekly sync plan with a past datetime as a sync date,
    add a custom product and verify the product gets synchronized on
    the next sync occurrence

    :id: 1079a66d-7c23-44f6-a4a0-47f4c74d92a4

    :expectedresults: Product is synchronized successfully.

    :BZ: 1396647

    :CaseLevel: System
    """
    delay = 2 * 60
    product = make_product({'organization-id': module_org.id})
    repo = make_repository({'product-id': product['id']})
    start_date = datetime.utcnow() - timedelta(weeks=1) + timedelta(seconds=delay)
    sync_plan = make_sync_plan(
        {
            'enabled': 'true',
            'interval': 'weekly',
            'organization-id': module_org.id,
            'sync-date': start_date.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    # Associate sync plan with product
    Product.set_sync_plan({'id': product['id'], 'sync-plan-id': sync_plan['id']})
    # Wait quarter of expected time
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was not synced'.format(delay / 4, product['name'])
    )
    sleep(delay / 4)
    # Verify product has not been synced yet
    with pytest.raises(AssertionError):
        validate_task_status(repo['id'], max_tries=1)
    validate_repo_content(repo, ['errata', 'packages'], after_sync=False)
    # Wait until the first recurrence
    logger.info(
        'Waiting {} seconds to check product {}'
        ' was synced'.format((delay * 3 / 4), product['name'])
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo['id'], repo_name=repo['name'])
    validate_repo_content(repo, ['errata', 'package-groups', 'packages'])
