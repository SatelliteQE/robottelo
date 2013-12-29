# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Partition Table UI
"""

from robottelo.ui.locators import locators
from robottelo.common.helpers import generate_name
from tests.ui.baseui import BaseUI
from urllib2 import urlopen

PART_SCRIPT_URL = 'https://gist.github.com/sghai/7822090/raw'


class PartitionTable(BaseUI):
    "Implements the partition table tests from UI"

    def test_create_partition_table(self):
        "Create new partition table"
        name = generate_name(6)
        layout = urlopen(PART_SCRIPT_URL).read()
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_partition_tables()
        self.partitiontable.create(name, layout, os_family)
        self.assertIsNotNone(self.partitiontable.search
                            (name, locators['ptable.ptable_name']))

    def test_remove_partition_table(self):
        "Delete Partition table"
        name = generate_name(6)
        layout = "test layout"
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_partition_tables()
        self.partitiontable.create(name, layout, os_family)
        self.partitiontable.remove(name, really=True)
        self.assertTrue(self.partitiontable.wait_until_element
                        (locators["notif.success"]))

    def test_update_partition_table(self):
        "Creates new partition table and update its name, layout and OS family"
        name = generate_name(6)
        new_name = generate_name(4)
        layout = "test layout"
        new_layout = urlopen(PART_SCRIPT_URL).read()
        os_family = "Debian"
        new_os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_partition_tables()
        self.partitiontable.create(name, layout, os_family)
        self.partitiontable.update(name, new_name, new_layout, new_os_family)
        self.assertIsNotNone(self, self.partitiontable.search
                             (new_name, locators['ptable.ptable_name']))
