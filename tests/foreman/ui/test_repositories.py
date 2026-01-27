"""Test module for Repositories UI.

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Artemis

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


@pytest.mark.rhel_ver_match('N-2')
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


@pytest.mark.rhel_ver_match('N-2')
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
           using the new functionality at the top
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


@pytest.mark.rhel_ver_match('N-2')
@pytest.mark.parametrize(
    'status_filter',
    ['All statuses', 'Enabled', 'Disabled', 'Overridden'],
)
def test_positive_repo_sets_status_filter(
    session,
    default_location,
    setup_content,
    rhel_contenthost,
    target_sat,
    status_filter,
):
    """Filter repository sets by status on host details page

    :id: 8d8d41d8-50d8-41fd-a6a6-7d9662599864

    :parametrized: yes

    :steps:
        1. Create custom product and upload repository
        2. Attach to activation key and register host
        3. Navigate to host repository sets tab
        4. Use status filter to filter by 'Enabled', 'Disabled', 'Overridden', and 'All statuses'

    :expectedresults:
        1. Filtering by 'Disabled' shows only disabled repositories
        2. Filtering by 'Enabled' shows only enabled repositories
        3. Filtering by 'Overridden' shows only overridden repositories
        4. Filtering by 'All statuses' shows all repositories
    """
    ak, org, custom_repo = setup_content
    rhel_contenthost.register(org, default_location, ak.name, target_sat)
    assert rhel_contenthost.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)

        # Navigate to host repository sets tab
        view = session.host_new.navigate_to(
            session.host_new, 'Edit', entity_name=rhel_contenthost.hostname
        )
        view.content.repository_sets.click()
        view.browser.plugin.ensure_page_safe(timeout='5s')

        # Apply status filter
        view.content.repository_sets.status_filter.fill(status_filter)
        view.content.repository_sets.table.wait_displayed()

        # Read filtered results
        repos = view.content.repository_sets.table.read()

        # Verify filter results based on status
        if status_filter == 'Disabled':
            # Should only show disabled repos (custom repos are disabled by default)
            assert len(repos) > 0
            for repo in repos:
                assert repo['Status'] == 'Disabled'
        elif status_filter == 'Enabled':
            # Should show no repos initially (none enabled yet)
            assert len(repos) == 0
        elif status_filter == 'Overridden':
            # Should show no repos initially (none overridden yet)
            assert len(repos) == 0
        elif status_filter == 'All statuses':
            # Should show all available repos
            assert len(repos) > 0
