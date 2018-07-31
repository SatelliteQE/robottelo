"""UI Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.cli.factory import (
    setup_org_for_a_custom_repo,
    setup_org_for_a_rh_repo,
)
from robottelo.constants import (
    DISTRO_RHEL7,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_6_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import tier3
from robottelo.vm import VirtualMachine

CUSTOM_REPO_URL = FAKE_6_YUM_REPO
CUSTOM_REPO_ERRATA_ID = FAKE_2_ERRATA_ID


@tier3
def test_end_to_end(session):
    """Create all entities required for errata, set up applicable host,
    read errata details and apply it to host

    :id: a26182fc-f31a-493f-b094-3f5f8d2ece47

    :expectedresults: Errata details are the same as expected, errata
        installation is successful

    :CaseLevel: System
    """
    ERRATA_DETAILS = {
        'advisory': 'RHEA-2012:0055',
        'cves': 'N/A',
        'type': 'Security Advisory',
        'severity': 'N/A',
        'issued': '1/27/12',
        'last_updated_on': '1/27/12',
        'reboot_suggested': 'No',
        'topic': '',
        'description': 'Sea_Erratum',
        'solution': '',
        'affected_packages': [
            'penguin-0.9.1-1.noarch',
            'shark-0.1-1.noarch',
            'walrus-5.21-1.noarch'
        ]
    }
    org = entities.Organization().create()
    env = entities.LifecycleEnvironment(organization=org).create()
    content_view = entities.ContentView(organization=org).create()
    activation_key = entities.ActivationKey(
        environment=env,
        organization=org,
    ).create()
    setup_org_for_a_rh_repo({
        'product': PRDS['rhel'],
        'repository-set': REPOSET['rhst7'],
        'repository': REPOS['rhst7']['name'],
        'organization-id': org.id,
        'content-view-id': content_view.id,
        'lifecycle-environment-id': env.id,
        'activationkey-id': activation_key.id,
    }, force_manifest_upload=True)
    custom_entities = setup_org_for_a_custom_repo({
        'url': CUSTOM_REPO_URL,
        'organization-id': org.id,
        'content-view-id': content_view.id,
        'lifecycle-environment-id': env.id,
        'activationkey-id': activation_key.id,
    })
    product = entities.Product(id=custom_entities['product-id']).read()
    repo = entities.Repository(id=custom_entities['repository-id']).read()
    with VirtualMachine(distro=DISTRO_RHEL7) as client:
        client.install_katello_ca()
        client.register_contenthost(
            org.label,
            activation_key.name,
        )
        assert client.subscribed
        client.enable_repo(REPOS['rhst7']['id'])
        client.install_katello_agent()
        client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        with session:
            session.organization.select(org.name)
            errata = session.errata.read(CUSTOM_REPO_ERRATA_ID)
            assert errata['details'] == ERRATA_DETAILS
            assert errata['repositories']['table'][0]['Name'] == repo.name
            assert errata[
                'repositories']['table'][0]['Product'] == product.name
            result = session.errata.install(
                CUSTOM_REPO_ERRATA_ID, client.hostname)
            assert result['result'] == 'success'
