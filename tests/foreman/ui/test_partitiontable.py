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
from nailgun import entities
from robottelo.constants import PARTITION_SCRIPT_DATA_FILE
from robottelo.datafactory import (
    generate_strings_list,
    invalid_names_list,
    invalid_values_list,
)
from robottelo.decorators import (
    run_only_on,
    tier1,
    tier2,
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_partitiontable
from robottelo.ui.locators import common_locators, tab_locators
from robottelo.ui.session import Session

PARTITION_SCRIPT_DATA_FILE = get_data_file(PARTITION_SCRIPT_DATA_FILE)


class PartitionTableTestCase(UITestCase):
    """Implements the partition table tests from UI"""

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_one_character_name(self):
        """Create a Partition table with 1 character in name

        @id: 2b8ee84f-34d4-464f-8fcb-4dd9647e43f0

        @expectedresults: Partition table is created

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

        @expectedresults: Partition table is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
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
    def test_positive_create_with_snippet(self):
        """Create a new partition table with enabled snippet option

        @id: 37bb748a-63d1-4d88-954f-71634168072a

        @expectedresults: Partition table is created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
                snippet=True,
            )
            self.assertIsNotNone(self.partitiontable.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_audit_comment(self):
        """Create a new partition table with some text inputted into audit
        comment section

        @id: f17e16ff-b07f-44ec-a824-b9af460c35aa

        @expectedresults: Partition table is created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            for comment_text in generate_strings_list():
                with self.subTest(comment_text):
                    make_partitiontable(
                        session,
                        name=name,
                        template_path=PARTITION_SCRIPT_DATA_FILE,
                        audit_comment=comment_text,
                    )
                    self.assertIsNotNone(self.partitiontable.search(name))

    @run_only_on('sat')
    @tier2
    def test_positive_create_default_for_organization(self):
        """Create new partition table with enabled 'default' option. Check
        that newly created organization has that partition table assigned to it

        @id: 91c64054-cd0c-4d4b-888b-17d42e298527

        @expectedresults: New partition table is created and is present in the
        list of selected partition tables for any new organization

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
                default=True,
            )
            self.assertIsNotNone(self.partitiontable.search(name))
            entities.Organization(name=org_name).create()
            session.nav.click(self.org.search(org_name))
            session.nav.click(tab_locators['context.tab_ptable'])
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(
                session.nav.wait_until_element((strategy1, value1 % name))
            )

    @run_only_on('sat')
    @tier2
    def test_positive_create_non_default_for_organization(self):
        """Create new partition table with disabled 'default' option. Check
        that newly created organization does not contain that partition table.

        @id: 69e6df0f-af1f-4aa2-8987-3e3b9a16be37

        @expectedresults: New partition table is created and is not present in
        the list of selected partition tables for any new organization

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        strategy1, value1 = common_locators['entity_select']
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
                default=False,
            )
            self.assertIsNotNone(self.partitiontable.search(name))
            entities.Organization(name=org_name).create()
            session.nav.click(self.org.search(org_name))
            session.nav.click(tab_locators['context.tab_ptable'])
            # Item is listed in 'All Items' list and not Selected Items' list.
            self.assertIsNotNone(
                session.nav.wait_until_element((strategy1, value1 % name))
            )

    @run_only_on('sat')
    @tier2
    def test_positive_create_default_for_location(self):
        """Create new partition table with enabled 'default' option. Check
        that newly created location has that partition table assigned to it

        @id: 8dfaae7c-2f33-4f0d-93f6-1f78ea4d750d

        @expectedresults: New partition table is created and is present in the
        list of selected partition tables for any new location

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        loc_name = gen_string('alpha')
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
                default=True,
            )
            self.assertIsNotNone(self.partitiontable.search(name))
            entities.Location(name=loc_name).create()
            session.nav.click(self.location.search(loc_name))
            session.nav.click(tab_locators['context.tab_ptable'])
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(
                session.nav.wait_until_element((strategy1, value1 % name))
            )

    @run_only_on('sat')
    @tier2
    def test_positive_create_non_default_for_location(self):
        """Create new partition table with disabled 'default' option. Check
        that newly created location does not contain that partition table.

        @id: 094d4583-763b-48d4-a89a-23b90741fd6f

        @expectedresults: New partition table is created and is not present in
        the list of selected partition tables for any new location

        @CaseLevel: Integration
        """
        name = gen_string('alpha')
        org_name = gen_string('alpha')
        strategy1, value1 = common_locators['entity_select']
        with Session(self.browser) as session:
            make_partitiontable(
                session,
                name=name,
                template_path=PARTITION_SCRIPT_DATA_FILE,
                default=False,
            )
            self.assertIsNotNone(self.partitiontable.search(name))
            entities.Location(name=org_name).create()
            session.nav.click(self.location.search(org_name))
            session.nav.click(tab_locators['context.tab_ptable'])
            # Item is listed in 'All Items' list and not Selected Items' list.
            self.assertIsNotNone(
                session.nav.wait_until_element((strategy1, value1 % name))
            )

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create partition table with invalid names

        @id: 225f1bb9-d5b2-4863-b89b-416f7cf5a7be

        @expectedresults: Partition table is not created
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

        @expectedresults: Partition table is not created
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

        @expectedresults: Partition table is not created
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

        @expectedresults: Partition table is deleted
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
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

        @expectedresults: Partition table is updated
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

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Update invalid name in partition table

        @id: 704e8336-e14a-4d1a-b9db-2f81c8af6ecc

        @expectedresults: Partition table is not updated.  Appropriate error
        shown.
        """
        name = gen_string('alphanumeric')
        with Session(self.browser) as session:
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
