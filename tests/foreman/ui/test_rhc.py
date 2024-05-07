"""Test class for RH Cloud connector - rhc

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseComponent: RHCloud

:Team: Phoenix-subscriptions

:CaseImportance: High

"""

from datetime import datetime, timedelta

from fauxfactory import gen_string
from manifester import Manifester
import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.logging import logger
from robottelo.utils.issue_handlers import is_open


@pytest.fixture(scope='module')
def fixture_enable_rhc_repos(module_target_sat):
    """Enable repos required for configuring RHC."""
    # subscribe rhc satellite to cdn.
    if settings.rh_cloud.crc_env == 'prod':
        module_target_sat.register_to_cdn()
        if module_target_sat.os_version.major == 8:
            module_target_sat.enable_repo(constants.REPOS['rhel8_bos']['id'])
            module_target_sat.enable_repo(constants.REPOS['rhel8_aps']['id'])
        else:
            module_target_sat.enable_repo(constants.REPOS['rhscl7']['id'])
            module_target_sat.enable_repo(constants.REPOS['rhel7']['id'])


@pytest.fixture(scope='module')
def module_rhc_org(module_target_sat):
    """Module level fixture for creating organization"""
    if settings.rh_cloud.crc_env == 'prod':
        org = module_target_sat.api.Organization(
            name=settings.rh_cloud.organization or gen_string('alpha')
        ).create()
    else:
        org = (
            module_target_sat.api.Organization()
            .search(query={'search': f'name="{settings.rh_cloud.organization}"'})[0]
            .read()
        )

    # adding remote_execution_connect_by_ip=Yes at org level
    module_target_sat.api.Parameter(
        name='remote_execution_connect_by_ip',
        value='Yes',
        parameter_type='boolean',
        organization=org.id,
    ).create()
    return org


@pytest.fixture
def fixture_setup_rhc_satellite(
    request,
    module_target_sat,
    module_rhc_org,
):
    """Create Organization and activation key after successful test execution"""
    if settings.rh_cloud.crc_env == 'prod':
        manifester = Manifester(
            allocation_name=module_rhc_org.name,
            manifest_category=settings.manifest.extra_rhel_entitlement,
            simple_content_access="enabled",
        )
        rhcloud_manifest = manifester.get_manifest()
        module_target_sat.upload_manifest(module_rhc_org.id, rhcloud_manifest.content)
    yield
    if request.node.rep_call.passed:
        # Enable and sync required repos
        repo1_id = module_target_sat.api_factory.enable_sync_redhat_repo(
            constants.REPOS['rhel8_aps'], module_rhc_org.id
        )
        repo2_id = module_target_sat.api_factory.enable_sync_redhat_repo(
            constants.REPOS['rhel7'], module_rhc_org.id
        )
        repo3_id = module_target_sat.api_factory.enable_sync_redhat_repo(
            constants.REPOS['rhel8_bos'], module_rhc_org.id
        )
        # Add repos to Content view
        content_view = module_target_sat.api.ContentView(
            organization=module_rhc_org, repository=[repo1_id, repo2_id, repo3_id]
        ).create()
        content_view.publish()
        # Create Activation key
        ak = module_target_sat.api.ActivationKey(
            name=settings.rh_cloud.activation_key or gen_string('alpha'),
            content_view=content_view,
            organization=module_rhc_org,
            environment=module_target_sat.api.LifecycleEnvironment(id=module_rhc_org.library.id),
            auto_attach=True,
        ).create()
        logger.debug(
            f"Activation key: {ak} \n CV: {content_view} \n Organization: {module_rhc_org}"
        )


@pytest.mark.e2e
@pytest.mark.tier3
def test_positive_configure_cloud_connector(
    session,
    module_target_sat,
    fixture_enable_rhc_repos,
    module_rhc_org,
    fixture_setup_rhc_satellite,
):
    """Install Cloud Connector through WebUI button

    :id: 67e45cfe-31bb-51a8-b88f-27918c68f32e

    :steps:

        1. Navigate to Configure > Inventory Upload
        2. Click Configure Cloud Connector
        3. Open the started job and wait until it is finished

    :expectedresults: The Cloud Connector has been installed and the service is running

    :CaseImportance: Critical

    :BZ: 1818076
    """
    # Delete old satellite hostname if BZ#2130173 is open
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
    timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_rhc_org.name)
        if session.cloudinventory.is_cloud_connector_configured():
            pytest.skip(
                'Cloud Connector has already been configured on this system. '
                'It is possible to reconfigure it but then the test would not really '
                'check if everything is correctly configured from scratch. Skipping.'
            )
        session.cloudinventory.configure_cloud_connector()
    template_name = 'Configure Cloud Connector'
    module_target_sat.wait_for_tasks(
        search_query=(
            f'action = "Run hosts job: {template_name}"' f' and started_at >= "{timestamp}"'
        ),
        search_rate=15,
        max_tries=10,
    )
    invocation_id = (
        module_target_sat.api.JobInvocation()
        .search(query={'search': f'description="{template_name}"'})[0]
        .id
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
    assert "Restart rhcd" in job_output
    assert 'Exit status: 0' in job_output

    assert rhc_status.status == 0
    assert "Connected to Red Hat Subscription Management" in rhc_status.stdout
    assert "The Remote Host Configuration daemon is active" in rhc_status.stdout

    assert "error" not in rhcd_log.stdout
