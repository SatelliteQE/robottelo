"""Tests for module ``robottelo.datafactory``."""
import itertools
import random

import six
import unittest2

from robottelo.config import settings
from robottelo.constants import STRING_TYPES
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import invalid_emails_list
from robottelo.datafactory import invalid_id_list
from robottelo.datafactory import invalid_interfaces_list
from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import invalid_usernames_list
from robottelo.datafactory import invalid_values_list
from robottelo.datafactory import InvalidArgumentError
from robottelo.datafactory import valid_cron_expressions
from robottelo.datafactory import valid_data_list
from robottelo.datafactory import valid_docker_repository_names
from robottelo.datafactory import valid_emails_list
from robottelo.datafactory import valid_environments_list
from robottelo.datafactory import valid_hostgroups_list
from robottelo.datafactory import valid_hosts_list
from robottelo.datafactory import valid_interfaces_list
from robottelo.datafactory import valid_labels_list
from robottelo.datafactory import valid_names_list
from robottelo.datafactory import valid_org_names_list
from robottelo.datafactory import valid_usernames_list

if six.PY2:
    import mock
else:
    from unittest import mock


class FilteredDataPointTestCase(unittest2.TestCase):
    """Tests for :meth:`robottelo.datafactory.filtered_datapoint` decorator"""

    @classmethod
    def setUpClass(cls):
        """Backup the config smoke property"""
        cls.backup = settings.run_one_datapoint

    def test_filtered_datapoint_True(self):
        """Tests if run_one_datapoint=false returns all data points"""
        settings.run_one_datapoint = False
        self.assertEqual(len(generate_strings_list()), 7)
        self.assertEqual(len(invalid_emails_list()), 8)
        self.assertEqual(len(invalid_id_list()), 4)
        self.assertEqual(len(invalid_interfaces_list()), 8)
        self.assertEqual(len(invalid_names_list()), 7)
        self.assertEqual(len(invalid_values_list()), 10)
        self.assertEqual(len(invalid_usernames_list()), 4)
        self.assertEqual(len(valid_labels_list()), 2)
        self.assertEqual(len(valid_data_list()), 7)
        self.assertEqual(len(valid_emails_list()), 8)
        self.assertEqual(len(valid_environments_list()), 4)
        self.assertEqual(len(valid_hosts_list()), 3)
        self.assertEqual(len(valid_hostgroups_list()), 7)
        self.assertEqual(len(valid_interfaces_list()), 3)
        self.assertEqual(len(valid_names_list()), 15)
        self.assertEqual(len(valid_org_names_list()), 7)
        self.assertEqual(len(valid_usernames_list()), 6)
        self.assertEqual(len((valid_cron_expressions())), 4)
        self.assertEqual(len(valid_docker_repository_names()), 7)

    def test_filtered_datapoint_False(self):
        """Tests if run_one_datapoint=True returns one data point"""
        settings.run_one_datapoint = True
        self.assertEqual(len(generate_strings_list()), 1)
        self.assertEqual(len(invalid_emails_list()), 1)
        self.assertEqual(len(invalid_id_list()), 1)
        self.assertEqual(len(invalid_interfaces_list()), 1)
        self.assertEqual(len(invalid_names_list()), 1)
        self.assertEqual(len(invalid_values_list()), 1)
        self.assertEqual(len(valid_data_list()), 1)
        self.assertEqual(len(valid_docker_repository_names()), 1)
        self.assertEqual(len(valid_emails_list()), 1)
        self.assertEqual(len(valid_environments_list()), 1)
        self.assertEqual(len(valid_hosts_list()), 1)
        self.assertEqual(len(valid_hostgroups_list()), 1)
        self.assertEqual(len(valid_interfaces_list()), 1)
        self.assertEqual(len(valid_labels_list()), 1)
        self.assertEqual(len(valid_names_list()), 1)
        self.assertEqual(len(valid_org_names_list()), 1)
        self.assertEqual(len(valid_usernames_list()), 1)
        self.assertEqual(len((valid_cron_expressions())), 1)

    @mock.patch('robottelo.datafactory.gen_string')
    def test_generate_strings_list_remove_str(self, gen_string):
        gen_string.side_effect = lambda str_type, _: str_type
        str_types = STRING_TYPES[:]
        remove_type = random.choice(str_types)
        str_types.remove(remove_type)
        str_types.sort()
        string_list = generate_strings_list(exclude_types=[remove_type])
        string_list.sort()
        self.assertEqual(string_list, str_types)

    @classmethod
    def tearDownClass(cls):
        """Reset the config smoke property"""
        settings.run_one_datapoint = cls.backup


class TestReturnTypes(unittest2.TestCase):
    """Tests for validating return types for different data factory
    functions."""

    def test_return_type(self):
        """This test validates return types for functions:

        1. :meth:`robottelo.datafactory.generate_strings_list`
        2. :meth:`robottelo.datafactory.invalid_emails_list`
        3. :meth:`robottelo.datafactory.invalid_names_list`
        4. :meth:`robottelo.datafactory.valid_data_list`
        5. :meth:`robottelo.datafactory.valid_docker_repository_names`
        6. :meth:`robottelo.datafactory.valid_emails_list`
        7. :meth:`robottelo.datafactory.valid_environments_list`
        8. :meth:`robottelo.datafactory.valid_hosts_list`
        9. :meth:`robottelo.datafactory.valid_hostgroups_list`
        10. :meth:`robottelo.datafactory.valid_labels_list`
        11. :meth:`robottelo.datafactory.valid_names_list`
        12. :meth:`robottelo.datafactory.valid_org_names_list`
        13. :meth:`robottelo.datafactory.valid_usernames_list`
        14. :meth:`robottelo.datafactory.invalid_id_list`
        15. :meth:`robottelo.datafactory.invalid_interfaces_list`
        16. :meth:`robottelo.datafactory.valid_interfaces_list`
        17. :meth:`robottelo.datafactory.valid_cron_expressions`

        """
        for item in itertools.chain(
                generate_strings_list(),
                invalid_emails_list(),
                invalid_interfaces_list(),
                invalid_names_list(),
                valid_data_list(),
                valid_docker_repository_names(),
                valid_emails_list(),
                valid_environments_list(),
                valid_hosts_list(),
                valid_hostgroups_list(),
                valid_interfaces_list(),
                valid_labels_list(),
                valid_names_list(),
                valid_org_names_list(),
                valid_cron_expressions(),
                valid_usernames_list()):
            self.assertIsInstance(item, six.text_type)
        for item in invalid_id_list():
            if not (
                    isinstance(item, (six.text_type, int)) or item is None
                    ):
                self.fail('Unexpected data type')


class InvalidValuesListTestCase(unittest2.TestCase):
    """Tests for :meth:`robottelo.datafactory.invalid_values_list`"""

    def test_return_values(self):
        """Tests if invalid values list returns right values based on input"""
        # Test valid values
        for value in 'api', 'cli', 'ui', None:
            return_value = invalid_values_list(value)
            self.assertIsInstance(return_value, list)
            if value == 'ui':
                self.assertEqual(len(return_value), 9)
            else:
                self.assertEqual(len(return_value), 10)
        # Test invalid values
        self.assertRaises(InvalidArgumentError, invalid_values_list, ' ')
        self.assertRaises(InvalidArgumentError, invalid_values_list, 'UI')
        self.assertRaises(InvalidArgumentError, invalid_values_list, 'CLI')
        self.assertRaises(InvalidArgumentError, invalid_values_list, 'API')
        self.assertRaises(InvalidArgumentError, invalid_values_list, 'invalid')
