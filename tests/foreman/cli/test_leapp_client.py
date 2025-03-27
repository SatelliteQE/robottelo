"""Tests for leapp upgrade of content hosts with Satellite

:Requirement: leapp

:CaseComponent: Leappintegration

:Team: Rocket

:CaseImportance: Critical

:CaseAutomation: Automated

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import RHEL8_VER, RHEL9_VER
from robottelo.utils import ohsnap


@pytest.mark.e2e
@pytest.mark.parametrize(
    'upgrade_path',
    [
        {
            'source_version': settings.leapp.source_rhel,
            'target_version': settings.leapp.target_rhel,
        },
    ],
    ids=lambda upgrade_path: f'{upgrade_path["source_version"]}'
    f'_to_{upgrade_path["target_version"]}',
)
@pytest.mark.parametrize('auth_type', ['admin', 'non-admin'])
def test_positive_leapp_upgrade_rhel(
    request,
    module_target_sat,
    custom_leapp_host,
    upgrade_path,
    verify_target_repo_on_satellite,
    precondition_check_upgrade_and_install_leapp_tool,
    auth_type,
    module_sca_manifest_org,
):
    """Test to upgrade RHEL host to next major RHEL release using leapp preupgrade and leapp upgrade
    job templates

    :id: 8eccc689-3bea-4182-84f3-c121e95d54c3

    :steps:
        1. Import a subscription manifest and enable, sync source & target repositories
        2. Create LCE, Create CV, add repositories to it, publish and promote CV, Create AK, etc.
        3. Register content host with AK
        4. Verify that target rhel repositories are enabled on Satellite
        5. Update all packages, install leapp tool and fix inhibitors
        6. Run Leapp Preupgrade and Leapp Upgrade job template

    :expectedresults:
        1. Update RHEL OS major version to another major version
    """

    login = settings.server.admin_username
    password = settings.server.admin_password
    org = module_sca_manifest_org
    if auth_type == 'non-admin':
        login = gen_string('alpha')
        roles = ['Organization admin', 'Remote Execution Manager', 'Remote Execution User']
        user = module_target_sat.cli_factory.user(
            {
                'admin': False,
                'login': login,
                'password': password,
                'organization-ids': org.id,
            }
        )
        request.addfinalizer(lambda: module_target_sat.cli.User.delete({'login': user.login}))
        for role in roles:
            module_target_sat.cli.User.add_role({'id': user['id'], 'login': login, 'role': role})
    # Workaround for https://issues.redhat.com/browse/RHEL-55871
    assert custom_leapp_host.execute('echo \'ulimit -n 16384\' > /root/.bashrc').status == 0
    # Run leapp preupgrade job
    invocation_command = module_target_sat.cli_factory.job_invocation_with_credentials(
        {
            'job-template': 'Run preupgrade via Leapp',
            'search-query': f'name = {custom_leapp_host.hostname}',
            'organization-id': org.id,
        },
        (login, password),
    )
    result = module_target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    assert result['success'] == '1'
    # Run leapp upgrade job
    invocation_command = module_target_sat.cli_factory.job_invocation_with_credentials(
        {
            'job-template': 'Run upgrade via Leapp',
            'search-query': f'name = {custom_leapp_host.hostname}',
            'organization-id': org.id,
            'inputs': 'Reboot=false',
        },
        (login, password),
    )
    custom_leapp_host.power_control(state='reboot')
    custom_leapp_host.wait_for_connection()
    result = module_target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    assert result['success'] == '1'

    custom_leapp_host.clean_cached_properties()
    assert str(custom_leapp_host.os_version) == upgrade_path['target_version']


@pytest.mark.no_containers
@pytest.mark.parametrize(
    'upgrade_path',
    [
        {'source_version': RHEL8_VER, 'target_version': RHEL9_VER},
    ],
    ids=lambda upgrade_path: f'{upgrade_path["source_version"]}'
    f'_to_{upgrade_path["target_version"]}',
)
@pytest.mark.parametrize(
    'setting_update',
    ['remote_execution_global_proxy=False'],
    ids=["no_global_proxy"],
    indirect=True,
)
def test_positive_ygdrassil_client_after_leapp_upgrade(
    request,
    module_target_sat,
    custom_leapp_host,
    upgrade_path,
    verify_target_repo_on_satellite,
    precondition_check_upgrade_and_install_leapp_tool,
    module_sca_manifest_org,
    module_capsule_configured_mqtt,
    smart_proxy_location,
    setting_update,
    function_leapp_ak,
    module_leapp_lce,
):
    """Test to upgrade a RHEL host to next major RHEL release using leapp while maintaining a working pull-mqtt rex setup

    :id: ba3a0eb6-779f-46b5-b4b9-c10fc182e974

    :steps:
        1. Import a subscription manifest and enable, sync source & target repositories
        2. Create LCE, Create CV, add repositories to it, publish and promote CV, Create AK, etc.
        3. Register content host with AK
        4. Verify that target rhel repositories are enabled on Satellite
        5. Update all packages, install leapp tool and fix inhibitors
        6. Set up mqtt capsule, sync content to it, re-register host to it
        7. Run Leapp Preupgrade and Leapp Upgrade job template

    :expectedresults:
        1. Update RHEL OS major version to another major version
        2. Check that pull mode rex is working after upgrade

    :CaseComponent: RemoteExecution
    """
    login = settings.server.admin_username
    password = settings.server.admin_password
    org = module_sca_manifest_org

    client_repo = ohsnap.dogfood_repository(
        settings.ohsnap,
        product='client',
        repo='client',
        release='client',
        os_release=custom_leapp_host.os_version.major,
    )

    # Update module_capsule_configured_mqtt to include org/loc
    module_target_sat.cli.Capsule.update(
        {
            'name': module_capsule_configured_mqtt.hostname,
            'organization-ids': module_sca_manifest_org.id,
            'location-ids': smart_proxy_location.id,
        }
    )
    # Associated LCE with pull provider capsule and sync
    module_capsule_configured_mqtt.nailgun_capsule.content_add_lifecycle_environment(
        data={'environment_id': module_leapp_lce.id}
    )
    # Update capsule's download policy to on_demand
    module_capsule_configured_mqtt.update_download_policy('on_demand')
    # Sync repo metatdata
    sync_status = module_capsule_configured_mqtt.nailgun_capsule.content_sync(timeout=800)
    assert sync_status['result'] == 'success', 'Capsule sync task failed.'

    # set releasever for activation key so that global registration can access the version-specific rhel repo
    module_target_sat.cli.ActivationKey.update(
        {
            'id': function_leapp_ak.id,
            'organization-id': module_sca_manifest_org.id,
            'release-version': RHEL8_VER,
        }
    )

    # re-register host with pull provider capsule
    result = custom_leapp_host.register(
        module_sca_manifest_org,
        smart_proxy_location,
        function_leapp_ak.name,
        module_capsule_configured_mqtt,
        setup_remote_execution_pull=True,
        repo_data=f'repo={client_repo.baseurl}',
        ignore_subman_errors=True,
        force=True,
    )
    assert result.status == 0, f'Failed to register host: {result.stderr}'

    service_name = custom_leapp_host.get_yggdrasil_service_name()
    result = custom_leapp_host.execute(f'systemctl status {service_name}')
    assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'

    # unset releasever in AK
    module_target_sat.cli.ActivationKey.update(
        {
            'id': function_leapp_ak.id,
            'organization-id': module_sca_manifest_org.id,
            'release-version': '',
        }
    )

    # Workaround for https://issues.redhat.com/browse/RHEL-55871
    assert custom_leapp_host.execute('echo \'ulimit -n 16384\' > /root/.bashrc').status == 0
    # Run leapp preupgrade job
    invocation_command = module_target_sat.cli_factory.job_invocation_with_credentials(
        {
            'job-template': 'Run preupgrade via Leapp',
            'search-query': f'name = {custom_leapp_host.hostname}',
            'organization-id': org.id,
        },
        (login, password),
    )
    result = module_target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    assert result['success'] == '1'

    # Run leapp upgrade job
    invocation_command = module_target_sat.cli_factory.job_invocation_with_credentials(
        {
            'job-template': 'Run upgrade via Leapp',
            'search-query': f'name = {custom_leapp_host.hostname}',
            'organization-id': org.id,
            'inputs': 'Reboot=false',
        },
        (login, password),
    )

    custom_leapp_host.power_control(state='reboot')
    custom_leapp_host.wait_for_connection()
    result = module_target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    assert result['success'] == '1'

    custom_leapp_host.clean_cached_properties()
    assert str(custom_leapp_host.os_version) == upgrade_path['target_version']

    # check mqtt still works after upgrade
    service_name = custom_leapp_host.get_yggdrasil_service_name()
    result = custom_leapp_host.execute(f'systemctl status {service_name}')
    assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'

    invocation_command = module_target_sat.cli_factory.job_invocation_with_credentials(
        {
            'job-template': 'Run Command - Script Default',
            'inputs': "command=ls",
            'search-query': f"name ~ {custom_leapp_host.hostname}",
        },
        (login, password),
    )
    result = module_target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    assert result['success'] == '1'
