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
from robottelo.hosts import Satellite, get_sat_rhel_version

pytestmark = [pytest.mark.foremanctl, pytest.mark.build_sanity, pytest.mark.upgrade]

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
        r'journalctl --quiet --no-pager --boot --priority err -u "dynflow-sidekiq*" -u "foreman-proxy" -u "foreman" -u "httpd" -u "postgresql" -u "pulp-api" -u "pulp-content" -u "pulp-worker*" -u "redis" -u "candlepin"'
    )
    assert not result.stdout
    # no errors/failures in /var/log/httpd/*
    result = satellite.execute(r'grep -iR "error" /var/log/httpd/*')
    assert not result.stdout
    # # no errors/failures in /var/log/candlepin/*
    result = satellite.execute(r'grep -iR "error" /var/log/candlepin/*')
    assert not result.stdout
    httpd_log = satellite.execute('journalctl --unit=httpd')
    assert 'WARNING' not in httpd_log.stdout


@pytest.fixture(scope='module')
def module_sat_ready_rhel(request):
    with Broker(
        workflow=settings.server.deploy_workflows.os,
        deploy_rhel_version=get_sat_rhel_version().major,
        deploy_flavor=settings.flavors.default,
        deploy_network_type=settings.server.network_type,
        host_class=Satellite,
    ) as sat:
        sat.install_satellite_foremanctl(
            enable_fapolicyd=(request.param == 'fapolicyd'), enable_fips=(request.param == 'fips')
        )
        yield sat


@pytest.mark.first_sanity
@pytest.mark.parametrize('module_sat_ready_rhel', ['default', 'fips', 'fapolicyd'], indirect=True)
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


def test_positive_check_installer_hammer_ping(module_sat_ready_rhel):
    """Check if hammer ping reports all services as ok

    :id: 85fd4388-6d94-42f5-bed2-24be38e9f111

    :steps:
        1. Run the 'hammer ping' command on satellite.

    :expectedresults: All services are active (running)
    """
    response = module_sat_ready_rhel.api.Ping().search_json()
    assert response['status'] == 'ok'  # overall status
    services = response['services']
    assert all([service['status'] == 'ok' for service in services.values()]), (
        'Not all services seem to be up and running!'
    )
