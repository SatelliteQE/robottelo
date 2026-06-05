from broker import Broker
from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import FAKE_9_YUM_OUTDATED_PACKAGES, PODMAN_AUTHFILE_PATH
from robottelo.hosts import ContentHost


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


def _setup_mcp_server(target_sat, image_settings):
    """Helper function to set up MCP server.

    :param target_sat: The target satellite instance
    :param image_settings: The container image settings
    :return: String container_id
    """
    if not target_sat.network_type.has_ipv4:
        target_sat.enable_ipv6_dnf_and_rhsm_proxy()
        target_sat.enable_ipv6_system_proxy()
    image_name = image_settings.image_path.split('/')[-1]
    assert (
        target_sat.execute(
            f'firewall-cmd --permanent --add-port="{settings.foreman_mcp.port}/tcp"'
        ).status
        == 0
    )
    assert target_sat.execute('firewall-cmd --reload').status == 0
    target_sat.ensure_podman_installed()
    authfile_arg = ''
    network_arg = '--network ipv6' if not target_sat.network_type.has_ipv4 else ''
    ca_mountpoint = '/app/ca.pem'

    if image_settings.get('registry_username') and image_settings.get('registry_password'):
        target_sat.podman_login(
            image_settings.registry_username,
            image_settings.registry_password,
            image_settings.registry_url,
        )
        authfile_arg = f'--authfile {PODMAN_AUTHFILE_PATH}'

    if not target_sat.network_type.has_ipv4:
        target_sat.execute('podman network create --ipv6 ipv6')

    pull_cmd = f'podman pull {authfile_arg} {image_settings.registry_url}/{image_settings.image_path}:{image_settings.image_tag}'
    assert target_sat.execute(pull_cmd).status == 0

    run_cmd = (
        f'podman run {network_arg} '
        f'-d --pull=never -it -p {settings.foreman_mcp.port}:8080 '
        f'-v /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:{ca_mountpoint}:ro,Z '
        f'{image_name}:{image_settings.image_tag} '
        f'--foreman-url https://{target_sat.hostname} --host 0.0.0.0 '
        f'--allowed-rex-features "katello_errata_install,katello_package_install" '
        f'--allowed-cv-actions "publish,promote,incremental_update"'
    )
    run_result = target_sat.execute(run_cmd)
    assert run_result.status == 0
    container_id = run_result.stdout.strip()[:12]
    wait_for(
        lambda: target_sat.execute(f'curl localhost:{settings.foreman_mcp.port}/mcp/').status == 0,
        timeout=60,
        delay=2,
    )
    result = target_sat.execute(f'podman inspect -f "{{{{.State.Status}}}}" {container_id}')
    log = target_sat.execute(f'podman logs {container_id}')
    assert result.stdout.strip() == 'running', (
        f'failed to start container {container_id}: {log.stdout}'
        f'failed to start container {container_id}: {log.stderr}'
    )
    return container_id


def _cleanup_mcp_server(target_sat, image_settings, container_id):
    """Helper function to clean up MCP server.

    :param target_sat: The target satellite instance
    :param image_settings: The container image settings
    :param container_id: ID of the container to clean up
    """
    target_sat.execute(f'podman kill {container_id}')
    result = target_sat.execute(f'podman inspect -f "{{{{.State.Status}}}}" {container_id}')
    assert result.stdout.strip() == 'exited', f'failed to clean up container {container_id}'
    target_sat.execute(f'podman rm {container_id}')
    target_sat.execute(
        f'podman rmi {image_settings.registry_url}/{image_settings.image_path}:{image_settings.image_tag}'
    )
    if not target_sat.network_type.has_ipv4:
        target_sat.execute('podman network rm ipv6')


@pytest.fixture(scope='module')
def module_target_sat_foreman_mcp(module_target_sat):
    """A module-level fixture to provide an MCP server configured on Satellite"""
    image_settings = settings.foreman_mcp.get(
        'upstream' if module_target_sat.is_upstream or module_target_sat.is_stream else 'stage'
    )
    container_id = _setup_mcp_server(module_target_sat, image_settings)
    yield module_target_sat
    _cleanup_mcp_server(module_target_sat, image_settings, container_id)


@pytest.fixture
def host_viewer_user(module_target_sat_foreman_mcp, module_org, module_location):
    """Creates a user with host viewing permissions only."""
    return _create_viewer_user(
        module_target_sat_foreman_mcp, module_org, module_location, 'view_hosts'
    )


@pytest.fixture
def domain_viewer_user(module_target_sat_foreman_mcp, module_org, module_location):
    """Creates a user with domain viewing permissions only."""
    return _create_viewer_user(
        module_target_sat_foreman_mcp, module_org, module_location, 'view_domains'
    )


@pytest.fixture
def incupd_host(
    request,
    module_target_sat_foreman_mcp,
    function_org,
    function_promoted_cv,
    function_ak_with_cv,
):
    with Broker(
        host_class=ContentHost,
        workflow='deploy-rhel',
        deploy_network_type=settings.content_host.network_type,
        deploy_rhel_version=settings.content_host.default_rhel_version,
    ) as host:
        result = host.register(
            function_org,
            None,
            function_ak_with_cv.name,
            module_target_sat_foreman_mcp,
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        # install outdated 'bear' package to have something to update
        client_pkg = f'{settings.repos.yum_9.url}/{FAKE_9_YUM_OUTDATED_PACKAGES[0]}.rpm'
        result = host.execute(f'dnf -y install {client_pkg}')
        assert result.status == 0, f'Failed to install package: {result.stderr}'
        yield host
