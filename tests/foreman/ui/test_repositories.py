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
def test_positive_custom_products_disabled_by_default(
    session,
    default_location,
    setup_content,
    rhel_contenthost,
    target_sat,
):
    """Verify that custom products should be disabled by default for content hosts
    and activation keys

    :id: 05bdf790-a7a1-48b1-bbae-dc25b6ee7d58

    :steps:
        1. Create custom product and upload repository
        2. Attach to activation key
        3. Register Host
        4. Assert that custom proudcts are disabled by default

    :expectedresults: Custom products should be disabled by default.
    """
    ak, org, custom_repo = setup_content
    client = rhel_contenthost
    client.install_katello_ca(target_sat)
    client.register_contenthost(org.label, ak.name)
    assert client.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)
        repos = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repos[0]['Repository'] == custom_repo.name
        assert repos[0]['Status'] == 'Disabled'
        assert repos[0]['Repository type'] == 'Custom'
        ak_details = session.activationkey.read(ak.name, widget_names='repository sets')[
            'repository sets'
        ]['table'][0]
        assert 'Disabled' in ak_details['Status']


@pytest.mark.rhel_ver_list([7, 8, 9])
def test_positive_override_custom_products_on_existing_host(
    session,
    default_location,
    setup_content,
    rhel_contenthost,
    target_sat,
):
    """Verify that custom products can be easily enabled/disabled on existing host
    using "select all" method

    :id: a3c9a8c8-a40f-448b-961a-7eb888883ba9

    :steps:
        1. Create custom product and upload repository
        2. Attach to activation key
        3. Register Host
        4. Assert that custom proudcts are disabled by default
        5. Override custom products to enabled using new functionality
        6. Assert custom products are now enabled

    :expectedresults: Custom products should be easily enabled.
    """
    ak, org, custom_repo = setup_content
    client = rhel_contenthost
    client.install_katello_ca(target_sat)
    client.register_contenthost(org.label, ak.name)
    assert client.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)
        repo1 = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repo1[0]['Repository'] == custom_repo.name
        assert repo1[0]['Status'] == 'Disabled'
        session.host_new.bulk_override_repo_sets(
            rhel_contenthost.hostname, 'Custom', "Override to enabled"
        )
        repo2 = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repo2[0]['Repository'] == custom_repo.name
        assert repo2[0]['Status'] == 'Enabled'
