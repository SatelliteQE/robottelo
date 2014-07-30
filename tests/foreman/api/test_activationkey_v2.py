"""Unit tests for the ``activationkeys`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/activation_keys.html

"""
from ddt import data, ddt
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.helpers import get_server_credentials
from robottelo.factory import FactoryError
from robottelo.orm import IntegerField, StringField
from robottelo import entities
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


@ddt
class ActivationKeysTestCase(TestCase):
    """Tests for the ``activationekys`` path."""

    def test_positive_create_1(self):
        """
        @Test Create a plain vanilla activationkey
        @Assert: Activationkey is created, defaults to unlimited content host
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
        """
        @Test Create an activationkey with limited content hosts
        @Assert: Activationkey is created, defaults to limited content host
        @Feature: ActivationKey
        """
        try:
            attrs = entities.ActivationKey().create(fields={
                u'unlimited_content_hosts': False,
                u'max_content_hosts': max_content_hosts
            })
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
    def test_positive_create_3(self, name):
        """
        @Test Create an activationkey providing the initial name.
        @Assert: Activationkey is created and contains provided name.
        @Feature: ActivationKey
        """
        try:
            attrs = entities.ActivationKey().create(fields={u'name': name})
        except FactoryError as err:
            self.fail(err)

        # Fetch the activationeky
        real_attrs = client.get(
            entities.ActivationKey(id=attrs['id']).path(),
            auth=get_server_credentials(),
            verify=False,
        ).json()
        # Assert that initial values match
        self.assertEqual(
            real_attrs['name'],
            name,
            u"Initial attribute values mismatch: {0} != {1}".format(
                real_attrs['name'], name)
        )

    def test_negative_create_1(self):
        """
        @Test Create activationkey with limited content hosts but no limit set
        @Assert: Activationkey is not created
        @Feature: ActivationKey
        """
        with self.assertRaises(FactoryError):
            entities.ActivationKey().create(
                fields={u'unlimited_content_hosts': False}
            )

    @data(
        StringField(str_type=('alpha',)).get_value(),
        IntegerField(max_val=-1).get_value(),
        0,
    )
    def test_negative_create_2(self, max_content_hosts):
        """
        @Test Create activationkey with limited content hosts but
          with invalid limit values
        @Assert: Activationkey is not created
        @Feature: ActivationKey
        """
        with self.assertRaises(FactoryError):
            entities.ActivationKey().create(
                fields={
                    u'unlimited_content_hosts': False,
                    u'max_content_hosts': max_content_hosts
                }
            )

    @data(
        IntegerField(min_val=-10, max_val=-1).get_value(),
        IntegerField(min_val=1, max_val=20).get_value(),
        StringField(str_type=('alpha',)).get_value(),
    )
    def test_negative_create_3(self, max_content_hosts):
        """
        @Test Create activationkey with unlimited content hosts and set
          max content hosts of varied values
        @Assert:
          1. Activationkey is not created
        @Feature: ActivationKey
        """
        with self.assertRaises(FactoryError):
            entities.ActivationKey().create(fields={
                u'unlimited_content_hosts': True,
                u'max_content_hosts': max_content_hosts
            })

    @data(
        IntegerField(min_val=1, max_val=30).get_value(),
        IntegerField(min_val=10000, max_val=20000).get_value(),
    )
    def test_positive_update_1(self, max_content_hosts):
        """
        @Test Create activationkey then update it to limited content hosts
        @Assert: ActivationKey is created, updated to limited content host
        @Feature: ActivationKey
        """
        try:
            attrs = entities.ActivationKey().create()
        except FactoryError as err:
            self.fail(err)
        path = entities.ActivationKey(id=attrs['id']).path()

        # Make a copy of the activationkey...
        ak_copy = attrs.copy()
        # ...and update a few fields
        ak_copy['unlimited_content_hosts'] = False
        ak_copy['max_content_hosts'] = max_content_hosts

        # Update the activationkey
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

        # Fetch the activationkey
        real_attrs = client.get(
            entities.ActivationKey(id=attrs['id']).path(),
            auth=get_server_credentials(),
            verify=False,
        ).json()
        # Assert that values have changed
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
        StringField(max_len=30, str_type=('alpha',)).get_value(),
        IntegerField(min_val=-200, max_val=-1).get_value(),
        -1,
        0
    )
    def test_negative_update_1(self, max_content_hosts):
        """
        @Test Create activationkey then update its limit to invalid value
        @Assert:
          1. ActivationKey is created
          2. Update fails
          3. Record is not changed
        @Feature: ActivationKey
        """
        try:
            attrs = entities.ActivationKey().create()
        except FactoryError as err:
            self.fail(err)
        path = entities.ActivationKey(id=attrs['id']).path()

        # Make a copy of the activationkey...
        ak_copy = attrs.copy()
        # ...and update a few fields
        ak_copy['unlimited_content_hosts'] = False
        ak_copy['max_content_hosts'] = max_content_hosts

        # Update the activationkey
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

        # Fetch the activationkey
        real_attrs = client.get(
            entities.ActivationKey(id=attrs['id']).path(),
            auth=get_server_credentials(),
            verify=False,
        ).json()
        # Assert that values have not changed
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
