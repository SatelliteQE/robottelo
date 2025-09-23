from datetime import datetime

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

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


def _setup_mcp_server(target_sat, settings_obj, is_downstream=False):
    """Helper function to set up MCP server.

    :param target_sat: The target satellite instance
    :param settings_obj: The settings object (foreman_mcp or foreman_mcp_downstream)
    :param is_downstream: Whether this is a downstream setup
    :return: Container name for cleanup
    """
    if not target_sat.network_type.has_ipv4:
        target_sat.enable_ipv6_dnf_and_rhsm_proxy()
        target_sat.enable_ipv6_system_proxy()
    container_name = (
        f'mcp_server{"_downstream" if is_downstream else ""}-{datetime.timestamp(datetime.now())}'
    )
    image_name = settings_obj.image_path.split('/')[-1]
    assert (
        target_sat.execute(f'firewall-cmd --permanent --add-port="{settings_obj.port}/tcp"').status
        == 0
    )
    assert target_sat.execute('firewall-cmd --reload').status == 0
    target_sat.ensure_podman_installed()
    if is_downstream:
        target_sat.podman_login(
            settings_obj.registry_stage_username,
            settings_obj.registry_stage_password,
            settings_obj.registry_stage,
        )
        registry = settings_obj.registry_stage
        ca_mountpoint = '/opt/app-root/src/ca.pem'
    else:
        registry = settings_obj.registry
        ca_mountpoint = '/app/ca.pem'
    if not target_sat.network_type.has_ipv4:
        target_sat.execute('podman network create --ipv6 ipv6')
    assert target_sat.execute(f'podman pull {registry}/{settings_obj.image_path}').status == 0
    target_sat.execute(
        f'podman run {"--network ipv6" if not target_sat.network_type.has_ipv4 else ""} '
        f'-v /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:{ca_mountpoint}:ro,Z '
        f'--name {container_name} -d --pull=never -it -p {settings_obj.port}:8080 '
        f'{image_name} --foreman-url https://{target_sat.hostname} --host 0.0.0.0'
    )
    wait_for(
        lambda: target_sat.execute(f'curl localhost:{settings_obj.port}/mcp/').status == 0,
        timeout=60,
        delay=2,
    )
    result = target_sat.execute(f'podman inspect -f "{{{{.State.Status}}}}" {container_name}')
    log = target_sat.execute(f'podman logs {container_name}')
    assert result.stdout.strip() == 'running', (
        f'failed to start container {container_name}: {log.stdout}'
        f'failed to start container {container_name}: {log.stderr}'
    )
    return container_name


def _cleanup_mcp_server(target_sat, container_name, registry, image_path):
    """Helper function to clean up MCP server.

    :param target_sat: The target satellite instance
    :param container_name: Name of the container to clean up
    :param registry: Registry path
    :param image_path: Image path
    """
    target_sat.execute(f'podman kill {container_name}')
    result = target_sat.execute(f'podman inspect -f "{{{{.State.Status}}}}" {container_name}')
    assert result.stdout.strip() == 'exited', f'failed to clean up container {container_name}'
    target_sat.execute(f'podman rm {container_name}')
    target_sat.execute(f'podman rmi {registry}/{image_path}')
    if not target_sat.network_type.has_ipv4:
        target_sat.execute('podman network rm ipv6')


@pytest.fixture(scope='module')
def module_mcp_target_sat(module_target_sat):
    """A module-level fixture to provide an MCP server configured on Satellite"""
    container_name = _setup_mcp_server(module_target_sat, settings.foreman_mcp)
    yield module_target_sat
    _cleanup_mcp_server(
        module_target_sat,
        container_name,
        settings.foreman_mcp.registry,
        settings.foreman_mcp.image_path,
    )


@pytest.fixture(scope='module')
def module_downstream_mcp_target_sat(module_target_sat):
    """A module-level fixture to provide an downstream distribution of MCP server configured on Satellite"""
    container_name = _setup_mcp_server(
        module_target_sat, settings.foreman_mcp_downstream, is_downstream=True
    )
    yield module_target_sat
    _cleanup_mcp_server(
        module_target_sat,
        container_name,
        settings.foreman_mcp_downstream.registry_stage,
        settings.foreman_mcp_downstream.image_path,
    )


@pytest.fixture
def host_viewer_user(module_mcp_target_sat, module_org, module_location):
    """Creates a user with host viewing permissions only."""
    return _create_viewer_user(module_mcp_target_sat, module_org, module_location, 'view_hosts')


@pytest.fixture
def domain_viewer_user(module_mcp_target_sat, module_org, module_location):
    """Creates a user with domain viewing permissions only."""
    return _create_viewer_user(module_mcp_target_sat, module_org, module_location, 'view_domains')
