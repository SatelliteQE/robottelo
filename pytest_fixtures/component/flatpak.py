# Flatpak-related fixtures
from box import Box
import pytest

from robottelo.config import settings
from robottelo.constants import FLATPAK_REMOTES
from robottelo.utils.datafactory import gen_string


@pytest.fixture
def function_flatpak_remote(request, target_sat, function_org):
    """Create flatpak remote, scan it and return both entities"""
    remote = FLATPAK_REMOTES[getattr(request, 'param', 'Fedora')]
    create_opts = {
        'organization-id': function_org.id,
        'url': remote['url'],
        'name': gen_string('alpha'),
    }
    if remote['authenticated']:
        create_opts['username'] = settings.container_repo.registries.redhat.username
        create_opts['token'] = settings.container_repo.registries.redhat.password
    fr = target_sat.cli.FlatpakRemote().create(create_opts)

    target_sat.cli.FlatpakRemote().scan({'id': fr['id']})
    scanned_repos = target_sat.cli.FlatpakRemote().repository_list({'flatpak-remote-id': fr['id']})
    assert len(scanned_repos), 'No repositories scanned'

    return Box(remote=fr, repos=scanned_repos)


@pytest.fixture
def function_host_cleanup(target_sat, module_flatpak_contenthost):
    """Cleans up the flatpak contenthost so it can be re-registered with different org"""
    res = target_sat.api.Host().search(
        query={'search': f'name="{module_flatpak_contenthost.hostname}"'}
    )
    if len(res) == 1:
        res[0].delete()
