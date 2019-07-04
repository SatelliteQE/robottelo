# -*- encoding: utf-8 -*-
"""Test class for Environment UI

:Requirement: Environment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities

from robottelo.datafactory import invalid_values_list, valid_environments_list
from robottelo.decorators import run_only_on, tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.factory import make_env
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class EnvironmentTestCase(UITestCase):
    """Implements environment tests in UI.

    Please note that, Environment will accept only alphanumeric chars as name.
    """

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create new environment

        :id: be8ee96a-29e4-4c64-9cae-78ab6aa483d7

        :expectedresults: Environment is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_environments_list():
                with self.subTest(name):
                    make_env(session, name=name)
                    self.assertIsNotNone(self.environment.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_org(self):
        """Create new environment with organization

        :id: 96d0b49c-2f01-4912-b93b-d2f9e614fe8a

        :expectedresults: Environment is created

        :CaseImportance: High
        """
        env_name = gen_string('alpha')
        org = entities.Organization().create()
        with Session(self) as session:
            make_env(session, name=env_name, organizations=[org.name])
            self.assertIsNotNone(self.environment.search(env_name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_loc(self):
        """Create new environment with location

        :id: ac3f4498-5cba-4fe6-a296-776f009fb28c

        :expectedresults: Environment is created

        :CaseImportance: High
        """
        env_name = gen_string('alpha')
        loc = entities.Location().create()
        with Session(self) as session:
            make_env(session, name=env_name, locations=[loc.name])
            self.assertIsNotNone(self.environment.search(env_name))

    @run_only_on('sat')
    @tier1
    def test_negative_create(self):
        """Try to create environment and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        :id: 51c7e300-5f59-4de8-bc55-1a75b03aa456

        :expectedresults: Environment is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_env(session, name=name)
                    self.assertIsNotNone(
                        session.nav.wait_until_element(
                            common_locators['name_haserror'])
                    )

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Update environment with a new name

        :id: 4fd6aa68-c850-4fcd-8c9b-f88d6c0d1c2d

        :expectedresults: Environment is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_env(session, name=name)
            for new_name in valid_environments_list():
                with self.subTest(new_name):
                    self.environment.update(name, new_name=new_name)
                    self.assertIsNotNone(self.environment.search(new_name))
                    name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete an environment

        :id: 8572461e-2457-4a1c-bb63-78f49ce2d0fd

        :expectedresults: Environment is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_environments_list():
                with self.subTest(name):
                    make_env(session, name=name)
                    self.environment.delete(name, dropdown_present=True)
