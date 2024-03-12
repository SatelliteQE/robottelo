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

from fauxfactory import gen_ipaddr, gen_mac
import pytest

from robottelo.constants import CLIENT_PORT, ENVIRONMENT
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
    assert rhel_contenthost.subscription_config['server']['port'] == CLIENT_PORT

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
    assert rhel_contenthost.subscription_config['server']['port'] == CLIENT_PORT


@pytest.mark.tier3
def test_positive_allow_reregistration_when_dmi_uuid_changed(
    module_org, rhel_contenthost, target_sat
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
    target_sat.execute(f'echo \'{{"dmi.system.uuid": "{uuid_1}"}}\' > /etc/rhsm/facts/uuid.facts')
    result = rhel_contenthost.register_contenthost(module_org.label, lce=ENVIRONMENT)
    assert result.status == 0
    result = rhel_contenthost.execute('subscription-manager clean')
    assert result.status == 0
    target_sat.execute(f'echo \'{{"dmi.system.uuid": "{uuid_2}"}}\' > /etc/rhsm/facts/uuid.facts')
    result = rhel_contenthost.register_contenthost(module_org.label, lce=ENVIRONMENT)
    assert result.status == 0


@pytest.mark.no_containers
def test_positive_rex_interface_for_global_registration(
    module_target_sat,
    module_org,
    module_location,
    rhel8_contenthost,
    module_ak_with_synced_repo,
):
    """Test remote execution interface is set for global registration

    :id: 982de593-dd1a-4c6c-81fe-728f40a7ad4d

    :steps:
        1. Register host with global registration template to Satellite specifying remote execution interface parameter.

    :expectedresults: remote execution interface passed in the registration command is properly set for the host.

    :BZ: 1841048

    :customerscenario: true
    """
    mac_address = gen_mac(multicast=False)
    ip = gen_ipaddr()
    # Create eth1 interface on the host
    add_interface_command = f'ip link add eth1 type dummy;ifconfig eth1 hw ether {mac_address};ip addr add {ip}/24 brd + dev eth1 label eth1:1;ip link set dev eth1 up'
    result = rhel8_contenthost.execute(add_interface_command)
    assert result.status == 0
    command = module_target_sat.api.RegistrationCommand(
        organization=module_org,
        location=module_location,
        activation_keys=[module_ak_with_synced_repo.name],
        update_packages=True,
        remote_execution_interface='eth1',
    ).create()
    result = rhel8_contenthost.execute(command)
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    host = module_target_sat.api.Host().search(
        query={'search': f'name={rhel8_contenthost.hostname}'}
    )[0]
    # Check if eth1 interface is set for remote execution
    for interface in host.read_json()['interfaces']:
        if 'eth1' in str(interface):
            assert interface['execution'] is True
            assert interface['ip'] == ip
            assert interface['mac'] == mac_address
