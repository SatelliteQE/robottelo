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

RHEL7_VER = '7.9'
RHEL8_VER = '8.10'
RHEL9_VER = '9.4'


@pytest.mark.e2e
@pytest.mark.parametrize(
    'upgrade_path',
    [
        # {'source_version': RHEL7_VER, 'target_version': RHEL8_VER},
        {'source_version': RHEL8_VER, 'target_version': RHEL9_VER},
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
    result = module_target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    assert result['success'] == '1'

    custom_leapp_host.clean_cached_properties()
    assert str(custom_leapp_host.os_version) == upgrade_path['target_version']
