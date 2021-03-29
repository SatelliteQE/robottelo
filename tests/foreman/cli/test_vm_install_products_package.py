"""CLI tests for Repository setup.

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:Assignee: tpapaioa

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_org
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CONTAINER_UPSTREAM_NAME
from robottelo.constants import DISTROS_SUPPORTED
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.constants.repos import FAKE_0_YUM_REPO
from robottelo.datafactory import xdist_adapter
from robottelo.products import DockerRepository
from robottelo.products import PuppetRepository
from robottelo.products import RepositoryCollection
from robottelo.products import SatelliteToolsRepository
from robottelo.products import YumRepository
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


@pytest.mark.tier4
@pytest.mark.parametrize('value', **xdist_adapter(_distro_cdn_variants()))
@pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
def test_vm_install_package(value, module_org, module_lce):
    """Install a package with all supported distros and cdn not cdn variants

    :id: b2a6065a-69f6-4805-a28b-eaaa812e0f4b

    :parametrized: yes

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
            DockerRepository(url=CONTAINER_REGISTRY_HUB, upstream_name=CONTAINER_UPSTREAM_NAME),
            PuppetRepository(
                url=CUSTOM_PUPPET_REPO, modules=[dict(name='generic_1', author='robottelo')]
            ),
        ],
    )
    # this will create repositories , content view and activation key
    repos_collection.setup_content(module_org['id'], module_lce['id'], upload_manifest=True)
    with VirtualMachine(distro=distro) as vm:
        # this will install katello ca, register vm host, enable rh repos,
        # install katello-agent
        repos_collection.setup_virtual_machine(vm, enable_custom_repos=True)
        # install a package
        result = vm.run(f'yum -y install {FAKE_0_CUSTOM_PACKAGE}')
        assert result.return_code == 0
