# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery Rules

:Requirement: Discoveryrule

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_integer, gen_ipaddr, gen_string
from nailgun import entities
from robottelo.datafactory import (
    generate_strings_list,
    filtered_datapoint,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    tier1,
    stubbed,
    upgrade,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_discoveryrule
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_search_queries():
    """Generates a list of all the input strings, (excluding html)"""
    return [
        'cpu_count ^ 10',
        'disk_count > 5',
        'disks_size <= {0}'.format(gen_string('numeric', 8)),
        'ip = {0}'.format(gen_ipaddr()),
        'model = KVM',
        u'organization ~ {0}'.format(entities.Organization().create().name),
        u'subnet = {0}'.format(entities.Subnet().create().name),
    ]


class DiscoveryRuleTestCase(UITestCase):
    """Implements Foreman discovery Rules in UI."""

    @classmethod
    def set_session_org(cls):
        cls.session_org = entities.Organization().create()
        cls.session_loc = entities.Location(
            organization=[cls.session_org]
        ).create()

    @classmethod
    def setUpClass(cls):
        """Display all the discovery rules on the same page"""
        super(DiscoveryRuleTestCase, cls).setUpClass()
        cls.per_page = entities.Setting().search(
            query={'search': 'name="entries_per_page"'})[0]
        cls.saved_per_page = str(cls.per_page.value)
        cls.per_page.value = '100000'
        cls.per_page.update({'value'})
        cls.host_group = entities.HostGroup(
            organization=[cls.session_org],
            location=[cls.session_loc],
        ).create()

    @classmethod
    def tearDownClass(cls):
        """Restore previous 'entries_per_page' value"""
        cls.per_page.value = cls.saved_per_page
        cls.per_page.update({'value'})

        super(DiscoveryRuleTestCase, cls).tearDownClass()

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create Discovery Rule using different names

        :id: afdf7000-4bd0-41ec-9773-96ff68e27b8d

        :expectedresults: Rule should be successfully created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_discoveryrule(
                        session,
                        name=name,
                        hostgroup=self.host_group.name,
                        locations=[self.session_loc.name],
                    )
                    self.assertIsNotNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_search(self):
        """Create Discovery Rule using different search queries

        :id: 973ff6e5-572e-401c-bc8c-d614a583e883

        :expectedresults: Rule should be successfully created and has expected
            search field value

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for query in valid_search_queries():
                with self.subTest(query):
                    name = gen_string('alpha')
                    make_discoveryrule(
                        session,
                        name=name,
                        hostgroup=self.host_group.name,
                        search_rule=query,
                        locations=[self.session_loc.name],
                    )
                    self.assertIsNotNone(self.discoveryrules.search(name))
                    self.assertEqual(
                        self.discoveryrules.get_attribute_value(
                            name, 'search'),
                        query
                    )

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_hostname(self):
        """Create Discovery Rule using valid hostname value

        :id: e6742ca5-1d41-4ba3-8f2c-2169db92485b

        :expectedresults: Rule should be successfully created and has expected
            hostname field value

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        hostname = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                locations=[self.session_loc.name],
                hostgroup=self.host_group.name,
                hostname=hostname,
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.assertEqual(
                self.discoveryrules.get_attribute_value(name, 'hostname'),
                hostname
            )

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_hosts_limit(self):
        """Create Discovery Rule providing any number from range 1..100 for
        hosts limit field

        :id: 64b90586-c1a9-4be4-8c44-4fa19ca998f8

        :expectedresults: Rule should be successfully created and has expected
            hosts limit field value

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        limit = str(gen_integer(1, 100))
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                host_limit=limit,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.assertEqual(
                self.discoveryrules.get_attribute_value(name, 'host_limit'),
                limit
            )

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_priority(self):
        """Create Discovery Rule providing any number from range 1..100 for
        priority field

        :id: de847288-257a-4f0e-9cb6-9a0dd0877d23

        :expectedresults: Rule should be successfully created and has expected
            priority field value

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        priority = str(gen_integer(1, 100))
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                priority=priority,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.assertEqual(
                self.discoveryrules.get_attribute_value(name, 'priority'),
                priority
            )

    @run_only_on('sat')
    @tier1
    def test_positive_create_disabled(self):
        """Create Discovery Rule in disabled state

        :id: 0b98d467-aabf-4efe-890f-50d6edcd99ff

        :expectedresults: Disabled rule should be successfully created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                enabled=False,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.assertEqual(
                self.discoveryrules.get_attribute_value(
                    name, 'enabled', element_type='checkbox'),
                False
            )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1378486)
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Discovery Rule with invalid names

        :id: 79d950dc-4ca1-407e-84ca-9092d1cba978

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_discoveryrule(
                        session, name=name, hostgroup=self.host_group.name)
                    self.assertIsNotNone(
                        self.discoveryrules.wait_until_element(
                            common_locators['name_haserror'])
                    )
                    self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_hostname(self):
        """Create Discovery Rule with invalid hostname

        :id: a322c8ce-4f05-401a-88cb-a3d30b4ac446

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                hostname=gen_string('numeric'),
            )
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['haserror']
            ))
            self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_limit(self):
        """Create Discovery Rule with invalid host limit

        :id: 743d29f4-a901-400c-ad98-a3b8942f02b5

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            for limit in '-1', gen_string('alpha'):
                with self.subTest(limit):
                    make_discoveryrule(
                        session,
                        name=name,
                        host_limit=limit,
                        hostgroup=self.host_group.name,
                    )
                    msg = self.discoveryrules.find_element(
                        locators['discoveryrules.host_limit']
                    ).get_attribute("validationMessage")
                    if limit == '-1':
                        self.assertEqual(
                            msg,
                            u'Please select a value that is no less than 0.'
                        )
                    else:
                        self.assertEqual(msg, u'Please enter a number.')
                    self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1308831)
    @tier1
    def test_negative_create_with_too_long_limit(self):
        """Create Discovery Rule with too long host limit value

        :id: 450b49d9-1058-4186-9b23-15cc615e5bd6

        :expectedresults: Validation error should be raised and rule should not
            be created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                host_limit=gen_string('numeric', 50),
                hostgroup=self.host_group.name,
            )
            msg = self.discoveryrules.find_element(
                locators['discoveryrules.host_limit']
            ).get_attribute("validationMessage")
            self.assertEqual(
                msg, u'Please select a value that is no more than 2147483647.')
            self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Create Discovery Rule with name that already exists

        :id: 5a914e76-de01-406d-9860-0e4e1521b074

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['name_haserror']
            ))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_priority(self):
        """Create Discovery Rule with invalid priority

        :id: f8829cce-86c0-452c-b866-d5645174e9e1

        :expectedresults: Error should be raised and rule should not be created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                priority=gen_string('alpha'),
            )
            msg = self.discoveryrules.find_element(
                locators['discoveryrules.priority']
            ).get_attribute("validationMessage")
            self.assertEqual(msg, u'Please enter a number.')
            self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete existing Discovery Rule

        :id: fc5b714c-e5bc-4b0f-bc94-88e080318704

        :expectedresults: Rule should be successfully deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_discoveryrule(
                        session,
                        name=name,
                        hostgroup=self.host_group.name,
                        locations=[self.session_loc.name],
                    )
                    self.assertIsNotNone(self.discoveryrules.search(name))
                    self.discoveryrules.delete(name, dropdown_present=True)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update discovery rule name

        :id: 16a79449-7200-492e-9ddb-65fc034e510d

        :expectedresults: Rule name is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.discoveryrules.update(name=name, new_name=new_name)
                    self.assertIsNotNone(self.discoveryrules.search(new_name))
                    name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_positive_update_query(self):
        """Update discovery rule search query

        :id: bcf85a4c-0b27-47a5-8d5d-7ede0f6eea41

        :expectedresults: Rule search field is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            for new_query in valid_search_queries():
                with self.subTest(new_query):
                    self.discoveryrules.update(
                        name=name, search_rule=new_query)
                    self.assertEqual(
                        self.discoveryrules.get_attribute_value(
                            name, 'search'),
                        new_query
                    )

    @run_only_on('sat')
    @tier1
    def test_positive_update_hostgroup(self):
        """Update discovery rule host group

        :id: e10274e9-bf1b-42cd-a809-f19e707e7f4c

        :expectedresults: Rule host group is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_hostgroup_name = entities.HostGroup(
            organization=[self.session_org]).create().name
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.assertEqual(
                self.discoveryrules.get_attribute_value(
                    name, 'hostgroup', element_type='select'),
                self.host_group.name
            )
            self.discoveryrules.update(name=name, hostgroup=new_hostgroup_name)
            self.assertEqual(
                self.discoveryrules.get_attribute_value(
                    name, 'hostgroup', element_type='select'),
                new_hostgroup_name
            )

    @run_only_on('sat')
    @tier1
    def test_positive_update_hostname(self):
        """Update discovery rule hostname value

        :id: 753ff15b-da73-4fb3-87cd-14d504d8e882

        :expectedresults: Rule host name is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        hostname = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.discoveryrules.update(name=name, hostname=hostname)
            self.assertEqual(
                self.discoveryrules.get_attribute_value(name, 'hostname'),
                hostname
            )

    @run_only_on('sat')
    @tier1
    def test_positive_update_limit(self):
        """Update discovery rule limit value

        :id: 69d59c34-407b-47d0-a2b8-46decb95ef47

        :expectedresults: Rule host limit field is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        limit = str(gen_integer(1, 100))
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.discoveryrules.update(name=name, host_limit=limit)
            self.assertEqual(
                self.discoveryrules.get_attribute_value(name, 'host_limit'),
                limit
            )

    @run_only_on('sat')
    @tier1
    def test_positive_update_priority(self):
        """Update discovery rule priority value

        :id: be4de7a9-df8e-44ae-9910-7397341f6d07

        :expectedresults: Rule priority is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        priority = str(gen_integer(1, 100))
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.discoveryrules.update(name=name, priority=priority)
            self.assertEqual(
                self.discoveryrules.get_attribute_value(name, 'priority'),
                priority
            )

    @run_only_on('sat')
    @tier1
    def test_positive_update_disable_enable(self):
        """Update discovery rule enabled state. (Disabled->Enabled)

        :id: 60d619e4-a039-4f9e-a16c-b05f0598e8fa

        :expectedresults: Rule enabled checkbox is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
                enabled=False,
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.discoveryrules.update(name=name, enabled=True)
            self.assertEqual(
                self.discoveryrules.get_attribute_value(
                    name, 'enabled', element_type='checkbox'),
                True
            )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1378486)
    @tier1
    def test_negative_update_name(self):
        """Update discovery rule name using invalid names only

        :id: 65f32628-796a-4d7e-bf2c-c84c6b06f309

        :expectedresults: Rule name is not updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            for new_name in invalid_values_list(interface='ui'):
                with self.subTest(new_name):
                    self.discoveryrules.update(name=name, new_name=new_name)
                    self.assertIsNotNone(
                        self.discoveryrules.wait_until_element(
                            common_locators['name_haserror'])
                    )
                    self.assertIsNone(self.discoveryrules.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_negative_update_hostname(self):
        """Update discovery rule host name using number as a value

        :id: 18713425-22fe-4eaa-a515-8e08aa07e116

        :expectedresults: Rule host name is not updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        hostname = gen_string('alpha')
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                hostname=hostname,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.discoveryrules.update(
                name=name, hostname=gen_string('numeric'))
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['haserror']
            ))
            self.assertEqual(
                self.discoveryrules.get_attribute_value(name, 'hostname'),
                hostname
            )

    @run_only_on('sat')
    @tier1
    def test_negative_update_limit(self):
        """Update discovery rule host limit using invalid values

        :id: 7e8b7218-3c8a-4b03-b0df-484e0d793ceb

        :expectedresults: Rule host limit is not updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        limit = str(gen_integer(1, 100))
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                host_limit=limit,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            for new_limit in '-1', gen_string('alpha'):
                with self.subTest(new_limit):
                    self.discoveryrules.update(
                        name=name, host_limit=new_limit)
                    msg = self.discoveryrules.find_element(
                        locators['discoveryrules.host_limit']
                    ).get_attribute("validationMessage")
                    if new_limit == '-1':
                        self.assertEqual(
                            msg,
                            u'Please select a value that is no less than 0.'
                        )
                    else:
                        self.assertEqual(msg, u'Please enter a number.')
            self.assertEqual(
                self.discoveryrules.get_attribute_value(name, 'host_limit'),
                limit
            )

    @run_only_on('sat')
    @tier1
    def test_negative_update_priority(self):
        """Update discovery rule priority using invalid values

        :id: d44ad49c-5d95-442f-a1b3-cd82dd8ffabf

        :expectedresults: Rule priority is not updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        priority = str(gen_integer(1, 100))
        with Session(self) as session:
            make_discoveryrule(
                session,
                name=name,
                hostgroup=self.host_group.name,
                priority=priority,
                locations=[self.session_loc.name],
            )
            self.assertIsNotNone(self.discoveryrules.search(name))
            for new_priority in '-1', gen_string('alpha'):
                with self.subTest(new_priority):
                    self.discoveryrules.update(
                        name=name, priority=new_priority)
                    msg = self.discoveryrules.find_element(
                        locators['discoveryrules.priority']
                    ).get_attribute("validationMessage")
                    if new_priority == '-1':
                        self.assertEqual(
                            msg,
                            u'Please select a value that is no less than 0.'
                        )
                    else:
                        self.assertEqual(msg, u'Please enter a number.')
            self.assertEqual(
                self.discoveryrules.get_attribute_value(name, 'priority'),
                priority
            )

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_order_rules_by_priority_and_create_time(self):
        """Create rule with same priority and see their ordering should be based
        on create time.

        :id: 585c4bc2-6e34-4fdd-88fb-d788f9e0625b

        :expectedresults: The ordering of rules should be based on priority as
            well as create time.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """
