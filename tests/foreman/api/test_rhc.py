"""Test class for RH Cloud connector - rhc

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseComponent: RHCloud

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

from fauxfactory import gen_string
import pytest

from robottelo.utils.issue_handlers import is_open


@pytest.fixture
def fixture_enable_rhc_repos(target_sat):
    """Enable repos required for configuring RHC."""
    # subscribe rhc satellite to cdn.
    target_sat.register_to_cdn()
    if target_sat.os_version.major > 7:
        target_sat.enable_repo(target_sat.REPOS['rhel_bos']['id'])
        target_sat.enable_repo(target_sat.REPOS['rhel_aps']['id'])
    else:
        target_sat.enable_repo(target_sat.REPOS['rhscl']['id'])
        target_sat.enable_repo(target_sat.REPOS['rhel']['id'])


@pytest.mark.e2e
@pytest.mark.tier3
@pytest.mark.destructive
def test_positive_configure_cloud_connector(target_sat, default_org, fixture_enable_rhc_repos):
    """
    Enable RH Cloud Connector through API

    :id: 1338dc6a-12e0-4378-9a51-a33f4679ba30

    :steps:

        1. Enable RH Cloud Connector
        2. Check if the task is completed successfully

    :expectedresults: The Cloud Connector has been installed and the service is running

    :CaseImportance: Critical
    """

    # Delete old satellite  hostname if BZ#2130173 is open
    if is_open('BZ:2130173'):
        host = target_sat.api.Host().search(query={'search': f"! {target_sat.hostname}"})[0]
        host.delete()

    # Copy foreman-proxy user's key to root@localhost user's authorized_keys
    target_sat.add_rex_key(satellite=target_sat)

    # Set Host parameter source_display_name to something random.
    # To avoid 'name has already been taken' error when run multiple times
    # on a machine with the same hostname.
    host = target_sat.api.Host().search(query={'search': target_sat.hostname})[0]
    parameters = [{'name': 'source_display_name', 'value': gen_string('alpha')}]
    host.host_parameters_attributes = parameters
    host.update(['host_parameters_attributes'])

    enable_connector = target_sat.api.RHCloud(organization=default_org).enable_connector()

    template_name = 'Configure Cloud Connector'
    invocation_id = (
        target_sat.api.JobInvocation()
        .search(query={'search': f'description="{template_name}"'})[0]
        .id
    )
    task_id = enable_connector['task_id']
    target_sat.wait_for_tasks(
        search_query=(f'label = Actions::RemoteExecution::RunHostsJob and id = {task_id}'),
        search_rate=15,
    )

    job_output = target_sat.cli.JobInvocation.get_output(
        {'id': invocation_id, 'host': target_sat.hostname}
    )
    # get rhc status
    rhc_status = target_sat.execute('rhc status')
    # get rhcd log
    rhcd_log = target_sat.execute('journalctl --unit=rhcd')

    assert target_sat.api.JobInvocation(id=invocation_id).read().status == 0
    assert "Install yggdrasil-worker-forwarder and rhc" in job_output
    assert "Restart rhcd" in job_output
    assert 'Exit status: 0' in job_output

    assert rhc_status.status == 0
    assert "Connected to Red Hat Subscription Management" in rhc_status.stdout
    assert "The Remote Host Configuration daemon is active" in rhc_status.stdout

    assert "error" not in rhcd_log.stdout
