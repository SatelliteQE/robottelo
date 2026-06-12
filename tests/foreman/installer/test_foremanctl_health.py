"""Tests for foremanctl health subcommand checks

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: Critical
"""

from broker import Broker
from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.hosts import Satellite

pytestmark = [pytest.mark.foremanctl]

FOREMANCTL_HEALTH_CMD = 'foremanctl health'
FOREMANCTL_HEALTH_SKIP_TASKS_CMD = 'foremanctl health --skip-check-foreman-tasks'
PSQL_CMD = 'podman exec postgresql psql -U foreman -d foreman -t -A -c'


@pytest.fixture(scope='module')
def foremanctl_sat():
    """Provide a foremanctl-deployed Satellite via Broker."""
    with Broker(workflow='deploy-foreman', host_class=Satellite) as sat:
        yield sat


class TestForemanctlHealthPositive:
    """Verify all health checks pass on a healthy foremanctl-deployed system."""

    @pytest.mark.e2e
    def test_positive_health_check_all_pass(self, foremanctl_sat):
        """Verify foremanctl health passes on a healthy system

        :id: 3a1d8f2e-6b4c-4e9a-8d7f-1c2b3a4d5e6f

        :steps:
            1. Run foremanctl health (skipping foreman tasks check
               to avoid pre-existing errored tasks failing the run)

        :expectedresults:
            1. All health checks pass with exit code 0.
            2. All services are reported as running.
            3. Foreman API responds with ok status.
            4. No duplicate permissions are found.
        """
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 0, (
            f'foremanctl health failed unexpectedly:\n{result.stdout}\n{result.stderr}'
        )
        assert 'failed=0' in result.stdout
        assert 'All services are running' in result.stdout
        assert 'Foreman tasks status: ok' in result.stdout
        assert 'duplicate permission(s) in database' not in result.stdout


class TestForemanctlHealthCheckServices:
    """Test check_services by stopping/starting services."""

    @pytest.fixture
    def stopped_redis(self, foremanctl_sat):
        """Stop redis and restart after test."""
        foremanctl_sat.execute('systemctl stop redis.service')
        yield
        foremanctl_sat.execute('systemctl start redis.service')
        wait_for(
            lambda: foremanctl_sat.execute('systemctl is-active redis.service').status == 0,
            timeout=30,
            delay=2,
        )

    def test_negative_health_check_services_detects_stopped_service(
        self, foremanctl_sat, stopped_redis
    ):
        """Verify check_services detects a stopped service

        :id: 7e5b2c6a-af8d-4c3e-cb1a-5a6f7e8d9bac

        :steps:
            1. Stop the redis service
            2. Run foremanctl health

        :expectedresults:
            1. Health check fails with exit code != 0
            2. Output reports redis as inactive
        """
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status != 0, 'Health check should have failed with stopped redis'
        assert 'Some services are not running' in result.stdout
        assert 'redis' in result.stdout


class TestForemanctlHealthCheckForemanApi:
    """Test check_foreman_api by disrupting the Foreman service."""

    @pytest.fixture
    def stopped_foreman(self, foremanctl_sat):
        """Stop foreman service and restart after test."""
        foremanctl_sat.execute('systemctl stop foreman.service')
        yield
        foremanctl_sat.execute('systemctl start foreman.service')
        wait_for(
            lambda: foremanctl_sat.execute('hammer ping').status == 0,
            timeout=300,
            delay=10,
            handle_exception=True,
        )

    def test_negative_health_check_foreman_api_detects_failure(
        self, foremanctl_sat, stopped_foreman
    ):
        """Verify check_foreman_api detects API failure when foreman is stopped

        :id: 8f6c3d7b-ba9e-4d4f-dc2b-6b7a8f9eacbd

        :steps:
            1. Stop the foreman service
            2. Run foremanctl health

        :expectedresults:
            1. Health check fails with exit code != 0
            2. Output shows API ping failure (non-200 status code)
        """
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status != 0, 'Health check should have failed with foreman stopped'
        assert 'Status code was' in result.stdout or 'check_foreman_api' in result.stdout


class TestForemanctlHealthCheckForemanTasks:
    """Test check_foreman_tasks for errored task detection and skip functionality."""

    @pytest.fixture
    def errored_foreman_task(self, foremanctl_sat):
        """Insert an errored foreman task and clean up after test."""
        insert_sql = (
            "INSERT INTO foreman_tasks_tasks "
            "(id, type, label, state, result, started_at, ended_at, state_updated_at) "
            "VALUES (gen_random_uuid(), 'Actions::Test::Task', 'robottelo_test_errored_task', "
            "'paused', 'error', NOW(), NOW(), NOW())"
        )
        result = foremanctl_sat.execute(f'{PSQL_CMD} "{insert_sql}"')
        assert result.status == 0, f'Failed to insert test task: {result.stderr}'
        yield
        delete_sql = "DELETE FROM foreman_tasks_tasks WHERE label = 'robottelo_test_errored_task'"
        foremanctl_sat.execute(f'{PSQL_CMD} "{delete_sql}"')

    def test_negative_health_check_foreman_tasks_detects_errors(
        self, foremanctl_sat, errored_foreman_task
    ):
        """Verify check_foreman_tasks detects errored tasks

        :id: 9a7d4e8c-cbaf-4e5a-ed3c-7c8b9a0fbcde

        :steps:
            1. Insert an errored foreman task into the database
            2. Run foremanctl health (without --skip-check-foreman-tasks)

        :expectedresults:
            1. Health check fails with exit code != 0
            2. Output reports errored foreman tasks
        """
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_CMD, timeout='5m')
        assert result.status != 0, 'Health check should have failed with errored tasks'
        assert 'foreman tasks with errors' in result.stdout

    def test_positive_health_check_foreman_tasks_skip_flag(
        self, foremanctl_sat, errored_foreman_task
    ):
        """Verify --skip-check-foreman-tasks skips the errored tasks check

        :id: ab8e5f9d-dcba-4f6b-fe4d-8d9cab1acdfe

        :steps:
            1. Insert an errored foreman task into the database
            2. Run foremanctl health with --skip-check-foreman-tasks

        :expectedresults:
            1. Health check passes with exit code 0
            2. check_foreman_tasks is skipped
        """
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 0, (
            f'Health check failed even with --skip-check-foreman-tasks:\n'
            f'{result.stdout}\n{result.stderr}'
        )


class TestForemanctlHealthCheckHostFactsCount:
    """Test check_host_facts_count threshold detection."""

    @pytest.fixture
    def host_with_many_facts(self, foremanctl_sat):
        """Create a host with facts exceeding the default threshold (10000)
        via the Foreman upload_facts API.
        """
        hostname = f'robottelo-facttest-{gen_string("alpha", 8).lower()}.example.com'
        facts = {
            'operatingsystem': 'RedHat',
            'operatingsystemrelease': '9.4',
        }
        facts.update({f'robottelo_fact_{i}': f'value_{i}' for i in range(1, 10001)})
        foremanctl_sat.api.Host().upload_facts(
            data={'name': hostname, 'certname': hostname, 'facts': facts}
        )
        yield hostname
        # Cleanup: delete the host created by upload_facts
        hosts = foremanctl_sat.api.Host().search(query={'search': f'name={hostname}'})
        if hosts:
            hosts[0].delete()

    def test_negative_health_check_facts_count_detects_excess(
        self, foremanctl_sat, host_with_many_facts
    ):
        """Verify check_host_facts_count detects hosts exceeding the threshold

        :id: bc9f6a0e-edcb-4a7c-af5e-9eabcb2bdefa

        :steps:
            1. Upload 10002 facts for a host via the API (exceeding the
               default threshold of 10000)
            2. Run foremanctl health

        :expectedresults:
            1. Health check fails with exit code != 0
            2. Output reports hosts exceeding the facts count limit
        """
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status != 0, 'Health check should have failed with excess facts'
        assert 'exceed the facts count limit' in result.stdout

    def test_positive_health_check_facts_count_passes_within_threshold(self, foremanctl_sat):
        """Verify check_host_facts_count passes when all hosts are within threshold

        :id: cdaa7b1f-fedc-4b8d-ba6f-afbcdc3ceaab

        :steps:
            1. Ensure no hosts exceed the default facts threshold (10000)
            2. Run foremanctl health

        :expectedresults: check_host_facts_count passes or is skipped (no fact data).
        """
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status == 0
        assert 'exceed the facts count limit' not in result.stdout


class TestForemanctlHealthCheckDuplicatePermissions:
    """Test check_duplicate_permissions detection."""

    @pytest.fixture
    def duplicate_permissions(self, foremanctl_sat):
        """Insert duplicate permissions and clean up after test."""
        # Get the name of the first permission to duplicate
        get_perm_sql = "SELECT name, resource_type FROM permissions LIMIT 1"
        result = foremanctl_sat.execute(f'{PSQL_CMD} "{get_perm_sql}"')
        assert result.status == 0, f'Failed to get permission: {result.stderr}'
        perm_name, resource_type = result.stdout.strip().split('|')

        # Insert a duplicate
        insert_sql = (
            f"INSERT INTO permissions (name, resource_type, created_at, updated_at) "
            f"VALUES ('{perm_name}', '{resource_type}', NOW(), NOW()) RETURNING id"
        )
        result = foremanctl_sat.execute(f'{PSQL_CMD} "{insert_sql}"')
        assert result.status == 0, f'Failed to insert duplicate permission: {result.stderr}'
        dup_id = result.stdout.splitlines()[0].strip()
        yield {'name': perm_name, 'id': dup_id}
        # Cleanup
        foremanctl_sat.execute(f'{PSQL_CMD} "DELETE FROM permissions WHERE id = {dup_id}"')

    def test_negative_health_check_duplicate_permissions_detects_dupes(
        self, foremanctl_sat, duplicate_permissions
    ):
        """Verify check_duplicate_permissions detects duplicate permissions

        :id: deab8c2a-afed-4c9e-cb7a-bacdde4dfbbc

        :steps:
            1. Insert a duplicate permission into the database
            2. Run foremanctl health

        :expectedresults:
            1. Health check fails with exit code != 0
            2. Output reports duplicate permissions with the permission name
        """
        result = foremanctl_sat.execute(FOREMANCTL_HEALTH_SKIP_TASKS_CMD, timeout='5m')
        assert result.status != 0, 'Health check should have failed with duplicate permissions'
        assert 'duplicate permission' in result.stdout.lower()
        assert duplicate_permissions['name'] in result.stdout
