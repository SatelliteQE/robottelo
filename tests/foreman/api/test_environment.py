"""Unit tests for the ``environments`` paths.

A full API reference for environments can be found here:
http://theforeman.org/api/apidoc/v2/environments.html


:Requirement: Environment

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Puppet

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.api.utils import one_to_many_names
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import parametrized


@filtered_datapoint
def valid_data_list():
    """Return a list of various kinds of valid strings for Environment entity"""
    return [gen_string('alpha'), gen_string('numeric'), gen_string('alphanumeric')]


def _org(request):
    api = entities.Organization()
    org = api.create()

    @request.addfinalizer
    def _cleanup():
        # Delete organization if it still exists
        if org.id in [o.id for o in api.search()]:
            org.delete()

    return org


def _location(request):
    api = entities.Location()
    loc = api.create()

    @request.addfinalizer
    def _cleanup():
        # Delete location if it still exists
        if loc.id in [o.id for o in api.search()]:
            loc.delete()

    return loc


def _environment(request, **kwargs):
    api = entities.Environment(**kwargs)
    env = api.create()

    @request.addfinalizer
    def _cleanup():
        # Delete environment if it still exists
        if env.id in [o.id for o in api.search()]:
            env.delete()

    return env


@pytest.fixture
def _make_org(request):
    yield _org(request)


@pytest.fixture
def _make_loc(request):
    yield _location(request)


@pytest.fixture
def _make_env(request):
    yield _environment(request)


@pytest.fixture
def env_attrs(_make_env):
    yield set(_make_env.update_json([]).keys())


class TestEnvironment:
    """Tests for environments."""

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_create_with_name(self, request, name):
        """Create an environment and provide a valid name.

        :id: 8869ccf8-a511-4fa7-ac36-11494e85f532

        :expectedresults: The environment created successfully and has expected
            name.

        :CaseImportance: Critical
        """
        env = _environment(request, name=name)
        assert env.name == name

    @pytest.mark.tier1
    def test_positive_create_with_org_and_loc(self, request, _make_org, _make_loc):
        """Create an environment and assign it to new organization.

        :id: de7e4132-5ca7-4b41-9af3-df075d31f8f4

        :expectedresults: The environment created successfully and has expected
            attributes.

        :CaseImportance: Critical
        """
        env = _environment(
            request,
            name=gen_string('alphanumeric'),
            organization=[_make_org],
            location=[_make_loc],
        )
        assert len(env.organization) == 1
        assert env.organization[0].id == _make_org.id
        assert len(env.location) == 1
        assert env.location[0].id == _make_loc.id

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
    def test_negative_create_with_too_long_name(self, request, name):
        """Create an environment and provide an invalid name.

        :id: e2654954-b3a1-4594-a487-bcd0cc8195ad

        :expectedresults: The server returns an error.

        """
        with pytest.raises(HTTPError):
            _environment(request, name=name)

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'name', **parametrized([gen_string(s) for s in ('cjk', 'latin1', 'utf8')])
    )
    def test_negative_create_with_invalid_characters(self, request, name):
        """Create an environment and provide an illegal name.

        :id: 8ec57d04-4ce6-48b4-b7f9-79025019ad0f

        :expectedresults: The server returns an error.

        """
        with pytest.raises(HTTPError):
            _environment(request, name=name)

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_data_list()))
    def test_positive_update_name(self, request, name):
        """Create environment entity providing the initial name, then
        update its name to another valid name.

        :id: ef48e79a-6b6a-4811-b49b-09f2effdd18f

        :expectedresults: Environment entity is created and updated properly

        """
        env = _environment(request)
        env.name = name
        env = env.update(['name'])
        assert env.name == name

    @pytest.mark.tier2
    def test_positive_update_and_remove(self, request, _make_org, _make_loc):
        """Update environment and assign it to a new organization
        and location. Delete environment afterwards.

        :id: 31e43faa-65ee-4757-ac3d-3825eba37ae5

        :expectedresults: Environment entity is updated and removed
            properly

        :CaseImportance: Critical

        :CaseLevel: Integration
        """
        env = _environment(request)
        assert len(env.organization) == 0
        assert len(env.location) == 0

        env.organization = [_make_org]
        env = env.update(['organization'])
        assert len(env.organization) == 1
        assert env.organization[0].id == _make_org.id

        env.location = [_make_loc]
        env = env.update(['location'])
        assert len(env.location) == 1
        assert env.location[0].id == _make_loc.id

        env.delete()
        with pytest.raises(HTTPError):
            env.read()

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
    def test_negative_update_name(self, name, _make_env):
        """Create environment entity providing the initial name, then
        try to update its name to invalid one.

        :id: 9cd024ab-db3d-4b15-b6da-dd2089321df3

        :expectedresults: Environment entity is not updated

        """
        with pytest.raises(HTTPError):
            entities.Environment(id=_make_env.id, name=name).update(['name'])


class TestMissingAttrEnvironment:
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. The ``one_to_*_names`` functions know what names
    Satellite may assign to fields.

    """

    @pytest.mark.tier2
    def test_positive_update_loc(self, env_attrs):
        """Update an environment. Inspect the server's response.

        :id: a4c1bc22-d586-4150-92fc-7797f0f5bfb0

        :expectedresults: The response contains some value for the ``location``
            field.

        :BZ: 1262029

        :CaseLevel: Integration
        """
        names = one_to_many_names('location')
        assert len(names & env_attrs) >= 1, f"None of {names} are in {env_attrs}"

    @pytest.mark.tier2
    def test_positive_update_org(self, env_attrs):
        """Update an environment. Inspect the server's response.

        :id: ac46bcac-5db0-4899-b2fc-d48d2116287e

        :expectedresults: The response contains some value for the
            ``organization`` field.

        :BZ: 1262029

        :CaseLevel: Integration
        """
        names = one_to_many_names('organization')
        assert len(names & env_attrs) >= 1, f"None of {names} are in {env_attrs}"
