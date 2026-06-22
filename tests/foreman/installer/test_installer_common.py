"""Common installation test infrastructure for both installation methods

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: Critical
"""

from robottelo.cli import hammer
from robottelo.utils.issue_handlers import is_open


def assert_hammer_ping_ok(result):
    """Shared assertion for hammer ping checks.

    :param result: Command result from executing 'hammer ping'
    """
    assert result.status == 0, 'hammer ping failed'
    services = hammer.parse_ping(result.stdout)
    for service_name, status in services.items():
        assert status == 'ok', f'Service {service_name} status is {status}, expected ok'


def common_sat_install_assertions(satellite):
    """Common assertions for any Satellite installation.

    Works with both installer and foremanctl methods.

    :param satellite: Satellite instance to verify
    """
    # Check journald for errors
    services = satellite.get_service_names()
    service_units = ' '.join([f'-u "{svc}"' for svc in services])

    result = satellite.execute(f'journalctl --quiet --no-pager --boot --grep ERROR {service_units}')

    if is_open('SAT-21086'):
        assert not list(filter(lambda x: 'PG::' not in x, result.stdout.splitlines()))
    else:
        assert not result.stdout

    # Check httpd logs - filter out expected transient startup errors
    result = satellite.execute(r'grep -iR "error" /var/log/httpd/*')
    if result.stdout:
        # Filter out expected "Connection refused" errors during service startup
        # These occur when httpd starts before Foreman is ready
        filtered_errors = [
            line
            for line in result.stdout.splitlines()
            if 'Connection refused' not in line
            and 'attempt to connect to 127.0.0.1:3000' not in line
            and 'failed to make connection to backend: localhost' not in line
        ]
        assert not filtered_errors, f"Unexpected httpd errors:\n{chr(10).join(filtered_errors)}"

    httpd_log = satellite.execute('journalctl --unit=httpd')
    assert 'WARNING' not in httpd_log.stdout
