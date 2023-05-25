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
        'version': '8',
        'reposet': CUSTOM_REPOSET['rhel8_8_bos'],
        'product': PRDS['rhel8'],
        'distro': 'rhel8',
        'key': 'rhel8_bos',
        'basearch': 'x86_64',
    },
    'rhel8_8_aps': {
        'id': 'rhel-8-for-x86_64-appstream-rpms',
        'name': 'Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8.8',
        'releasever': '8.8',
        'basearch': 'x86_64',
        'version': '8',
        'reposet': CUSTOM_REPOSET['rhel8_8_aps'],
        'product': PRDS['rhel8'],
        'distro': 'rhel8',
        'key': 'rhel8_aps',
    },
    'rhel9_2_bos': {
        'id': 'rhel-9-for-x86_64-baseos-rpms',
        'name': 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS RPMs 9.2',
        'releasever': '9.2',
        'version': '9',
        'reposet': CUSTOM_REPOSET['rhel9_2_bos'],
        'product': PRDS['rhel9'],
        'distro': 'rhel9',
        'key': 'rhel9_bos',
        'basearch': 'x86_64',
    },
    'rhel9_2_aps': {
        'id': 'rhel-9-for-x86_64-appstream-rpms',
        'name': 'Red Hat Enterprise Linux 9 for x86_64 - AppStream RPMs 9.2',
        'releasever': '9.2',
        'basearch': 'x86_64',
        'version': '9',
        'reposet': CUSTOM_REPOSET['rhel9_2_aps'],
        'product': PRDS['rhel9'],
        'distro': 'rhel9',
        'key': 'rhel9_aps',
    },
}


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('8')
def test_upgrade_rhel8_to_rehl9(
    target_sat,
    default_org,
    rhel_contenthost,
):
    """Test to upgrade RHEL host to next major RHEL Realse with Leapp Preupgrade and Leapp Upgrade
    Job templates

    :Steps:

        1. Import a subscription manifest and enable, sync source & target repositories
        2. Create CV, add repositories, create lce, ak, etc.
        3. Register contenthost using ak
        4. Varify target rhel repositories are enable on Satellite
        5. Update all packages, install leapp tool and fix inhibitors
        6. Run Leapp Preupgrade and Leapp Upgrade job template

    :Expectedresult: 1. Update RHEL OS major version to another major version
    """
    # 1. Import a subscription manifest
    target_sat.upload_manifest(default_org)
    # Enable rhel8/rhel9 bos, aps repository and add in content view
    lc_env = target_sat.api.LifecycleEnvironment(organization=default_org).create()
    c_view = target_sat.api.ContentView(organization=default_org).create()
    all_repos = []
    for rh_repo_key in ['rhel8_8_bos', 'rhel8_8_aps', 'rhel9_2_bos', 'rhel9_2_aps']:
        if 'rhel8' in rh_repo_key:
            prod = PRDS['rhel8']
        else:
            prod = PRDS['rhel9']
        repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=default_org.id,
            product=prod,
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
        organization=default_org,
    ).create()
    # 3. Register Host
    rhel_contenthost.install_katello_ca(target_sat)
    rhel_contenthost.register_contenthost(org=default_org.label, activation_key=ak.name)
    rhel_contenthost.add_rex_key(satellite=target_sat)
    assert rhel_contenthost.subscribed
    # Verify target rhel version repositories has enabled on Satellite Server
    cmd_out = target_sat.execute(
        f"hammer repository list --search 'content_label ~ rhel-9' --content-view {c_view.name} "
        f"--organization '{default_org.name}' --lifecycle-environment '{lc_env.name}'"
    )
    assert cmd_out.status == 0
    assert ("AppStream RPMs 9" in cmd_out.stdout) and ("BaseOS RPMs 9" in cmd_out.stdout)

    # Preupgrade conditions and check
    rhel_contenthost.run("rm -rf /root/tmp_leapp_py3")
    # Remove directory if in-place upgrade already performed from RHEL7 to RHEL8
    rhel_old_ver = rhel_contenthost.run("cat /etc/redhat-release")
    # 5. Update all packages and install Leapp utility
    rhel_contenthost.run("yum clean all")
    rhel_contenthost.run("yum repolist")

    rhel_contenthost.run("subscription-manager release --set 8.8")
    result = rhel_contenthost.run("dnf update -y")
    assert result.status == 0
    rhel_contenthost.run("yum install leapp-upgrade -y")

    # Fixing inhibitors - download data files to avoid inhibitors
    rhel_contenthost.run(
        'curl -k "https://gitlab.cee.redhat.com/oamg/leapp-data/-/raw/stage/data/'
        '{repomap.json,pes-events.json,device_driver_deprecation_data.json}"'
        ' -o "/etc/leapp/files/#1"'
    )
    rhel_contenthost.run(
        'sed -i "s/^AllowZoneDrifting=.*/AllowZoneDrifting=no/" /etc/firewalld/firewalld.conf'
    )
    # 6.1 Run LEAPP-PREUPGRADE Job Template-
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
            'search_query': f'name = {rhel_contenthost.hostname}',
        },
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1800
    )
    result = target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1

    # 6.2 Run LEAPP-UPGRADE Job Template-
    template_id = (
        target_sat.api.JobTemplate().search(query={'search': 'name="Run upgrade via Leapp"'})[0].id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'targeting_type': 'static_query',
            'search_query': f'name = {rhel_contenthost.hostname}',
            'inputs': {'Reboot': 'true'},
        },
    )
    target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1800
    )
    result = target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1
    # Resume the rhel_contenthsot with ensure True to ping the virtual machine
    rhel_contenthost.power_control(state=VmState.RUNNING, ensure=True)
    rhel_new_ver = rhel_contenthost.run("cat /etc/redhat-release")
    assert rhel_old_ver != rhel_new_ver
