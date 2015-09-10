"""Meta class for all CLI tests"""

import itertools
import types

from ddt import ddt
from robottelo.cli.metatest import default_data, template_methods
from robottelo.decorators import data


# Possible permutations of CRUD tests:
# e.g. positive_create, negative_create, positive_delete, etc
NAMES = ('%s_%s' % (a, b) for a, b in itertools.product(
    ('positive', 'negative'), ('create', 'delete', 'update')))


class MetaCLITest(type):
    """
    Meta class for all CLI tests
    """

    factory = None
    test_class = None

    def __new__(cls, name, bases, attributes):
        """
        Adds a create method for the specific class.

        @param mcs:
        @param name:
        @param bases:
        @param attributes:
        @return:
        """

        _klass = super(
            MetaCLITest, cls).__new__(cls, name, bases, attributes)

        # When loading test classes for a test run, the Nose class
        # loader "transplants" any class that inherits from unittest.TestCase
        # into an internal class "C". If your test class uses MetaCLI,
        # then it will automatically also inherit from BaseCLI and
        # Nose will automatically see a new "C". We want to ignore
        # this class when using MetaCLITest
        if name == 'C':
            return _klass

        # Only perform attribute tests if instance is MetaCLITest
        parents = [b for b in bases if isinstance(b, MetaCLITest)]
        if not parents:
            return _klass

        # Make sure test module has required properties
        if not hasattr(_klass, 'factory'):
            raise AttributeError('No "factory" attribute found.')
        if not hasattr(_klass, 'factory_obj'):
            raise AttributeError('No "factory_obj" attribute found.')
        if not hasattr(_klass, 'search_key'):
            setattr(_klass, 'search_key', 'name')

        # If the factory is a "plain" function makes it a staticmethod
        if isinstance(attributes['factory'], types.FunctionType):
            setattr(_klass, 'factory', staticmethod(attributes['factory']))

        for name in NAMES:
            test_name = 'test_%s' % name

            if test_name not in attributes.keys():
                data_name = '%s_data' % name

                # The data provided is a tuple so we need to unpack to pass to
                # the  data decorator e.g. @data(*((a, b), (a, c)))
                if data_name.upper() in attributes.keys():
                    # Use data provided by test class
                    params = attributes[data_name.upper()]
                else:
                    # Use data provided by default_data module
                    params = getattr(default_data, data_name.upper())
                # Pass data to @data decorator
                func = data(*params)(getattr(template_methods, test_name))
                # Update method's docstring to include name of object
                func.__doc__ = func.__doc__.replace(
                    'FOREMAN_OBJECT', _klass.factory_obj.__name__)
                # Add method to test class
                setattr(_klass, test_name, func)

        # Apply ddt decorator to class
        _klass = ddt(_klass)

        return _klass
