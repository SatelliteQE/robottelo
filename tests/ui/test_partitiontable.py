# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Partition Table UI
"""

from robottelo.common.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.common.helpers import generate_name, read_data_file
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


class PartitionTable(BaseUI):
    """
    Implements the partition table tests from UI
    """
    def create_partition_table(self, name, layout, os_family=None):
        """
        Creates partition table with navigation
        """
        name = name or generate_name(6)
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

        name = generate_name(6)
        layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_partition_table(name, layout, os_family)

    def test_remove_partition_table(self):
        """
        @Feature: Partition table - Positive Delete
        @Test: Delete a partition table
        @Assert: Partition table is deleted
        """

        name = generate_name(6)
        layout = "test layout"
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_partition_table(name, layout, os_family)
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

        name = generate_name(6)
        new_name = generate_name(4)
        layout = "test layout"
        new_layout = read_data_file(PARTITION_SCRIPT_DATA_FILE)
        os_family = "Debian"
        new_os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_partition_table(name, layout, os_family)
        self.partitiontable.update(name, new_name, new_layout, new_os_family)
        self.assertIsNotNone(self, self.partitiontable.search(new_name))
