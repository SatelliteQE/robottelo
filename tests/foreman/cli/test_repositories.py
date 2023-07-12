"""Test module for Repositories CLI.

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
    setup_content,
    default_location,
    rhel_contenthost,
    target_sat,
):
    """Verify that custom products should be disabled by default for content hosts

    :id: ba237e11-3b41-49e3-94b3-63e1f404d9e5

    :steps:
        1. Create custom product and upload repository
        2. Attach to activation key
        3. Register Host
        4. Assert that custom proudcts are disabled by default

    :expectedresults: Custom products should be disabled by default. "Enabled: 0"

    :customerscenario: true

    :BZ: 1265120
    """
    ak, org, _ = setup_content
    rhel_contenthost.register(org, default_location, ak.name, target_sat)
    assert rhel_contenthost.subscribed
    product_details = rhel_contenthost.run('subscription-manager repos --list')
    assert 'Enabled:   0' in product_details.stdout
