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
    CUSTOM_PUPPET_REPO,
    DISTROS_SUPPORTED,
    DOCKER_REGISTRY_HUB,
    DOCKER_UPSTREAM_NAME,
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_YUM_REPO,
)
from robottelo.datafactory import xdist_adapter
from robottelo.products import (
    DockerRepository,
    PuppetRepository,
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


@pytest.fixture(scope='module')
def module_org():
    return make_org()


@pytest.fixture(scope='module')
def module_lce(module_org):
    return make_lifecycle_environment({'organization-id': module_org['id']})


@pytest.mark.parametrize('value', **xdist_adapter(_distro_cdn_variants()))
def test_vm_install_package(value, module_org, module_lce):
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
    repos_collection = RepositoryCollection(
        distro=distro,
        repositories=[
            SatelliteToolsRepository(cdn=cdn),
            YumRepository(url=FAKE_0_YUM_REPO),
            DockerRepository(url=DOCKER_REGISTRY_HUB, upstream_name=DOCKER_UPSTREAM_NAME),
            PuppetRepository(url=CUSTOM_PUPPET_REPO,
                             modules=[dict(name='generic_1', author='robottelo')])
        ]
    )
    # this will create repositories , content view and activation key
    repos_collection.setup_content(module_org['id'], module_lce['id'], upload_manifest=True)
    with VirtualMachine(distro=distro) as vm:
        # this will install katello ca, register vm host, enable rh repos,
        # install katello-agent
        repos_collection.setup_virtual_machine(vm, enable_custom_repos=True)
        # install a package
        result = vm.run('yum -y install {0}'.format(FAKE_0_CUSTOM_PACKAGE))
        assert result.return_code == 0
