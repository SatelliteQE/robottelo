"""Test for LEAPP cli

:Requirement: leapp

:CaseLevel: Acceptance

:CaseComponent: Leappintegration

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
import pytest
from wait_for import wait_for

from robottelo.constants import PRDS

CUSTOM_REPOSET = {
    'rhel8_8_bos': 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS (RPMs)',
    'rhel8_8_aps': 'Red Hat Enterprise Linux 8 for x86_64 - AppStream (RPMs)',
    'rhel9_2_bos': 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS (RPMs)',
    'rhel9_2_aps': 'Red Hat Enterprise Linux 9 for x86_64 - AppStream (RPMs)',
}
CUSTOM_REPOS = {
    'rhel8_8_bos': {
        'id': 'rhel-8-for-x86_64-baseos-rpms',
        'name': 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs 8.8',
        'releasever': '8.8',
    },
    'rhel8_8_aps': {
        'id': 'rhel-8-for-x86_64-appstream-rpms',
        'name': 'Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8.8',
        'releasever': '8.8',
    },
    'rhel9_2_bos': {
        'id': 'rhel-9-for-x86_64-baseos-rpms',
        'name': 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS RPMs 9.2',
        'releasever': '9.2',
    },
    'rhel9_2_aps': {
        'id': 'rhel-9-for-x86_64-appstream-rpms',
        'name': 'Red Hat Enterprise Linux 9 for x86_64 - AppStream RPMs 9.2',
        'releasever': '9.2',
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
    custom_host.install_katello_ca(satellite)
    custom_host.register_contenthost(org=organization.label, activation_key=activation_key.name)
    custom_host.add_rex_key(satellite=satellite)
    assert custom_host.subscribed


def verify_target_repo_on_satellite(
    satellite, content_view, organization, lifecycle_env, target_rhel
):
    """Verify target rhel version repositories has enabled on Satellite Server"""
    cmd_out = satellite.execute(
        f"hammer repository list --search 'content_label ~ {target_rhel}' "
        f"--content-view {content_view.name} --organization '{organization.name}' "
        f"--lifecycle-environment '{lifecycle_env.name}'"
    )
    assert cmd_out.status == 0
    if 'rhel-9' in target_rhel:
        assert ("AppStream RPMs 9" in cmd_out.stdout) and ("BaseOS RPMs 9" in cmd_out.stdout)
    else:
        # placeholder for target_rhel - rhel-8
        pass


def precondition_check_upgrade_and_install_leapp_tool(custom_host, source_rhel):
    """Clean-up directory, set rhel release version, update system and install leapp tool"""
    # Remove directory if in-place upgrade already performed from RHEL7 to RHEL8
    custom_host.run("rm -rf /root/tmp_leapp_py3")
    custom_host.run("dnf clean all")
    custom_host.run("dnf repolist")
    custom_host.run(f"subscription-manager release --set {source_rhel}")
    assert custom_host.run("dnf update -y").status == 0
    assert custom_host.run("dnf install leapp-upgrade -y").status == 0


def fix_inhibitors(custom_host, source_rhel):
    """Fixing inhibitors to avoid hard stop of Leapp tool execution"""
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
    """Creating essential things and returning in form of dictiory for use"""
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
@pytest.mark.parametrize('target_rhel', ['rhel-9'])
def test_upgrade_rhel8_to_rhel9(
    setup_env,
    custom_host,
    target_rhel,
):
    """Test to upgrade RHEL host to next major RHEL Realse with Leapp Preupgrade and Leapp Upgrade
    Job templates

    :id: 7add9b32-a13a-4e65-973c-cd64326b332a

    :Steps:
        1. Import a subscription manifest and enable, sync source & target repositories
        2. Create CV, add repositories, create lce, ak, etc.
        3. Register contenthost using ak
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
    c_view = setup_env['contentview']

    # Enable rhel8/rhel9 bos, aps repository and add in content view
    all_repos = []
    for rh_repo_key in CUSTOM_REPOS.keys():
        prod = rh_repo_key.split('_')[0]
        repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch=custom_host.arch,
            org_id=organization.id,
            product=PRDS[prod],
            repo=CUSTOM_REPOS[rh_repo_key]['name'],
            reposet=CUSTOM_REPOSET[rh_repo_key],
            releasever=CUSTOM_REPOS[rh_repo_key]['releasever'],
        )
        rh_repo = target_sat.api.Repository(id=repo_id).read()
        all_repos.append(rh_repo)
        # sync repo
        rh_repo.sync(timeout=1800)
    c_view.repository = all_repos
    c_view = c_view.update(['repository'])
    # Publish, promote content view to lce
    c_view.publish()
    cv_version = c_view.read().version[0]
    cv_version.promote(data={'environment_ids': lc_env.id, 'force': True})
    c_view = c_view.read()
    # Create activation key
    ak = create_activation_key(target_sat, c_view, lc_env, organization)

    # 3. Register Host
    register_host_with_satellite(target_sat, custom_host, organization, ak)

    # 4. Verify target rhel version repositories has enabled on Satellite Server
    verify_target_repo_on_satellite(target_sat, c_view, organization, lc_env, target_rhel)

    # 5. Update all packages and install Leapp utility
    # Preupgrade conditions and check
    # rhel_old_ver = custom_host.run('cat /etc/redhat-release')
    rhel_old_ver = custom_host.os_version
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
    # rhel_new_ver = custom_host.run('cat /etc/redhat-release')
    custom_host.list_and_clean_cached()
    rhel_new_ver = custom_host.os_version
    assert rhel_old_ver != rhel_new_ver
    assert "9.2" in str(rhel_new_ver)
