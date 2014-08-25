"""Tests for :mod:`robottelo.orm`."""
# (Too many public methods) pylint: disable=R0904
#
# Python 3.3 and later includes module `ipaddress` in the standard library. If
# Robottelo ever moves past Python 2.x, that module should be used instead of
# `socket`.
from fauxfactory import FauxFactory
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
        api_path = 'foo'


class ManyRelatedEntity(orm.Entity):
    """An entity with a OneToManyField"""
    entities = orm.OneToManyField(SampleEntity)


class EntityWithDelete(orm.Entity, orm.EntityDeleteMixin):
    """An entity which inherits from :class:`orm.EntityDeleteMixin`."""

    class Meta(object):
        """Non-field attributes for this entity."""
        api_path = 'foo'


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

    def test_entity_get_values(self):
        """Test :meth:`robottelo.orm.Entity.get_values`."""
        name = orm.StringField().get_value()
        value = orm.IntegerField().get_value()

        # First, provide a name.
        values = SampleEntity(name=name).get_values()
        self.assertIn('name', values.keys())
        self.assertNotIn('value', values.keys())
        self.assertEqual(values['name'], name)

        # Second, provide a value.
        values = SampleEntity(value=value).get_values()
        self.assertNotIn('name', values.keys())
        self.assertIn('value', values.keys())
        self.assertEqual(values['value'], value)

        # Third, provide a name and value.
        values = SampleEntity(name=name, value=value).get_values()
        self.assertIn('name', values.keys())
        self.assertIn('value', values.keys())
        self.assertEqual(values['name'], name)
        self.assertEqual(values['value'], value)


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
        self.assertEqual(SampleEntity(id=5).path('all'), self.base_path)
        with self.assertRaises(orm.NoSuchPathError):
            SampleEntity().path('this')


class OneToManyFieldTestCase(unittest.TestCase):
    """Tests for the OneToManyField"""
    def test_get_value(self):
        """Test :meth:`robottelo.orm.OneToManyField.get_value`.

        Assert that ``get_value()`` returns a list of entity instances.

        """
        values = orm.OneToManyField(SampleEntity).get_value()
        self.assertIsInstance(values, list)
        for value in values:
            self.assertIsInstance(value, SampleEntity)


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
        min_val = FauxFactory.generate_integer()
        val = orm.IntegerField(min_val=min_val).get_value()
        self.assertGreaterEqual(val, min_val)

    def test_max_val(self):
        """Set a ``max_val`` and call ``get_value``.

        Assert the number generated is less than or equal to the specified
        value.

        """
        max_val = FauxFactory.generate_integer()
        val = orm.IntegerField(max_val=max_val).get_value()
        self.assertLessEqual(val, max_val)

    def test_min_max_val(self):
        """Set both ``min_val`` and ``max_val`` and call ``get_value``.

        Assert the number generated falls between the specified bounds.

        """
        min_val = FauxFactory.generate_integer(-1000, 0)
        max_val = FauxFactory.generate_integer(0, 1000)

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

        Assert that ``get_value()`` returns an entity instance.

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

    def test_max_len(self):
        """Set a ``max_len`` and call ``get_value``.

        Assert the string generated is between 1 and ``max_len`` chars long,
        inclusive.

        """
        string = orm.StringField(max_len=20).get_value()
        self.assertGreater(len(string), 0)
        self.assertLessEqual(len(string), 20)

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
    """Tests for :func:`robottelo.orm._get_class`."""
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


@ddt.ddt
class GetValueTestCase(unittest.TestCase):
    """Tests for :func:`robottelo.orm._get_value`."""
    # (protected-access) pylint:disable=W0212
    def test_field_choices(self):
        """Pass in a field that has a set of choices.

        Assert a value from the choices is returned.

        """
        field = orm.StringField(choices=('a', 'b', 'c'))
        self.assertIn(orm._get_value(field, None), ('a', 'b', 'c'))

    @ddt.data('foo', None, True, False, 150)
    def test_field_default(self, value):
        """Pass in a field that has a default value of ``value``.

        Assert ``value`` is returned.

        """
        field = orm.StringField(default=value)
        self.assertEqual(orm._get_value(field, None), value)

    @ddt.data('foo', None, True, False, 150)
    def test_default(self, value):
        """Pass in a field that has no default value or choices.

        Assert the default argument to ``_get_value`` is returned.

        """
        field = orm.StringField()
        self.assertEqual(orm._get_value(field, lambda: value), value)
        self.assertEqual(orm._get_value(field, value), value)

    def test_field_default_and_choices(self):
        """Pass in a field that has a default and choices.

        Assert the default value is returned.

        """
        field = orm.StringField(choices=('a', 'b', 'c'), default='d')
        self.assertEqual(orm._get_value(field, None), 'd')


class EntityDeleteMixinTestCase(unittest.TestCase):
    """Tests for :class:`robottelo.orm.EntityDeleteMixin`."""
    def setUp(self):  # pylint:disable=C0103
        """Back up and customize ``conf.properties`` and ``client.delete``.

        Also generate a number suitable for use when instantiating entities.

        """
        self.conf_properties = conf.properties.copy()
        conf.properties['main.server.hostname'] = 'example.com'
        conf.properties['foreman.admin.username'] = 'Alice'
        conf.properties['foreman.admin.password'] = 'hackme'
        self.client_delete = client.delete
        # SomeEntity(id=self.entity_id)
        self.entity_id = FauxFactory.generate_integer(min_value=1)

    def tearDown(self):  # pylint:disable=C0103
        """Restore ``conf.properties``."""
        conf.properties = self.conf_properties
        client.delete = self.client_delete

    def test_delete_200(self):
        """Call :meth:`robottelo.orm.EntityWithDelete.delete`.

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
        """Call :meth:`robottelo.orm.EntityWithDelete.delete`.

        Assert that ``EntityDeleteMixin.delete`` returns a task ID if it
        receives an HTTP 202 response.

        """
        # Create a mock server response object.
        foreman_task_id = FauxFactory.generate_integer()
        mock_response = mock.Mock()
        mock_response.status_code = 202
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {u'id': foreman_task_id}

        # Make `client.delete` return the above object.
        client.delete = mock.Mock(return_value=mock_response)

        # See if EntityDeleteMixin.delete behaves correctly.
        response = EntityWithDelete(id=self.entity_id).delete()
        self.assertEqual(response, foreman_task_id)
