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
import datetime

import pytest
from fauxfactory import gen_string

from robottelo import constants
from robottelo.config import settings
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_7_CUSTOM_PACKAGE


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.tier3
@pytest.mark.rhel_ver_match('[^6]')
def test_positive_global_registration_end_to_end(
    session,
    module_activation_key,
    module_org,
    smart_proxy_location,
    default_os,
    default_smart_proxy,
    rhel_contenthost,
    target_sat,
):
    """Host registration form produces a correct registration command and host is
    registered successfully with it, remote execution and insights are set up

    :id: a02658bf-097e-47a8-8472-5d9f649ba07a

    :customerscenario: true

    :BZ: 1993874

    :expectedresults: Host is successfully registered, remote execution and insights
         client work out of the box

    :parametrized: yes

    :CaseLevel: Integration
    """
    # make sure global parameters for rex and insights are set to true
    insights_cp = (
        target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_insights'})[0]
        .read()
    )
    rex_cp = (
        target_sat.api.CommonParameter()
        .search(query={'search': 'name=host_registration_remote_execution'})[0]
        .read()
    )

    if not insights_cp.value:
        target_sat.api.CommonParameter(id=insights_cp.id, value=1).update(['value'])
    if not rex_cp.value:
        target_sat.api.CommonParameter(id=rex_cp.id, value=1).update(['value'])

    # rex interface
    iface = 'eth0'
    # fill in the global registration form
    with target_sat.ui_session() as session:
        cmd = session.host_new.get_register_command(
            {
                'general.organization': module_org.name,
                'general.location': smart_proxy_location.name,
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
    assert rhel_contenthost.identity
    # Assert that a yum update was made this day ("Update" or "I, U" in history)
    timezone_offset = rhel_contenthost.execute('date +"%:z"').stdout.strip()
    tzinfo = datetime.strptime(timezone_offset, '%z').tzinfo
    result = rhel_contenthost.execute('yum history | grep U')
    assert result.status == 0
    assert datetime.now(tzinfo).strftime('%Y-%m-%d') in result.stdout
    # Set "Connect to host using IP address"
    target_sat.api.Parameter(
        host=rhel_contenthost.hostname,
        name='remote_execution_connect_by_ip',
        parameter_type='boolean',
        value='True',
    ).create()
    # run insights-client via REX
    command = "insights-client --status"
    invocation_command = target_sat.cli_factory.make_job_invocation(
        {
            'job-template': 'Run Command - Script Default',
            'inputs': f'command={command}',
            'search-query': f"name ~ {rhel_contenthost.hostname}",
        }
    )
    # results provide all info but job invocation might not be finished yet
    result = (
        target_sat.api.JobInvocation()
        .search(
            query={'search': f'id={invocation_command["id"]} and host={rhel_contenthost.hostname}'}
        )[0]
        .read()
    )
    # make sure that task is finished
    task_result = target_sat.wait_for_tasks(
        search_query=(f'id = {result.task.id}'), search_rate=2, max_tries=60
    )
    assert task_result[0].result == 'success'
    host = rhel_contenthost.nailgun_host.read()
    for interface in host.interface:
        interface_result = target_sat.api.Interface(host=host.id).search(
            query={'search': f'{interface.id}'}
        )[0]
        # more interfaces can be inside the host
        if interface_result.identifier == iface:
            assert interface_result.execution


@pytest.mark.tier2
def test_global_registration_form_populate(
    session,
    module_org,
    module_ak_with_cv,
    module_lce,
    module_promoted_cv,
    default_architecture,
    default_os,
    target_sat,
):
    """Host registration form should be populated automatically based on the host-group

    :id: b949e010-36b8-48b8-9907-36138342c72b

    :expectedresults: Some of the fields in the form should be populated based on host-group
        e.g. activation key, operating system, life-cycle environment, host parameters for
        remote-execution, insights setup.

    :CaseLevel: Integration

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. create the host-group with activation key, operating system, host-parameters
        4. Open the global registration form and select the same host-group
        5. check host registration form should be populated automatically based on the host-group

    :BZ: 2056469

    :CaseAutomation: Automated
    """
    hg_name = gen_string('alpha')
    iface = gen_string('alpha')
    group_params = {'name': 'host_packages', 'value': constants.FAKE_0_CUSTOM_PACKAGE}
    target_sat.api.HostGroup(
        name=hg_name,
        organization=[module_org],
        lifecycle_environment=module_lce,
        architecture=default_architecture,
        operatingsystem=default_os,
        content_view=module_promoted_cv,
        group_parameters_attributes=[group_params],
    ).create()
    with target_sat.ui_session() as session:
        session.hostgroup.update(
            hg_name,
            {
                'activation_keys.activation_keys': module_ak_with_cv.name,
            },
        )
        cmd = session.host_new.get_register_command(
            {
                'general.host_group': hg_name,
                'advanced.rex_interface': iface,
                'general.insecure': True,
            },
            full_read=True,
        )

        assert hg_name in cmd['general']['host_group']
        assert module_ak_with_cv.name in cmd['general']['activation_key_helper']
        assert module_lce.name in cmd['advanced']['life_cycle_env_helper']
        assert constants.FAKE_0_CUSTOM_PACKAGE in cmd['advanced']['install_packages_helper']


@pytest.mark.rhel_ver_match('[^6]')
@pytest.mark.tier3
@pytest.mark.usefixtures('enable_capsule_for_registration')
def test_global_re_registration_host_with_force_ignore_error_options(
    session, module_activation_key, default_os, default_smart_proxy, rhel_contenthost, target_sat
):
    """If the ignore_error and force checkbox is checked then registered host can
    get re-registered without any error.

    :id: 8f0ecc13-5d18-4adb-acf5-3f3276dccbb7

    :expectedresults: Verify the force and ignore checkbox options

    :CaseLevel: Integration

    :steps:
        1. create and sync repository
        2. create the content view and activation-key
        3. open the global registration form and select --force and --Ignore Errors option
        4. registered the host with generated curl command
        5. re-register the same host again and check it is getting registered

    :parametrized: yes
    """
    client = rhel_contenthost
    with target_sat.ui_session() as session:
        cmd = session.host_new.get_register_command(
            {
                'general.operating_system': default_os.title,
                'general.capsule': default_smart_proxy.name,
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
                'advanced.ignore_error': True,
            }
        )
    client.execute(cmd)
    assert client.identity
    # rerun the register command
    client.execute(cmd)
    assert client.identity


@pytest.mark.rhel_ver_match('8')
def test_host_facts_upload_on_host_registration(
    session,
    module_target_sat,
    module_activation_key,
    rhel_contenthost,
    default_os,
    default_smart_proxy,
    module_entitlement_manifest_org,
):
    """Host Facts are uploaded to satellite when host is registered using global registration form.

    :id: fe16d66a-8e0b-4872-a6bf-36c5c12d8d5c

    :CaseLevel: Integration

    :steps:
        1. Enable and sync any repository.
        2. Create CV, add synced repo and publish it to library environment.
        3. Create an activation key
        4. Register host using global registration curl command.
        5. Navigate to Hosts -> All Hosts -> Hostname

    :expectedresults: Verify that host facts are uploaded to satellite when host
        is registered using global registration

    :BZ: 2001552

    :CaseAutomation: Automated

    :customerscenario: true

    :CaseImportance: High

    :parametrized: yes
    """
    module_target_sat.api_factory.enable_sync_redhat_repo(
        constants.REPOS['rhel8_bos'], module_entitlement_manifest_org.id
    )
    cv = module_target_sat.api.ContentView(organization=module_entitlement_manifest_org).create()
    cv.publish()
    with module_target_sat.ui_session() as session:
        cmd = session.host_new.get_register_command(
            {
                'general.organization': module_entitlement_manifest_org.name,
                'general.activation_keys': module_activation_key.name,
                'general.insecure': True,
                'advanced.force': True,
            }
        )
        rhel_contenthost.execute(cmd)
        host_info = session.host_new.get_details(module_target_sat.hostname)
        assert 'Facts' in host_info['facts_details']
