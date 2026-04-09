"""Test class for MCP server

:CaseAutomation: Automated

:CaseComponent: MCP

:Team: Endeavour

:Requirement: MCP

:CaseImportance: High

"""

from datetime import UTC, datetime
from urllib.parse import quote

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import pytest

from robottelo.config import settings
from robottelo.constants import FAKE_9_YUM_UPDATED_PACKAGES
from robottelo.enums import NetworkType


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'mcp_server',
    [
        'module_target_sat_foreman_mcp',
    ],
    ids=['upstream'],
)
@pytest.mark.skipif(
    settings.server.network_type == NetworkType.IPV6,
    reason='IPV6 scenario is not essential for this case',
)
async def test_positive_call_mcp_server(request, mcp_server):
    """Test that the MCP response matches with what is available on Satellite

    :id: 6f3c31c2-2f50-43ba-ac52-b3ebc6af4e45

    :expectedresults: MCP server is running and returns up to date data
    """
    target_sat = request.getfixturevalue(mcp_server)
    mcp_settings = settings.get(mcp_server.removeprefix('module_target_sat_'))
    async with Client(
        transport=StreamableHttpTransport(
            f'http://{target_sat.hostname}:{mcp_settings.port}/mcp',
            headers={
                'FOREMAN_USERNAME': mcp_settings.username,
                'FOREMAN_TOKEN': mcp_settings.password,
            },
        ),
    ) as client:
        result = await client.call_tool(
            'call_foreman_api_get', {'resource': 'hosts', 'action': 'index', 'params': {}}
        )
        assert result.data['message'] == "Action 'index' on resource 'hosts' executed successfully."
        hosts = target_sat.api.Host().search(query={'per_page': 'all'})
        hostnames = sorted([host.name for host in hosts])
        mcp_hostnames = sorted([host['name'] for host in result.data['response']['results']])
        assert hostnames == mcp_hostnames

        # add new host
        host = target_sat.api.Host().create()
        result = await client.call_tool(
            'call_foreman_api_get', {'resource': 'hosts', 'action': 'index', 'params': {}}
        )
        mcp_hostnames = [host['name'] for host in result.data['response']['results']]
        assert host.name in mcp_hostnames


@pytest.mark.asyncio
@pytest.mark.skipif(
    settings.server.network_type == NetworkType.IPV6,
    reason='IPV6 scenario is not essential for this case',
)
async def test_negative_call_mcp_server(module_target_sat_foreman_mcp):
    """Test that MCP server cannot alter Satellite

    :id: 7b643847-4aa0-42ec-92cd-873de853f1ba

    :expectedresults: non read-only actions are not allowed
    """
    async with Client(
        transport=StreamableHttpTransport(
            f'http://{module_target_sat_foreman_mcp.hostname}:{settings.foreman_mcp.port}/mcp',
            headers={
                'FOREMAN_USERNAME': settings.foreman_mcp.username,
                'FOREMAN_TOKEN': settings.foreman_mcp.password,
            },
        ),
    ) as client:
        result = await client.call_tool(
            'call_foreman_api_get',
            {
                'resource': 'organizations',
                'action': 'create',
                'params': {'name': 'test_organization'},
            },
        )
        assert (
            result.data['message']
            == "Failed to execute action 'create' on resource 'organizations'"
        )
        assert (
            result.data['error']
            == "Action 'create' on resource 'organizations' is not allowed: POST method is not allowed, expected GET."
        )


@pytest.mark.asyncio
@pytest.mark.skipif(
    settings.server.network_type == NetworkType.IPV6,
    reason='IPV6 scenario is not essential for this case',
)
@pytest.mark.parametrize(
    ('user_fixture', 'allowed_resource', 'denied_resource', 'auth_type'),
    [
        ('host_viewer_user', 'hosts', 'domains', 'password'),
        ('host_viewer_user', 'hosts', 'domains', 'token'),
        ('domain_viewer_user', 'domains', 'hosts', 'password'),
        ('domain_viewer_user', 'domains', 'hosts', 'token'),
    ],
    ids=[
        'host_viewer_user_password',
        'host_viewer_user_token',
        'domain_viewer_user_password',
        'domain_viewer_user_token',
    ],
)
async def test_positive_mcp_user_view_permissions(
    request,
    module_target_sat_foreman_mcp,
    user_fixture,
    allowed_resource,
    denied_resource,
    auth_type,
):
    """Test that users with different view permissions can only view their authorized resources through MCP

    :id: 9f3c31c2-2f50-43ba-ac52-b3ebc6af4e46

    :expectedresults: Users can only view resources they have view permissions for using both password
        and token authentication
    """
    user, password, token = request.getfixturevalue(user_fixture)
    auth_value = password if auth_type == 'password' else token
    async with Client(
        transport=StreamableHttpTransport(
            f'http://{module_target_sat_foreman_mcp.hostname}:{settings.foreman_mcp.port}/mcp',
            headers={
                'FOREMAN_USERNAME': user.login,
                'FOREMAN_TOKEN': auth_value,
            },
        ),
    ) as client:
        result = await client.call_tool(
            'call_foreman_api_get', {'resource': allowed_resource, 'action': 'index', 'params': {}}
        )
        if 'error' in result.data and 'Max retries exceeded' in result.data['error']:
            result = await client.call_tool(
                'call_foreman_api_get',
                {'resource': allowed_resource, 'action': 'index', 'params': {}},
            )
        assert (
            result.data['message']
            == f"Action 'index' on resource '{allowed_resource}' executed successfully."
        )

        result = await client.call_tool(
            'call_foreman_api_get', {'resource': denied_resource, 'action': 'index', 'params': {}}
        )
        assert (
            f"Failed to execute action 'index' on resource '{denied_resource}'"
            in result.data['message']
        )
        assert result.data['response']['error']['message'] == 'Access denied'


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_host_incremental_update(
    module_target_sat_foreman_mcp,
    function_org,
    function_lce,
    function_promoted_cv,
    incupd_host,
):
    """Scenario to test host incremental updates through MCP

    :id: 132f2200-2830-11f1-b673-183d2dca5728

    :expectedresults: A host is updated incrementally through MCP server
    """
    async with Client(
        transport=StreamableHttpTransport(
            f'http://{module_target_sat_foreman_mcp.hostname}:{settings.foreman_mcp.port}/mcp',
            headers={
                'FOREMAN_USERNAME': settings.foreman_mcp.username,
                'FOREMAN_TOKEN': settings.foreman_mcp.password,
            },
        ),
    ) as client:
        sat = module_target_sat_foreman_mcp
        cv = function_promoted_cv
        repo = sat.api.Repository(
            product=sat.api.Product(organization=function_org).create(),
            url=settings.repos.yum_9.url,
        ).create()
        repo.sync()
        repo = repo.read()
        cv.repository = [repo]
        cv.update(['repository'])
        # filter out erratum containing update for 'bear' package
        cvf = sat.api.ErratumContentViewFilter(content_view=cv, inclusion=False).create()
        sat.api.ContentViewFilterRule(
            content_view_filter=cvf,
            errata=quote(settings.repos.yum_9.errata[2]),
        ).create()
        # publish CV using MCP
        result = await client.call_tool(
            'publish_content_view',
            {'content_view_id': cv.id},
        )
        assert result.data['message'] == f'Content view {cv.id} publish triggered successfully.'
        cv = cv.read()
        cvv = cv.version[0]
        assert result.data['response']['input']['content_view_version_id'] == cvv.id
        # wait for publish task to complete
        sat.wait_for_tasks(
            f'id = {result.data["response"]["id"]}',
            search_rate=5,
        )
        # promote CV using MCP
        result = await client.call_tool(
            'promote_content_view_version',
            {
                'content_view_version_id': cvv.id,
                'environment_ids': [function_lce.id],
                'force': True,
            },
        )
        assert (
            result.data['message']
            == f'Content view version {cvv.id} promotion triggered successfully.'
        )
        cvv = cvv.read()
        assert function_lce.name in result.data['response']['input']['environments']
        # wait for promote task to complete
        sat.wait_for_tasks(
            f'id = {result.data["response"]["id"]}',
            search_rate=5,
        )
        # create CV incremental update using MCP
        result = await client.call_tool(
            'incremental_content_view_update',
            {
                'content_view_version_environments': [
                    {'content_view_version_id': cvv.id, 'environment_ids': [function_lce.id]}
                ],
                'errata_ids': [settings.repos.yum_9.errata[2]],
            },
        )
        assert result.data['message'] == 'Incremental content view update triggered successfully.'
        cv = cv.read()
        cvv_inc = cv.version[0]
        assert result.data['response']['input']['errata_ids'] == [settings.repos.yum_9.errata[2]]
        assert result.data['response']['input']['version_outputs'][0]['version_id'] == cvv_inc.id
        # wait for incremental update task to complete
        sat.wait_for_tasks(
            f'id = {result.data["response"]["id"]}',
            search_rate=5,
        )
        # enable repository on the host to have the new erratum applicable
        repo_label = f'{function_org.label}_{repo.product.read().label}_{repo.label}'
        repo_enable_time = (
            datetime.now(UTC).replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S UTC')
        )
        cmd = incupd_host.execute(f'subscription-manager repos --enable {repo_label}')
        assert cmd.status == 0, f'Failed to enable repository {repo_label} on host: {cmd.stderr}'
        # wait for applicability generation for the host to complete
        sat.wait_for_tasks(
            f'action = "Bulk generate applicability for host {incupd_host.hostname}" '
            f'and started_at > "{repo_enable_time}"'
        )
        # find applicable hosts for the erratum using MCP
        result = await client.call_tool(
            'call_foreman_api_get',
            {
                'resource': 'hosts',
                'action': 'index',
                'params': {'search': f'installable_errata = {settings.repos.yum_9.errata[2]}'},
            },
        )
        assert result.data['message'] == "Action 'index' on resource 'hosts' executed successfully."
        assert incupd_host.hostname in [h['name'] for h in result.data['response']['results']], (
            'The erratum is not applicable to the host after incremental update'
        )
        # apply erratum by REX using MCP
        result = await client.call_tool(
            'trigger_remote_execution_job',
            {
                'feature': 'katello_errata_install',
                'search_query': f'installable_errata = {settings.repos.yum_9.errata[2]}',
                'inputs': {'errata': settings.repos.yum_9.errata[2]},
            },
        )
        assert result.data['message'] == "Remote execution job triggered successfully."
        # wait for remote execution task to complete
        sat.wait_for_tasks(
            f'id = {result.data["task_id"]}',
            search_rate=5,
        )
        # verify that the erratum has been installed on the host
        cmd = incupd_host.execute(f'rpm -q {FAKE_9_YUM_UPDATED_PACKAGES[0].split("-")[0]}')
        assert f'{FAKE_9_YUM_UPDATED_PACKAGES[0]}' in cmd.stdout, (
            'Failed to install the erratum on the host'
        )
