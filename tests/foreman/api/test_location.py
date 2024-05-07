"""Unit tests for the ``locations`` paths.

A full API reference for locations can be found here:
http://theforeman.org/api/apidoc/v2/locations.html

:Requirement: Location

:CaseAutomation: Automated

:CaseComponent: OrganizationsandLocations

:Team: Endeavour

:CaseImportance: High

"""

from random import randint

from fauxfactory import gen_integer, gen_string
import pytest
from requests.exceptions import HTTPError

from robottelo.constants import DEFAULT_LOC
from robottelo.utils.datafactory import (
    filtered_datapoint,
    invalid_values_list,
    parametrized,
)


@filtered_datapoint
def valid_loc_data_list():
    """List of valid data for input testing.

    Note: The maximum allowed length of location name is 246 only. This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)
    """
    return dict(
        alpha=gen_string('alpha', randint(1, 246)),
        numeric=gen_string('numeric', randint(1, 246)),
        alphanumeric=gen_string('alphanumeric', randint(1, 246)),
        latin1=gen_string('latin1', randint(1, 246)),
        utf8=gen_string('utf8', randint(1, 85)),
        cjk=gen_string('cjk', randint(1, 85)),
        html=gen_string('html', randint(1, 85)),
    )


class TestLocation:
    """Tests for the ``locations`` path."""

    # TODO Add coverage for media, realms as soon as they're implemented

    @pytest.fixture
    def make_proxies(self, target_sat):
        """Create a Proxy"""
        proxy1 = target_sat.cli_factory.make_proxy()
        proxy2 = target_sat.cli_factory.make_proxy()
        yield dict(proxy1=proxy1, proxy2=proxy2)
        target_sat.cli.Proxy.delete({'id': proxy1['id']})
        target_sat.cli.Proxy.delete({'id': proxy2['id']})

    @pytest.fixture
    def make_orgs(self, target_sat):
        """Create two organizations"""
        return dict(
            org=target_sat.api.Organization().create(), org2=target_sat.api.Organization().create()
        )

    @pytest.fixture
    def make_entities(self, target_sat):
        """Set up reusable entities for tests."""
        return dict(
            domain=target_sat.api.Domain().create(),
            subnet=target_sat.api.Subnet().create(),
            host_group=target_sat.api.HostGroup().create(),
            template=target_sat.api.ProvisioningTemplate().create(),
            test_cr=target_sat.api.LibvirtComputeResource().create(),
            new_user=target_sat.api.User().create(),
        )

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_loc_data_list()))
    def test_positive_create_with_name(self, name, target_sat):
        """Create new locations using different inputs as a name

        :id: 90bb90a3-120f-4ea6-89a9-62757be42486

        :expectedresults: Location created successfully and has expected and
            correct name

        :CaseImportance: Critical

        :parametrized: yes
        """
        location = target_sat.api.Location(name=name).create()
        assert location.name == name

    @pytest.mark.tier1
    def test_positive_create_and_delete_with_comma_separated_name(self, target_sat):
        """Create new location using name that has comma inside, delete location

        :id: 3131e99d-b278-462e-a650-a5a4f4e0a2f1

        :expectedresults: Location created successfully and has expected name
        """
        name = '{}, {}'.format(gen_string('alpha'), gen_string('alpha'))
        location = target_sat.api.Location(name=name).create()
        assert location.name == name
        location.delete()
        with pytest.raises(HTTPError):
            location.read()

    @pytest.mark.tier2
    def test_positive_create_and_update_with_org(self, make_orgs, target_sat):
        """Create new location with assigned organization to it

        :id: 5032a93f-4b37-4c19-b6d3-26e3a868d0f1

        :expectedresults: Location created successfully and has correct
            organization assigned to it with expected title

        """
        location = target_sat.api.Location(organization=[make_orgs['org']]).create()
        assert location.organization[0].id == make_orgs['org'].id
        assert location.organization[0].read().title == make_orgs['org'].title

        orgs = [make_orgs['org'], make_orgs['org2']]
        location.organization = orgs
        location = location.update(['organization'])
        assert {org.id for org in orgs} == {org.id for org in location.organization}

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
    def test_negative_create_with_name(self, name, target_sat):
        """Attempt to create new location using invalid names only

        :id: 320e6bca-5645-423b-b86a-2b6f35c8dae3

        :expectedresults: Location is not created and expected error is raised

        :CaseImportance: Critical

        :parametrized: yes
        """
        with pytest.raises(HTTPError):
            target_sat.api.Location(name=name).create()

    @pytest.mark.tier1
    def test_negative_create_with_same_name(self, target_sat):
        """Attempt to create new location using name of existing entity

        :id: bc09acb3-9ecf-4d23-b3ef-94f24e16e6db

        :expectedresults: Location is not created and expected error is raised

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        location = target_sat.api.Location(name=name).create()
        assert location.name == name
        with pytest.raises(HTTPError):
            target_sat.api.Location(name=name).create()

    @pytest.mark.tier1
    def test_negative_create_with_domain(self, target_sat):
        """Attempt to create new location using non-existent domain identifier

        :id: 5449532d-7959-4547-ba05-9e194eea495d

        :expectedresults: Location is not created and expected error is raised

        """
        with pytest.raises(HTTPError):
            target_sat.api.Location(domain=[gen_integer(10000, 99999)]).create()

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(valid_loc_data_list()))
    def test_positive_update_name(self, new_name, target_sat):
        """Update location with new name

        :id: 73ff6dab-e12a-4f7d-9c1f-6984fc076329

        :expectedresults: Location updated successfully and name was changed

        :CaseImportance: Critical

        :parametrized: yes
        """
        location = target_sat.api.Location().create()
        location.name = new_name
        assert location.update(['name']).name == new_name

    @pytest.mark.tier2
    def test_positive_update_entities(self, make_entities, target_sat):
        """Update location with new domain

        :id: 1016dfb9-8103-45f1-8738-0579fa9754c1

        :expectedresults: Location updated successfully and has correct domain
            assigned

        """
        location = target_sat.api.Location().create()

        location.domain = [make_entities["domain"]]
        location.subnet = [make_entities["subnet"]]
        location.hostgroup = [make_entities["host_group"]]
        location.provisioning_template = [make_entities["template"]]
        location.compute_resource = [make_entities["test_cr"]]
        location.user = [make_entities["new_user"]]

        assert location.update(['domain']).domain[0].id == make_entities["domain"].id
        assert location.update(['subnet']).subnet[0].id == make_entities["subnet"].id
        assert location.update(['hostgroup']).hostgroup[0].id == make_entities["host_group"].id
        ct_list = [
            ct
            for ct in location.update(['provisioning_template']).provisioning_template
            if ct.id == make_entities["template"].id
        ]
        assert len(ct_list) == 1
        assert (
            location.update(['compute_resource']).compute_resource[0].id
            == make_entities["test_cr"].id
        )
        assert location.compute_resource[0].read().provider == 'Libvirt'
        assert location.update(['user']).user[0].id == make_entities["new_user"].id

    @pytest.mark.run_in_one_thread
    @pytest.mark.tier2
    def test_positive_create_update_and_remove_capsule(self, make_proxies, target_sat):
        """Update location with new capsule

        :id: 2786146f-f466-4ed8-918a-5f46806558e2

        :expectedresults: Location updated successfully and has correct capsule
            assigned

        :BZ: 1398695

        :CaseImportance: High
        """
        proxy_id_1 = make_proxies['proxy1']['id']
        proxy_id_2 = make_proxies['proxy2']['id']

        proxy = target_sat.api.SmartProxy(id=proxy_id_1).read()
        location = target_sat.api.Location(smart_proxy=[proxy]).create()

        new_proxy = target_sat.api.SmartProxy(id=proxy_id_2).read()
        location.smart_proxy = [new_proxy]
        location = location.update(['smart_proxy'])
        assert location.smart_proxy[0].id == new_proxy.id
        assert location.smart_proxy[0].read().name == new_proxy.name

        location.smart_proxy = []
        location = location.update(['smart_proxy'])
        assert len(location.smart_proxy) == 0

    @pytest.mark.tier2
    def test_negative_update_domain(self, target_sat):
        """Try to update existing location with incorrect domain. Use
        domain id

        :id: e26c92f2-42cb-4706-9e03-3e00a134cb9f

        :expectedresults: Location is not updated

        """
        location = target_sat.api.Location(domain=[target_sat.api.Domain().create()]).create()
        domain = target_sat.api.Domain().create()
        location.domain[0].id = gen_integer(10000, 99999)
        with pytest.raises(HTTPError):
            assert location.update(['domain']).domain[0].id != domain.id

    @pytest.mark.tier1
    def test_default_loc_id_check(self, target_sat):
        """test to check the default_location id

        :id: 3c89d63b-d5fb-4f05-9efb-f560f0194c85

        :BZ: 1713269

        :expectedresults: The default_location ID remain 2.

        """
        default_loc_id = (
            target_sat.api.Location().search(query={'search': f'name="{DEFAULT_LOC}"'})[0].id
        )
        assert default_loc_id == 2

    @pytest.mark.tier1
    def test_positive_get_location_by_name(self, make_entities, target_sat):
        """test to search location by name

        :id: 9721bd0c-df51-11eb-9353-b0a460e02491

        :BZ: 1566630

        :steps:
            1. Make an API call to create a location
            2. Search the location by name

        :expectedresults: Location search by name returns success

        :CaseImportance: High
        """
        name = gen_string('alphanumeric')
        target_sat.api.Location(name=name).create()
        loc_name = target_sat.api.Location().search(query={'search': f'name="{name}"'})[0].name
        assert loc_name == name
