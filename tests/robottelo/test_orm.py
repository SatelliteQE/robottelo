"""Tests for robottelo.orm module"""
# (Too many public methods) pylint: disable=R0904
#
# Python 3.3 and later includes module `ipaddress` in the standard library. If
# Robottelo ever moves past Python 2.x, that module should be used instead of
# `socket`.
from fauxfactory import FauxFactory
from robottelo import orm
from sys import version_info
import socket
import unittest


class SampleEntity(orm.Entity):
    """Sample entity to be used in the tests"""
    name = orm.StringField()
    value = orm.IntegerField()


class ManyRelatedEntity(orm.Entity):
    """An entity with a OneToManyField"""
    entities = orm.OneToManyField(SampleEntity)


class EntityTestCase(unittest.TestCase):
    def test_entity_get_fields(self):
        """Test Entity instance ``get_fields`` method."""
        entity = SampleEntity()
        fields = entity.get_fields()

        self.assertIn('name', fields)
        self.assertIn('value', fields)

        self.assertIsInstance(fields['name'], orm.StringField)
        self.assertIsInstance(fields['value'], orm.IntegerField)


class OneToManyFieldTestCase(unittest.TestCase):
    """Tests for the OneToManyField"""

    def test_value_is_single_model_instance(self):
        """Test a single entity value"""
        entity = SampleEntity(name='aname')
        other = ManyRelatedEntity(entities=entity)

        self.assertIsInstance(other.entities, list)
        self.assertEqual(other.entities[0].name, 'aname')

    def test_value_is_dictionary(self):
        """Test a single dictionary value"""
        entity = {'name': 'aname'}
        other = ManyRelatedEntity(entities=entity)

        self.assertIsInstance(other.entities, list)
        self.assertEqual(other.entities[0].name, 'aname')

    def test_value_is_list_of_dictionary(self):
        """Test a list of dictionaries value"""
        entity = [{'name': 'aname'}]
        other = ManyRelatedEntity(entities=entity)

        self.assertIsInstance(other.entities, list)
        self.assertEqual(other.entities[0].name, 'aname')


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
        """Test method ``get_value``.

        Assert a :class:`robottelo.orm.Entity` instance is returned.

        """
        self.assertIsInstance(
            orm.OneToOneField(SampleEntity).get_value(),
            orm.Entity
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
        self.assertLess(len(string), 20)
