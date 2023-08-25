"""Unit tests for the ``compute_resource`` paths.

A full API reference for compute resources can be found here:
http://www.katello.org/docs/api/apidoc/compute_resources.html


:Requirement: Computeresource Libvirt

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ComputeResources-libvirt

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants import FOREMAN_PROVIDERS
from robottelo.constants import LIBVIRT_RESOURCE_URL
from robottelo.utils.datafactory import invalid_values_list
from robottelo.utils.datafactory import parametrized
from robottelo.utils.datafactory import valid_data_list

pytestmark = [pytest.mark.skip_if_not_set('libvirt')]

LIBVIRT_URL = LIBVIRT_RESOURCE_URL % settings.libvirt.libvirt_hostname


@pytest.mark.e2e
def test_positive_crud_libvirt_cr(module_target_sat, module_org, module_location):
    """CRUD compute resource libvirt

    :id: 1e545c56-2f53-44c1-a17e-38c83f8fe0c2

    :expectedresults: Compute resources are created with expected names

    :CaseImportance: Critical

    :CaseLevel: Component
    """
    name = gen_string('alphanumeric')
    description = gen_string('alphanumeric')
    display_type = 'spice'
    libvirt_url = 'qemu+tcp://libvirt.example.com:16509/system'

    cr = module_target_sat.api.LibvirtComputeResource(
        name=name,
        description=description,
        provider=FOREMAN_PROVIDERS['libvirt'],
        display_type=display_type,
        organization=[module_org],
        location=[module_location],
        url=libvirt_url,
    ).create()
    assert cr.name == name
    assert cr.description == description
    assert cr.provider == FOREMAN_PROVIDERS['libvirt']
    assert cr.display_type == display_type
    assert cr.url == libvirt_url

    # Update
    new_name = gen_string('alphanumeric')
    new_description = gen_string('alphanumeric')
    new_display_type = 'vnc'
    new_org = module_target_sat.api.Organization().create()
    new_loc = module_target_sat.api.Location(organization=[new_org]).create()
    cr.name = new_name
    cr.description = new_description
    cr.display_type = new_display_type
    cr.url = LIBVIRT_URL
    cr.organization = [new_org]
    cr.location = [new_loc]
    cr.update(['name', 'description', 'display_type', 'url', 'organization', 'location'])

    # READ
    updated_cr = module_target_sat.api.LibvirtComputeResource(id=cr.id).read()
    assert updated_cr.name == new_name
    assert updated_cr.description == new_description
    assert updated_cr.display_type == new_display_type
    assert updated_cr.url == LIBVIRT_URL
    assert updated_cr.organization[0].id == new_org.id
    assert updated_cr.location[0].id == new_loc.id
    # DELETE
    updated_cr.delete()
    assert not module_target_sat.api.LibvirtComputeResource().search(
        query={'search': f'name={new_name}'}
    )


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
def test_positive_create_with_name_description(
    name, request, module_target_sat, module_org, module_location
):
    """Create compute resources with different names and descriptions

    :id: 1e545c56-2f53-44c1-a17e-38c83f8fe0c1

    :expectedresults: Compute resources are created with expected names and descriptions

    :CaseImportance: Critical

    :CaseLevel: Component

    :parametrized: yes
    """
    compresource = module_target_sat.api.LibvirtComputeResource(
        name=name,
        description=name,
        organization=[module_org],
        location=[module_location],
        url=LIBVIRT_URL,
    ).create()
    assert compresource.name == name
    assert compresource.description == name
    request.addfinalizer(compresource.delete)


@pytest.mark.tier2
def test_positive_create_with_orgs_and_locs(request, module_target_sat):
    """Create a compute resource with multiple organizations and locations

    :id: c6c6c6f7-50ca-4f38-8126-eb95359d7cbb

    :expectedresults: A compute resource is created with expected multiple
        locations assigned

    :CaseImportance: High

    :CaseLevel: Integration
    """
    orgs = [module_target_sat.api.Organization().create() for _ in range(2)]
    locs = [module_target_sat.api.Location(organization=[org]).create() for org in orgs]
    compresource = module_target_sat.api.LibvirtComputeResource(
        location=locs, organization=orgs, url=LIBVIRT_URL
    ).create()
    assert {org.name for org in orgs} == {org.read().name for org in compresource.organization}
    assert {loc.name for loc in locs} == {loc.read().name for loc in compresource.location}
    request.addfinalizer(compresource.delete)


@pytest.mark.tier2
@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
def test_negative_create_with_invalid_name(name, module_target_sat, module_org, module_location):
    """Attempt to create compute resources with invalid names

    :id: f73bf838-3ffd-46d3-869c-81b334b47b13

    :expectedresults: Compute resources are not created

    :CaseImportance: High

    :CaseLevel: Component

    :parametrized: yes
    """
    with pytest.raises(HTTPError):
        module_target_sat.api.LibvirtComputeResource(
            name=name,
            organization=[module_org],
            location=[module_location],
            url=LIBVIRT_URL,
        ).create()


@pytest.mark.tier2
def test_negative_create_with_same_name(request, module_target_sat, module_org, module_location):
    """Attempt to create a compute resource with already existing name

    :id: 9376e25c-2aa8-4d99-83aa-2eec160c030e

    :expectedresults: Compute resources is not created

    :CaseImportance: High

    :CaseLevel: Component
    """
    name = gen_string('alphanumeric')
    cr = module_target_sat.api.LibvirtComputeResource(
        location=[module_location], name=name, organization=[module_org], url=LIBVIRT_URL
    ).create()
    assert cr.name == name
    request.addfinalizer(cr.delete)
    with pytest.raises(HTTPError):
        module_target_sat.api.LibvirtComputeResource(
            name=name,
            organization=[module_org],
            location=[module_location],
            url=LIBVIRT_URL,
        ).create()


@pytest.mark.tier2
@pytest.mark.parametrize('url', **parametrized({'random': gen_string('alpha'), 'empty': ''}))
def test_negative_create_with_url(module_target_sat, module_org, module_location, url):
    """Attempt to create compute resources with invalid url

    :id: 37e9bf39-382e-4f02-af54-d3a17e285c2a

    :expectedresults: Compute resources are not created

    :CaseImportance: High

    :CaseLevel: Component

    :parametrized: yes
    """
    with pytest.raises(HTTPError):
        module_target_sat.api.LibvirtComputeResource(
            location=[module_location], organization=[module_org], url=url
        ).create()


@pytest.mark.tier2
@pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
def test_negative_update_invalid_name(
    request, module_target_sat, module_org, module_location, new_name
):
    """Attempt to update compute resource with invalid names

    :id: a6554c1f-e52f-4614-9fc3-2127ced31470

    :expectedresults: Compute resource is not updated

    :CaseImportance: High

    :CaseLevel: Component

    :parametrized: yes
    """
    name = gen_string('alphanumeric')
    compresource = module_target_sat.api.LibvirtComputeResource(
        location=[module_location], name=name, organization=[module_org], url=LIBVIRT_URL
    ).create()
    request.addfinalizer(compresource.delete)
    with pytest.raises(HTTPError):
        compresource.name = new_name
        compresource.update(['name'])
    assert compresource.read().name == name


@pytest.mark.tier2
def test_negative_update_same_name(request, module_target_sat, module_org, module_location):
    """Attempt to update a compute resource with already existing name

    :id: 4d7c5eb0-b8cb-414f-aa10-fe464a164ab4

    :expectedresults: Compute resources is not updated

    :CaseImportance: High

    :CaseLevel: Component
    """
    name = gen_string('alphanumeric')
    compresource = module_target_sat.api.LibvirtComputeResource(
        location=[module_location], name=name, organization=[module_org], url=LIBVIRT_URL
    ).create()
    new_compresource = module_target_sat.api.LibvirtComputeResource(
        location=[module_location], organization=[module_org], url=LIBVIRT_URL
    ).create()
    with pytest.raises(HTTPError):
        new_compresource.name = name
        new_compresource.update(['name'])
    assert new_compresource.read().name != name

    @request.addfinalizer
    def _finalize():
        compresource.delete()
        new_compresource.delete()


@pytest.mark.tier2
@pytest.mark.parametrize('url', **parametrized({'random': gen_string('alpha'), 'empty': ''}))
def test_negative_update_url(url, request, module_target_sat, module_org, module_location):
    """Attempt to update a compute resource with invalid url

    :id: b5256090-2ceb-4976-b54e-60d60419fe50

    :expectedresults: Compute resources is not updated

    :CaseImportance: High

    :CaseLevel: Component

    :parametrized: yes
    """
    compresource = module_target_sat.api.LibvirtComputeResource(
        location=[module_location], organization=[module_org], url=LIBVIRT_URL
    ).create()
    request.addfinalizer(compresource.delete)
    with pytest.raises(HTTPError):
        compresource.url = url
        compresource.update(['url'])
    assert compresource.read().url != url
