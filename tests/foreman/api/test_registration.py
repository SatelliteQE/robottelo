"""Tests for registration.

:Requirement: Registration

:CaseComponent: Registration

:CaseAutomation: Automated

:CaseImportance: Critical

:Team: Rocket

"""

import uuid

from fauxfactory import gen_ipaddr, gen_mac, gen_string
import pytest
from requests import HTTPError

from robottelo import constants
from robottelo.config import (
    settings,
    user_nailgun_config,
)

pytestmark = pytest.mark.tier1


@pytest.mark.e2e
@pytest.mark.no_containers
def test_host_registration_end_to_end(
    module_sca_manifest_org,
    module_location,
    module_activation_key,
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
    org = module_sca_manifest_org
    command = module_target_sat.api.RegistrationCommand(
        organization=org,
        activation_keys=[module_activation_key.name],
        location=module_location,
    ).create()

    result = rhel_contenthost.execute(command)
    rc = 1 if rhel_contenthost.os_version.major == 6 else 0
    assert result.status == rc, f'Failed to register host: {result.stderr}'

    # Verify server.hostname and server.port from subscription-manager config
    assert module_target_sat.hostname == rhel_contenthost.subscription_config['server']['hostname']
    assert rhel_contenthost.subscription_config['server']['port'] == constants.CLIENT_PORT

    # Update module_capsule_configured to include module_org/module_location
    nc = module_capsule_configured.nailgun_smart_proxy
    module_target_sat.api.SmartProxy(id=nc.id, organization=[org]).update(['organization'])
    module_target_sat.api.SmartProxy(id=nc.id, location=[module_location]).update(['location'])

    command = module_target_sat.api.RegistrationCommand(
        smart_proxy=nc,
        organization=org,
        activation_keys=[module_activation_key.name],
        location=module_location,
        force=True,
    ).create()
    result = rhel_contenthost.execute(command)

    rc = 1 if rhel_contenthost.os_version.major == 6 else 0
    assert result.status == rc, f'Failed to register host: {result.stderr}'

    # Verify server.hostname and server.port from subscription-manager config
    assert (
        module_capsule_configured.hostname
        == rhel_contenthost.subscription_config['server']['hostname']
    )
    assert rhel_contenthost.subscription_config['server']['port'] == constants.CLIENT_PORT


@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_allow_reregistration_when_dmi_uuid_changed(
    module_sca_manifest_org,
    rhel_contenthost,
    target_sat,
    module_activation_key,
    module_location,
):
    """Register a content host with a custom DMI UUID, unregistering it, change
    the DMI UUID, and re-registering it again

    :id: 7f431cb2-5a63-41f7-a27f-62b86328b50d

    :expectedresults: The content host registers successfully

    :customerscenario: true

    :BZ: 1747177,2229112
    """
    uuid_1 = str(uuid.uuid1())
    uuid_2 = str(uuid.uuid4())
    org = module_sca_manifest_org
    target_sat.execute(f'echo \'{{"dmi.system.uuid": "{uuid_1}"}}\' > /etc/rhsm/facts/uuid.facts')
    command = target_sat.api.RegistrationCommand(
        organization=org,
        activation_keys=[module_activation_key.name],
        location=module_location,
    ).create()
    result = rhel_contenthost.execute(command)
    assert result.status == 0
    result = rhel_contenthost.execute('subscription-manager clean')
    assert result.status == 0
    target_sat.execute(f'echo \'{{"dmi.system.uuid": "{uuid_2}"}}\' > /etc/rhsm/facts/uuid.facts')
    command = target_sat.api.RegistrationCommand(
        organization=org,
        activation_keys=[module_activation_key.name],
        location=module_location,
    ).create()
    result = rhel_contenthost.execute(command)
    assert result.status == 0


def test_positive_update_packages_registration(
    module_target_sat,
    module_sca_manifest_org,
    module_location,
    rhel8_contenthost,
    module_activation_key,
):
    """Test package update on host post registration

    :id: 3d0a3252-ab81-4acf-bca6-253b746f26bb

    :expectedresults: Package update is successful on host post registration.
    """
    org = module_sca_manifest_org
    command = module_target_sat.api.RegistrationCommand(
        organization=org,
        location=module_location,
        activation_keys=[module_activation_key.name],
        update_packages=True,
    ).create()
    result = rhel8_contenthost.execute(command)
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    package = constants.FAKE_7_CUSTOM_PACKAGE
    repo_url = settings.repos.yum_3['url']
    rhel8_contenthost.create_custom_repos(fake_yum=repo_url)
    result = rhel8_contenthost.execute(f"yum install -y {package}")
    assert result.status == 0


@pytest.mark.no_containers
def test_positive_rex_interface_for_global_registration(
    module_target_sat,
    module_sca_manifest_org,
    module_location,
    rhel8_contenthost,
    module_activation_key,
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
    org = module_sca_manifest_org
    command = module_target_sat.api.RegistrationCommand(
        organization=org,
        location=module_location,
        activation_keys=[module_activation_key.name],
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


@pytest.mark.tier1
def test_negative_global_registration_without_ak(module_target_sat):
    """Attempt to register a host without ActivationKey

    :id: e48a6260-97e0-4234-a69c-77bbbcde85de

    :expectedresults: Generate command is disabled without ActivationKey
    """
    with pytest.raises(HTTPError) as context:
        module_target_sat.api.RegistrationCommand().create()
    assert 'Missing activation key!' in context.value.response.text


def test_negative_capsule_without_registration_enabled(
    module_target_sat,
    module_capsule_configured,
    module_ak_with_cv,
    module_entitlement_manifest_org,
    module_location,
):
    """Verify registration with Capsule, when registration isn't configured in installer

    :id: a2f23e42-648d-4428-a961-6e0b933c6dff

    :steps:
            1. Get a configured capsule
            2. The registration is set to False on capsule by default
            3. Try to register host with that capsule

    :expectedresults: Registration fails with HTTP error code 422 and an error message.
    """
    org = module_entitlement_manifest_org

    nc = module_capsule_configured.nailgun_smart_proxy
    module_target_sat.api.SmartProxy(id=nc.id, organization=[org]).update(['organization'])
    module_target_sat.api.SmartProxy(id=nc.id, location=[module_location]).update(['location'])

    res = module_capsule_configured.install(
        cmd_args={},
        cmd_kwargs={'foreman-proxy-registration': 'false', 'foreman-proxy-templates': 'true'},
    )
    assert res.status == 0
    error_message = '422 Client Error'
    with pytest.raises(HTTPError, match=f'{error_message}') as context:
        module_target_sat.api.RegistrationCommand(
            smart_proxy=nc,
            organization=org,
            location=module_location,
            activation_keys=[module_ak_with_cv.name],
            insecure=True,
        ).create()
    assert (
        "Proxy lacks one of the following features: 'Registration', 'Templates'"
        in context.value.response.text
    )


@pytest.mark.rhel_ver_match('[^6]')
def test_positive_host_registration_with_non_admin_user_with_setup_false(
    module_org,
    module_location,
    module_activation_key,
    module_target_sat,
    rhel_contenthost,
):
    """Verify host registration with non admin user with setup false

    :id: 02bdda6a-010d-4098-a7e0-e4b5e8416ce3

    :steps:
        1. Sync the content repositories, add and publish it in CV
        2. Create a non-admin user and assign "Register Hosts" role to it.
        3. Create an activation key and assign CV and LCE to it.
        4. Create new user and generate curl command to register host

    :expectedresults: Host registered successfully with all setup options set to 'NO' with non-admin user

    :BZ: 2211484

    :customerscenario: true
    """
    register_host_role = module_target_sat.api.Role().search(
        query={'search': 'name="Register hosts"'}
    )
    login = gen_string('alphanumeric')
    password = gen_string('alphanumeric')
    module_target_sat.api.User(
        role=register_host_role,
        admin=False,
        login=login,
        password=password,
        organization=[module_org],
        location=[module_location],
    ).create()
    user_cfg = user_nailgun_config(login, password)
    command = module_target_sat.api.RegistrationCommand(
        server_config=user_cfg,
        organization=module_org,
        activation_keys=[module_activation_key.name],
        location=module_location,
        setup_insights=False,
        setup_remote_execution=False,
        setup_remote_execution_pull=False,
        update_packages=False,
    ).create()
    result = rhel_contenthost.execute(command)
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    # verify package install for insights-client didn't run when Setup Insights is false
    assert 'dnf -y install insights-client' not in result.stdout
    # verify  package install for foreman_ygg_worker didn't run when REX pull mode is false
    assert 'dnf -y install foreman_ygg_worker' not in result.stdout
    # verify packages aren't getting updated when Update packages is false
    assert '# Updating packages' not in result.stdout
    # verify foreman-proxy ssh pubkey isn't present when Setup REX is false
    assert rhel_contenthost.execute('cat ~/.ssh/authorized_keys | grep foreman-proxy').status == 1


@pytest.mark.rhel_ver_match('[^6]')
def test_negative_verify_bash_exit_status_failing_host_registration(
    module_sca_manifest_org,
    module_location,
    module_target_sat,
    rhel_contenthost,
):
    """Verify status code, when curl command registration fail intentionally

    :id: 4789e8da-6391-4ea4-aa0d-73c93220ce44

    :steps:
        1. Generate a curl command and make the registration fail intentionally.
        2. Check the exit code for the command.

    :expectedresults: Exit code returns 1 if registration fails.

    :BZ: 2155444

    :customerscenario: true

    :parametrized: yes
    """
    ak = module_target_sat.api.ActivationKey(name=gen_string('alpha')).create()
    # Try registration command generated with AK not in same as selected organization
    command = module_target_sat.api.RegistrationCommand(
        organization=module_sca_manifest_org,
        activation_keys=[ak.name],
        location=module_location,
    ).create()
    result = rhel_contenthost.execute(command)

    # verify status code when registrationCommand fails to register on host
    assert result.status == 1
    assert 'Couldn\'t find activation key' in result.stderr
