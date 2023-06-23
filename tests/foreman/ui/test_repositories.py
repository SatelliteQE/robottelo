"""Test module for Repositories UI.

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


@pytest.mark.rhel_ver_match('[^6]')
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

    :BZ: 1265120
    """
    ak, org, custom_repo = setup_content
    client = rhel_contenthost
    client.register(org, default_location, ak.name, target_sat)
    assert client.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)
        ak_details = session.activationkey.read(ak.name, widget_names='repository sets')[
            'repository sets'
        ]['table'][0]
        assert 'Disabled' in ak_details['Status']
        repos = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repos[0]['Repository'] == custom_repo.name
        assert repos[0]['Status'] == 'Disabled'
        assert repos[0]['Repository type'] == 'Custom'
