"""
Meta class for all CLI tests
"""

from ddt import data
from robottelo.common.helpers import generate_string


class MetaCLITest(type):
    """
    Meta class for all CLI tests
    """

    factory = None
    test_class = None

    def __new__(mcs, name, bases, attributes):
        """
        Adds a create method for the specific class.

        @param mcs:
        @param name:
        @param bases:
        @param attributes:
        @return:
        """

        _klass = super(
            MetaCLITest, mcs).__new__(mcs, name, bases, attributes)

        # Make sure test module has required properties
        if not hasattr(_klass, "factory"):
            raise AttributeError("No 'factory' attribute found.")
        if not hasattr(_klass, "factory_obj"):
            raise AttributeError("No 'factory_obj' attribute found.")

        # Dynamically adds methods to test module
        setattr(_klass, "create", mcs.create)
        setattr(_klass, "test_positive_create", mcs.test_positive_create)
        setattr(_klass, "test_negative_create", mcs.test_negative_create)

        return _klass

    @staticmethod
    def create(cls, options=None):
        """
        Creates a new record
        """

        result = cls.factory(options)

        return result

    @staticmethod
    @data(
        ('name', generate_string("latin1", 10).encode("utf-8")),
        ('name', generate_string("utf8", 10).encode("utf-8")),
        ('name', generate_string("alpha", 10)),
        ('name', generate_string("alphanumeric", 10)),
        ('name', generate_string("numeric", 10)),
    )
    def test_positive_create(cls, key_value):
        """
        Successfully creates object.
        """
        key = key_value[0]
        value = key_value[1]

        new_obj = cls.create({key: value})
        result = cls.factory_obj().info({key: new_obj[key]})

        # Dict keys start with upper case
        _dict_key = key[0].upper() + key[1:]
        cls.assertEqual(new_obj[key], result.stdout[_dict_key])
        cls.assertEqual(result.return_code, 0)
        cls.assertTrue(len(result.stderr) == 0)

    @staticmethod
    @data(
        ('name', generate_string("latin1", 300).encode("utf-8")),
        ('name', " "),
        ('', generate_string("alpha", 10)),
        (generate_string("alphanumeric", 10), " "),
    )
    def test_negative_create(cls, key_value):
        """
        Fails to creates object.
        """
        key = key_value[0]
        value = key_value[1]

        new_obj = cls.factory_obj().create({key: value})
        cls.assertNotEqual(new_obj.return_code, 0)
        cls.assertIsNotNone(new_obj.stderr)
