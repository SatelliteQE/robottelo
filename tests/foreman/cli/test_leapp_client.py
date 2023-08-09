"""Tests for leapp upgrade of content hosts with Satellite

:Requirement: leapp

:CaseLevel: Integration

:CaseComponent: LeappIntegration

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
import pytest
from wait_for import wait_for

from robottelo.cli.repository import Repository
from robottelo.constants import PRDS

RHEL_REPOS = {
    'rhel7_9_server': {
        'id': 'rhel-7-server-rpms',
        'name': 'Red Hat Enterprise Linux 7 Server RPMs x86_64 7.9',
        'releasever': '7.9',
        'reposet': 'Red Hat Enterprise Linux 7 Server (RPMs)',
        'product': 'Red Hat Enterprise Linux Server',
    },
    'rhel7_server_extras': {
        'id': 'rhel-7-server-extras-rpms',
        'name': 'Red Hat Enterprise Linux 7 Server - Extras RPMs x86_64',
        'releasever': '7',
        'reposet': 'Red Hat Enterprise Linux 7 Server - Extras (RPMs)',
        'product': 'Red Hat Enterprise Linux Server',
    },
    'rhel8_8_bos': {
        'id': 'rhel-8-for-x86_64-baseos-rpms',
        'name': 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs 8.8',
        'releasever': '8.8',
        'reposet': 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS (RPMs)',
    },
    'rhel8_8_aps': {
        'id': 'rhel-8-for-x86_64-appstream-rpms',
        'name': 'Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8.8',
        'releasever': '8.8',
        'reposet': 'Red Hat Enterprise Linux 8 for x86_64 - AppStream (RPMs)',
    },
    'rhel9_2_bos': {
        'id': 'rhel-9-for-x86_64-baseos-rpms',
        'name': 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS RPMs 9.2',
        'releasever': '9.2',
        'reposet': 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS (RPMs)',
    },
    'rhel9_2_aps': {
        'id': 'rhel-9-for-x86_64-appstream-rpms',
        'name': 'Red Hat Enterprise Linux 9 for x86_64 - AppStream RPMs 9.2',
        'releasever': '9.2',
        'reposet': 'Red Hat Enterprise Linux 9 for x86_64 - AppStream (RPMs)',
    },
}


def create_activation_key(satellite, content_view, lifecycle_env, organization):
    """Create activation key uinsg specific entities"""
    return satellite.api.ActivationKey(
        content_view=content_view,
        environment=lifecycle_env,
        organization=organization,
    ).create()


def register_host_with_satellite(satellite, custom_host, organization, activation_key):
    """Register content host with satellite"""
    result = custom_host.register(organization, None, activation_key.name, satellite)
    assert result.status == 0, f"Failed to register host: {result.stderr}"


def verify_target_repo_on_satellite(
    satellite, content_view, organization, lifecycle_env, target_rhel
):
    """Verify target rhel version repositories has enabled on Satellite Server"""
    cmd_out = Repository.list(
        {
            'search': f'content_label ~ {target_rhel}',
            'content-view-id': content_view.id,
            'organization-id': organization.id,
            'lifecycle-environment-id': lifecycle_env.id,
        }
    )
    repo_names = [out['name'] for out in cmd_out]
    if 'rhel-9' in target_rhel:
        assert RHEL_REPOS['rhel9_2_bos']['name'] in repo_names
        assert RHEL_REPOS['rhel9_2_aps']['name'] in repo_names
    else:
        # placeholder for target_rhel - rhel-8
        pass


def precondition_check_upgrade_and_install_leapp_tool(custom_host, source_rhel):
    """Clean-up directory, set rhel release version, update system and install leapp tool"""
    # Remove directory if in-place upgrade already performed from RHEL7 to RHEL8
    custom_host.run('rm -rf /root/tmp_leapp_py3')
    custom_host.run('dnf clean all')
    custom_host.run('dnf repolist')
    custom_host.run(f'subscription-manager release --set {source_rhel}')
    assert custom_host.run('dnf update -y').status == 0
    assert custom_host.run('dnf install leapp-upgrade -y').status == 0


def fix_inhibitors(custom_host, source_rhel):
    """Fix inhibitors to avoid hard stop of Leapp tool execution"""
    if '8' in source_rhel:
        # 1. Firewalld Configuration AllowZoneDrifting Is Unsupported
        custom_host.run(
            'sed -i "s/^AllowZoneDrifting=.*/AllowZoneDrifting=no/" /etc/firewalld/firewalld.conf'
        )
        # 2. Newest installed kernel not in use
        if custom_host.run('needs-restarting -r').status == 1:
            custom_host.power_control(state='reboot', ensure=True)
    else:
        # placeholder for source_rhel - 7
        pass


@pytest.fixture(scope="module")
def setup_env(module_target_sat, module_sca_manifest_org):
    """Create essential things and returning in form of directory for use"""
    # 1. Import a subscription manifest
    lc_env = module_target_sat.api.LifecycleEnvironment(
        organization=module_sca_manifest_org
    ).create()
    c_view = module_target_sat.api.ContentView(organization=module_sca_manifest_org).create()
    return {
        'organization': module_sca_manifest_org,
        'satellite': module_target_sat,
        'environment': lc_env,
        'contentview': c_view,
    }


@pytest.mark.no_containers
@pytest.mark.parametrize(
    'custom_host',
    [
        {'deploy_rhel_version': '8.8'},
    ],
    ids=['RHEL8.8'],
    indirect=True,
)
def test_upgrade_rhel8_to_rhel9(
    setup_env,
    custom_host,
):
    """Test to upgrade RHEL host to next major RHEL Realse with Leapp Preupgrade and Leapp Upgrade
    Job templates

    :id: 7add9b32-a13a-4e65-973c-cd64326b332a

    :Steps:
        1. Import a subscription manifest and enable, sync source & target repositories
        2. Create LCE, Create CV, add repositories to it, publish and promote CV, Create AK, etc.
        3. Register content host with AK
        4. Varify target rhel repositories are enable on Satellite
        5. Update all packages, install leapp tool and fix inhibitors
        6. Run Leapp Preupgrade and Leapp Upgrade job template

    :expectedresults:
        1. Update RHEL OS major version to another major version

    """
    # rhel_contenthost = custom_host
    organization = setup_env['organization']
    target_sat = setup_env['satellite']
    lc_env = setup_env['environment']
    cv = setup_env['contentview']

    # Enable rhel8/rhel9 bos, aps repository and add in content view
    all_repos = []
    for rh_repo_key in RHEL_REPOS.keys():
        release_version = RHEL_REPOS[rh_repo_key]['releasever']
        if release_version == '8.8' or release_version == '9.2':
            prod = rh_repo_key.split('_')[0]
            repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
                basearch=custom_host.arch,
                org_id=organization.id,
                product=PRDS[prod],
                repo=RHEL_REPOS[rh_repo_key]['name'],
                reposet=RHEL_REPOS[rh_repo_key]['reposet'],
                releasever=release_version,
            )
            rh_repo = target_sat.api.Repository(id=repo_id).read()
            all_repos.append(rh_repo)
            # sync repo
            rh_repo.sync(timeout=1800)
        else:
            pass
    cv.repository = all_repos
    cv = cv.update(['repository'])
    # Publish, promote content view to lce
    cv.publish()
    cvv = cv.read().version[0]
    cvv.promote(data={'environment_ids': lc_env.id, 'force': True})
    cv = cv.read()
    # Create activation key
    ak = create_activation_key(target_sat, cv, lc_env, organization)

    # 3. Register Host
    register_host_with_satellite(target_sat, custom_host, organization, ak)

    # 4. Verify target rhel version repositories has enabled on Satellite Server
    verify_target_repo_on_satellite(target_sat, cv, organization, lc_env, target_rhel='rhel-9')

    # 5. Update all packages and install Leapp utility
    # Preupgrade conditions and check
    rhel_old_ver = custom_host.run('cat /etc/redhat-release')
    precondition_check_upgrade_and_install_leapp_tool(custom_host, custom_host.deploy_rhel_version)

    # Fixing inhibitors to avoid hard stop of Leapp tool execution
    fix_inhibitors(custom_host, custom_host.deploy_rhel_version)

    # 6. Run LEAPP-PREUPGRADE Job Template-
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Run preupgrade via Leapp"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'targeting_type': 'static_query',
            'search_query': f'name = {custom_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1800
    )
    result = target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1
    # Run LEAPP-UPGRADE Job Template-
    template_id = (
        target_sat.api.JobTemplate().search(query={'search': 'name="Run upgrade via Leapp"'})[0].id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'targeting_type': 'static_query',
            'search_query': f'name = {custom_host.hostname}',
            'inputs': {'Reboot': 'true'},
        },
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1800
    )
    result = target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1
    # Wait for the host to be rebooted and SSH daemon to be started.
    try:
        wait_for(
            custom_host.connect,
            fail_condition=lambda res: res is not None,
            handle_exception=True,
            raise_original=True,
            timeout=180,
            delay=1,
        )
    except ConnectionRefusedError:
        raise ConnectionRefusedError('Timed out waiting for SSH daemon to start on the host')
    rhel_new_ver = custom_host.run('cat /etc/redhat-release')
    assert rhel_old_ver != rhel_new_ver
    assert "9.2" in str(rhel_new_ver)
