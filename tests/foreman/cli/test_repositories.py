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
import time
from requests.exceptions import HTTPError



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


def test_negative_invalid_repo_fails_publish(
    module_repository,
    module_org,
    target_sat,
):
    """Verify that an invalid repository fails when trying to publish in a content view

    :id: 64e03f28-8213-467a-a229-44c8cbfaaef1

    :steps:
        1. Create custom product and upload repository
        2. Run Katello commands to make repository invalid
        3. Create content view and add repository 
        4. Verify Publish fails 

    :expectedresults: Publishing a content view with an invalid repository fails

    :customerscenario: true

    :BZ: 2032040
    """
    repo = module_repository
    with target_sat.session.shell() as sh:
            sh.send('foreman-rake console')
            time.sleep(30)  # sleep to allow time for console to open
            sh.send(f'root = ::Katello::RootRepository.last')
            time.sleep(3)  # give enough time for the command to complete
            sh.send(f'::Katello::Resources::Candlepin::Product.remove_content(root.product.organization.label, root.product.cp_id, root.content_id)')
            time.sleep(3)
            sh.send(f'::Katello::Resources::Candlepin::Content.destroy(root.product.organization.label, root.content_id)') 
            time.sleep(3)  
    cv = target_sat.api.ContentView(
        organization=module_org.name,
        repository=[repo.id],
    ).create()
    with pytest.raises(HTTPError) as context:
        cv.publish()
    assert 'Remove the invalid repository before publishing again' in context.value.response.text