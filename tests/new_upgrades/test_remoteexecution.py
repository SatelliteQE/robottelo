"""Test for Remote Execution related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: RemoteExecution

:Team: Endeavour

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo.utils.shared_resource import SharedResource

from remote_pdb import RemotePdb
from robottelo.logging import logger
import os
import random

# class TestScenarioREXCapsule:
#     """Test Remote Execution job created before migration runs successfully
#     post migration on a client registered with external capsule.
#
#         Test Steps:
#
#         1. Before Satellite upgrade:
#            a. Register content host to Capsule.
#            b. run a REX job on content host.
#         2. Upgrade satellite/capsule.
#         3. Run a REX Job again with same content host.
#         4. Check if REX job still getting success.
#     """
#
# @pytest.mark.rhel_ver_list([7, 8, 9])
@pytest.mark.no_containers
@pytest.fixture
def remote_execution_external_capsule_setup(
    capsule_upgrade_integrated_sat_cap,
    rhel9_contenthost,
    upgrade_action,
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
    rhel9_contenthost._skip_context_checkin = True
    target_sat = capsule_upgrade_integrated_sat_cap.satellite
    capsule = capsule_upgrade_integrated_sat_cap.capsule
    cap_smart_proxy = capsule_upgrade_integrated_sat_cap.cap_smart_proxy
    with (
        SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade,
        SharedResource(capsule.hostname, upgrade_action, target_sat=capsule) as cap_upgrade,
    ):
        test_name = f'rex_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        library_id = int(target_sat.cli.LifecycleEnvironment.list({'organization-id': org.id, 'library': 'true'})[0]['id'])
        lce = target_sat.api.LifecycleEnvironment(
            name=f'{test_name}_lce', organization=org, prior=library_id
        ).create()
        cap_smart_proxy.organization.append(org)
        cap_smart_proxy.update(['organization'])
        capsule.nailgun_capsule.content_add_lifecycle_environment(data={'environment_id': lce.id})
        content_view = target_sat.publish_content_view(org, [], f'{test_name}_cv')
        content_view.version[0].promote(data={'environment_ids': lce.id})
        ak = target_sat.api.ActivationKey(
            name=f'{test_name}_ak', organization=org.id, environment=lce, content_view=content_view
        ).create()
        test_data = Box(
            {
                'target_sat': target_sat,
                'capsule': capsule,
                'rhel_client': rhel9_contenthost.hostname,
            }
        )
        # register host with rex, enable client repo, install katello-agent
        result = rhel9_contenthost.api_register(
            capsule,
            organization=org,
            activation_keys=[ak.name],
            location=location,
        )
        assert f'The registered system name is: {rhel9_contenthost.hostname}' in result.stdout
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
                'organization': org.name,
                'location': lce.name,
                'inputs': {
                    'command': 'echo start; sleep 10; echo done',
                },
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel9_contenthost.hostname}',
                'time_to_pickup': '5',
            },
        )
        target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
        result = target_sat.api.JobInvocation(id=job['id']).read()
        assert result.succeeded == 1
        sat_upgrade.ready()
        cap_upgrade.ready()
        target_sat._session = None
        capsule._session = None
        yield test_data


# @pytest.mark.parametrize('remote_execution_external_capsule_setup', ['rhel7', 'rhel8', 'rhel9'], indirect=True)
def test_post_scenario_remote_execution_external_capsule(remote_execution_external_capsule_setup):
    """Run a REX job on pre-upgrade created client registered
    with external capsule.

    :id: postupgrade-00ed2a25-b0bd-446f-a3fc-09149c57fe94

    :steps:
        1. Run a REX job on content host.

    :expectedresults:
        1. The job should successfully executed on pre-upgrade created client.
    """
    target_sat = remote_execution_external_capsule_setup.target_sat
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
            'search_query': f"name = {remote_execution_external_capsule_setup['rhel_client']}",
        }
    )
    assert job['output']['success_count'] == 1


# class TestScenarioREXSatellite:
#     """Test Remote Execution job created before migration runs successfully
#     post migration on a client registered with Satellite.
# 
#         Test Steps:
# 
#         1. Before Satellite upgrade:
#         2. Create Content host.
#         3. Register content host to Satellite.
#         4. Run a REX job on content host.
#         5. Upgrade satellite/capsule.
#         6. Run a rex Job again with same content host.
#         7. Check if REX job still getting success.
#     """

    # @pytest.mark.rhel_ver_list([7, 8, 9])
@pytest.mark.no_containers
@pytest.fixture
def remote_execution_satellite_setup(
    capsule_upgrade_integrated_sat_cap,
    rhel9_contenthost,
    upgrade_action,
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
    rhel9_contenthost._skip_context_checkin = True
    target_sat = capsule_upgrade_integrated_sat_cap.satellite
    # register host with rex, enable client repo, install katello-agent
    port = random.randint(6000, 7000) 
    logger.debug(f'{os.environ.get("PYTEST_XIST_WORKER")} opening RemotePdb session on port {port}')
    RemotePdb('127.0.0.1', port).set_trace()
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'rex_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        library_id = int(target_sat.cli.LifecycleEnvironment.list({'organization-id': org.id, 'library': 'true'})[0]['id'])
        lce = target_sat.api.LifecycleEnvironment(
            name=f'{test_name}_lce', organization=org, prior=library_id
        ).create()
        content_view = target_sat.publish_content_view(org, [], f'{test_name}_cv')
        content_view.version[0].promote(data={'environment_ids': lce.id})
        ak = target_sat.api.ActivationKey(
            name=f'{test_name}_ak', organization=org.id, environment=lce, content_view=content_view
        ).create()
        result = rhel9_contenthost.register(
            org,
            location,
            ak.name,
            target_sat,
            packages=['katello-agent'],
        )
        assert f'The registered system name is: {rhel9_contenthost.hostname}' in result.stdout
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
                'organization': org.name,
                'location': location.name,
                'inputs': {
                    'command': 'echo start; sleep 10; echo done',
                },
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel9_contenthost.hostname}',
                'time_to_pickup': '5',
            },
        )
        target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
        result = target_sat.api.JobInvocation(id=job['id']).read()
        assert result.succeeded == 1
        # Save client info to disk for post-upgrade test
        sat_upgrade.ready()
        target_sat._session = None
        test_data = Box({
            'rhel_client': rhel9_contenthost.hostname,
            'target_sat': target_sat
        })
        yield test_data

# @pytest.mark.parametrize('pre_upgrade_data', ['rhel7', 'rhel8', 'rhel9'], indirect=True)
# @pytest.mark.post_upgrade(depend_on=test_pre_scenario_remote_execution_satellite)
def test_post_scenario_remote_execution_satellite(remote_execution_satellite_setup):
    """Run a REX job on pre-upgrade created client registered
    with Satellite.

    :id: postupgrade-ad3b1564-d3e6-4ada-9337-3a6ee6863bae

    :steps:
        1. Run a REX job on content host.

    :expectedresults:
        1. The job should successfully executed on pre-upgrade created client.
    """
    target_sat = remote_execution_satellite_setup.target_sat
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
            'search_query': f"name = {remote_execution_satellite_setup.rhel_client}",
        }
    )
    assert job['output']['success_count'] == 1
