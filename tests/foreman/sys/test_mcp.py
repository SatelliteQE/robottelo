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


@pytest.mark.asyncio
async def test_positive_call_mcp_server(module_mcp_target_sat):
    """Test that the MCP response matches with what is available on Satellite

    :id: 6f3c31c2-2f50-43ba-ac52-b3ebc6af4e45

    :expectedresults: MCP server is running and returns up to date data
    """
    async with Client(
        transport=StreamableHttpTransport(
            f'http://{settings.server.hostname}:{settings.foreman_mcp.port}/mcp',
            headers={
                'FOREMAN_USERNAME': settings.foreman_mcp.username,
                'FOREMAN_TOKEN': settings.foreman_mcp.password,
            },
        ),
    ) as client:
        result = await client.call_tool(
            'call_foreman_api_get', {'resource': 'hosts', 'action': 'index', 'params': {}}
        )
        assert result.data['message'] == "Action 'index' on resource 'hosts' executed successfully."
        hosts = module_mcp_target_sat.api.Host().search(query={'per_page': 'all'})
        hostnames = sorted([host.name for host in hosts])
        mcp_hostnames = sorted([host['name'] for host in result.data['response']['results']])
        assert hostnames == mcp_hostnames

        # add new host
        host = module_mcp_target_sat.api.Host().create()
        result = await client.call_tool(
            'call_foreman_api_get', {'resource': 'hosts', 'action': 'index', 'params': {}}
        )
        mcp_hostnames = [host['name'] for host in result.data['response']['results']]
        assert host.name in mcp_hostnames


@pytest.mark.asyncio
async def test_negative_call_mcp_server(module_mcp_target_sat):
    """Test that MCP server cannot alter Satellite

    :id: 7b643847-4aa0-42ec-92cd-873de853f1ba

    :expectedresults: non read-only actions are not allowed
    """
    async with Client(
        transport=StreamableHttpTransport(
            f'http://{settings.server.hostname}:{settings.foreman_mcp.port}/mcp',
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
