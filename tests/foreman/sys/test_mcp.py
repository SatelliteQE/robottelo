"""Test class for MCP server

:CaseAutomation: Automated

:CaseComponent: API

:Team: Endeavour

:Requirement: API

:CaseImportance: High

"""

from fastmcp import Client
import pytest

from robottelo.config import settings


@pytest.mark.asyncio
async def test_positive_call_mcp_server(module_mcp_target_sat):
    """Test that the MCP response matches with what is available on Satellite

    :id: 6f3c31c2-2f50-43ba-ac52-b3ebc6af4e45

    :expectedresults: MCP server is running
    """
    async with Client(
        f'http://{settings.foreman_mcp.hostname}:{settings.foreman_mcp.port}/mcp', timeout=30
    ) as client:
        result = await client.call_tool(
            'call_foreman_api', {'resource': 'hosts', 'action': 'index', 'params': {}}
        )
        assert result.data['message'] == "Action 'index' on resource 'hosts' executed successfully."
        hosts = module_mcp_target_sat.api.Host().search(query={'per_page': 'all'})
        hostnames = [host.name for host in hosts]
        mcp_hostnames = [host['name'] for host in result.data['response']['results']]
        assert len(hostnames) == len(mcp_hostnames)
        assert set(hostnames) == set(mcp_hostnames)
