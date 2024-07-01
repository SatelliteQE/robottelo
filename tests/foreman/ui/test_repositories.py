"""Test module for Repositories UI.

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: Critical

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

    :customerscenario: true
    """
    ak, org, custom_repo = setup_content
    rhel_contenthost.register(org, default_location, ak.name, target_sat)
    assert rhel_contenthost.subscribed
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


@pytest.mark.rhel_ver_match('[^6]')
def test_positive_override_custom_products_using_select_all(
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

    :parametrized: yes
    """
    ak, org, custom_repo = setup_content
    client = rhel_contenthost
    client.register(org, default_location, ak.name, target_sat)
    assert client.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)
        repo = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repo[0]['Repository'] == custom_repo.name
        assert repo[0]['Status'] == 'Disabled'
        session.host_new.bulk_override_repo_sets(
            rhel_contenthost.hostname, 'Custom', "Override to enabled"
        )
        repo = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repo[0]['Repository'] == custom_repo.name
        assert repo[0]['Status'] == 'Enabled'


@pytest.mark.rhel_ver_match('[^6]')
def test_positive_override_custom_products_not_using_select_all(
    session,
    default_location,
    setup_content,
    rhel_contenthost,
    target_sat,
):
    """Verify that custom products can be easily enabled/disabled on existing host
    by individually selecting the repositories from the table instead of the select all method

    :id: 9d5c05fb-3683-40a2-91fd-a3aa526b25f4

    :setup:
        1. Create custom product and upload repository
        2. Attach to activation key

    :steps:
        1. Register Host
        2. Assert that custom proudcts are disabled by default
        3. Override custom products to enabled by selecting the repos individually and
           using the new funtionality at the top
        4. Assert custom products are now enabled

    :expectedresults: Custom products should be easily enable NOT using the select all method

    :BZ: 2256473

    :parametrized: yes
    """
    ak, org, custom_repo = setup_content
    rhel_contenthost.register(org, default_location, ak.name, target_sat)
    assert rhel_contenthost.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)
        repo = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repo[0]['Repository'] == custom_repo.name
        assert repo[0]['Status'] == 'Disabled'
        session.host_new.override_multiple_repo_sets(
            rhel_contenthost.hostname, custom_repo.name, 'Custom', 'Override to enabled'
        )
        repo = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repo[0]['Repository'] == custom_repo.name
        assert repo[0]['Status'] == 'Enabled'
