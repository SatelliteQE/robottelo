"""Unit tests for the ``activation_keys`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/activation_keys.html

"""
from ddt import data, ddt
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo.factory import FactoryError
from robottelo import entities
from robottelo.orm import IntegerField, StringField
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


@ddt
class ActivationKeysTestCase(TestCase):
    """Tests for the ``activation_keys`` path."""

    def test_positive_create_1(self):
        """@Test: Create a plain vanilla activation key.

        @Assert: Activation key is created, defaults to unlimited content host

        @Feature: ActivationKey

        """
        try:
            attrs = entities.ActivationKey().create()
        except FactoryError as err:
            self.fail(err)
        # Assert that it defaults to unlimited content host
        self.assertTrue(
            attrs['unlimited_content_hosts'],
            u"Unlimited content hosts is {0}".format(
                attrs['unlimited_content_hosts'])
        )

    @data(
        IntegerField(min_val=1, max_val=20).get_value(),
        IntegerField(min_val=10000, max_val=20000).get_value(),
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
        except FactoryError as err:
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
        StringField(str_type=('alpha',)).get_value(),
        StringField(str_type=('alphanumeric',)).get_value(),
        StringField(str_type=('cjk',)).get_value(),
        StringField(str_type=('latin1',)).get_value(),
    )
    @skip_if_bug_open('bugzilla', 1127335)
    def test_positive_create_3(self, name):
        """@Test: Create an activation key providing the initial name.

        @Assert: Activation key is created and contains provided name.

        @Feature: ActivationKey

        """
        try:
            attrs = entities.ActivationKey(name=name).create()
        except FactoryError as err:
            self.fail(err)

        # Fetch the activation key. Assert that initial values match.
        real_attrs = entities.ActivationKey(id=attrs['id']).read_json()
        self.assertEqual(
            real_attrs['name'],
            name,
            u"Initial attribute values mismatch: {0} != {1}".format(
                real_attrs['name'], name)
        )

    def test_negative_create_1(self):
        """@Test: Create activation key with limited content hosts but no limit
        set.

        @Assert: Activation key is not created

        @Feature: ActivationKey

        """
        with self.assertRaises(FactoryError):
            entities.ActivationKey(unlimited_content_hosts=False).create()

    @data(
        StringField(str_type=('alpha',)).get_value(),
        IntegerField(max_val=-1).get_value(),
        0,
    )
    def test_negative_create_2(self, max_content_hosts):
        """@Test: Create activation key with limited content hosts but with
        invalid limit values.

        @Assert: Activation key is not created

        @Feature: ActivationKey

        """
        with self.assertRaises(FactoryError):
            entities.ActivationKey(
                unlimited_content_hosts=False,
                max_content_hosts=max_content_hosts
            ).create()

    @data(
        IntegerField(min_val=-10, max_val=-1).get_value(),
        IntegerField(min_val=1, max_val=20).get_value(),
        StringField(str_type=('alpha',)).get_value(),
    )
    def test_negative_create_3(self, max_content_hosts):
        """@Test Create activation key with unlimited content hosts and set max
        content hosts of varied values.

        @Assert: Activation key is not created

        @Feature: ActivationKey

        """
        with self.assertRaises(FactoryError):
            entities.ActivationKey(
                unlimited_content_hosts=True,
                max_content_hosts=max_content_hosts
            ).create()

    @data(
        IntegerField(min_val=1, max_val=30).get_value(),
        IntegerField(min_val=10000, max_val=20000).get_value(),
    )
    def test_positive_update_1(self, max_content_hosts):
        """@Test: Create activation key then update it to limited content
        hosts.

        @Assert: Activation key is created, updated to limited content host

        @Feature: ActivationKey

        """
        try:
            attrs = entities.ActivationKey().create()
        except FactoryError as err:
            self.fail(err)
        path = entities.ActivationKey(id=attrs['id']).path()

        # Make a copy of the activation key...
        ak_copy = attrs.copy()
        # ...and update a few fields
        ak_copy['unlimited_content_hosts'] = False
        ak_copy['max_content_hosts'] = max_content_hosts

        # Update the activation key
        response = client.put(
            path,
            ak_copy,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(
            response.status_code,
            httplib.OK,
            status_code_error(path, httplib.OK, response),
        )

        # Fetch the activation key. Assert that values have changed.
        real_attrs = entities.ActivationKey(id=attrs['id']).read_json()
        self.assertNotEqual(
            real_attrs['unlimited_content_hosts'],
            attrs['unlimited_content_hosts'],
            u"Unlimited content hosts values: {0} == {1}".format(
                real_attrs['unlimited_content_hosts'],
                attrs['unlimited_content_hosts'])
        )
        self.assertFalse(
            real_attrs['unlimited_content_hosts'],
            u"Unlimited content hosts is {0}".format(
                real_attrs['unlimited_content_hosts']
            )
        )

        self.assertNotEqual(
            real_attrs['max_content_hosts'],
            attrs['max_content_hosts'],
            u"Max content hosts values: {0} == {1}".format(
                real_attrs['max_content_hosts'],
                attrs['max_content_hosts'])
        )
        self.assertEqual(
            real_attrs['max_content_hosts'],
            max_content_hosts,
            u"Max content hosts values don't match: {0} != {1}".format(
                real_attrs['max_content_hosts'],
                attrs['max_content_hosts']
            )
        )

    @data(
        StringField(len=(1, 30), str_type=('alpha',)).get_value(),
        IntegerField(min_val=-200, max_val=-1).get_value(),
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
        except FactoryError as err:
            self.fail(err)
        path = entities.ActivationKey(id=attrs['id']).path()

        # Make a copy of the activation key and update a few fields.
        ak_copy = attrs.copy()
        ak_copy['unlimited_content_hosts'] = False
        ak_copy['max_content_hosts'] = max_content_hosts

        # Update the activation key with semantically incorrect values.
        response = client.put(
            path,
            ak_copy,
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(
            response.status_code,
            httplib.UNPROCESSABLE_ENTITY,
            status_code_error(path, httplib.UNPROCESSABLE_ENTITY, response),
        )

        # Fetch the activation key. Assert that values have not changed.
        real_attrs = entities.ActivationKey(id=attrs['id']).read_json()
        self.assertEqual(
            real_attrs['unlimited_content_hosts'],
            attrs['unlimited_content_hosts'],
            u"Unlimited content hosts values: {0} == {1}".format(
                real_attrs['unlimited_content_hosts'],
                attrs['unlimited_content_hosts'])
        )
        self.assertTrue(
            real_attrs['unlimited_content_hosts'],
            u"Unlimited content hosts is {0}".format(
                real_attrs['unlimited_content_hosts']
            )
        )
        self.assertEqual(
            real_attrs['max_content_hosts'],
            attrs['max_content_hosts'],
            u"Max content hosts values: {0} == {1}".format(
                real_attrs['max_content_hosts'],
                attrs['max_content_hosts'])
        )

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
        except FactoryError as err:
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
        except FactoryError as err:
            self.fail(err)
        response = client.get(
            entities.ActivationKey(id=attrs['id']).path(which='releases'),
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertIn('results', response.keys())
        self.assertEqual(type(response['results']), list)
