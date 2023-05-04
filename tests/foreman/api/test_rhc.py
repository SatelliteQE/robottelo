"""Test class for RH Cloud connector - rhc

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RHCloud-CloudConnector

:Team: Platform

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from wait_for import wait_for

from robottelo import constants
from robottelo.utils.issue_handlers import is_open


@pytest.fixture(scope='module')
def fixture_enable_rhc_repos(module_target_sat):
    """Enable repos required for configuring RHC."""
    # subscribe rhc satellite to cdn.
    module_target_sat.register_to_cdn()
    if module_target_sat.os_version.major == 8:
        module_target_sat.enable_repo(constants.REPOS['rhel8_bos']['id'])
        module_target_sat.enable_repo(constants.REPOS['rhel8_aps']['id'])
    else:
        module_target_sat.enable_repo(constants.REPOS['rhscl7']['id'])
        module_target_sat.enable_repo(constants.REPOS['rhel7']['id'])


@pytest.fixture(scope='module')
def module_rhc_org(module_target_sat, module_org):
    """Module level fixture for creating organization"""
    # adding remote_execution_connect_by_ip=Yes at org level
    module_target_sat.api.Parameter(
        name='remote_execution_connect_by_ip',
        value='Yes',
        parameter_type='boolean',
        organization=module_org.id,
    ).create()
    return module_org


@pytest.mark.e2e
@pytest.mark.tier3
def test_positive_configure_cloud_connector(
    module_target_sat, module_rhc_org, fixture_enable_rhc_repos
):
    """
    Enable RH Cloud Connector through API

    :id: 1338dc6a-12e0-4378-9a51-a33f4679ba30

    :Steps:

        1. Enable RH Cloud Connector
        2. Check if the task is completed successfully

    :expectedresults: The Cloud Connector has been installed and the service is running
    """

    # Delete old satellite  hostname if BZ#2130173 is open
    if is_open('BZ:2130173'):
        host = module_target_sat.api.Host().search(
            query={'search': f"! {module_target_sat.hostname}"}
        )[0]
        host.delete()

    # Copy foreman-proxy user's key to root@localhost user's authorized_keys
    module_target_sat.add_rex_key(satellite=module_target_sat)

    # Set Host parameter source_display_name to something random.
    # To avoid 'name has already been taken' error when run multiple times
    # on a machine with the same hostname.
    host = module_target_sat.api.Host().search(query={'search': module_target_sat.hostname})[0]
    parameters = [{'name': 'source_display_name', 'value': gen_string('alpha')}]
    host.host_parameters_attributes = parameters
    host.update(['host_parameters_attributes'])

    module_target_sat.api.RHCloud().enable_connector(data={'organization_id': module_rhc_org.id})

    template_name = 'Configure Cloud Connector'
    invocation_id = (
        module_target_sat.api.JobInvocation()
        .search(query={'search': f'description="{template_name}"'})[0]
        .id
    )
    wait_for(
        lambda: module_target_sat.api.JobInvocation(id=invocation_id).read().status_label
        in ["succeeded", "failed"],
        timeout="1500s",
    )

    job_output = module_target_sat.cli.JobInvocation.get_output(
        {'id': invocation_id, 'host': module_target_sat.hostname}
    )
    # if installation fails, it's often due to missing rhscl repo -> print enabled repos
    module_target_sat.execute('yum repolist')
    # get rhc status
    rhc_status = module_target_sat.execute('rhc status')
    # get rhcd log
    rhcd_log = module_target_sat.execute('journalctl --unit=rhcd')

    assert module_target_sat.api.JobInvocation(id=invocation_id).read().status == 0
    assert "Install yggdrasil-worker-forwarder and rhc" in job_output
    # assert "Restart rhcd" in job_output
    assert 'Exit status: 0' in job_output

    assert rhc_status.status == 0
    assert "Connected to Red Hat Subscription Management" in rhc_status.stdout
    assert "The Red Hat connector daemon is active" in rhc_status.stdout

    assert "error" not in rhcd_log.stdout
