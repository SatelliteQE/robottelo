"""Test class for Content Hosts UI

:Requirement: Content Host

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
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_ERRATA_ID,
    FAKE_1_YUM_REPO,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE_NAME,
)
from robottelo.decorators import tier3
from robottelo.products import (
    YumRepository,
    RepositoryCollection,
    SatelliteToolsRepository,
)
from robottelo.vm import VirtualMachine


@tier3
def test_positive_end_to_end(session):
    """Create all entities required for content host, set up host, register it
    as a content host, read content host details, install package and errata.

    :id: f43f2826-47c1-4069-9c9d-2410fd1b622c

    :expectedresults: content host details are the same as expected, package
        and errata installation are successful

    :CaseLevel: System
    """
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7,
        repositories=[
            SatelliteToolsRepository(),
            YumRepository(url=FAKE_1_YUM_REPO)
        ]
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    with VirtualMachine(distro=DISTRO_RHEL7) as vm:
        repos_collection.setup_virtual_machine(vm)
        result = vm.run('yum -y install {0}'.format(FAKE_1_CUSTOM_PACKAGE))
        assert result.return_code == 0
        with session:
            session.organization.select(org.name)
            # Ensure content host is searchable
            assert session.contenthost.search(
                vm.hostname)[0]['Name'] == vm.hostname
            chost = session.contenthost.read(vm.hostname)
            # Ensure all content host fields/tabs have appropriate values
            assert chost['details']['name'] == vm.hostname
            assert (
                chost['details']['content_view'] ==
                repos_collection.setup_content_data['content_view']['name']
            )
            assert chost['details']['lce'][lce.name][lce.name]
            assert (
                chost['details']['registered_by'] == 'Activation Key {}'
                .format(repos_collection.setup_content_data[
                    'activation_key']['name'])
            )
            assert chost['provisioning_details']['name'] == vm.hostname
            assert (
                chost['subscriptions']['resources']['assigned'][0][
                    'Repository Name'] ==
                repos_collection.custom_product['name']
            )
            actual_repos = {
                repo['Repository Name']
                for repo in chost['repository_sets']['table']
            }
            expected_repos = {
                repo['name'] for repo in repos_collection.custom_repos_info}
            assert actual_repos == expected_repos
            # Install package
            result = session.contenthost.execute_package_action(
                vm.hostname,
                'Package Install',
                FAKE_0_CUSTOM_PACKAGE_NAME,
            )
            assert result['result'] == 'success'
            # Ensure package installed
            packages = session.contenthost.search_package(
                vm.hostname, FAKE_0_CUSTOM_PACKAGE_NAME)
            assert packages[0]['Installed Package'] == FAKE_0_CUSTOM_PACKAGE
            # Install errata
            result = session.contenthost.install_errata(
                vm.hostname, FAKE_1_ERRATA_ID)
            assert result['result'] == 'success'
            # Ensure errata installed
            packages = session.contenthost.search_package(
                vm.hostname, FAKE_2_CUSTOM_PACKAGE_NAME)
            assert packages[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE
            # Delete content host
            session.contenthost.delete(vm.hostname)
            assert not session.contenthost.search(vm.hostname)
