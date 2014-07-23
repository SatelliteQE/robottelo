"""Unit tests for the ``users`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/users

"""
from ddt import data, ddt
from fauxfactory import FauxFactory
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
import httplib
# (too many public methods) pylint: disable=R0904


@ddt
class UsersTestCase(TestCase):
    """Tests for the ``users`` path."""
    @data(
        FauxFactory.generate_alpha(FauxFactory.generate_integer(1, 60)),
        FauxFactory.generate_alphanumeric(FauxFactory.generate_integer(1, 60)),
        FauxFactory.generate_cjk(FauxFactory.generate_integer(1, 60)),
        FauxFactory.generate_latin1(FauxFactory.generate_integer(1, 60)),
    )
    def test_positive_create_1(self, login):
        """
        @Test Create a user providing the initial login name.
        @Assert: User is created and contains provided login name.
        @Feature: User
        """
        path = entities.User().path()
        attrs = entities.User().build(
            fields={
                u'login': login,
            }
        )
        response = client.post(
            path,
            attrs,
            auth=get_server_credentials(),
            headers={'content-type': 'application/json'},
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
        self.assertEqual(
            real_attrs['login'],
            login,
            u'Logins do not match: \'{0}\' != \'{1}\'.'.format(
                real_attrs['login'],
                login,
            )
        )
