# coding: utf-8

from unittest2 import TestCase
from robottelo.bz_helpers import get_deselect_bug_ids, group_by_key
from robottelo.helpers import get_func_name


class BZHelperTestCase(TestCase):

    def setUp(self):
        self.bz_data = {
            '1234': {
                'bug_data': {
                    'resolution': 'WONTFIX'
                }
            },
            '1235': {
                'bug_data': {
                    'resolution': 'CANTFIX'
                }
            },
            '1236': {
                'bug_data': {
                    'resolution': ''
                }
            }
        }

        self.decorated_functions = [
            ('function1', '1234'),
            ('function1', '1235'),
            ('function2', '1236')
        ]

    def test_get_wontfix_bugs(self):
        """Test if wontfixes are filtered"""
        self.assertNotIn('1236', get_deselect_bug_ids(self.bz_data))

    def test_group_by_key(self):
        """Test if decorated functions are grouped"""
        grouped = group_by_key(self.decorated_functions)
        self.assertEqual(
            set(['function1', 'function2']),
            set(list(grouped.keys()))
        )
        self.assertEqual(set(grouped['function1']), set(['1234', '1235']))
        self.assertEqual(set(grouped['function2']), set(['1236']))

    def test_get_func_name(self):
        """Test if name is proper generated for function"""

        self.assertEqual(
            get_func_name(test_function),
            'tests.robottelo.test_bz_helpers.test_function'
        )


def test_function():
    """Does nothing, only used to test get_func_name"""
