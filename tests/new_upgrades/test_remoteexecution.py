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


@pytest.fixture
def remote_execution_external_capsule_setup(
    capsule_upgrade_integrated_sat_cap,
    rhel_contenthost,
    upgrade_action,
):
    """
    Run REX job on client registered with external capsule

    :steps:
        1. Create Content host.
        2. Add SSH key of external capsule on content host.
        3. Run REX job on content host.

    :expectedresults:
        1. Content host should be created with pre-required details.
        2. REX job should run on it.

    """
    target_sat = capsule_upgrade_integrated_sat_cap.satellite
    capsule = capsule_upgrade_integrated_sat_cap.capsule
    cap_smart_proxy = capsule_upgrade_integrated_sat_cap.cap_smart_proxy
    with (
        SharedResource(
            target_sat.hostname, upgrade_action, target_sat=target_sat, action_is_recoverable=True
        ) as sat_upgrade,
        SharedResource(
            capsule.hostname, upgrade_action, target_sat=capsule, action_is_recoverable=True
        ) as cap_upgrade,
    ):
        test_name = f'rex_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        library_id = int(
            target_sat.cli.LifecycleEnvironment.list(
                {'organization-id': org.id, 'library': 'true'}
            )[0]['id']
        )
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
                'rhel_client': rhel_contenthost.hostname,
            }
        )
        # register host with rex, enable client repo, install katello-agent
        result = rhel_contenthost.api_register(
            capsule,
            organization=org,
            activation_keys=[ak.name],
            location=location,
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
                'organization': org.name,
                'location': lce.name,
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
        sat_upgrade.ready()
        cap_upgrade.ready()
        target_sat._session = None
        capsule._session = None
        yield test_data


@pytest.mark.rhel_ver_list([7, 8, 9, 10])
@pytest.mark.no_containers
@pytest.mark.capsule_upgrades
def test_post_scenario_remote_execution_external_capsule(remote_execution_external_capsule_setup):
    """Run a REX job on pre-upgrade created client registered
    with external capsule.

    :id: postupgrade-00ed2a25-b0bd-446f-a3fc-09149c57fe94

    :steps:
        1. Run a REX job on content host.

    :expectedresults:
        1. The job should be successfully executed on pre-upgrade created client.

    :parametrized: yes
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


@pytest.fixture
def remote_execution_satellite_setup(
    capsule_upgrade_integrated_sat_cap,
    rhel_contenthost,
    upgrade_action,
):
    """Run REX job on client registered with Satellite

    Before Satellite upgrade:
    1. Create content host.
    2. Register content host to Satellite.
    3. Run a REX job on content host.
    4. Upgrade Satellite/Capsule.
    5. Run a REX job again with same content host.
    6. Check if REX job still succeeds.
    """
    target_sat = capsule_upgrade_integrated_sat_cap.satellite
    # register host with rex, enable client repo, install katello-agent
    with SharedResource(
        target_sat.hostname, upgrade_action, target_sat=target_sat, action_is_recoverable=True
    ) as sat_upgrade:
        test_name = f'rex_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        library_id = int(
            target_sat.cli.LifecycleEnvironment.list(
                {'organization-id': org.id, 'library': 'true'}
            )[0]['id']
        )
        lce = target_sat.api.LifecycleEnvironment(
            name=f'{test_name}_lce', organization=org, prior=library_id
        ).create()
        content_view = target_sat.publish_content_view(org, [], f'{test_name}_cv')
        content_view.version[0].promote(data={'environment_ids': lce.id})
        ak = target_sat.api.ActivationKey(
            name=f'{test_name}_ak', organization=org.id, environment=lce, content_view=content_view
        ).create()
        result = rhel_contenthost.api_register(
            target_sat,
            organization=org,
            activation_keys=[ak.name],
            location=location,
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
                'organization': org.name,
                'location': location.name,
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
        sat_upgrade.ready()
        target_sat._session = None
        test_data = Box({'rhel_client': rhel_contenthost.hostname, 'target_sat': target_sat})
        yield test_data


@pytest.mark.rhel_ver_list([7, 8, 9, 10])
@pytest.mark.no_containers
@pytest.mark.capsule_upgrades
def test_post_scenario_remote_execution_satellite(remote_execution_satellite_setup):
    """Run a REX job on pre-upgrade created client registered
    with Satellite.

    :id: postupgrade-ad3b1564-d3e6-4ada-9337-3a6ee6863bae

    :steps:
        1. Run a REX job on content host.

    :expectedresults:
        1. The job should successfully executed on pre-upgrade created client.

    :parametrized: yes
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
