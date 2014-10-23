"""Unit tests for the ``activation_keys`` paths."""
from ddt import data, ddt
from fauxfactory import gen_integer, gen_string
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
import httplib
# (too-many-public-methods) pylint:disable=R0904


@ddt
class ActivationKeysTestCase(TestCase):
    """Tests for the ``activation_keys`` path."""

    def test_positive_create_1(self):
        """@Test: Create a plain vanilla activation key.

        @Assert: An activation key is created and its "unlimited_content_hosts"
        attribute defaults to true.

        @Feature: ActivationKey

        """
        try:
            attrs = entities.ActivationKey().create()
        except HTTPError as err:
            self.fail(err)
        self.assertTrue(attrs['unlimited_content_hosts'])

    @data(
        gen_integer(min_value=1, max_value=20),
        gen_integer(min_value=10000, max_value=20000),
    )
    def test_positive_create_2(self, max_content_hosts):
        """@Test: Create an activation key with limited content hosts.

        @Assert: Activation key is created, defaults to limited content host

        @Feature: ActivationKey

        """
        try:
            attrs = entities.ActivationKey(
                unlimited_content_hosts=False,
                max_content_hosts=max_content_hosts,
            ).create()
        except HTTPError as err:
            self.fail(err)
        # Assert that it defaults to limited content host...
        self.assertFalse(
            attrs['unlimited_content_hosts'],
            u"Unlimited content hosts is {0}".format(
                attrs['unlimited_content_hosts'])
        )
        # ...and matches value passed
        self.assertEqual(
            attrs['max_content_hosts'],
            max_content_hosts,
            u"Max content hosts values don't match: {0} != {1}".format(
                attrs['max_content_hosts'], max_content_hosts)
        )

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
        try:
            attrs = entities.ActivationKey(name=name).create()
        except HTTPError as err:
            self.fail(err)

        # Fetch the activation key. Assert that initial values match.
        real_attrs = entities.ActivationKey(id=attrs['id']).read_json()
        self.assertEqual(
            real_attrs['name'],
            name,
            u"Initial attribute values mismatch: {0} != {1}".format(
                real_attrs['name'], name)
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
        try:
            entity_id = entities.ActivationKey(
                description=description
            ).create()['id']
        except HTTPError as err:
            self.fail(err)

        # Fetch the activation key. Assert that initial values match.
        attrs = entities.ActivationKey(id=entity_id).read_json()
        self.assertEqual(attrs['description'], description)

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
                unlimited_content_hosts=False,
                max_content_hosts=max_content_hosts
            ).create()

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
                unlimited_content_hosts=True,
                max_content_hosts=max_content_hosts
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
        # Create an activation key.
        try:
            activation_key = entities.ActivationKey(
                id=entities.ActivationKey().create()['id']
            )
        except HTTPError as err:
            self.fail(err)

        # Update the activation key.
        description = entities.ActivationKey.description.get_value()
        response = client.put(
            activation_key.path(),
            {
                'description': description,
                'max_content_hosts': max_content_hosts,
                'unlimited_content_hosts': False,
            },
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()

        # Fetch the activation key. Assert that values have been updated.
        real_attrs = activation_key.read_json()
        self.assertEqual(real_attrs['description'], description)
        self.assertEqual(real_attrs['max_content_hosts'], max_content_hosts)
        self.assertFalse(real_attrs['unlimited_content_hosts'])

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
        try:
            attrs = entities.ActivationKey().create()
        except HTTPError as err:
            self.fail(err)
        activationkey = entities.ActivationKey(id=attrs['id'])

        # Update the activation key with semantically incorrect values.
        response = client.put(
            activationkey.path(),
            {
                u'unlimited_content_hosts': False,
                u'max_content_hosts': max_content_hosts
            },
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(
            response.status_code,
            httplib.UNPROCESSABLE_ENTITY,
            status_code_error(
                activationkey.path(),
                httplib.UNPROCESSABLE_ENTITY,
                response
            ),
        )

        # Make sure no attributes have changed.
        new_attrs = activationkey.read_json()
        for attr in ('unlimited_content_hosts', 'max_content_hosts'):
            self.assertEqual(attrs[attr], new_attrs[attr])
        self.assertTrue(new_attrs['unlimited_content_hosts'])

    def test_update_max_content_hosts(self):
        """@Test: Create an activation key with ``max_content_hosts == 1``,
        then update that field with a string value.

        @Feature: ActivationKey

        @Assert: The update fails with an HTTP 422 return code.

        """
        attrs = entities.ActivationKey(max_content_hosts=1).create()
        path = entities.ActivationKey(id=attrs['id']).path()
        new_attrs = attrs.copy()
        new_attrs['max_content_hosts'] = 'foo'
        response = client.put(
            path,
            new_attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(
            response.status_code,
            httplib.UNPROCESSABLE_ENTITY,
            status_code_error(path, httplib.UNPROCESSABLE_ENTITY, response),
        )

        # Status code is OK. Was `max_content_hosts` changed, or is it still 1?
        response = entities.ActivationKey(id=attrs['id']).read_json()
        self.assertEqual(response['max_content_hosts'], 1)

    def test_get_releases_status_code(self):
        """@Test: Get an activation key's releases. Check response format.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        @Feature: ActivationKey

        """
        try:
            attrs = entities.ActivationKey().create()
        except HTTPError as err:
            self.fail(err)
        path = entities.ActivationKey(id=attrs['id']).path(which='releases')
        response = client.get(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    def test_get_releases_content(self):
        """@Test: Get an activation key's releases. Check response contents.

        @Assert: A list of results is returned.

        @Feature: ActivationKey

        """
        try:
            attrs = entities.ActivationKey().create()
        except HTTPError as err:
            self.fail(err)
        response = client.get(
            entities.ActivationKey(id=attrs['id']).path(which='releases'),
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
        # Let's create an organization and re-use it in several places. Doing
        # so will speed up this test.
        org = entities.Organization().create()

        # By default, an activation key should have no host collections.
        act_key = entities.ActivationKey(organization=org['id']).create()
        self.assertEqual(act_key['host_collections'], [])

        # Associate our activation key with one host collection.
        host_coll_1 = entities.HostCollection(organization=org['id']).create()
        client.put(
            entities.ActivationKey(id=act_key['id']).path(),
            verify=False,
            auth=get_server_credentials(),
            data={u'host_collection_ids': [host_coll_1['id']]},
        )

        # Verify that the association succeeded.
        act_key = entities.ActivationKey(id=act_key['id']).read_json()
        self.assertEqual(len(act_key['host_collections']), 1)
        self.assertEqual(
            act_key['host_collections'][0]['id'],
            host_coll_1['id'],
        )

        # Associate our activation key with two host collections.
        host_coll_2 = entities.HostCollection(organization=org['id']).create()
        client.put(
            entities.ActivationKey(id=act_key['id']).path(),
            verify=False,
            auth=get_server_credentials(),
            data={
                u'host_collection_ids': [host_coll_1['id'], host_coll_2['id']]
            },
        )

        # Verify that the association succeeded.
        act_key = entities.ActivationKey(id=act_key['id']).read_json()
        self.assertEqual(len(act_key['host_collections']), 2)
        for host_coll in act_key['host_collections']:
            self.assertIn(
                host_coll['id'],
                (host_coll_1['id'], host_coll_2['id'])
            )

        # Finally, associate our activation key with zero host collections.
        client.put(
            entities.ActivationKey(id=act_key['id']).path(),
            verify=False,
            auth=get_server_credentials(),
            data={u'host_collection_ids': []},
        )

        # Verify that the association succeeded.
        act_key = entities.ActivationKey(id=act_key['id']).read_json()
        self.assertEqual(act_key['host_collections'], [])
