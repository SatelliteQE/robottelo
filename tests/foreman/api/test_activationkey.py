"""Unit tests for the ``activation_keys`` paths."""
import httplib

from ddt import data, ddt
from fauxfactory import gen_integer, gen_string
from nailgun import client, entities
from requests.exceptions import HTTPError
from robottelo.decorators import skip_if_bug_open
from robottelo.helpers import get_server_credentials
from robottelo.test import APITestCase


@ddt
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

    @data(
        gen_integer(min_value=1, max_value=20),
        gen_integer(min_value=10000, max_value=20000),
    )
    def test_positive_create_2(self, max_content_hosts):
        """@Test: Create an activation key with limited content hosts.

        @Assert: Activation key is created, defaults to limited content host

        @Feature: ActivationKey

        """
        act_key = entities.ActivationKey(
            max_content_hosts=max_content_hosts,
            unlimited_content_hosts=False,
        ).create()
        self.assertEqual(act_key.max_content_hosts, max_content_hosts)
        self.assertFalse(act_key.unlimited_content_hosts)

    @data(
        gen_string(str_type='alpha'),
        gen_string(str_type='alphanumeric'),
        gen_string(str_type='cjk'),
        gen_string(str_type='latin1'),
    )
    def test_positive_create_3(self, name):
        """@Test: Create an activation key providing the initial name.

        @Assert: Activation key is created and contains provided name.

        @Feature: ActivationKey

        """
        self.assertEqual(
            entities.ActivationKey(name=name).create().name,
            name,
        )

    @data(
        gen_string(str_type='alpha'),
        gen_string(str_type='alphanumeric'),
        gen_string(str_type='cjk'),
        gen_string(str_type='latin1'),
    )
    def test_positive_create_4(self, description):
        """@Test: Create an activation key and provide a description.

        @Assert: Created entity contains the provided description.

        @Feature: ActivationKey

        """
        act_key = entities.ActivationKey(description=description).create()
        self.assertEqual(act_key.description, description)

    def test_negative_create_1(self):
        """@Test: Create activation key with limited content hosts but no limit
        set.

        @Assert: Activation key is not created

        @Feature: ActivationKey

        """
        with self.assertRaises(HTTPError):
            entities.ActivationKey(unlimited_content_hosts=False).create()

    @data(
        gen_string(str_type='alpha'),
        gen_integer(max_value=-1),
        0,
    )
    def test_negative_create_2(self, max_content_hosts):
        """@Test: Create activation key with limited content hosts but with
        invalid limit values.

        @Assert: Activation key is not created

        @Feature: ActivationKey

        """
        with self.assertRaises(HTTPError):
            entities.ActivationKey(
                max_content_hosts=max_content_hosts,
                unlimited_content_hosts=False,
            ).create()

    @skip_if_bug_open('bugzilla', 1156555)
    @data(
        gen_integer(min_value=-10, max_value=-1),
        gen_integer(min_value=1, max_value=20),
        gen_string(str_type='alpha'),
    )
    def test_negative_create_3(self, max_content_hosts):
        """@Test Create activation key with unlimited content hosts and set max
        content hosts of varied values.

        @Assert: Activation key is not created

        @Feature: ActivationKey

        """
        with self.assertRaises(HTTPError):
            entities.ActivationKey(
                max_content_hosts=max_content_hosts,
                unlimited_content_hosts=True,
            ).create()

    @data(
        gen_integer(min_value=1, max_value=30),
        gen_integer(min_value=10000, max_value=20000),
    )
    def test_positive_update_1(self, max_content_hosts):
        """@Test: Create activation key then update it to limited content
        hosts.

        @Assert: Activation key is created, updated to limited content host

        @Feature: ActivationKey

        """
        # Create and update an activation key.
        act_key = entities.ActivationKey().create()
        attrs = {
            'description': act_key.get_fields()['description'].gen_value(),
            'max_content_hosts': max_content_hosts,
            'unlimited_content_hosts': False,
        }
        act_key = entities.ActivationKey(id=act_key.id, **attrs).update()
        for field_name, field_value in attrs.items():
            self.assertEqual(getattr(act_key, field_name), field_value)

    @data(
        gen_string(str_type='alpha'),
        gen_integer(min_value=-200, max_value=-1),
        -1,
        0
    )
    def test_negative_update_1(self, max_content_hosts):
        """@Test: Create activation key then update its limit to invalid value.

        @Assert:

        1. Activation key is created
        2. Update fails
        3. Record is not changed

        @Feature: ActivationKey

        """
        act_key = entities.ActivationKey().create()
        self.assertTrue(act_key.unlimited_content_hosts)
        with self.assertRaises(HTTPError):
            entities.ActivationKey(
                id=act_key.id,
                max_content_hosts=max_content_hosts,
                unlimited_content_hosts=False,
            ).update(['max_content_hosts', 'unlimited_content_hosts'])
        act_key_2 = act_key.read()
        for attr in ('max_content_hosts', 'unlimited_content_hosts'):
            self.assertEqual(getattr(act_key, attr), getattr(act_key_2, attr))

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
            auth=get_server_credentials(),
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
            auth=get_server_credentials(),
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
