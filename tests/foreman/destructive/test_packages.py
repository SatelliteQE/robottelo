"""Test class for satellite-maintain packages functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Platform

:CaseImportance: Critical

"""

import re

import pytest

from robottelo.hosts import Satellite

pytestmark = pytest.mark.destructive


@pytest.mark.include_capsule
def test_positive_all_packages_update(sat_maintain):
    """Verify update and check-update work as expected.

    :id: eb8a5611-b1a8-4a18-b80e-56b045c0d2f6

    :steps:
        1. Run yum update
        2. Reboot
        3. Run satellite-maintain packages check-update

    :expectedresults: update should update the packages,
        and check-update should list no packages at the end.

    :BZ: 2218656

    :customerscenario: true
    """
    # Register to CDN for package updates
    sat_maintain.register_to_cdn()
    # Update packages with yum
    result = sat_maintain.execute('yum update -y --disableplugin=foreman-protector')
    assert result.status == 0
    # Reboot
    if sat_maintain.execute('needs-restarting -r').status == 1:
        sat_maintain.power_control(state='reboot')
    # Run check-update again to verify there are no more packages available to update
    result = sat_maintain.cli.Packages.check_update()
    # Regex to match if there are packages available to update
    # Matches lines like '\n\nwalrus.noarch        5.21-1        custom_repo\n'
    pattern = '(\\n){1,2}(\\S+)(\\s+)(\\S+)(\\s+)(\\S+)(\\n)'
    matches = re.search(pattern, result.stdout)
    assert matches is None  # No packages available to update
    assert 'FAIL' not in result.stdout
    assert result.status == 0


@pytest.mark.include_capsule
def test_negative_remove_satellite_packages(sat_maintain):
    """Ensure user can't remove satellite or its dependent packages

    :id: af150302-418a-4d42-8d01-bb0e6b90f81f

    :steps:
        1. yum remove <satellite or other dependency>

    :expectedresults: removal should fail due to protecting the satellite package

    :BZ: 1884395

    :customerscenario: true
    """
    # Packages include satellite direct dependencies like foreman,
    # but also dependency of dependencies like wget for foreman
    if isinstance(sat_maintain, Satellite):
        package_list = ['foreman', 'foreman-proxy', 'katello', 'wget', 'satellite']
    else:
        package_list = ['foreman-proxy', 'satellite-capsule']
    for package in package_list:
        result = sat_maintain.execute(f'yum remove {package}')
        assert result.status != 0
        assert (
            'Problem: The operation would result in removing the following protected packages: satellite'
            in str(result.stderr[1])
        )
