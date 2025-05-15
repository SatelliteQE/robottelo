"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:Team: Rocket

:CaseImportance: High
"""

from time import sleep

import awxkit
from fauxfactory import gen_string
import pytest
from wait_for import wait_for
import yaml

from robottelo.config import (
    robottelo_tmp_dir,
    settings,
)
from robottelo.exceptions import CLIFactoryError
from robottelo.utils.issue_handlers import is_open


def assert_job_invocation_result(
    sat, invocation_command_id, client_hostname, expected_result='success'
):
    """Asserts the job invocation finished with the expected result and fetches job output
    when error occurs. Result is one of: success, pending, error, warning"""
    result = sat.cli.JobInvocation.info({'id': invocation_command_id})
    try:
        assert result[expected_result] == '1'
    except AssertionError as err:
        raise AssertionError(
            'host output: {}'.format(
                ' '.join(
                    sat.cli.JobInvocation.get_output(
                        {'id': invocation_command_id, 'host': client_hostname}
                    )
                )
            )
        ) from err


@pytest.mark.upgrade
class TestAnsibleCfgMgmt:
    """Test class for Configuration Management with Ansible

    :CaseComponent: Ansible-ConfigurationManagement
    """

    @pytest.mark.e2e
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_match('[^6].*')
    def test_positive_ansible_e2e(
        self, target_sat, module_sca_manifest_org, module_ak_with_cv, rhel_contenthost
    ):
        """
        Test successful execution of Ansible Job on host.

        :id: 0c52bc63-a41a-4f48-a980-fe49b4ecdbdc

        :steps:
            1. Register a content host with satellite
            2. Import a role into satellite
            3. Assign that role to a host
            4. Assert that the role and variable were assigned to the host successfully
            5. Run the Ansible playbook associated with that role
            6. Check if the job is executed successfully.
            7. Disassociate the Role from the host.
            8. Delete the assigned ansible role

        :expectedresults:
            1. Host should be assigned the proper role.
            2. Job execution must be successful.
            3. Operations performed with hammer must be successful.

        :BZ: 2154184

        :customerscenario: true
        """
        SELECTED_ROLE = 'RedHatInsights.insights-client'
        SELECTED_ROLE_1 = 'theforeman.foreman_scap_client'
        SELECTED_VAR = gen_string('alpha')
        proxy_id = target_sat.nailgun_smart_proxy.id
        rhel_contenthost.enable_ipv6_dnf_and_rhsm_proxy()
        # disable batch tasks to test BZ#2154184
        target_sat.cli.Settings.set({'name': 'foreman_tasks_proxy_batch_trigger', 'value': 'false'})
        result = rhel_contenthost.register(
            module_sca_manifest_org, None, module_ak_with_cv.name, target_sat
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        if rhel_contenthost.os_version.major <= 7:
            rhel_contenthost.create_custom_repos(rhel7=settings.repos.rhel7_os)
            assert rhel_contenthost.execute('yum install -y insights-client').status == 0
        target_host = rhel_contenthost.nailgun_host

        target_sat.cli.Ansible.roles_sync(
            {'role-names': f'{SELECTED_ROLE},{SELECTED_ROLE_1}', 'proxy-id': proxy_id}
        )
        result = target_sat.cli.Host.ansible_roles_add(
            {'id': target_host.id, 'ansible-role': SELECTED_ROLE}
        )
        assert 'Ansible role has been associated.' in result[0]['message']

        target_sat.cli.Ansible.variables_create(
            {'variable': SELECTED_VAR, 'ansible-role': SELECTED_ROLE}
        )

        assert SELECTED_ROLE, (
            SELECTED_VAR in target_sat.cli.Ansible.variables_info({'name': SELECTED_VAR}).stdout
        )
        template_id = (
            target_sat.api.JobTemplate()
            .search(query={'search': 'name="Ansible Roles - Ansible Default"'})[0]
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
            f'resource_type = JobInvocation and resource_id = {job["id"]}', poll_timeout=1000
        )
        result = target_sat.api.JobInvocation(id=job['id']).read()
        assert result.succeeded == 1

        result = target_sat.cli.Host.ansible_roles_assign(
            {'id': target_host.id, 'ansible-roles': f'{SELECTED_ROLE},{SELECTED_ROLE_1}'}
        )
        assert 'Ansible roles were assigned to the host' in result[0]['message']

        result = target_sat.cli.Host.ansible_roles_remove(
            {'id': target_host.id, 'ansible-role': SELECTED_ROLE}
        )
        assert 'Ansible role has been disassociated.' in result[0]['message']

        result = target_sat.cli.Ansible.roles_delete({'name': SELECTED_ROLE})
        assert f'Ansible role [{SELECTED_ROLE}] was deleted.' in result[0]['message']

        assert SELECTED_ROLE, (
            SELECTED_VAR not in target_sat.cli.Ansible.variables_info({'name': SELECTED_VAR}).stdout
        )

    @pytest.mark.e2e
    def test_add_and_remove_ansible_role_hostgroup(self, target_sat):
        """
        Test add and remove functionality for ansible roles in hostgroup via CLI

        :id: 2c6fda14-4cd2-490a-b7ef-7a08f8164fad

        :customerscenario: true

        :steps:
            1. Create a hostgroup
            2. Sync few ansible roles
            3. Assign a few ansible roles with the host group
            4. Add some ansible role with the host group
            5. Remove the added ansible roles from the host group

        :expectedresults:
            1. Ansible role assign/add/remove functionality should work as expected in CLI

        :BZ: 2029402
        """
        ROLES = [
            'theforeman.foreman_scap_client',
            'redhat.satellite.hostgroups',
            'RedHatInsights.insights-client',
        ]
        proxy_id = target_sat.nailgun_smart_proxy.id
        hg_name = gen_string('alpha')
        result = target_sat.cli.HostGroup.create({'name': hg_name})
        assert result['name'] == hg_name
        target_sat.cli.Ansible.roles_sync({'role-names': ROLES, 'proxy-id': proxy_id})
        result = target_sat.cli.HostGroup.ansible_roles_assign(
            {'name': hg_name, 'ansible-roles': f'{ROLES[1]},{ROLES[2]}'}
        )
        assert 'Ansible roles were assigned to the hostgroup' in result[0]['message']
        result = target_sat.cli.HostGroup.ansible_roles_add(
            {'name': hg_name, 'ansible-role': ROLES[0]}
        )
        assert 'Ansible role has been associated.' in result[0]['message']
        result = target_sat.cli.HostGroup.ansible_roles_remove(
            {'name': hg_name, 'ansible-role': ROLES[0]}
        )
        assert 'Ansible role has been disassociated.' in result[0]['message']

    @pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
    def test_positive_ansible_variables_installed_with_collection(
        self, request, target_sat, module_org, module_ak_with_cv, rhel_contenthost
    ):
        """Verify that installing an Ansible collection also imports
        any variables associated with the roles avaialble in the collection

        :id: 7ff88022-fe9b-482f-a6bb-3922036a1e1c

        :steps:
            1. Register a content host with Satellite
            2. Install a ansible collection with roles from ansible-galaxy
            3. Import any role with variables from installed ansible collection
            4. Assert that the role is imported along with associated variables
            5. Assign that role to a host and verify the role assigned to the host

        :expectedresults: Verify variables associated to role from collection are also imported along with roles

        :bz: 1982753
        """
        SELECTED_COLLECTION = 'oasis_roles.system'
        SELECTED_ROLE = 'oasis_roles.system.sshd'
        SELECTED_VAR = 'sshd_allow_password_login'

        @request.addfinalizer
        def _finalize():
            result = target_sat.cli.Ansible.roles_delete({'name': SELECTED_ROLE})
            assert f'Ansible role [{SELECTED_ROLE}] was deleted.' in result[0]['message']

        result = rhel_contenthost.register(
            module_org,
            None,
            module_ak_with_cv.name,
            target_sat,
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        target_host = rhel_contenthost.nailgun_host
        proxy_id = target_sat.nailgun_smart_proxy.id

        for path in ['/etc/ansible/collections', '/usr/share/ansible/collections']:
            http_proxy = (
                f'HTTPS_PROXY={settings.http_proxy.HTTP_PROXY_IPv6_URL} '
                if settings.server.is_ipv6
                else ''
            )
            assert (
                target_sat.execute(
                    f'{http_proxy}ansible-galaxy collection install -p {path} {SELECTED_COLLECTION}'
                ).status
                == 0
            )
            target_sat.cli.Ansible.roles_sync({'role-names': SELECTED_ROLE, 'proxy-id': proxy_id})
            result = target_sat.cli.Host.ansible_roles_assign(
                {'id': target_host.id, 'ansible-roles': f'{SELECTED_ROLE}'}
            )
            assert 'Ansible roles were assigned to the host' in result[0]['message']

            result = target_sat.cli.Ansible.variables_list(
                {'search': f'ansible_role="{SELECTED_ROLE}"'}
            )
            assert result[0]['variable'] == SELECTED_VAR
            # Remove the ansible collection from collection_paths
            target_sat.execute(f'rm -rf {path}/ansible_collections/')


@pytest.mark.upgrade
class TestAnsibleREX:
    """Test class for remote execution via Ansible

    :CaseComponent: Ansible-RemoteExecution
    """

    @pytest.mark.pit_client
    @pytest.mark.pit_server
    @pytest.mark.rhel_ver_match('[^6]')
    def test_positive_run_effective_user_job(self, rex_contenthost, target_sat):
        """Tests Ansible REX job having effective user runs successfully

        :id: a5fa20d8-c2bd-4bbf-a6dc-bf307b59dd8c

        :steps:
            0. Create a VM and register to SAT and prepare for REX (ssh key)
            1. Run Ansible Command job for the host to create a user
            2. Run Ansible Command job using effective user
            3. Check the job result at the host is done under that user

        :expectedresults: multiple asserts along the code

        :parametrized: yes
        """
        client = rex_contenthost
        # create a user on client via remote job
        username = gen_string('alpha')
        filename = gen_string('alpha')
        make_user_job = target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': f'command=useradd -m {username}',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(target_sat, make_user_job['id'], client.hostname)
        # create a file as new user
        invocation_command = target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': f'command=touch /home/{username}/{filename}',
                'search-query': f'name ~ {client.hostname}',
                'effective-user': username,
            }
        )
        assert_job_invocation_result(target_sat, invocation_command['id'], client.hostname)

        # check the file owner
        result = client.execute(
            f'''stat -c '%U' /home/{username}/{filename}''',
        )
        # assert the file is owned by the effective user
        assert username == result.stdout.strip('\n'), 'file ownership mismatch'

    @pytest.mark.rhel_ver_list([8])
    def test_positive_run_reccuring_job(self, rex_contenthost, target_sat):
        """Tests Ansible REX reccuring job runs successfully multiple times

        :id: 49b0d31d-58f9-47f1-aa5d-561a1dcb0d66

        :setup:
            1. Create a VM, register to SAT and configure REX (ssh-key)

        :steps:
            1. Run recurring Ansible Command job for the host
            2. Check the multiple job results at the host

        :expectedresults: multiple asserts along the code

        :bz: 2129432

        :customerscenario: true

        :parametrized: yes
        """
        client = rex_contenthost
        invocation_command = target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': 'command=ls',
                'search-query': f'name ~ {client.hostname}',
                'cron-line': '* * * * *',  # every minute
                'max-iteration': 2,  # just two runs
            }
        )
        result = target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
        sleep(150)
        rec_logic = target_sat.cli.RecurringLogic.info({'id': result['recurring-logic-id']})
        assert rec_logic['state'] == 'finished'
        assert rec_logic['iteration'] == '2'
        # 2129432
        rec_logic_keys = rec_logic.keys()
        assert 'action' in rec_logic_keys
        assert 'last-occurrence' in rec_logic_keys
        assert 'next-occurrence' in rec_logic_keys
        assert 'state' in rec_logic_keys
        assert 'purpose' in rec_logic_keys
        assert 'iteration' in rec_logic_keys
        assert 'iteration-limit' in rec_logic_keys

    @pytest.mark.rhel_ver_list([8])
    def test_positive_run_concurrent_jobs(self, rex_contenthosts, target_sat):
        """Tests Ansible REX concurent jobs without batch trigger

        :id: ad0f108c-03f2-49c7-8732-b1056570567b

        :steps:
            1. Create 2 hosts, disable foreman_tasks_proxy_batch_trigger
            2. Run Ansible Command job with concurrency-setting

        :expectedresults: multiple asserts along the code

        :BZ: 1817320

        :customerscenario: true

        :parametrized: yes
        """
        clients = rex_contenthosts
        param_name = 'foreman_tasks_proxy_batch_trigger'
        target_sat.cli.GlobalParameter().set({'name': param_name, 'value': 'false'})
        output_msgs = []
        invocation_command = target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': 'command=ls',
                'search-query': f'name ~ {clients[0].hostname} or name ~ {clients[1].hostname}',
                'concurrency-level': 2,
            }
        )
        for vm in clients:
            output_msgs.append(
                'host output from {}: {}'.format(
                    vm.hostname,
                    ' '.join(
                        target_sat.cli.JobInvocation.get_output(
                            {'id': invocation_command['id'], 'host': vm.hostname}
                        )
                    ),
                )
            )
        result = target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
        assert result['success'] == '2', output_msgs
        target_sat.cli.GlobalParameter().delete({'name': param_name})
        assert len(target_sat.cli.GlobalParameter().list({'search': param_name})) == 0

    @pytest.mark.parametrize(
        'value', [0, -2, 2.5, 'a'], ids=['zero', 'negative', 'decimal', 'string']
    )
    @pytest.mark.rhel_ver_list([8])
    def test_negative_invalid_concurrency_level(self, rex_contenthost, target_sat, value):
        """Tests you can not invoke job with invalid concurrency level

        :id: 15b55f91-759a-4b77-8ba2-330a5ca7ca0b

        :steps:
            1. Run a REX job with invalid concurrency-setting

        :expectedresults: should refuse gracefully

        :BZ: 2250732

        :parametrized: yes
        """
        with pytest.raises(CLIFactoryError) as error:
            target_sat.cli_factory.job_invocation(
                {
                    'job-template': 'Run Command - Ansible Default',
                    'inputs': 'command=ls',
                    'search-query': f'name ~ {rex_contenthost.hostname}',
                    'concurrency-level': f'{value}',
                }
            )
        assert 'Concurrency level: must be greater than 0' in str(
            error.value
        ) or 'Numeric value is required' in str(error.value)

    @pytest.mark.rhel_ver_list([8])
    def test_positive_run_serial(self, rex_contenthosts, target_sat):
        """Tests subtasks in a job run one by one when concurrency level set to 1

        :id: 5ce39447-82d0-42df-81be-16ed3d67a2a4

        :setup:
            1. Create 2 hosts, register to SAT and configure REX (ssh-key)

        :steps:
            1. Run a bash command job with concurrency level 1

        :expectedresults: First subtask should run immediately, second one after the first one finishes

        :parametrized: yes
        """
        hosts = rex_contenthosts
        output_msgs = []
        template_file = f'/root/{gen_string("alpha")}.template'
        target_sat.execute(
            f"echo 'rm /root/test-<%= @host %>; echo $(date +%s) >> /root/test-<%= @host %>; sleep 120; echo $(date +%s) >> /root/test-<%= @host %>' > {template_file}"
        )
        template = target_sat.cli.JobTemplate.create(
            {
                'name': gen_string('alpha'),
                'file': template_file,
                'job-category': 'Commands',
                'provider-type': 'script',
            }
        )
        invocation = target_sat.cli_factory.job_invocation(
            {
                'job-template': template['name'],
                'search-query': f'name ~ {hosts[0].hostname} or name ~ {hosts[1].hostname}',
                'concurrency-level': 1,
            }
        )
        for vm in hosts:
            output_msgs.append(
                'host output from {}: {}'.format(
                    vm.hostname,
                    ' '.join(
                        target_sat.cli.JobInvocation.get_output(
                            {'id': invocation['id'], 'host': vm.hostname}
                        )
                    ),
                )
            )
        result = target_sat.cli.JobInvocation.info({'id': invocation['id']})
        assert result['success'] == '2', output_msgs
        # assert for time diffs
        file1 = hosts[0].execute('cat /root/test-$(hostname)').stdout
        file2 = hosts[1].execute('cat /root/test-$(hostname)').stdout
        file1_start, file1_end = map(int, file1.rstrip().split('\n'))
        file2_start, file2_end = map(int, file2.rstrip().split('\n'))
        if file1_start > file2_start:
            file1_start, file1_end, file2_start, file2_end = (
                file2_start,
                file2_end,
                file1_start,
                file1_end,
            )
        assert file1_end - file1_start >= 120
        assert file2_end - file2_start >= 120
        assert file2_start >= file1_end  # the jobs did NOT run concurrently

    @pytest.mark.e2e
    @pytest.mark.no_containers
    @pytest.mark.pit_server
    @pytest.mark.pit_client
    @pytest.mark.rhel_ver_match('[^6].*')
    @pytest.mark.skipif(
        (not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url'
    )
    def test_positive_run_packages_and_services_job(
        self, rhel_contenthost, module_sca_manifest_org, module_ak_with_cv, target_sat
    ):
        """Tests Ansible REX job can install packages and start services

        :id: 47ed82fb-77ca-43d6-a52e-f62bae5d3a42

        :setup:
            1. Create a VM, register to SAT and configure REX (ssh-key)

        :steps:
            1. Run Ansible Package job for the host to install a package
            2. Check the package is present at the host
            3. Run Ansible Service job for the host to start a service
            4. Check the service is started on the host

        :expectedresults: multiple asserts along the code

        :bz: 1872688, 1811166

        :customerscenario: true

        :parametrized: yes
        """
        client = rhel_contenthost
        packages = ['tapir']
        result = client.register(
            module_sca_manifest_org,
            None,
            module_ak_with_cv.name,
            target_sat,
            repo_data=f'repo={settings.repos.yum_3.url}',
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        # install package
        invocation_command = target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Package Action - Ansible Default',
                'inputs': 'state=latest, name={}'.format(*packages),
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(target_sat, invocation_command['id'], client.hostname)
        result = client.run(f'rpm -q {" ".join(packages)}')
        assert result.status == 0

        # stop a service
        service = 'rsyslog'
        invocation_command = target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Service Action - Ansible Default',
                'inputs': f'state=stopped, name={service}',
                'search-query': f"name ~ {client.hostname}",
            }
        )
        assert_job_invocation_result(target_sat, invocation_command['id'], client.hostname)
        result = client.execute(f'systemctl status {service}')
        assert result.status == 3

        # start it again
        invocation_command = target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Service Action - Ansible Default',
                'inputs': f'state=started, name={service}',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(target_sat, invocation_command['id'], client.hostname)
        result = client.execute(f'systemctl status {service}')
        assert result.status == 0

    @pytest.mark.upgrade
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
    def test_positive_install_ansible_collection(
        self, rhel_contenthost, target_sat, module_org, module_ak_with_cv
    ):
        """Test whether Ansible collection can be installed via Ansible REX

        :id: ad25aee5-4ea3-4743-a301-1c6271856f79

        :steps:
            1. Upload a manifest.
            2. Register content host to Satellite with REX setup
            3. Enable Ansible repo on content host.
            4. Install ansible or ansible-core package
            5. Run REX job to install Ansible collection on content host.

        :expectedresults: Ansible collection can be installed on content host via REX.

        :verifies: SAT-30807
        """
        client = rhel_contenthost
        # Adding IPv6 proxy for IPv6 communication
        client.enable_ipv6_dnf_and_rhsm_proxy()
        rhel_contenthost.enable_ipv6_system_proxy()
        # Enable Ansible repository and Install ansible or ansible-core package
        client.register(module_org, None, module_ak_with_cv.name, target_sat)
        rhel_repo_urls = getattr(settings.repos, f'rhel{client.os_version.major}_os', None)
        rhel_contenthost.create_custom_repos(**rhel_repo_urls)
        assert client.execute('dnf -y install ansible-core').status == 0

        collection_job = target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Ansible Collection - Install from Galaxy',
                'inputs': 'ansible_collections_list="oasis_roles.system"',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        result = target_sat.cli.JobInvocation.info({'id': collection_job['id']})
        assert result['success'] == '1'
        collection_path = client.execute('ls /etc/ansible/collections/ansible_collections').stdout
        assert 'oasis_roles' in collection_path

        # Extend test with custom collections_path advanced input field
        collection_job = target_sat.cli_factory.job_invocation(
            {
                'job-template': 'Ansible Collection - Install from Galaxy',
                'inputs': 'ansible_collections_list="oasis_roles.system", collections_path="~/"',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        result = target_sat.cli.JobInvocation.info({'id': collection_job['id']})
        assert result['success'] == '1'
        collection_path = client.execute('ls ~/ansible_collections').stdout
        assert 'oasis_roles' in collection_path

    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
    @pytest.mark.parametrize('auth_type', ['admin', 'non-admin'])
    def test_positive_ansible_variables_imported_with_roles(
        self,
        request,
        auth_type,
        target_sat,
        module_org,
        default_location,
        module_ak_with_cv,
        rhel_contenthost,
    ):
        """Verify that when Ansible roles are imported, their variables are imported simultaneously

        :id: 107c53e8-5a8a-4291-bbde-fbd66a0bb85e

        :steps:
            1. Register a content host with satellite
            2. Create a custom role with variables and import it into satellite
            3. Assert that the role is imported along with associated variables
            4. Assign that role to a host and verify the role is assigned to the host
            5. Run the Ansible role

        :expectedresults:
            1. Verify variables associated to role are also imported along with roles
            2. Verify custom role is successfully assigned and running on a host

        :verifies: SAT-28198
        """
        username = settings.server.admin_username
        password = settings.server.admin_password
        if auth_type == 'non-admin':
            username = gen_string('alpha')
            user = target_sat.cli_factory.user(
                {
                    'admin': False,
                    'login': username,
                    'password': password,
                    'organization-ids': module_org.id,
                    'location-ids': default_location.id,
                }
            )
            target_sat.cli.User.add_role(
                {'id': user['id'], 'login': username, 'role': 'Ansible Roles Manager'}
            )

        @request.addfinalizer
        def _finalize():
            result = target_sat.cli.Ansible.roles_delete({'name': SELECTED_ROLE})
            assert f'Ansible role [{SELECTED_ROLE}] was deleted.' in result[0]['message']
            target_sat.execute(f'rm -rvf /etc/ansible/roles/{SELECTED_ROLE}')

        SELECTED_ROLE = gen_string('alphanumeric')
        playbook = f'{robottelo_tmp_dir}/playbook.yml'
        vars = f'{robottelo_tmp_dir}/vars.yml'
        target_sat.execute(f'ansible-galaxy init --init-path /etc/ansible/roles/ {SELECTED_ROLE}')
        tasks_file = f'/etc/ansible/roles/{SELECTED_ROLE}/tasks/main.yml'
        vars_file = f'/etc/ansible/roles/{SELECTED_ROLE}/{"defaults" if is_open("SAT-28198") else "vars"}/main.yml'
        tasks_main = [
            {
                'name': 'Copy SSH keys',
                'copy': {
                    'src': '/var/lib/foreman-proxy/ssh/{{ item }}',
                    'dest': '/root/.ssh',
                    'owner': 'root',
                    'group': 'root',
                    'mode': '0400',
                },
                'loop': '{{ ssh_keys }}',
            }
        ]
        vars_main = {'ssh_keys': ['id_rsa_foreman_proxy.pub', 'id_rsa_foreman_proxy']}
        with open(playbook, 'w') as f:
            yaml.dump(tasks_main, f, sort_keys=False, default_flow_style=False)
        with open(vars, 'w') as f:
            yaml.dump(vars_main, f, sort_keys=False, default_flow_style=False)
        target_sat.put(playbook, tasks_file)
        target_sat.put(vars, vars_file)

        result = rhel_contenthost.register(
            module_org,
            None,
            module_ak_with_cv.name,
            target_sat,
            auth_username=username,
            auth_password=password,
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        proxy_id = target_sat.nailgun_smart_proxy.id
        target_host = rhel_contenthost.nailgun_host
        target_sat.cli.Ansible.with_user(username, password).roles_sync(
            {'role-names': SELECTED_ROLE, 'proxy-id': proxy_id}
        )
        result = target_sat.cli.Host.with_user(username, password).ansible_roles_assign(
            {'id': target_host.id, 'ansible-roles': f'{SELECTED_ROLE}'}
        )
        assert 'Ansible roles were assigned to the host' in result[0]['message']

        role_list = target_sat.cli.Host.with_user(username, password).ansible_roles_list(
            {'name': target_host.name}
        )
        assert role_list[0]['name'] == SELECTED_ROLE

        result = target_sat.cli.Ansible.with_user(username, password).variables_list(
            {'search': f'ansible_role="{SELECTED_ROLE}"'}
        )
        assert result[0]['variable'] == 'ssh_keys'

        job_id = target_sat.cli.Host.ansible_roles_play({'name': rhel_contenthost.hostname})[0].get(
            'id'
        )
        target_sat.wait_for_tasks(
            f'resource_type = JobInvocation and resource_id = {job_id} and action ~ "hosts job"'
        )
        result = target_sat.cli.JobInvocation.info({'id': job_id})['success']
        assert result == '1'


@pytest.mark.upgrade
@pytest.mark.parametrize('aap_version', ['2.3', '2.5'], scope='class')
class TestAnsibleAAPIntegration:
    """Test class for Satellite integration with Ansible Automation Controller

    :CaseComponent: Ansible-ConfigurationManagement
    """

    def update_sat_credentials_in_aap(
        self,
        aap_client,
        sat,
        username=settings.server.admin_username,
        password=settings.server.admin_password,
        creds_name=settings.AAP_INTEGRATION.satellite_credentials,
        aap_version='2.5',
    ):
        # Find the Satellite credentials in AAP and update it for target_sat.hostname and user credentials
        api_base = '/api/v2/' if aap_version == '2.3' else '/api/controller/v2/'
        creds_list = aap_client.get(
            f'{api_base}credentials/', query_parameters=f'name={creds_name}'
        ).json()
        new_creds = {
            'inputs': {
                'host': f'https://{sat.hostname}',
                'username': username,
                'password': password,
            }
        }
        response = aap_client.patch(
            f'{api_base}credentials/{creds_list["results"][0]["id"]}/', json=new_creds
        )
        assert response.ok

    @pytest.fixture(scope='class')
    def aap_client(self, aap_version):
        # Retrieve credentials based on AAP/AWX version
        fqdn = settings.AAP_INTEGRATION.get('AAP23_FQDN' if aap_version == '2.3' else 'AAP25_FQDN')
        client = awxkit.api.client.Connection(f'https://{fqdn}/')
        client.login(settings.AAP_INTEGRATION.USERNAME, settings.AAP_INTEGRATION.PASSWORD)

        yield client
        client.logout()

    @pytest.mark.parametrize('auth_type', ['admin', 'non-admin'])
    @pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
    def test_positive_ansible_dynamic_inventory(
        self,
        request,
        target_sat,
        module_org,
        module_location,
        module_ak_with_cv,
        aap_client,
        rhel_contenthost,
        auth_type,
        aap_version,
    ):
        """Verify AAP is able to pull a dynamic inventory of hosts from Satellite,
        with admin and non-admin user.

        :id: ad25aee5-4ea3-4743-a301-1c6271856g19

        :steps:
            1. Register content host to Satellite with admin and non-admin user
            2. Update Satellite type credentials in AAP
            3. Find Satellite inventory, inventory source and sync inventory source in AAP
            4. Verify registered hosts are added to Satellite inventory

        :expectedresults: All hosts managed by Satellite are added to Satellite inventory.

        :verifies: SAT-28613, SAT-30761

        :customerscenario: true
        """
        inventory_name = settings.AAP_INTEGRATION.satellite_inventory
        api_base = '/api/v2/' if aap_version == '2.3' else '/api/controller/v2/'

        password = settings.server.admin_password
        if auth_type == 'admin':
            login = gen_string('alpha')
            user = target_sat.api.User(
                admin=True,
                login=login,
                password=password,
                organization=[module_org],
                location=[module_location],
            ).create()
        else:
            login = gen_string('alpha')
            role = target_sat.api.Role(
                name=gen_string('alpha'), location=[module_location], organization=[module_org]
            ).create()
            for perm in ['view_hosts', 'view_hostgroups', 'view_facts']:
                permission = target_sat.api.Permission().search(query={'search': f'name={perm}'})
                target_sat.api.Filter(permission=permission, role=role).create()
            user = target_sat.api.User(
                role=[role],
                admin=False,
                login=login,
                password=password,
                organization=[module_org],
                location=[module_location],
            ).create()
            target_sat.cli.User.add_role(
                {'login': user.login, 'role': 'Ansible Tower Inventory Reader'}
            )
        result = rhel_contenthost.register(
            module_org,
            module_location,
            module_ak_with_cv.name,
            target_sat,
            auth_username=user.login,
            auth_password=password,
            force=True,
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        # Find the Satellite credentials in AAP and update it for target_sat.hostname and user credentials
        self.update_sat_credentials_in_aap(
            aap_client, target_sat, username=login, aap_version=aap_version
        )

        # Find the Satellite inventory in AAP and update it for target_sat and user credentials
        inv_list = aap_client.get(
            f'{api_base}inventories/', query_parameters=f'name={inventory_name}'
        ).json()
        inv_source_list = aap_client.get(
            f'{api_base}inventories/{inv_list["results"][0]["id"]}/inventory_sources/'
        ).json()
        sync_response = aap_client.post(
            f'{api_base}inventory_sources/{inv_source_list["results"][0]["id"]}/update/'
        )
        assert sync_response.ok
        wait_for(
            lambda: rhel_contenthost.hostname
            in [
                host['name']
                for host in aap_client.get(
                    f'{api_base}inventories/{inv_list["results"][0]["id"]}/hosts/?search={rhel_contenthost.hostname}'
                ).json()['results']
            ],
            timeout=180,
            delay=30,
        )
        # Find the hosts in Satellite inventory in AAP and verify if target_sat is listed in inventory
        hosts_list = aap_client.get(
            f'{api_base}inventories/{inv_list["results"][0]["id"]}/hosts/?search={rhel_contenthost.hostname}'
        ).json()
        assert rhel_contenthost.hostname in [host['name'] for host in hosts_list['results']]

    @pytest.mark.on_premises_provisioning
    @pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
    def test_positive_ansible_provisioning_callback(
        self,
        request,
        aap_client,
        aap_version,
        module_provisioning_sat,
        module_sca_manifest_org,
        module_location,
        provisioning_host,
        pxe_loader,
        module_provisioning_rhel_content,
        provisioning_hostgroup,
        module_lce_library,
        module_default_org_view,
    ):
        """Verify provisioning callback functionality which allows to run an Ansible playbook
        on the new RHEL provisioned host.

        :id: a272a594-f758-40ef-95ec-813245e44b66

        :steps:
            1. Configure Satellite for provisioning
            2. Update Satellite type credentials in AAP
            3. Create or update a hostgroup to add hostgroup parameters for provisioning callback
            4. Provision a RHEL hosts which must be added to Satellite inventory
            5. Find Satellite inventory, inventory source and sync inventory source in AAP
            6. Start ansible-callback systemd service, and Verify that job_template execution has begun in AAP

        :expectedresults:
            1. All hosts managed by Satellite are added to Satellite inventory.
            2. Starting ansible-callback systemd service, starts a job_template execution in AAP

        :verifies: SAT-30761

        :customerscenario: true
        """
        host_mac_addr = provisioning_host.provisioning_nic_mac_addr
        sat = module_provisioning_sat.sat
        aap_fqdn = settings.AAP_INTEGRATION.get(
            'AAP23_FQDN' if aap_version == '2.3' else 'AAP25_FQDN'
        )
        api_base = '/api/v2/' if aap_version == '2.3' else '/api/controller/v2/'
        aap_api_url = f'https://{aap_fqdn}{api_base}'
        job_template = settings.AAP_INTEGRATION.callback_job_template
        config_key = settings.AAP_INTEGRATION.host_config_key
        inventory_name = settings.AAP_INTEGRATION.satellite_inventory
        extra_vars_dict = '{"package_install": "tmux"}'

        # Find the Satellite credentials in AAP and update it for sat.hostname and user credentials
        self.update_sat_credentials_in_aap(aap_client, sat, aap_version=aap_version)

        # Find the Satellite inventory in AAP and update it for provisioning_sat and user credentials
        inv_list = aap_client.get(
            f'{api_base}inventories/', query_parameters=f'name={inventory_name}'
        ).json()
        inv_source_list = aap_client.get(
            f'{api_base}inventories/{inv_list["results"][0]["id"]}/inventory_sources/'
        ).json()

        # Find the provisioning callback job template id, which is required for provisioning
        jt_list = aap_client.get(
            f'{api_base}job_templates/', query_parameters=f"name={job_template}"
        ).json()
        template_id = jt_list['results'][0]['id']

        # Update the provisioning callback parameters in hostgroup
        existing_params = provisioning_hostgroup.group_parameters_attributes
        provisioning_hostgroup.group_parameters_attributes = [
            {'name': 'ansible_tower_provisioning', 'value': 'true', 'parameter_type': 'boolean'},
            {'name': 'ansible_tower_api_url', 'value': aap_api_url, 'parameter_type': 'string'},
            {'name': 'ansible_host_config_key', 'value': config_key, 'parameter_type': 'string'},
            {'name': 'ansible_job_template_id', 'value': template_id, 'parameter_type': 'integer'},
            {'name': 'ansible_extra_vars', 'value': extra_vars_dict, 'parameter_type': 'string'},
        ] + existing_params
        provisioning_hostgroup.update(['group_parameters_attributes'])

        hostname = gen_string('alpha').lower()
        host = sat.cli.Host.create(
            {
                'name': hostname,
                'organization': module_sca_manifest_org.name,
                'location': module_location.name,
                'hostgroup': provisioning_hostgroup.name,
                'mac': host_mac_addr,
                'provision-method': 'build',
            }
        )
        # teardown
        request.addfinalizer(lambda: sat.provisioning_cleanup(host['name'], interface='CLI'))

        hostname = f'{hostname}.{module_provisioning_sat.domain.name}'
        assert hostname == host['name']

        # Start the VM, do not ensure that we can connect to SSHD
        provisioning_host.power_control(ensure=False)

        # Host should do call back to the Satellite reporting
        # the result of the installation. Wait until Satellite reports that the host is installed.
        wait_for(
            lambda: sat.cli.Host.info({'name': hostname})['status']['build-status']
            != 'Pending installation',
            timeout=1800,
            delay=30,
        )
        host_info = sat.cli.Host.info({'id': host['id']})
        assert host_info['status']['build-status'] == 'Installed'
        host_os = sat.api.OperatingSystem(
            id=host_info['operating-system']['operating-system']['id']
        ).read()

        # In the current infra environment we don't support, addressing hosts using FQDNs, falling back to IP.
        # Change the hostname of the host as we know it already.
        provisioning_host.hostname = host_info['network']['ipv4-address']
        # Update host since it is not blank anymore
        provisioning_host.blank = False

        # Wait for the host to be rebooted and SSH daemon to be started.
        provisioning_host.wait_for_connection()

        if int(host_os.major) >= 9:
            assert (
                provisioning_host.execute(
                    'echo -e "\nPermitRootLogin yes" >> /etc/ssh/sshd_config; systemctl restart sshd'
                ).status
                == 0
            )

        # Sync the AAP inventory to add a provisioning host
        sync_response = aap_client.post(
            f'{api_base}inventory_sources/{inv_source_list["results"][0]["id"]}/update/'
        )
        assert sync_response.ok

        wait_for(
            lambda: hostname
            in [
                host['name']
                for host in aap_client.get(
                    f'{api_base}inventories/{inv_list["results"][0]["id"]}/hosts/?search={hostname}'
                ).json()['results']
            ],
            timeout=180,
            delay=30,
        )
        # Find the hosts in AAP inventory and verify if provisioning host is listed in inventory
        hosts_list = aap_client.get(
            f'{api_base}inventories/{inv_list["results"][0]["id"]}/hosts/?search={hostname}'
        ).json()
        assert hostname in [host['name'] for host in hosts_list['results']]
        assert provisioning_host.execute('systemctl start ansible-callback').status == 0
        jobs = aap_client.get(
            f'{api_base}job_templates/{template_id}/jobs/?launch_type=callback&order_by=-created'
        ).json()['results'][0]
        # when the callback service is started, the job sometimes starts with pending or waiting state before going to the running state
        filtered_job = jobs['id'] if jobs['status'] in ('running', 'pending', 'waiting') else None
        wait_for(
            lambda: aap_client.get(f'{api_base}jobs/?id={filtered_job}').json()['results'][0][
                'status'
            ]
            == 'successful',
            timeout=120,
        )
        # Verify user rocket and package tmux is installed via ansible-callback on provisioning host
        assert provisioning_host.execute('cat /etc/passwd | grep rocket').status == 0
        assert provisioning_host.execute('dnf list installed tmux').status == 0
