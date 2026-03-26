"""Test module for satellite-maintain health functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Rocket

:CaseImportance: Critical

"""

import pytest

from robottelo.config import settings


@pytest.mark.satellite_iop_only
def test_podman_login_check(request, sat_maintain):
    """Test Podman login check with local Red Hat Lightspeed(IoP) Satellite.

    :id: 70fd6d86-a647-442c-a971-cbd1207b734b

    :setup: Configure a Satellite with local Red Hat Lightspeed(IoP) enabled.

    :steps:
        1. Run satellite-maintain update check.
        2. Verify that the Podman login check passes.
        3. Log out of the remote container registry.
        4. Run satellite-maintain update check.
        5. Verify that the Podman login check fails.

    :Verifies: SAT-35282
    """
    iop_settings = settings.rh_cloud.iop

    request.addfinalizer(lambda: sat_maintain.podman_logout(iop_settings.registry))

    check_description = 'Check whether podman needs to be logged in to the registry'
    fail_message = (
        'You are using containers from registry.redhat.io,\n'
        'but your system is not logged in to the registry, or the login expired.\n'
        'Please login to registry.redhat.io.'
    )
    # Login to Prod registry to ensure the check runs correctly, it won't work for any other registry
    sat_maintain.podman_login(iop_settings.username, iop_settings.token, iop_settings.registry)
    result = sat_maintain.cli.Health.check(options={'label': 'container-podman-login'})
    assert 'FAIL' not in result.stdout
    assert check_description in result.stdout, result.stdout
    sat_maintain.podman_logout(iop_settings.registry)
    result = sat_maintain.cli.Health.check(options={'label': 'container-podman-login'})
    assert 'FAIL' in result.stdout
    assert fail_message in result.stdout, result.stdout
