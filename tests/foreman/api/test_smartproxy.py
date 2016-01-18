"""Tests for the ``smart_proxies`` paths."""
from nailgun import entities
from robottelo.decorators import (
    skip_if_bug_open,
    tier1,
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
        """Update a smart proxy. Inspect the server's response.

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
        """Update a smart proxy. Inspect the server's response.

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
