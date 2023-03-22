"""Tests for registration.

:Requirement: Registration

:CaseLevel: Acceptance

:CaseComponent: Registration

:CaseAutomation: Automated

:CaseImportance: Critical

:Team: Rocket

:TestType: Functional

:Upstream: No
"""
import uuid

import pytest

from robottelo.constants import CLIENT_PORT
from robottelo.constants import ENVIRONMENT
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

    @pytest.mark.tier3
    def test_positive_allow_reregistration_when_dmi_uuid_changed(
        self, module_org, rhel_contenthost, target_sat
    ):
        """Register a content host with a custom DMI UUID, unregistering it, change
        the DMI UUID, and re-registering it again

        :id: 7f431cb2-5a63-41f7-a27f-62b86328b50d

        :expectedresults: The content host registers successfully

        :customerscenario: true

        :BZ: 1747177

        :CaseLevel: Integration
        """
        uuid_1 = str(uuid.uuid1())
        uuid_2 = str(uuid.uuid4())
        rhel_contenthost.install_katello_ca(target_sat)
        target_sat.execute(
            f'echo \'{{"dmi.system.uuid": "{uuid_1}"}}\' > /etc/rhsm/facts/uuid.facts'
        )
        result = rhel_contenthost.register_contenthost(module_org.label, lce=ENVIRONMENT)
        assert result.status == 0
        result = rhel_contenthost.execute('subscription-manager clean')
        assert result.status == 0
        target_sat.execute(
            f'echo \'{{"dmi.system.uuid": "{uuid_2}"}}\' > /etc/rhsm/facts/uuid.facts'
        )
        result = rhel_contenthost.register_contenthost(module_org.label, lce=ENVIRONMENT)
        assert result.status == 0
