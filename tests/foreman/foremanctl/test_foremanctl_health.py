"""Tests for foremanctl health subcommand checks

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: Critical
"""

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

pytestmark = [pytest.mark.foremanctl]

FOREMANCTL_HEALTH_CMD = 'foremanctl health'
FOREMANCTL_HEALTH_SKIP_TASKS_CMD = 'foremanctl health --skip-check-foreman-tasks'


@pytest.mark.e2e
def test_positive_health_check_all_pass(foremanctl_sat):
    """Verify foremanctl health passes on a healthy system

    :id: 317c3a55-a740-4120-84b1-da0a6e9056c7

    :steps:
        1. Run foremanctl health (skipping foreman tasks check
           to avoid pre-existing errored tasks failing the run)

    :expectedresults:
        1. All health checks pass with exit code 0.
        2. All services are reported as running.
        3. Foreman API responds with ok status.
        4. No duplicate permissions are found.

    :Verifies: SAT-44798
    """
    result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
    assert result.status == 0, (
        f'foremanctl health failed unexpectedly:\n{result.stdout}\n{result.stderr}'
    )
    assert 'failed=0' in result.stdout
    assert 'All services are running' in result.stdout
    assert 'Foreman tasks status: ok' in result.stdout
    assert 'duplicate permission(s) in database' not in result.stdout


def test_negative_health_check_services_detects_stopped_service(foremanctl_sat):
    """Verify check_services detects a stopped service

    :id: 805a1e78-3979-4c9d-aad6-8a0fea8156b5

    :steps:
        1. Stop the redis service
        2. Run foremanctl health
        3. Restart the redis service
        4. Verify satellite is healthy after recovery

    :expectedresults:
        1. Health check fails with exit code 2
        2. Output reports redis as inactive (dead)
        3. Satellite passes health check after redis restart

    :Verifies: SAT-44798
    """
    try:
        foremanctl_sat.execute('systemctl stop redis.service')
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 2, 'Health check should have failed with stopped redis'
        assert 'Some services are not running' in result.stdout
        assert 'redis: inactive (dead)' in result.stdout
    finally:
        foremanctl_sat.execute('systemctl start redis.service')
        wait_for(
            lambda: foremanctl_sat.execute('systemctl is-active redis.service').status == 0,
            timeout=30,
            delay=2,
        )
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 0, f'Satellite not healthy after redis restart:\n{result.stdout}'


def test_negative_health_check_foreman_api_detects_failure(foremanctl_sat):
    """Verify check_foreman_api detects API failure when foreman is stopped

    :id: 1c1338d8-b41b-4afb-9cee-daabc3f95e2e

    :steps:
        1. Stop the foreman service
        2. Run foremanctl health
        3. Restart the foreman service
        4. Verify satellite is healthy after recovery

    :expectedresults:
        1. Health check fails with exit code 2
        2. Output reports foreman service as failed
        3. Output shows API ping failure with 503 status code
        4. Satellite passes health check after foreman restart

    :Verifies: SAT-44798
    """
    try:
        foremanctl_sat.execute('systemctl stop foreman.service')
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 2, 'Health check should have failed with foreman stopped'
        assert 'Some services are not running' in result.stdout
        assert 'foreman: failed (failed)' in result.stdout
        assert 'Status code was 503' in result.stdout
    finally:
        foremanctl_sat.execute('systemctl start foreman.service')
        wait_for(
            lambda: foremanctl_sat.execute('hammer ping').status == 0,
            timeout=300,
            delay=10,
            handle_exception=True,
        )
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 0, f'Satellite not healthy after foreman restart:\n{result.stdout}'


def test_negative_health_check_foreman_tasks_detects_errors(foremanctl_sat):
    """Verify check_foreman_tasks detects errored tasks and that
    --skip-check-foreman-tasks allows bypassing the check

    :id: e73fd900-2bdc-4b0a-b538-7e938ceb0163

    :steps:
        1. Insert an errored foreman task into the database
        2. Run foremanctl health (without skip flag)
        3. Verify it detects the errored task
        4. Run foremanctl health with --skip-check-foreman-tasks
        5. Verify the check is skipped and health passes
        6. Clean up the errored task
        7. Run a final health check to verify the task is cleaned up

    :expectedresults:
        1. Without skip: health check fails, reports errored tasks
        2. With skip: health check passes

    :Verifies: SAT-44798
    """
    psql = 'podman exec postgresql psql -U foreman -d foreman -t -A -c'
    insert_sql = (
        "INSERT INTO foreman_tasks_tasks "
        "(id, type, label, state, result, started_at, ended_at, state_updated_at) "
        "VALUES (gen_random_uuid(), 'Actions::Test::Task', 'robottelo_test_errored_task', "
        "'paused', 'error', NOW(), NOW(), NOW())"
    )
    try:
        result = foremanctl_sat.execute(f'{psql} "{insert_sql}"')
        assert result.status == 0, f'Failed to insert test task: {result.stderr}'

        # Without skip — should fail
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_CMD, timeout='5m')
        assert result.status == 2, 'Health check should have failed with errored tasks'
        assert 'foreman tasks with errors' in result.stdout

        # With skip — should pass
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 0, (
            f'Health check failed even with --skip-check-foreman-tasks:\n'
            f'{result.stdout}\n{result.stderr}'
        )
    finally:
        delete_sql = "DELETE FROM foreman_tasks_tasks WHERE label = 'robottelo_test_errored_task'"
        foremanctl_sat.execute(f'{psql} "{delete_sql}"')
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_CMD, timeout='5m')
        assert result.status == 0, (
            f'Health check failed even after cleaning up the errored task:\n'
            f'{result.stdout}\n{result.stderr}'
        )


def test_negative_health_check_facts_count_detects_excess(foremanctl_sat):
    """Verify check_host_facts_count detects hosts exceeding the threshold
    and passes when hosts are within the threshold

    :id: c1ad6b71-85c0-4d14-b329-9daad9ceb6df

    :steps:
        1. Verify health passes with no hosts exceeding the facts threshold
        2. Upload 10002 facts for a host via the API (exceeding the
           default threshold of 10000)
        3. Run foremanctl health
        4. Clean up the test host
        5. Run a final health check to verify the host is cleaned up

    :expectedresults:
        1. Before: health check passes, no facts count warning
        2. After: health check fails, reports hosts exceeding the limit

    :Verifies: SAT-44798
    """
    # First verify the check passes with no excessive facts
    result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
    assert result.status == 0
    assert 'exceed the facts count limit' not in result.stdout

    # Now create a host with facts exceeding the threshold
    hostname = f'robottelo-facttest-{gen_string("alpha", 8).lower()}.example.com'
    facts = {
        'operatingsystem': 'RedHat',
        'operatingsystemrelease': '9.4',
    }
    facts.update({f'robottelo_fact_{i}': f'value_{i}' for i in range(1, 10001)})
    try:
        foremanctl_sat.api.Host().upload_facts(
            data={'name': hostname, 'certname': hostname, 'facts': facts}
        )
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 2, 'Health check should have failed with excess facts'
        assert 'exceed the facts count limit' in result.stdout
    finally:
        for host in foremanctl_sat.api.Host().search(query={'search': f'name={hostname}'}):
            host.delete()
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_CMD, timeout='5m')
        assert result.status == 0, (
            f'Health check failed even after cleaning up the host:\n'
            f'{result.stdout}\n{result.stderr}'
        )


def test_negative_health_check_duplicate_permissions_detects_dupes(foremanctl_sat):
    """Verify check_duplicate_permissions detects duplicate permissions

    :id: 8deaa9c6-aa9c-4482-851a-a0035642f9da

    :steps:
        1. Query an existing permission name from the database
        2. Insert a duplicate permission row
        3. Run foremanctl health
        4. Clean up the duplicate
        5. Run a final health check to verify the duplicate is cleaned up

    :expectedresults:
        1. Health check fails with exit code 2
        2. Output reports duplicate permissions with the permission name

    :Verifies: SAT-44798
    """
    psql = 'podman exec postgresql psql -U foreman -d foreman -t -A -c'

    # Get an existing permission to duplicate
    result = foremanctl_sat.execute(f'{psql} "SELECT name, resource_type FROM permissions LIMIT 1"')
    assert result.status == 0, f'Failed to get permission: {result.stderr}'
    perm_name, resource_type = result.stdout.splitlines()[0].strip().split('|')

    # Insert a duplicate
    insert_sql = (
        "INSERT INTO permissions (name, resource_type, created_at, updated_at) "
        f"VALUES ('{perm_name}', '{resource_type}', NOW(), NOW()) RETURNING id"
    )
    dup_id = None
    try:
        result = foremanctl_sat.execute(f'{psql} "{insert_sql}"')
        assert result.status == 0, f'Failed to insert duplicate permission: {result.stderr}'
        dup_id = result.stdout.splitlines()[0].strip()

        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 2, 'Health check should have failed with duplicate permissions'
        assert 'duplicate permission(s) in database' in result.stdout
        assert perm_name in result.stdout
    finally:
        if dup_id:
            foremanctl_sat.execute(f'{psql} "DELETE FROM permissions WHERE id = {dup_id}"')
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_CMD, timeout='5m')
        assert result.status == 0, (
            f'Health check failed even after cleaning up the duplicate permission:\n'
            f'{result.stdout}\n{result.stderr}'
        )
