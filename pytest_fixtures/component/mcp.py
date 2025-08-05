from datetime import datetime
from time import sleep

import pytest

from robottelo.config import settings


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
