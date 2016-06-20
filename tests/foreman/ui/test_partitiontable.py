# -*- encoding: utf-8 -*-
"""Test class for Partition Table UI

@Requirement: Partitiontable

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from fauxfactory import gen_string
from robottelo.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.datafactory import (
    datacheck,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_only_on,
    skip_if_bug_open,
    tier1,
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_partitiontable
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session

PARTITION_SCRIPT_DATA_FILE = get_data_file(PARTITION_SCRIPT_DATA_FILE)


@datacheck
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


@datacheck
def valid_partition_table_update_names():
    """Returns a list of valid partition table names for update tests"""
    return [
        {u'new_name': gen_string('alpha')},
        {u'new_name': gen_string('html'), 'bugzilla': 1225857},
        {u'new_name': gen_string('utf8')},
        {u'new_name': gen_string('alphanumeric')},
    ]


class PartitionTableTestCase(UITestCase):
    """Implements the partition table tests from UI"""

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1229384)
    @tier1
    def test_positive_create_with_one_character_name(self):
        """Create a Partition table with 1 character in name

        @id: 2b8ee84f-34d4-464f-8fcb-4dd9647e43f0

        @Assert: Partition table is created

        @BZ: 1229384
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=1):
                with self.subTest(name):
                    make_partitiontable(
                        session,
                        name=name,
                        template_path=PARTITION_SCRIPT_DATA_FILE,
                        os_family='Red Hat'
                    )
                    self.assertIsNotNone(self.partitiontable.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create a new partition table

        @id: 2dd8e34d-5a39-49d0-9bde-dd1cdfddb2ad

        @Assert: Partition table is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=10):
                with self.subTest(name):
                    make_partitiontable(
                        session,
                        name=name,
                        template_path=PARTITION_SCRIPT_DATA_FILE,
                        os_family='Red Hat',
                    )
                    self.assertIsNotNone(self.partitiontable.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create partition table with invalid names

        @id: 225f1bb9-d5b2-4863-b89b-416f7cf5a7be

        @Assert: Partition table is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_partitiontable(
                        session,
                        name=name,
                        template_path=PARTITION_SCRIPT_DATA_FILE,
                        os_family='Red Hat',
                    )
                    self.assertIsNotNone(
                        self.partitiontable.wait_until_element(
                            common_locators['name_haserror'])
                    )

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Create a new partition table with same name

        @id: 3462ff33-1645-41c1-8fbd-513c7e4a18ed

        @Assert: Partition table is not created
        """
        name = gen_string('utf8')
        os_family = 'Red Hat'
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
                os_family=os_family,
            )
            self.assertIsNotNone(self.partitiontable.search(name))
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
                os_family=os_family,
            )
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators['name_haserror']))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_empty_layout(self):
        """Create a new partition table with empty layout

        @id: 427bce9b-c38e-4d78-943f-3cc7f422ebcd

        @Assert: Partition table is not created
        """
        name = gen_string('utf8')
        with Session(self.browser) as session:
            make_partitiontable(
                session, name=name, template_path='', os_family='Red Hat')
            self.assertIsNotNone(self.partitiontable.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.partitiontable.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete a partition table

        @id: 405ed98a-4207-4bf8-899e-dcea7791850e

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
                        session,
                        name=name,
                        template_path=PARTITION_SCRIPT_DATA_FILE,
                        os_family='Red Hat',
                    )
                    self.partitiontable.delete(name)

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Update partition table with its name, layout and OS family

        @id: 63203508-7c73-4ce0-853e-64564167bec3

        @Assert: Partition table is updated
        """
        name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
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
                            old_name=name,
                            new_name=test_data['new_name'],
                            new_template_path=PARTITION_SCRIPT_DATA_FILE,
                            new_os_family='Red Hat',
                        )
                        self.assertIsNotNone(self.partitiontable.search(
                            test_data['new_name']))
                        name = test_data['new_name']  # for next iteration
