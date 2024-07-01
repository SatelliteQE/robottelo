"""Test class for Ansible Roles and Variables pages

:Requirement: Ansible

:CaseAutomation: Automated

:Team: Rocket

:CaseImportance: High
"""

from time import sleep

from fauxfactory import gen_string
import pytest

from robottelo.config import settings


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
    @pytest.mark.tier2
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


@pytest.mark.tier3
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
            repo=settings.repos.yum_3.url,
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

    @pytest.mark.rhel_ver_list([8])
    def test_positive_install_ansible_collection(self, rex_contenthost, target_sat):
        """Test whether Ansible collection can be installed via Ansible REX

        :id: ad25aee5-4ea3-4743-a301-1c6271856f79

        :steps:
            1. Upload a manifest.
            2. Register content host to Satellite with REX setup
            3. Enable Ansible repo on content host.
            4. Install ansible or ansible-core package
            5. Run REX job to install Ansible collection on content host.

        :expectedresults: Ansible collection can be installed on content host via REX.
        """
        client = rex_contenthost
        # Enable Ansible repository and Install ansible or ansible-core package
        client.create_custom_repos(rhel8_aps=settings.repos.rhel8_os.appstream)
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
