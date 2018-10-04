"""Tests for Red Hat Access Insights

:Requirement: Rhai

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL6, DISTRO_RHEL7
from robottelo.decorators import run_in_one_thread, skip_if_not_set, stubbed
from robottelo.test import UITestCase
from robottelo.ui.factory import set_context
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@run_in_one_thread
class RHAITestCase(UITestCase):

    @classmethod
    def setUpClass(cls):  # noqa
        super(RHAITestCase, cls).setUpClass()
        # Create a new organization with prefix 'insights'
        org = entities.Organization(
            name='insights_{0}'.format(gen_string('alpha', 6))
        ).create()

        # Upload manifest
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)

        # Create activation key using default CV and library environment
        activation_key = entities.ActivationKey(
            auto_attach=True,
            content_view=org.default_content_view.id,
            environment=org.library.id,
            name=gen_string('alpha'),
            organization=org,
        ).create()

        # Walk through the list of subscriptions.
        # Find the "Red Hat Employee Subscription" and attach it to the
        # recently-created activation key.
        for subs in entities.Subscription(organization=org).search():
            if subs.read_json()['product_name'] == DEFAULT_SUBSCRIPTION_NAME:
                # 'quantity' must be 1, not subscription['quantity']. Greater
                # values produce this error: "RuntimeError: Error: Only pools
                # with multi-entitlement product subscriptions can be added to
                # the activation key with a quantity greater than one."
                activation_key.add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': subs.id,
                })
                break
        cls.org_label = org.label
        cls.ak_name = activation_key.name
        cls.org_name = org.name

    @skip_if_not_set('clients')
    def test_positive_register_client_to_rhai(self):
        """Check client registration to redhat-access-insights service.

        :id: f3aefdb3-ac99-402d-afd9-e53e9ee1e8d7

        :expectedresults: Registered client should appear in the Systems sub-
            menu of Red Hat Access Insights
        """
        # Register a VM to Access Insights Service
        with VirtualMachine(distro=DISTRO_RHEL6) as vm:
            try:
                vm.configure_rhai_client(self.ak_name, self.org_label,
                                         DISTRO_RHEL6)

                with Session(self) as session:
                    # view clients registered to Red Hat Access Insights
                    set_context(session, org=self.org_name, force_context=True)
                    self.assertIsNotNone(
                        session.rhai_inventory.search(vm.hostname)
                    )
                    result = session.rhai_inventory.get_total_systems()
                    self.assertIn("1", result,
                                  'Registered clients are not listed')
            finally:
                vm.get('/var/log/redhat-access-insights/'
                       'redhat-access-insights.log',
                       './insights_client_registration.log')

    def test_negative_org_not_selected(self):
        """Verify that user attempting to access RHAI is directed to select an
        Organization if there is no organization selected

        :id: 6ddfdb29-eeb5-41a4-8851-ad19130b112c

        :expectedresults: 'Organization Selection Required' message must be
            displayed if the user tries to view Access Insights overview
            without selecting an org
        """
        with Session(self) as session:
            # Given that the user does not specify any Organization
            set_context(session, org='Any Organization', force_context=True)
            # 'Organization Selection Required' message must be present
            msg = session.rhai_overview.get_organization_selection_message()
            self.assertIsNotNone(msg)
            self.assertIn("Organization Selection Required", msg)

    @skip_if_not_set('clients')
    def test_positive_unregister_client_from_rhai(self):
        """Verify that 'Unregister' a system from RHAI works correctly then the
        system should not be able to use the service.

        :id: 580f9704-8c6d-4f63-b027-68a6ac97af77

        :expectedresults: Once the system is unregistered from the RHAI web
            interface then the unregistered system should return `1` on running
            the service 'redhat-access-insights'
        """
        # Register a VM to Access Insights Service
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            try:
                vm.configure_rhai_client(self.ak_name, self.org_label,
                                         DISTRO_RHEL7)

                with Session(self) as session:
                    set_context(session, org=self.org_name, force_context=True)
                    session.rhai_inventory.unregister_system(vm.hostname)

                result = vm.run('redhat-access-insights')
                self.assertEqual(result.return_code, 1,
                                 "System has not been unregistered")
            finally:
                vm.get('/var/log/redhat-access-insights/'
                       'redhat-access-insights.log',
                       './insights_unregister.log')

    @stubbed
    def test_positive_rule_disable_enable(self):
        """Tests Insights rule can be disabled and enabled

        :id: ca61b798-7502-43a0-9045-392b350fdded

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Rules

            2. Disable the chosen rule (assert)

            3. Enable chosen rule (assert)

        :expectedresults: rule is disabled, rule is enabled

        :caseautomation: notautomated

        :CaseLevel: System
        """


@run_in_one_thread
class RHAIPlannerTestCase(RHAITestCase):
    """Tests Insights Planner related cases"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(RHAIPlannerTestCase, cls).setUpClass()

    @stubbed
    def test_positive_playbook_run(self):
        """Tests Planner playbook runs successfully

        :id: b4cce0dc-c98e-4e1a-9dac-cdee3be05227

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Planner

            2. Create a plan

            3. Assign specific host to the plan

            4. Assign a rule with ansible support to the plan

            5. Run Playbook

            6. Check the result at the host


        :expectedresults: playbook run finished successfully

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed
    def test_positive_playbook_customized_run(self):
        """Tests Planner playbook customized run is successful

        :id: eee4556d-69b9-4e89-88b7-3cc34a3fe3b2

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Planner

            2. Create a plan

            3. Assign specific host to the plan

            4. Assign a rule with ansible support to the plan

            5. Customize Playbook Run

            6. Run the customized job

            7. Check the result at the host


        :expectedresults: customized playbook run finished successfully

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed
    def test_positive_playbook_download(self):
        """Tests Planner playbook download is successful

        :id: 7e9ed852-3f23-4256-862c-1d05058e8a95

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Planner

            2. Create a plan

            3. Assign specific host to the plan

            4. Assign a rule with ansible support to the plan

            5. Download Playbook

            6. Check the downloaded result

        :expectedresults: sane playbook downloaded

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed
    def test_positive_plan_export_csv(self):
        """Tests Insights plan is exported to csv successfully

        :id: 4bf67758-e07a-41de-974f-9eda753d28e1

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Planner

            2. Create a plan

            3. Assign specific host to the plan

            4. Assign any rule to the plan

            5. Export CSV

            6. Check the exported plan CSV


        :expectedresults: plan exported to sane csv file

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed
    def test_positive_plan_edit_remove_system(self):
        """Tests Insights plan can be edited by removing a system from it

        :id: d4ea837e-48b0-4482-a1a7-0507346519d7

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Planner

            2. Create a plan

            3. Assign specific host to the plan

            4. Assign any rule to the plan

            5. Edit the plan and remove assigned system

            6. Check the plan become empty


        :expectedresults: plan becomes empty

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed
    def test_positive_plan_edit_remove_rule(self):
        """Tests Insights plan can be edited by removing a rule from it

        :id: dd05f149-b6ca-4845-8824-87e21d7b46e1

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Planner

            2. Create a plan

            3. Assign specific host to the plan

            4. Assign any rule to the plan

            5. Edit the plan and remove assigned rule

            6. Check the plan do not contain the rule


        :expectedresults: rule is not present in the plan

        :caseautomation: notautomated

        :CaseLevel: System
        """


@run_in_one_thread
class RHAIInventoryTestCase(RHAITestCase):
    """Tests Insights Inventory related cases"""

    @classmethod
    def setUpClass(cls):  # noqa
        super(RHAIInventoryTestCase, cls).setUpClass()

    @stubbed
    def test_positive_inventory_export_csv(self):
        """Tests Insights inventory can be exported to csv

        :id: df4085f4-b058-4c2f-974f-89bc90d83c9c

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Inventory

            2. Export CSV


        :expectedresults: inventory is exported in sane csv file

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed
    def test_positive_inventory_create_new_plan(self):
        """Tests Insights plan can be created using chosen inventory

        :id: 5af59eb0-b5d3-4ddb-9c34-f5f0d79353cc

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Inventory

            2. In Actions select Create new Plan/Playbook for a system

        :expectedresults: new plan is created and involves the chosen system

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed
    def test_positive_inventory_add_to_existing_plan(self):
        """Tests Insights inventory system can be added to the existing plan

        :id: 1a1923d0-22d3-4ecc-b9cb-ec8ebc2d9155

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Inventory

            2. In Actions select Create new Plan/Playbook for a system1

            3. In Actions select Add to existing Plan/Playbook for a system2

            4. Check that original plan contains also system2


        :expectedresults: existing plan gets extended of new system

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed
    def test_positive_inventory_group_systems(self):
        """Tests Insights inventory systems can be grouped

        :id: d6a2496f-b038-4d2b-80f9-95ef00225eb7

        :Steps:

            0. Create a VM and register to insights within org having manifest

            1. Navigate to Insights -> Inventory

            2. In Actions select Group systems and create new system group

            3. Check that selected system(s) are grouped in system group


        :expectedresults: systems are groupped in new Insights system group

        :caseautomation: notautomated

        :CaseLevel: System
        """
