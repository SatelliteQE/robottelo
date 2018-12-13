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

from robottelo.constants import (
    DISTRO_RHEL7,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_6_YUM_REPO,
)
from robottelo.decorators import tier3
from robottelo.products import (
    YumRepository,
    RepositoryCollection,
    SatelliteToolsRepository,
)
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
    }
    ERRATA_PACKAGES = {
        'independent_packages': [
            'penguin-0.9.1-1.noarch',
            'shark-0.1-1.noarch',
            'walrus-5.21-1.noarch'
        ],
        'module_stream_packages': [],
    }
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7,
        repositories=[
            SatelliteToolsRepository(),
            YumRepository(url=CUSTOM_REPO_URL)
        ]
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    with VirtualMachine(distro=DISTRO_RHEL7) as client:
        repos_collection.setup_virtual_machine(client)
        assert client.subscribed
        client.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        with session:
            session.organization.select(org.name)
            errata = session.errata.read(CUSTOM_REPO_ERRATA_ID)
            assert errata['details'] == ERRATA_DETAILS
            assert errata['packages'] == ERRATA_PACKAGES
            assert (
                errata['repositories']['table'][0]['Name'] ==
                repos_collection.custom_repos_info[-1]['name']
            )
            assert (
                errata['repositories']['table'][0]['Product'] ==
                repos_collection.custom_product['name']
            )
            result = session.errata.install(
                CUSTOM_REPO_ERRATA_ID, client.hostname)
            assert result['result'] == 'success'
