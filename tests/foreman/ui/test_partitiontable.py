# -*- encoding: utf-8 -*-
"""Test class for Partition Table UI

:Requirement: Partitiontable

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from robottelo.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.datafactory import (
    generate_strings_list,
    invalid_names_list,
    invalid_values_list,
)
from robottelo.decorators import (
    tier1,
    upgrade
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_partitiontable
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session

PARTITION_SCRIPT_DATA_FILE = get_data_file(PARTITION_SCRIPT_DATA_FILE)


class PartitionTableTestCase(UITestCase):
    """Implements the partition table tests from UI"""

    @tier1
    def test_positive_create_with_one_character_name(self):
        """Create a Partition table with 1 character in name

        :id: 2b8ee84f-34d4-464f-8fcb-4dd9647e43f0

        :expectedresults: Partition table is created

        :BZ: 1229384

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list(length=1):
                with self.subTest(name):
                    make_partitiontable(
                        session,
                        name=name,
                        template_path=PARTITION_SCRIPT_DATA_FILE,
                        os_family='Red Hat'
                    )
                    self.assertIsNotNone(self.partitiontable.search(name))

    @tier1
    def test_positive_create_with_name(self):
        """Create a new partition table

        :id: 2dd8e34d-5a39-49d0-9bde-dd1cdfddb2ad

        :customerscenario: true

        :expectedresults: Partition table is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_partitiontable(
                        session,
                        name=name,
                        template_path=PARTITION_SCRIPT_DATA_FILE,
                        os_family='Red Hat',
                    )
                    self.assertIsNotNone(self.partitiontable.search(name))

    @tier1
    def test_positive_create_with_snippet(self):
        """Create a new partition table with enabled snippet option

        :id: 37bb748a-63d1-4d88-954f-71634168072a

        :expectedresults: Partition table is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
                snippet=True,
            )
            self.assertIsNotNone(self.partitiontable.search(name))

    @tier1
    def test_positive_create_with_audit_comment(self):
        """Create a new partition table with some text inputted into audit
        comment section

        :id: f17e16ff-b07f-44ec-a824-b9af460c35aa

        :expectedresults: Partition table is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            for comment_text in generate_strings_list():
                with self.subTest(comment_text):
                    make_partitiontable(
                        session,
                        name=name,
                        template_path=PARTITION_SCRIPT_DATA_FILE,
                        audit_comment=comment_text,
                    )
                    self.assertIsNotNone(self.partitiontable.search(name))

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create partition table with invalid names

        :id: 225f1bb9-d5b2-4863-b89b-416f7cf5a7be

        :expectedresults: Partition table is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

    @tier1
    def test_negative_create_with_same_name(self):
        """Create a new partition table with same name

        :id: 3462ff33-1645-41c1-8fbd-513c7e4a18ed

        :expectedresults: Partition table is not created

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        os_family = 'Red Hat'
        with Session(self) as session:
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
            self.assertIsNotNone(self.partitiontable.wait_until_element(
                common_locators['name_haserror']))

    @tier1
    def test_negative_create_with_empty_layout(self):
        """Create a new partition table with empty layout

        :id: 427bce9b-c38e-4d78-943f-3cc7f422ebcd

        :expectedresults: Partition table is not created

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        with Session(self) as session:
            make_partitiontable(
                session, name=name, template_path='', os_family='Red Hat')
            self.assertIsNotNone(self.partitiontable.wait_until_element(
                common_locators['haserror']))
            self.assertIsNone(self.partitiontable.search(name))

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete a partition table

        :id: 405ed98a-4207-4bf8-899e-dcea7791850e

        :customerscenario: true

        :expectedresults: Partition table is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_partitiontable(
                        session,
                        name=name,
                        template_path=PARTITION_SCRIPT_DATA_FILE,
                        os_family='Red Hat',
                    )
                    self.partitiontable.delete(name, dropdown_present=True)

    @tier1
    def test_positive_update(self):
        """Update partition table with its name, layout and OS family

        :id: 63203508-7c73-4ce0-853e-64564167bec3

        :customerscenario: true

        :expectedresults: Partition table is updated

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        with Session(self) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
                os_family='Debian',
            )
            self.assertIsNotNone(self.partitiontable.search(name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.partitiontable.update(
                        old_name=name,
                        new_name=new_name,
                        new_template_path=PARTITION_SCRIPT_DATA_FILE,
                        new_os_family='Red Hat',
                    )
                    self.assertIsNotNone(self.partitiontable.search(new_name))
                    name = new_name  # for next iteration

    @tier1
    def test_negative_update_name(self):
        """Update invalid name in partition table

        :id: 704e8336-e14a-4d1a-b9db-2f81c8af6ecc

        :expectedresults: Partition table is not updated.  Appropriate error
            shown.

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        with Session(self) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
            )
            self.assertIsNotNone(self.partitiontable.search(name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.partitiontable.update(name, new_name=new_name)
                    self.assertIsNotNone(
                        self.partitiontable.wait_until_element(
                            common_locators['name_haserror'])
                    )
                    self.assertIsNone(self.partitiontable.search(new_name))
