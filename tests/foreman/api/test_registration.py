"""Tests for registration.

:Requirement: Registration

:CaseLevel: Acceptance

:CaseComponent: Registration

:CaseAutomation: Automated

:CaseImportance: Critical

:Assignee: sbible

:TestType: Functional

:Upstream: No
"""
import pytest

from robottelo.constants import CLIENT_PORT
from robottelo.utils.issue_handlers import is_open

pytestmark = pytest.mark.tier1


@pytest.mark.e2e
@pytest.mark.no_containers
def test_host_registration_end_to_end(
    module_org,
    module_location,
    module_ak_with_synced_repo,
    module_target_sat,
    module_capsule_configured,
    rhel_contenthost,
):
    """Verify content host registration with global registration

    :id: 219567a8-856a-11ed-944d-03d9b43011c2

    :steps:
        1. Register host with global registration template to Satellite and Capsule

    :expectedresults: Host registered successfully

    :BZ: 2156926

    :customerscenario: true
    """
    command = module_target_sat.api.RegistrationCommand(
        organization=module_org,
        activation_keys=[module_ak_with_synced_repo.name],
        location=module_location,
    ).create()

    result = rhel_contenthost.execute(command)
    if is_open('BZ:2156926') and rhel_contenthost.os_version.major == 6:
        assert result.status == 1, f'Failed to register host: {result.stderr}'
    else:
        assert result.status == 0, f'Failed to register host: {result.stderr}'

    # Verify server.hostname and server.port from subscription-manager config
    assert module_target_sat.hostname == rhel_contenthost.subscription_config['server']['hostname']
    assert CLIENT_PORT == rhel_contenthost.subscription_config['server']['port']

    # Update module_capsule_configured to include module_org/module_location
    nc = module_capsule_configured.nailgun_smart_proxy
    module_target_sat.api.SmartProxy(id=nc.id, organization=[module_org]).update(['organization'])
    module_target_sat.api.SmartProxy(id=nc.id, location=[module_location]).update(['location'])

    command = module_target_sat.api.RegistrationCommand(
        smart_proxy=nc,
        organization=module_org,
        activation_keys=[module_ak_with_synced_repo.name],
        location=module_location,
        force=True,
    ).create()
    result = rhel_contenthost.execute(command)

    if is_open('BZ:2156926') and rhel_contenthost.os_version.major == 6:
        assert result.status == 1, f'Failed to register host: {result.stderr}'
    else:
        assert result.status == 0, f'Failed to register host: {result.stderr}'

    # Verify server.hostname and server.port from subscription-manager config
    assert (
        module_capsule_configured.hostname
        == rhel_contenthost.subscription_config['server']['hostname']
    )
    assert CLIENT_PORT == rhel_contenthost.subscription_config['server']['port']
