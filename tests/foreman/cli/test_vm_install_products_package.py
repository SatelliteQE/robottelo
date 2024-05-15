"""CLI tests for Repository setup.

:Requirement: Repository

:CaseAutomation: Automated

:CaseComponent: Repositories

:team: Phoenix-content

:CaseImportance: High

"""

from broker import Broker
import pytest

from robottelo.config import settings
from robottelo.constants import (
    CONTAINER_REGISTRY_HUB,
    CONTAINER_UPSTREAM_NAME,
    DISTROS_SUPPORTED,
    FAKE_0_CUSTOM_PACKAGE,
)
from robottelo.hosts import ContentHost


@pytest.fixture
def lce(function_entitlement_manifest_org, target_sat):
    return target_sat.cli_factory.make_lifecycle_environment(
        {'organization-id': function_entitlement_manifest_org.id}
    )


@pytest.mark.tier4
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.parametrize('cdn', [True, False], ids=['cdn', 'no_cdn'])
@pytest.mark.parametrize('distro', DISTROS_SUPPORTED)
@pytest.mark.parametrize(
    'repos_collection',
    [
        {
            'SatelliteToolsRepository': {'cdn': 'cdn', 'distro': 'distro'},
            'YumRepository': {'url': settings.repos.yum_0.url},
            'DockerRepository': {
                'url': CONTAINER_REGISTRY_HUB,
                'upstream_name': CONTAINER_UPSTREAM_NAME,
            },
        }
    ],
    indirect=True,
)
def test_vm_install_package(repos_collection, function_entitlement_manifest_org, lce, distro, cdn):
    """Install a package with all supported distros and cdn / non-cdn variants

    :id: b2a6065a-69f6-4805-a28b-eaaa812e0f4b

    :parametrized: yes

    :expectedresults: Package is install is installed
    """
    if distro == 'rhel6':
        pytest.skip('rhel6 skipped until ELS subscriptions are in manifest.')
    # Create repos, content view, and activation key.
    repos_collection.setup_content(function_entitlement_manifest_org.id, lce['id'])
    with Broker(nick=distro, host_class=ContentHost) as host:
        # enable custom repos
        repos_collection.setup_virtual_machine(host, enable_custom_repos=True)
        # install a package from custom repo
        result = host.execute(f'yum -y install {FAKE_0_CUSTOM_PACKAGE}')
        assert result.status == 0
