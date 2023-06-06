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
    setup_content,
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
    """
    ak, org = setup_content
    client = rhel_contenthost
    client.install_katello_ca(target_sat)
    client.register_contenthost(org.label, ak.name)
    assert client.subscribed
    product_details = rhel_contenthost.run('subscription-manager repos --list')
    assert "Enabled:   0" in product_details.stdout
