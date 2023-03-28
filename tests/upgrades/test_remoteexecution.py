"""Test for Remote Execution related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Team: Endeavour

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.hosts import Capsule


class TestScenarioREXCapsule:
    """Test Remote Execution job created before migration runs successfully
    post migration on a client registered with external capsule.

        Test Steps:

        1. Before Satellite upgrade:
           a. Register content host to Capsule.
           b. run a REX job on content host.
        2. Upgrade satellite/capsule.
        3. Run a REX Job again with same content host.
        4. Check if REX job still getting success.
    """

    @pytest.mark.rhel_ver_list([8])
    @pytest.mark.no_containers
    @pytest.mark.pre_upgrade
    def test_pre_scenario_remote_execution_external_capsule(
        self,
        rhel_contenthost,
        target_sat,
        module_org,
        smart_proxy_location,
        module_ak_with_cv,
        save_test_data,
    ):
        """
        Run REX job on client registered with external capsule

        :id: preupgrade-261dd2aa-be01-4c34-b877-54b8ee346561

        :steps:
            1. Create Content host.
            2. add rex ssh_key of external capsule on content host.
            3. run the REX job on client vm.

        :expectedresults:
            1. Content host should create with pre-required details.
            2. REX job should run on it.

        :parametrized: yes

        """
        rhel_contenthost._skip_context_checkin = True
        capsule = Capsule(target_sat.api.SmartProxy(id=2).read().name)
        target_sat.cli.Capsule.update(
            {
                'name': capsule.hostname,
                'organization-ids': module_org.id,
                'location-ids': smart_proxy_location.id,
            }
        )
        # register host with rex, enable client repo, install katello-agent
        result = rhel_contenthost.register(
            module_org,
            smart_proxy_location,
            module_ak_with_cv.name,
            target=capsule,
            satellite=target_sat,
            packages=['katello-agent'],
        )
        assert f'The registered system name is: {rhel_contenthost.hostname}' in result.stdout
        # run rex command
        template_id = (
            target_sat.api.JobTemplate()
            .search(query={'search': 'name="Run Command - Script Default"'})[0]
            .id
        )
        job = target_sat.api.JobInvocation().run(
            synchronous=False,
            data={
                'job_template_id': template_id,
                'organization': module_org.name,
                'location': smart_proxy_location.name,
                'inputs': {
                    'command': 'echo start; sleep 10; echo done',
                },
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel_contenthost.hostname}',
                'time_to_pickup': '5',
            },
        )
        target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
        result = target_sat.api.JobInvocation(id=job['id']).read()
        assert result.succeeded == 1
        # Save client info to disk for post-upgrade test
        save_test_data(
            {
                'rhel_client': rhel_contenthost.hostname,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_remote_execution_external_capsule)
    def test_post_scenario_remote_execution_external_capsule(self, target_sat, pre_upgrade_data):
        """Run a REX job on pre-upgrade created client registered
        with external capsule.

        :id: postupgrade-00ed2a25-b0bd-446f-a3fc-09149c57fe94

        :steps:
            1. Run a REX job on content host.

        :expectedresults:
            1. The job should successfully executed on pre-upgrade created client.
        """
        template_id = (
            target_sat.api.JobTemplate()
            .search(query={'search': 'name="Run Command - Script Default"'})[0]
            .id
        )
        job = target_sat.api.JobInvocation().run(
            data={
                'job_template_id': template_id,
                'inputs': {'command': 'ls'},
                'targeting_type': 'static_query',
                'search_query': f"name = {pre_upgrade_data['rhel_client']}",
            }
        )
        assert job['output']['success_count'] == 1


class TestScenarioREXSatellite:
    """Test Remote Execution job created before migration runs successfully
    post migration on a client registered with Satellite.

        Test Steps:

        1. Before Satellite upgrade:
        2. Create Content host.
        3. Register content host to Satellite.
        4. Run a REX job on content host.
        5. Upgrade satellite/capsule.
        6. Run a rex Job again with same content host.
        7. Check if REX job still getting success.
    """

    @pytest.mark.rhel_ver_list([8])
    @pytest.mark.no_containers
    @pytest.mark.pre_upgrade
    def test_pre_scenario_remote_execution_satellite(
        self,
        rhel_contenthost,
        target_sat,
        module_org,
        smart_proxy_location,
        module_ak_with_cv,
        save_test_data,
    ):
        """Run REX job on client registered with Satellite

        :id: preupgrade-3f338475-fa69-43ef-ac86-f00f4d324b33

        :steps:
            1. Create Content host.
            2. Run the REX job on client vm.

        :expectedresults:
            1. It should create with pre-required details.
            2. REX job should run on it.

        :parametrized: yes
        """
        rhel_contenthost._skip_context_checkin = True
        # register host with rex, enable client repo, install katello-agent
        result = rhel_contenthost.register(
            module_org,
            smart_proxy_location,
            module_ak_with_cv.name,
            target=target_sat,
            satellite=target_sat,
            packages=['katello-agent'],
        )
        assert f'The registered system name is: {rhel_contenthost.hostname}' in result.stdout
        # run rex command
        template_id = (
            target_sat.api.JobTemplate()
            .search(query={'search': 'name="Run Command - Script Default"'})[0]
            .id
        )
        job = target_sat.api.JobInvocation().run(
            synchronous=False,
            data={
                'job_template_id': template_id,
                'organization': module_org.name,
                'location': smart_proxy_location.name,
                'inputs': {
                    'command': 'echo start; sleep 10; echo done',
                },
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel_contenthost.hostname}',
                'time_to_pickup': '5',
            },
        )
        target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
        result = target_sat.api.JobInvocation(id=job['id']).read()
        assert result.succeeded == 1
        # Save client info to disk for post-upgrade test
        save_test_data(
            {
                'rhel_client': rhel_contenthost.hostname,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_scenario_remote_execution_satellite)
    def test_post_scenario_remote_execution_satellite(self, target_sat, pre_upgrade_data):
        """Run a REX job on pre-upgrade created client registered
        with Satellite.

        :id: postupgrade-ad3b1564-d3e6-4ada-9337-3a6ee6863bae

        :steps:
            1. Run a REX job on content host.

        :expectedresults:
            1. The job should successfully executed on pre-upgrade created client.
        """
        template_id = (
            target_sat.api.JobTemplate()
            .search(query={'search': 'name="Run Command - Script Default"'})[0]
            .id
        )
        job = target_sat.api.JobInvocation().run(
            data={
                'job_template_id': template_id,
                'inputs': {'command': 'ls'},
                'targeting_type': 'static_query',
                'search_query': f"name = {pre_upgrade_data['rhel_client']}",
            }
        )
        assert job['output']['success_count'] == 1
