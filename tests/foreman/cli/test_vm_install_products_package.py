"""CLI tests for Repository setup.

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Repositories

:Assignee: chiggins

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker import VMBroker

from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_org
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CONTAINER_UPSTREAM_NAME
from robottelo.constants import DISTRO_RHEL6
from robottelo.constants import DISTROS_SUPPORTED
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE
from robottelo.hosts import ContentHost
from robottelo.products import DockerRepository
from robottelo.products import RepositoryCollection
from robottelo.products import SatelliteToolsRepository
from robottelo.products import YumRepository


@pytest.fixture
def org():
    return make_org()


@pytest.fixture
def lce(org):
    return make_lifecycle_environment({'organization-id': org['id']})


@pytest.mark.tier4
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.parametrize('cdn', [True, False], ids=['cdn', 'no_cdn'])
@pytest.mark.parametrize('distro', DISTROS_SUPPORTED)
def test_vm_install_package(org, lce, distro, cdn, default_sat):
    """Install a package with all supported distros and cdn / non-cdn variants

    :id: b2a6065a-69f6-4805-a28b-eaaa812e0f4b

    :parametrized: yes

    :expectedresults: Package is install is installed
    """
    if distro == DISTRO_RHEL6:
        pytest.skip(f'{DISTRO_RHEL6!s} skipped until ELS subscriptions are in manifest.')
    repos_collection = RepositoryCollection(
        distro=distro,
        repositories=[
            SatelliteToolsRepository(cdn=cdn, distro=distro),
            YumRepository(url=settings.repos.yum_0.url),
            DockerRepository(url=CONTAINER_REGISTRY_HUB, upstream_name=CONTAINER_UPSTREAM_NAME),
        ],
    )
    # Create repos, content view, and activation key.
    repos_collection.setup_content(
        satellite=default_sat, org_id=org['id'], lce_id=lce['id'], upload_manifest=True
    )
    with VMBroker(nick=distro, host_classes={'host': ContentHost}) as host:
        # install katello-agent
        repos_collection.setup_virtual_machine(
            host, default_sat, enable_custom_repos=True, install_katello_agent=False
        )
        # install a package from custom repo
        result = host.execute(f'yum -y install {FAKE_0_CUSTOM_PACKAGE}')
        assert result.status == 0
