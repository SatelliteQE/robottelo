"""Test class for satellite-maintain advanced command functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Platform

:CaseImportance: Critical

"""

import pytest
import yaml

from robottelo.config import robottelo_tmp_dir, settings
from robottelo.constants import MAINTAIN_HAMMER_YML, SAT_NON_GA_VERSIONS
from robottelo.hosts import get_sat_rhel_version, get_sat_version

sat_x_y_release = f'{get_sat_version().major}.{get_sat_version().minor}'


def get_satellite_capsule_repos(
    x_y_release=sat_x_y_release, product='satellite', os_major_ver=None
):
    if os_major_ver is None:
        os_major_ver = get_sat_rhel_version().major
    if product == 'capsule':
        product = 'satellite-capsule'
    return [
        f'{product}-{x_y_release}-for-rhel-{os_major_ver}-x86_64-rpms',
        f'satellite-maintenance-{x_y_release}-for-rhel-{os_major_ver}-x86_64-rpms',
        f'rhel-{os_major_ver}-for-x86_64-baseos-rpms',
        f'rhel-{os_major_ver}-for-x86_64-appstream-rpms',
    ]


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

    :customerscenario: true

    :BZ: 1830355
    """

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


@pytest.mark.e2e
@pytest.mark.upgrade
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

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.execute('dnf remove -y walrus').status == 0
        sat_maintain.execute('rm -rf /etc/yum.repos.d/custom_repo.repo')

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


@pytest.mark.e2e
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


def test_positive_sync_plan_with_hammer_defaults(request, sat_maintain, module_org):
    """Verify that sync plan is disabled and enabled with hammer defaults set.

    :id: b25734c8-470f-4cad-bc56-5c0f75aa7499

    :steps:
        1. Setup hammer on system with defaults set
        2. Run satellite-maintain advanced procedure run sync-plans-disable
        3. Run satellite-maintain advanced procedure run sync-plans-enable

    :expectedresults: sync plans should get disabled and enabled.

    :BZ: 2175007, 1997186

    :customerscenario: true
    """

    sat_maintain.cli.Defaults.add({'param-name': 'organization_id', 'param-value': module_org.id})

    sync_plans = []
    for name in ['plan1', 'plan2']:
        sync_plans.append(
            sat_maintain.api.SyncPlan(enabled=True, name=name, organization=module_org).create()
        )

    @request.addfinalizer
    def _finalize():
        sat_maintain.cli.Defaults.delete({'param-name': 'organization_id'})
        sync_plans[1].delete()
        sync_plan = sat_maintain.api.SyncPlan(organization=module_org.id).search(
            query={'search': f'name="{sync_plans[0]}"'}
        )
        if sync_plan:
            sync_plans[0].delete()

    result = sat_maintain.cli.Advanced.run_sync_plans_disable()
    assert 'FAIL' not in result.stdout
    assert result.status == 0

    sync_plans[0].delete()

    result = sat_maintain.cli.Advanced.run_sync_plans_enable()
    assert 'FAIL' not in result.stdout
    assert result.status == 0


@pytest.mark.e2e
def test_positive_satellite_repositories_setup(sat_maintain):
    """Verify that all required repositories gets enabled.

    :id: e32fee2d-2a1f-40ed-9f94-515f75511c5a

    :steps:
        1. Run satellite-maintain advanced procedure run repositories-setup --version 6.y

    :BZ: 1684730, 1869731

    :expectedresults: Required Satellite repositories for install/upgrade should get enabled
    """
    sat_version = ".".join(sat_maintain.version.split('.')[0:2])
    result = sat_maintain.cli.Advanced.run_repositories_setup(options={'version': sat_version})
    if sat_version not in SAT_NON_GA_VERSIONS:
        assert result.status == 0
        assert 'FAIL' not in result.stdout
        result = sat_maintain.execute('yum repolist')
        for repo in get_satellite_capsule_repos(sat_version):
            assert repo in result.stdout

    # for non-ga versions
    else:
        assert result.status == 1
        assert 'FAIL' in result.stdout
        for repo in get_satellite_capsule_repos(sat_version):
            assert repo in result.stdout


@pytest.mark.e2e
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
    sat_version = ".".join(sat_maintain.version.split('.')[0:2])
    result = sat_maintain.cli.Advanced.run_repositories_setup(options={'version': sat_version})
    if sat_version not in SAT_NON_GA_VERSIONS:
        assert result.status == 0
        assert 'FAIL' not in result.stdout
        result = sat_maintain.execute('yum repolist')
        for repo in get_satellite_capsule_repos(sat_version, 'capsule'):
            assert repo in result.stdout
    # for non-ga versions
    else:
        assert result.status == 1
        assert 'FAIL' in result.stdout
        for repo in get_satellite_capsule_repos(sat_version, 'capsule'):
            assert repo in result.stdout
