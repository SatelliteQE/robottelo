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
def test_positive_custom_products_override_when_sca_toggle(
    session,
    default_location,
    setup_content,
    rhel_contenthost,
    target_sat,
):
    """Verify that Custom Products enabled in non sca Organizations are
    set to Disabled(override) when sca is toggled on

    :id: baf4e620-1ed9-4840-bb53-869b8873af63

    :steps:
        1. Create Custom Product and upload Repository
        2. Attach to Activation Key
        3. Disable SCA on the Organization
        4. Add Subscription to Activation Key
        5. Register Host
        6. Verify Repository status is "Enabled"
        7. Set Organization back to SCA mode
        8. Verify Repository status is "Disabled(Override)"

    :expectedresults: Repository status should be set to Disabled(Override)
    """
    ak, org, custom_repo = setup_content
    org.sca_disable()
    ak.add_subscriptions(data={'subscription_id': custom_repo.product.id})
    client = rhel_contenthost
    client.install_katello_ca(target_sat)
    client.register_contenthost(org.label, ak.name)
    assert client.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)
        repos1 = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repos1[0]['Repository'] == custom_repo.name
        assert repos1[0]['Status'] == 'Enabled'
        org.sca_enable()
        repos2 = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repos2[0]['Repository'] == custom_repo.name
        assert repos2[0]['Status'] == 'Disabled'
