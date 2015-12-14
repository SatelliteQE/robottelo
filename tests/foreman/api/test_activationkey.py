"""Unit tests for the ``activation_keys`` paths."""
from fauxfactory import gen_integer, gen_string
from nailgun import client, entities
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import rm_bug_is_open, skip_if_bug_open, tier1, tier2
from robottelo.test import APITestCase
from six.moves import http_client


def _good_max_content_hosts():
    """Return a generator yielding valid ``max_content_hosts`` values."""
    return (gen_integer(*limits) for limits in ((1, 20), (10000, 20000)))


def _bad_max_content_hosts():
    """Return a generator yielding invalid ``max_content_hosts`` values."""
    return (gen_integer(-100, -1), 0, gen_string('alpha'))


class ActivationKeyTestCase(APITestCase):
    """Tests for the ``activation_keys`` path."""

    @tier1
    def test_positive_create_unlimited_chosts(self):
        """@Test: Create a plain vanilla activation key.

        @Assert: An activation key is created and its "unlimited_content_hosts"
        attribute defaults to true.

        @Feature: ActivationKey
        """
        self.assertTrue(
            entities.ActivationKey().create().unlimited_content_hosts
        )

    @tier1
    def test_positive_create_limited_chosts(self):
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

    @tier1
    def test_positive_create_with_name(self):
        """@Test: Create an activation key providing the initial name.

        @Assert: Activation key is created and contains provided name.

        @Feature: ActivationKey
        """
        for name in valid_data_list():
            with self.subTest(name):
                act_key = entities.ActivationKey(name=name).create()
                self.assertEqual(name, act_key.name)

    @tier1
    def test_positive_create_with_description(self):
        """@Test: Create an activation key and provide a description.

        @Assert: Created entity contains the provided description.

        @Feature: ActivationKey
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                act_key = entities.ActivationKey(description=desc).create()
                self.assertEqual(desc, act_key.description)

    @tier1
    def test_negative_create_no_chost_limit(self):
        """@Test: Create activation key with limited content hosts but no limit
        set.

        @Assert: Activation key is not created

        @Feature: ActivationKey
        """
        with self.assertRaises(HTTPError):
            entities.ActivationKey(unlimited_content_hosts=False).create()

    @tier1
    def test_negative_create_invalid_chost_limit(self):
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

    @tier1
    @skip_if_bug_open('bugzilla', 1156555)
    def test_negative_create_no_chost_limit_with_set_max(self):
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

    @tier1
    def test_negative_create_with_name(self):
        """@Test: Create activation key providing an invalid name.

        @Assert: Activation key is not created

        @Feature: ActivationKey
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.ActivationKey(name=name).create()

    @tier1
    def test_positive_update_limited_chost(self):
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

    @tier1
    def test_positive_update_name(self):
        """@Test: Create activation key providing the initial name, then update
        its name to another valid name.

        @Assert: Activation key is created, and its name can be updated.

        @Feature: ActivationKey
        """
        act_key = entities.ActivationKey().create()

        for new_name in valid_data_list():
            with self.subTest(new_name):
                updated = entities.ActivationKey(
                    id=act_key.id, name=new_name).update(['name'])
                self.assertEqual(new_name, updated.name)

    @tier1
    def test_negative_update_limit(self):
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

    @tier1
    def test_negative_update_name(self):
        """@Test: Create activation key then update its name to an invalid name.

        @Assert: Activation key is created, and its name is not updated.

        @Feature: ActivationKey
        """
        act_key = entities.ActivationKey().create()
        for new_name in invalid_names_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.ActivationKey(
                        id=act_key.id, name=new_name).update(['name'])
                new_key = entities.ActivationKey(id=act_key.id).read()
                self.assertNotEqual(new_key.name, new_name)
                self.assertEqual(new_key.name, act_key.name)

    @tier1
    def test_negative_update_max_chosts(self):
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

    @tier2
    def test_positive_get_releases_status_code(self):
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
        status_code = http_client.OK
        self.assertEqual(status_code, response.status_code)
        self.assertIn('application/json', response.headers['content-type'])

    @tier2
    def test_positive_get_releases_content(self):
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

    @tier2
    def test_positive_add_host_collections(self):
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

    @tier1
    def test_positive_update_auto_attach(self):
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

    @tier1
    def test_positive_delete(self):
        """@Test: Create activation key and then delete it.

        @Assert: Activation key is successfully deleted.

        @Feature: ActivationKey
        """
        for name in valid_data_list():
            with self.subTest(name):
                act_key = entities.ActivationKey().create()
                act_key.delete()
                with self.assertRaises(HTTPError):
                    entities.ActivationKey(id=act_key.id).read()


class ActivationKeySearchTestCase(APITestCase):
    """Tests that search for activation keys."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and an activation key belonging to it."""
        super(ActivationKeySearchTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.act_key = entities.ActivationKey(organization=cls.org).create()
        if rm_bug_is_open(4638):
            cls.act_key.read()  # Wait for elasticsearch to index new act key.

    @tier1
    def test_positive_search_by_org(self):
        """@Test: Search for all activation keys in an organization.

        @Assert: Only activation keys in the organization are returned.

        @Feature: ActivationKey
        """
        act_keys = entities.ActivationKey(organization=self.org).search()
        self.assertEqual(len(act_keys), 1)
        self.assertEqual(act_keys[0].id, self.act_key.id)
