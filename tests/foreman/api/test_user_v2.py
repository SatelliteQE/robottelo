"""Unit tests for the ``users`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/users.html

"""
from ddt import data, ddt
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.helpers import get_server_credentials
from robottelo.orm import StringField
from robottelo import entities
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


@ddt
class UsersTestCase(TestCase):
    """Tests for the ``users`` path."""
    @data(
        StringField(max_len=60, str_type=('alpha',)).get_value(),
        StringField(max_len=60, str_type=('alphanumeric',)).get_value(),
        StringField(max_len=60, str_type=('cjk',)).get_value(),
        StringField(max_len=60, str_type=('latin1',)).get_value(),
    )
    def test_positive_create_1(self, login):
        """
        @Test Create a user providing the initial login name.
        @Assert: User is created and contains provided login name.
        @Feature: User
        """
        path = entities.User().path()
        attrs = entities.User(login=login).build()
        response = client.post(
            path,
            attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = (httplib.OK, httplib.CREATED)
        self.assertIn(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response),
        )

        # Fetch the user
        real_attrs = client.get(
            entities.User(id=response.json()['id']).path(),
            auth=get_server_credentials(),
            verify=False,
        ).json()
        # Remove the ``password`` field from ``attrs`` since it isn't
        # returned by GET.
        attrs.pop('password')
        # Assert that keys and values match
        for key, value in attrs.items():
            self.assertIn(key, real_attrs.keys())
            self.assertEqual(value, real_attrs[key])
