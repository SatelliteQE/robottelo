"""Unit tests for the ``activation_keys`` paths."""
import httplib

from fauxfactory import gen_integer, gen_string
from nailgun import client, entities
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.decorators import rm_bug_is_open, skip_if_bug_open
from robottelo.helpers import valid_data_list
from robottelo.test import APITestCase


def _good_max_content_hosts():
    """Return a generator yielding valid ``max_content_hosts`` values."""
    return (gen_integer(*limits) for limits in ((1, 20), (10000, 20000)))


def _bad_max_content_hosts():
    """Return a generator yielding invalid ``max_content_hosts`` values."""
    return (gen_integer(-100, -1), 0, gen_string('alpha'))


class ActivationKeysTestCase(APITestCase):
    """Tests for the ``activation_keys`` path."""

    def test_positive_create_1(self):
        """@Test: Create a plain vanilla activation key.

        @Assert: An activation key is created and its "unlimited_content_hosts"
        attribute defaults to true.

        @Feature: ActivationKey

        """
        self.assertTrue(
            entities.ActivationKey().create().unlimited_content_hosts
        )

    def test_positive_create_2(self):
        """@Test: Create an activation key with limited content hosts.

        @Assert: Activation key is created, defaults to limited content host

        @Feature: ActivationKey

        """
        for mch in _good_max_content_hosts():
            with self.subTest(mch):
                act_key = entities.ActivationKey(
                    max_content_hosts=mch,
                    unlimited_content_hosts=False,
                ).create()
                self.assertEqual(act_key.max_content_hosts, mch)
                self.assertFalse(act_key.unlimited_content_hosts)

    def test_positive_create_3(self):
        """@Test: Create an activation key providing the initial name.

        @Assert: Activation key is created and contains provided name.

        @Feature: ActivationKey

        """
        for name in valid_data_list():
            with self.subTest(name):
                act_key = entities.ActivationKey(name=name).create()
                self.assertEqual(name, act_key.name)

    def test_positive_create_4(self):
        """@Test: Create an activation key and provide a description.

        @Assert: Created entity contains the provided description.

        @Feature: ActivationKey

        """
        for desc in valid_data_list():
            with self.subTest(desc):
                act_key = entities.ActivationKey(description=desc).create()
                self.assertEqual(desc, act_key.description)

    def test_negative_create_1(self):
        """@Test: Create activation key with limited content hosts but no limit
        set.

        @Assert: Activation key is not created

        @Feature: ActivationKey

        """
        with self.assertRaises(HTTPError):
            entities.ActivationKey(unlimited_content_hosts=False).create()

    def test_negative_create_2(self):
        """@Test: Create activation key with limited content hosts but with
        invalid limit values.

        @Assert: Activation key is not created

        @Feature: ActivationKey

        """
        for mch in _bad_max_content_hosts():
            with self.subTest(mch):
                with self.assertRaises(HTTPError):
                    entities.ActivationKey(
                        max_content_hosts=mch,
                        unlimited_content_hosts=False,
                    ).create()

    @skip_if_bug_open('bugzilla', 1156555)
    def test_negative_create_3(self):
        """@Test Create activation key with unlimited content hosts and set max
        content hosts of varied values.

        @Assert: Activation key is not created

        @Feature: ActivationKey

        """
        for mch in _good_max_content_hosts() + _bad_max_content_hosts():
            with self.subTest(mch):
                with self.assertRaises(HTTPError):
                    entities.ActivationKey(
                        max_content_hosts=mch,
                        unlimited_content_hosts=True,
                    ).create()

    def test_positive_update_1(self):
        """@Test: Create activation key then update it to limited content
        hosts.

        @Assert: Activation key is created, updated to limited content host

        @Feature: ActivationKey

        """
        # unlimited_content_hosts defaults to True.
        act_key = entities.ActivationKey().create()
        for mch in _good_max_content_hosts():
            want = {'max_content_hosts': mch, 'unlimited_content_hosts': False}
            for key, value in want.items():
                setattr(act_key, key, value)
            with self.subTest(want):
                act_key = act_key.update(want.keys())
                actual = {attr: getattr(act_key, attr) for attr in want.keys()}
                self.assertEqual(want, actual)

    def test_negative_update_1(self):
        """@Test: Create activation key then update its limit to invalid value.

        @Assert:

        1. Activation key is created
        2. Update fails
        3. Record is not changed

        @Feature: ActivationKey

        """
        act_key = entities.ActivationKey().create()
        want = {
            'max_content_hosts': act_key.max_content_hosts,
            'unlimited_content_hosts': act_key.unlimited_content_hosts,
        }
        for mch in _bad_max_content_hosts():
            with self.subTest(mch):
                act_key.max_content_hosts = mch
                act_key.unlimited_content_hosts = False
                with self.assertRaises(HTTPError):
                    act_key.update(want.keys())
                act_key = act_key.read()
                actual = {attr: getattr(act_key, attr) for attr in want.keys()}
                self.assertEqual(want, actual)

    def test_update_max_content_hosts(self):
        """@Test: Create an activation key with ``max_content_hosts == 1``,
        then update that field with a string value.

        @Feature: ActivationKey

        @Assert: The update fails with an HTTP 422 return code.

        """
        act_key = entities.ActivationKey(max_content_hosts=1).create()
        with self.assertRaises(HTTPError):
            entities.ActivationKey(
                id=act_key.id,
                max_content_hosts='foo',
            ).update(['max_content_hosts'])
        self.assertEqual(act_key.read().max_content_hosts, 1)

    def test_get_releases_status_code(self):
        """@Test: Get an activation key's releases. Check response format.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        @Feature: ActivationKey

        """
        act_key = entities.ActivationKey().create()
        path = act_key.path('releases')
        response = client.get(
            path,
            auth=settings.server.get_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(status_code, response.status_code)
        self.assertIn('application/json', response.headers['content-type'])

    def test_get_releases_content(self):
        """@Test: Get an activation key's releases. Check response contents.

        @Assert: A list of results is returned.

        @Feature: ActivationKey

        """
        act_key = entities.ActivationKey().create()
        response = client.get(
            act_key.path('releases'),
            auth=settings.server.get_credentials(),
            verify=False,
        ).json()
        self.assertIn('results', response.keys())
        self.assertEqual(type(response['results']), list)

    def test_set_host_collection(self):
        """@Test: Associate an activation key with several host collections.

        @Assert:

        1. By default, an activation key is associated with no host
           collections.
        2. After associating an activation key with some set of host
           collections and reading that activation key, the correct host
           collections are listed.

        @Feature: ActivationKey

        """
        org = entities.Organization().create()  # re-use this to speed up test

        # An activation key has no host collections by default.
        act_key = entities.ActivationKey(organization=org).create()
        self.assertEqual(len(act_key.host_collection), 0)

        # Give activation key one host collection.
        act_key.host_collection.append(
            entities.HostCollection(organization=org).create()
        )
        act_key = act_key.update(['host_collection'])
        self.assertEqual(len(act_key.host_collection), 1)

        # Give activation key second host collection.
        act_key.host_collection.append(
            entities.HostCollection(organization=org).create()
        )
        act_key = act_key.update(['host_collection'])
        self.assertEqual(len(act_key.host_collection), 2)

        # Give activation key zero host collections.
        act_key.host_collection = []
        act_key = act_key.update(['host_collection'])
        self.assertEqual(len(act_key.host_collection), 0)

    def test_update_auto_attach(self):
        """@Test: Create an activation key, then update the auto_attach
        field with the inverse boolean value.

        @Feature: ActivationKey

        @Assert: The value is changed.

        """
        act_key = entities.ActivationKey().create()
        act_key_2 = entities.ActivationKey(
            id=act_key.id,
            auto_attach=(not act_key.auto_attach),
        ).update(['auto_attach'])
        self.assertNotEqual(act_key.auto_attach, act_key_2.auto_attach)


class SearchTestCase(APITestCase):
    """Tests that search for activation keys."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and an activation key belonging to it."""
        super(SearchTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.act_key = entities.ActivationKey(organization=cls.org).create()
        if rm_bug_is_open(4638):
            cls.act_key.read()  # Wait for elasticsearch to index new act key.

    def test_search_by_org(self):
        """@Test: Search for all activation keys in an organization.

        @Assert: Only activation keys in the organization are returned.

        @Feature: ActivationKey

        """
        act_keys = entities.ActivationKey(organization=self.org).search()
        self.assertEqual(len(act_keys), 1)
        self.assertEqual(act_keys[0].id, self.act_key.id)
