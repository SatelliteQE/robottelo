# coding: utf-8

from unittest2 import TestCase
from robottelo.bz_helpers import get_deselect_bug_ids, group_by_key
from robottelo.helpers import get_func_name

BZ_DATA = {
    '1234': {
        'bug_data': {
            'resolution': 'WONTFIX',
            'flags': {'sat-6.3.0': '+'}
        }
    },
    '1235': {
        'bug_data': {
            'resolution': 'CANTFIX',
            'flags': {'sat-6.2.0': '+'}
        }
    },
    '1236': {
        'bug_data': {
            'resolution': '',
            'flags': {'sat-6.2.z': '+'}
        }
    },
    '1237': {
        'bug_data': {
            'resolution': 'NEW',
            'flags': {'sat-backlog': '+'}
        }
    }
}

DECORATED_FUNCTIONS = [
    ('function1', '1234'),
    ('function1', '1235'),
    ('function2', '1236'),
    ('function3', '1237'),
]


class BZHelperTestCase(TestCase):

    def test_get_wontfix_bugs(self):
        """Test if wontfixes are filtered"""
        self.assertNotIn('1236', get_deselect_bug_ids(BZ_DATA, lookup=True))
        self.assertIn('1234', get_deselect_bug_ids(BZ_DATA, lookup=True))
        self.assertIn('1235', get_deselect_bug_ids(BZ_DATA, lookup=True))

    def test_get_unflagged_bugs(self):
        """Test if unflagged are deselected"""
        self.assertIn('1237', get_deselect_bug_ids(BZ_DATA, lookup=True))

    def test_group_by_key(self):
        """Test if decorated functions are grouped"""
        grouped = group_by_key(DECORATED_FUNCTIONS)
        self.assertEqual(
            set(['function1', 'function2', 'function3']),
            set(list(grouped.keys()))
        )
        self.assertEqual(set(grouped['function1']), set(['1234', '1235']))
        self.assertEqual(set(grouped['function2']), set(['1236']))
        self.assertEqual(set(grouped['function3']), set(['1237']))

    def test_get_func_name(self):
        """Test if name is proper generated for function"""

        self.assertEqual(
            get_func_name(test_function),
            'tests.robottelo.test_bz_helpers.test_function'
        )


def test_function():
    """Does nothing, only used to test get_func_name"""
