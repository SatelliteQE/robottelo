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

from robottelo import ssh
from robottelo.cli.factory import make_job_invocation
from robottelo.cli.factory import make_job_template
from robottelo.cli.globalparam import GlobalParameter
from robottelo.cli.host import Host
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.recurring_logic import RecurringLogic
from robottelo.cli.task import Task
from robottelo.config import settings
from robottelo.constants.repos import FAKE_0_YUM_REPO
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.hosts import ContentHost


@pytest.fixture()
def fixture_vmsetup(request, module_org):
    """ Create VM and register content host """
    if '_count' in request.param.keys():
        with VMBroker(
            nick=request.param['nick'],
            host_classes={'host': ContentHost},
            _count=request.param['_count'],
        ) as clients:
            for client in clients:
                _setup_host(client, module_org.label)
            yield clients
    else:
        with VMBroker(nick=request.param['nick'], host_classes={'host': ContentHost}) as client:
            _setup_host(client, module_org.label)
            yield client


def _setup_host(client, org_label):
    """Set up host for remote execution"""
    client.install_katello_ca()
    client.register_contenthost(org=org_label, lce='Library')
    assert client.subscribed
    add_remote_execution_ssh_key(client.ip_addr)
    Host.set_parameter(
        {
            'host': client.hostname,
            'name': 'remote_execution_connect_by_ip',
            'value': 'True',
        }
    )


class TestRemoteExecution:
    """Implements job execution tests in CLI."""

    @pytest.mark.tier3
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], indirect=True)
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

        try:
            assert invocation_command['success'] == '1'
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
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], indirect=True)
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
        try:
            assert make_user_job['success'] == '1'
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
        try:
            assert invocation_command['success'] == '1'
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
        result = ssh.command(
            f'''stat -c '%U' /home/{username}/{filename}''',
            hostname=client.ip_addr,
        )
        # assert the file is owned by the effective user
        assert username == result.stdout[0]

    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'fixture_vmsetup',
        [{'nick': 'rhel7'}, {'nick': 'rhel7_fips'}],
        ids=['rhel7', 'rhel7_fips'],
        indirect=True,
    )
    def test_positive_run_custom_job_template_by_ip(self, fixture_vmsetup, module_org):
        """Run custom template on host connected by ip

        :id: 9740eb1d-59f5-42b2-b3ab-659ca0202c74

        :expectedresults: Verify the job was successfully ran against the host

        :parametrized: yes
        """
        self.org = module_org
        client = fixture_vmsetup
        template_file = 'template_file.txt'
        ssh.command(f'echo "echo Enforcing" > {template_file}')
        template_name = gen_string('alpha', 7)
        make_job_template(
            {'organizations': self.org.name, 'name': template_name, 'file': template_file}
        )
        invocation_command = make_job_invocation(
            {'job-template': template_name, 'search-query': f"name ~ {client.hostname}"}
        )
        try:
            assert invocation_command['success'] == '1'
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
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7', '_count': 2}], indirect=True)
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
        assert invocation_command['success'] == '2', output_msgs

    @pytest.mark.tier3
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], indirect=True)
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
    def test_positive_install_multiple_packages_with_a_job_by_ip(self, fixture_vmsetup, module_org):
        """Run job to install several packages on host by ip

        :id: 8b73033f-83c9-4024-83c3-5e442a79d320

        :expectedresults: Verify the packages were successfully installed
            on host

        :parametrized: yes
        """
        self.org = module_org
        client = fixture_vmsetup
        packages = ["cow", "dog", "lion"]
        # Create a custom repo
        repo = entities.Repository(
            content_type='yum',
            product=entities.Product(organization=self.org).create(),
            url=FAKE_0_YUM_REPO,
        ).create()
        repo.sync()
        prod = repo.product.read()
        subs = entities.Subscription().search(query={'search': f'name={prod.name}'})
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
        try:
            assert invocation_command['success'] == '1'
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
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], indirect=True)
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

        JobInvocation.get_output({'id': invocation_command['id'], 'host': client.hostname})
        try:
            assert invocation_command['status'] == 'queued'
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
        rec_logic = RecurringLogic.info({'id': invocation_command['recurring-logic-id']})
        assert rec_logic['state'] == 'finished'
        assert rec_logic['iteration'] == '2'

    @pytest.mark.tier3
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], indirect=True)
    def test_positive_run_scheduled_job_template_by_ip(self, fixture_vmsetup):
        """Schedule a job to be ran against a host

        :id: 0407e3de-ef59-4706-ae0d-b81172b81e5c

        :expectedresults: Verify the job was successfully ran after the
            designated time

        :parametrized: yes
        """
        client = fixture_vmsetup
        system_current_time = ssh.command('date --utc +"%b %d %Y %I:%M%p"').stdout[0]
        current_time_object = datetime.strptime(system_current_time, '%b %d %Y %I:%M%p')
        plan_time = (current_time_object + timedelta(seconds=30)).strftime("%Y-%m-%d %H:%M")
        Host.set_parameter(
            {
                'host': client.hostname,
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
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
    def test_positive_run_receptor_installer(self):
        """Run Receptor installer ("Configure Cloud Connector")

        :CaseComponent: RHCloud-CloudConnector

        :Assignee: lhellebr

        :id: 811c7747-bec6-1a2d-8e5c-b5045d3fbc0d

        :expectedresults: The job passes, installs Receptor that peers with c.r.c

        :BZ: 1818076
        """
        # Set Host parameter source_display_name to something random.
        # To avoid 'name has already been taken' error when run multiple times
        # on a machine with the same hostname.
        host_id = Host.info({'name': settings.server.hostname})['id']
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
                'search-query': f'name ~ {settings.server.hostname}',
            }
        )
        invocation_id = invocation['id']

        wait_for(
            lambda: entities.JobInvocation(id=invocation_id).read().status_label
            in ["succeeded", "failed"],
            timeout="1500s",
        )
        assert entities.JobInvocation(id=invocation_id).read().status == 0

        result = ' '.join(
            JobInvocation.get_output({'id': invocation_id, 'host': settings.server.hostname})
        )
        assert 'project-receptor.satellite_receptor_installer' in result
        assert 'Exit status: 0' in result
        # check that there is one receptor conf file and it's only readable
        # by the receptor user and root
        result = ssh.command('stat /etc/receptor/*/receptor.conf --format "%a:%U"')
        assert result.stdout[0] == '400:foreman-proxy'
        result = ssh.command('ls -l /etc/receptor/*/receptor.conf | wc -l')
        assert result.stdout[0] == '1'


class TestAnsibleREX:
    """Test class for remote execution via Ansible"""

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], indirect=True)
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
        try:
            assert make_user_job['success'] == '1'
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
        try:
            assert invocation_command['success'] == '1'
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
        result = ssh.command(
            f'''stat -c '%U' /home/{username}/{filename}''',
            hostname=client.ip_addr,
        )
        # assert the file is owned by the effective user
        assert username == result.stdout[0], "file ownership mismatch"

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7'}], indirect=True)
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
        JobInvocation.get_output({'id': invocation_command['id'], 'host': client.hostname})
        try:
            assert invocation_command['status'] == 'queued'
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
        rec_logic = RecurringLogic.info({'id': invocation_command['recurring-logic-id']})
        assert rec_logic['state'] == 'finished'
        assert rec_logic['iteration'] == '2'

    @pytest.mark.tier3
    @pytest.mark.parametrize('fixture_vmsetup', [{'nick': 'rhel7', '_count': 2}], indirect=True)
    def test_positive_run_concurrent_jobs(self, fixture_vmsetup, module_org):
        """Tests Ansible REX concurent jobs without batch trigger

        :id: ad0f108c-03f2-49c7-8732-b1056570567b

        :Steps:

            0. Create 2 hosts, disable foreman_tasks_proxy_batch_trigger

            1. Run Ansible Command job with concurrency-setting

        :expectedresults: multiple asserts along the code

        :CaseAutomation: Automated

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
        assert invocation_command['success'] == '2', output_msgs
        GlobalParameter().delete({'name': param_name})
        assert len(GlobalParameter().list({'search': param_name})) == 0

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'fixture_vmsetup',
        [{'nick': 'rhel7'}, {'nick': 'rhel7_fips'}],
        ids=['rhel7', 'rhel7_fips'],
        indirect=True,
    )
    @pytest.mark.skipif((not settings.repos_hosting_url), reason='Missing repos_hosting_url')
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

        :parametrized: yes
        """
        self.org = module_org
        client = fixture_vmsetup
        packages = ["cow"]
        # Create a custom repo
        repo = entities.Repository(
            content_type='yum',
            product=entities.Product(organization=self.org).create(),
            url=FAKE_0_YUM_REPO,
        ).create()
        repo.sync()
        prod = repo.product.read()
        subs = entities.Subscription().search(query={'search': f'name={prod.name}'})
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
        try:
            assert invocation_command['success'] == '1'
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

        # start a service
        service = "postfix"
        ssh.command(
            "sed -i 's/^inet_protocols.*/inet_protocols = ipv4/' /etc/postfix/main.cf",
            hostname=client.ip_addr,
        )
        invocation_command = make_job_invocation(
            {
                'job-template': 'Service Action - Ansible Default',
                'inputs': f'state=started, name={service}',
                'search-query': f"name ~ {client.hostname}",
            }
        )
        try:
            assert invocation_command['success'] == '1'
        except AssertionError:
            result = 'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output(
                        {'id': invocation_command['id'], 'host': client.hostname}
                    )
                )
            )
            raise AssertionError(result)
        result = ssh.command(f"systemctl status {service}", hostname=client.ip_addr)
        assert result.return_code == 0
