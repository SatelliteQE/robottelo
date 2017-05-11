# -*- encoding: utf-8 -*-
"""Test class for Domain UI

@Requirement: Domain

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
from fauxfactory import gen_string
from robottelo.constants import DOMAIN
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import (
    affected_by_bz,
    run_only_on,
    skip_if_bug_open,
    tier1,
    tier2,
)
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_domain
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_long_domain_names():
    """Returns a list of valid long domain names

    The length of chars is in accordance with DOMAIN global variable.

    """
    return[
        gen_string('alphanumeric', 243),
        gen_string('alpha', 243),
        gen_string('numeric', 243),
        gen_string('latin1', 243),
        gen_string('utf8', 243),
    ]


@filtered_datapoint
def valid_domain_update_data():
    """Returns a list of valid test data for domain update tests"""
    return [
        {'name': gen_string('alpha', 10)},
        {'name': gen_string('numeric', 10)},
        {'name': gen_string('alphanumeric', 10)},
        {'name': gen_string('utf8', 10)},
        {'name': gen_string('latin1', 10)},
        {'name': gen_string('html', 10), 'bugzilla': 1220104}
    ]


class DomainTestCase(UITestCase):
    """Implements Domain tests in UI"""

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create a new domain

        @id: 142f90e3-a2a3-4f99-8f9b-11189f230bc5

        @expectedresults: Domain is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=4):
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    make_domain(
                        session, name=domain_name, description=description)
                    element = self.domain.search(description)
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_long_name(self):
        """Create a new domain

        @id: 0b856ad7-97a6-4632-8b84-1d8ee45bedc8

        @expectedresults: Domain is created
        """
        with Session(self.browser) as session:
            for name in valid_long_domain_names():
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    make_domain(
                        session, name=domain_name, description=description)
                    element = self.domain.search(description)
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete a domain

        @id: 07c1cc34-4569-4f04-9c4a-2842821a6977

        @expectedresults: Domain is deleted
        """
        domain_name = description = DOMAIN % gen_string('alpha')
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            self.domain.delete(domain_name)

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Update a domain with name and description

        @id: 25ff4a1d-3ca1-4153-be45-4fe1e63f3f16

        @expectedresults: Domain is updated
        """
        domain_name = description = DOMAIN % gen_string('alpha', 10)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            self.assertIsNotNone(self.domain.search(domain_name))
            for testdata in valid_domain_update_data():
                with self.subTest(testdata):
                    bug_id = testdata.pop('bugzilla', None)
                    if bug_id is not None and affected_by_bz(bug_id):
                        self.skipTest('Bugzilla bug {0} is open.'.format(
                            bug_id))
                    new_name = new_description = DOMAIN % testdata['name']
                    self.domain.update(domain_name, new_name, new_description)
                    self.assertIsNotNone(self.domain.search(new_name))
                    domain_name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create domain and use whitespace, blank, tab symbol or
        too long string of different types as its name value

        @id: 5a8ba1a8-2da8-48e1-8b2a-96d91161bf94

        @expectedresults: Domain is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_domain(session, name=name, description=name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @run_only_on('sat')
    @tier2
    def test_positive_set_parameter(self):
        """Set parameter name and value for domain

        @id: a05615de-c9e5-4784-995c-b2fe2a1dfd3e

        @expectedresults: Domain is updated

        @CaseLevel: Integration
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=4):
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    param_name = gen_string('alpha', 4)
                    param_value = gen_string('alpha', 3)
                    make_domain(
                        session, name=domain_name, description=description)
                    self.assertIsNotNone(self.domain.search(domain_name))
                    try:
                        self.domain.set_domain_parameter(
                            description, param_name, param_value)
                    except UIError as err:
                        self.fail(err)

    @run_only_on('sat')
    @tier2
    def test_positive_set_parameter_long(self):
        """Set a parameter in a domain with 255 chars in name and value.

        @id: b346ae66-1720-46af-b0da-460c52ce9476

        @expectedresults: Domain parameter is created.

        @CaseLevel: Integration
        """
        name = gen_string('alpha', 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string('alpha', 255)
        param_value = gen_string('alpha', 255)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
            except UIError as err:
                self.fail(err)

    @run_only_on('sat')
    @tier2
    def test_positive_set_parameter_blank(self):
        """Set a parameter in a domain with blank value.

        @id: b5a67709-57ad-4043-8e72-190ec31b8217

        @expectedresults: Domain parameter is created with blank value.

        @CaseLevel: Integration
        """
        name = gen_string('alpha', 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string('alpha', 4)
        param_value = ''
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
            except UIError as err:
                self.fail(err)

    @run_only_on('sat')
    @tier2
    def test_negative_set_parameter(self):
        """Set a parameter in a domain with 256 chars in name and value.

        @id: 1c647d66-6a3f-4d88-8e6b-60f2fc7fd603

        @expectedresults: Domain parameter is not updated.

        @CaseLevel: Integration
        """
        name = gen_string('alpha', 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string('alpha', 256)
        param_value = gen_string('alpha', 256)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
            except UIError as err:
                self.fail(err)
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators['common_param_error']))

    @skip_if_bug_open('bugzilla', 1123360)
    @run_only_on('sat')
    @tier2
    def test_negative_set_parameter_same(self):
        """Again set the same parameter for domain with name and value.

        @id: 6266f12e-cf94-4564-ba26-b467ced2737f

        @expectedresults: Domain parameter is not updated.

        @BZ: 1123360

        @CaseLevel: Integration
        """
        name = gen_string('alpha', 4)
        domain_name = description = DOMAIN % name
        param_name = gen_string('alpha', 8)
        param_value = gen_string('alpha', 8)
        with Session(self.browser) as session:
            make_domain(session, name=domain_name, description=description)
            element = self.domain.search(description)
            self.assertIsNotNone(element)
            try:
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
                self.domain.set_domain_parameter(
                    description, param_name, param_value)
            except UIError as err:
                self.fail(err)
            self.assertIsNotNone(session.nav.wait_until_element(
                common_locators['common_param_error']))

    @run_only_on('sat')
    @tier2
    def test_positive_remove_parameter(self):
        """Remove a selected domain parameter

        @id: 8f7f8501-cf39-418f-a412-1a4b53698bc3

        @expectedresults: Domain parameter is removed

        @CaseLevel: Integration
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=4):
                with self.subTest(name):
                    domain_name = description = DOMAIN % name
                    param_name = gen_string('alpha', 3)
                    param_value = gen_string('alpha', 3)
                    make_domain(
                        session, name=domain_name, description=description)
                    element = self.domain.search(domain_name)
                    self.assertIsNotNone(element)
                    try:
                        self.domain.set_domain_parameter(
                            description, param_name, param_value)
                        self.domain.remove_domain_parameter(
                            description, param_name)
                    except UIError as err:
                        self.fail(err)
