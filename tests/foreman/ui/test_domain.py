# -*- encoding: utf-8 -*-
"""Test class for Domain UI

:Requirement: Domain

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from robottelo.constants import DOMAIN
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import (
    bz_bug_is_open,
    tier1,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_domain
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_long_domain_names():
    """Returns a list of valid long domain names

    The length of chars is in accordance with DOMAIN global variable.
    """
    return [
        gen_string('alphanumeric', 243),
        gen_string('alpha', 243),
        gen_string('numeric', 243),
        gen_string('latin1', 243),
        gen_string('utf8', 243),
    ]


@filtered_datapoint
def valid_domain_update_data():
    """Returns a list of valid test data for domain update tests"""
    names = [
        {'name': gen_string('alpha')},
        {'name': gen_string('numeric')},
        {'name': gen_string('alphanumeric')},
        {'name': gen_string('utf8')},
        {'name': gen_string('latin1')}
    ]
    if not bz_bug_is_open(1220104):
        names.append({'name': gen_string('html')})
    return names


class DomainTestCase(UITestCase):
    """Implements Domain tests in UI"""

    @tier1
    def test_positive_create_with_name(self):
        """Create a new domain with different names

        :id: 142f90e3-a2a3-4f99-8f9b-11189f230bc5

        :expectedresults: Domain is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list(length=4):
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    make_domain(
                        session, name=domain_name, description=description)
                    self.assertIsNotNone(self.domain.search(description))

    @tier1
    def test_positive_create_with_long_name(self):
        """Create a new domain with long names

        :id: 0b856ad7-97a6-4632-8b84-1d8ee45bedc8

        :expectedresults: Domain is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_long_domain_names():
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    make_domain(
                        session, name=domain_name, description=description)
                    element = self.domain.search(description)
                    self.assertIsNotNone(element)

    @upgrade
    @tier1
    def test_positive_delete(self):
        """Delete a domain

        :id: 07c1cc34-4569-4f04-9c4a-2842821a6977

        :expectedresults: Domain is deleted

        :CaseImportance: Critical
        """
        domain_name = description = DOMAIN % gen_string('alpha')
        with Session(self) as session:
            make_domain(session, name=domain_name, description=description)
            self.domain.delete(domain_name)

    @tier1
    @upgrade
    def test_positive_update(self):
        """Update a domain with name and description

        :id: 25ff4a1d-3ca1-4153-be45-4fe1e63f3f16

        :expectedresults: Domain is updated

        :CaseImportance: Critical
        """
        domain_name = description = DOMAIN % gen_string('alpha')
        with Session(self) as session:
            make_domain(session, name=domain_name, description=description)
            self.assertIsNotNone(self.domain.search(domain_name))
            for testdata in valid_domain_update_data():
                with self.subTest(testdata):
                    new_name = new_description = DOMAIN % testdata['name']
                    self.domain.update(domain_name, new_name, new_description)
                    self.assertIsNotNone(self.domain.search(new_name))
                    domain_name = new_name  # for next iteration

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create domain and use whitespace, blank, tab symbol or
        too long string of different types as its name value

        :id: 5a8ba1a8-2da8-48e1-8b2a-96d91161bf94

        :expectedresults: Domain is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_domain(session, name=name, description=name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)
