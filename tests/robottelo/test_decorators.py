import unittest

from ddt import DATA_ATTR

from robottelo.common import conf
from robottelo.common.decorators import data


def function():
    """Function to test data decorator against"""


class DataDecoratorTestCase(unittest.TestCase):
    def setUp(self):
        self.test_data = ('one', 'two', 'three')

    def test_data_decorator_smoke(self):
        conf.properties['main.smoke'] = '1'
        decorated = data(*self.test_data)(function)
        data_attr = getattr(decorated, DATA_ATTR)

        self.assertEqual(len(data_attr), 1)
        self.assertIn(data_attr[0], self.test_data)

    def test_data_decorator_not_smoke(self):
        conf.properties['main.smoke'] = '0'
        decorated = data(*self.test_data)(function)
        data_attr = getattr(decorated, DATA_ATTR)

        self.assertEqual(len(data_attr), len(self.test_data))
        self.assertEqual(getattr(decorated, DATA_ATTR), self.test_data)
