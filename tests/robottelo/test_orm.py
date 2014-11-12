"""Tests for :mod:`robottelo.orm`."""
# (Too many public methods) pylint: disable=R0904
#
# Python 3.3 and later includes module `ipaddress` in the standard library. If
# Robottelo ever moves past Python 2.x, that module should be used instead of
# `socket`.
from fauxfactory import gen_integer
from robottelo.api import client
from robottelo.common import conf, helpers
from robottelo import entities, orm
from sys import version_info
import ddt
import mock
import socket
import unittest


class SampleEntity(orm.Entity):
    """Sample entity to be used in the tests"""
    name = orm.StringField()
    value = orm.IntegerField()

    class Meta(object):
        """Non-field attributes for this entity."""
        # (too-few-public-methods) pylint:disable=R0903
        api_path = 'foo'


class ManyRelatedEntity(orm.Entity):
    """An entity with a OneToManyField"""
    entities = orm.OneToManyField(SampleEntity)


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
    one_to_one = orm.OneToOneField(SampleEntity)
    one_to_many = orm.OneToManyField(SampleEntity)

    class Meta(object):
        """Non-field attributes for this entity."""
        # (too-few-public-methods) pylint:disable=R0903
        api_path = ''


#------------------------------------------------------------------------------


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

        self.assertIsInstance(fields['name'], orm.StringField)
        self.assertIsInstance(fields['value'], orm.IntegerField)

    def test_path(self):
        """Test :meth:`robottelo.orm.Entity.path`."""
        self.assertEqual(SampleEntity().path(), self.base_path)
        self.assertEqual(SampleEntity(id=5).path(), self.base_path + '/5')
        self.assertEqual(SampleEntity(id=5).path('base'), self.base_path)
        with self.assertRaises(orm.NoSuchPathError):
            SampleEntity().path('self')


class OneToManyFieldTestCase(unittest.TestCase):
    """Tests for the OneToManyField"""
    def test_get_value(self):
        """Test :meth:`robottelo.orm.OneToManyField.get_value`.

        Assert that an object of the correct type is returned.

        """
        self.assertIsInstance(
            orm.OneToManyField(SampleEntity).get_value(),
            SampleEntity
        )


class BooleanFieldTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.BooleanField`."""
    def test_get_value(self):
        """Test method ``get_value``.

        Ensure either ``True`` or ``False`` is returned.

        """
        self.assertIn(orm.BooleanField().get_value(), (True, False))


class EmailFieldTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.EmailField`."""
    def test_get_value(self):
        """Test method ``get_value``.

        Ensure a unicode string is returned, containing the character '@'.

        """
        email = orm.EmailField().get_value()
        if version_info[0] == 2:
            self.assertIsInstance(email, unicode)
        else:
            self.assertIsInstance(email, str)
        self.assertIn('@', email)


class FloatFieldTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.FloatField`."""
    def test_get_value(self):
        """Test method ``get_value``.

        Ensure the value returned is a ``float``.

        """
        self.assertIsInstance(orm.FloatField().get_value(), float)


class IntegerFieldTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.IntegerField`."""
    def test_get_value(self):
        """Test method ``get_value``.

        Ensure the value returned is a ``int``.

        """
        self.assertIsInstance(orm.IntegerField().get_value(), int)

    def test_min_val(self):
        """Set a ``min_val`` and call ``get_value``.

        Assert the number generated is greater than or equal to the specified
        value.

        """
        min_val = gen_integer()
        val = orm.IntegerField(min_val=min_val).get_value()
        self.assertGreaterEqual(val, min_val)

    def test_max_val(self):
        """Set a ``max_val`` and call ``get_value``.

        Assert the number generated is less than or equal to the specified
        value.

        """
        max_val = gen_integer()
        val = orm.IntegerField(max_val=max_val).get_value()
        self.assertLessEqual(val, max_val)

    def test_min_max_val(self):
        """Set both ``min_val`` and ``max_val`` and call ``get_value``.

        Assert the number generated falls between the specified bounds.

        """
        min_val = gen_integer(-1000, 0)
        max_val = gen_integer(0, 1000)

        # First, we'll allow a range of values...
        val = orm.IntegerField(min_val, max_val).get_value()
        self.assertGreaterEqual(val, min_val)
        self.assertLessEqual(val, max_val)

        # ... then, we'll allow only a single value...
        val = orm.IntegerField(min_val, min_val).get_value()
        self.assertEqual(val, min_val)

        # ... twice over, just to be sure.
        val = orm.IntegerField(max_val, max_val).get_value()
        self.assertEqual(val, max_val)

class IPAddressFieldTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.IPAddressField`."""
    def test_get_value(self):
        """Test method ``get_value``.

        Ensure the value returned is acceptable to ``socket.inet_aton``.

        """
        addr = orm.IPAddressField().get_value()
        try:
            socket.inet_aton(addr)
        except socket.error as err:
            self.fail('({0}) {1}'.format(addr, err))


class MACAddressFieldTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.MACAddressField`."""
    def test_get_value(self):
        """Test method ``get_value``.

        Ensure the value returned is a string containing 12 hex digits (either
        upper or lower case), grouped into pairs of digits and separated by
        colon characters. For example: ``'01:23:45:FE:dc:BA'``

        """
        # flake8:noqa (line-too-long) pylint:disable=C0301
        # This regex is inspired by suggestions from others, but simpler. See:
        # http://stackoverflow.com/questions/7629643/how-do-i-validate-the-format-of-a-mac-address
        self.assertRegexpMatches(
            orm.MACAddressField().get_value().upper(),
            '^([0-9A-F]{2}[:]){5}[0-9A-F]{2}$'
        )


class OneToOneFieldTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.OneToOneField`."""
    def test_get_value(self):
        """Test :meth:`robottelo.orm.OneToOneField.get_value`.

        Assert that an object of the correct type is returned.

        """
        self.assertIsInstance(
            orm.OneToOneField(SampleEntity).get_value(),
            SampleEntity
        )


class StringFieldTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.StringField`."""
    def test_get_value(self):
        """Test method ``get_value``.

        Ensure a unicode string at least 1 char long is returned.

        """
        string = orm.StringField().get_value()
        if version_info[0] == 2:
            self.assertIsInstance(string, unicode)
        else:
            self.assertIsInstance(string, str)
        self.assertGreater(len(string), 0)

    def test_len(self):
        """Set a ``len`` and call ``get_value``.

        Assert the length of generated string specified by ``len``.

        """
        string = orm.StringField(len=(1,20)).get_value()
        self.assertGreater(len(string), 0)
        self.assertLessEqual(len(string), 20)

        string = orm.StringField(len=5).get_value()
        self.assertEqual(len(string), 5)

    def test_str_type(self):
        """Set a ``str_type`` can call ``get_value``.

        Assert the string generated is comprised of characters within the
        specified character set.

        """
        # This can be shrunk down to about 5 lines of idiomatic code, but doing
        # so totally destroys readability.
        self.assertTrue(
            orm.StringField(str_type=('alpha',)).get_value().isalpha()
        )
        self.assertTrue(
            orm.StringField(str_type=['alpha']).get_value().isalpha()
        )
        self.assertTrue(
            orm.StringField(str_type=('numeric',)).get_value().isnumeric()
        )
        self.assertTrue(
            orm.StringField(str_type=['numeric']).get_value().isnumeric()
        )

        string = orm.StringField(str_type=('alpha', 'numeric')).get_value()
        self.assertTrue(string.isalpha() or string.isnumeric())


class GetClassTestCase(unittest.TestCase):
    """Tests for ``robottelo.orm._get_class``."""
    # (protected-access) pylint:disable=W0212
    def test_class(self):
        """Pass a class into the function.

        Assert that the class passed in is returned.

        """
        self.assertEqual(SampleEntity, orm._get_class(SampleEntity))

    def test_name(self):
        """Pass a string name into the function.

        Assert that the named class is returned from :mod:`robottelo.entities`.

        """
        self.assertEqual(
            entities.ActivationKey,
            orm._get_class('ActivationKey'),
        )

    def test_name_module(self):
        """Pass a class name and module name into the function.

        Assert that the named class is returned from the named module.

        """
        self.assertEqual(
            SampleEntity,
            orm._get_class('SampleEntity', 'tests.robottelo.test_orm'),
        )


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

        Assert that ``EntityDeleteMixin.delete`` returns ``None`` if it
        receives an HTTP 200 response.

        """
        # Create a mock server response object.
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        # Make `client.delete` return the above object.
        client.delete = mock.Mock(return_value=mock_response)

        # See if EntityDeleteMixin.delete behaves correctly.
        response = EntityWithDelete(id=self.entity_id).delete()
        self.assertIsNone(response)

    def test_delete_202(self):
        """Test :meth:`robottelo.orm.EntityDeleteMixin.delete`.

        Assert that ``EntityDeleteMixin.delete`` returns a task ID if it
        receives an HTTP 202 response.

        """
        # Create a mock server response object.
        foreman_task_id = gen_integer()
        mock_response = mock.Mock()
        mock_response.status_code = 202
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {u'id': foreman_task_id}

        # Make `client.delete` return the above object.
        client.delete = mock.Mock(return_value=mock_response)

        # See if EntityDeleteMixin.delete behaves correctly.
        response = EntityWithDelete(id=self.entity_id).delete(
            synchronous=False
        )
        self.assertEqual(response, foreman_task_id)

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
