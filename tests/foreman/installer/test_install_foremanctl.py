"""Smoke tests to check installation health

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: Critical

"""

from broker import Broker
import pytest

from robottelo.config import settings
from robottelo.constants import FOREMANCTL_PARAMETERS_FILE, FOREMANCTL_POSTGRESQL_TUNING_PROFILES
from robottelo.hosts import Satellite
from robottelo.utils.issue_handlers import is_open

pytestmark = [pytest.mark.foremanctl, pytest.mark.upgrade]

SATELLITE_SERVICES = [
    'candlepin',
    'dynflow-sidekiq@orchestrator',
    'dynflow-sidekiq@worker',
    'dynflow-sidekiq@worker-hosts-queue',
    'foreman-proxy',
    'foreman',
    'httpd',
    'postgresql',
    'pulp-api',
    'pulp-content',
    'pulp-worker@*',
    'redis',
]


def common_sat_install_assertions(satellite):
    # no errors/failures in journald
    result = satellite.execute(
        r'journalctl --quiet --no-pager --boot --grep ERROR -u "dynflow-sidekiq*" -u "foreman-proxy" -u "foreman" -u "httpd" -u "postgresql" -u "pulp-api" -u "pulp-content" -u "pulp-worker*" -u "redis" -u "candlepin"'
    )
    if is_open('SAT-21086'):
        assert not list(filter(lambda x: 'PG::' not in x, result.stdout.splitlines()))
    else:
        assert not result.stdout
    # no errors/failures in /var/log/httpd/*
    result = satellite.execute(r'grep -iR "error" /var/log/httpd/*')
    assert not result.stdout
    httpd_log = satellite.execute('journalctl --unit=httpd')
    assert 'WARNING' not in httpd_log.stdout


def assert_postgresql_tuning(sat, tuning):
    expected_pg = FOREMANCTL_POSTGRESQL_TUNING_PROFILES[tuning]
    for pg_setting, expected_value in expected_pg.items():
        result = sat.execute(
            f'podman exec postgresql psql -U postgres -t -A -c "show {pg_setting};"'
        )
        actual_value = result.stdout.strip()
        assert actual_value == expected_value, (
            f'Expected {pg_setting}={expected_value}, got {actual_value}'
        )


@pytest.fixture(scope='module')
def module_sat_ready_rhel(request):
    with Broker(
        workflow=settings.server.deploy_workflows.os,
        deploy_rhel_version=settings.server.version.rhel_version,
        deploy_flavor=settings.flavors.default,
        deploy_network_type=settings.server.network_type,
        host_class=Satellite,
    ) as sat:
        sat.install_satellite_foremanctl(
            enable_fapolicyd=(request.param == 'fapolicyd'), enable_fips=(request.param == 'fips')
        )
        yield sat


@pytest.fixture(scope='module')
def module_sat_foremanctl_tuning(request):
    # Deploy rhel to install foremanctl with different tuning profiles
    with Broker(
        workflow=settings.server.deploy_workflows.os,
        deploy_rhel_version=settings.server.version.rhel_version,
        deploy_flavor=settings.flavors.large,
        deploy_network_type=settings.server.network_type,
        host_class=Satellite,
    ) as sat:
        sat.install_satellite_foremanctl(
            parameters=[
                f'--tuning {request.param}',
            ]
        )
        yield sat


@pytest.mark.first_sanity
@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
def test_satellite_installation_with_foremanctl(module_sat_ready_rhel):
    """Run a basic Satellite installation

    :id: 661206f3-2eec-403c-af26-3c5cadcd5769

    :steps:
        1. Get RHEL Host
        2. Configure satellite repos
        3. Install satellite using foremanctl
        4. Run foremanctl deploy

    :expectedresults:
        1. foremanctl deploy runs successfully
        2. no unexpected errors in logs
    """
    common_sat_install_assertions(module_sat_ready_rhel)


@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
@pytest.mark.parametrize('service', SATELLITE_SERVICES)
def test_positive_check_installer_service_running(service, module_sat_ready_rhel):
    """Check if all Satellite services is running

    :id: 5389c174-7ab1-4e9d-b2aa-66d80fd6dc5h

    :steps:
        1. Verify a service is active with systemctl is-active

    :expectedresults: All Satellite services are active
    """
    is_active = module_sat_ready_rhel.execute(f'systemctl is-active {service}')
    status = module_sat_ready_rhel.execute(f'systemctl status {service}')
    assert is_active.status == 0, status.stdout


@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
def test_positive_check_installer_hammer_ping(module_sat_ready_rhel):
    """Check if hammer ping reports all services as ok

    :id: 85fd4388-6d94-42f5-bed2-24be38e9f111

    :steps:
        1. Run the 'hammer ping' command on satellite.

    :expectedresults: All services are active (running)
    """
    # check status reported by hammer ping command
    result = module_sat_ready_rhel.execute('hammer ping')
    assert result.status == 0
    for line in result.stdout.split('\n'):
        if 'Status' in line:
            assert 'ok' in line


@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
def test_foremanctl_deploy_reset_parameters(module_sat_ready_rhel):
    """Check if foremanctl deploy --reset parameters works

    :id: 661206f3-2eec-403c-af26-3c5caaaa5769

    :steps:
        1. Install Satellite with foremanctl deploy with parameters
        2. Verify foreman_puma_workers and pulp_worker_count are set to 2
        3. Reset foreman_puma_workers and pulp_worker_count
        4. Verify foreman_puma_workers and pulp_worker_count are not set

    :expectedresults:
        1. foremanctl deploy with parameters runs successfully
        2. foreman_puma_workers and pulp_worker_count are set to 2
        3. foreman_puma_workers and pulp_worker_count are not set
    """

    assert (
        module_sat_ready_rhel.execute(
            'foremanctl deploy --pulp-worker-count 2 --foreman-puma-workers 2',
            timeout='30m',
        ).status
        == 0
    )

    parameters_file = module_sat_ready_rhel.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert parameters_file.foreman_puma_workers == '2'
    assert parameters_file.pulp_worker_count == '2'

    assert (
        module_sat_ready_rhel.execute(
            'foremanctl deploy --reset-foreman-puma-workers --reset-pulp-worker-count'
        ).status
        == 0
    )

    parameters_file = module_sat_ready_rhel.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert 'foreman_puma_workers' not in parameters_file
    assert 'pulp_worker_count' not in parameters_file


@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
def test_foremanctl_deploy_certificate_cname(module_sat_ready_rhel):
    """Verify foremanctl deploy --certificate-cname adds CNAME to server certificate SANs

    :id: a5390e11-0e48-4a13-951f-749df8716e0c

    :steps:
        1. Run foremanctl deploy --certificate-cname with an additional DNS name
        2. Verify HTTPS connectivity using the CNAME with the self-signed CA

    :expectedresults:
        1. foremanctl deploy completes successfully
        2. HTTPS request via the CNAME returns HTTP 200 without certificate errors
    """
    satellite = module_sat_ready_rhel
    cname = f'cname.{satellite.hostname}'

    result = satellite.execute(
        f'foremanctl deploy --certificate-cname {cname}',
        timeout='10m',
    )
    assert result.status == 0, (
        f'foremanctl deploy with --certificate-cname failed:\n{result.stderr}'
    )

    result = satellite.execute(
        'curl --fail --output /dev/null --cacert /root/certificates/certs/ca.crt '
        f'--resolve "{cname}:443:127.0.0.1" '
        f'https://{cname}/users/login'
    )
    assert result.status == 0, f'HTTPS request to {cname} failed with output:\n{result.stderr}'


@pytest.mark.parametrize('module_sat_foremanctl_tuning', ['medium'], indirect=True)
def test_positive_foremanctl_tuning_profile(module_sat_foremanctl_tuning):
    """Verify foremanctl deploy with a tuning profile applies successfully

    :id: f55e8a14-eb93-4416-82ee-f389b3bbd768

    :steps:
        1. Install Satellite with foremanctl deploy with the 'medium' tuning profile
        2. Verify the tuning parameter is recorded in the parameters file
        3. Verify PostgreSQL settings match the medium profile
        4. Reset tuning back to 'default'
        5. Verify the default profile is recorded
        6. Verify PostgreSQL settings match the default profile

    :expectedresults:
        1. foremanctl deploy --tuning medium succeeds
        2. The parameters file records tuning as 'medium'
        3. PostgreSQL max_connections, shared_buffers, effective_cache_size match medium profile
        4. foremanctl deploy --tuning default succeeds
        5. The parameters file records tuning as 'default'
        6. PostgreSQL settings revert to default values

    :CaseAutomation: Automated
    """
    sat = module_sat_foremanctl_tuning
    # verify foremanctl is deployed with medium tuning profile
    parameters_file = sat.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert parameters_file.tuning == 'medium'
    assert_postgresql_tuning(sat, 'medium')

    # reset tuning back to default
    assert (
        sat.execute(
            'foremanctl deploy --reset-tuning',
            timeout='30m',
        ).status
        == 0
    )

    parameters_file = sat.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert 'tuning' not in parameters_file
    assert_postgresql_tuning(sat, 'default')
