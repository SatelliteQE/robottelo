"""Test module for satellite-maintain service functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Rocket

:CaseImportance: Critical

"""

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import (
    HAMMER_CONFIG,
    MAINTAIN_HAMMER_YML,
    SATELLITE_ANSWER_FILE,
)
from robottelo.hosts import Satellite

IOP_SERVICES = [
    'iop-core-engine.service',
    'iop-core-gateway.service',
    'iop-core-host-inventory-api.service',
    'iop-core-host-inventory-migrate.service',
    'iop-core-host-inventory.service',
    'iop-core-ingress.service',
    'iop-core-kafka.service',
    'iop-core-puptoo.service',
    'iop-core-yuptoo.service',
    'iop-service-advisor-backend-api.service',
    'iop-service-advisor-backend-service.service',
    'iop-service-remediations-api.service',
    'iop-service-vmaas-reposcan.service',
    'iop-service-vmaas-webapp-go.service',
    'iop-service-vuln-dbupgrade.service',
    'iop-service-vuln-evaluator-recalc.service',
    'iop-service-vuln-evaluator-upload.service',
    'iop-service-vuln-grouper.service',
    'iop-service-vuln-listener.service',
    'iop-service-vuln-manager.service',
    'iop-service-vuln-taskomatic.service',
]

SATELLITE_SERVICES = [
    'dynflow-sidekiq@.service',
    'foreman-proxy.service',
    'foreman.service',
    'httpd.service',
    'postgresql.service',
    'pulpcore-api.service',
    'pulpcore-content.service',
    'pulpcore-worker@.service',
    'redis.service',
    'tomcat.service',
]

CAPSULE_SERVICES = [
    'foreman-proxy.service',
    'httpd.service',
    'postgresql.service',
    'pulpcore-api.service',
    'pulpcore-content.service',
    'pulpcore-worker@.service',
    'redis.service',
]


@pytest.fixture
def setup_test_positive_service_restart(request, sat_maintain):
    """Setup/teardown fixture used by test_positive_service_restart"""
    flag = 'initial_admin_password'
    sat_maintain.execute(
        f'sed -i "s/{flag}: {settings.server.admin_password}/{flag}: invalid/g" '
        f'{SATELLITE_ANSWER_FILE}'
    )
    sat_maintain.execute(f'mv {HAMMER_CONFIG} /tmp/foreman.yml')
    sat_maintain.execute(f'mv {MAINTAIN_HAMMER_YML} /tmp/foreman-maintain-hammer.yml')
    sat_maintain.cli.Admin.logging({'all': True, 'level-debug': True})

    @request.addfinalizer
    def _finalize():
        sat_maintain.execute(
            f'sed -i "s/{flag}: .*/{flag}: {settings.server.admin_password}/g" '
            f'{SATELLITE_ANSWER_FILE}'
        )
        sat_maintain.execute(f'mv /tmp/foreman.yml {HAMMER_CONFIG}')
        sat_maintain.execute(f'mv /tmp/foreman-maintain-hammer.yml {MAINTAIN_HAMMER_YML}')
        sat_maintain.cli.Admin.logging({'all': True, 'level-production': True})


@pytest.mark.include_satellite_iop
@pytest.mark.include_capsule
def test_positive_service_list(sat_maintain):
    """List satellite services using satellite-maintain service subcommand

    :id: aa878d16-5a22-11ed-849d-cb7ac12cece2

    :parametrized: yes

    :steps:
        1. Run satellite-maintain service list

    :expectedresults: Satellite services should be listed
    """
    result = sat_maintain.cli.Service.list()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    if isinstance(sat_maintain, Satellite):
        services = (
            SATELLITE_SERVICES + IOP_SERVICES
            if sat_maintain.local_advisor_enabled
            else SATELLITE_SERVICES
        )
    else:
        services = CAPSULE_SERVICES
    for service in services:
        assert service in result.stdout


@pytest.mark.include_satellite_iop
@pytest.mark.include_capsule
@pytest.mark.usefixtures('start_satellite_services')
def test_positive_service_stop_start(sat_maintain):
    """Start/Stop services using satellite-maintain service subcommand

    :id: fa3b02a9-b441-413b-b9d2-1a59d04f285c

    :parametrized: yes

    :steps:
        1. Run satellite-maintain service stop
        2. Run satellite-maintain service status --brief
        3. Run satellite-maintain service start
        4. Run satellite-maintain service status --brief

    :expectedresults: Satellite services should stop and start.
    """
    result = sat_maintain.cli.Service.stop()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    result = sat_maintain.cli.Service.status(options={'brief': True})
    assert 'FAIL' in result.stdout
    assert result.status == 1
    result = sat_maintain.cli.Service.start()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    result = sat_maintain.cli.Service.status(options={'brief': True})
    assert 'FAIL' not in result.stdout
    assert result.status == 0


@pytest.mark.upgrade
@pytest.mark.include_satellite_iop
@pytest.mark.include_capsule
@pytest.mark.usefixtures('start_satellite_services')
def test_positive_service_stop_restart(sat_maintain):
    """Disable services using satellite-maintain service

    :id: dc60e388-f012-4164-a496-b12d6230cdc2

    :parametrized: yes

    :steps:
        1. Run satellite-maintain service stop.
        2. Run satellite-maintain service status --brief
        3. Run satellite-maintain service restart
        4. Run satellite-maintain service status --brief

    :expectedresults: service should restart.

    :BZ: 1626651
    """
    result = sat_maintain.cli.Service.stop()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    result = sat_maintain.cli.Service.status(options={'brief': True})
    assert 'FAIL' in result.stdout
    assert result.status == 1
    result = sat_maintain.cli.Service.restart()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    result = sat_maintain.cli.Service.status(options={'brief': True})
    assert 'FAIL' not in result.stdout
    assert result.status == 0


@pytest.mark.include_capsule
@pytest.mark.include_satellite_iop
@pytest.mark.usefixtures('start_satellite_services')
def test_positive_service_enable_disable(sat_maintain):
    """Enable/Disable services using satellite-maintain service subcommand

    :id: a0e0a052-0e21-465c-bb28-2e7613dbece6

    :parametrized: yes

    :steps:
        1. Run satellite-maintain service disable
        2. Run satellite-maintain service enable

    :expectedresults: Services should enable/disable

    :BZ: 1995783, 2055790

    :customerscenario: true
    """
    result = sat_maintain.cli.Service.stop()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    result = sat_maintain.cli.Service.disable()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    result = sat_maintain.cli.Service.enable()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    sat_maintain.power_control(state='reboot')
    if isinstance(sat_maintain, Satellite):
        result, _ = wait_for(
            sat_maintain.cli.Service.status,
            func_kwargs={'options': {'brief': True, 'only': 'foreman.service'}},
            fail_condition=lambda res: "FAIL" in res.stdout,
            handle_exception=True,
            delay=30,
            timeout=300,
        )
        assert 'FAIL' not in sat_maintain.cli.Base.ping()
    else:
        result, _ = wait_for(
            sat_maintain.cli.Service.status,
            func_kwargs={'options': {'brief': True}},
            fail_condition=lambda res: "FAIL" in res.stdout,
            handle_exception=True,
            delay=30,
            timeout=300,
        )
    assert 'FAIL' not in result.stdout
    assert result.status == 0


@pytest.mark.include_satellite_iop
@pytest.mark.usefixtures('start_satellite_services')
def test_positive_foreman_service(sat_maintain):
    """Validate httpd service should work as expected even stopping of the foreman service

    :id: 08a29ea2-2e49-11eb-a22b-d46d6dd3b5b2

    :steps:
        1. Stop foreman service
        2. Check the status for httpd should not have affect
        3. Run satellite-maintain health check

    :expectedresults: foreman service should restart correctly
    """
    result = sat_maintain.cli.Service.stop(options={'only': 'foreman'})
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    assert 'foreman' in result.stdout
    result = sat_maintain.cli.Service.status(options={'only': 'httpd'})
    assert result.status == 0
    result = sat_maintain.cli.Health.check(
        options={'assumeyes': True, 'whitelist': 'check-tftp-storage'}
    )
    assert result.status == 0
    assert 'foreman' in result.stdout
    assert sat_maintain.cli.Service.start(options={'only': 'foreman'}).status == 0


@pytest.mark.include_capsule
def test_positive_status_clocale(sat_maintain):
    """Test service status with C locale

    :id: 143dda54-5ab5-478a-b33e-af805bace2d7

    :parametrized: yes

    :steps:
        1. Run LC_ALL=C.UTF-8 satellite-maintain service status

    :expectedresults: service status works with C locale
    """
    assert sat_maintain.cli.Service.status(env_var='LC_ALL=C.UTF-8').status == 0


def test_positive_service_restart(setup_test_positive_service_restart, sat_maintain):
    """Restart services using service restart when hammer config/credentials are missing
        and debug logging is enabled.

    :id: c7518650-d72a-47b1-8d38-42b862f474fc

    :steps:
        1. Remove hammer config/credentials
        2. Enable debug logging
        3. Run satellite-maintain service restart

    :expectedresults: Services restart should work.

    :customerscenario: true

    :Verifies: SAT-30970

    :BZ: 1696862
    """
    result = sat_maintain.cli.Service.restart()
    assert 'FAIL' not in result.stdout
    assert result.status == 0


def test_positive_status_rpmsave(request, sat_maintain):
    """Verify satellite-maintain service status doesn't contain any backup files like .rpmsave,
    or any file with .yml which don't exist as services.

    :id: dda696c9-7385-4450-8380-b694e4016661

    :steps:
        1. Run satellite-maintain service status --brief.
        2. Verify satellite-maintain service status doesn't pick up any backup files like
           .rpmsave, or any file with .yml which don't exist as services.

    :expectedresults: Service status doesn't contain invalid services with extension .rpmsave

    :BZ: 1945916, 1962853

    :CaseImportance: High
    """
    file_path = f'/etc/foreman/dynflow/{gen_string("alpha")}.yml.rpmsave'
    assert sat_maintain.execute(f'touch {file_path}').status == 0

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.execute(f'rm {file_path}').status == 0

    result = sat_maintain.cli.Service.status(options={'brief': True})
    assert 'rpmsave' not in result.stdout
    assert 'FAIL' not in result.stdout
    assert result.status == 0
