# -*- encoding: utf-8 -*-
"""Test class for Host Group UI

:Requirement: Hostgroup

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities

from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_hostgroup
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session
from robottelo.config import settings


class HostgroupTestCase(UITestCase):
    """Implements HostGroup tests from UI"""

    @classmethod
    def setUpClass(cls):
        """Set up class for hostgroup UI test cases"""
        super(HostgroupTestCase, cls).setUpClass()
        cls.sat6_hostname = settings.server.hostname
        cls.organization = entities.Organization().create()
        cls.env = entities.LifecycleEnvironment(
            organization=cls.organization, name='Library').search()[0]
        cls.cv = entities.ContentView(organization=cls.organization).create()
        cls.cv.publish()
        cls.ak = entities.ActivationKey(
            organization=cls.organization,
            environment=cls.env,
            content_view=cls.cv,
        ).create()

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create new hostgroup

        :id: 8bcf45e5-9e7f-4050-9de6-a90350b70006

        :Assert: Hostgroup is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_hostgroup(session, name=name)
                    self.assertIsNotNone(self.hostgroup.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new hostgroup with invalid names

        :id: a0232740-ae9f-44ce-9f3d-bafc8f1b05cb

        :Assert: Hostgroup is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_hostgroup(session, name=name)
                    self.assertIsNotNone(
                        self.hostgroup.wait_until_element(
                            common_locators['name_haserror'])
                    )

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Create new hostgroup with same name

        :id: 237b684d-3b55-444a-be00-a9825952bb53

        :Assert: Hostgroup is not created
        """
        name = gen_string('utf8')
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            make_hostgroup(session, name=name)
            self.assertIsNotNone(
                self.hostgroup.wait_until_element(
                    common_locators['name_haserror'])
            )

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete a hostgroup

        :id: f118532b-ca9b-4bf4-b53b-9573abcb347a

        :Assert: Hostgroup is deleted
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=4):
                with self.subTest(name):
                    make_hostgroup(session, name=name)
                    self.hostgroup.delete(name)

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Update hostgroup with a new name

        :id: 7c8de1b8-aced-44f0-88a0-dc9e6b83bf7f

        :Assert: Hostgroup is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            for new_name in generate_strings_list(length=4):
                with self.subTest(new_name):
                    self.hostgroup.update(name, new_name=new_name)
                    self.assertIsNotNone(self.hostgroup.search(new_name))
                    name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_oscap_capsule(self):
        """Create new hostgroup with oscap capsule

        :id: c0ab1148-93ff-41d3-93c3-2ff139349884

        :Assert: Hostgroup is created with oscap capsule
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_hostgroup(
                    session,
                    content_source=self.sat6_hostname,
                    name=name,
                    puppet_ca=self.sat6_hostname,
                    puppet_master=self.sat6_hostname,
                    oscap_capsule=self.sat6_hostname,
                )
            self.assertIsNotNone(self.hostgroup.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_activation_keys(self):
        """Create new hostgroup with activation keys

        :id: cfda3c1b-37fd-42c1-a74c-841efb83b2f5

        :Assert: Hostgroup is created with activation keys
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_hostgroup(
                session,
                name=name,
                environment=self.env.name,
                content_view=self.cv.name,
                activation_key=self.ak.name,
            )
            self.assertIsNotNone(self.hostgroup.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_check_activation_keys_autocomplete(self):
        """Open Hostgroup New/Edit modal and verify that Activation Keys
        autocomplete respects selected Content View

        :id: 07906caf-871d-4d1f-8914-38027e71c16b

        :Steps:

            1. Create two content views A & B
            2. Publish both content views
            3. Create an activation key pointed to view A in Library
            4. Create an activation key pointed to view B in Library
            5. Go to the new Hostgroup page, select content view B & Library,
                click on the activation key tab and click in the input box

        :Assert: Only the activation key for view B is listed

        :BZ: 1321511
        """
        # Use setup entities as A and create another set for B.
        cv_b = entities.ContentView(organization=self.organization).create()
        cv_b.publish()
        ak_b = entities.ActivationKey(
            organization=self.organization,
            environment=self.env,
            content_view=cv_b,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_host_groups()
            self.hostgroup.click(locators['hostgroups.new'])
            self.hostgroup.assign_value(
                locators['hostgroups.environment'], self.env.name)
            self.hostgroup.assign_value(
                locators['hostgroups.content_view'], cv_b.name)
            # Switch to Activation Keys tab and click on input
            # to load autocomplete
            self.hostgroup.click(tab_locators['hostgroup.tab_activation_keys'])
            self.hostgroup.click(locators['hostgroups.activation_keys'])
            autocompletes = self.hostgroup.find_elements(
                locators['hostgroups.ak_autocomplete'])
            # Ensure that autocomplete list is not empty
            self.assertGreaterEqual(len(autocompletes), 1)
            # Check for AK names in list
            autocompletes = [item.text for item in autocompletes]
            self.assertIn(ak_b.name, autocompletes)
            self.assertNotIn(self.ak.name, autocompletes)
