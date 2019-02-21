"""CLI tests for Repository setup.

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.cli.factory import (
    make_lifecycle_environment,
    make_org,
)
from robottelo.constants import (
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_YUM_REPO,
    DISTROS_SUPPORTED,
)
from robottelo.datafactory import xdist_adapter
from robottelo.products import (
    YumRepository,
    RepositoryCollection,
    SatelliteToolsRepository,
)
from robottelo.vm import VirtualMachine


def _distro_cdn_variants():
    distro_cdn = []
    for cdn in [False, True]:
        for distro in DISTROS_SUPPORTED:
            distro_cdn.append((distro, cdn))

    return distro_cdn


@pytest.mark.parametrize('value', **xdist_adapter(_distro_cdn_variants()))
def test_vm_install_package(value):
    """Install a package with all supported distros and cdn not cdn variants

    :id: b2a6065a-69f6-4805-a28b-eaaa812e0f4b

    :expectedresults: Package is install is installed
    """
    # the value is support distro DISTRO_RH6 or DISTRO_RH7
    # this will create 4 tests:
    #  - one test with disto rhel6 cdn False
    #  - one test with distro rhel7 cdn False
    #  - one test with disto rhel6 cdn True
    #  - one test with distro rhel7 cdn True
    distro, cdn = value
    org = make_org()
    lce = make_lifecycle_environment({'organization-id': org['id']})
    repos_collection = RepositoryCollection(
        distro=distro,
        repositories=[
            SatelliteToolsRepository(cdn=cdn),
            YumRepository(url=FAKE_0_YUM_REPO)
        ]
    )
    # this will create repositories , content view and activation key
    repos_collection.setup_content(org['id'], lce['id'], upload_manifest=True)
    with VirtualMachine(distro=distro) as vm:
        # this will install katello ca, register vm host, enable rh repos,
        # install katello-agent
        repos_collection.setup_virtual_machine(vm)
        # install a package
        result = vm.run('yum -y install {0}'.format(FAKE_0_CUSTOM_PACKAGE))
        assert result.return_code == 0
