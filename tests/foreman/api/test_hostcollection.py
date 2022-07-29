"""Unit tests for host collections.

:Requirement: Hostcollection

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: HostCollections

:Assignee: spusater

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice
from random import randint

import pytest
from broker import Broker
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.hosts import ContentHost


@pytest.fixture(scope='module')
def fake_hosts(module_org):
    """Create content hosts that can be shared by tests."""
    hosts = [entities.Host(organization=module_org).create() for _ in range(2)]
    return hosts


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_name(module_org, name):
    """Create host collections with different names.

    :id: 8f2b9223-f5be-4cb1-8316-01ea747cae14

    :parametrized: yes

    :expectedresults: The host collection was successfully created and has
        appropriate name.

    :CaseImportance: Critical
    """
    host_collection = entities.HostCollection(name=name, organization=module_org).create()
    assert host_collection.name == name


@pytest.mark.tier1
def test_positive_list(module_org):
    """Create new host collection and then retrieve list of all existing
    host collections

    :id: 6ae32df2-b917-4830-8709-15fb272b76c1

    :BZ: 1331875

    :customerscenario: true

    :expectedresults: Returned list of host collections for the system
        contains at least one collection

    :CaseImportance: Critical
    """
    entities.HostCollection(organization=module_org).create()
    hc_list = entities.HostCollection().search()
    assert len(hc_list) >= 1


@pytest.mark.tier1
def test_positive_list_for_organization():
    """Create host collection for specific organization. Retrieve list of
    host collections for that organization

    :id: 5f9de8ab-2c53-401b-add3-57d86c97563a

    :expectedresults: The host collection was successfully created and
        present in the list of collections for specific organization

    :CaseImportance: Critical
    """
    org = entities.Organization().create()
    hc = entities.HostCollection(organization=org).create()
    hc_list = entities.HostCollection(organization=org).search()
    assert len(hc_list) == 1
    assert hc_list[0].id == hc.id


@pytest.mark.parametrize('desc', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_description(module_org, desc):
    """Create host collections with different descriptions.

    :id: 9d13392f-8d9d-4ff1-8909-4233e4691055

    :parametrized: yes

    :expectedresults: The host collection was successfully created and has
        appropriate description.

    :CaseImportance: Critical
    """
    host_collection = entities.HostCollection(description=desc, organization=module_org).create()
    assert host_collection.description == desc


@pytest.mark.tier1
def test_positive_create_with_limit(module_org):
    """Create host collections with different limits.

    :id: 86d9387b-7036-4794-96fd-5a3472dd9160

    :expectedresults: The host collection was successfully created and has
        appropriate limit.

    :CaseImportance: Critical
    """
    for _ in range(5):
        limit = randint(1, 30)
        host_collection = entities.HostCollection(max_hosts=limit, organization=module_org).create()
        assert host_collection.max_hosts == limit


@pytest.mark.parametrize("unlimited", [False, True])
@pytest.mark.tier1
def test_positive_create_with_unlimited_hosts(module_org, unlimited):
    """Create host collection with different values of 'unlimited hosts'
    parameter.

    :id: d385574e-5794-4442-b6cd-e5ded001d877

    :parametrized: yes

    :expectedresults: The host collection was successfully created and has
        appropriate 'unlimited hosts' parameter value.

    :CaseImportance: Critical
    """
    host_collection = entities.HostCollection(
        max_hosts=None if unlimited else 1,
        organization=module_org,
        unlimited_hosts=unlimited,
    ).create()
    assert host_collection.unlimited_hosts == unlimited


@pytest.mark.tier1
def test_positive_create_with_host(module_org, fake_hosts):
    """Create a host collection that contains a host.

    :id: 9dc0ad72-58c2-4079-b1ca-2c4373472f0f

    :expectedresults: The host collection can be read back, and it includes
        one host.

    :CaseImportance: Critical

    :BZ: 1325989
    """
    host_collection = entities.HostCollection(
        host=[fake_hosts[0]], organization=module_org
    ).create()
    assert len(host_collection.host) == 1


@pytest.mark.tier1
def test_positive_create_with_hosts(module_org, fake_hosts):
    """Create a host collection that contains hosts.

    :id: bb8d2b42-9a8b-4c4f-ba0c-c56ae5a7eb1d

    :expectedresults: The host collection can be read back, and it
        references two hosts.

    :CaseImportance: Critical

    :BZ: 1325989
    """
    host_collection = entities.HostCollection(host=fake_hosts, organization=module_org).create()
    assert len(host_collection.host) == len(fake_hosts)


@pytest.mark.tier2
def test_positive_add_host(module_org, fake_hosts):
    """Add a host to host collection.

    :id: da8bc901-7ac8-4029-bb62-af21aa4d3a88

    :expectedresults: Host was added to the host collection.

    :CaseLevel: Integration

    :BZ:1325989
    """
    host_collection = entities.HostCollection(organization=module_org).create()
    host_collection.host_ids = [fake_hosts[0].id]
    host_collection = host_collection.update(['host_ids'])
    assert len(host_collection.host) == 1


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_add_hosts(module_org, fake_hosts):
    """Add hosts to host collection.

    :id: f76b4db1-ccd5-47ab-be15-8c7d91d03b22

    :expectedresults: Hosts were added to the host collection.

    :CaseLevel: Integration

    :BZ: 1325989
    """
    host_collection = entities.HostCollection(organization=module_org).create()
    host_ids = [str(host.id) for host in fake_hosts]
    host_collection.host_ids = host_ids
    host_collection = host_collection.update(['host_ids'])
    assert len(host_collection.host) == len(fake_hosts)


@pytest.mark.tier1
def test_positive_read_host_ids(module_org, fake_hosts):
    """Read a host collection and look at the ``host_ids`` field.

    :id: 444a1528-64c8-41b6-ba2b-6c49799d5980

    :expectedresults: The ``host_ids`` field matches the host IDs passed in
        when creating the host collection.

    :CaseImportance: Critical

    :BZ:1325989
    """
    host_collection = entities.HostCollection(host=fake_hosts, organization=module_org).create()
    assert frozenset(host.id for host in host_collection.host) == frozenset(
        host.id for host in fake_hosts
    )


@pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_update_name(module_org, new_name):
    """Check if host collection name can be updated

    :id: b2dedb99-6dd7-41be-8aaa-74065c820ac6

    :parametrized: yes

    :expectedresults: Host collection name was successfully updated

    :CaseImportance: Critical
    """
    host_collection = entities.HostCollection(organization=module_org).create()
    host_collection.name = new_name
    assert host_collection.update().name == new_name


@pytest.mark.parametrize('new_desc', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_update_description(module_org, new_desc):
    """Check if host collection description can be updated

    :id: f8e9bd1c-1525-4b5f-a07c-eb6b6e7aa628

    :parametrized: yes

    :expectedresults: Host collection description was updated

    :CaseImportance: Critical
    """
    host_collection = entities.HostCollection(organization=module_org).create()
    host_collection.description = new_desc
    assert host_collection.update().description == new_desc


@pytest.mark.tier1
def test_positive_update_limit(module_org):
    """Check if host collection limit can be updated

    :id: 4eda7796-cd81-453b-9b72-4ef84b2c1d8c

    :expectedresults: Host collection limit was updated

    :CaseImportance: Critical
    """
    host_collection = entities.HostCollection(
        max_hosts=1, organization=module_org, unlimited_hosts=False
    ).create()
    for limit in (1, 3, 5, 10, 20):
        host_collection.max_hosts = limit
        assert host_collection.update().max_hosts == limit


@pytest.mark.tier1
def test_positive_update_unlimited_hosts(module_org):
    """Check if host collection 'unlimited hosts' parameter can be updated

    :id: 09a3973d-9832-4255-87bf-f9eaeab4aee8

    :expectedresults: Host collection 'unlimited hosts' parameter was
        updated

    :CaseImportance: Critical
    """
    random_unlimited = choice([True, False])
    host_collection = entities.HostCollection(
        max_hosts=1 if not random_unlimited else None,
        organization=module_org,
        unlimited_hosts=random_unlimited,
    ).create()
    for unlimited in (not random_unlimited, random_unlimited):
        host_collection.max_hosts = 1 if not unlimited else None
        host_collection.unlimited_hosts = unlimited
        host_collection = host_collection.update(['max_hosts', 'unlimited_hosts'])
        assert host_collection.unlimited_hosts == unlimited


@pytest.mark.tier1
def test_positive_update_host(module_org, fake_hosts):
    """Update host collection's host.

    :id: 23082854-abcf-4085-be9c-a5d155446acb

    :expectedresults: The host collection was updated with a new host.

    :CaseImportance: Critical
    """
    host_collection = entities.HostCollection(
        host=[fake_hosts[0]], organization=module_org
    ).create()
    host_collection.host_ids = [fake_hosts[1].id]
    host_collection = host_collection.update(['host_ids'])
    assert host_collection.host[0].id == fake_hosts[1].id


@pytest.mark.upgrade
@pytest.mark.tier1
def test_positive_update_hosts(module_org, fake_hosts):
    """Update host collection's hosts.

    :id: 0433b37d-ae16-456f-a51d-c7b800334861

    :expectedresults: The host collection was updated with new hosts.

    :CaseImportance: Critical
    """
    host_collection = entities.HostCollection(host=fake_hosts, organization=module_org).create()
    new_hosts = [entities.Host(organization=module_org).create() for _ in range(2)]
    host_ids = [str(host.id) for host in new_hosts]
    host_collection.host_ids = host_ids
    host_collection = host_collection.update(['host_ids'])
    assert {host.id for host in host_collection.host} == {host.id for host in new_hosts}


@pytest.mark.upgrade
@pytest.mark.tier1
def test_positive_delete(module_org):
    """Check if host collection can be deleted

    :id: 13a16cd2-16ce-4966-8c03-5d821edf963b

    :expectedresults: Host collection was successfully deleted

    :CaseImportance: Critical
    """
    host_collection = entities.HostCollection(organization=module_org).create()
    host_collection.delete()
    with pytest.raises(HTTPError):
        host_collection.read()


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_create_with_invalid_name(module_org, name):
    """Try to create host collections with different invalid names

    :id: 38f67d04-a19d-4eab-a577-21b8d62c7389

    :parametrized: yes

    :expectedresults: The host collection was not created

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError):
        entities.HostCollection(name=name, organization=module_org).create()


@pytest.mark.tier1
def test_positive_add_remove_subscription(module_org, module_ak_cv_lce, target_sat):
    """Try to bulk add and remove a subscription to members of a host collection.

    :id: c4ec5727-eb25-452e-a91f-87cafb16666b

    :steps:

        1. Create HC, add AK to HC
        2. Create product so we can use it's subscription
        3. Create some VMs and register them with AK so they are in HC
        4. Add the subscription to the members of the Host Collection
        5. Assert subscription is added
        6. Bulk remove subscription
        7. Assert it is removed

    :expectedresults: subscription added to, and removed from, members of host collection

    :CaseImportance: Critical
    """
    # this command creates a host collection and "appends", makes available, to the AK
    module_ak_cv_lce.host_collection.append(
        entities.HostCollection(organization=module_org).create()
    )
    # Move HC from Add tab to List tab on AK view
    module_ak_cv_lce = module_ak_cv_lce.update(['host_collection'])
    # Create a product so we have a subscription to use
    product = entities.Product(organization=module_org).create()
    prod_name = product.name
    product_subscription = entities.Subscription(organization=module_org).search(
        query={'search': f'name={prod_name}'}
    )[0]
    # Create and register VMs as members of Host Collection
    with Broker(nick='rhel7', host_classes={'host': ContentHost}, _count=2) as hosts:
        for client in hosts:
            client.install_katello_ca(target_sat)
            client.register_contenthost(module_org.label, module_ak_cv_lce.name)
        # Read host_collection back from Satellite to get host_ids
        host_collection = module_ak_cv_lce.host_collection[0].read()
        host_ids = [host.id for host in host_collection.host]
        # Add subscription
        # Call nailgun to make the API PUT to members of Host Collection
        entities.Host().bulk_add_subscriptions(
            data={
                "organization_id": module_org.id,
                "included": {"ids": host_ids},
                "subscriptions": [{"id": product_subscription.id, "quantity": 1}],
            }
        )
        # GET the subscriptions from hosts and assert they are there
        for host_id in host_ids:
            req = entities.HostSubscription(host=host_id).subscriptions()
            assert (
                prod_name in req['results'][0]['product_name']
            ), 'Subscription not applied to HC members'
        # Remove the subscription
        # Call nailgun to make the API PUT to members of Host Collection
        entities.Host().bulk_remove_subscriptions(
            data={
                "organization_id": module_org.id,
                "included": {"ids": host_ids},
                "subscriptions": [{"id": product_subscription.id, "quantity": 1}],
            }
        )
        # GET the subscriptions from hosts and assert they are gone
        for host_id in host_ids:
            req = entities.HostSubscription(host=host_id).subscriptions()
            assert not req['results'], 'Subscription not removed from HC members'
