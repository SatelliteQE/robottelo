"""Test class for satellite-maintain packages functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ForemanMaintain

:Team: Platform

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest

pytestmark = pytest.mark.destructive


@pytest.mark.include_capsule
def test_positive_all_packages_update(target_sat):
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
    target_sat.register_to_cdn()
    # Update packages with yum
    result = target_sat.execute('yum update -y --disableplugin=foreman-protector')
    assert result.status == 0
    # Reboot
    if target_sat.execute('needs-restarting -r').status == 1:
        target_sat.power_control(state='reboot')
    # Run check-update again to verify there are no more packages available to update
    result = target_sat.cli.Packages.check_update()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
