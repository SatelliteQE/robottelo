"""Test class for Hosts UI

:Requirement: Host

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: tstrych

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from airgun.exceptions import NoSuchElementException


class TestHostCockpit:
    """Tests for cockpit plugin"""

    pytestmark = pytest.mark.destructive

    @pytest.mark.upgrade
    @pytest.mark.rhel_ver_match('[^6].*')
    @pytest.mark.usefixtures('install_cockpit_plugin')
    @pytest.mark.tier2
    def test_positive_cockpit(self, cockpit_host, class_target_sat, class_org):
        """Install cockpit plugin and test whether webconsole button and cockpit integration works.
        also verify if cockpit service is restarted after the service restart.

        :id: 5a9be063-cdc4-43ce-91b9-7608fbebf8bb

        :expectedresults: Cockpit page is loaded and displays sat host info

        :BZ: 1876220

        :CaseLevel: System

        :steps:
            1. kill the cockpit service.
            2. go to web console and verify if getting 503 error.
            3. check if service "cockpit.service" exists using service list.
            4. restart the satellite services.
            5. check cockpit page is loaded and displays sat host info.

        expectedresults:
            1. cockpit service is restarted after the services restart.
            2. cockpit page is loaded and displays sat host info

        :parametrized: yes
        """
        with class_target_sat.ui_session as session:
            session.organization.select(org_name=class_org.name)
            session.location.select(loc_name='Any Location')
            kill_process = class_target_sat.execute('pkill -f cockpit-ws')
            assert kill_process.status == 0
            # Verify if getting 503 error
            with pytest.raises(NoSuchElementException):
                session.host.get_webconsole_content(entity_name=cockpit_host.hostname)
            title = session.browser.title
            assert "503 Service Unavailable" in title

            service_list = class_target_sat.cli.Service.list()
            assert service_list.status == 0
            assert "foreman-cockpit.service" in service_list.stdout

            service_restart = class_target_sat.cli.Service.restart()
            assert service_restart.status == 0
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
