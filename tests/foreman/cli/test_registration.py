"""Tests for registration.

:Requirement: Registration

:CaseComponent: Registration

:CaseAutomation: Automated

:CaseImportance: Critical

:Team: Proton

"""

import json
import re
from tempfile import mkstemp

from fauxfactory import gen_mac, gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import CLIENT_PORT
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.issue_handlers import is_open


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

    :id: b6cd60ba-8069-11ed-ac61-83315855d126

    :steps:
        1. Register host with global registration template to Satellite and Capsule
        2. Check the host is registered and verify host owner name

    :expectedresults: Host registered successfully with valid owner name

    :Verifies: SAT-21682, SAT-14716

    :customerscenario: true
    """
    org = module_sca_manifest_org
    result = rhel_contenthost.register(
        org, module_location, module_activation_key.name, module_target_sat
    )

    rc = 1 if rhel_contenthost.os_version.major == 6 else 0
    assert result.status == rc, f'Failed to register host: {result.stderr}'

    owner_name = module_target_sat.cli.Host.info(
        options={'name': rhel_contenthost.hostname, 'fields': 'Additional info/owner'}
    )
    # Verify host owner name set correctly
    assert 'Admin User' in owner_name['additional-info']['owner']['name'], (
        f'Host owner name is incorrect: {owner_name["additional-info"]["owner"]["name"]}'
    )

    # Verify server.hostname and server.port from subscription-manager config
    assert module_target_sat.hostname == rhel_contenthost.subscription_config['server']['hostname']
    assert rhel_contenthost.subscription_config['server']['port'] == CLIENT_PORT

    # Update module_capsule_configured to include module_org/module_location
    module_target_sat.cli.Capsule.update(
        {
            'name': module_capsule_configured.hostname,
            'organization-ids': org.id,
            'location-ids': module_location.id,
        }
    )
    result = rhel_contenthost.register(
        org,
        module_location,
        module_activation_key.name,
        module_capsule_configured,
        force=True,
    )
    rc = 1 if rhel_contenthost.os_version.major == 6 else 0
    assert result.status == rc, f'Failed to register host: {result.stderr}'

    owner_name = module_target_sat.cli.Host.info(
        options={'name': rhel_contenthost.hostname, 'fields': 'Additional info/owner'}
    )
    # Verify capsule host owner name set correctly
    assert 'Admin User' in owner_name['additional-info']['owner']['name'], (
        f'Host owner name is incorrect: {owner_name["additional-info"]["owner"]["name"]}'
    )

    # Verify server.hostname and server.port from subscription-manager config
    assert (
        module_capsule_configured.hostname
        == rhel_contenthost.subscription_config['server']['hostname']
    )
    assert rhel_contenthost.subscription_config['server']['port'] == CLIENT_PORT


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_upgrade_katello_ca_consumer_rpm(module_org, module_location, target_sat, rhel_contenthost):
    """After updating the consumer cert the rhsm.conf file still points to Satellite host name
    and not Red Hat CDN for subscription.

    :id: c8d861ec-0d81-4d89-a8e1-02afecfd8171

    :steps:

        1. Get consumer crt source file
        2. Install rpm-build
        3. Use rpmbuild to change the version in the spec file
        4. Build new RPM with higher version number
        5. Install new RPM and assert no change in server URL

    :expectedresults: Server URL is still Satellite host name not Red Hat CDN

    :CaseImportance: High

    :customerscenario: true

    :BZ: 1791503
    """
    # Adding IPv6 proxy for IPv6 communication
    rhel_contenthost.enable_ipv6_dnf_and_rhsm_proxy()
    consumer_cert_name = f'katello-ca-consumer-{target_sat.hostname}'
    consumer_cert_src = f'{consumer_cert_name}-1.0-1.src.rpm'
    new_consumer_cert_rpm = f'{consumer_cert_name}-1.0-2.noarch.rpm'
    spec_file = f'{consumer_cert_name}.spec'
    vm = rhel_contenthost
    # Install consumer cert and check server URL in /etc/rhsm/rhsm.conf
    result = vm.execute(
        f'rpm -Uvh "http://{target_sat.hostname}/pub/{consumer_cert_name}-1.0-1.noarch.rpm"'
    )
    assert result.status == 0
    # Check server URL is not Red Hat CDN's "subscription.rhsm.redhat.com"
    assert vm.subscription_config['server']['hostname'] != 'subscription.rhsm.redhat.com'
    assert target_sat.hostname == vm.subscription_config['server']['hostname']

    # Get consumer cert source file
    assert vm.execute(f'curl -O "http://{target_sat.hostname}/pub/{consumer_cert_src}"')
    # Install repo for build tools
    vm.create_custom_repos(rhel7=settings.repos.rhel7_os)
    result = vm.execute('[ -s "/etc/yum.repos.d/rhel7.repo" ]')
    assert result.status == 0
    # Install tools
    assert vm.execute('yum -y install rpm-build')
    # Install src to create the SPEC
    assert vm.execute(f'rpm -i {consumer_cert_src}')
    # rpmbuild spec file
    assert vm.execute(
        f'rpmbuild --define "name {consumer_cert_name}" --define "release 2" \
        -ba rpmbuild/SPECS/{spec_file}'
    )
    # Install new rpmbuild/RPMS/noarch/katello-ca-consumer-*-2.noarch.rpm
    assert vm.execute(f'yum install -y rpmbuild/RPMS/noarch/{new_consumer_cert_rpm}')
    # Check server URL is not Red Hat CDN's "subscription.rhsm.redhat.com"
    assert vm.subscription_config['server']['hostname'] != 'subscription.rhsm.redhat.com'
    assert target_sat.hostname == vm.subscription_config['server']['hostname']

    # Register as final check
    vm.register_contenthost(module_org.label)
    result = vm.execute('subscription-manager identity')
    # Result will be 0 if registered
    assert result.status == 0


@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
def test_negative_register_twice(module_ak_with_cv, module_org, rhel_contenthost, target_sat):
    """Attempt to register a host twice to Satellite

    :id: 0af81129-cd69-4fa7-a128-9e8fcf2d03b1

    :expectedresults: host cannot be registered twice

    :parametrized: yes
    """
    rhel_contenthost.register(module_org, None, module_ak_with_cv.name, target_sat)
    assert rhel_contenthost.subscribed
    result = rhel_contenthost.register(
        module_org, None, module_ak_with_cv.name, target_sat, force=False
    )
    # host being already registered.
    assert result.status == 1
    assert 'This system is already registered' in str(result.stderr)


@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
def test_positive_force_register_twice(module_ak_with_cv, module_org, rhel_contenthost, target_sat):
    """Register a host twice to Satellite, with force=true

    :id: 7ccd4efd-54bb-4207-9acf-4c6243a32fab

    :expectedresults: Host will be re-registered

    :parametrized: yes

    :BZ: 1361309

    :customerscenario: true
    """
    reg_id_pattern = r"The system has been registered with ID: ([^\n]*)"
    name = gen_string('alpha') + ".example.com"
    rhel_contenthost.execute(f'hostnamectl set-hostname {name}')
    result = rhel_contenthost.register(module_org, None, module_ak_with_cv.name, target_sat)
    reg_id_old = re.search(reg_id_pattern, result.stdout).group(1)
    assert result.status == 0
    assert rhel_contenthost.subscribed
    result = rhel_contenthost.register(
        module_org, None, module_ak_with_cv.name, target_sat, force=True
    )
    assert result.status == 0
    assert rhel_contenthost.subscribed
    assert f'Unregistering from: {target_sat.hostname}' in str(result.stdout)
    assert f'The registered system name is: {rhel_contenthost.hostname}' in str(result.stdout)
    reg_id_new = re.search(reg_id_pattern, result.stdout).group(1)
    assert f'The system has been registered with ID: {reg_id_new}' in str(result.stdout)
    assert reg_id_new != reg_id_old
    assert (
        target_sat.cli.Host.info({'name': rhel_contenthost.hostname}, output_format='json')[
            'subscription-information'
        ]['uuid']
        == reg_id_new
    )


def test_negative_global_registration_without_ak(module_target_sat):
    """Attempt to register a host without ActivationKey

    :id: e48a6260-97e0-4234-a69c-77bbbcde85df

    :expectedresults: Generate command is disabled without ActivationKey
    """
    with pytest.raises(CLIReturnCodeError) as context:
        module_target_sat.cli.HostRegistration.generate_command(options=None)
    assert (
        'Failed to generate registration command:\n  Missing activation key!'
        in context.value.message
    )


@pytest.mark.rhel_ver_match('8')
def test_positive_custom_facts_for_host_registration(
    module_sca_manifest_org,
    module_location,
    module_target_sat,
    rhel_contenthost,
    module_activation_key,
):
    """Attempt to register a host and check all the interfaces are created from the custom facts

    :id: db73c146-4557-4bf4-a8e2-950ecba31620

    :steps:
        1. Register the host.
        2. Check the host is registered and all the interfaces are created successfully.

    :expectedresults: Host registered successfully with all interfaces created from the custom facts.

    :BZ: 2250397

    :customerscenario: true
    """
    interfaces = [
        {'name': gen_string('alphanumeric')},
        {'name': 'enp98s0f0', 'mac': gen_mac(multicast=False)},
        {'name': 'Datos', 'vlan_id': gen_string('numeric', 4)},
        {'name': 'bondBk', 'vlan_id': gen_string('numeric', 4)},
    ]
    facts = {
        f'net.interface.{interfaces[0]["name"]}.mac_address': gen_mac(),
        f'net.interface.{interfaces[1]["name"]}.mac_address': interfaces[1]["mac"],
        f'net.interface.{interfaces[2]["name"]}.{interfaces[2]["vlan_id"]}.mac_address': gen_mac(),
        f'net.interface.{interfaces[3]["name"]}.{interfaces[3]["vlan_id"]}.mac_address': gen_mac(),
    }
    _, facts_file = mkstemp(suffix='.facts')
    with open(facts_file, 'w') as f:
        json.dump(facts, f, indent=4)
    rhel_contenthost.put(facts_file, '/etc/rhsm/facts/')
    result = rhel_contenthost.register(
        module_sca_manifest_org, module_location, module_activation_key.name, module_target_sat
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    host_info = module_target_sat.cli.Host.info(
        {'name': rhel_contenthost.hostname}, output_format='json'
    )
    assert len(host_info['network-interfaces']) == len(interfaces) + 1  # facts + default interface
    for interface in interfaces:
        for interface_name in interface.values():
            assert interface_name in str(host_info['network-interfaces'])


@pytest.mark.upgrade
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_global_registration_with_gpg_repo(
    module_sca_manifest_org,
    module_location,
    module_activation_key,
    module_target_sat,
    rhel_contenthost,
):
    """Verify host registration command gets generated and host is registered successfully with gpg repo enabled.

    :id: 8f01d904-dd52-47eb-b909-975574a7c7c7

    :steps:
        1. Register host with global registration template with gpg repo and key to Satellite.

    :expectedresults: Host is successfully registered, gpg repo is enabled.
    """
    org = module_sca_manifest_org
    repo_url = settings.repos.gr_yum_repo.url
    repo_gpg_url = settings.repos.gr_yum_repo.gpg_url
    result = rhel_contenthost.register(
        org,
        module_location,
        module_activation_key.name,
        module_target_sat,
        repo_data=f'repo={repo_url},repo_gpg_key_url={repo_gpg_url}',
    )
    assert result.status == 0
    assert rhel_contenthost.subscribed
    result = rhel_contenthost.execute('yum -v repolist')
    assert repo_url in result.stdout
    assert result.status == 0
    if not is_open('SAT-27653'):
        assert rhel_contenthost.execute('dnf install -y bear').status == 0


@pytest.mark.upgrade
@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
@pytest.mark.parametrize('download_utility', ['wget', 'curl'])
def test_positive_register_download_utility(
    module_sca_manifest_org,
    module_location,
    module_activation_key,
    module_target_sat,
    rhel_contenthost,
    download_utility,
):
    """Verify host registration command gets generated and host is registered successfully with all supported download utilities.

    :id: 80c3204a-7923-4c70-b7c1-7b368c61d4b8

    :steps:
        1. Register host with global registration template using different download utilities.

    :expectedresults: Host is successfully registered.
    """
    org = module_sca_manifest_org
    result = rhel_contenthost.register(
        org,
        module_location,
        module_activation_key.name,
        module_target_sat,
        download_utility=download_utility,
    )
    assert result.status == 0
    assert rhel_contenthost.subscribed


@pytest.mark.parametrize('setting_update', ['default_location_subscribed_hosts'], indirect=True)
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_verify_default_location_for_registered_host(
    module_target_sat,
    module_sca_manifest_org,
    module_location,
    rhel_contenthost,
    module_activation_key,
    setting_update,
):
    """Verify default location set for registered host with default_location_subscribed_hosts setting.

    :id: 6ea802d8-0788-4309-845c-c877013a8e48

    :steps:
        1. Create a location and set it as a default location in Administer --> Settings --> Content --> "Default Location subscribed hosts".
        2. Register the host without specifying the location.
        3. Verify that the default location in settings is set as host location after registration.
        4. Re-register the host with a new location.
        5. Verify the host location is registered to new location provided during registration.

    :expectedresults:
        1. Host registers in location set to "Default Location subscribed hosts" setting if no location is provided.
        2. Host registers in location is set to the location provided during registration which overrides the "Default Location subscribed hosts" setting.

    :Verifies: SAT-23047

    :customerscenario: true
    """
    org = module_sca_manifest_org
    location = module_target_sat.api.Location(organization=[org]).create()
    setting_update.value = location.name
    setting_update.update({'value'})
    location_set = (
        module_target_sat.api.Setting()
        .search(query={'search': f'name={setting_update.name}'})[0]
        .value
    )
    result = rhel_contenthost.register(
        module_sca_manifest_org,
        None,
        module_activation_key.name,
        module_target_sat,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    host = module_target_sat.api.Host().search(
        query={"search": f'name={rhel_contenthost.hostname}'}
    )[0]
    assert host.location.read().name == location_set
    # Re-register the host with location provided during registration
    result = rhel_contenthost.register(
        module_sca_manifest_org,
        module_location,
        module_activation_key.name,
        module_target_sat,
        force=True,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    host = module_target_sat.api.Host().search(
        query={"search": f'name={rhel_contenthost.hostname}'}
    )[0]
    assert host.location.read().name == module_location.name


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_invalidate_users_tokens(
    module_target_sat, rhel_contenthost, module_activation_key, module_org, request
):
    """Verify invalidating single and multiple users tokens.

    :id: 5db602d4-9c57-4b70-8d46-5323044824e0

    :steps:
        1. Create an admin user and a non-admin user with "edit_users" and "register_hosts" permission.
        2. Generate a token with admin user and register a host with it, it should be successful.
        3. Invalidate the token and try to use the generated token again to register the host, it should fail.
        4. Invalidate tokens for multiple users with "invalidate-multiple" command, it should invalidate all the tokens for provided users.
        5. Repeat Steps 2,3 and 4 with non-admin user and it should work the same way.

    :expectedresults: Host registration will not be possible after/with invalidated tokens.

    :CaseImportance: Critical

    :Verifies: SAT-30385
    """
    password = settings.server.admin_password
    admin_user = module_target_sat.api.User().search(
        query={'search': f'login={settings.server.admin_username}'}
    )[0]

    # Non-Admin user with "edit_users" permission and "Register hosts" role
    non_admin_user = module_target_sat.api.User(
        login=gen_string('alpha'), password=password, organization=[module_org]
    ).create()
    role = module_target_sat.cli_factory.make_role({'organization-id': module_org.id})
    module_target_sat.cli_factory.add_role_permissions(
        role.id,
        resource_permissions={'User': {'permissions': ['edit_users']}},
    )
    module_target_sat.cli.User.add_role({'id': non_admin_user.id, 'role-id': role.id})
    module_target_sat.cli.User.add_role({'id': non_admin_user.id, 'role': 'Register hosts'})

    # delete the host and the user
    @request.addfinalizer
    def _finalize():
        wait_for(lambda: module_target_sat.cli.Host.delete({'name': rhel_contenthost.hostname}))
        module_target_sat.cli.User.delete({'login': non_admin_user.login})

    # Generate token and verify token invalidation
    for usertype in (admin_user, non_admin_user):
        user = admin_user if usertype.admin else non_admin_user
        cmd = module_target_sat.cli.HostRegistration.with_user(
            user.login, password
        ).generate_command(
            options={
                'activation-keys': module_activation_key.name,
                'insecure': 'true',
                'organization-id': module_org.id,
            }
        )
        result = rhel_contenthost.execute(cmd.strip('\n'))
        assert result.status == 0, f'Failed to register host: {result.stderr}'

        # Invalidate JWTs for a single user
        result = module_target_sat.cli.User.with_user(user.login, password).invalidate(
            options={
                'user-id': user.id,
            }
        )
        assert f'Successfully invalidated registration tokens for {user.login}' in result

        rhel_contenthost.unregister()
        # Re-register the host with invalidated token
        result = rhel_contenthost.execute(cmd.strip('\n'))
        assert result.status == 1
        assert 'ERROR: unauthorized' in result.stdout

        # Invalidate JWTs for multiple users
        result = module_target_sat.cli.User.with_user(user.login, password).invalidate_multiple(
            options={'search': f"id ^ ({admin_user.id}, {non_admin_user.id})"}
        )
        assert 'Successfully invalidated registration tokens' in result


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_negative_users_permission_for_invalidating_tokens(
    module_target_sat, rhel_contenthost, module_activation_key, module_org
):
    """Verify invalidating single and multiple users tokens require "edit_users" permission for non_admin user.

    :id: 6592e106-29c8-4360-8ebb-8db0c45ca616

    :steps:
        1. Create an admin user and a non-admin user with "register_hosts" permission.
        2. Generate a token with non_admin user and register a host with it, it should be successful.
        3. Try to invalidate the token with non_admin user, it should fail.
        4. Repeat Step 3 with invalidate_multiple command and it should fail too.

    :expectedresults: Tokens invalidation fail for non_admin user without "edit_users" permission.

    :Verifies: SAT-30385
    """
    password = settings.server.admin_password
    admin_user = module_target_sat.api.User().search(
        query={'search': f'login={settings.server.admin_username}'}
    )[0]

    # Non-Admin user with "Register hosts" role
    non_admin_user = module_target_sat.cli_factory.user(
        {
            'login': gen_string('alpha'),
            'password': password,
            'organization-ids': module_org.id,
            'roles': ['Register hosts'],
        }
    )

    # Generate token and verify token invalidation
    cmd = module_target_sat.cli.HostRegistration.with_user(
        non_admin_user.login, password
    ).generate_command(
        options={
            'activation-keys': module_activation_key.name,
            'insecure': 'true',
            'organization-id': module_org.id,
        }
    )
    result = rhel_contenthost.execute(cmd.strip('\n'))
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    # Try invalidating JWTs for a single user
    with pytest.raises(CLIReturnCodeError) as context:
        module_target_sat.cli.User.with_user(non_admin_user.login, password).invalidate(
            options={
                'user-id': admin_user.id,
            }
        )
    assert "Missing one of the required permissions: edit_users" in str(context.value)

    # Try invalidating JWTs  for multiple users
    with pytest.raises(CLIReturnCodeError) as context:
        module_target_sat.cli.User.with_user(non_admin_user.login, password).invalidate_multiple(
            options={'search': f"id ^ ({admin_user.id}, {non_admin_user.id})"}
        )
    assert "Missing one of the required permissions: edit_users" in str(context.value)


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_negative_register_host_when_sat_has_port_80_blocked(
    target_sat,
    rhel_contenthost,
    function_org,
    function_location,
    function_activation_key,
):
    """
    Verify host registration fails when there is port 80 blocked on Satellite.

    :id: 3c3e1a8e-7b4c-4d5e-9a6d-8f2e1b3c4d5e

    :steps:
        1. Block port 80 on Satellite
        2. Generate and execute registration command
        3. Verify registration fails with non-zero exit code
        4. Unblock port 80
        5. Re-register host and verify it succeeds

    :expectedresults:
        1. Registration fails with non-zero exit code when port 80 is blocked
        2. Registration succeeds after port 80 is unblocked

    :Verifies: SAT-34258

    :customerscenario: true
    """

    # Block port 80 on Satellite
    target_sat.execute('nft add table inet filter')
    target_sat.execute(
        r'nft add chain inet filter input { type filter hook input priority 0 \; policy accept \; }'
    )
    target_sat.execute('nft add rule inet filter input tcp dport 80 drop')

    try:
        # Attempt to register with port 80 blocked
        result = rhel_contenthost.register(
            function_org, function_location, function_activation_key.name, target_sat
        )

        # Registration should fail with non-zero exit code
        assert result.status != 0, (
            f'Registration should have failed when port 80 is blocked, but got status {result.status}.',
            f'\n STDOUT: {result.stdout} \n STDERR: {result.stderr}',
        )

    finally:  # Unblock port 80
        rule_handle_res = target_sat.execute(
            'nft -a list chain inet filter input | grep "tcp dport 80 drop # handle"'
        )
        handle = rule_handle_res.stdout.split()[-1]
        target_sat.execute(f'nft delete rule inet filter input handle {handle}')

    # Now registration should succeed
    result = rhel_contenthost.register(
        function_org, function_location, function_activation_key.name, target_sat, force=True
    )

    assert result.status == 0, f'Failed to register host after unblocking port 80: {result.stderr}'
