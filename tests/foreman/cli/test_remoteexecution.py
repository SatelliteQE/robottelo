"""Test class for Remote Execution Management UI

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Team: Endeavour

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from calendar import monthrange
from datetime import datetime, timedelta
import random
from time import sleep

from broker import Broker
from dateutil.relativedelta import FR, relativedelta
from fauxfactory import gen_string
import pytest

from robottelo import constants
from robottelo.cli.factory import (
    make_filter,
    make_job_invocation,
    make_job_invocation_with_credentials,
    make_job_template,
    make_role,
    make_user,
)
from robottelo.cli.filter import Filter
from robottelo.cli.globalparam import GlobalParameter
from robottelo.cli.host import Host
from robottelo.cli.job_invocation import JobInvocation
from robottelo.cli.recurring_logic import RecurringLogic
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.task import Task
from robottelo.cli.user import User
from robottelo.config import settings
from robottelo.constants import PRDS, REPOS, REPOSET
from robottelo.hosts import ContentHost
from robottelo.utils import ohsnap
from robottelo.utils.datafactory import filtered_datapoint, parametrized


@filtered_datapoint
def valid_feature_names():
    """Returns a list of valid features and their descriptions"""
    return [
        {'label': 'katello_package_install', 'jt_name': 'Install Package - Katello Script Default'},
        {'label': 'katello_package_update', 'jt_name': 'Update Package - Katello Script Default'},
        {'label': 'katello_package_remove', 'jt_name': 'Remove Package - Katello Script Default'},
        {'label': 'katello_group_install', 'jt_name': 'Install Group - Katello Script Default'},
        {'label': 'katello_group_update', 'jt_name': 'Update Group - Katello Script Default'},
        {'label': 'katello_group_remove', 'jt_name': 'Remove Group - Katello Script Default'},
        {'label': 'katello_errata_install', 'jt_name': 'Install Errata - Katello Script Default'},
    ]


@pytest.fixture
def fixture_sca_vmsetup(request, module_sca_manifest_org, target_sat):
    """Create VM and register content host to Simple Content Access organization"""
    if '_count' in request.param.keys():
        with Broker(
            nick=request.param['nick'],
            host_class=ContentHost,
            _count=request.param['_count'],
        ) as clients:
            for client in clients:
                client.configure_rex(satellite=target_sat, org=module_sca_manifest_org)
            yield clients
    else:
        with Broker(nick=request.param['nick'], host_class=ContentHost) as client:
            client.configure_rex(satellite=target_sat, org=module_sca_manifest_org)
            yield client


@pytest.fixture
def infra_host(request, target_sat, module_capsule_configured):
    infra_hosts = {'target_sat': target_sat, 'module_capsule_configured': module_capsule_configured}
    return infra_hosts[request.param]


def assert_job_invocation_result(invocation_command_id, client_hostname, expected_result='success'):
    """Asserts the job invocation finished with the expected result and fetches job output
    when error occurs. Result is one of: success, pending, error, warning"""
    result = JobInvocation.info({'id': invocation_command_id})
    try:
        assert result[expected_result] == '1'
    except AssertionError:
        raise AssertionError(
            'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output({'id': invocation_command_id, 'host': client_hostname})
                )
            )
        )


def assert_job_invocation_status(invocation_command_id, client_hostname, status):
    """Asserts the job invocation status and fetches job output when error occurs.
    Status is one of: queued, stopped, running, paused"""
    result = JobInvocation.info({'id': invocation_command_id})
    try:
        assert result['status'] == status
    except AssertionError:
        raise AssertionError(
            'host output: {}'.format(
                ' '.join(
                    JobInvocation.get_output({'id': invocation_command_id, 'host': client_hostname})
                )
            )
        )


class TestRemoteExecution:
    """Implements job execution tests in CLI."""

    @pytest.mark.tier3
    @pytest.mark.pit_client
    @pytest.mark.pit_server
    @pytest.mark.rhel_ver_list([8])
    def test_positive_run_default_job_template(self, module_org, rex_contenthost):
        """Run default template on host connected and list task

        :id: 811c7747-bec6-4a2d-8e5c-b5045d3fbc0d

        :expectedresults: Verify the job was successfully ran against the host
            and task can be listed by name and ID

        :BZ: 1647582, 1896628

        :customerscenario: true

        :parametrized: yes
        """
        client = rex_contenthost
        command = f'echo {gen_string("alpha")}'
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': f'command={command}',
                'search-query': f"name ~ {client.hostname}",
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        task = Task.list_tasks({'search': command})[0]
        search = Task.list_tasks({'search': f'id={task["id"]}'})
        assert search[0]['action'] == task['action']
        out = JobInvocation.get_output(
            {
                'id': invocation_command['id'],
                'host': client.hostname,
                'organization-id': module_org.id,
            }
        )
        assert 'Exit' in out
        assert 'Internal Server Error' not in out

    @pytest.mark.tier3
    @pytest.mark.pit_client
    @pytest.mark.pit_server
    @pytest.mark.rhel_ver_list([7, 8, 9])
    def test_positive_run_job_effective_user(self, rex_contenthost):
        """Run default job template as effective user on a host

        :id: 0cd75cab-f699-47e6-94d3-4477d2a94bb7

        :BZ: 1451675, 1804685

        :expectedresults: Verify the job was successfully run under the
            effective user identity on host

        :parametrized: yes
        """
        client = rex_contenthost
        # create a user on client via remote job
        username = gen_string('alpha')
        filename = gen_string('alpha')
        make_user_job = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': f"command=useradd -m {username}",
                'search-query': f"name ~ {client.hostname}",
            }
        )
        assert_job_invocation_result(make_user_job['id'], client.hostname)
        # create a file as new user
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': f"command=touch /home/{username}/{filename}",
                'search-query': f"name ~ {client.hostname}",
                'effective-user': f'{username}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        # check the file owner
        result = client.execute(
            f'''stat -c '%U' /home/{username}/{filename}''',
        )
        # assert the file is owned by the effective user
        assert username == result.stdout.strip('\n')

    @pytest.mark.tier3
    @pytest.mark.e2e
    @pytest.mark.rhel_ver_match('[^6].*')
    def test_positive_run_custom_job_template(self, rex_contenthost, module_org, target_sat):
        """Run custom template on host connected

        :id: 9740eb1d-59f5-42b2-b3ab-659ca0202c74

        :expectedresults: Verify the job was successfully ran against the host

        :bz: 1872688, 1811166

        :customerscenario: true

        :CaseImportance: Critical

        :parametrized: yes
        """
        self.org = module_org
        client = rex_contenthost
        template_file = 'template_file.txt'
        target_sat.execute(f'echo "echo Enforcing" > {template_file}')
        template_name = gen_string('alpha', 7)
        make_job_template(
            {'organizations': self.org.name, 'name': template_name, 'file': template_file}
        )
        invocation_command = make_job_invocation(
            {'job-template': template_name, 'search-query': f'name ~ {client.hostname}'}
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([8])
    def test_positive_run_default_job_template_multiple_hosts(self, registered_hosts, module_org):
        """Run default job template against multiple hosts

        :id: 694a21d3-243b-4296-8bd0-4bad9663af15

        :expectedresults: Verify the job was successfully ran against all hosts

        :parametrized: yes
        """
        clients = registered_hosts
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': 'command=ls',
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
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([8])
    @pytest.mark.skipif(
        (not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url'
    )
    def test_positive_install_remove_multiple_packages_with_a_job(
        self, rhel_contenthost, module_org, module_ak_with_cv, target_sat
    ):
        """Run job to install and remove several packages on host

        :id: 8b73033f-83c9-4024-83c3-5e442a79d320

        :expectedresults: Verify the packages were successfully installed
            and removed on a host

        :parametrized: yes
        """
        client = rhel_contenthost
        packages = ['monkey', 'panda', 'seal']
        client.register(
            module_org,
            None,
            module_ak_with_cv.name,
            target_sat,
            repo=settings.repos.yum_3.url,
        )
        # Install packages
        invocation_command = make_job_invocation(
            {
                'job-template': 'Install Package - Katello Script Default',
                'inputs': f'package={" ".join(packages)}',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        result = client.run(f'rpm -q {" ".join(packages)}')
        assert result.status == 0
        # Update packages
        pre_versions = result.stdout.splitlines()
        result = client.run(f'dnf -y downgrade {" ".join(packages)}')
        assert result.status == 0
        invocation_command = make_job_invocation(
            {
                'job-template': 'Update Package - Katello Script Default',
                'inputs': f'package={" ".join(packages)}',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        post_versions = client.run(f'rpm -q {" ".join(packages)}').stdout.splitlines()
        assert set(pre_versions) == set(post_versions)
        # Remove packages
        invocation_command = make_job_invocation(
            {
                'job-template': 'Remove Package - Katello Script Default',
                'inputs': f'package={" ".join(packages)}',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        result = client.run(f'rpm -q {" ".join(packages)}')
        assert result.status == len(packages)

    @pytest.mark.tier3
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([8])
    @pytest.mark.skipif(
        (not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url'
    )
    def test_positive_install_remove_packagegroup_with_a_job(
        self, rhel_contenthost, module_org, module_ak_with_cv, target_sat
    ):
        """Run job to install and remove several package groups on host

        :id: 5be2a5c0-199a-4655-9784-e95c7ef151f5

        :expectedresults: Verify the package groups were successfully installed
            and removed on a host

        :parametrized: yes
        """
        client = rhel_contenthost
        groups = ['birds', 'mammals']
        client.register(
            module_org,
            None,
            module_ak_with_cv.name,
            target_sat,
            repo=settings.repos.yum_1.url,
        )
        # Install the package groups
        invocation_command = make_job_invocation(
            {
                'job-template': 'Install Group - Katello Script Default',
                'inputs': f'package={" ".join(groups)}',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        result = client.run('dnf grouplist --installed')
        assert all(item in result.stdout for item in groups)
        # Remove one of the installed package groups
        remove = random.choice(groups)
        invocation_command = make_job_invocation(
            {
                'job-template': 'Remove Group - Katello Script Default',
                'inputs': f'package={remove}',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        result = client.run('dnf grouplist --installed')
        assert remove not in result.stdout

    @pytest.mark.tier3
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_list([8])
    @pytest.mark.skipif(
        (not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url'
    )
    def test_positive_install_errata_with_a_job(
        self, rhel_contenthost, module_org, module_ak_with_cv, target_sat
    ):
        """Run job to install errata on host

        :id: d906a884-9fd7-48dc-a91b-fa6e8c3311c1

        :expectedresults: Verify the errata was successfully installed on a host

        :parametrized: yes
        """
        client = rhel_contenthost
        client.register(
            module_org,
            None,
            module_ak_with_cv.name,
            target_sat,
            repo=settings.repos.yum_1.url,
        )
        client.run(f'dnf install -y {constants.FAKE_1_CUSTOM_PACKAGE}')
        # Install errata
        invocation_command = make_job_invocation(
            {
                'job-template': 'Install Errata - Katello Script Default',
                'inputs': f'errata={settings.repos.yum_0.errata[1]}',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        result = client.run(f'rpm -q {constants.FAKE_2_CUSTOM_PACKAGE}')
        assert result.status == 0

    @pytest.mark.tier3
    @pytest.mark.parametrize('feature', **parametrized(valid_feature_names()))
    def test_positive_match_feature_templates(self, target_sat, feature):
        """Verify the `feature` names match the correct templates

        :id: a7cf23fe-4d3b-4bd2-b921-d31ad3e4d7e9

        :expectedresults: All features exist and match the expected templates

        :parametrized: yes
        """
        result = target_sat.cli.RemoteExecutionFeature.info({'id': feature['label']})
        assert result['job-template-name'] == feature['jt_name']

    @pytest.mark.tier3
    @pytest.mark.rhel_ver_list([8])
    def test_positive_run_recurring_job_with_max_iterations(self, rex_contenthost):
        """Run default job template multiple times with max iteration

        :id: 0a3d1627-95d9-42ab-9478-a908f2a7c509

        :expectedresults: Verify the job was run not more than the specified
            number of times.

        :parametrized: yes
        """
        client = rex_contenthost
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': 'command=ls',
                'search-query': f"name ~ {client.hostname}",
                'cron-line': '* * * * *',  # every minute
                'max-iteration': 2,  # just two runs
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        assert_job_invocation_status(invocation_command['id'], client.hostname, 'queued')
        sleep(150)
        rec_logic = RecurringLogic.info({'id': result['recurring-logic-id']})
        assert rec_logic['state'] == 'finished'
        assert rec_logic['iteration'] == '2'

    @pytest.mark.tier3
    @pytest.mark.rhel_ver_list([8])
    def test_positive_time_expressions(self, rex_contenthost):
        """Test various expressions for extended cronline syntax

        :id: 584e7b27-9484-436a-b850-11acb900a7d8

        :expectedresults: Verify the job was scheduled to the expected
            iteration

        :bz: 1967030

        :customerscenario: true

        """
        client = rex_contenthost
        today = datetime.today()
        hour = datetime.utcnow().hour
        last_day_of_month = monthrange(today.year, today.month)[1]
        days_to = (2 - today.weekday()) % 7
        # cronline uses https://github.com/floraison/fugit
        fugit_expressions = [
            ['@yearly', f'{today.year + 1}/01/01 00:00:00'],
            [
                '@monthly',
                f'{(today + relativedelta(months=+1)).strftime("%Y/%m")}/01 00:00:00',
            ],
            [
                '@weekly',
                f'{(today + timedelta(days=-today.weekday() +6)).strftime("%Y/%m/%d")} 00:00:00',
            ],
            [
                '@midnight',
                f'{(today + timedelta(days=1)).strftime("%Y/%m/%d")} 00:00:00',
            ],
            [
                '@hourly',
                f'{(datetime.utcnow() + timedelta(hours=1)).strftime("%Y/%m/%d %H")}:00:00',
            ],
            [
                '0 0 * * wed-fri',
                f'{(today + timedelta(days=(days_to if days_to > 0 else 1))).strftime("%Y/%m/%d")} '
                '00:00:00',
            ],
            # 23 mins after every other hour
            [
                '23 0-23/2 * * *',
                f'{today.strftime("%Y/%m/%d")} '
                f'{ (str(hour if hour % 2 == 0 else hour + 1)).rjust(2,"0") }:23:00',
            ],
            # last day of month
            [
                '0 0 last * *',
                f'{today.strftime("%Y/%m")}/{last_day_of_month} 00:00:00',
            ],
            # last 7 days of month
            [
                '0 0 -7-L * *',
                f'{today.strftime("%Y/%m")}/{last_day_of_month-6} 00:00:00',
            ],
            # last friday of month at 7
            [
                '0 7 * * fri#-1',
                f'{(today+relativedelta(day=31, weekday=FR(-1))).strftime("%Y/%m/%d")} 07:00:00',
            ],
        ]
        for exp in fugit_expressions:
            invocation_command = make_job_invocation(
                {
                    'job-template': 'Run Command - Script Default',
                    'inputs': 'command=ls',
                    'search-query': f"name ~ {client.hostname}",
                    'cron-line': exp[0],
                    'max-iteration': 1,
                }
            )
            result = JobInvocation.info({'id': invocation_command['id']})
            assert_job_invocation_status(invocation_command['id'], client.hostname, 'queued')
            rec_logic = RecurringLogic.info({'id': result['recurring-logic-id']})
            assert (
                rec_logic['next-occurrence'] == exp[1]
            ), f'Job was not scheduled as expected using {exp[0]}'

    @pytest.mark.tier3
    @pytest.mark.rhel_ver_list([8])
    def test_positive_run_scheduled_job_template(self, rex_contenthost, target_sat):
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
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': 'command=ls',
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
        assert_job_invocation_result(invocation_command['id'], client.hostname)


class TestAnsibleREX:
    """Test class for remote execution via Ansible"""

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.pit_client
    @pytest.mark.pit_server
    @pytest.mark.rhel_ver_list([7, 8, 9])
    def test_positive_run_effective_user_job(self, rex_contenthost):
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
        client = rex_contenthost
        # create a user on client via remote job
        username = gen_string('alpha')
        filename = gen_string('alpha')
        make_user_job = make_job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': f"command=useradd -m {username}",
                'search-query': f"name ~ {client.hostname}",
            }
        )
        assert_job_invocation_result(make_user_job['id'], client.hostname)
        # create a file as new user
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': f"command=touch /home/{username}/{filename}",
                'search-query': f"name ~ {client.hostname}",
                'effective-user': f'{username}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        # check the file owner
        result = client.execute(
            f'''stat -c '%U' /home/{username}/{filename}''',
        )
        # assert the file is owned by the effective user
        assert username == result.stdout.strip('\n'), "file ownership mismatch"

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.rhel_ver_list([8])
    def test_positive_run_reccuring_job(self, rex_contenthost):
        """Tests Ansible REX reccuring job runs successfully multiple times

        :id: 49b0d31d-58f9-47f1-aa5d-561a1dcb0d66

        :Steps:

            0. Create a VM and register to SAT and prepare for REX (ssh key)

            1. Run recurring Ansible Command job for the host

            2. Check the multiple job results at the host

        :expectedresults: multiple asserts along the code

        :CaseAutomation: Automated

        :customerscenario: true

        :bz: 2129432

        :CaseLevel: System

        :parametrized: yes
        """
        client = rex_contenthost
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Ansible Default',
                'inputs': 'command=ls',
                'search-query': f"name ~ {client.hostname}",
                'cron-line': '* * * * *',  # every minute
                'max-iteration': 2,  # just two runs
            }
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        sleep(150)
        rec_logic = RecurringLogic.info({'id': result['recurring-logic-id']})
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

    @pytest.mark.tier3
    @pytest.mark.no_containers
    def test_positive_run_concurrent_jobs(self, registered_hosts, module_org):
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
        clients = registered_hosts
        output_msgs = []
        invocation_command = make_job_invocation(
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

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.e2e
    @pytest.mark.no_containers
    @pytest.mark.pit_server
    @pytest.mark.rhel_ver_match('[^6].*')
    @pytest.mark.skipif(
        (not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url'
    )
    def test_positive_run_packages_and_services_job(
        self, rhel_contenthost, module_org, module_ak_with_cv, target_sat
    ):
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
        client = rhel_contenthost
        packages = ['tapir']
        client.register(
            module_org,
            None,
            module_ak_with_cv.name,
            target_sat,
            repo=settings.repos.yum_3.url,
        )
        # install package
        invocation_command = make_job_invocation(
            {
                'job-template': 'Package Action - Ansible Default',
                'inputs': 'state=latest, name={}'.format(*packages),
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
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
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        result = client.execute(f'systemctl status {service}')
        assert result.status == 3

        # start it again
        invocation_command = make_job_invocation(
            {
                'job-template': 'Service Action - Ansible Default',
                'inputs': f'state=started, name={service}',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], client.hostname)
        result = client.execute(f'systemctl status {service}')
        assert result.status == 0

    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'fixture_sca_vmsetup', [{'nick': 'rhel8'}], ids=['rhel8'], indirect=True
    )
    def test_positive_install_ansible_collection(
        self, fixture_sca_vmsetup, module_sca_manifest_org
    ):
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

        :Team: Rocket
        """
        # Configure repository to prepare for installing ansible on host
        RepositorySet.enable(
            {
                'basearch': 'x86_64',
                'name': REPOSET['rhae2.9_el8'],
                'organization-id': module_sca_manifest_org.id,
                'product': PRDS['rhae'],
                'releasever': '8',
            }
        )
        Repository.synchronize(
            {
                'name': REPOS['rhae2.9_el8']['name'],
                'organization-id': module_sca_manifest_org.id,
                'product': PRDS['rhae'],
            }
        )
        client = fixture_sca_vmsetup
        client.execute('subscription-manager refresh')
        client.execute(f'subscription-manager repos --enable {REPOS["rhae2.9_el8"]["id"]}')
        client.execute('dnf -y install ansible')
        collection_job = make_job_invocation(
            {
                'job-template': 'Ansible Collection - Install from Galaxy',
                'inputs': 'ansible_collections_list="oasis_roles.system"',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        result = JobInvocation.info({'id': collection_job['id']})
        assert result['success'] == '1'
        collection_path = client.execute('ls /etc/ansible/collections/ansible_collections').stdout
        assert 'oasis_roles' in collection_path

        # Extend test with custom collections_path advanced input field
        collection_job = make_job_invocation(
            {
                'job-template': 'Ansible Collection - Install from Galaxy',
                'inputs': 'ansible_collections_list="oasis_roles.system", collections_path="~/"',
                'search-query': f'name ~ {client.hostname}',
            }
        )
        result = JobInvocation.info({'id': collection_job['id']})
        assert result['success'] == '1'
        collection_path = client.execute('ls ~/ansible_collections').stdout
        assert 'oasis_roles' in collection_path


class TestRexUsers:
    """Tests related to remote execution users"""

    @pytest.fixture(scope='class')
    def class_rexmanager_user(self, module_org):
        """Creates a user with Remote Execution Manager role"""
        password = gen_string('alpha')
        rexmanager = gen_string('alpha')
        make_user({'login': rexmanager, 'password': password, 'organization-ids': module_org.id})
        User.add_role({'login': rexmanager, 'role': 'Remote Execution Manager'})
        return (rexmanager, password)

    @pytest.fixture(scope='class')
    def class_rexinfra_user(self, module_org):
        """Creates a user with all Remote Execution related permissions"""
        password = gen_string('alpha')
        rexinfra = gen_string('alpha')
        make_user({'login': rexinfra, 'password': password, 'organization-ids': module_org.id})
        role = make_role({'organization-ids': module_org.id})
        invocation_permissions = [
            permission['name']
            for permission in Filter.available_permissions(
                {'search': 'resource_type=JobInvocation'}
            )
        ]
        template_permissions = [
            permission['name']
            for permission in Filter.available_permissions({'search': 'resource_type=JobTemplate'})
        ]
        permissions = ','.join(invocation_permissions)
        make_filter({'role-id': role['id'], 'permissions': permissions})
        permissions = ','.join(template_permissions)
        # needs execute_jobs_on_infrastructure_host permission
        make_filter({'role-id': role['id'], 'permissions': permissions})
        User.add_role({'login': rexinfra, 'role': role['name']})
        User.add_role({'login': rexinfra, 'role': 'Remote Execution Manager'})
        return (rexinfra, password)

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.parametrize(
        'infra_host',
        ['target_sat', 'module_capsule_configured'],
        ids=['satellite', 'capsule'],
        indirect=True,
    )
    @pytest.mark.rhel_ver_list([8])
    @pytest.mark.no_containers
    def test_positive_rex_against_infra_hosts(
        self,
        rex_contenthost,
        class_rexmanager_user,
        class_rexinfra_user,
        target_sat,
        infra_host,
        module_org,
    ):
        """
        Tests related to remote execution against Satellite host

        :id: 36942e30-b885-4ba3-933b-7f59888935c9

        :steps:
            1. Run rex job against Satellite and Capsule as admin
            2. Run rex job against Satellite and Capsule as a REX admin
            3. Run rex job against Satellite and Capsule as a custom user with
               required permission

        :expectedresults: Only users with execute_jobs_on_infrastructure_host perm
            can run rex against Satellite

        :caseautomation: Automated

        :parametrized: yes

        """
        client = rex_contenthost
        infra_host.add_rex_key(satellite=target_sat)
        Host.update({'name': infra_host.hostname, 'new-organization-id': module_org.id})

        # run job as admin
        command = f"echo {gen_string('alpha')}"
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': f'command={command}',
                'search-query': f"name ^ ({client.hostname}, {infra_host.hostname})",
            }
        )
        output_msgs = []
        hostnames = [client.hostname, infra_host.hostname]
        for hostname in hostnames:
            inv_output = ' '.join(
                JobInvocation.get_output({'id': invocation_command['id'], 'host': hostname})
            )
            output_msgs.append(f"host output from {hostname}: { inv_output }")
        result = JobInvocation.info({'id': invocation_command['id']})
        assert result['success'] == '2', output_msgs

        # run job as regular rex user on all hosts
        invocation_command = make_job_invocation_with_credentials(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': f'command={command}',
                'search-query': f"name ^ ({client.hostname}, {infra_host.hostname})",
            },
            class_rexmanager_user,
        )

        result = JobInvocation.info({'id': invocation_command['id']})
        assert result['success'] == '1'

        # run job as regular rex user just on infra hosts
        invocation_command = make_job_invocation_with_credentials(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': f'command={command}',
                'search-query': f"name ^ ({infra_host.hostname})",
            },
            class_rexmanager_user,
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        assert result['success'] == '0'

        # run job as rex user on Satellite
        invocation_command = make_job_invocation_with_credentials(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': f'command={command}',
                'search-query': f"name ^ ({infra_host.hostname})",
            },
            class_rexinfra_user,
        )
        result = JobInvocation.info({'id': invocation_command['id']})
        assert result['success'] == '1'


class TestAsyncSSHProviderRex:
    """Tests related to remote execution via async ssh provider"""

    @pytest.mark.no_containers
    @pytest.mark.tier3
    @pytest.mark.e2e
    @pytest.mark.upgrade
    @pytest.mark.rhel_ver_match('[^6].*')
    def test_positive_run_job_on_host_registered_to_async_ssh_provider(
        self,
        module_org,
        smart_proxy_location,
        module_ak_with_cv,
        module_target_sat,
        module_capsule_configured_async_ssh,
        rhel_contenthost,
    ):
        """Run custom template on host registered to async ssh provider

        :id: 382dd6b8-eee5-4a95-8510-b3f8cc540c01

        :expectedresults: Verify the job was successfully ran against the host registered to
            capsule with ssh-async provider enabled

        :CaseImportance: Critical

        :bz: 2128209

        :parametrized: yes
        """
        # Update module_capsule_configured_async_ssh to include module_org/smart_proxy_location
        module_target_sat.cli.Capsule.update(
            {
                'name': module_capsule_configured_async_ssh.hostname,
                'organization-ids': module_org.id,
                'location-ids': smart_proxy_location.id,
            }
        )
        result = rhel_contenthost.register(
            module_org,
            smart_proxy_location,
            module_ak_with_cv.name,
            module_capsule_configured_async_ssh,
            ignore_subman_errors=True,
            force=True,
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'
        # run script provider rex command, longer-running command is needed to
        # verify the connection is not shut down too soon
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': 'command=echo start; sleep 10; echo done',
                'search-query': f"name ~ {rhel_contenthost.hostname}",
            }
        )
        assert_job_invocation_result(invocation_command['id'], rhel_contenthost.hostname)


class TestPullProviderRex:
    """Tests related to remote execution via pull provider (mqtt)"""

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_match('[^6].*')
    def test_positive_run_job_on_host_converted_to_pull_provider(
        self,
        module_org,
        smart_proxy_location,
        module_ak_with_cv,
        module_target_sat,
        module_capsule_configured_mqtt,
        rhel_contenthost,
    ):
        """Run custom template on host converted to mqtt

        :id: 9ad68172-de7b-4578-a3ae-49b6ff461691

        :expectedresults: Verify the job was successfully ran against the host converted to mqtt

        :CaseImportance: Critical

        :parametrized: yes
        """
        client_repo = ohsnap.dogfood_repository(
            settings.ohsnap,
            product='client',
            repo='client',
            release='client',
            os_release=rhel_contenthost.os_version.major,
        )
        # Update module_capsule_configured_mqtt to include module_org/smart_proxy_location
        module_target_sat.cli.Capsule.update(
            {
                'name': module_capsule_configured_mqtt.hostname,
                'organization-ids': module_org.id,
                'location-ids': smart_proxy_location.id,
            }
        )
        # register host with rex, enable client repo, install katello-agent
        result = rhel_contenthost.register(
            module_org,
            smart_proxy_location,
            module_ak_with_cv.name,
            module_capsule_configured_mqtt,
            packages=['katello-agent'],
            repo=client_repo.baseurl,
            ignore_subman_errors=True,
            force=True,
        )
        assert result.status == 0, f'Failed to register host: {result.stderr}'

        # install conversion script (SAT-1670)
        result = rhel_contenthost.execute('yum install -y katello-pull-transport-migrate')
        assert result.status == 0, 'Failed to install katello-pull-transport-migrate'
        # check mqtt client is running
        result = rhel_contenthost.execute('systemctl status yggdrasild')
        assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'
        result = rhel_contenthost.execute('systemctl status yggdrasild')
        assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'
        # run script provider rex command
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': 'command=ls',
                'search-query': f"name ~ {rhel_contenthost.hostname}",
            }
        )
        assert_job_invocation_result(invocation_command['id'], rhel_contenthost.hostname)
        # check katello-agent runs along ygdrassil (SAT-1671)
        result = rhel_contenthost.execute('systemctl status goferd')
        assert result.status == 0, 'Failed to start goferd on client'

        # run Ansible rex command to prove ssh provider works, remove katello-agent
        invocation_command = make_job_invocation(
            {
                'job-template': 'Package Action - Ansible Default',
                'inputs': 'state=absent, name=katello-agent',
                'search-query': f"name ~ {rhel_contenthost.hostname}",
            }
        )
        assert_job_invocation_result(invocation_command['id'], rhel_contenthost.hostname)

        # check katello-agent removal did not influence ygdrassil (SAT-1672)
        result = rhel_contenthost.execute('systemctl status yggdrasild')
        assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'
        result = rhel_contenthost.execute('systemctl status yggdrasild')
        assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': 'command=ls',
                'search-query': f"name ~ {rhel_contenthost.hostname}",
            }
        )
        assert_job_invocation_result(invocation_command['id'], rhel_contenthost.hostname)
        result = JobInvocation.info({'id': invocation_command['id']})

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.e2e
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_match('[^6].*')
    def test_positive_run_job_on_host_registered_to_pull_provider(
        self,
        module_org,
        module_target_sat,
        smart_proxy_location,
        module_ak_with_cv,
        module_capsule_configured_mqtt,
        rhel_contenthost,
    ):
        """Run custom template on host registered to mqtt, check effective user setting

        :id: 759ad51d-eea7-4d7b-b6ee-60af2b814464

        :expectedresults: Verify the job was successfully ran against the host registered to mqtt,
            effective user setting is honored.

        :CaseImportance: Critical

        :parametrized: yes
        """
        client_repo = ohsnap.dogfood_repository(
            settings.ohsnap,
            product='client',
            repo='client',
            release='client',
            os_release=rhel_contenthost.os_version.major,
        )
        # Update module_capsule_configured_mqtt to include module_org/smart_proxy_location
        module_target_sat.cli.Capsule.update(
            {
                'name': module_capsule_configured_mqtt.hostname,
                'organization-ids': module_org.id,
                'location-ids': smart_proxy_location.id,
            }
        )
        # register host with pull provider rex (SAT-1677)
        result = rhel_contenthost.register(
            module_org,
            smart_proxy_location,
            module_ak_with_cv.name,
            module_capsule_configured_mqtt,
            setup_remote_execution_pull=True,
            repo=client_repo.baseurl,
            ignore_subman_errors=True,
            force=True,
        )

        assert result.status == 0, f'Failed to register host: {result.stderr}'
        # check mqtt client is running
        result = rhel_contenthost.execute('systemctl status yggdrasild')
        assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'
        # run script provider rex command
        invocation_command = make_job_invocation(
            {
                'job-template': 'Service Action - Script Default',
                'inputs': 'action=status, service=yggdrasild',
                'search-query': f"name ~ {rhel_contenthost.hostname}",
            }
        )
        assert_job_invocation_result(invocation_command['id'], rhel_contenthost.hostname)
        # create user on host
        username = gen_string('alpha')
        filename = gen_string('alpha')
        make_user_job = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': f"command=useradd -m {username}",
                'search-query': f"name ~ {rhel_contenthost.hostname}",
            }
        )
        assert_job_invocation_result(make_user_job['id'], rhel_contenthost.hostname)
        # create a file as new user
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': f"command=touch /home/{username}/{filename}",
                'search-query': f"name ~ {rhel_contenthost.hostname}",
                'effective-user': f'{username}',
            }
        )
        assert_job_invocation_result(invocation_command['id'], rhel_contenthost.hostname)
        # check the file owner
        result = rhel_contenthost.execute(
            f'''stat -c '%U' /home/{username}/{filename}''',
        )
        # assert the file is owned by the effective user
        assert username == result.stdout.strip('\n')

    @pytest.mark.tier3
    @pytest.mark.upgrade
    @pytest.mark.no_containers
    @pytest.mark.rhel_ver_match('[^6].*')
    def test_positive_run_pull_job_on_offline_host(
        self,
        module_org,
        module_target_sat,
        smart_proxy_location,
        module_ak_with_cv,
        module_capsule_configured_mqtt,
        rhel_contenthost,
    ):
        """Run pull-mqtt job against offline host

        :id: c4914b78-6414-4a13-87b1-5b5cf01702a0

        :expectedresults: Job is resumed when host comes back online

        :CaseImportance: Critical

        :parametrized: yes
        """
        client_repo = ohsnap.dogfood_repository(
            settings.ohsnap,
            product='client',
            repo='client',
            release='client',
            os_release=rhel_contenthost.os_version.major,
        )
        # Update module_capsule_configured_mqtt to include module_org/smart_proxy_location
        module_target_sat.cli.Capsule.update(
            {
                'name': module_capsule_configured_mqtt.hostname,
                'organization-ids': module_org.id,
                'location-ids': smart_proxy_location.id,
            }
        )
        result = rhel_contenthost.register(
            module_org,
            smart_proxy_location,
            module_ak_with_cv.name,
            module_capsule_configured_mqtt,
            setup_remote_execution_pull=True,
            repo=client_repo.baseurl,
            ignore_subman_errors=True,
            force=True,
        )

        assert result.status == 0, f'Failed to register host: {result.stderr}'
        # check mqtt client is running
        result = rhel_contenthost.execute('systemctl status yggdrasild')
        assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'
        # stop the client on host
        result = rhel_contenthost.execute('systemctl stop yggdrasild')
        assert result.status == 0, f'Failed to stop yggdrasil on client: {result.stderr}'
        # run script provider rex command
        invocation_command = make_job_invocation(
            {
                'job-template': 'Run Command - Script Default',
                'inputs': 'command=ls',
                'search-query': f'name ~ {rhel_contenthost.hostname}',
                'async': True,
            }
        )
        # assert the job is waiting to be picked up by client
        assert_job_invocation_status(invocation_command['id'], rhel_contenthost.hostname, 'running')
        # start client on host
        result = rhel_contenthost.execute('systemctl start yggdrasild')
        assert result.status == 0, f'Failed to start yggdrasil on client: {result.stderr}'
        # wait twice the mqtt_resend_interval (set in module_capsule_configured_mqtt)
        sleep(60)
        assert_job_invocation_result(invocation_command['id'], rhel_contenthost.hostname)
