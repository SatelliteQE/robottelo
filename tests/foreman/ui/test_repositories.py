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
        4. Register Host
        5. Set Organization back to SCA mode
        6. Verify Repository status is "Disabled(Override)"
        7. Verify Repository is listed under SubMan repo-override


    :expectedresults: Repository status should be set to Disabled(Override)

    :BZ: 2188380
    """
    ak, org, custom_repo = setup_content
    org.sca_disable()
    rhel_contenthost.register(org, default_location, ak.name, target_sat)
    assert rhel_contenthost.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)
        org.sca_enable()
        repos2 = session.host_new.get_repo_sets(rhel_contenthost.hostname, custom_repo.name)
        assert repos2[0]['Repository'] == custom_repo.name
        assert repos2[0]['Status'] == 'Disabled'
        result = rhel_contenthost.execute('subscription-manager repo-override --list')
        assert custom_repo.name in result.stdout
