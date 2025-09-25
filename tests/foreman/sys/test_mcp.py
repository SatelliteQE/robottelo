"""Test class for MCP server

:CaseAutomation: Automated

:CaseComponent: API

:Team: Endeavour

:Requirement: API

:CaseImportance: High

"""

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import pytest

from robottelo.config import settings
from robottelo.enums import NetworkType


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'mcp_server',
    ['module_mcp_target_sat', 'module_downstream_mcp_target_sat'],
    ids=['upstream', 'downstream'],
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
    mcp_settings = settings.get(
        'foreman_mcp_downstream'
        if mcp_server == 'module_downstream_mcp_target_sat'
        else 'foreman_mcp'
    )
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
async def test_negative_call_mcp_server(module_mcp_target_sat):
    """Test that MCP server cannot alter Satellite

    :id: 7b643847-4aa0-42ec-92cd-873de853f1ba

    :expectedresults: non read-only actions are not allowed
    """
    async with Client(
        transport=StreamableHttpTransport(
            f'http://{module_mcp_target_sat.hostname}:{settings.foreman_mcp.port}/mcp',
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
    request, module_mcp_target_sat, user_fixture, allowed_resource, denied_resource, auth_type
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
            f'http://{module_mcp_target_sat.hostname}:{settings.foreman_mcp.port}/mcp',
            headers={
                'FOREMAN_USERNAME': user.login,
                'FOREMAN_TOKEN': auth_value,
            },
        ),
    ) as client:
        result = await client.call_tool(
            'call_foreman_api_get', {'resource': allowed_resource, 'action': 'index', 'params': {}}
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
