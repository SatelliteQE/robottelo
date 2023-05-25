"""Unit tests for the new ``repositories`` paths.

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:team: Phoenix-content

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest


@pytest.mark.rhel_ver_list([7, 8, 9])
def test_positive_custom_products_by_default(
    session,
    default_location,
    setup_content,
    rhel_contenthost,
    target_sat,
):
    """Verify that custom products should be enabled by default for content hosts

    :id: 05bdf790-a7a1-48b1-bbae-dc25b6ee7d58

    :steps:
        1. Create custom product and upload repository
        2. Attach to activation key
        3. Register Host
        4. Assert that custom proudct is disabled by default

    :expectedresults: Custom products should be disabled by default. "Enabled: 0"
    """
    ak, org = setup_content
    client = rhel_contenthost
    client.install_katello_ca(target_sat)
    client.register_contenthost(org.label, ak.name)
    assert client.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)
        #assert session.contenthost.search(rhel_contenthost.hostname)[0]['Name'] == rhel_contenthost.hostname
        # chost = session.contenthost.read(
        #     rhel_contenthost.hostname, widget_names=['details', 'provisioning_details', 'subscriptions']
        # )
        # session.contenthost.update(rhel_contenthost.hostname, {'repository_sets.limit_to_lce': True})
        # host_details = session.contenthost.read(
        #     rhel_contenthost.hostname, widget_names=['repository_sets']
        # )
        host_detail = session.host_new.get_details(target_sat.hostname, widget_names='content.repository_sets')
        ak_details = session.activationkey.read(ak.name, widget_names='repository sets')[
            'repository sets'
        ]['table'][0]
        assert 'Disabled' in ak_details['Status']
        # assert host_details != 0
        # assert session.activationkey.search(name)[0]['Name'] == name
        # session.activationkey.add_subscription(name, constants.DEFAULT_SUBSCRIPTION_NAME)
        # ak = session.activationkey.read(name, widget_names='subscriptions')
        # subs_name = ak['subscriptions']['resources']['assigned'][0]['Repository Name']
        # assert subs_name == constants.DEFAULT_SUBSCRIPTION_NAME
