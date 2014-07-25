# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Partition Table UI
"""
from ddt import ddt
from robottelo.common.decorators import data
from robottelo.common.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.common.helpers import (generate_string, read_data_file,
                                      valid_names_list, generate_strings_list)
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc,
                                  make_partitiontable)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class PartitionTable(UITestCase):
    """
    Implements the partition table tests from UI
    """

    org_name = None
    loc_name = None

    def setUp(self):
        super(PartitionTable, self).setUp()
        #  Make sure to use the Class' org_name instance
        if (PartitionTable.org_name is None
                and PartitionTable.loc_name is None):
            PartitionTable.org_name = generate_string("alpha", 8)
            PartitionTable.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=PartitionTable.org_name)
                make_loc(session, name=PartitionTable.loc_name)

    @data(*valid_names_list())
    def test_positive_create_partition_table(self, name):
        """
        @Test: Create a new partition table
        @Feature: Partition table - Positive Create
        @Assert: Partition table is created
        """

        layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_partitiontable(session, name=name, layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.search(name))

    @data(*generate_strings_list(len1=256))
    def test_negative_create_partition_table_1(self, name):
        """
        @Test: Create a new partition table with 256 characters in name
        @Feature: Partition table - Negative Create
        @Assert: Partition table is not created
        """

        layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_partitiontable(session, name=name, layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators["alert.error"]))
            self.assertIsNone(self.partitiontable.search(name))

    @data({u'name': ""},
          {u'name': "  "})
    def test_negative_create_partition_table_2(self, test_data):
        """
        @Test: Create partition table with blank and whitespace in name
        @Feature: Partition table - Negative Create
        @Assert: Partition table is not created
        """

        layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_partitiontable(session, name=test_data['name'], layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators["name_haserror"]))

    @data(*generate_strings_list(len1=6))
    def test_negative_create_partition_table_3(self, name):
        """
        @Test: Create a new partition table with same name
        @Feature: Partition table - Negative Create
        @Assert: Partition table is not created
        """

        layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_partitiontable(session, name=name, layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.search(name))
            make_partitiontable(session, name=name, layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators["name_haserror"]))

    @data(*generate_strings_list(len1=6))
    def test_negative_create_partition_table_4(self, name):
        """
        @Test: Create a new partition table with empty layout
        @Feature: Partition table - Negative Create
        @Assert: Partition table is not created
        """

        layout = ""
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_partitiontable(session, name=name, layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators["haserror"]))
            self.assertIsNone(self.partitiontable.search(name))

    @data(*valid_names_list())
    def test_remove_partition_table(self, name):
        """
        @Test: Delete a partition table
        @Feature: Partition table - Positive Delete
        @Assert: Partition table is deleted
        """

        layout = "test layout"
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_partitiontable(session, name=name, layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.search(name))
            self.partitiontable.delete(name, really=True)
            self.assertTrue(self.partitiontable.wait_until_element
                            (common_locators["notif.success"]))
            self.assertIsNone(self.partitiontable.search(name))

    @data({u'name': generate_string('alpha', 10),
           u'new_name': generate_string('alpha', 10)},
          {u'name': generate_string('html', 10),
           u'new_name': generate_string('html', 10)},
          {u'name': generate_string('utf8', 10),
           u'new_name': generate_string('utf8', 10)},
          {u'name': generate_string('alphanumeric', 255),
           u'new_name': generate_string('alphanumeric', 255)})
    def test_update_partition_table(self, test_data):
        """
        @Test: Update partition table with its name, layout and OS family
        @Feature: Partition table - Positive Update
        @Assert: Partition table is updated
        """

        layout = "test layout"
        new_layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = "Debian"
        new_os_family = "Red Hat"
        with Session(self.browser) as session:
            make_partitiontable(session, name=test_data['name'], layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.search(test_data['name']))
            self.partitiontable.update(test_data['name'],
                                       test_data['new_name'],
                                       new_layout, new_os_family)
            self.assertIsNotNone(self.partitiontable.search
                                 (test_data['new_name']))
