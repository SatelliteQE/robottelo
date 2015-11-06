# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for Partition Table UI"""
from fauxfactory import gen_string
from robottelo.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import bz_bug_is_open, run_only_on
from robottelo.helpers import read_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_partitiontable
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


def valid_partition_table_names():
    """Returns a list of valid partition table names"""
    return [
        {u'name': gen_string('alpha')},
        {u'name': gen_string('numeric')},
        {u'name': gen_string('alphanumeric')},
        {u'name': gen_string('html'), 'bugzilla': 1225857},
        {u'name': gen_string('latin1')},
        {u'name': gen_string('utf8')},
    ]


def valid_partition_table_update_names():
    """Returns a list of valid partition table names for update tests"""
    return [
        {u'new_name': gen_string('alpha')},
        {u'new_name': gen_string('html'), 'bugzilla': 1225857},
        {u'new_name': gen_string('utf8')},
        {u'new_name': gen_string('alphanumeric')},
    ]


class PartitionTable(UITestCase):
    """Implements the partition table tests from UI"""

    @run_only_on('sat')
    def test_positive_create_partition_table(self):
        """@Test: Create a new partition table

        @Feature: Partition table - Positive Create

        @Assert: Partition table is created

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=10):
                with self.subTest(name):
                    make_partitiontable(
                        session,
                        name=name,
                        layout=read_data_file(PARTITION_SCRIPT_DATA_FILE),
                        os_family='Red Hat'
                    )
                    self.assertIsNotNone(self.partitiontable.search(name))

    @run_only_on('sat')
    def test_negative_create_partition_table_invalid_names(self):
        """@Test: Create partition table with invalid names

        @Feature: Partition table - Negative Create

        @Assert: Partition table is not created

        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_partitiontable(
                        session,
                        name=name,
                        layout=read_data_file(PARTITION_SCRIPT_DATA_FILE),
                        os_family='Red Hat'
                    )
                    self.assertIsNotNone(
                        self.partitiontable.wait_until_element(
                            common_locators['name_haserror'])
                    )

    @run_only_on('sat')
    def test_negative_create_partition_table_with_same_name(self):
        """@Test: Create a new partition table with same name

        @Feature: Partition table - Negative Create

        @Assert: Partition table is not created

        """
        name = gen_string('utf8')
        layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = 'Red Hat'
        with Session(self.browser) as session:
            make_partitiontable(
                session, name=name, layout=layout, os_family=os_family)
            self.assertIsNotNone(self.partitiontable.search(name))
            make_partitiontable(
                session, name=name, layout=layout, os_family=os_family)
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators['name_haserror']))

    @run_only_on('sat')
    def test_negative_create_partition_table_empty_layout(self):
        """@Test: Create a new partition table with empty layout

        @Feature: Partition table - Negative Create

        @Assert: Partition table is not created

        """
        name = gen_string('utf8')
        with Session(self.browser) as session:
            make_partitiontable(
                session, name=name, layout='', os_family='Red Hat')
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.partitiontable.search(name))

    @run_only_on('sat')
    def test_remove_partition_table(self):
        """@Test: Delete a partition table

        @Feature: Partition table - Positive Delete

        @Assert: Partition table is deleted

        """
        with Session(self.browser) as session:
            for test_data in valid_partition_table_names():
                with self.subTest(test_data):
                    bug_id = test_data.pop('bugzilla', None)
                    if bug_id is not None and bz_bug_is_open(bug_id):
                        self.skipTest(
                            'Bugzilla bug {0} is open for html '
                            'data.'.format(bug_id)
                        )
                    name = test_data['name']
                    make_partitiontable(
                        session, name=name,
                        layout='test layout',
                        os_family='Red Hat'
                    )
                    self.partitiontable.delete(name)

    @run_only_on('sat')
    def test_update_partition_table(self):
        """@Test: Update partition table with its name, layout and OS family

        @Feature: Partition table - Positive Update

        @Assert: Partition table is updated

        """
        name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                layout='test layout',
                os_family='Debian',
            )
            self.assertIsNotNone(self.partitiontable.search(name))
            for test_data in valid_partition_table_update_names():
                with self.subTest(test_data):
                    bug_id = test_data.pop('bugzilla', None)
                    if bug_id is not None and bz_bug_is_open(bug_id):
                        self.skipTest(
                            'Bugzilla bug {0} is open for html '
                            'data.'.format(bug_id)
                        )
                        self.partitiontable.update(
                            name,
                            test_data['new_name'],
                            read_data_file(PARTITION_SCRIPT_DATA_FILE),
                            'Red Hat',
                        )
                        self.assertIsNotNone(self.partitiontable.search(
                            test_data['new_name']))
                        name = test_data['new_name']  # for next iteration
