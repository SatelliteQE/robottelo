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
from robottelo.constants import DEFAULT_ARCHITECTURE
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

@pytest.fixture(scope="module")
def module_cv(module_target_sat, module_sca_manifest_org):
    return module_target_sat.api.ContentView(organization=module_sca_manifest_org).create()


@pytest.fixture(scope="module")
def module_lce(module_target_sat, module_sca_manifest_org):
    return module_target_sat.api.LifecycleEnvironment(organization=module_sca_manifest_org).create()


@pytest.fixture(scope="module")
def module_ak(module_target_sat, module_cv, module_lce, module_sca_manifest_org):
    # module_cv.publish()
    # module_cvv = module_cv.read().version[0]
    # module_cvv.promote(data={'environment_ids': module_lce.id, 'force': True})

    return module_target_sat.api.ActivationKey(
        content_view=module_cv,
        environment=module_lce,
        organization=module_sca_manifest_org,
    ).create()

@pytest.fixture
def register_host_with_satellite(module_target_sat, custom_host, module_sca_manifest_org, module_ak):
    result = custom_host.register(module_sca_manifest_org, None, module_ak.name, module_target_sat)
    assert result.status == 0, f"Failed to register host: {result.stderr}"


@pytest.fixture
def target_rhel_minor_ver(custom_host):
    """Return the next major RHEL verision of custom_host to upgrade"""
    return str(int(custom_host.deploy_rhel_version.split('.')[0]) + 1)

@pytest.fixture
def verify_target_repo_on_satellite(
    module_target_sat, module_cv, module_sca_manifest_org, module_lce, target_rhel_minor_ver
):
    """Verify target rhel version repositories has enabled on Satellite Server"""
    cmd_out = Repository.list(
        {
            'search': f'content_label ~ rhel-{target_rhel_minor_ver}',
            'content-view-id': module_cv.id,
            'organization-id': module_sca_manifest_org.id,
            'lifecycle-environment-id': module_lce.id,
        }
    )
    repo_names = [out['name'] for out in cmd_out]
    if target_rhel_minor_ver == '9':
        assert RHEL_REPOS['rhel9_2_bos']['name'] in repo_names
        assert RHEL_REPOS['rhel9_2_aps']['name'] in repo_names
    else:
        # placeholder for target_rhel - rhel-8
        pass


@pytest.fixture
def precondition_check_upgrade_and_install_leapp_tool(custom_host):
    """Clean-up directory if in-place upgrade already performed,
    set rhel release version, update system and install leapp tool"""
    source_rhel = custom_host.deploy_rhel_version
    custom_host.run('rm -rf /root/tmp_leapp_py3')
    custom_host.run('dnf clean all')
    custom_host.run('dnf repolist')
    custom_host.run(f'subscription-manager release --set {source_rhel}')
    assert custom_host.run('dnf update -y').status == 0
    assert custom_host.run('dnf install leapp-upgrade -y').status == 0

@pytest.fixture
def fix_inhibitors(custom_host):
    """Fix inhibitors to avoid hard stop of Leapp tool execution"""
    source_rhel_minor_ver = custom_host.deploy_rhel_version.split('.')[0]
    if source_rhel_minor_ver == '8':
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
def leapp_sat_content(custom_host, target_rhel_version, module_target_sat, module_sca_manifest_org, module_cv, module_lce):
    """Enable rhel8/rhel9 bos, aps repository and add in content view"""
    source = custom_host.deploy_rhel_version
    target = target_rhel_version
    all_repos = []
    for rh_repo_key in RHEL_REPOS.keys():
        release_version = RHEL_REPOS[rh_repo_key]['releasever']
        if release_version == source or release_version == target:
            prod = rh_repo_key.split('_')[0]
            repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
                basearch=DEFAULT_ARCHITECTURE,
                org_id=module_sca_manifest_org.id,
                product=PRDS[prod],
                repo=RHEL_REPOS[rh_repo_key]['name'],
                reposet=RHEL_REPOS[rh_repo_key]['reposet'],
                releasever=release_version,
            )
            rh_repo = module_target_sat.api.Repository(id=repo_id).read()
            all_repos.append(rh_repo)
            # sync repo
            rh_repo.sync(timeout=1800)
        else:
            pass
    module_cv.repository = all_repos
    module_cv = module_cv.update(['repository'])
    # Publish, promote content view to lce
    module_cv.publish()
    cvv = module_cv.read().version[0]
    cvv.promote(data={'environment_ids': module_lce.id, 'force': True})
    module_cv = module_cv.read()


@pytest.mark.no_containers
@pytest.mark.parametrize(
    'custom_host',
    [
        {'deploy_rhel_version': '8.8'},
    ],
    ids=['RHEL8.8'],
    indirect=True,
)
@pytest.mark.parametrize('target_rhel_version', ['9.2'])
@pytest.mark.usefixtures(
    'leapp_sat_content',
    'register_host_with_satellite',
    'verify_target_repo_on_satellite',
    'precondition_check_upgrade_and_install_leapp_tool',
    'fix_inhibitors',
)
def test_upgrade_rhel8_to_rhel9(
    module_target_sat,
    custom_host,
    target_rhel_version,
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

    rhel_old_ver = custom_host.run('cat /etc/redhat-release')
    # 6. Run LEAPP-PREUPGRADE Job Template-
    template_id = (
        module_target_sat.api.JobTemplate()
        .search(query={'search': 'name="Run preupgrade via Leapp"'})[0]
        .id
    )
    job = module_target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'targeting_type': 'static_query',
            'search_query': f'name = {custom_host.hostname}',
        },
    )
    module_target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1800
    )
    result = module_target_sat.api.JobInvocation(id=job['id']).read()
    assert result.succeeded == 1
    # Run LEAPP-UPGRADE Job Template-
    template_id = (
        module_target_sat.api.JobTemplate().search(query={'search': 'name="Run upgrade via Leapp"'})[0].id
    )
    job = module_target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'targeting_type': 'static_query',
            'search_query': f'name = {custom_host.hostname}',
            'inputs': {'Reboot': 'true'},
        },
    )
    module_target_sat.wait_for_tasks(
        f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1800
    )
    result = module_target_sat.api.JobInvocation(id=job['id']).read()
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
