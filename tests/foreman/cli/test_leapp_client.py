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
from wrapanapi.entities.vm import VmState

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
def test_upgrade_rhel8_to_rhel9(
    setup_env,
    custom_host,
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
    ak = target_sat.api.ActivationKey(
        content_view=c_view,
        environment=lc_env,
        organization=organization,
    ).create()
    # 3. Register Host
    custom_host.install_katello_ca(target_sat)
    custom_host.register_contenthost(org=organization.label, activation_key=ak.name)
    custom_host.add_rex_key(satellite=target_sat)
    assert custom_host.subscribed
    # 4. Verify target rhel version repositories has enabled on Satellite Server
    cmd_out = target_sat.execute(
        f"hammer repository list --search 'content_label ~ rhel-9' --content-view {c_view.name} "
        f"--organization '{organization.name}' --lifecycle-environment '{lc_env.name}'"
    )
    assert cmd_out.status == 0
    assert ("AppStream RPMs 9" in cmd_out.stdout) and ("BaseOS RPMs 9" in cmd_out.stdout)

    # Preupgrade conditions and check
    custom_host.run("rm -rf /root/tmp_leapp_py3")
    # Remove directory if in-place upgrade already performed from RHEL7 to RHEL8
    rhel_old_ver = custom_host.run('cat /etc/redhat-release')
    # 5. Update all packages and install Leapp utility
    custom_host.run("dnf clean all")
    custom_host.run("dnf repolist")

    custom_host.run("subscription-manager release --set 8.8")
    result = custom_host.run("dnf update -y")
    assert result.status == 0
    custom_host.run("dnf install leapp-upgrade -y")

    # Fixing inhibitors - download data files to avoid inhibitors
    custom_host.run(
        'sed -i "s/^AllowZoneDrifting=.*/AllowZoneDrifting=no/" /etc/firewalld/firewalld.conf'
    )
    if custom_host.run('needs-restarting -r').status == 1:
        custom_host.power_control(state='reboot', ensure=True)
        custom_host.power_control(state=VmState.RUNNING, ensure=True)
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
