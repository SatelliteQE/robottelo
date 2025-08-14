from datetime import datetime
from time import sleep

from fauxfactory import gen_string
import pytest

from robottelo.config import settings


def _create_viewer_user(target_sat, org, location, permission_name):
    """Helper function to create a user with specific view permissions.

    :param target_sat: The target satellite instance
    :param org: The organization to assign the user to
    :param location: The location to assign the user to
    :param permission_name: The name of the view permission to assign
    :return: Tuple of (user, password, token)
    """
    viewer_role = target_sat.api.Role().create()
    perm = target_sat.api.Permission().search(query={'search': f'name="{permission_name}"'})
    target_sat.api.Filter(permission=perm, role=viewer_role.id).create()
    viewer_password = gen_string('alphanumeric')
    viewer_pat = gen_string('alphanumeric')
    viewer = target_sat.api.User(
        admin=False,
        location=[location],
        organization=[org],
        role=[viewer_role],
        password=viewer_password,
    ).create()
    result = target_sat.cli.User.access_token(
        action="create", options={'name': viewer_pat, 'user-id': viewer.id}
    )
    viewer_pat_value = result[0]['message'].split(':')[-1]
    return (viewer, viewer_password, viewer_pat_value)


@pytest.fixture(scope='module')
def module_mcp_target_sat(module_target_sat):
    """A module-level fixture to provide an MCP server configured on Satellite"""
    container_name = f'mcp_server-{datetime.timestamp(datetime.now())}'
    result = module_target_sat.execute(
        f'firewall-cmd --permanent --add-port="{settings.foreman_mcp.port}/tcp"'
    )
    assert result.status == 0
    result = module_target_sat.execute('firewall-cmd --reload')
    assert result.status == 0
    module_target_sat.ensure_podman_installed()
    result = module_target_sat.execute(f'podman pull {settings.foreman_mcp.registry}')
    assert result.status == 0
    module_target_sat.execute(
        f'podman run --name {container_name} -d --pull=never -it -p {settings.foreman_mcp.port}:8080 \
            foreman-mcp-server --foreman-url https://{settings.server.hostname} --host 0.0.0.0 --no-verify-ssl'
    )
    sleep(20)
    result = module_target_sat.execute(
        f'podman inspect -f "{{{{.State.Status}}}}" {container_name}'
    )
    log = module_target_sat.execute(f'podman logs {container_name}')
    assert result.stdout.strip() == 'running', (
        f'failed to start container {container_name}: {log.stdout}'
        f'failed to start container {container_name}: {log.stderr}'
    )
    yield module_target_sat
    module_target_sat.execute(f'podman kill {container_name}')
    result = module_target_sat.execute(
        f'podman inspect -f "{{{{.State.Status}}}}" {container_name}'
    )
    assert result.stdout.strip() == 'exited', f'failed to clean up container {container_name}'


@pytest.fixture
def host_viewer_user(module_mcp_target_sat, module_org, module_location):
    """Creates a user with host viewing permissions only."""
    return _create_viewer_user(module_mcp_target_sat, module_org, module_location, 'view_hosts')


@pytest.fixture
def domain_viewer_user(module_mcp_target_sat, module_org, module_location):
    """Creates a user with domain viewing permissions only."""
    return _create_viewer_user(module_mcp_target_sat, module_org, module_location, 'view_domains')
