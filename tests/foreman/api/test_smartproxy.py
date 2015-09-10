"""Tests for the ``smart_proxies`` paths."""
from nailgun import entities
from nailgun.entity_mixins import _get_entity_ids
from robottelo.common.decorators import run_only_on, stubbed, skip_if_bug_open
from robottelo.test import APITestCase


@skip_if_bug_open('bugzilla', 1262037)
class MissingAttrTestCase(APITestCase):
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. Satellite may name a given attribute in one of several
    ways, and the ``_get_entity_*`` methods know about all the names Satellite
    may give to an attribute.

    """

    @classmethod
    def setUpClass(cls):
        """Find a ``SmartProxy``.

        Every Satellite has a built-in smart proxy, so searching for an
        existing smart proxy should always succeed.

        """
        smart_proxies = entities.SmartProxy().search()
        assert len(smart_proxies) > 0
        cls.smart_proxy_attrs = smart_proxies[0].update_json([])

    def test_location(self):
        """@Test: Update a smart proxy. Inspect the server's response.

        @Assert: The response contains some value for the ``location`` field.

        @Feature: SmartProxy

        """
        _get_entity_ids('location', self.smart_proxy_attrs)

    def test_organization(self):
        """@Test: Update a smart proxy. Inspect the server's response.

        @Assert: The response contains some value for the ``organization``
        field.

        @Feature: SmartProxy

        """
        _get_entity_ids('organization', self.smart_proxy_attrs)


@run_only_on('sat')
class SmartProxyTestCaseStub(APITestCase):
    """Incomplete tests for smart proxies.

    When implemented, each of these tests should probably be data-driven. A
    decorator of this form might be used::

        @data(
            medium name is alpha,
            medium name is alpha_numeric,
            medium name is html,
            medium name is latin1,
            medium name is numeric,
            medium name is utf-8,
        )

    """

    @stubbed()
    def test_add_smartproxy_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

    @stubbed()
    def test_add_smartproxy_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

    @stubbed()
    def test_add_smartproxy_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

    @stubbed()
    def test_add_smartproxy_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

    @stubbed()
    def test_remove_smartproxy_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

    @stubbed()
    def test_remove_smartproxy_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

    @stubbed()
    def test_remove_smartproxy_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """

    @stubbed()
    def test_remove_smartproxy_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """
