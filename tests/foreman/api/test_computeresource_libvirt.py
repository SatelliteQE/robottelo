"""Unit tests for the ``compute_resource`` paths.

A full API reference for compute resources can be found here:
http://www.katello.org/docs/api/apidoc/compute_resources.html


:Requirement: Computeresource Libvirt

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint

import pytest
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants import LIBVIRT_RESOURCE_URL
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_data_list
from robottelo.decorators import skip_if_not_set


@pytest.fixture(scope="module")
@skip_if_not_set('compute_resources')
def setup():
    """Set up organization and location for tests."""
    setupEntities = type("", (), {})()
    setupEntities.org = entities.Organization().create()
    setupEntities.loc = entities.Location(organization=[setupEntities.org]).create()
    setupEntities.current_libvirt_url = (
        LIBVIRT_RESOURCE_URL % settings.compute_resources.libvirt_hostname
    )
    return setupEntities


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_create_with_name(setup, name):
    """Create compute resources with different names

    :id: 1e545c56-2f53-44c1-a17e-38c83f8fe0c1

    :expectedresults: Compute resources are created with expected names

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    compresource = entities.LibvirtComputeResource(
        location=[setup.loc],
        name=name,
        organization=[setup.org],
        url=setup.current_libvirt_url,
    ).create()
    assert compresource.name == name


@pytest.mark.tier1
@pytest.mark.parametrize('description', **parametrized(valid_data_list()))
def test_positive_create_with_description(setup, description):
    """Create compute resources with different descriptions

    :id: 1fa5b35d-ee47-452b-bb5f-4a4ca321f992

    :expectedresults: Compute resources are created with expected
        descriptions

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    compresource = entities.LibvirtComputeResource(
        description=description,
        location=[setup.loc],
        organization=[setup.org],
        url=setup.current_libvirt_url,
    ).create()
    assert compresource.description == description


@pytest.mark.tier2
@pytest.mark.parametrize('display_type', ['spice', 'vnc'])
def test_positive_create_libvirt_with_display_type(setup, display_type):
    """Create a libvirt compute resources with different values of
    'display_type' parameter

    :id: 76380f31-e217-4ff1-ac6b-20f41e59f133

    :expectedresults: Compute resources are created with expected
        display_type value

    :CaseImportance: High

    :CaseLevel: Component
    """
    compresource = entities.LibvirtComputeResource(
        display_type=display_type,
        location=[setup.loc],
        organization=[setup.org],
        url=setup.current_libvirt_url,
    ).create()
    assert compresource.display_type == display_type


@pytest.mark.tier1
def test_positive_create_with_provider(setup):
    """Create compute resources with different providers. Testing only
    Libvirt and Docker as other providers require valid credentials

    :id: f61c66c9-15f8-4b00-9e53-7ebfb09397cc

    :expectedresults: Compute resources are created with expected providers

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    entity = entities.LibvirtComputeResource()
    entity.location = [setup.loc]
    entity.organization = [setup.org]
    result = entity.create()
    assert result.provider == entity.provider


@pytest.mark.tier2
def test_positive_create_with_locs(setup):
    """Create a compute resource with multiple locations

    :id: c6c6c6f7-50ca-4f38-8126-eb95359d7cbb

    :expectedresults: A compute resource is created with expected multiple
        locations assigned

    :CaseImportance: High

    :CaseLevel: Integration
    """
    locs = [entities.Location(organization=[setup.org]).create() for _ in range(randint(3, 5))]
    compresource = entities.LibvirtComputeResource(
        location=locs, organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    assert {loc.name for loc in locs} == {loc.read().name for loc in compresource.location}


@pytest.mark.tier2
def test_positive_create_with_orgs(setup):
    """Create a compute resource with multiple organizations

    :id: 2f6e5019-6353-477e-a81f-2a551afc7556

    :expectedresults: A compute resource is created with expected multiple
        organizations assigned

    :CaseImportance: High

    :CaseLevel: Integration
    """
    orgs = [entities.Organization().create() for _ in range(randint(3, 5))]
    compresource = entities.LibvirtComputeResource(
        organization=orgs, url=setup.current_libvirt_url
    ).create()
    assert {org.name for org in orgs} == {org.read().name for org in compresource.organization}


@pytest.mark.tier1
@pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
def test_positive_update_name(setup, new_name):
    """Update a compute resource with different names

    :id: 60f08418-b1a2-445e-9cd6-dbc92a33b57a

    :expectedresults: Compute resource is updated with expected names

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    compresource = entities.LibvirtComputeResource(
        location=[setup.loc], organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    compresource.name = new_name
    compresource = compresource.update(['name'])
    assert compresource.name == new_name


@pytest.mark.tier2
@pytest.mark.parametrize('new_description', **parametrized(valid_data_list()))
def test_positive_update_description(setup, new_description):
    """Update a compute resource with different descriptions

    :id: aac5dc53-8709-441b-b360-28b8efd3f63f

    :expectedresults: Compute resource is updated with expected
        descriptions

    :CaseImportance: High

    :CaseLevel: Component
    """
    compresource = entities.LibvirtComputeResource(
        description=gen_string('alpha'),
        location=[setup.loc],
        organization=[setup.org],
        url=setup.current_libvirt_url,
    ).create()
    compresource.description = new_description
    compresource = compresource.update(['description'])
    assert compresource.description == new_description


@pytest.mark.tier2
@pytest.mark.parametrize('display_type', ['spice', 'vnc'])
def test_positive_update_libvirt_display_type(setup, display_type):
    """Update a libvirt compute resource with different values of
    'display_type' parameter

    :id: 0cbf08ac-acc4-476a-b389-271cea2b6cda

    :expectedresults: Compute resource is updated with expected
        display_type value

    :CaseImportance: High

    :CaseLevel: Component
    """
    compresource = entities.LibvirtComputeResource(
        display_type='VNC',
        location=[setup.loc],
        organization=[setup.org],
        url=setup.current_libvirt_url,
    ).create()
    compresource.display_type = display_type
    compresource = compresource.update(['display_type'])
    assert compresource.display_type == display_type


@pytest.mark.tier2
def test_positive_update_url(setup):
    """Update a compute resource's url field

    :id: 259aa060-ed9e-4ed5-91e1-7fb0a3592879

    :expectedresults: Compute resource is updated with expected url

    :CaseImportance: High

    :CaseLevel: Component
    """
    new_url = 'qemu+tcp://localhost:16509/system'

    compresource = entities.LibvirtComputeResource(
        location=[setup.loc], organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    compresource.url = new_url
    compresource = compresource.update(['url'])
    assert compresource.url == new_url


@pytest.mark.tier2
def test_positive_update_loc(setup):
    """Update a compute resource's location

    :id: 57e96c7c-da9e-4400-af80-c374cd6b3d4a

    :expectedresults: Compute resource is updated with expected location

    :CaseImportance: High

    :CaseLevel: Integration
    """
    compresource = entities.LibvirtComputeResource(
        location=[setup.loc], organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    new_loc = entities.Location(organization=[setup.org]).create()
    compresource.location = [new_loc]
    compresource = compresource.update(['location'])
    assert len(compresource.location) == 1
    assert compresource.location[0].id == new_loc.id


@pytest.mark.tier2
def test_positive_update_locs(setup):
    """Update a compute resource with new multiple locations

    :id: cda9f501-2879-4cb0-a017-51ee795232f1

    :expectedresults: Compute resource is updated with expected locations

    :CaseImportance: High

    :CaseLevel: Integration
    """
    compresource = entities.LibvirtComputeResource(
        location=[setup.loc], organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    new_locs = [entities.Location(organization=[setup.org]).create() for _ in range(randint(3, 5))]
    compresource.location = new_locs
    compresource = compresource.update(['location'])
    assert {location.id for location in compresource.location} == {
        location.id for location in new_locs
    }


@pytest.mark.tier2
def test_positive_update_org(setup):
    """Update a compute resource's organization

    :id: 430b64a2-7f64-4344-a73b-1b47d8dfa6cb

    :expectedresults: Compute resource is updated with expected
        organization

    :CaseImportance: High

    :CaseLevel: Integration
    """
    compresource = entities.LibvirtComputeResource(
        organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    new_org = entities.Organization().create()
    compresource.organization = [new_org]
    compresource = compresource.update(['organization'])
    assert len(compresource.organization) == 1
    assert compresource.organization[0].id == new_org.id


@pytest.mark.tier2
def test_positive_update_orgs(setup):
    """Update a compute resource with new multiple organizations

    :id: 2c759ad5-d115-46d9-8365-712c0bb39a1d

    :expectedresults: Compute resource is updated with expected
        organizations

    :CaseImportance: High

    :CaseLevel: Integration
    """
    compresource = entities.LibvirtComputeResource(
        organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    new_orgs = [entities.Organization().create() for _ in range(randint(3, 5))]
    compresource.organization = new_orgs
    compresource = compresource.update(['organization'])
    assert {organization.id for organization in compresource.organization} == {
        organization.id for organization in new_orgs
    }


@pytest.mark.tier1
def test_positive_delete(setup):
    """Delete a compute resource

    :id: 0117a4f1-e2c2-44aa-8919-453166aeebbc

    :expectedresults: Compute resources is successfully deleted

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    compresource = entities.LibvirtComputeResource(
        location=[setup.loc], organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    compresource.delete()
    with pytest.raises(HTTPError):
        compresource.read()


@pytest.mark.tier2
@pytest.mark.parametrize('name', invalid_values_list())
def test_negative_create_with_invalid_name(setup, name):
    """Attempt to create compute resources with invalid names

    :id: f73bf838-3ffd-46d3-869c-81b334b47b13

    :expectedresults: Compute resources are not created

    :CaseImportance: High

    :CaseLevel: Component
    """
    with pytest.raises(HTTPError):
        entities.LibvirtComputeResource(
            location=[setup.loc],
            name=name,
            organization=[setup.org],
            url=setup.current_libvirt_url,
        ).create()


@pytest.mark.tier2
def test_negative_create_with_same_name(setup):
    """Attempt to create a compute resource with already existing name

    :id: 9376e25c-2aa8-4d99-83aa-2eec160c030e

    :expectedresults: Compute resources is not created

    :CaseImportance: High

    :CaseLevel: Component
    """
    name = gen_string('alphanumeric')
    entities.LibvirtComputeResource(
        location=[setup.loc], name=name, organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    with pytest.raises(HTTPError):
        entities.LibvirtComputeResource(
            location=[setup.loc],
            name=name,
            organization=[setup.org],
            url=setup.current_libvirt_url,
        ).create()


@pytest.mark.tier2
@pytest.mark.parametrize('url', ['', gen_string('alpha')])
def test_negative_create_with_url(setup, url):
    """Attempt to create compute resources with invalid url

    :id: 37e9bf39-382e-4f02-af54-d3a17e285c2a

    :expectedresults: Compute resources are not created

    :CaseImportance: High

    :CaseLevel: Component
    """
    with pytest.raises(HTTPError):
        entities.LibvirtComputeResource(
            location=[setup.loc], organization=[setup.org], url=url
        ).create()


@pytest.mark.tier2
@pytest.mark.parametrize('new_name', invalid_values_list())
def test_negative_update_invalid_name(setup, new_name):
    """Attempt to update compute resource with invalid names

    :id: a6554c1f-e52f-4614-9fc3-2127ced31470

    :expectedresults: Compute resource is not updated

    :CaseImportance: High

    :CaseLevel: Component
    """
    name = gen_string('alphanumeric')
    compresource = entities.LibvirtComputeResource(
        location=[setup.loc], name=name, organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    with pytest.raises(HTTPError):
        compresource.name = new_name
        compresource.update(['name'])
    assert compresource.read().name == name


@pytest.mark.tier2
def test_negative_update_same_name(setup):
    """Attempt to update a compute resource with already existing name

    :id: 4d7c5eb0-b8cb-414f-aa10-fe464a164ab4

    :expectedresults: Compute resources is not updated

    :CaseImportance: High

    :CaseLevel: Component
    """
    name = gen_string('alphanumeric')
    entities.LibvirtComputeResource(
        location=[setup.loc], name=name, organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    new_compresource = entities.LibvirtComputeResource(
        location=[setup.loc], organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    with pytest.raises(HTTPError):
        new_compresource.name = name
        new_compresource.update(['name'])
    assert new_compresource.read().name != name


@pytest.mark.tier2
@pytest.mark.parametrize('url', ['', gen_string('alpha')])
def test_negative_update_url(setup, url):
    """Attempt to update a compute resource with invalid url

    :id: b5256090-2ceb-4976-b54e-60d60419fe50

    :expectedresults: Compute resources is not updated

    :CaseImportance: High

    :CaseLevel: Component
    """
    compresource = entities.LibvirtComputeResource(
        location=[setup.loc], organization=[setup.org], url=setup.current_libvirt_url
    ).create()
    with pytest.raises(HTTPError):
        compresource.url = url
        compresource.update(['url'])
    assert compresource.read().url != url
