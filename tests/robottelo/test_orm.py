"""Tests for :mod:`robottelo.orm`."""
# (Too many public methods) pylint: disable=R0904
#
# Python 3.3 and later includes module `ipaddress` in the standard library. If
# Robottelo ever moves past Python 2.x, that module should be used instead of
# `socket`.
from fauxfactory import gen_integer
from nailgun import client
from nailgun.entity_fields import (
    IntegerField,
    OneToManyField,
    OneToOneField,
    StringField,
)
from robottelo.common import conf, helpers
from robottelo import orm
import mock
import unittest


class SampleEntity(orm.Entity):
    """Sample entity to be used in the tests"""
    name = StringField()
    value = IntegerField()

    class Meta(object):
        """Non-field attributes for this entity."""
        # (too-few-public-methods) pylint:disable=R0903
        api_path = 'foo'


class ManyRelatedEntity(orm.Entity):
    """An entity with a ``OneToManyField`` pointing to ``SampleEntity``."""
    entities = OneToManyField(SampleEntity)


class EntityWithDelete(orm.Entity, orm.EntityDeleteMixin):
    """
    An entity which inherits from :class:`robottelo.orm.EntityDeleteMixin`.
    """

    class Meta(object):
        """Non-field attributes for this entity."""
        # (too-few-public-methods) pylint:disable=R0903
        api_path = ''


class EntityWithRead(orm.Entity, orm.EntityReadMixin):
    """An entity which inherits from :class:`robottelo.orm.EntityReadMixin`."""
    one_to_one = OneToOneField(SampleEntity)
    one_to_many = OneToManyField(SampleEntity)

    class Meta(object):
        """Non-field attributes for this entity."""
        # (too-few-public-methods) pylint:disable=R0903
        api_path = ''


# -----------------------------------------------------------------------------


class EntityTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.Entity`."""
    def setUp(self):  # pylint:disable=C0103
        """
        Back up and configure ``conf.properties``, and set ``self.base_path``.
        """
        self.conf_properties = conf.properties.copy()
        conf.properties['main.server.hostname'] = 'example.com'
        self.base_path = '{0}/{1}'.format(
            helpers.get_server_url(),
            SampleEntity.Meta.api_path
        )

    def tearDown(self):  # pylint:disable=C0103
        """Restore ``conf.properties``."""
        conf.properties = self.conf_properties

    def test_entity_get_fields(self):
        """Test :meth:`robottelo.orm.Entity.get_fields`."""
        fields = SampleEntity().get_fields()

        self.assertIn('name', fields)
        self.assertIn('value', fields)

        self.assertIsInstance(fields['name'], StringField)
        self.assertIsInstance(fields['value'], IntegerField)

    def test_path(self):
        """Test :meth:`robottelo.orm.Entity.path`."""
        self.assertEqual(SampleEntity().path(), self.base_path)
        self.assertEqual(SampleEntity(id=5).path(), self.base_path + '/5')
        self.assertEqual(SampleEntity(id=5).path('base'), self.base_path)
        with self.assertRaises(orm.NoSuchPathError):
            SampleEntity().path('self')


class EntityDeleteMixinTestCase(unittest.TestCase):
    """Tests for entity mixin classes."""
    def setUp(self):  # pylint:disable=C0103
        """Back up several objects so they can be safely modified.

        Also generate a number suitable for use as an entity ID.

        """
        self.client_delete = client.delete
        self.client_get = client.get
        self.conf_properties = conf.properties.copy()
        conf.properties['main.server.hostname'] = 'example.com'
        conf.properties['foreman.admin.username'] = 'Alice'
        conf.properties['foreman.admin.password'] = 'hackme'

        # e.g. SomeEntity(id=self.entity_id)
        self.entity_id = gen_integer(min_value=1)

    def tearDown(self):  # pylint:disable=C0103
        """Restore backed-up objects."""
        client.delete = self.client_delete
        client.get = self.client_get
        conf.properties = self.conf_properties

    def test_delete_200(self):
        """Test :meth:`robottelo.orm.EntityDeleteMixin.delete`.

        Assert that ``delete`` returns a JSON-decoded response from the server
        when an HTTP 200 status code is returned.

        """
        delete_return = mock.Mock()
        delete_return.status_code = 200
        delete_return.json.return_value = {'9501743': '14697417'}  # arbitrary
        with mock.patch.object(client, 'delete') as client_delete:
            client_delete.return_value = delete_return
            self.assertEqual(
                EntityWithDelete(id=self.entity_id).delete(),
                delete_return.json.return_value
            )

    def test_delete_202(self):
        """Test :meth:`robottelo.orm.EntityDeleteMixin.delete`.

        Assert that ``delete`` returns information about a foreman task when an
        HTTP 202 status code is returned.

        """
        delete_return = mock.Mock()
        delete_return.status_code = 202
        delete_return.json.return_value = {'id': gen_integer()}  # mock task ID
        with mock.patch.object(client, 'delete') as client_delete:
            client_delete.return_value = delete_return
            with mock.patch.object(orm, '_poll_task') as poller:
                poller.return_value = {'324171': '59601212'}  # arbitrary
                self.assertEqual(
                    EntityWithDelete(id=self.entity_id).delete(),
                    poller.return_value
                )

    def test_read(self):
        """Test :meth:`robottelo.orm.EntityReadMixin.read`  and
        :meth:`robottelo.orm.EntityReadMixin.read_json`.

        Assert that ``EntityReadMixin.read_json`` returns the server's
        response, with all JSON decoded.

        Assert that ``EntityReadMixin.read`` returns an object with correctly
        populated attributes.

        """
        # Create a mock server response object.
        mock_response = mock.Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            u'id': self.entity_id,
            u'one_to_one_id': 123,
            u'one_to_many_ids': [234, 345],
        }

        # Make `client.get` return the above object.
        client.get = mock.Mock(return_value=mock_response)

        # See if EntityReadMixin.read_json behaves correctly.
        self.assertEqual(
            EntityWithRead(id=self.entity_id).read_json(),
            mock_response.json.return_value,
        )

        # See if EntityReadMixin.read behaves correctly.
        entity = EntityWithRead(id=self.entity_id).read()
        self.assertEqual(entity.id, self.entity_id)
        self.assertIsInstance(entity.one_to_one, SampleEntity)
        self.assertEqual(entity.one_to_one.id, 123)
        self.assertEqual(len(entity.one_to_many), 2)
        for entity_ in entity.one_to_many:
            self.assertIsInstance(entity_, SampleEntity)
            self.assertIn(entity_.id, [234, 345])
