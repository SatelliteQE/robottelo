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
from robottelo.decorators import run_only_on, stubbed, tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.factory import make_hostgroup, set_context
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

        :expectedresults: Hostgroup is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_hostgroup(session, name=name)
                    self.assertIsNotNone(self.hostgroup.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new hostgroup with invalid names

        :id: a0232740-ae9f-44ce-9f3d-bafc8f1b05cb

        :expectedresults: Hostgroup is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :expectedresults: Hostgroup is not created

        :CaseImportance: Critical
        """
        name = gen_string('utf8')
        with Session(self) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            make_hostgroup(session, name=name)
            self.assertIsNotNone(
                self.hostgroup.wait_until_element(
                    common_locators['name_haserror'])
            )

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_arch_and_os(self):
        """Create new hostgroup with architecture and operating system assigned

        :id: eaa91ddb-fce0-4284-88f8-c4d4367086c5

        :expectedresults: Hostgroup is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        arch = entities.Architecture().create()
        custom_os = entities.OperatingSystem(
            architecture=[arch]).create()
        with Session(self) as session:
            make_hostgroup(
                session,
                name=name,
                org=self.organization.name,
                parameters_list=[
                    ['Operating System', 'Architecture', arch.name],
                    [
                        'Operating System',
                        'Operating system',
                        '{0} {1}'.format(custom_os.name, custom_os.major)
                    ],
                ],
            )
            self.assertIsNotNone(self.hostgroup.search(name))

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_create_with_oscap_capsule(self):
        """Create new hostgroup with oscap capsule

        :id: c0ab1148-93ff-41d3-93c3-2ff139349884

        :expectedresults: Hostgroup is created with oscap capsule

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_hostgroup(
                session,
                name=name,
                parameters_list=[
                    ['Host Group', 'Content Source', self.sat6_hostname],
                    ['Host Group', 'Puppet CA', self.sat6_hostname],
                    ['Host Group', 'Puppet Master', self.sat6_hostname],
                    ['Host Group', 'Openscap Capsule', self.sat6_hostname],
                ],
            )
            self.assertIsNotNone(self.hostgroup.search(name))

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_create_with_activation_keys(self):
        """Create new hostgroup with activation keys

        :id: cfda3c1b-37fd-42c1-a74c-841efb83b2f5

        :expectedresults: Hostgroup is created with activation keys

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_hostgroup(
                session,
                name=name,
                org=self.organization.name,
                parameters_list=[
                    ['Host Group', 'Lifecycle Environment', self.env.name],
                    ['Host Group', 'Content View', self.cv.name],
                    ['Activation Keys', 'Activation Keys', self.ak.name],
                ],
            )
            self.assertIsNotNone(self.hostgroup.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Update hostgroup with a new name

        :id: 7c8de1b8-aced-44f0-88a0-dc9e6b83bf7f

        :expectedresults: Hostgroup is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            for new_name in generate_strings_list(length=4):
                with self.subTest(new_name):
                    self.hostgroup.update(name, new_name=new_name)
                    self.assertIsNotNone(self.hostgroup.search(new_name))
                    name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_positive_update_with_removed_arch(self):
        """Create new hostgroup with content view, architecture and os
        assigned. Then remove these attributes from the hostgroup. Attempt to
        update hostgroup with the same architecture

        :id: 431d88a3-590e-42cf-b45d-09b1d8a62b30

        :expectedresults: Hostgroup is updated and no error is raised

        :BZ: 1372917

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        arch = entities.Architecture().create()
        custom_os = entities.OperatingSystem(
            architecture=[arch]).create()
        with Session(self) as session:
            make_hostgroup(
                session,
                name=name,
                org=self.organization.name,
                parameters_list=[
                    ['Host Group', 'Lifecycle Environment', self.env.name],
                    ['Host Group', 'Content View', self.cv.name],
                    ['Operating System', 'Architecture', arch.name],
                    [
                        'Operating System',
                        'Operating system',
                        '{0} {1}'.format(custom_os.name, custom_os.major)
                    ],
                ],
            )
            self.hostgroup.search_and_click(name)
            self.hostgroup.click(
                tab_locators['hostgroup.tab_operating_system'])
            self.assertEqual(
                self.hostgroup.wait_until_element(
                    locators['hostgroups.architecture_value']).text,
                arch.name
            )
            self.hostgroup.update(
                name,
                parameters_list=[
                    ['Operating System', 'Operating system', None],
                    ['Operating System', 'Architecture', None],
                ],
            )
            self.hostgroup.search_and_click(name)
            self.hostgroup.click(
                tab_locators['hostgroup.tab_operating_system'])
            self.assertIsNone(self.hostgroup.wait_until_element(
                locators['hostgroups.architecture_value'], timeout=5))
            self.hostgroup.update(
                name,
                parameters_list=[
                    ['Operating System', 'Architecture', arch.name]
                ],
            )
            self.assertIsNone(self.hostgroup.wait_until_element(
                common_locators['haserror'], timeout=3))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete a hostgroup

        :id: f118532b-ca9b-4bf4-b53b-9573abcb347a

        :expectedresults: Hostgroup is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list(length=4):
                with self.subTest(name):
                    make_hostgroup(session, name=name)
                    self.hostgroup.delete(name, dropdown_present=True)

    @run_only_on('sat')
    @tier1
    def test_negative_delete_with_discovery_rule(self):
        """Attempt to delete hostgroup which has dependent discovery rule

        :id: bd046e9a-f0d0-4110-8f94-fd04193cb3af

        :customerscenario: true

        :BZ: 1254102

        :expectedresults: Hostgroup was not deleted. Informative error message
            was shown

        :CaseImportance: High
        """
        hostgroup = entities.HostGroup(
            organization=[self.session_org]).create()
        entities.DiscoveryRule(
            hostgroup=hostgroup,
            organization=[self.session_org],
        ).create()
        with Session(self):
            self.hostgroup.search(hostgroup.name)
            self.hostgroup.click(
                common_locators['select_action_dropdown'] % hostgroup.name)
            self.hostgroup.click(
                common_locators['delete_button'] % hostgroup.name,
                wait_for_ajax=False
            )
            self.hostgroup.handle_alert(True)
            error = self.hostgroup.wait_until_element(
                common_locators['alert.error'])
            self.assertIsNotNone(error)
            self.assertEqual(
                error.text,
                'Error: Cannot delete record because dependent discovery '
                'rules exist'
            )
            self.assertIsNotNone(self.hostgroup.search(hostgroup.name))

    @run_only_on('sat')
    @tier1
    def test_positive_redirection_for_multiple_hosts(self):
        """Create new hostgroup with whitespaces in its name for specific
        organization and location. After that create some hosts using already
        created hostgroup

        :id: f301ec2f-1e9b-4e34-8c87-4d0b3381d9e1

        :expectedresults: Hostgroup hosts count can be successfully observed
            in a table and redirection to these hosts works properly

        :BZ: 1402390

        :CaseImportance: Critical
        """
        name = '{0} {1}'.format(gen_string('alpha'), gen_string('numeric'))
        org = entities.Organization().create()
        loc = entities.Location(organization=[org]).create()
        hostgroup = entities.HostGroup(
            location=[loc],
            organization=[org],
            name=name,
        ).create()
        host_names = [
            entities.Host(
                hostgroup=hostgroup,
                location=loc,
                organization=org,
                content_facet_attributes={
                    'content_view_id': self.cv.id,
                    'lifecycle_environment_id': self.env.id,
                },
            ).create().name
            for _ in range(3)
        ]
        with Session(self) as session:
            set_context(session, org=org.name, loc=loc.name)
            self.assertIsNotNone(self.hostgroup.search(name))
            self.hostgroup.click(
                common_locators['table_cell_link'] % (name, 'Hosts'))
            for host_name in host_names:
                self.hosts.wait_until_element(
                    locators['host.select_name'] % host_name)

    @run_only_on('sat')
    @stubbed('unstub once os/browser/env combination is changed')
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

        :expectedresults: Only the activation key for view B is listed

        :BZ: 1321511

        :CaseImportance: Critical
        """
        # Use setup entities as A and create another set for B.
        cv_b = entities.ContentView(organization=self.organization).create()
        cv_b.publish()
        ak_b = entities.ActivationKey(
            organization=self.organization,
            environment=self.env,
            content_view=cv_b,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_host_groups()
            self.hostgroup.click(locators['hostgroups.new'])
            self.hostgroup.assign_value(
                locators['hostgroups.lifecycle_environment'], self.env.name)
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
