# -*- encoding: utf-8 -*-
"""Test class for Partition Table UI"""
from ddt import ddt
from fauxfactory import gen_string
from robottelo.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.decorators import (
    bz_bug_is_open, data, run_only_on, skip_if_bug_open)
from robottelo.helpers import generate_strings_list, read_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_partitiontable
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class PartitionTable(UITestCase):
    """Implements the partition table tests from UI"""

    @data(*generate_strings_list(len1=10))
    def test_positive_create_partition_table(self, name):
        """@Test: Create a new partition table

        @Feature: Partition table - Positive Create

        @Assert: Partition table is created

        """
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                layout=read_data_file(PARTITION_SCRIPT_DATA_FILE),
                os_family='Red Hat'
            )
            self.assertIsNotNone(self.partitiontable.search(name))

    @data(*generate_strings_list(len1=256))
    def test_negative_create_partition_table_with_long_names(self, name):
        """@Test: Create a new partition table with 256 characters in name

        @Feature: Partition table - Negative Create

        @Assert: Partition table is not created

        """
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                layout=read_data_file(PARTITION_SCRIPT_DATA_FILE),
                os_family='Red Hat'
            )
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators['name_haserror']))
            self.assertIsNone(self.partitiontable.search(name))

    @data('', '  ')
    def test_negative_create_partition_table_with_empty_name(self, name):
        """@Test: Create partition table with blank and whitespace in name

        @Feature: Partition table - Negative Create

        @Assert: Partition table is not created

        """
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                layout=read_data_file(PARTITION_SCRIPT_DATA_FILE),
                os_family='Red Hat'
            )
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators['name_haserror']))

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

    @skip_if_bug_open('bugzilla', 1177591)
    @data(*generate_strings_list())
    def test_remove_partition_table(self, name):
        """@Test: Delete a partition table

        @Feature: Partition table - Positive Delete

        @Assert: Partition table is deleted

        """
        with Session(self.browser) as session:
            make_partitiontable(
                session, name=name, layout='test layout', os_family='Red Hat')
            self.assertIsNotNone(self.partitiontable.search(name))
            self.partitiontable.delete(name)
            self.assertIsNone(self.partitiontable.search(name))

    @data({u'name': gen_string('alpha'),
           u'new_name': gen_string('alpha')},
          {u'name': gen_string('html'),
           u'new_name': gen_string('html'), 'bugzilla': 1225857},
          {u'name': gen_string('utf8'),
           u'new_name': gen_string('utf8')},
          {u'name': gen_string('alphanumeric'),
           u'new_name': gen_string('alphanumeric')})
    def test_update_partition_table(self, test_data):
        """@Test: Update partition table with its name, layout and OS family

        @Feature: Partition table - Positive Update

        @Assert: Partition table is updated

        """
        bug_id = test_data.pop('bugzilla', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest(
                'Bugzilla bug {0} is open for html data.'.format(bug_id)
            )
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=test_data['name'],
                layout='test layout',
                os_family='Debian',
            )
            self.assertIsNotNone(self.partitiontable.search(test_data['name']))
            self.partitiontable.update(
                test_data['name'],
                test_data['new_name'],
                read_data_file(PARTITION_SCRIPT_DATA_FILE),
                'Red Hat',
            )
            self.assertIsNotNone(self.partitiontable.search
                                 (test_data['new_name']))
