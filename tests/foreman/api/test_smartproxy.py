"""Tests for the ``smart_proxies`` paths.

@Requirement: Smartproxy

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: API

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from nailgun import entities
from robottelo.decorators import (
    skip_if_bug_open,
    tier1,
)
from robottelo.test import APITestCase
from robottelo.api.utils import one_to_many_names


class SmartProxyMissingAttrTestCase(APITestCase):
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. The ``one_to_*_names`` functions know what names
    Satellite may assign to fields.
    """

    @classmethod
    @skip_if_bug_open('bugzilla', 1262037)
    def setUpClass(cls):
        """Find a ``SmartProxy``.

        Every Satellite has a built-in smart proxy, so searching for an
        existing smart proxy should always succeed.
        """
        super(SmartProxyMissingAttrTestCase, cls).setUpClass()
        smart_proxy = entities.SmartProxy(id=1).read()
        cls.smart_proxy_attrs = set(smart_proxy.update_json([]).keys())

    @tier1
    def test_positive_update_loc(self):
        """Update a smart proxy. Inspect the server's response.

        @id: 42d6b749-c047-4fd2-90ee-ffab7be558f9

        @Assert: The response contains some value for the ``location`` field.
        """
        names = one_to_many_names('location')
        self.assertGreater(
            len(names & self.smart_proxy_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.smart_proxy_attrs),
        )

    @tier1
    def test_positive_update_org(self):
        """Update a smart proxy. Inspect the server's response.

        @id: fbde9f87-33db-4b95-a5f7-71a618460c84

        @Assert: The response contains some value for the ``organization``
        field.
        """
        names = one_to_many_names('organization')
        self.assertGreater(
            len(names & self.smart_proxy_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.smart_proxy_attrs),
        )
