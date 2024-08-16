"""Destructive test module for satellite-maintain upgrade functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Platform

:CaseImportance: Critical

"""

import pytest

pytestmark = pytest.mark.destructive


@pytest.mark.include_capsule
def test_negative_ipv6_update_check(sat_maintain):
    """Ensure update check fails when ipv6.disable=1 in boot options

    :id: 7b3e017f-443a-4204-99be-e39fa04c89f6

    :parametrized: yes

    :steps:
        1. Add ipv6.disable to grub boot options
        2. Reboot
        3. Run update check

    :customerscenario: true

    :verifies: SAT-24811

    :expectedresults: Update check fails due to ipv6.disable=1 in boot options
    """
    result = sat_maintain.execute('grubby --args="ipv6.disable=1" --update-kernel=ALL')
    assert result.status == 0

    sat_maintain.power_control(state='reboot')

    result = sat_maintain.cli.Update.check(
        options={
            'assumeyes': True,
            'disable-self-update': True,
            'whitelist': 'check-non-redhat-repository, repositories-validate',
        }
    )
    assert result.status != 0
    assert (
        'The kernel contains ipv6.disable=1 which is known to break installation and upgrade, remove and reboot before continuining.'
        in result.stdout
    )
