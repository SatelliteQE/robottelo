"""Tests for the ``sync_plans`` API paths.

API reference for sync plans can be found on your Satellite:
<sat6.example.com>/apidoc/v2/sync_plans.html


:Requirement: Syncplan

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SyncPlans

:Assignee: swadeley

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime
from datetime import timedelta
from time import sleep

import pytest
from fauxfactory import gen_choice
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo import manifests
from robottelo.api.utils import disable_syncplan
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import wait_for_tasks
from robottelo.config import get_credentials
from robottelo.config import get_url
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants import SYNC_INTERVAL
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_cron_expressions
from robottelo.datafactory import valid_data_list
from robottelo.logging import logger


sync_date_deltas = {
    # Today
    'now': 0,
    # 5 minutes from now
    '5min': 300,
    # 5 days from now
    '5days': 432000,
    # Yesterday
    'yesterday': -86400,
    # 5 minutes ago
    '5min_ago': -300,
}


@filtered_datapoint
def valid_sync_interval():
    """Returns a list of valid sync intervals."""
    return {i.replace(' ', '_'): i for i in ['hourly', 'daily', 'weekly', 'custom cron']}


def validate_task_status(repo_id, org_id, max_tries=6):
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
            assert repo.last_sync is not None, 'Repository unexpectedly was not synced.'
            assert (
                repo.content_counts[content] > 0
            ), 'Repository contains invalid number of content entities.'
        else:
            assert repo.last_sync is None, 'Repository was unexpectedly synced.'
            assert not repo.content_counts[
                content
            ], 'Repository contains invalid number of content entities.'


@pytest.mark.tier1
def test_positive_get_routes():
    """Issue an HTTP GET response to both available routes.

    :id: 9e40ea7f-71ea-4ced-94ba-cde03620c654

    :expectedresults: The same response is returned.

    :BZ: 1132817

    :CaseImportance: Critical
    """
    org = entities.Organization().create()
    entities.SyncPlan(organization=org).create()
    response1 = client.get(
        f'{get_url()}/katello/api/v2/sync_plans',
        auth=get_credentials(),
        data={'organization_id': org.id},
        verify=False,
    )
    response2 = client.get(
        f'{get_url()}/katello/api/v2/organizations/{org.id}/sync_plans',
        auth=get_credentials(),
        verify=False,
    )
    for response in (response1, response2):
        response.raise_for_status()
    assert response1.json()['results'] == response2.json()['results']


@pytest.mark.build_sanity
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.tier1
def test_positive_create_enabled_disabled(module_org, enabled):
    """Create sync plan with different 'enabled' field values.

    :id: df5837e7-3d0f-464a-bd67-86b423c16eb4

    :parametrized: yes

    :expectedresults: A sync plan is created, 'enabled' field has correct
        value.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(enabled=enabled, organization=module_org).create()
    sync_plan = sync_plan.read()
    assert sync_plan.enabled == enabled
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_name(module_org, name):
    """Create a sync plan with a random name.

    :id: c1263134-0d7c-425a-82fd-df5274e1f9ba

    :parametrized: yes

    :expectedresults: A sync plan is created with the specified name.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(enabled=False, name=name, organization=module_org).create()
    sync_plan = sync_plan.read()
    assert sync_plan.name == name


@pytest.mark.parametrize('description', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_description(module_org, description):
    """Create a sync plan with a random description.

    :id: 3e5745e8-838d-44a5-ad61-7e56829ad47c

    :parametrized: yes

    :expectedresults: A sync plan is created with the specified
        description.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(
        enabled=False, description=description, organization=module_org
    ).create()
    sync_plan = sync_plan.read()
    assert sync_plan.description == description


@pytest.mark.parametrize('interval', **parametrized(valid_sync_interval()))
@pytest.mark.tier1
def test_positive_create_with_interval(module_org, interval):
    """Create a sync plan with a random interval.

    :id: d160ed1c-b698-42dc-be0b-67ac693c7840

    :parametrized: yes

    :expectedresults: A sync plan is created with the specified interval.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(
        enabled=False, description=gen_string('alpha'), organization=module_org, interval=interval
    )
    if interval == SYNC_INTERVAL['custom']:
        sync_plan.cron_expression = gen_choice(valid_cron_expressions())
    sync_plan = sync_plan.create()
    sync_plan = sync_plan.read()
    assert sync_plan.interval == interval


@pytest.mark.parametrize('sync_delta', **parametrized(sync_date_deltas))
@pytest.mark.tier1
def test_positive_create_with_sync_date(module_org, sync_delta):
    """Create a sync plan and update its sync date.

    :id: bdb6e0a9-0d3b-4811-83e2-2140b7bb62e3

    :parametrized: yes

    :expectedresults: A sync plan can be created with a random sync date.

    :CaseImportance: Critical
    """
    sync_date = datetime.now() + timedelta(seconds=sync_delta)
    sync_plan = entities.SyncPlan(
        enabled=False, organization=module_org, sync_date=sync_date
    ).create()
    sync_plan = sync_plan.read()
    assert sync_date.strftime('%Y-%m-%d %H:%M:%S UTC') == sync_plan.sync_date


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_create_with_invalid_name(module_org, name):
    """Create a sync plan with an invalid name.

    :id: a3a0f844-2f81-4f87-9f68-c25506c29ce2

    :parametrized: yes

    :expectedresults: A sync plan can not be created with the specified
        name.

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError):
        entities.SyncPlan(name=name, organization=module_org).create()


@pytest.mark.parametrize('interval', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_create_with_invalid_interval(module_org, interval):
    """Create a sync plan with invalid interval specified.

    :id: f5844526-9f58-4be3-8a96-3849a465fc02

    :parametrized: yes

    :expectedresults: A sync plan can not be created with invalid interval
        specified

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError):
        entities.SyncPlan(interval=interval, organization=module_org).create()


@pytest.mark.tier1
def test_negative_create_with_empty_interval(module_org):
    """Create a sync plan with no interval specified.

    :id: b4686463-69c8-4538-b040-6fb5246a7b00

    :expectedresults: A sync plan can not be created with no interval
        specified.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(organization=module_org)
    sync_plan.create_missing()
    del sync_plan.interval
    with pytest.raises(HTTPError):
        sync_plan.create(False)


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.tier1
def test_positive_update_enabled(module_org, enabled):
    """Create sync plan and update it with opposite 'enabled' value.

    :id: 325c0ef5-c0e8-4cb9-b85e-87eb7f42c2f8

    :parametrized: yes

    :expectedresults: Sync plan is updated with different 'enabled' value.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(enabled=not enabled, organization=module_org).create()
    sync_plan.enabled = enabled
    sync_plan.update(['enabled'])
    sync_plan = sync_plan.read()
    assert sync_plan.enabled == enabled
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_update_name(module_org, name):
    """Create a sync plan and update its name.

    :id: dbfadf4f-50af-4aa8-8d7d-43988dc4528f

    :parametrized: yes

    :expectedresults: A sync plan is created and its name can be updated
        with the specified name.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(enabled=False, organization=module_org).create()
    sync_plan.name = name
    sync_plan.update(['name'])
    sync_plan = sync_plan.read()
    assert sync_plan.name == name


@pytest.mark.parametrize('description', **parametrized(valid_data_list()))
@pytest.mark.tier2
def test_positive_update_description(module_org, description):
    """Create a sync plan and update its description.

    :id: 4769fe9c-9eec-40c8-b015-1e3d7e570bec

    :parametrized: yes

    :expectedresults: A sync plan is created and its description can be
        updated with the specified description.
    """
    sync_plan = entities.SyncPlan(
        enabled=False, description=gen_string('alpha'), organization=module_org
    ).create()
    sync_plan.description = description
    sync_plan.update(['description'])
    sync_plan = sync_plan.read()
    assert sync_plan.description == description


@pytest.mark.parametrize('interval', **parametrized(valid_sync_interval()))
@pytest.mark.tier1
def test_positive_update_interval(module_org, interval):
    """Create a sync plan and update its interval.

    :id: cf2eddf8-b4db-430e-a9b0-83c626b45068

    :parametrized: yes

    :expectedresults: A sync plan is created and its interval can be
        updated with the specified interval.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(
        enabled=False, description=gen_string('alpha'), organization=module_org, interval=interval
    )
    if interval == SYNC_INTERVAL['custom']:
        sync_plan.cron_expression = gen_choice(valid_cron_expressions())
    sync_plan = sync_plan.create()
    # ensure "new interval" not equal to "interval"
    new_interval = 'hourly' if interval != 'hourly' else 'daily'
    sync_plan.interval = new_interval
    if new_interval == SYNC_INTERVAL['custom']:
        sync_plan.cron_expression = gen_choice(valid_cron_expressions())
        sync_plan = sync_plan.update(['interval', 'cron_expression'])
    else:
        sync_plan = sync_plan.update(['interval'])
    sync_plan = sync_plan.read()
    assert sync_plan.interval == new_interval


@pytest.mark.parametrize('interval', **parametrized(valid_sync_interval()))
@pytest.mark.tier1
def test_positive_update_interval_custom_cron(module_org, interval):
    """Create a sync plan and update its interval to custom cron.

    :id: 26c58319-cae0-4b0c-b388-2a1fe3f22344

    :parametrized: yes

    :expectedresults: A sync plan is created and its interval can be
        updated to custom cron.

    :CaseImportance: Critical
    """
    if interval != SYNC_INTERVAL['custom']:
        sync_plan = entities.SyncPlan(
            enabled=False,
            description=gen_string('alpha'),
            organization=module_org,
            interval=interval,
        ).create()

        sync_plan.interval = SYNC_INTERVAL['custom']
        sync_plan.cron_expression = gen_choice(valid_cron_expressions())
        sync_plan.update(['interval', 'cron_expression'])
        sync_plan = sync_plan.read()
        assert sync_plan.interval == SYNC_INTERVAL['custom']


@pytest.mark.parametrize('sync_delta', **parametrized(sync_date_deltas))
@pytest.mark.tier1
def test_positive_update_sync_date(module_org, sync_delta):
    """Updated sync plan's sync date.

    :id: fad472c7-01b4-453b-ae33-0845c9e0dfd4

    :parametrized: yes

    :expectedresults: Sync date is updated with the specified sync date.

    :CaseImportance: Critical
    """
    sync_date = datetime.now() + timedelta(seconds=sync_delta)
    sync_plan = entities.SyncPlan(
        enabled=False, organization=module_org, sync_date=datetime.now() + timedelta(days=10)
    ).create()
    sync_plan.sync_date = sync_date
    sync_plan.update(['sync_date'])
    sync_plan = sync_plan.read()
    assert sync_date.strftime('%Y-%m-%d %H:%M:%S UTC') == sync_plan.sync_date


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_update_name(module_org, name):
    """Try to update a sync plan with an invalid name.

    :id: ae502053-9d3c-4cad-aee4-821f846ceae5

    :parametrized: yes

    :expectedresults: A sync plan can not be updated with the specified
        name.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(enabled=False, organization=module_org).create()
    sync_plan.name = name
    with pytest.raises(HTTPError):
        sync_plan.update(['name'])


@pytest.mark.parametrize('interval', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_update_interval(module_org, interval):
    """Try to update a sync plan with invalid interval.

    :id: 8c981174-6f55-49c0-8baa-40e5c3fc598c

    :parametrized: yes

    :expectedresults: A sync plan can not be updated with empty interval
        specified.

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(enabled=False, organization=module_org).create()
    sync_plan.interval = interval
    with pytest.raises(HTTPError):
        sync_plan.update(['interval'])


@pytest.mark.tier2
def test_positive_add_product(module_org):
    """Create a sync plan and add one product to it.

    :id: 036dea02-f73d-4fc1-9c41-5515b6659c79

    :expectedresults: A sync plan can be created and one product can be
        added to it.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    sync_plan = entities.SyncPlan(enabled=False, organization=module_org).create()
    product = entities.Product(organization=module_org).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    sync_plan = sync_plan.read()
    assert len(sync_plan.product) == 1
    assert sync_plan.product[0].id == product.id


@pytest.mark.tier2
def test_positive_add_products(module_org):
    """Create a sync plan and add two products to it.

    :id: 2a80ecad-2245-46d8-bbc6-0b802e68d50c

    :expectedresults: A sync plan can be created and two products can be
        added to it.

    :CaseLevel: Integration
    """
    sync_plan = entities.SyncPlan(enabled=False, organization=module_org).create()
    products = [entities.Product(organization=module_org).create() for _ in range(2)]
    sync_plan.add_products(data={'product_ids': [product.id for product in products]})
    sync_plan = sync_plan.read()
    assert len(sync_plan.product) == 2
    assert {product.id for product in products} == {product.id for product in sync_plan.product}


@pytest.mark.tier2
def test_positive_remove_product(module_org):
    """Create a sync plan with two products and then remove one
    product from it.

    :id: 987a0d94-ceb7-4115-9770-2297e60a63fa

    :expectedresults: A sync plan can be created and one product can be
        removed from it.

    :CaseLevel: Integration

    :BZ: 1199150
    """
    sync_plan = entities.SyncPlan(enabled=False, organization=module_org).create()
    products = [entities.Product(organization=module_org).create() for _ in range(2)]
    sync_plan.add_products(data={'product_ids': [product.id for product in products]})
    assert len(sync_plan.read().product) == 2
    sync_plan.remove_products(data={'product_ids': [products[0].id]})
    sync_plan = sync_plan.read()
    assert len(sync_plan.product) == 1
    assert sync_plan.product[0].id == products[1].id


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_remove_products(module_org):
    """Create a sync plan with two products and then remove both
    products from it.

    :id: eed8c239-8ba3-4dbd-aa6b-c289cd4efd47

    :expectedresults: A sync plan can be created and both products can be
        removed from it.

    :CaseLevel: Integration
    """
    sync_plan = entities.SyncPlan(enabled=False, organization=module_org).create()
    products = [entities.Product(organization=module_org).create() for _ in range(2)]
    sync_plan.add_products(data={'product_ids': [product.id for product in products]})
    assert len(sync_plan.read().product) == 2
    sync_plan.remove_products(data={'product_ids': [product.id for product in products]})
    assert len(sync_plan.read().product) == 0


@pytest.mark.tier2
def test_positive_repeatedly_add_remove(module_org):
    """Repeatedly add and remove a product from a sync plan.

    :id: b67536ba-3a36-4bb7-a405-0e12081d5a7e

    :expectedresults: A task is returned which can be used to monitor the
        additions and removals.

    :CaseLevel: Integration

    :BZ: 1199150
    """
    sync_plan = entities.SyncPlan(organization=module_org).create()
    product = entities.Product(organization=module_org).create()
    for _ in range(5):
        sync_plan.add_products(data={'product_ids': [product.id]})
        assert len(sync_plan.read().product) == 1
        sync_plan.remove_products(data={'product_ids': [product.id]})
        assert len(sync_plan.read().product) == 0
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.tier2
def test_positive_add_remove_products_custom_cron(module_org):
    """Create a sync plan with two products having custom cron interval
    and then remove both products from it.

    :id: 5ce34eaa-3574-49ba-ab02-aa25515394aa

    :expectedresults: A sync plan can be created and both products can be
        removed from it.

    :CaseLevel: Integration
    """
    cron_expression = gen_choice(valid_cron_expressions())

    sync_plan = entities.SyncPlan(
        organization=module_org, interval='custom cron', cron_expression=cron_expression
    ).create()
    products = [entities.Product(organization=module_org).create() for _ in range(2)]
    sync_plan.add_products(data={'product_ids': [product.id for product in products]})
    assert len(sync_plan.read().product) == 2
    sync_plan.remove_products(data={'product_ids': [product.id for product in products]})
    assert len(sync_plan.read().product) == 0
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.tier4
def test_negative_synchronize_custom_product_past_sync_date(module_org):
    """Verify product won't get synced immediately after adding association
    with a sync plan which has already been started

    :id: 263a6a79-8236-4757-bf9e-8d9091ba2a11

    :expectedresults: Product was not synchronized

    :BZ: 1279539

    :CaseLevel: System
    """
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    # Verify product is not synced and doesn't have any content
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, module_org.id, max_tries=2)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # Create and Associate sync plan with product
    sync_plan = entities.SyncPlan(
        organization=module_org, enabled=True, sync_date=datetime.utcnow().replace(second=0)
    ).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    # Verify product was not synced right after it was added to sync plan
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, module_org.id, max_tries=2)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.tier4
def test_positive_synchronize_custom_product_past_sync_date(module_org):
    """Create a sync plan with past datetime as a sync date, add a
    custom product and verify the product gets synchronized on the next
    sync occurrence

    :id: 0495cb39-2f15-4b6e-9828-1e9517c5c826

    :expectedresults: Product is synchronized successfully.

    :BZ: 1279539

    :CaseLevel: System
    """
    interval = 60 * 60  # 'hourly' sync interval in seconds
    delay = 2 * 60
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    # Create and Associate sync plan with product
    sync_plan = entities.SyncPlan(
        organization=module_org,
        enabled=True,
        interval='hourly',
        sync_date=datetime.utcnow().replace(second=0) - timedelta(seconds=interval - delay),
    ).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    # Wait quarter of expected time
    logger.info(
        f"Waiting {(delay / 4)} seconds to check product {product.name}"
        f" was not synced by {sync_plan.name}"
    )
    sleep(delay / 4)
    # Verify product is not synced and doesn't have any content
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, module_org.id, max_tries=1)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # Wait until the next recurrence
    logger.info(
        f"Waiting {(delay * 3 / 4)} seconds to check product {product.name}"
        f" was synced by {sync_plan.name}"
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo.id, module_org.id)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'])
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.tier4
def test_positive_synchronize_custom_product_future_sync_date(module_org):
    """Create a sync plan with sync date in a future and sync one custom
    product with it automatically.

    :id: b70a0c50-7335-4285-b24c-edfc1187f034

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System

    :BZ: 1655595, 1695733
    """
    delay = 2 * 60  # delay for sync date in seconds
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    # Verify product is not synced and doesn't have any content
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, module_org.id, max_tries=1)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # Create and Associate sync plan with product
    # BZ:1695733 is closed WONTFIX so apply this workaround
    logger.info('Need to set seconds to zero because BZ#1695733')
    sync_date = datetime.utcnow().replace(second=0) + timedelta(seconds=delay)
    sync_plan = entities.SyncPlan(
        organization=module_org, enabled=True, sync_date=sync_date
    ).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    # Wait quarter of expected time
    logger.info(
        f"Waiting {(delay / 4)} seconds to check product {product.name}"
        f" was not synced by {sync_plan.name}"
    )
    sleep(delay / 4)
    # Verify product has not been synced yet
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, module_org.id, max_tries=1)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # Wait the rest of expected time
    logger.info(
        f"Waiting {(delay * 3 / 4)} seconds to check product {product.name}"
        f" was synced by {sync_plan.name}"
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo.id, module_org.id)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'])
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_synchronize_custom_products_future_sync_date(module_org):
    """Create a sync plan with sync date in a future and sync multiple
    custom products with multiple repos automatically.

    :id: e646196e-3951-4297-8c3c-1494d9895347

    :expectedresults: Products are synchronized successfully.

    :CaseLevel: System

    :BZ: 1695733
    """
    delay = 4 * 60  # delay for sync date in seconds
    products = [entities.Product(organization=module_org).create() for _ in range(2)]
    repos = [
        entities.Repository(product=product).create() for product in products for _ in range(2)
    ]
    # Verify products have not been synced yet
    logger.info(
        f"Check products {products[0].name} and {products[1].name}"
        f" were not synced before sync plan created in org {module_org.label}"
    )
    for repo in repos:
        with pytest.raises(AssertionError):
            validate_task_status(repo.id, module_org.id, max_tries=1)
    # Create and Associate sync plan with products
    # BZ:1695733 is closed WONTFIX so apply this workaround
    logger.info('Need to set seconds to zero because BZ#1695733')
    sync_date = datetime.utcnow().replace(second=0) + timedelta(seconds=delay)
    sync_plan = entities.SyncPlan(
        organization=module_org, enabled=True, sync_date=sync_date
    ).create()
    sync_plan.add_products(data={'product_ids': [product.id for product in products]})
    # Wait quarter of expected time
    logger.info(
        f"Waiting {(delay / 4)} seconds to check products {products[0].name} and {products[1].name}"
        f" were not synced by {sync_plan.name}"
    )
    sleep(delay / 4)
    # Verify products has not been synced yet
    for repo in repos:
        with pytest.raises(AssertionError):
            validate_task_status(repo.id, module_org.id, max_tries=1)
    # Wait the rest of expected time
    logger.info(
        f"Waiting {(delay * 3 / 4)} seconds to check products {products[0].name}"
        f" and {products[1].name} were synced by {sync_plan.name}"
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    for repo in repos:
        validate_task_status(repo.id, module_org.id)
        validate_repo_content(repo, ['erratum', 'rpm', 'package_group'])
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.run_in_one_thread
@pytest.mark.tier4
def test_positive_synchronize_rh_product_past_sync_date():
    """Create a sync plan with past datetime as a sync date, add a
    RH product and verify the product gets synchronized on the next sync
    occurrence

    :id: 080c316d-4a06-4ee9-b5f6-1b210d8d0593

    :expectedresults: Product is synchronized successfully.

    :customerscenario: true

    :BZ: 1279539, 1879537

    :CaseLevel: System
    """
    interval = 60 * 60  # 'hourly' sync interval in seconds
    delay = 2 * 60
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        entities.Subscription().upload(
            data={'organization_id': org.id}, files={'content': manifest.content}
        )
    repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    product = entities.Product(name=PRDS['rhel'], organization=org).search()[0]
    repo = entities.Repository(id=repo_id).read()
    sync_plan = entities.SyncPlan(
        organization=org,
        enabled=True,
        interval='hourly',
        sync_date=datetime.utcnow() - timedelta(seconds=interval - delay),
    ).create()
    # Associate sync plan with product
    sync_plan.add_products(data={'product_ids': [product.id]})
    # Wait quarter of expected time
    logger.info(
        f"Waiting {(delay / 4)} seconds to check product {product.name}"
        f" was not synced by {sync_plan.name}"
    )
    sleep(delay / 4)
    # Verify product has not been synced yet
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, org.id, max_tries=1)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # Wait until the next recurrence
    logger.info(
        f"Waiting {(delay * 3 / 4)} seconds to check product {product.name}"
        f" was synced by {sync_plan.name}"
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo.id, org.id)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'])
    # Add disassociate RH product from sync plan check for BZ#1879537
    assert len(sync_plan.read().product) == 1
    # Disable the reposet
    reposet = entities.RepositorySet(name=REPOSET['rhst7'], product=product).search()[0]
    reposet.disable(data={'basearch': 'x86_64', 'releasever': None, 'product_id': product.id})
    # Assert that the Sync Plan now has no product associated with it
    assert len(sync_plan.read().product) == 0
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.run_in_one_thread
@pytest.mark.tier4
@pytest.mark.upgrade
def test_positive_synchronize_rh_product_future_sync_date():
    """Create a sync plan with sync date in a future and sync one RH
    product with it automatically.

    :id: 6697a00f-2181-4c2b-88eb-2333268d780b

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System
    """
    delay = 2 * 60  # delay for sync date in seconds
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        entities.Subscription().upload(
            data={'organization_id': org.id}, files={'content': manifest.content}
        )
    repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    product = entities.Product(name=PRDS['rhel'], organization=org).search()[0]
    repo = entities.Repository(id=repo_id).read()
    # BZ:1695733 is closed WONTFIX so apply this workaround
    logger.info('Need to set seconds to zero because BZ#1695733')
    sync_date = datetime.utcnow().replace(second=0) + timedelta(seconds=delay)
    sync_plan = entities.SyncPlan(
        organization=org, enabled=True, interval='hourly', sync_date=sync_date
    ).create()
    # Create and Associate sync plan with product
    sync_plan.add_products(data={'product_ids': [product.id]})
    # Verify product is not synced and doesn't have any content
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, org.id, max_tries=1)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # Wait quarter of expected time
    logger.info(
        f"Waiting {(delay / 4)} seconds to check product {product.name}"
        f" was not synced by {sync_plan.name}"
    )
    sleep(delay / 4)
    # Verify product has not been synced yet
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, org.id, max_tries=1)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # Wait the rest of expected time
    logger.info(
        f"Waiting {(delay * 3 / 4)} seconds to check product {product.name}"
        f" was synced by {sync_plan.name}"
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo.id, org.id)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'])
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.tier3
def test_positive_synchronize_custom_product_daily_recurrence(module_org):
    """Create a daily sync plan with current datetime as a sync date,
    add a custom product and verify the product gets synchronized on
    the next sync occurrence

    :id: d60e33a0-f75c-498e-9e6f-0a2025295a9d

    :expectedresults: Product is synchronized successfully.

    :CaseLevel: System
    """
    delay = 2 * 60
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    start_date = datetime.utcnow().replace(second=0) - timedelta(days=1) + timedelta(seconds=delay)
    # Create and Associate sync plan with product
    sync_plan = entities.SyncPlan(
        organization=module_org, enabled=True, interval='daily', sync_date=start_date
    ).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    # Wait quarter of expected time
    logger.info(
        f"Waiting {(delay / 4)} seconds to check product {product.name}"
        f" was not synced by {sync_plan.name}"
    )
    sleep(delay / 4)
    # Verify product is not synced and doesn't have any content
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, module_org.id, max_tries=1)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # Wait the rest of expected time
    logger.info(
        f"Waiting {(delay * 3 / 4)} seconds to check product {product.name}"
        f" was synced by {sync_plan.name}"
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo.id, module_org.id)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'])
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.tier3
def test_positive_synchronize_custom_product_weekly_recurrence(module_org):
    """Create a weekly sync plan with a past datetime as a sync date,
    add a custom product and verify the product gets synchronized on
    the next sync occurrence

    :id: ef52dd8e-756e-429c-8c30-b3e7db2b6d61

    :expectedresults: Product is synchronized successfully.

    :BZ: 1396647

    :CaseLevel: System
    """
    delay = 2 * 60
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product).create()
    start_date = datetime.utcnow().replace(second=0) - timedelta(weeks=1) + timedelta(seconds=delay)
    # Create and Associate sync plan with product
    sync_plan = entities.SyncPlan(
        organization=module_org, enabled=True, interval='weekly', sync_date=start_date
    ).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    # Wait quarter of expected time
    logger.info(
        f"Waiting {(delay / 4)} seconds to check product {product.name}"
        f" was not synced by {sync_plan.name}"
    )
    sleep(delay / 4)
    # Verify product is not synced and doesn't have any content
    with pytest.raises(AssertionError):
        validate_task_status(repo.id, module_org.id, max_tries=1)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'], after_sync=False)
    # Wait the rest of expected time
    logger.info(
        f"Waiting {(delay * 3 / 4)} seconds to check product {product.name}"
        f" was synced by {sync_plan.name}"
    )
    sleep(delay * 3 / 4)
    # Verify product was synced successfully
    validate_task_status(repo.id, module_org.id)
    validate_repo_content(repo, ['erratum', 'rpm', 'package_group'])
    # disable sync plan after test
    disable_syncplan(sync_plan)


@pytest.mark.tier2
def test_positive_delete_one_product(module_org):
    """Create a sync plan with one product and delete it.

    :id: e565c464-33e2-4bca-8eca-15d5a7d4b155

    :expectedresults: A sync plan is created with one product and sync plan
        can be deleted.

    :CaseLevel: Integration
    """
    sync_plan = entities.SyncPlan(organization=module_org).create()
    product = entities.Product(organization=module_org).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    sync_plan.delete()
    with pytest.raises(HTTPError):
        sync_plan.read()


@pytest.mark.tier2
def test_positive_delete_products(module_org):
    """Create a sync plan with two products and delete them.

    :id: f21bd57f-369e-4acd-a492-5532349a3804

    :expectedresults: A sync plan is created with one product and sync plan
        can be deleted.

    :CaseLevel: Integration
    """
    sync_plan = entities.SyncPlan(organization=module_org).create()
    products = [entities.Product(organization=module_org).create() for _ in range(2)]
    sync_plan.add_products(data={'product_ids': [product.id for product in products]})
    sync_plan.delete()
    with pytest.raises(HTTPError):
        sync_plan.read()


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_synced_product(module_org):
    """Create a sync plan with one synced product and delete it.

    :id: 195d8fec-1fa0-42ab-84a5-32dd81a285ca

    :expectedresults: A sync plan is created with one synced product and
        sync plan can be deleted.

    :CaseLevel: Integration
    """
    sync_plan = entities.SyncPlan(organization=module_org).create()
    product = entities.Product(organization=module_org).create()
    entities.Repository(product=product).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    product.sync()
    sync_plan.delete()
    with pytest.raises(HTTPError):
        sync_plan.read()


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_synced_product_custom_cron(module_org):
    """Create a sync plan with custom cron with one synced
    product and delete it.

    :id: f13936f5-7522-43b8-a986-26795637cde9

    :expectedresults: A sync plan is created with one synced product and
        sync plan can be deleted.

    :CaseLevel: Integration
    """
    sync_plan = entities.SyncPlan(
        organization=module_org,
        interval='custom cron',
        cron_expression=gen_choice(valid_cron_expressions()),
    ).create()
    product = entities.Product(organization=module_org).create()
    entities.Repository(product=product).create()
    sync_plan.add_products(data={'product_ids': [product.id]})
    product.sync()
    product = product.read()
    assert product.sync_plan.id == sync_plan.id
    sync_plan.delete()
    product = product.read()
    assert product.sync_plan is None
    with pytest.raises(HTTPError):
        sync_plan.read()
