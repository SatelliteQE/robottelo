"""Unit tests for the ``roles`` paths.

Each ``TestCase`` subclass tests a single URL. A full list of URLs to be tested
can be found here: http://theforeman.org/api/apidoc/v2/roles.html

"""
from robottelo.api import client
from robottelo.common.decorators import skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo import entities, factory, orm
from unittest import TestCase
import ddt
# (too many public methods) pylint: disable=R0904


@ddt.ddt
class RoleTestCase(TestCase):
    """Tests for ``api/v2/roles``."""
    def _test_role_name(self, name):
        """Create a role with name ``name``."""
        try:
            role_attrs = entities.Role(name=name).create()
        except factory.FactoryError as err:
            self.fail(err)  # fail instead of error

        # Creation apparently succeeded. GET the role and verify it's name.
        response = client.get(
            entities.Role(id=role_attrs['id']).path(),
            auth=get_server_credentials(),
            verify=False,
        ).json()
        self.assertEqual(response['name'], name)

    @ddt.data(
        orm.StringField(str_type=('alphanumeric',)).get_value(),
        orm.StringField(str_type=('alpha',)).get_value(),
        orm.StringField(str_type=('numeric',)).get_value(),
    )
    def test_positive_create_1(self, name):
        """@Test: Create a role with a name containing alphanumeric chars.

        @Feature: Role

        @Assert: An entity can be created without receiving any errors, the
        entity can be fetched, and the fetched entity has the specified name.

        """
        self._test_role_name(name)

    @skip_if_bug_open('bugzilla', 1129785)
    @ddt.data(
        orm.StringField(str_type=('cjk',)).get_value(),
        orm.StringField(str_type=('latin1',)).get_value(),
        orm.StringField(str_type=('utf8',)).get_value(),
    )
    def test_positive_create_2(self, name):
        """@Test: Create a role with a name containing non-alphanumeric chars.

        @Feature: Role

        @Assert: An entity can be created without receiving any errors, the
        entity can be fetched, and the fetched entity has the specified name.

        """
        self._test_role_name(name)
