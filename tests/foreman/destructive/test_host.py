"""Test class for Hosts UI

:Requirement: Host

:CaseAutomation: Automated

:CaseComponent: Hosts

:Team: Proton

:CaseImportance: High

"""

from airgun.exceptions import NoSuchElementException
import pytest

from robottelo.constants import ANY_CONTEXT
from robottelo.logging import logger


class TestHostCockpit:
    """Tests for cockpit plugin"""

    pytestmark = pytest.mark.destructive

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

            try:
                hostname_inside_cockpit = session.host.get_webconsole_content(
                    entity_name=cockpit_host.hostname,
                    rhel_version=cockpit_host.os_version.major,
                )
            except NoSuchElementException:
                # /login returns 500 — capture foreman-cockpit-session error
                host = cockpit_host.hostname
                # Restart foreman-cockpit with debug logging, then
                # replay the /login request to capture the error
                class_cockpit_sat.execute('systemctl stop foreman-cockpit')
                class_cockpit_sat.execute(
                    'COCKPIT_DEBUG=all /usr/libexec/cockpit-ws'
                    ' --no-tls --address 127.0.0.1 --port 19090'
                    ' &>/tmp/cockpit-ws-debug.log &'
                    ' echo $!>/tmp/cockpit-ws-debug.pid;'
                    ' sleep 2'
                )
                class_cockpit_sat.execute(
                    f'curl -sk -o /dev/null'
                    f' https://{class_cockpit_sat.hostname}'
                    f'/webcon/cockpit+%3D{host}/login 2>&1 || true'
                )
                import time

                time.sleep(3)
                class_cockpit_sat.execute(
                    'kill $(cat /tmp/cockpit-ws-debug.pid) 2>/dev/null || true'
                )
                result = class_cockpit_sat.execute('cat /tmp/cockpit-ws-debug.log 2>&1')
                logger.info(
                    f'[cockpit-debug][sat-cockpit_ws_debug_log] rc={result.status}\n{result.stdout}'
                )
                class_cockpit_sat.execute('systemctl start foreman-cockpit')
                raise

            assert cockpit_host.hostname in hostname_inside_cockpit, (
                f'cockpit page shows hostname {hostname_inside_cockpit} '
                f'instead of {cockpit_host.hostname}'
            )
