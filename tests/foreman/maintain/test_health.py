"""Test module for satellite-maintain health functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ForemanMaintain

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import time

import pytest
from fauxfactory import gen_string

from robottelo.config import settings


upstream_url = {
    'foreman_repo': 'https://yum.theforeman.org/releases/nightly/el8/x86_64/',
    'puppet_repo': 'https://yum.puppetlabs.com/puppet/el/8/x86_64/',
    'fedorapeople_repo': (
        'https://fedorapeople.org/groups/katello/releases/yum/latest/candlepin/el7/x86_64/'
    ),
}


@pytest.mark.include_capsule
def test_positive_health_list(sat_maintain):
    """List health check in satellite-maintain

    :id: 976ef4cd-e028-4545-91bb-72433d40d7ee

    :parametrized: yes

    :steps:
        1. Run satellite-maintain health list

    :expectedresults: Health check list should work.
    """
    assert sat_maintain.cli.Health.list().status == 0


@pytest.mark.include_capsule
def test_positive_health_list_tags(sat_maintain):
    """List tags for health check in satellite-maintain

    :id: d0a6c8c1-8266-464a-bfdf-01d405dd9bd2

    :parametrized: yes

    :steps:
        1. Run satellite-maintain health list-tags

    :expectedresults: Tags for health checks should list.
    """
    assert sat_maintain.cli.Health.list_tags().status == 0


@pytest.mark.include_capsule
def test_positive_list_health_check_by_tags(sat_maintain):
    """List health check in satellite-maintain by tags

    :id: 420d8e62-84d8-4496-8c24-037bd23febe9

    :steps:
        1. Run satellite-maintain health list --tags default

    :expectedresults: health checks according to tag should list.
    """
    result = sat_maintain.cli.Health.list_tags().stdout
    output = [i.split("]\x1b[0m")[0] for i in result.split("\x1b[36m[") if i]
    for tag in output:
        assert sat_maintain.cli.Health.list({"tags": tag}).status == 0


@pytest.mark.include_capsule
def test_positive_health_check(sat_maintain):
    """Verify satellite-maintain health check

    :id: bfff93dd-adde-4630-8411-1bb6b74daddd

    :parametrized: yes

    :steps:
        1. Run satellite-maintain health check

    :expectedresults: Health check should pass.
    """
    result = sat_maintain.cli.Health.check(options={'assumeyes': True})
    assert result.status == 0
    if 'paused tasks in the system' not in result.stdout:
        assert 'FAIL' not in result.stdout


@pytest.mark.include_capsule
def test_positive_health_check_by_tags(sat_maintain):
    """Verify satellite-maintain health check by tags

    :id: 518e19af-2dd4-4fb0-8c90-208cbd354107

    :parametrized: yes

    :steps:
        1. Run satellite-maintain health check --tags tag_name

    :expectedresults: Health check should pass for listed tags.
    """
    result = sat_maintain.cli.Health.list_tags().stdout
    output = [i.split("]\x1b[0m")[0] for i in result.split("\x1b[36m[") if i]
    for tag in output:
        assert sat_maintain.cli.Health.check(options={'tags': tag, 'assumeyes': True}).status == 0


@pytest.mark.include_capsule
def test_positive_health_check_pre_upgrade(sat_maintain):
    """Verify pre-upgrade health checks

    :id: f52bd43e-79cd-488b-adbb-3c9e5bac32cc

    :parametrized: yes

    :steps:
        1. Run satellite-maintain health check --tags pre-upgrade

    :expectedresults: Pre-upgrade health checks should pass.
    """
    result = sat_maintain.cli.Health.check(options={'tags': 'pre-upgrade'})
    assert result.status == 0
    assert 'FAIL' not in result.stdout


@pytest.mark.include_capsule
def test_positive_health_check_server_ping(sat_maintain):
    """Verify server ping check

    :id: b1eec8cb-9f94-439a-b5e7-8621cb35501f

    :parametrized: yes

    :steps:
        1. Run satellite-maintain health check --label server-ping

    :expectedresults: server-ping health check should pass.
    """
    result = sat_maintain.cli.Health.check(options={'label': 'server-ping'})
    assert result.status == 0
    assert 'FAIL' not in result.stdout


def test_negative_health_check_server_ping(sat_maintain, request):
    """Verify hammer ping check

    :id: ecdc5bfb-2adf-49f6-948d-995dae34bcd3

    :steps:
        1. Run satellite maintain service stop
        2. Run satellite-maintain health check --label server-ping
        3. Run satellite maintain service start

    :expectedresults: server-ping health check should pass
    """
    assert sat_maintain.cli.Service.stop().status == 0
    result = sat_maintain.cli.Health.check(options={'label': 'server-ping', 'assumeyes': True})
    assert result.status == 0
    assert 'FAIL' in result.stdout

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.cli.Service.start().status == 0


@pytest.mark.include_capsule
def test_positive_health_check_upstream_repository(sat_maintain, request):
    """Verify upstream repository check

    :id: 349fcf33-2d25-4628-a6af-cff53e624b25

    :parametrized: yes

    :steps:
        1. Run satellite-maintain health check --label check-upstream-repository

    :expectedresults: check-upstream-repository health check should pass.
    """
    for name, url in upstream_url.items():
        sat_maintain.create_custom_repos(**{name: url})
    result = sat_maintain.cli.Health.check(
        options={'label': 'check-upstream-repository', 'assumeyes': True}
    )
    assert result.status == 0
    assert 'System has upstream foreman_repo,puppet_repo repositories enabled' in result.stdout
    assert 'FAIL' in result.stdout
    for name in upstream_url.keys():
        result = sat_maintain.execute(f'cat /etc/yum.repos.d/{name}.repo')
        if name == 'fedorapeople_repo':
            assert 'enabled=1' in result.stdout
        elif name in ['foreman_repo', 'puppet_repo']:
            assert 'enabled=0' in result.stdout

    @request.addfinalizer
    def _finalize():
        for name, url in upstream_url.items():
            sat_maintain.execute(f'rm -fr /etc/yum.repos.d/{name}.repo')
        sat_maintain.execute('dnf clean all')


@pytest.mark.include_capsule
def test_positive_health_check_available_space(sat_maintain):
    """Verify available-space check

    :id: 7d8798ca-3334-4dda-a9b0-dc3d7c0903e9

    :parametrized: yes

    :steps:
        1. Run satellite-maintain health check --label available-space

    :expectedresults: available-space health check should pass.
    """
    result = sat_maintain.cli.Health.check(options={'label': 'available-space'})
    assert 'FAIL' not in result.stdout
    assert result.status == 0


def test_positive_health_check_available_space_candlepin(sat_maintain):
    """Verify available-space-cp check

    :id: 382a2bf3-a3da-4e46-b370-a443450f93b7

    :steps:
        1. Run satellite-maintain health check --label available-space-cp

    :expectedresults: available-space-cp health check should pass.
    """
    result = sat_maintain.cli.Health.check(options={'label': 'available-space-cp'})
    assert 'FAIL' not in result.stdout
    assert result.status == 0


def test_positive_hammer_defaults_set(sat_maintain, request):
    """Verify that health check is performed when
     hammer on system have defaults set.

    :id: 27a8b49b-8cb8-4004-ba41-36ed084c4740

    :steps:
        1. Setup hammer on system with defaults set
        2. Run satellite-maintain health check

    :expectedresults: Health check should pass.

    :BZ: 1632768

    :customerscenario: true
    """
    sat_maintain.cli.Defaults.add({'param-name': 'organization_id', 'param-value': 1})
    result = sat_maintain.cli.Health.check(options={'assumeyes': True})
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    @request.addfinalizer
    def _finalize():
        sat_maintain.cli.Defaults.delete({'param-name': 'organization_id'})


@pytest.mark.include_capsule
def test_positive_health_check_hotfix_installed(sat_maintain, request):
    """Verify check-hotfix-installed check.

    :id: d9023293-4173-4223-bbf5-328b41cf87cd

    :parametrized: yes

    :setup:
        1. Modify gems files of a Satellite
        2. Install hotfix-package

    :steps:
        1. Run satellite-maintain health check --label check-hotfix-installed

    :expectedresults: check-hotfix-installed check should detect modified file
        and installed hotfix.
    """
    # Verify check-hotfix-installed without hotfix package.
    result = sat_maintain.cli.Health.check(options={'label': 'check-hotfix-installed'})
    assert result.status == 0
    assert 'WARNING' not in result.stdout

    # Verify check-hotfix-installed with hotfix package.
    gems_path = '/usr/share/gems/gems/'
    fpath = sat_maintain.execute(f"find {gems_path} -type f -name 'self_upgrade.rb'")
    sat_maintain.execute(f'sed -i "$ a #modifying_file" {fpath.stdout}')
    hotfix_url = f'{settings.robottelo.repos_hosting_url}/hotfix_package/'
    sat_maintain.create_custom_repos(custom_repo=hotfix_url)
    result = sat_maintain.execute('dnf install -y --disableplugin=foreman-protector hotfix-package')
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    result = sat_maintain.cli.Health.check(options={'label': 'check-hotfix-installed'})
    assert result.status == 78
    assert 'WARNING' in result.stdout
    assert 'hotfix-package' in result.stdout

    @request.addfinalizer
    def _finalize():
        sat_maintain.execute('rm -fr /etc/yum.repos.d/custom_repo.repo')
        sat_maintain.execute('dnf remove -y hotfix-package')
        assert sat_maintain.execute(f'sed -i "/#modifying_file/d" {fpath.stdout}').status == 0


@pytest.mark.include_capsule
def test_positive_health_check_validate_yum_config(sat_maintain):
    """Verify validate-yum-config

    :id: b50c8866-6175-4286-8106-561945726023

    :parametrized: yes

    :steps:
        1. configure yum exclude.
        2. Run satellite-maintain health check --label validate-yum-config
        3. Assert that excluded packages are listed in output.
        4. remove yum exclude configured in step 1.

    :expectedresults: validate-yum-config should work.

    :BZ: 1669498

    :customerscenario: true
    """
    file = '/etc/yum.conf'
    yum_exclude = 'exclude=cat*'
    failure_message = 'Unset this configuration as it is risky while yum update or upgrade!'
    sat_maintain.execute(f'sed -i "$ a {yum_exclude}" {file}')
    result = sat_maintain.cli.Health.check(options={'label': 'validate-yum-config'})
    assert result.status == 1
    assert yum_exclude in result.stdout
    assert failure_message in result.stdout
    sat_maintain.execute(f'sed -i "/{yum_exclude}/d" {file}')
    result = sat_maintain.cli.Health.check(options={'label': 'validate-yum-config'})
    assert result.status == 0
    assert 'FAIL' not in result.stdout


@pytest.mark.include_capsule
def test_positive_health_check_epel_repository(request, sat_maintain):
    """Verify check-non-redhat-repository.

    :id: ce2d7278-d7b7-4f76-9923-79be831c0368

    :parametrized: yes

    :steps:
        1. Configure epel repository.
        2. Run satellite-maintain health check --label check-non-redhat-repository.
        3. Assert that EPEL repos are enabled on system.

    :BZ: 1755755

    :expectedresults: check-non-redhat-repository health check should pass.
    """
    epel_repo = 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm'
    sat_maintain.execute(f'dnf install -y {epel_repo}')
    result = sat_maintain.cli.Health.check(options={'label': 'check-non-redhat-repository'})
    assert 'System is subscribed to non Red Hat repositories' in result.stdout
    assert result.status == 1
    assert 'FAIL' in result.stdout

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.execute('dnf remove -y epel-release').status == 0


def test_positive_health_check_old_foreman_tasks(sat_maintain):
    """Verify check-old-foreman-tasks.

    :id: 156350c4-b55b-40b3-b8f2-202bd5ed9fb6

    :parametrized: yes

    :setup:
        1. Setup old ForemanTasks using 'foreman-rake console'

    :steps:
        1. Run satellite-maintain health check --label check-old-foreman-tasks.
        2. Assert that old tasks are found on system.
        3. Assert that old tasks are deleted from system.

    :BZ: 1745489

    :expectedresults: check-old-foreman-tasks health check should pass.
    """
    rake_command = 'foreman-rake console <<< '
    find_task = '\'t = ForemanTasks::Task.where(state: "stopped").first;'
    update_task = "t.started_at = t.started_at - 31.day;t.save(:validate => false)'"
    error_message = 'paused or stopped task(s) older than 30 days'
    delete_message = 'Deleted old tasks:'
    sat_maintain.execute(rake_command + find_task + update_task)
    result = sat_maintain.cli.Health.check(
        options={'label': 'check-old-foreman-tasks', 'assumeyes': True}
    )
    assert result.status == 0
    assert "FAIL" in result.stdout
    assert error_message in result.stdout
    assert delete_message in result.stdout
    result = sat_maintain.cli.Health.check(options={'label': 'check-old-foreman-tasks'})
    assert result.status == 0
    assert 'FAIL' not in result.stdout


@pytest.mark.include_capsule
def test_positive_health_check_tmout_variable(sat_maintain):
    """Verify check-tmout-variable. Upstream issue #23430.

    :id: e0eea928-0ffb-4692-adb9-fc4bf041f301

    :parametrized: yes

    :steps:
        1. Run satellite-maintain health check --label check-tmout-variable.
        2. Assert that check-tmout-variable pass.
        3. export TMOUT environment variable.
        4. Run satellite-maintain health check --label check-tmout-variable.
        5. Assert that check-tmout-variable fails.

    :expectedresults: check-tmout-variable health check should pass.
    """
    error_message = (
        "The TMOUT environment variable is set with value 100. "
        "Run 'unset TMOUT' command to unset this variable."
    )
    # Run check without setting TMOUT environment variable.
    result = sat_maintain.cli.Health.check(options={'label': 'check-tmout-variable'})
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    # Run check with TMOUT environment variable set.
    result = sat_maintain.cli.Health.check(
        options={'label': 'check-tmout-variable'},
        env_var='TMOUT=100',
    )
    assert result.status == 1
    assert 'FAIL' in result.stdout
    assert error_message in result.stdout


def test_positive_health_check_tftp_storage(sat_maintain, request):
    """Verify check-tftp-storage

    :id: 9a900bc7-65ff-4280-bf8a-8974a7cb76c6

    :steps:
        1. Create test files in /var/lib/tftpboot/boot/
        2. Run satellite-maintain health check --label check-tftp-storage.
        3. Assert that check-tftp-storage fails.
        4. Assert that check deletes files older than token_duration setting.
        5. Delete all files from /var/lib/tftpboot/boot/
        6. Run satellite-maintain health check --label check-tftp-storage.
        7. Assert that check-tftp-storage pass.

    :BZ: 1827176

    :customerscenario: true

    :expectedresults: check-tftp-storage health check should pass.
    """
    sat_maintain.cli.Settings.set({'name': 'token_duration', 'value': '2'})
    assert sat_maintain.cli.Settings.list({'search': 'name=token_duration'})[0]['value'] == '2'
    files_to_delete = [
        'foreman-discovery-vmlinuz',
        'foreman-discovery-initrd.img',
        'do-not-delete.yml',
    ]
    files_to_keep = ['keep-discovery-initrd.img']
    # Create files for testing check-tftp-storage check.
    for file in files_to_delete:
        assert sat_maintain.execute(f'touch /var/lib/tftpboot/boot/{file}').status == 0
    time.sleep(200)
    assert sat_maintain.execute(f'touch /var/lib/tftpboot/boot/{files_to_keep[0]}').status == 0
    # Run check-tftp-storage check.
    result = sat_maintain.cli.Health.check(
        options={'label': 'check-tftp-storage', 'assumeyes': True}
    )
    assert 'There are old initrd and vmlinuz files present in tftp' in result.stdout
    assert 'Rerunning the check after fix procedure' in result.stdout
    assert result.status == 0
    assert 'FAIL' in result.stdout
    # check whether expected files are deleted
    for file in files_to_delete[:2]:
        assert sat_maintain.execute(f'ls -l /var/lib/tftpboot/boot/{file}').status != 0
    # check whether expected files are not deleted.
    for file in files_to_keep + files_to_delete[2:]:
        assert sat_maintain.execute(f'ls -l /var/lib/tftpboot/boot/{file}').status == 0
        sat_maintain.execute(f'rm -fr /var/lib/tftpboot/boot/{file}')
    # Re-run check with no files present in /var/lib/tftpboot/boot/
    result = sat_maintain.cli.Health.check({'label': 'check-tftp-storage'})
    assert result.status == 0
    assert 'FAIL' not in result.stdout

    @request.addfinalizer
    def _finalize():
        sat_maintain.cli.Settings.set({'name': 'token_duration', 'value': '360'})
        assert (
            sat_maintain.cli.Settings.list({'search': 'name=token_duration'})[0]['value'] == '360'
        )


def test_positive_health_check_postgresql_checkpoint_segments(sat_maintain):
    """Verify check-postgresql-checkpoint-segments

    :id: 963a5b47-168a-4443-9fdf-bba59c9b0e97

    :steps:
        1. Have an invalid /etc/foreman-installer/custom-hiera.yaml file
        2. Run satellite-maintain health check --label check-postgresql-checkpoint-segments.
        3. Assert that check-postgresql-checkpoint-segments gives proper
           error message saying an invalid yaml file
        4. Make /etc/foreman-installer/custom-hiera.yaml file valid
        5. Add config_entries section in /etc/foreman-installer/custom-hiera.yaml
        6. Run satellite-maintain health check --label check-postgresql-checkpoint-segments.
        7. Assert that check-postgresql-checkpoint-segments fails.
        8. Add checkpoint_segments parameter in /etc/foreman-installer/custom-hiera.yaml
        9. Run satellite-maintain health check --label check-postgresql-checkpoint-segments.
        10. Assert that check-postgresql-checkpoint-segments fails.
        11. Remove config_entries section from /etc/foreman-installer/custom-hiera.yaml
        12. Run satellite-maintain health check --label check-postgresql-checkpoint-segments.
        13. Assert that check-postgresql-checkpoint-segments pass.

    :BZ: 1894149, 1899322

    :expectedresults: check-postgresql-checkpoint-segments health check should pass.

    :CaseImportance: High
    """
    custom_hiera = '/etc/foreman-installer/custom-hiera.yaml'
    # Create invalid yaml file
    sat_maintain.execute(f'sed -i "s/---/----/g" {custom_hiera}')
    result = sat_maintain.cli.Health.check(
        options={'label': 'check-postgresql-checkpoint-segments'}
    )

    assert f'File {custom_hiera} is not a yaml file.' in result.stdout
    assert 'FAIL' in result.stdout
    assert result.status == 1
    # Make yaml file valid
    sat_maintain.execute(f'sed -i "s/----/---/g" {custom_hiera}')
    # Add config_entries section
    sat_maintain.execute(f'sed -i "$ a postgresql::server::config_entries:" {custom_hiera}')
    # Run check-postgresql-checkpoint-segments check.
    result = sat_maintain.cli.Health.check(
        options={'label': 'check-postgresql-checkpoint-segments'}
    )

    assert "ERROR: 'postgresql::server::config_entries' cannot be null." in result.stdout
    assert 'Please remove it from following file and re-run the command.' in result.stdout
    assert result.status == 1
    assert 'FAIL' in result.stdout
    # Add checkpoint_segments
    sat_maintain.execute(fr'sed -i "$ a\  checkpoint_segments: 32" {custom_hiera}')
    # Run check-postgresql-checkpoint-segments check.
    result = sat_maintain.cli.Health.check(
        options={'label': 'check-postgresql-checkpoint-segments'}
    )

    assert "ERROR: Tuning option 'checkpoint_segments' found." in result.stdout
    assert 'Please remove it from following file and re-run the command.' in result.stdout
    assert result.status == 1
    assert 'FAIL' in result.stdout
    # Remove config_entries section
    sat_maintain.execute(
        fr'sed -i "/postgresql::server::config_entries\|checkpoint_segments: 32/d" {custom_hiera}'
    )
    # Run check-postgresql-checkpoint-segments check.
    result = sat_maintain.cli.Health.check(
        options={'label': 'check-postgresql-checkpoint-segments'}
    )
    assert result.status == 0
    assert 'FAIL' not in result.stdout


@pytest.mark.include_capsule
def test_positive_health_check_env_proxy(sat_maintain):
    """Verify env-proxy health check.

    :id: f8c44b40-3ce5-4179-8d6b-1156c0032450

    :parametrized: yes

    :steps:
        1. export HTTP_PROXY environment variable.
        2. Run satellite-maintain health check --label env-proxy.
        3. Assert that check env-proxy fail.
        4. Run satellite-maintain health check --label env-proxy.
        5. Assert that check env-proxy pass.

    :expectedresults: check env-proxy health check should pass .

    :CaseImportance: Medium
    """
    error_message = 'Global HTTP(S) proxy in environment (env) is set. Please unset first!'
    # Run check with HTTP_PROXY environment variable set.
    result = sat_maintain.cli.Health.check(
        options={'label': 'env-proxy'}, env_var='HTTP_PROXY=https://proxy.example.com:5442'
    )
    assert 'FAIL' in result.stdout
    assert result.status == 1
    assert error_message in result.stdout
    # Run check without setting HTTP_PROXY environment variable.
    result = sat_maintain.cli.Health.check(options={'label': 'env-proxy'})
    assert result.status == 0
    assert 'FAIL' not in result.stdout


@pytest.mark.stubbed
def test_positive_health_check_foreman_proxy_verify_dhcp_config_syntax():
    """Verify foreman-proxy-verify-dhcp-config-syntax

    :id: 43ca5cc7-9888-490d-b1ba-f3298e737039

    :parametrized: yes

    :setup:
        1. Satellite instance configured with external DHCP like Infoblox,
           which has `:use_provider: dhcp_infoblox` set in /etc/foreman-proxy/settings.d/dhcp.yml
        2. Satellite instance which is DHCP enabled and has `:use_provider: dhcp_isc`
           set in /etc/foreman-proxy/settings.d/dhcp.yml

    :steps:
        1. satellite-maintain health list | grep foreman-proxy-verify-dhcp-config-syntax
        2. satellite-maintain health check --label foreman-proxy-verify-dhcp-config-syntax

    :BZ: 1847889

    :expectedresults: Check is not available on the satellite instances where `:use_provider:`
                      is set other than `dhcp_isc`, and also not on DHCP disabled Satellite.

    :CaseImportance: Medium

    :CaseAutomation: NotAutomated
    """


def test_positive_remove_job_file(sat_maintain):
    """Verify file /var/lib/pulp/job1.0.0 is not present after the following command.

    :id: eed224f9-a2ec-4d15-9047-cede0b823866

    :steps:
        1. Run satellite-maintain health list --tags pre-upgrade
        2. Run satellite-maintain health check --label disk-performance

    :expectedresults: `disk-performance` shouldn't exist under pre-upgrade tag and
            /var/lib/pulp/job1.0.0 file should not exist after check execution

    :CaseImportance: Medium

    :BZ: 1827219, 1762302
    """
    # Verify pre-upgrade checks don't include disk-performance check
    result = sat_maintain.cli.Health.list({'tags': 'pre-upgrade'})
    assert 'disk-performance' not in result.stdout
    # Verify job1.0.0 file not exist after check completion
    result = sat_maintain.cli.Health.check(options={'label': 'disk-performance', 'assumeyes': True})
    assert 'FAIL' not in result.stdout
    assert sat_maintain.execute("ls -l /var/lib/pulp/job1.0.0").status != 0


def test_positive_health_check_corrupted_roles(sat_maintain, request):
    """Verify corrupted-roles check.

    :id: 46117c38-edec-462d-83e1-4a5c035500d7

    :steps:
        1. Run satellite-maintain health check --label corrupted-roles
        2. Run "hammer filter list --search role=test_role" again to check if corrupted roles
           are fixed and verify if new filter is created for updated resource_type

    :expectedresults: corrupted-roles health check should pass and should handle corrupted
                      roles by splitting filters as per updated values.

    :CaseImportance: Medium

    :BZ: 1703041, 1908846
    """
    # Check the filter created to verify the role, resource type, and permissions assigned.
    role_name = 'test_role'
    resource_type = gen_string("alpha")
    sat_maintain.cli.Role.create(options={'name': role_name})
    sat_maintain.cli.Filter.create(
        options={'role': role_name, 'permissions': ['view_hosts', 'console_hosts']}
    )
    permission_name = r"'\''console_hosts'\''"
    resource_type = rf"'\''{resource_type}'\''"
    setup = sat_maintain.execute(
        f'''sudo su - postgres -c "psql -d foreman -c 'UPDATE permissions SET
            resource_type = {resource_type} WHERE name = {permission_name};'"'''
    )
    assert setup.status == 0
    result = sat_maintain.cli.Filter.list(options={'search': role_name}, output_format='yaml')
    # Shows the filter id which comprises of role id hence asserting 2 here
    assert result.count('Id') == 2
    # Run corrupted-roles check.
    result = sat_maintain.cli.Health.check(options={'label': 'corrupted-roles', 'assumeyes': True})
    assert result.status == 0
    assert 'FAIL' in result.stdout
    # Verify corrupted roles are fixed and new filter is created for updated resource_type.
    result = sat_maintain.cli.Filter.list(options={'search': role_name}, output_format='yaml')
    assert result.count('Id') == 4

    @request.addfinalizer
    def _finalize():
        resource_type = r"'\''Host'\''"
        sat_maintain.execute(
            f'''sudo su - postgres -c "psql -d foreman -c 'UPDATE permissions SET
                        resource_type = {resource_type} WHERE name = {permission_name};'"'''
        )
        sat_maintain.cli.Role.delete(options={'name': role_name})


@pytest.mark.include_capsule
def test_positive_health_check_non_rh_packages(sat_maintain, request):
    """Verify non-rh-packages health check

    :id: 2b7a25bb-902c-4a87-bb71-f460dcce655c

    :parametrized: yes

    :setup:
        1. Configure custom repository and install non-RH/custom package

    :steps:
        1. Run satellite-maintain health check --label non-rh-packages.
        2. Verify presense of non-RH/custom package installed on system.

    :BZ: 1869865

    :expectedresults: check-non-rh-packages health check should pass.

    :CaseImportance: High
    """
    sat_maintain.create_custom_repos(custom_repo=settings.repos.yum_0.url)
    assert (
        sat_maintain.cli.Packages.install(packages='walrus', options={'assumeyes': True}).status
        == 0
    )
    result = sat_maintain.cli.Health.check({'label': 'non-rh-packages'})
    assert 'Found 1 unexpected non Red Hat Package(s) installed!' in result.stdout
    assert 'walrus-5.21-1.noarch' in result.stdout
    assert result.status == 78
    assert 'WARNING' in result.stdout

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.execute('dnf remove -y  walrus').status == 0
        assert sat_maintain.execute('rm -fr /etc/yum.repos.d/custom_repo.repo').status == 0


@pytest.mark.stubbed
def test_positive_health_check_available_space_postgresql12():
    """Verify warnings when available space in /var/opt/rh/rh-postgresql12/
    is less than consumed space of /var/lib/pgsql/

    :id: 283e627d-6afc-49cb-afdb-5b77a91bbd1e

    :parametrized: yes

    :setup:
        1. Have some data under /var/lib/pgsql (upgrade templates have ~565Mib data)
        2. Create dir /var/opt/rh/rh-postgresql12/ and mount a partition of ~300Mib
           to this dir (less than /var/lib/pgsql).

    :steps:
        1. satellite-maintain health check --label available-space-for-postgresql12
        2. Verify Warning or Error is displayed when enough space is not
           available under /var/opt/rh/rh-postgresql12/

    :BZ: 1898108, 1973363

    :expectedresults: Verify warnings when available space in /var/opt/rh/rh-postgresql12/
                      is less than consumed space of /var/lib/pgsql/

    :CaseImportance: High

    :CaseAutomation: ManualOnly
    """


def test_positive_health_check_duplicate_permissions(sat_maintain):
    """Verify duplicate-permissions check

    :id: 192a5943-43cc-4f89-9949-893c8011831a

    :setup:
        1. Setup duplicate permissions in the database

    :steps:
        1. foreman-maintain health check --label duplicate-permissions

    :expectedresults: Verify if the check passes and removes duplicate permissions.

    :CaseImportance: High

    :BZ: 1849110, 1884024
    """
    # Verify if check failed because of duplicate permissions
    name = r"'\''view_ansible_variables'\''"
    resource_type = r"'\''AnsibleVariable'\''"
    result = sat_maintain.execute(
        f'''sudo su - postgres -c "psql -d foreman -c 'INSERT INTO permissions(name, resource_type)
            VALUES({name}, {resource_type});'"'''
    )
    assert result.status == 0
    result = sat_maintain.cli.Health.check({'label': 'duplicate-permissions', 'assumeyes': True})
    assert result.status == 0
    assert 'FAIL' in result.stdout
    assert 'Remove duplicate permissions from database' in result.stdout
    # Verify the check passed
    result = sat_maintain.cli.Health.check({'label': 'duplicate-permissions'})
    assert result.status == 0
    assert 'FAIL' not in result.stdout
