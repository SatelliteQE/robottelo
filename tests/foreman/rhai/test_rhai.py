"""Tests for Red Hat Access Insights

:Requirement: Rhai

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import pytest
from fauxfactory import gen_string
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import upload_manifest as up_man
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME, DISTRO_RHEL7
from robottelo.decorators import fixture, stubbed
from robottelo.vm import VirtualMachine


pytestmark = pytest.mark.usefixtures("attach_subscription")


@fixture(scope="module")
def module_org():
    org = entities.Organization(name="insights_{0}".format(
        gen_string("alpha", 6))).create()
    with manifests.clone() as manifest:
        up_man(org.id, manifest.content)
    yield org
    org.delete()


@fixture(scope="module")
def activation_key(module_org):
    ak = entities.ActivationKey(
        auto_attach=True,
        content_view=module_org.default_content_view.id,
        environment=module_org.library.id,
        name=gen_string("alpha"),
        organization=module_org
    ).create()
    yield ak
    ak.delete()


@fixture(scope="module")
def attach_subscription(module_org, activation_key):
    for subs in entities.Subscription(organization=module_org).search():
        if subs.read_json()["product_name"] == DEFAULT_SUBSCRIPTION_NAME:
            # "quantity" must be 1, not subscription["quantity"]. Greater
            # values produce this error: "RuntimeError: Error: Only pools
            # with multi-entitlement product subscriptions can be added to
            # the activation key with a quantity greater than one."
            activation_key.add_subscriptions(data={
                "quantity": 1,
                "subscription_id": subs.id,
            })
            break
    else:
        raise Exception("{} organization doesn't have any subscription".format(
            module_org.name))


@fixture
def vm(activation_key, module_org):
    with VirtualMachine(distro=DISTRO_RHEL7) as vm:
        vm.configure_rhai_client(
            activation_key=activation_key.name,
            org=module_org.label,
            rhel_distro=DISTRO_RHEL7)
        yield vm


def test_positive_register_client_to_rhai(vm, autosession):
    """Check client registration to redhat-access-insights service.

    :id: 9815151e-d50d-4160-9d29-ae7c89422e18

    :expectedresults: Registered client should appear in the Systems sub-
        menu of Red Hat Access Insights
    """
    table = autosession.insightsinventory.search(vm.hostname)
    assert table[0]["System Name"].text == vm.hostname
    result = autosession.insightsinventory.total_systems
    assert result == "1", "Registered clients are not listed"


def test_positive_unregister_client_to_rhai(vm, autosession):
    """Check client canceling registration to redhat-access-insights service.

    :id: 70d1045b-7d9d-472e-8ce9-8a5b81c41a85

    :expectedresults: Unregistered client should not appear in the Systems sub-
        menu of Red Hat Access Insights
    """
    vm.unregister()
    table = autosession.insightsinventory.search(vm.hostname)
    assert not table[0].is_displayed
    result = autosession.insightsinventory.total_systems
    assert result == "0", "The client is still registered"


@stubbed
def test_negative_org_not_selected():
    """Verify that user attempting to access RHAI is directed to select an
    Organization if there is no organization selected

    :id: 6ddfdb29-eeb5-41a4-8851-ad19130b112c

    :expectedresults: 'Organization Selection Required' message must be
        displayed if the user tries to view Access Insights overview
        without selecting an org
    """


@stubbed
def test_positive_rule_disable_enable():
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


@stubbed
def test_positive_playbook_run():
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
def test_positive_playbook_customized_run():
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
def test_positive_playbook_download():
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
def test_positive_plan_export_csv():
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
def test_positive_plan_edit_remove_system():
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
def test_positive_plan_edit_remove_rule():
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


@stubbed
def test_positive_inventory_export_csv():
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
def test_positive_inventory_create_new_plan():
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
def test_positive_inventory_add_to_existing_plan():
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
def test_positive_inventory_group_systems():
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
