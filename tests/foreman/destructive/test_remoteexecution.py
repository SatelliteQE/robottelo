"""Test for Remote Execution

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""

from airgun.exceptions import NoSuchElementException
from fauxfactory import gen_string
from nailgun import client
from nailgun.entity_mixins import TaskFailedError
import pytest

from robottelo.config import get_credentials
from robottelo.constants import ANY_CONTEXT
from robottelo.hosts import get_sat_version

CAPSULE_TARGET_VERSION = f'6.{get_sat_version().minor}.z'

pytestmark = pytest.mark.destructive


def test_negative_run_capsule_upgrade_playbook_on_satellite(target_sat):
    """Run Capsule Upgrade playbook against the Satellite itself

    :id: 99462a11-5133-415d-ba64-4354da539a34

    :steps:
        1. Add REX key to the Satellite server.
        2. Run the Capsule Upgrade Playbook.
        3. Check the job output for proper failure reason.

    :expectedresults: Should fail

    :BZ: 2152951

    :CaseImportance: Medium
    """
    template_name = 'Capsule Upgrade Playbook'
    template_id = (
        target_sat.api.JobTemplate().search(query={'search': f'name="{template_name}"'})[0].id
    )
    target_sat.add_rex_key(satellite=target_sat)
    with pytest.raises(TaskFailedError) as error:
        target_sat.api.JobInvocation().run(
            data={
                'job_template_id': template_id,
                'inputs': {
                    'target_version': CAPSULE_TARGET_VERSION,
                    'whitelist_options': "repositories-validqqate,repositories-setup",
                },
                'targeting_type': "static_query",
                'search_query': f"name = {target_sat.hostname}",
            }
        )
    assert 'A sub task failed' in error.value.args[0]
    job = target_sat.api.JobInvocation().search(
        query={
            'search': f'host={target_sat.hostname},'
            'status=failed,description="Capsule Upgrade Playbook"'
        }
    )[0]
    host = target_sat.api.Host().search(query={'search': target_sat.hostname})
    response = client.get(
        f'{target_sat.url}/api/job_invocations/{job.id}/hosts/{host[0].id}',
        auth=get_credentials(),
        verify=False,
    )
    assert 'This playbook cannot be executed on a Satellite server.' in response.text


@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([8])
def test_positive_use_alternate_directory(
    target_sat, rhel_contenthost, default_org, default_location
):
    """Use alternate working directory on client to execute rex jobs

    :id: a0181f18-d3dc-4bd9-a2a6-430c2a49809e

    :expectedresults: Verify the job was successfully ran against the host

    :customerscenario: true

    :parametrized: yes
    """
    client = rhel_contenthost
    ak = target_sat.cli_factory.make_activation_key(
        {
            'lifecycle-environment': 'Library',
            'content-view': 'Default Organization View',
            'organization-id': default_org.id,
            'auto-attach': False,
        }
    )
    result = client.register(default_org, default_location, ak.name, target_sat)
    assert result.status == 0, f'Failed to register host: {result.stderr}'
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
    invocation_command = target_sat.cli_factory.job_invocation(
        {
            'job-template': 'Run Command - Script Default',
            'inputs': f'command={command}',
            'search-query': f"name ~ {client.hostname}",
        }
    )
    result = target_sat.cli.JobInvocation.info({'id': invocation_command['id']})
    try:
        assert result['success'] == '1'
    except AssertionError as err:
        output = ' '.join(
            target_sat.cli.JobInvocation.get_output(
                {'id': invocation_command['id'], 'host': client.hostname}
            )
        )
        result = f'host output: {output}'
        raise AssertionError(result) from err

    task = target_sat.cli.Task.list_tasks({'search': command})[0]
    search = target_sat.cli.Task.list_tasks({'search': f'id={task["id"]}'})
    assert search[0]['action'] == task['action']


class TestCockpit:
    """Tests for cockpit plugin"""

    @pytest.mark.upgrade
    @pytest.mark.rhel_ver_match('[^6].*')
    @pytest.mark.no_containers
    def test_positive_cockpit(self, cockpit_host, class_cockpit_sat, class_org):
        """Install cockpit plugin and test whether webconsole button and cockpit integration works.
        also verify if cockpit service is restarted after the service restart.

        :id: 5a9be063-cdc4-43ce-91b9-7608fbebf8bb

        :expectedresults: Cockpit page is loaded and displays sat host info

        :BZ: 1876220

        :steps:
            1. kill the cockpit service.
            2. go to web console and verify if getting 503 error.
            3. check if service "cockpit.service" exists using service list.
            4. restart the satellite services.
            5. check cockpit page is loaded and displays sat host info.

        :expectedresults:
            1. cockpit service is restarted after the services restart.
            2. cockpit page is loaded and displays sat host info

        :Verifies: SAT-27411, SAT-36783

        :customerscenario: true

        :parametrized: yes
        """
        with class_cockpit_sat.ui_session() as session:
            session.organization.select(org_name=class_org.name)
            session.location.select(loc_name=ANY_CONTEXT['location'])
            kill_process = class_cockpit_sat.execute('pkill -f cockpit-ws')
            assert kill_process.status == 0
            # Verify if getting 503 error
            with pytest.raises(NoSuchElementException):
                session.host.get_webconsole_content(entity_name=cockpit_host.hostname)
            title = session.browser.title
            assert "503 Service Unavailable" in title

            service_list = class_cockpit_sat.cli.Service.list()
            assert service_list.status == 0
            assert "foreman-cockpit.service" in service_list.stdout

            service_restart = class_cockpit_sat.cli.Service.restart()
            assert service_restart.status == 0
            # SAT-36783 can be triggered by just having wide characters anywhere
            # in the payload that gets sent between Satellite, Capsule and
            # cockpit. The password doesn't have to be accepted, it doesn't even
            # have to be used. Its mere presence in the communication should be
            # enough to trigger the bug.
            class_cockpit_sat.cli.Host.set_parameter(
                {
                    'host': cockpit_host.hostname,
                    'name': 'remote_execution_ssh_password',
                    'value': '「£」はポンド記号です',
                }
            )

            session.browser.switch_to_window(session.browser.window_handles[0])
            session.browser.close_window(session.browser.window_handles[-1])
            hostname_inside_cockpit = session.host.get_webconsole_content(
                entity_name=cockpit_host.hostname,
                rhel_version=cockpit_host.os_version.major,
            )
            assert cockpit_host.hostname in hostname_inside_cockpit, (
                f'cockpit page shows hostname {hostname_inside_cockpit} '
                f'instead of {cockpit_host.hostname}'
            )
