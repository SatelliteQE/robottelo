"""Test class for satellite-maintain advanced command functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ForemanMaintain

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
import yaml
from packaging.version import Version

from robottelo.config import robottelo_tmp_dir
from robottelo.config import settings
from robottelo.constants import MAINTAIN_HAMMER_YML

pytestmark = pytest.mark.destructive


def rhel7():
    return True if Version(str(settings.server.version.rhel_version)).major == 7 else False


# Common repositories for Satellite and Capsule
common_repos = (
    ['rhel-7-server-rpms', 'rhel-server-rhscl-7-rpms', 'rhel-7-server-ansible-2.9-rpms']
    if rhel7()
    else ['rhel-8-for-x86_64-baseos-rpms', 'rhel-8-for-x86_64-appstream-rpms']
)

# Satellite repositories
sat_68_repos = [
    'rhel-7-server-satellite-6.8-rpms',
    'rhel-7-server-satellite-maintenance-6-rpms',
] + common_repos

sat_69_repos = [
    'rhel-7-server-satellite-6.9-rpms',
    'rhel-7-server-satellite-maintenance-6-rpms',
] + common_repos

sat_610_repos = [
    'rhel-7-server-satellite-6.10-rpms',
    'rhel-7-server-satellite-maintenance-6-rpms',
] + common_repos

sat_611_repos = (
    ['rhel-7-server-satellite-6.11-rpms', 'rhel-7-server-satellite-maintenance-6.11-rpms']
    if rhel7()
    else [
        'satellite-6.11-for-rhel-8-x86_64-rpms',
        'satellite-maintenance-6.11-for-rhel-8-x86_64-rpms',
    ]
) + common_repos

# Capsule repositories
cap_68_repos = [
    'rhel-7-server-satellite-capsule-6.8-rpms',
    'rhel-7-server-satellite-maintenance-6-rpms',
] + common_repos

cap_69_repos = [
    'rhel-7-server-satellite-capsule-6.9-rpms',
    'rhel-7-server-satellite-maintenance-6-rpms',
] + common_repos

cap_610_repos = [
    'rhel-7-server-satellite-capsule-6.10-rpms',
    'rhel-7-server-satellite-maintenance-6-rpms',
] + common_repos

cap_611_repos = (
    [
        'rhel-7-server-satellite-capsule-6.11-rpms',
        'rhel-7-server-satellite-maintenance-6.11-rpms',
    ]
    if rhel7()
    else [
        'satellite-capsule-6.11-for-rhel-8-x86_64-rpms',
        'satellite-maintenance-6.11-for-rhel-8-x86_64-rpms',
    ]
) + common_repos

sat_repos = {
    '6.8': sat_68_repos,
    '6.9': sat_69_repos,
    '6.10': sat_610_repos,
    '6.11': sat_611_repos,
}
cap_repos = {
    '6.8': cap_68_repos,
    '6.9': cap_69_repos,
    '6.10': cap_610_repos,
    '6.11': cap_611_repos,
}


def test_positive_advanced_run_service_restart(sat_maintain):
    """Restart service using advanced procedure run

    :id: 64d3c78e-d602-43d6-bf77-f31135ed019e

    :steps:
        1. Run satellite-maintain advanced procedure run service-restart

    :expectedresults: Satellite service should restart.
    """
    result = sat_maintain.cli.Advanced.run_service_restart()
    assert result.status == 0
    assert 'FAIL' not in result.stdout


def test_positive_advanced_run_hammer_setup(request, sat_maintain):
    """Hammer setup using advanced procedure

    :id: 236171c0-5185-465e-9eec-e15dfefb41c3

    :steps:
        1. Change password for user to any string
        2. Run advanced procedure run hammer-setup with wrong_password.
        3. Verify wrong_password isn't updated in MAINTAIN_HAMMER_YML
        4. Run advanced procedure run hammer-setup with changed password.
        5. Verify changed password is updated in MAINTAIN_HAMMER_YML
        6. Update admin password back to default
        7. Verify default password is updated in MAINTAIN_HAMMER_YML

    :expectedresults:
        1. Run hammer setup with wrong password, it should fail and
           password shouldn't be updated in MAINTAIN_HAMMER_YML
        2. Run hammer setup with changed password, it should pass and
           password should be updated in MAINTAIN_HAMMER_YML

    :BZ: 1830355
    """
    default_admin_pass = settings.server.admin_password
    result = sat_maintain.execute(
        f'hammer -u admin -p {default_admin_pass} user update --login admin --password admin'
    )
    assert result.status == 0

    # try with incorrect password
    result = sat_maintain.cli.Advanced.run_hammer_setup(env_var='echo "wrong_password" | ')
    assert 'Incorrect credential for admin user' in result.stdout
    assert result.status == 1

    # Verify wrong_password isn't updated in MAINTAIN_HAMMER_YML
    result = sat_maintain.execute(f"grep -i ':password: wrong_password' {MAINTAIN_HAMMER_YML}")
    assert result.status != 0
    assert 'wrong_password' not in result.stdout

    # try with correct password
    result = sat_maintain.cli.Advanced.run_hammer_setup(env_var='echo "admin" | ')
    assert result.status == 0

    # Verify new password updated in MAINTAIN_HAMMER_YML
    result = sat_maintain.execute(f"grep -i ':password: admin' {MAINTAIN_HAMMER_YML}")
    assert result.status == 0
    assert 'admin' in result.stdout

    @request.addfinalizer
    def _finalize():
        result = sat_maintain.execute(
            f'hammer -u admin -p admin user update --login admin --password {default_admin_pass}'
        )
        assert result.status == 0
        # Make default admin creds available in MAINTAIN_HAMMER_YML
        assert sat_maintain.cli.Advanced.run_hammer_setup().status == 0
        # Make sure default password available in MAINTAIN_HAMMER_YML
        result = sat_maintain.execute(
            f"grep -i ':password: {default_admin_pass}' {MAINTAIN_HAMMER_YML}"
        )
        assert result.status == 0
        assert default_admin_pass in result.stdout


def test_positive_advanced_run_packages(request, sat_maintain):
    """Packages install/downgrade/check-update/update using advanced procedure run

    :id: d56523d7-7042-40e1-a96e-db8f33b960e5

    :steps:
        1. Run satellite-maintain advanced procedure run packages-install
        2. Run dnf -y --disableplugin=foreman-protector downgrade
        3. Run satellite-maintain advanced procedure run packages-check-update
        4. Run satellite-maintain advanced procedure run packages-update

    :expectedresults: packages should install/downgrade/check-update/update.
    """
    # Setup custom_repo and install walrus package
    sat_maintain.create_custom_repos(custom_repo=settings.repos.yum_0.url)
    result = sat_maintain.cli.Advanced.run_packages_install(
        options={'packages': 'walrus', 'assumeyes': True}
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    assert 'Nothing to do' not in result.stdout

    # Downgrade walrus package and prepare an package update
    disableplugin = '--disableplugin=foreman-protector'
    assert sat_maintain.execute(f'dnf -y {disableplugin} downgrade walrus-0.71-1').status == 0

    # Run satellite-maintain packages check update and verify walrus package is available for update
    result = sat_maintain.cli.Advanced.run_packages_check_update()
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    assert 'walrus' in result.stdout
    # Run satellite-maintain packages update
    result = sat_maintain.cli.Advanced.run_packages_update(
        options={'packages': 'walrus', 'assumeyes': True}
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    # Verify walrus package is updated.
    result = sat_maintain.execute('rpm -qa walrus')
    assert result.status == 0
    assert 'walrus-5.21-1' in result.stdout

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.execute('dnf remove -y walrus').status == 0
        sat_maintain.execute('rm -rf /etc/yum.repos.d/custom_repo.repo')


@pytest.mark.parametrize(
    'tasks_state',
    ['old', 'planning', 'pending'],
    ids=['old_tasks', 'planning_tasks', 'pending_tasks'],
)
def test_positive_advanced_run_foreman_tasks_delete(sat_maintain, tasks_state):
    """Delete old/planning/pending foreman-tasks using advanced procedure run

    :id: 6bd3af66-9910-48c4-8cbb-69c3ddd18d6c

    :steps:
        1. Run satellite-maintain advanced procedure run foreman-tasks-delete --state tasks_state

    :expectedresults: foreman tasks in old/planning/pending state should delete.
    """
    result = sat_maintain.cli.Advanced.run_foreman_tasks_delete(options={'state': tasks_state})
    assert result.status == 0
    assert 'FAIL' not in result.stdout


def test_positive_advanced_run_foreman_task_resume(sat_maintain):
    """Resume paused foreman-tasks using advanced procedure run

    :id: e9afe55b-e3a4-425a-8bfd-a8df6674e516

    :steps:
        1. Run satellite-maintain advanced procedure run foreman-tasks-resume

    :expectedresults: foreman tasks in paused state should resume.
    """
    result = sat_maintain.cli.Advanced.run_foreman_tasks_resume()
    assert result.status == 0
    assert 'FAIL' not in result.stdout


def test_positive_advanced_run_foreman_tasks_ui_investigate(sat_maintain):
    """Run foreman-tasks-ui-investigate using advanced procedure run

    :id: 3b4f69c6-c0a1-42e3-a099-8a6e26280d17

    :steps:
        1. Run satellite-maintain advanced procedure run foreman-tasks-ui-investigate

    :expectedresults: procedure foreman-tasks-ui-investigate should work.
    """
    result = sat_maintain.cli.Advanced.run_foreman_tasks_ui_investigate(env_var='echo " " | ')
    assert result.status == 0


def test_positive_advanced_run_sync_plan(setup_sync_plan, sat_maintain):
    """Run sync-plans-enable and sync-plans-disable using advanced procedure run

    :id: 865df1e1-1189-437c-8451-22d772ff97d4

    :steps:
        1. Run satellite-maintain advanced procedure run sync-plans-disable
        2. Run satellite-maintain advanced procedure run sync-plans-enable

    :expectedresults: procedure sync-plans-enable should work.
    """
    enable_sync_ids = setup_sync_plan
    data_yml_path = '/var/lib/foreman-maintain/data.yml'
    local_data_yml_path = f'{robottelo_tmp_dir}/data.yml'

    result = sat_maintain.cli.Advanced.run_sync_plans_disable()
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    sat_maintain.get(remote_path=data_yml_path, local_path=local_data_yml_path)
    with open(local_data_yml_path) as f:
        data_yml = yaml.safe_load(f)
    assert len(enable_sync_ids) == len(data_yml[':default'][':sync_plans'][':disabled'])

    result = sat_maintain.cli.Advanced.run_sync_plans_enable()
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    sat_maintain.get(remote_path=data_yml_path, local_path=local_data_yml_path)
    with open(local_data_yml_path) as f:
        data_yml = yaml.safe_load(f)
    assert len(enable_sync_ids) == len(data_yml[':default'][':sync_plans'][':enabled'])


@pytest.mark.include_capsule
def test_positive_advanced_by_tag_check_migrations(sat_maintain):
    """Run pre-migrations and post-migrations using advanced procedure by-tag

    :id: 65cacca0-f142-4a63-a644-01f76120f16c

    :parametrized: yes

    :steps:
        1. Run satellite-maintain advanced procedure by-tag pre-migrations
        2. Run satellite-maintain advanced procedure by-tag post-migrations

    :expectedresults: procedures of pre-migrations tag and post-migrations tag should work.
    """
    iptables_nftables = 'iptables -L' if rhel7() else 'nft list tables'
    result = sat_maintain.cli.AdvancedByTag.pre_migrations()
    assert 'FAIL' not in result.stdout
    rules = sat_maintain.execute(iptables_nftables)
    assert 'FOREMAN_MAINTAIN_TABLE' in rules.stdout

    result = sat_maintain.cli.AdvancedByTag.post_migrations()
    assert 'FAIL' not in result.stdout
    rules = sat_maintain.execute(iptables_nftables)
    assert 'FOREMAN_MAINTAIN_TABLE' not in rules.stdout


@pytest.mark.include_capsule
def test_positive_advanced_by_tag_restore_confirmation(sat_maintain):
    """Run restore_confirmation using advanced procedure by-tag

    :id: f9e10352-04fb-49ba-8346-5b02e64fd028

    :parametrized: yes

    :steps:
        1. Run satellite-maintain advanced procedure by-tag restore

    :expectedresults: procedure restore_confirmation should work.
    """
    result = sat_maintain.cli.AdvancedByTag.restore(options={'assumeyes': True})
    assert 'FAIL' not in result.stdout
    assert result.status == 0


def test_positive_sync_plan_with_hammer_defaults(request, sat_maintain):
    """Verify that sync plan is disabled and enabled with hammer defaults set.

    :id: b25734c8-470f-4cad-bc56-5c0f75aa7499

    :steps:
        1. Setup hammer on system with defaults set
        2. Run satellite-maintain advanced procedure run sync-plans-disable
        3. Run satellite-maintain advanced procedure run sync-plans-enable

    :expectedresults: sync plans should get disabled and enabled.
    """
    sat_maintain.cli.Defaults.add({'param-name': 'organization_id', 'param-value': 1})

    result = sat_maintain.cli.Advanced.run_sync_plans_disable()
    assert 'FAIL' not in result.stdout
    assert result.status == 0

    result = sat_maintain.cli.Advanced.run_sync_plans_enable()
    assert 'FAIL' not in result.stdout
    assert result.status == 0

    @request.addfinalizer
    def _finalize():
        sat_maintain.cli.Defaults.delete({'param-name': 'organization_id'})


def test_positive_satellite_repositories_setup(sat_maintain):
    """Verify that all required repositories gets enabled.

    :id: e32fee2d-2a1f-40ed-9f94-515f75511c5a

    :steps:
        1. Run satellite-maintain advanced procedure run repositories-setup --version 6.y

    :BZ: 1684730, 1869731

    :expectedresults: Required Satellite repositories for install/upgrade should get enabled
    """
    supported_versions = ['6.8', '6.9', '6.10', '6.11'] if rhel7() else ['6.11']
    for ver in supported_versions:
        result = sat_maintain.cli.Advanced.run_repositories_setup(options={'version': ver})
        assert result.status == 0
        assert 'FAIL' not in result.stdout
        result = sat_maintain.execute('yum repolist')
        for repo in sat_repos[ver]:
            assert repo in result.stdout

    # Verify that all required beta repositories gets enabled
    # maintain beta repo is unavailable for EL8 https://bugzilla.redhat.com/show_bug.cgi?id=2106750
    sat_beta_repo = (
        ['rhel-server-7-satellite-6-beta-rpms', 'rhel-7-server-satellite-maintenance-6-beta-rpms']
        if rhel7()
        else [
            'satellite-6-beta-for-rhel-8-x86_64-rpms',
        ]
    ) + common_repos
    missing_beta_el8_repos = ['satellite-maintenance-6-beta-for-rhel-8-x86_64-rpms']
    result = sat_maintain.cli.Advanced.run_repositories_setup(
        options={'version': '6.11'}, env_var='FOREMAN_MAINTAIN_USE_BETA=1'
    )
    if rhel7():
        assert result.status == 0
        assert 'FAIL' not in result.stdout
    else:
        assert result.status != 0
        assert 'FAIL' in result.stdout
        for repo in missing_beta_el8_repos:
            assert f"Error: '{repo}' does not match a valid repository ID" in result.stdout
    result = sat_maintain.execute('yum repolist')
    for repo in sat_beta_repo:
        assert repo in result.stdout


@pytest.mark.capsule_only
def test_positive_capsule_repositories_setup(sat_maintain):
    """Verify that all required capsule repositories gets enabled.

    :id: 88558fb0-2268-469f-86ae-c4d18ccef782

    :parametrized: yes

    :steps:
        1. Run satellite-maintain advanced procedure run repositories-setup --version 6.y

    :BZ: 1684730, 1869731

    :expectedresults: Required Capsule repositories should get enabled
    """
    supported_versions = ['6.8', '6.9', '6.10', '6.11'] if rhel7() else ['6.11']
    for ver in supported_versions:
        result = sat_maintain.cli.Advanced.run_repositories_setup(options={'version': ver})
        assert result.status == 0
        assert 'FAIL' not in result.stdout
        result = sat_maintain.execute('yum repolist')
        for repo in cap_repos[ver]:
            assert repo in result.stdout

    # Verify that all required beta repositories gets enabled
    # maintain beta repo is unavailable for EL8 https://bugzilla.redhat.com/show_bug.cgi?id=2106750
    cap_beta_repo = (
        [
            'rhel-server-7-satellite-capsule-6-beta-rpms',
            'rhel-7-server-satellite-maintenance-6-beta-rpms',
        ]
        if rhel7()
        else []
    ) + common_repos
    missing_beta_el8_repos = [
        'satellite-capsule-6-beta-for-rhel-8-x86_64-rpms',
        'satellite-maintenance-6-beta-for-rhel-8-x86_64-rpms',
    ]
    result = sat_maintain.cli.Advanced.run_repositories_setup(
        options={'version': '6.11'}, env_var='FOREMAN_MAINTAIN_USE_BETA=1'
    )
    if rhel7():
        assert result.status == 0
        assert 'FAIL' not in result.stdout
    else:
        assert result.status != 0
        assert 'FAIL' in result.stdout
        for repo in missing_beta_el8_repos:
            assert f"Error: '{repo}' does not match a valid repository ID" in result.stdout
    result = sat_maintain.execute('yum repolist')
    for repo in cap_beta_repo:
        assert repo in result.stdout
