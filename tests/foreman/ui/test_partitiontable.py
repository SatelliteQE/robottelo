# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Partition Table UI
"""

from robottelo.common.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.common.helpers import generate_string, read_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc,
                                  make_partitiontable)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


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

    def create_partition_table(self, name, layout, os_family=None):
        """
        Creates partition table with navigation
        """
        name = name or generate_string("alpha", 8)
        layout = layout or read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = os_family or "Red Hat"
        self.navigator.go_to_partition_tables()
        self.partitiontable.create(name, layout, os_family)
        self.assertIsNotNone(self.partitiontable.search(name))

    def test_create_partition_table(self):
        """
        @Feature: Partition table - Positive Create
        @Test: Create a new partition table
        @Assert: Partition table is created
        """

        name = generate_string("alpha", 8)
        layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_partitiontable(session, name=name, layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.search(name))

    def test_remove_partition_table(self):
        """
        @Feature: Partition table - Positive Delete
        @Test: Delete a partition table
        @Assert: Partition table is deleted
        """

        name = generate_string("alpha", 6)
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

    def test_update_partition_table(self):
        """
        @Feature: Partition table - Positive Update
        @Test: Update partition table with its name, layout and OS family
        @Assert: Partition table is updated
        """

        name = generate_string("alpha", 6)
        new_name = generate_string("alpha", 4)
        layout = "test layout"
        new_layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = "Debian"
        new_os_family = "Red Hat"
        with Session(self.browser) as session:
            make_partitiontable(session, name=name, layout=layout,
                                os_family=os_family)
            self.assertIsNotNone(self.partitiontable.search(name))
            self.partitiontable.update(name, new_name, new_layout,
                                       new_os_family)
            self.assertIsNotNone(self.partitiontable.search(new_name))
