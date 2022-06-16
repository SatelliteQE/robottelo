"""Test class for Remote Execution Management UI

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime
from datetime import timedelta
from time import sleep

import pytest
from broker import VMBroker
from fauxfactory import gen_string
from nailgun import entities
from wait_for import wait_for

from robottelo.cli.factory import make_job_invocation
from robottelo.cli.factory import make_job_template
from robottelo.cli.globalparam import GlobalParameter
from robottelo.cli.host import Host
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.recurring_logic import RecurringLogic
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.task import Task
from robottelo.config import settings
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.hosts import ContentHost
from robottelo.logging import logger
from robottelo.utils.issue_handlers import is_open


@pytest.fixture()
def fixture_vmsetup(request, module_org, target_sat):
    """Create VM and register content host"""
    if '_count' in request.param.keys():
        with VMBroker(
            nick=request.param['nick'],
            host_classes={'host': ContentHost},
            _count=request.param['_count'],
        ) as clients:
            for client in clients:
                client.configure_rex(satellite=target_sat, org=module_org)
            yield clients
    else:
        with VMBroker(nick=request.param['nick'], host_classes={'host': ContentHost}) as client:
            client.configure_rex(satellite=target_sat, org=module_org)
            yield client


@pytest.fixture()
def fixture_sca_vmsetup(request, module_gt_manifest_org, target_sat):
    """Create VM and register content host to Simple Content Access organization"""
    if '_count' in request.param.keys():
        with VMBroker(
            nick=request.param['nick'],
            host_classes={'host': ContentHost},
            _count=request.param['_count'],
        ) as clients:
            for client in clients:
                client.configure_rex(satellite=target_sat, org=module_gt_manifest_org)
            yield clients
    else:
        with VMBroker(nick=request.param['nick'], host_classes={'host': ContentHost}) as client:
            client.configure_rex(satellite=target_sat, org=module_gt_manifest_org)
            yield client


class TestRemoteExecution:
    """Implements job execution tests in CLI."""

    @pytest.mark.tier3
    @pytest.mark.pit_client
    @pytest.mark.pit_server
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], ids=['rhel7'], indirect=True)
    def test_positive_run_default_job_template_by_ip(self, fixture_vmsetup):
        """Run default template on host connected by ip and list task

        :id: 811c7747-bec6-4a2d-8e5c-b5045d3fbc0d

        :expectedresults: Verify the job was successfully ran against the host
            and task can be listed by name and ID

        :BZ: 1647582

        :parametrized: yes
        """
        client = fixture_vmsetup
        command = "echo {}".format(gen_string('alpha'))
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - SSH Default',
                'inputs': f'command={command}',
                'search-query': f"name ~ {client.hostname}",
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)

        task = Task.list_tasks({"search": command})[0]
        search = Task.list_tasks({"search": 'id={}'.format(task["id"])})
        assert search[0]["action"] == task["action"]

    @pytest.mark.skip_if_open('BZ:1804685')
    @pytest.mark.tier3
    @pytest.mark.pit_client
    @pytest.mark.pit_server
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], ids=['rhel7'], indirect=True)
    def test_positive_run_job_effective_user_by_ip(self, fixture_vmsetup):
        """Run default job template as effective user on a host by ip

        :id: 0cd75cab-f699-47e6-94d3-4477d2a94bb7

        :BZ: 1451675

        :expectedresults: Verify the job was successfully run under the
            effective user identity on host

        :parametrized: yes
        """
        client = fixture_vmsetup
        # create a user on client via remote job
        username = gen_string('alpha')
        filename = gen_string('alpha')
        make_user_job = make_job_invocation(
            {
                'job-template': 'Run Command - SSH Default',
                'inputs': f"command='useradd -m {username}'",
                'search-query': f"name ~ {client.hostname}",
            }
        )
        result = JobInvocation.info({'id': make_user_job['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output({'id': make_user_job['id'], 'host': client.hostname})
                )
            )
            raise AssertionError(result)
        # create a file as new user
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - SSH Default',
                'inputs': f"command='touch /home/{username}/{filename}'",
                'search-query': f"name ~ {client.hostname}",
                'effective-user': f'{username}',
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)
        # check the file owner
        result = client.execute(
            f'''stat -c '%U' /home/{username}/{filename}''',
        )
        # assert the file is owned by the effective user
        assert username == result.stdout.strip('\n')

    nick_params = [{'nick': 'rhel7'}, {'nick': 'rhel7_fips'}, {'nick': 'rhel8'}]
    if not is_open('BZ:1811166'):
        nick_params.append({'nick': 'rhel8_fips'})

    @pytest.mark.tier3
    @pytest.mark.rhel_ver_list([7, '7_fips', 8, '8_fips', 9, '9_fips'])
    def test_positive_run_custom_job_template_by_ip(self, rex_contenthost, module_org, target_sat):
        """Run custom template on host connected by ip

        :id: 9740eb1d-59f5-42b2-b3ab-659ca0202c74

        :expectedresults: Verify the job was successfully ran against the host

        :bz: 1872688, 1811166

        :CaseImportance: Critical

        :parametrized: yes
        """
        self.org = module_org
        template_file = 'template_file.txt'
        target_sat.execute(f'echo "echo Enforcing" > {template_file}')
        template_name = gen_string('alpha', 7)
        make_job_template(
            {'organizations': self.org.name, 'name': template_name, 'file': template_file}
        )
        invocation_command = make_job_invocation(
            {'job-template': template_name, 'search-query': f"name ~ {rex_contenthost.hostname}"}
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': rex_contenthost.hostname}
                    )
                )
            )
            raise AssertionError(result)

    @pytest.mark.destructive
    @pytest.mark.rhel_ver_list([7])
    def test_positive_use_alternate_directory(self, rex_contenthost, target_sat):
        """Use alternate working directory on client to execute rex jobs

        :id: a0181f18-d3dc-4bd9-a2a6-430c2a49809e

        :expectedresults: Verify the job was successfully ran against the host

        :customerscenario: true

        :parametrized: yes
        """
        client = rex_contenthost
        testdir = gen_string('alpha')
        result = client.run(f'mkdir /{testdir}')
        assert result.status == 0
        result = client.run(f'chcon --reference=/var /{testdir}')
        assert result.status == 0
        result = target_sat.execute(
            f"sed -i r's/^:remote_working_dir:.*/:remote_working_dir: \\/{testdir}/' \
            /etc/foreman-proxy/settings.d/remote_execution_ssh.yml",
        )
        assert result.status == 0
        result = target_sat.execute('systemctl restart foreman-proxy')
        assert result.status == 0

        command = f'echo {gen_string("alpha")}'
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - SSH Default',
                'inputs': f'command={command}',
                'search-query': f"name ~ {client.hostname}",
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            output = ' '.join(
                JobInvocation.get_output({'id': invocation_command['id'], 'host': client.hostname})
            )
            result = f'host output: {output}'
            raise AssertionError(result)

        task = Task.list_tasks({"search": command})[0]
        search = Task.list_tasks({"search": f'id={task["id"]}'})
        assert search[0]["action"] == task["action"]

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'fixture_vmsetup', [{'nick': 'rhel7', '_count': 2}], ids=['rhel7'], indirect=True
    )
    def test_positive_run_default_job_template_multiple_hosts_by_ip(
        self, fixture_vmsetup, module_org
    ):
        """Run default job template against multiple hosts by ip

        :id: 694a21d3-243b-4296-8bd0-4bad9663af15

        :expectedresults: Verify the job was successfully ran against all hosts

        :parametrized: yes
        """
        clients = fixture_vmsetup
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - SSH Default',
                'inputs': 'command="ls"',
                'search-query': f'name ~ {clients[0].hostname} or name ~ {clients[1].hostname}',
            }
        )
        # collect output messages from clients
        output_msgs = []
        for vm in clients:
            output_msgs.append(
                'host output from {}: {}'.format(
                    vm.hostname,
                    ' '.join(
                        JobInvocation.get_output(
                            {'id': invocation_command['id'], 'host': vm.hostname}
                        )
                    ),
                )
            )
        result = JobInvocation.info({'id': invocation_command['id']})
        assert result['success'] == '2', output_msgs

    @pytest.mark.tier3
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], ids=['rhel7'], indirect=True)
    @pytest.mark.skipif(
        (not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url'
    )
    def test_positive_install_multiple_packages_with_a_job_by_ip(self, fixture_vmsetup, module_org):
        """Run job to install several packages on host by ip

        :id: 8b73033f-83c9-4024-83c3-5e442a79d320

        :expectedresults: Verify the packages were successfully installed
            on host

        :parametrized: yes
        """
        self.org = module_org
        client = fixture_vmsetup
        packages = ['monkey', 'panda', 'seal']
        # Create a custom repo
        repo = entities.Repository(
            content_type='yum',
            product=entities.Product(organization=self.org).create(),
            url=settings.repos.yum_3.url,
        ).create()
        repo.sync()
        prod = repo.product.read()
        subs = entities.Subscription(organization=self.org).search(
            query={'search': f'name={prod.name}'}
        )
        assert len(subs) > 0, 'No subscriptions matching the product returned'

        ak = entities.ActivationKey(
            organization=self.org,
            content_view=self.org.default_content_view,
            environment=self.org.library,
        ).create()
        ak.add_subscriptions(data={'subscriptions': [{'id': subs[0].id}]})
        client.register_contenthost(org=self.org.label, activation_key=ak.name)

        invocation_command = make_job_invocation(
            {
                'job-template': 'Install Package - Katello SSH Default',
                'inputs': 'package={} {} {}'.format(*packages),
                'search-query': f'name ~ {client.hostname}',
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)
        result = client.run(f'rpm -q {" ".join(packages)}')
        assert result.status == 0

    @pytest.mark.tier3
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], ids=['rhel7'], indirect=True)
    def test_positive_run_recurring_job_with_max_iterations_by_ip(self, fixture_vmsetup):
        """Run default job template multiple times with max iteration by ip

        :id: 0a3d1627-95d9-42ab-9478-a908f2a7c509

        :expectedresults: Verify the job was run not more than the specified
            number of times.

        :parametrized: yes
        """
        client = fixture_vmsetup
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - SSH Default',
                'inputs': 'command="ls"',
                'search-query': f"name ~ {client.hostname}",
                'cron-line': '* * * * *',  # every minute
                'max-iteration': 2,  # just two runs
            }
        )

        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['status'] == 'queued'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)

        sleep(150)
        rec_logic = RecurringLogic.info({'id': result['recurring-logic-id']})
        assert rec_logic['state'] == 'finished'
        assert rec_logic['iteration'] == '2'

    @pytest.mark.tier3
    @pytest.mark.rhel_ver_list([7])
    def test_positive_run_scheduled_job_template_by_ip(self, rex_contenthost, target_sat):
        """Schedule a job to be ran against a host

        :id: 0407e3de-ef59-4706-ae0d-b81172b81e5c

        :expectedresults: Verify the job was successfully ran after the
            designated time

        :parametrized: yes
        """
        client = rex_contenthost
        system_current_time = target_sat.execute('date --utc +"%b %d %Y %I:%M%p"').stdout
        current_time_object = datetime.strptime(system_current_time.strip('\n'), '%b %d %Y %I:%M%p')
        plan_time = (current_time_object + timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M")
        Host.set_parameter(
            {
                'host': client.hostname,
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
                'parameter-type': 'boolean',
            }
        )
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - SSH Default',
                'inputs': 'command="ls"',
                'start-at': plan_time,
                'search-query': f"name ~ {client.hostname}",
            }
        )
        # Wait until the job runs
        pending_state = '1'
        while pending_state != '0':
            invocation_info = JobInvocation.info({'id': invocation_command['id']})
            pending_state = invocation_info['pending']
            sleep(30)
        invocation_info = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert invocation_info['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)

    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_run_receptor_installer(self, target_sat, subscribe_satellite):
        """Run Receptor installer ("Configure Cloud Connector")

        :CaseComponent: RHCloud-CloudConnector

        :Assignee: lhellebr

        :id: 811c7747-bec6-1a2d-8e5c-b5045d3fbc0d

        :expectedresults: The job passes, installs Receptor that peers with c.r.c

        :BZ: 1818076
        """
        result = target_sat.execute('stat /etc/receptor/*/receptor.conf')
        if result.status == 0:
            pytest.skip(
                'Cloud Connector has already been configured on this system. '
                'It is possible to reconfigure it but then the test would not really '
                'check if everything is correctly configured from scratch. Skipping.'
            )
        # Copy foreman-proxy user's key to root@localhost user's authorized_keys
        target_sat.add_rex_key(satellite=target_sat)

        # Set Host parameter source_display_name to something random.
        # To avoid 'name has already been taken' error when run multiple times
        # on a machine with the same hostname.
        host_id = Host.info({'name': target_sat.hostname})['id']
        Host.set_parameter(
            {'host-id': host_id, 'name': 'source_display_name', 'value': gen_string('alpha')}
        )

        template_name = 'Configure Cloud Connector'
        invocation = make_job_invocation(
            {
                'async': True,
                'job-template': template_name,
                'inputs': f'satellite_user="{settings.server.admin_username}",\
                        satellite_password="{settings.server.admin_password}"',
                'search-query': f'name ~ {target_sat.hostname}',
            }
        )
        invocation_id = invocation['id']
        wait_for(
            lambda: entities.JobInvocation(id=invocation_id).read().status_label
            in ["succeeded", "failed"],
            timeout="1500s",
        )

        result = JobInvocation.get_output({'id': invocation_id, 'host': target_sat.hostname})
        logger.debug(f'Invocation output>>\n{result}\n<<End of invocation output')
        # if installation fails, it's often due to missing rhscl repo -> print enabled repos
        repolist = target_sat.execute('yum repolist')
        logger.debug(f'Repolist>>\n{repolist}\n<<End of repolist')

        assert entities.JobInvocation(id=invocation_id).read().status == 0
        assert 'project-receptor.satellite_receptor_installer' in result
        assert 'Exit status: 0' in result
        # check that there is one receptor conf file and it's only readable
        # by the receptor user and root
        result = target_sat.execute('stat /etc/receptor/*/receptor.conf --format "%a:%U"')
        assert all(
            filestats == '400:foreman-proxy' for filestats in result.stdout.strip().split('\n')
        )
        result = target_sat.execute('ls -l /etc/receptor/*/receptor.conf | wc -l')
        assert int(result.stdout.strip()) >= 1


class TestAnsibleREX:
    """Test class for remote execution via Ansible"""

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.pit_client
    @pytest.mark.pit_server
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], ids=['rhel7'], indirect=True)
    def test_positive_run_effective_user_job(self, fixture_vmsetup):
        """Tests Ansible REX job having effective user runs successfully

        :id: a5fa20d8-c2bd-4bbf-a6dc-bf307b59dd8c

        :Steps:

            0. Create a VM and register to SAT and prepare for REX (ssh key)

            1. Run Ansible Command job for the host to create a user

            2. Run Ansible Command job using effective user

            3. Check the job result at the host is done under that user

        :expectedresults: multiple asserts along the code

        :CaseAutomation: Automated

        :CaseLevel: System

        :parametrized: yes
        """
        client = fixture_vmsetup
        # create a user on client via remote job
        username = gen_string('alpha')
        filename = gen_string('alpha')
        make_user_job = make_job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': f"command='useradd -m {username}'",
                'search-query': f"name ~ {client.hostname}",
            }
        )
        result = JobInvocation.info({'id': make_user_job['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output({'id': make_user_job['id'], 'host': client.hostname})
                )
            )
            raise AssertionError(result)
        # create a file as new user
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': f"command='touch /home/{username}/{filename}'",
                'search-query': f"name ~ {client.hostname}",
                'effective-user': f'{username}',
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)
        # check the file owner
        result = client.execute(
            f'''stat -c '%U' /home/{username}/{filename}''',
        )
        # assert the file is owned by the effective user
        assert username == result.stdout.strip('\n'), "file ownership mismatch"

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], ids=['rhel7'], indirect=True)
    def test_positive_run_reccuring_job(self, fixture_vmsetup):
        """Tests Ansible REX reccuring job runs successfully multiple times

        :id: 49b0d31d-58f9-47f1-aa5d-561a1dcb0d66

        :Steps:

            0. Create a VM and register to SAT and prepare for REX (ssh key)

            1. Run recurring Ansible Command job for the host

            2. Check the multiple job results at the host

        :expectedresults: multiple asserts along the code

        :CaseAutomation: Automated

        :CaseLevel: System

        :parametrized: yes
        """
        client = fixture_vmsetup
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': 'command="ls"',
                'search-query': f"name ~ {client.hostname}",
                'cron-line': '* * * * *',  # every minute
                'max-iteration': 2,  # just two runs
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['status'] == 'queued'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)
        sleep(150)
        rec_logic = RecurringLogic.info({'id': result['recurring-logic-id']})
        assert rec_logic['state'] == 'finished'
        assert rec_logic['iteration'] == '2'

    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'fixture_vmsetup', [{'nick': 'rhel7', '_count': 2}], ids=['rhel7'], indirect=True
    )
    def test_positive_run_concurrent_jobs(self, fixture_vmsetup, module_org):
        """Tests Ansible REX concurent jobs without batch trigger

        :id: ad0f108c-03f2-49c7-8732-b1056570567b

        :Steps:

            0. Create 2 hosts, disable foreman_tasks_proxy_batch_trigger

            1. Run Ansible Command job with concurrency-setting

        :expectedresults: multiple asserts along the code

        :CaseAutomation: Automated

        :customerscenario: true

        :CaseLevel: System

        :BZ: 1817320

        :parametrized: yes
        """
        param_name = 'foreman_tasks_proxy_batch_trigger'
        GlobalParameter().set({'name': param_name, 'value': 'false'})
        clients = fixture_vmsetup
        output_msgs = []
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': 'command="ls"',
                'search-query': f'name ~ {clients[0].hostname} or name ~ {clients[1].hostname}',
                'concurrency-level': 2,
            }
        )
        for vm in clients:
            output_msgs.append(
                'host output from {}: {}'.format(
                    vm.hostname,
                    ' '.join(
                        JobInvocation.get_output(
                            {'id': invocation_command['id'], 'host': vm.hostname}
                        )
                    ),
                )
            )
        result = JobInvocation.info({'id': invocation_command['id']})
        assert result['success'] == '2', output_msgs
        GlobalParameter().delete({'name': param_name})
        assert len(GlobalParameter().list({'search': param_name})) == 0

    nick_params = [{'nick': 'rhel7'}, {'nick': 'rhel7_fips'}, {'nick': 'rhel8'}]
    if not is_open('BZ:1811166'):
        nick_params.append({'nick': 'rhel8_fips'})

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.pit_server
    @pytest.mark.parametrize(
        'fixture_vmsetup',
        nick_params,
        ids=[n['nick'] for n in nick_params],
        indirect=True,
    )
    @pytest.mark.skipif(
        (not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url'
    )
    def test_positive_run_packages_and_services_job(self, fixture_vmsetup, module_org):
        """Tests Ansible REX job can install packages and start services

        :id: 47ed82fb-77ca-43d6-a52e-f62bae5d3a42

        :Steps:

            0. Create a VM and register to SAT and prepare for REX (ssh key)

            1. Run Ansible Package job for the host to install a package

            2. Check the package is present at the host

            3. Run Ansible Service job for the host to start a service

            4. Check the service is started on the host

        :expectedresults: multiple asserts along the code

        :CaseAutomation: Automated

        :CaseLevel: System

        :bz: 1872688, 1811166

        :CaseImportance: Critical

        :customerscenario: true

        :parametrized: yes
        """
        self.org = module_org
        client = fixture_vmsetup
        packages = ['tapir']
        # Create a custom repo
        repo = entities.Repository(
            content_type='yum',
            product=entities.Product(organization=self.org).create(),
            url=settings.repos.yum_3.url,
        ).create()
        repo.sync()
        prod = repo.product.read()
        subs = entities.Subscription(organization=self.org).search(
            query={'search': f'name={prod.name}'}
        )
        assert len(subs), 'No subscriptions matching the product returned'
        ak = entities.ActivationKey(
            organization=self.org,
            content_view=self.org.default_content_view,
            environment=self.org.library,
        ).create()
        ak.add_subscriptions(data={'subscriptions': [{'id': subs[0].id}]})
        client.register_contenthost(org=self.org.label, activation_key=ak.name)

        # install package
        invocation_command = make_job_invocation(
            {
                'job-template': 'Package Action - Ansible Default',
                'inputs': 'state=latest, name={}'.format(*packages),
                'search-query': f'name ~ {client.hostname}',
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)
        result = client.run(f'rpm -q {" ".join(packages)}')
        assert result.status == 0

        # stop a service
        service = "rsyslog"
        invocation_command = make_job_invocation(
            {
                'job-template': 'Service Action - Ansible Default',
                'inputs': f'state=stopped, name={service}',
                'search-query': f"name ~ {client.hostname}",
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)
        result = client.execute(f"systemctl status {service}")
        assert result.status == 3

        # start it again
        invocation_command = make_job_invocation(
            {
                'job-template': 'Service Action - Ansible Default',
                'inputs': f'state=started, name={service}',
                'search-query': f"name ~ {client.hostname}",
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        try:
            assert result['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)
        result = client.execute(f"systemctl status {service}")
        assert result.status == 0

    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'fixture_sca_vmsetup', [{'nick': 'rhel7'}], ids=['rhel7'], indirect=True
    )
    def test_positive_install_ansible_collection(self, fixture_sca_vmsetup, module_gt_manifest_org):
        """Test whether Ansible collection can be installed via REX

        :Steps:

            1. Upload a manifest.
            2. Enable and sync Ansible repository.
            3. Register content host to Satellite.
            4. Enable Ansible repo on content host.
            5. Install ansible package.
            6. Run REX job to install Ansible collection on content host.

        :id: ad25aee5-4ea3-4743-a301-1c6271856f79

        :CaseComponent: Ansible

        :Assignee: dsynk
        """

        # Configure repository to prepare for installing ansible on host
        RepositorySet.enable(
            {
                'basearch': 'x86_64',
                'name': REPOSET['rhae2'],
                'organization-id': module_gt_manifest_org.id,
                'product': PRDS['rhae'],
                'releasever': '7Server',
            }
        )
        Repository.synchronize(
            {
                'name': REPOS['rhae2']['name'],
                'organization-id': module_gt_manifest_org.id,
                'product': PRDS['rhae'],
            }
        )
        client = fixture_sca_vmsetup
        client.execute(f'subscription-manager repos --enable {REPOS["rhae2"]["id"]}')
        client.execute('yum -y install ansible')
        collection_job = make_job_invocation(
            {
                'job-template': 'Ansible Collection - Install from Galaxy',
                'inputs': 'ansible_collections_list="oasis_roles.system"',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        result = JobInvocation.info({'id': collection_job['id']})
        assert result['success'] == '1'
        collection_path = str(client.execute('ls /etc/ansible/collections/ansible_collections'))
        assert 'oasis' in collection_path
