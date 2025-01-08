"""Test module for Repositories CLI.

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: Critical

"""

import pytest
from requests.exceptions import HTTPError

from robottelo.constants import DEFAULT_ARCHITECTURE, REPOS, REPOSET


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
    target_sat.execute(
        'echo "root = ::Katello::RootRepository.last; ::Katello::Resources::Candlepin::Product.'
        'remove_content(root.product.organization.label, root.product.cp_id, root.content_id); '
        '::Katello::Resources::Candlepin::Content.destroy(root.product.organization.label, '
        'root.content_id)" | foreman-rake console'
    )
    cv = target_sat.api.ContentView(
        organization=module_org.name,
        repository=[repo.id],
    ).create()
    with pytest.raises(HTTPError) as context:
        cv.publish()
    assert 'Remove the invalid repository before publishing again' in context.value.response.text


def test_positive_disable_rh_repo_with_basearch(module_target_sat, module_entitlement_manifest_org):
    """Verify that users can disable Red Hat Repositories with basearch

    :id: dd3b63b7-1dbf-4d8a-ab66-348de0ad7cf3

    :steps:
        1.  You have the Appstream Kicstart repositories release version
            "8" synced in from the release of RHEL 8
        2.  hammer repository-set disable --basearch --name --product-id
            --organization --releasever


    :expectedresults: Users can now disable Red Hat repositories with
        basearch

    :customerscenario: true

    :BZ: 1932486
    """
    rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_entitlement_manifest_org.id,
        product=REPOS['kickstart']['rhel8_aps']['product'],
        repo=REPOS['kickstart']['rhel8_aps']['name'],
        reposet=REPOS['kickstart']['rhel8_aps']['reposet'],
        releasever=REPOS['kickstart']['rhel8_aps']['version'],
    )
    repo = module_target_sat.api.Repository(id=rh_repo_id).read()
    repo.sync(timeout=600)
    disabled_repo = module_target_sat.cli.RepositorySet.disable(
        {
            'basearch': DEFAULT_ARCHITECTURE,
            'name': REPOSET['kickstart']['rhel8_bos'],
            'product-id': repo.product.id,
            'organization-id': module_entitlement_manifest_org.id,
            'releasever': REPOS['kickstart']['rhel8_aps']['version'],
            'repository-id': rh_repo_id,
        }
    )
    assert 'Repository disabled' in disabled_repo[0]['message']
