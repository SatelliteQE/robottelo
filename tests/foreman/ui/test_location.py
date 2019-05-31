# -*- encoding: utf-8 -*-
"""Test class for Locations UI

:Requirement: Location

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import (
    tier1,
    upgrade,
)
from robottelo.constants import (
    DEFAULT_ORG,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_loc
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_org_loc_data():
    """Returns a list of valid org/location data"""
    return [
        {'org_name': gen_string('alpha', 242),
         'loc_name': gen_string('alpha', 242)},
        {'org_name': gen_string('numeric', 242),
         'loc_name': gen_string('numeric', 242)},
        {'org_name': gen_string('alphanumeric', 242),
         'loc_name': gen_string('alphanumeric', 242)},
        {'org_name': gen_string('utf8', 80),
         'loc_name': gen_string('utf8', 80)},
        {'org_name': gen_string('latin1', 242),
         'loc_name': gen_string('latin1', 242)},
        {'org_name': gen_string('html', 217),
         'loc_name': gen_string('html', 217)}
    ]


@filtered_datapoint
def valid_env_names():
    """Returns a list of valid environment names"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    ]


class LocationTestCase(UITestCase):
    """Implements Location tests in UI"""
    location = None

    @classmethod
    def setUpClass(cls):
        """Set up an organization for tests."""
        super(LocationTestCase, cls).setUpClass()
        cls.org_ = entities.Organization().search(query={
            'search': 'name="{0}"'.format(DEFAULT_ORG)
        })[0]

    # Auto Search

    @tier1
    def test_positive_auto_search(self):
        """Can auto-complete search for location by partial name

        :id: 6aaf104b-481a-4dd9-8639-8ddb1e4d6828

        :expectedresults: Created location can be auto search by its partial
            name

        :CaseImportance: Critical
        """
        loc_name = gen_string('alpha')
        with Session(self) as session:
            page = session.nav.go_to_loc
            make_loc(session, name=loc_name)
            auto_search = self.location.auto_complete_search(
                page,
                locators['location.select_name'],
                loc_name[:3],
                loc_name,
                search_key='name'
            )
            self.assertIsNotNone(auto_search)

    # Positive Create

    @tier1
    def test_positive_create_with_name(self):
        """Create Location with valid name only

        :id: 92b23082-09e4-49e1-92e1-d6d89d5180ac

        :expectedresults: Location is created, label is auto-generated

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for loc_name in generate_strings_list():
                with self.subTest(loc_name):
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))

    @tier1
    def test_negative_create_with_invalid_names(self):
        """Create location with invalid name

        :id: 85f05458-b86c-4d94-a412-ea03412c4588

        :expectedresults: location is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for loc_name in invalid_values_list(interface='ui'):
                with self.subTest(loc_name):
                    make_loc(session, name=loc_name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @tier1
    def test_negative_create_with_same_name(self):
        """Create location with valid values, then create a new one with same
        values.

        :id: 33983f00-406b-4289-b9e2-ffe6901bf99d

        :expectedresults: location is not created

        :CaseImportance: Critical
        """
        loc_name = gen_string('utf8')
        with Session(self) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    # Positive Update

    @tier1
    def test_positive_update_name(self):
        """Create Location with valid values then update its name

        :id: 79d8dbbb-9b7f-4482-a0f5-4fe72713d575

        :expectedresults: Location name is updated

        :CaseImportance: Critical
        """
        loc_name = gen_string('alpha')
        with Session(self) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.location.update(loc_name, new_name=new_name)
                    self.assertIsNotNone(self.location.search(new_name))
                    loc_name = new_name  # for next iteration

    # Negative Update

    @tier1
    def test_negative_update_with_too_long_name(self):
        """Create Location with valid values then fail to update
        its name

        :id: 57fed455-47f0-4b7c-a58e-3d8f6d761da9

        :expectedresults: Location name is not updated

        :CaseImportance: Critical
        """
        loc_name = gen_string('alphanumeric')
        with Session(self) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            new_name = gen_string('alpha', 247)
            self.location.update(loc_name, new_name=new_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create location with valid values then delete it.

        :id: b7664152-9398-499c-b165-3107f4350ba4

        :expectedresults: Location is deleted

        :CaseImportance: Critical
        """
        with Session(self):
            for loc_name in generate_strings_list():
                with self.subTest(loc_name):
                    entities.Location(name=loc_name).create()
                    self.location.delete(loc_name, dropdown_present=True)

    @tier1
    def test_positive_check_all_values_hostgroup(self):
        """check whether host group has the 'All values' checked.

        :id: ca2f2522-ba34-4d20-87f4-7777ec9a1282

        :expectedresults: host group 'All values' checkbox is checked.

        :CaseImportance: Critical
        """
        loc_name = gen_string('alpha')
        with Session(self) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            selected = self.location.check_all_values(
                session.nav.go_to_loc,
                loc_name,
                locators['location.select_name'],
                tab_locators['context.tab_hostgrps'],
                context='location',
            )
            self.assertIsNotNone(selected)

    @tier1
    def test_positive_check_all_values_template(self):
        """check whether config template has the 'All values' checked.

        :id: 358cf1c0-4187-4b5a-b900-5971e708b83f

        :expectedresults: configtemplate 'All values' checkbox is checked.

        :CaseImportance: Critical
        """
        loc_name = gen_string('alpha')
        with Session(self) as session:
            page = session.nav.go_to_loc
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            selected = self.location.check_all_values(
                page, loc_name, locators['location.select_name'],
                tab_locators['context.tab_template'], context='location')
            self.assertIsNotNone(selected)
