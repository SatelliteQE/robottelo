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
from robottelo.decorators import tier2
from robottelo.vm import VirtualMachine


pytestmark = pytest.mark.usefixtures("attach_subscription")


@pytest.fixture(scope="module")
def module_org():
    org = entities.Organization(name="insights_{0}".format(
        gen_string("alpha", 6))).create()
    with manifests.clone() as manifest:
        up_man(org.id, manifest.content)
    yield org
    org.delete()


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
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


@pytest.fixture
def vm(activation_key, module_org):
    with VirtualMachine(distro=DISTRO_RHEL7) as vm:
        vm.configure_rhai_client(
            activation_key=activation_key.name,
            org=module_org.label,
            rhel_distro=DISTRO_RHEL7)
        yield vm


@tier2
def test_positive_register_client_to_rhai(vm, autosession):
    """Check client registration to redhat-access-insights service.

    :id: 9815151e-d50d-4160-9d29-ae7c89422e18

    :expectedresults: Registered client should appear in the Systems sub-
        menu of Red Hat Access Insights

    :CaseLevel: Integration
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
