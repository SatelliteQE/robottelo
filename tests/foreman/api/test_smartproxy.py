"""Tests for the ``smart_proxies`` paths."""
from nailgun import entities
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
)
from robottelo.test import APITestCase
from robottelo.api.utils import one_to_many_names


@skip_if_bug_open('bugzilla', 1262037)
class SmartProxyMissingAttrTestCase(APITestCase):
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. The ``one_to_*_names`` functions know what names
    Satellite may assign to fields.
    """

    @classmethod
    def setUpClass(cls):
        """Find a ``SmartProxy``.

        Every Satellite has a built-in smart proxy, so searching for an
        existing smart proxy should always succeed.
        """
        super(SmartProxyMissingAttrTestCase, cls).setUpClass()
        smart_proxies = entities.SmartProxy().search()
        assert len(smart_proxies) > 0
        cls.smart_proxy_attrs = set(smart_proxies[0].update_json([]).keys())

    @tier1
    def test_positive_update_loc(self):
        """@Test: Update a smart proxy. Inspect the server's response.

        @Assert: The response contains some value for the ``location`` field.

        @Feature: SmartProxy
        """
        names = one_to_many_names('location')
        self.assertGreater(
            len(names & self.smart_proxy_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.smart_proxy_attrs),
        )

    @tier1
    def test_positive_update_org(self):
        """@Test: Update a smart proxy. Inspect the server's response.

        @Assert: The response contains some value for the ``organization``
        field.

        @Feature: SmartProxy
        """
        names = one_to_many_names('organization')
        self.assertGreater(
            len(names & self.smart_proxy_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.smart_proxy_attrs),
        )


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

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_by_name_org_name(self):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_by_name_org_id(self):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_by_id_org_name(self):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_by_id_org_id(self):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_by_name_org_name(self):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_by_name_org_id(self):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_by_id_org_name(self):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_by_id_org_id(self):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """
