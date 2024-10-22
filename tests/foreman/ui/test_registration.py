"""Tests for registration.

:Requirement: Registration

:CaseComponent: Registration

:CaseAutomation: Automated

:CaseImportance: Critical

:Team: Rocket
"""

from datetime import datetime
import re

from airgun.exceptions import DisabledWidgetError
from fauxfactory import gen_string
import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import (
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_7_CUSTOM_PACKAGE,
    REPO_TYPE,
)
from robottelo.utils.issue_handlers import is_open

pytestmark = pytest.mark.tier1


def test_positive_verify_default_values_for_global_registration(
    module_target_sat,
    default_org,
):
    """Check for all the Default values pre-populated in the global registration template

    :id: 34122bf3-ae23-47ca-ba3d-da0653d8fd33

    :expectedresults: Default fields in the form should be auto-populated
        e.g. organization, location, rex, insights setup, etc

    :steps:
        1. Check for the default values in the global registration template
    """
    module_target_sat.cli_factory.make_activation_key(
        {'organization-id': default_org.id, 'name': gen_string('alpha')}
    )
    with module_target_sat.ui_session() as session:
        cmd = session.host.get_register_command(
            full_read=True,
        )
    assert cmd['general']['organization'] == 'Default Organization'
    assert cmd['general']['location'] == 'Default Location'
    assert cmd['general']['capsule'] == 'Nothing to select.'
    assert cmd['general']['operating_system'] == ''
    assert cmd['general']['host_group'] == 'Nothing to select.'
    assert cmd['general']['insecure'] is False
    assert cmd['advanced']['setup_rex'] == 'Inherit from host parameter (yes)'
    assert cmd['advanced']['setup_insights'] == 'Inherit from host parameter (yes)'
    assert cmd['advanced']['token_life_time'] == '4'
    assert cmd['advanced']['rex_pull_mode'] == 'Inherit from host parameter (no)'
    assert cmd['advanced']['update_packages'] is False
    assert cmd['advanced']['ignore_error'] is False
    assert cmd['advanced']['force'] is False


@pytest.mark.tier2
def test_positive_org_loc_change_for_registration(
    module_activation_key,
    module_sca_manifest_org,
    module_location,
    module_target_sat,
):
    """Changing the organization and location to check if correct org and loc is updated on the global registration page as well as in the command

    :id: e83ed6bc-ceae-4021-87fe-3ecde1cbf347

    :expectedresults: organization and location is updated correctly on the global registration page as well as in the command.

    :CaseImportance: Medium
    """
    new_org = module_target_sat.api.Organization().create()
    new_loc = module_target_sat.api.Location().create()
    ak = module_target_sat.api.ActivationKey(organization=new_org).create()
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_sca_manifest_org.name)
        session.location.select(loc_name=module_location.name)
        cmd = session.host.get_register_command(
            {
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
            }
        )
        expected_pairs = [
            f'organization_id={module_sca_manifest_org.id}',
            f'location_id={module_location.id}',
        ]
        for pair in expected_pairs:
            assert pair in cmd
        # changing the org and loc to check if correct org and loc is updated on the registration command
        session.organization.select(org_name=new_org.name)
        session.location.select(loc_name=new_loc.name)
        cmd = session.host.get_register_command(
            {
                'general.activation_keys': ak.name,
                'general.insecure': True,
            }
        )
        expected_pairs = [
            f'organization_id={new_org.id}',
            f'location_id={new_loc.id}',
        ]
        for pair in expected_pairs:
            assert pair in cmd


def test_negative_global_registration_without_ak(
    module_target_sat, function_org, function_location
):
    """Attempt to register a host without ActivationKey

    :id: 34122bf3-ae23-47ca-ba3d-da0653d8fd36

    :expectedresults: Generate command is disabled without ActivationKey
    """
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=function_org.name)
        session.location.select(loc_name=function_location.name)
        with pytest.raises(DisabledWidgetError) as context:
            session.host.get_register_command()
        assert 'Generate registration command button is disabled' in str(context.value)


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.pit_client
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_global_registration_end_to_end(
    module_activation_key,
    module_org,
    smart_proxy_location,
    default_os,
    default_smart_proxy,
    rhel_contenthost,
    module_target_sat,
):
    """Host registration form produces a correct registration command and host is
    registered successfully with it, remote execution and insights are set up

    :id: a02658bf-097e-47a8-8472-5d9f649ba07a

    :customerscenario: true

    :BZ: 1993874

    :expectedresults: Host is successfully registered, remote execution and insights
         client work out of the box

    :parametrized: yes
    """
    # make sure global parameters for rex and insights are set to true
    insights_cp = (
        module_target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_insights'})[0]
        .read()
    )
    rex_cp = (
        module_target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_remote_execution'})[0]
        .read()
    )

    if not insights_cp.value:
        module_target_sat.api.CommonParameter(id=insights_cp.id, value=1).update(['value'])
    if not rex_cp.value:
        module_target_sat.api.CommonParameter(id=rex_cp.id, value=1).update(['value'])

    # rex interface
    iface = 'eth0'
    # fill in the global registration form
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=smart_proxy_location.name)
        cmd = session.host.get_register_command(
            {
                'general.operating_system': default_os.title,
                'general.activation_keys': module_activation_key.name,
                'advanced.update_packages': True,
                'advanced.rex_interface': iface,
                'general.insecure': True,
            }
        )
    expected_pairs = [
        f'organization_id={module_org.id}',
        f'activation_keys={module_activation_key.name}',
        f'location_id={smart_proxy_location.id}',
        f'operatingsystem_id={default_os.id}',
        f'{default_smart_proxy.name}',
        'insecure',
        'update_packages=true',
    ]
    for pair in expected_pairs:
        assert pair in cmd
    # rhel repo required for insights client installation,
    # syncing it to the satellite would take too long
    rhelver = rhel_contenthost.os_version.major
    if rhelver > 7:
        rhel_contenthost.create_custom_repos(**settings.repos[f'rhel{rhelver}_os'])
    else:
        rhel_contenthost.create_custom_repos(
            **{f'rhel{rhelver}_os': settings.repos[f'rhel{rhelver}_os']}
        )
    # make sure there will be package availabe for update
    if rhel_contenthost.os_version.major == '6':
        package = FAKE_1_CUSTOM_PACKAGE
        repo_url = settings.repos.yum_1['url']
    else:
        package = FAKE_7_CUSTOM_PACKAGE
        repo_url = settings.repos.yum_3['url']
    rhel_contenthost.create_custom_repos(fake_yum=repo_url)
    rhel_contenthost.execute(f"yum install -y {package}")
    # run curl
    result = rhel_contenthost.execute(cmd)
    assert result.status == 0
    result = rhel_contenthost.execute('subscription-manager identity')
    assert result.status == 0
    # Assert that a yum update was made this day ("Update" or "I, U" in history)
    timezone_offset = rhel_contenthost.execute('date +"%:z"').stdout.strip()
    tzinfo = datetime.strptime(timezone_offset, '%z').tzinfo
    result = rhel_contenthost.execute('yum history | grep -E "I|U"')
    assert result.status == 0
    assert datetime.now(tzinfo).strftime('%Y-%m-%d') in result.stdout
    # Set "Connect to host using IP address"
    module_target_sat.api.Parameter(
        host=rhel_contenthost.hostname,
        name='remote_execution_connect_by_ip',
        parameter_type='boolean',
        value='True',
    ).create()
    # run insights-client via REX
    command = "insights-client --status"
    invocation_command = module_target_sat.cli_factory.job_invocation(
        {
            'job-template': 'Run Command - Script Default',
            'inputs': f'command={command}',
            'search-query': f"name ~ {rhel_contenthost.hostname}",
        }
    )
    # results provide all info but job invocation might not be finished yet
    result = (
        module_target_sat.api.JobInvocation()
        .search(
            query={'search': f'id={invocation_command["id"]} and host={rhel_contenthost.hostname}'}
        )[0]
        .read()
    )
    # make sure that task is finished
    task_result = module_target_sat.wait_for_tasks(
        search_query=(f'id = {result.task.id}'), search_rate=2, max_tries=60
    )
    assert task_result[0].result == 'success'
    host = (
        module_target_sat.api.Host()
        .search(query={'search': f'name={rhel_contenthost.hostname}'})[0]
        .read()
    )
    for interface in host.interface:
        interface_result = module_target_sat.api.Interface(host=host.id).search(
            query={'search': f'{interface.id}'}
        )[0]
        # more interfaces can be inside the host
        if interface_result.identifier == iface:
            assert interface_result.execution


@pytest.mark.tier2
def test_global_registration_form_populate(
    function_sca_manifest_org,
    function_activation_key,
    default_architecture,
    default_os,
    target_sat,
):
    """Host registration form should be populated automatically based on the host-group

    :id: b949e010-36b8-48b8-9907-36138342c72b

    :expectedresults: Some of the fields in the form should be populated based on host-group
        e.g. activation key, operating system, life-cycle environment, host parameters for
        remote-execution, insights setup.

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. create the host-group with activation key, operating system, host-parameters
        4. create a nested host-group to inherit values
        5. open the global registration form and select the same host-group
        6. check host registration form should be populated automatically based on the host-group

    :BZ: 2056469, 1994654, 1955421

    :customerscenario: true
    """
    hg_name = gen_string('alpha')
    hg_nested_name = gen_string('alpha')
    iface = gen_string('alpha')
    group_params = {'name': 'host_packages', 'value': constants.FAKE_0_CUSTOM_PACKAGE}
    parent_hg = target_sat.api.HostGroup(
        name=hg_name,
        organization=[function_sca_manifest_org],
        lifecycle_environment=function_sca_manifest_org.library.id,
        architecture=default_architecture,
        operatingsystem=default_os,
        content_view=function_sca_manifest_org.default_content_view.id,
        group_parameters_attributes=[group_params],
    ).create()
    target_sat.api.HostGroup(name=hg_nested_name, parent=parent_hg).create()
    new_org = target_sat.api.Organization().create()
    new_ak = target_sat.api.ActivationKey(
        content_view=new_org.default_content_view,
        environment=target_sat.api.LifecycleEnvironment(id=new_org.library.id),
        organization=new_org,
    ).create()
    with target_sat.ui_session() as session:
        session.organization.select(org_name=function_sca_manifest_org.name)
        session.hostgroup.update(
            f'{hg_name}/{hg_nested_name}',
            {
                'activation_keys.activation_keys': function_activation_key.name,
            },
        )
        cmd = session.host.get_register_command(
            {
                'general.host_group': f'{hg_name}/{hg_nested_name}',
                'advanced.rex_interface': iface,
                'general.insecure': True,
            },
            full_read=True,
        )
        assert hg_nested_name in cmd['general']['host_group']
        assert function_activation_key.name in cmd['general']['activation_key_helper']
        assert constants.FAKE_0_CUSTOM_PACKAGE in cmd['advanced']['install_packages_helper']

        session.organization.select(org_name=new_org.name)
        session.browser.refresh()
        registration_opts = {
            'general.insecure': True,
            'advanced.force': True,
        }
        # Select activation key explicitly due to SAT-27348
        if is_open('SAT-27348'):
            registration_opts['general.activation_keys'] = new_ak.name
        cmd = session.host.get_register_command(
            registration_opts,
            full_read=True,
        )
        assert new_org.name in cmd['general']['organization']
        assert new_ak.name in cmd['general']['activation_keys']


@pytest.mark.tier2
@pytest.mark.pit_client
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
@pytest.mark.no_containers
def test_global_registration_with_gpg_repo_and_default_package(
    module_activation_key, rhel_contenthost, target_sat, module_org
):
    """Host registration form produces a correct registration command and host is
    registered successfully with gpg repo enabled and have default package
    installed.

    :id: b5738b20-e281-4d0b-ac78-dcdc177b8c9f

    :expectedresults: Host is successfully registered, gpg repo is enabled
        and default package is installed.

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. update the 'host_packages' parameter in organization with package name e.g. zsh
        4. open the global registration form and update the gpg repo and key
        5. check host is registered successfully with installed same package
        6. check gpg repo is exist in registered host

    :parametrized: yes
    """
    client = rhel_contenthost
    repo_name = 'foreman_register'
    repo_url = settings.repos.gr_yum_repo.url
    repo_gpg_url = settings.repos.gr_yum_repo.gpg_url
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)

        cmd = session.host.get_register_command(
            {
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
                'advanced.install_packages': 'mlocate zsh',
                'advanced.repository': repo_url,
                'advanced.repository_gpg_key_url': repo_gpg_url,
            }
        )

    # rhel repo required for insights client installation,
    # syncing it to the satellite would take too long
    rhelver = client.os_version.major
    if rhelver > 7:
        repos = {f'rhel{rhelver}_os': settings.repos[f'rhel{rhelver}_os']['baseos']}
    else:
        repos = {
            'rhel7_os': settings.repos['rhel7_os'],
            'rhel7_extras': settings.repos['rhel7_extras'],
        }
    client.create_custom_repos(**repos)
    # run curl
    result = client.execute(cmd)
    assert result.status == 0
    result = client.execute('yum list installed | grep mlocate')
    assert result.status == 0
    assert 'mlocate' in result.stdout
    result = client.execute('yum -v repolist')
    assert result.status == 0
    assert repo_name in result.stdout
    assert repo_url in result.stdout


@pytest.mark.tier3
@pytest.mark.rhel_ver_match('9')
def test_global_re_registration_host_with_force_ignore_error_options(
    module_activation_key, rhel_contenthost, module_target_sat, module_org
):
    """If the ignore_error and force checkbox is checked then registered host can
    get re-registered without any error.

    :id: 8f0ecc13-5d18-4adb-acf5-3f3276dccbb7

    :expectedresults: Verify the force and ignore checkbox options

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. open the global registration form and select --force and --Ignore Errors option
        4. registered the host with generated curl command
        5. re-register the same host again and check it is getting registered

    :parametrized: yes
    """
    client = rhel_contenthost
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        cmd = session.host.get_register_command(
            {
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
                'advanced.ignore_error': True,
            }
        )
    client.execute(cmd)
    result = client.execute('subscription-manager identity')
    assert result.status == 0
    # rerun the register command
    client.execute(cmd)
    result = client.execute('subscription-manager identity')
    assert result.status == 0


@pytest.mark.tier2
@pytest.mark.rhel_ver_match('8')
def test_global_registration_token_restriction(
    module_activation_key, rhel_contenthost, module_target_sat, module_org
):
    """Global registration token should be only used for registration call, it
    should be restricted for any other api calls.

    :id: 4528b5c6-0a6d-40cd-857a-68b76db2179b

    :expectedresults: global registration token should be restricted for any api calls
        other than the registration

    :steps:
        1. open the global registration form and generate the curl token
        2. use that curl token to execute other api calls e.g. GET /hosts, /users

    :parametrized: yes
    """
    client = rhel_contenthost
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        cmd = session.host.get_register_command(
            {
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
            }
        )

    pattern = re.compile("Authorization.*(?=')")
    auth_header = re.search(pattern, cmd).group()

    # build curl
    curl_users = f'curl -X GET -k -H {auth_header} -i {module_target_sat.url}/api/users/'
    curl_hosts = f'curl -X GET -k -H {auth_header} -i {module_target_sat.url}/api/hosts/'
    for curl_cmd in (curl_users, curl_hosts):
        result = client.execute(curl_cmd)
        assert result.status == 0
        assert 'Unable to authenticate user' in result.stdout


@pytest.mark.rhel_ver_match('8')
def test_positive_host_registration_with_non_admin_user(
    test_name,
    module_sca_manifest_org,
    module_location,
    module_target_sat,
    rhel_contenthost,
    module_activation_key,
):
    """Register hosts from a non-admin user with only register_hosts, edit_hosts
    and view_organization permissions

    :id: 35458bbc-4556-41b9-ba26-ae0b15179731

    :expectedresults: User with register hosts permission able to register hosts.
    """
    user_password = gen_string('alpha')
    org = module_sca_manifest_org
    role = module_target_sat.api.Role(organization=[org]).create()

    user_permissions = {
        'Organization': ['view_organizations'],
        'Host': ['view_hosts'],
    }
    module_target_sat.api_factory.create_role_permissions(role, user_permissions)
    user = module_target_sat.api.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[org],
        location=[module_location],
        default_organization=org,
        default_location=module_location,
    ).create()
    role = module_target_sat.cli.Role.info({'name': 'Register hosts'})
    module_target_sat.cli.User.add_role({'id': user.id, 'role-id': role['id']})

    with module_target_sat.ui_session(
        test_name, user=user.login, password=user_password
    ) as session:
        cmd = session.host_new.get_register_command(
            {
                'general.insecure': True,
                'general.activation_keys': module_activation_key.name,
            }
        )

        result = rhel_contenthost.execute(cmd)
        assert result.status == 0, f'Failed to register host: {result.stderr}'

        # Verify server.hostname and server.port from subscription-manager config
        assert (
            module_target_sat.hostname == rhel_contenthost.subscription_config['server']['hostname']
        )
        assert rhel_contenthost.subscription_config['server']['port'] == constants.CLIENT_PORT


@pytest.mark.tier2
def test_positive_global_registration_form(
    module_activation_key, module_org, smart_proxy_location, default_os, target_sat
):
    """Host registration form produces a correct curl command for various inputs

    :id: f81c2ec4-85b1-4372-8e63-464ddbf70296

    :customerscenario: true

    :expectedresults: The curl command contains all required parameters
    """
    # rex and insights parameters are only specified in curl when differing from
    # inerited parameters
    result = (
        target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_remote_execution'})[0]
        .read()
    )
    rex_value = not result.value
    result = (
        target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_insights'})[0]
        .read()
    )
    insights_value = not result.value
    hostgroup = target_sat.api.HostGroup(
        organization=[module_org], location=[smart_proxy_location]
    ).create()
    iface = 'eth0'
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=smart_proxy_location.name)
        cmd = session.host.get_register_command(
            {
                'advanced.setup_insights': 'Yes (override)' if insights_value else 'No (override)',
                'advanced.setup_rex': 'Yes (override)' if rex_value else 'No (override)',
                'general.insecure': True,
                'general.host_group': hostgroup.name,
                'general.operating_system': default_os.title,
                'general.activation_keys': module_activation_key.name,
                'advanced.update_packages': True,
                'advanced.rex_interface': iface,
            }
        )
    expected_pairs = [
        f'organization_id={module_org.id}',
        f'activation_keys={module_activation_key.name}',
        f'hostgroup_id={hostgroup.id}',
        f'location_id={smart_proxy_location.id}',
        f'operatingsystem_id={default_os.id}',
        f'remote_execution_interface={iface}',
        f'setup_insights={"true" if insights_value else "false"}',
        f'setup_remote_execution={"true" if rex_value else "false"}',
        f'{target_sat.hostname}',
        'insecure',
        'update_packages=true',
    ]
    for pair in expected_pairs:
        assert pair in cmd


@pytest.mark.tier2
@pytest.mark.rhel_ver_match('8')
def test_global_registration_with_capsule_host(
    capsule_configured,
    rhel_contenthost,
    module_org,
    module_location,
    module_product,
    default_os,
    module_lce_library,
    target_sat,
):
    """Host registration form produces a correct registration command and host is
    registered successfully with selected capsule from form.

    :id: 6356c6d0-ee45-4ad7-8a0e-484d3490bc58

    :expectedresults: Host is successfully registered with capsule host,
        remote execution and insights client work out of the box

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. integrate capsule and sync content
        4. open the global registration form and select the same capsule
        5. check host is registered successfully with selected capsule

    :parametrized: yes

    :CaseAutomation: Automated
    """
    client = rhel_contenthost
    repo = target_sat.api.Repository(
        url=settings.repos.yum_1.url,
        content_type=REPO_TYPE['yum'],
        product=module_product,
    ).create()
    # Sync all repositories in the product
    module_product.sync()
    capsule = target_sat.api.Capsule(id=capsule_configured.nailgun_capsule.id).search(
        query={'search': f'name={capsule_configured.hostname}'}
    )[0]
    module_org = target_sat.api.Organization(id=module_org.id).read()
    module_org.smart_proxy.append(capsule)
    module_location = target_sat.api.Location(id=module_location.id).read()
    module_location.smart_proxy.append(capsule)
    module_org.update(['smart_proxy'])
    module_location.update(['smart_proxy'])

    # Associate the lifecycle environment with the capsule
    capsule.content_add_lifecycle_environment(data={'environment_id': module_lce_library.id})
    result = capsule.content_lifecycle_environments()
    # TODO result is not used, please add assert once you fix the test

    # Create a content view with the repository
    cv = target_sat.api.ContentView(organization=module_org, repository=[repo]).create()

    # Publish new version of the content view
    cv.publish()
    cv = cv.read()

    assert len(cv.version) == 1

    activation_key = target_sat.api.ActivationKey(
        content_view=cv, environment=module_lce_library, organization=module_org
    ).create()

    # Assert that a task to sync lifecycle environment to the capsule
    # is started (or finished already)
    sync_status = capsule.content_get_sync()
    assert len(sync_status['active_sync_tasks']) >= 1 or sync_status['last_sync_time']

    # Wait till capsule sync finishes
    for task in sync_status['active_sync_tasks']:
        target_sat.api.ForemanTask(id=task['id']).poll()
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        cmd = session.host.get_register_command(
            {
                'general.organization': module_org.name,
                'general.location': module_location.name,
                'general.operating_system': default_os.title,
                'general.capsule': capsule_configured.hostname,
                'general.activation_keys': activation_key.name,
                'general.insecure': True,
            }
        )
    client.create_custom_repos(rhel7=settings.repos.rhel7_os)
    # run curl
    client.execute(cmd)
    result = client.execute('subscription-manager identity')
    assert result.status == 0
    assert module_lce_library.name in result.stdout
    assert module_org.name in result.stdout


@pytest.mark.tier2
@pytest.mark.rhel_ver_match('[^6].*')
def test_subscription_manager_install_from_repository(
    module_activation_key, module_os, rhel_contenthost, target_sat, module_org
):
    """Host registration form produces a correct registration command and
    subscription-manager can be installed from a custom repository before
    registration is completed.

    :id: b7a44f32-90b2-4fd6-b65b-5a3d2a5c5deb

    :customerscenario: true

    :expectedresults: Host is successfully registered, repo is enabled
        on advanced tab and subscription-manager is installed.

    :steps:
        1. Create activation-key
        2. Open the global registration form, add repo and activation key
        3. Add 'subscription-manager' to install packages field
        4. Check subscription-manager was installed from repo_name

    :parametrized: yes

    :BZ: 1923320
    """
    client = rhel_contenthost
    repo_name = 'foreman_register'
    rhel_ver = rhel_contenthost.os_version.major
    repo_url = settings.repos.get(f'rhel{rhel_ver}_os')
    if isinstance(repo_url, dict):
        repo_url = repo_url['baseos']
    # Ensure subs-man is installed from repo_name by removing existing package.
    result = client.execute('rpm --erase --nodeps subscription-manager')
    assert result.status == 0
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        cmd = session.host.get_register_command(
            {
                'general.operating_system': module_os.title,
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
                'advanced.install_packages': 'subscription-manager',
                'advanced.repository': repo_url,
            }
        )

    # run curl
    result = client.execute(cmd)
    assert result.status == 0
    result = client.execute('yum repolist')
    assert repo_name in result.stdout
    assert result.status == 0


@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_positive_global_registration_with_setup_insights(
    module_os,
    rhel_contenthost,
    module_activation_key,
    target_sat,
    module_org,
    module_location,
):
    """Verify that the host is successfully registered with setup_insights=true and does not remain in build mode.

    :id: 729f53c0-853b-11ef-b738-8242a35ddd79

    :steps:
        1. Generate a curl command which should have setup_insights=true in it
        2. Execute the command

    :expectedresults: No options should leave the host in build mode at the end of successful registration, specifically not insights configuration/setup.

    :Verifies: SAT-26417

    :customerscenario: true
    """
    rhel_ver = rhel_contenthost.os_version.major
    repo_url = getattr(settings.repos, f'rhel{rhel_ver}_os', None)
    rhel_contenthost.create_custom_repos(**repo_url)
    result = rhel_contenthost.api_register(
        target_sat,
        organization=module_org,
        activation_keys=[module_activation_key.name],
        location=module_location,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'
    with target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        cmd = session.host.get_register_command(
            {
                'general.operating_system': module_os.title,
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.setup_insights': 'Yes (override)',
                'advanced.force': True,
            }
        )
        cmd_link = re.search(r"'https://ip-[^']*' -H '[^']*'", cmd)
        output = rhel_contenthost.execute(
            f'set -o pipefail && curl -sS --insecure {cmd_link.group()} | sed "s/bash/bash -x/g"  | bash -x'
        )
        assert f'The registered system name is: {rhel_contenthost.hostname}' in output.stdout
        assert (
            f'Host {[rhel_contenthost.hostname]} successfully configured, but failed to set built status.'
            not in output.stdout
        )
        status = session.host.host_status(rhel_contenthost.hostname)
        assert 'Build: Installed' in status
        facts = session.host.build_mode(rhel_contenthost.hostname, 'Facts')
        assert 'insights_client' in facts['permission_denied']
        assert 'Successfully updated the system facts' in output.stdout
