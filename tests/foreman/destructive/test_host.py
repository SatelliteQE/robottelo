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
                # Grab read_auth_reply method and inject debug logging
                result = class_cockpit_sat.execute(
                    'grep -n "def read_auth_reply\\|def send_auth"'
                    ' /usr/sbin/foreman-cockpit-session 2>&1'
                )
                logger.info(
                    f'[cockpit-debug][sat-auth_methods_lines] rc={result.status}\n{result.stdout}'
                )
                result = class_cockpit_sat.execute(
                    'grep -n "def read_auth_reply" /usr/sbin/foreman-cockpit-session'
                    ' | head -1 | cut -d: -f1'
                )
                line_num = result.stdout.strip()
                if line_num:
                    start = max(1, int(line_num) - 2)
                    end = int(line_num) + 20
                    result = class_cockpit_sat.execute(
                        f'sed -n "{start},{end}p" /usr/sbin/foreman-cockpit-session 2>&1'
                    )
                    logger.info(
                        f'[cockpit-debug][sat-read_auth_reply_source]'
                        f' rc={result.status}\n{result.stdout}'
                    )
                # Patch the script to log what read_auth_reply returns
                class_cockpit_sat.execute(
                    "sed -i"
                    " 's/token = read_auth_reply/"
                    "reply = read_auth_reply;"
                    " LOG.error(\"AUTH_REPLY: [#{reply}]\");"
                    " token = reply/'"
                    " /usr/sbin/foreman-cockpit-session"
                )
                class_cockpit_sat.execute('systemctl restart foreman-cockpit')
                class_cockpit_sat.execute(
                    f'curl -sk -o /dev/null'
                    f' https://{class_cockpit_sat.hostname}'
                    f'/webcon/cockpit+%3D{cockpit_host.hostname}/login'
                    f' 2>&1 || true'
                )
                import time

                time.sleep(3)
                result = class_cockpit_sat.execute(
                    'journalctl -u foreman-cockpit --no-pager -n 30 2>&1'
                )
                logger.info(
                    f'[cockpit-debug][sat-patched_session_output]'
                    f' rc={result.status}\n{result.stdout}'
                )
                # Restore original script
                class_cockpit_sat.execute(
                    'yum reinstall -y rubygem-foreman_remote_execution-cockpit 2>/dev/null || true'
                )
                raise

            assert cockpit_host.hostname in hostname_inside_cockpit, (
                f'cockpit page shows hostname {hostname_inside_cockpit} '
                f'instead of {cockpit_host.hostname}'
            )
