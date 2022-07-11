"""Test class for RH Cloud connector - rhc

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RHCloud-CloudConnector

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from wait_for import wait_for

from robottelo import constants
from robottelo.api.utils import enable_sync_redhat_repo
from robottelo.config import settings
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.datafactory import gen_string
from robottelo.helpers import file_downloader
from robottelo.logging import logger


@pytest.fixture()
def fixture_enable_rhc_repos(target_sat):
    """Enable repos required for configuring RHC."""
    if target_sat.os_version.major == 8:
        target_sat.enable_repo(constants.REPOS['rhel8_bos']['id'])
        target_sat.enable_repo(constants.REPOS['rhel8_aps']['id'])
    else:
        target_sat.enable_repo(constants.REPOS['rhscl7']['id'])
        target_sat.enable_repo(constants.REPOS['rhel7']['id'])


@pytest.fixture()
def fixture_setup_rhc_satellite(request, target_sat, module_org):
    """Populate Satellite with repo, cv and ak after successful test execution"""
    yield
    if request.node.rep_call.passed:
        manifests_path = file_downloader(
            file_url=settings.fake_manifest.url['default'], hostname=target_sat.hostname
        )[0]
        target_sat.cli.Subscription.upload(
            {'file': manifests_path, 'organization-id': module_org.id}
        )
        rh_repo1 = {
            'name': constants.REPOS['rhel8_bos']['name'],
            'product': constants.PRDS['rhel8'],
            'reposet': constants.REPOSET['rhel8_bos'],
            'basearch': constants.DEFAULT_ARCHITECTURE,
            'releasever': '8',
        }
        rh_repo2 = {
            'name': constants.REPOS['rhel8_aps']['name'],
            'product': constants.PRDS['rhel8'],
            'reposet': constants.REPOSET['rhel8_aps'],
            'basearch': constants.DEFAULT_ARCHITECTURE,
            'releasever': '8',
        }
        rh_repo3 = {
            'name': constants.REPOS['rhscl7']['name'],
            'product': constants.PRDS['rhscl'],
            'reposet': constants.REPOSET['rhscl7'],
            'basearch': constants.DEFAULT_ARCHITECTURE,
            'releasever': '7Server',
        }
        rh_repo4 = {
            'name': constants.REPOS['rhel7']['name'],
            'product': constants.PRDS['rhel'],
            'reposet': constants.REPOSET['rhel7'],
            'basearch': constants.DEFAULT_ARCHITECTURE,
            'releasever': '7Server',
        }
        # Enable and sync required repos
        repo1_id = enable_sync_redhat_repo(rh_repo1, module_org.id)
        repo2_id = enable_sync_redhat_repo(rh_repo2, module_org.id)
        repo3_id = enable_sync_redhat_repo(rh_repo3, module_org.id)
        repo4_id = enable_sync_redhat_repo(rh_repo4, module_org.id)
        # Add repos to Content view
        cv = target_sat.api.ContentView(
            organization=module_org, repository=[repo1_id, repo2_id, repo3_id, repo4_id]
        ).create()
        cv.publish()
        # Create Activation key
        ak = target_sat.api.ActivationKey(content_view=cv, organization=module_org).create()
        subscription = target_sat.api.Subscription(organization=module_org)
        default_subscription = subscription.search(
            query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
        )[0]
        ak.add_subscriptions(data={'quantity': 10, 'subscription_id': default_subscription.id})
        logger.debug(f"Activation key: {ak} \n Content view: {cv} \n Organization: {module_org}")


@pytest.mark.tier3
def test_positive_configure_cloud_connector(
    session,
    target_sat,
    subscribe_satellite,
    fixture_enable_rhc_repos,
    module_org,
    fixture_setup_rhc_satellite,
):
    """Install Cloud Connector through WebUI button

    :id: 67e45cfe-31bb-51a8-b88f-27918c68f32e

    :Steps:

        1. Navigate to Configure > Inventory Upload
        2. Click Configure Cloud Connector
        3. Open the started job and wait until it is finished

    :expectedresults: The Cloud Connector has been installed and the service is running

    :CaseLevel: Integration

    :CaseImportance: Critical

    :BZ: 1818076
    """
    # Copy foreman-proxy user's key to root@localhost user's authorized_keys
    target_sat.add_rex_key(satellite=target_sat)

    # Set Host parameter source_display_name to something random.
    # To avoid 'name has already been taken' error when run multiple times
    # on a machine with the same hostname.
    host_id = target_sat.cli.Host.info({'name': target_sat.hostname})['id']
    target_sat.cli.Host.set_parameter(
        {'host-id': host_id, 'name': 'source_display_name', 'value': gen_string('alpha')}
    )

    with session:
        session.organization.select(org_name=module_org.name)
        if session.cloudinventory.is_cloud_connector_configured():
            pytest.skip(
                'Cloud Connector has already been configured on this system. '
                'It is possible to reconfigure it but then the test would not really '
                'check if everything is correctly configured from scratch. Skipping.'
            )
        session.cloudinventory.configure_cloud_connector()

    template_name = 'Configure Cloud Connector'
    invocation_id = (
        target_sat.api.JobInvocation()
        .search(query={'search': f'description="{template_name}"'})[0]
        .id
    )
    wait_for(
        lambda: target_sat.api.JobInvocation(id=invocation_id).read().status_label
        in ["succeeded", "failed"],
        timeout="1500s",
    )

    result = target_sat.cli.JobInvocation.get_output(
        {'id': invocation_id, 'host': target_sat.hostname}
    )
    logger.debug(f"Invocation output>>\n{result}\n<<End of invocation output")
    # if installation fails, it's often due to missing rhscl repo -> print enabled repos
    repolist = target_sat.execute('yum repolist')
    logger.debug(f"Repolist>>\n{repolist}\n<<End of repolist")
    assert target_sat.api.JobInvocation(id=invocation_id).read().status == 0
    assert "Install yggdrasil-worker-forwarder and rhc" in result
    assert "Restart rhcd" in result
    assert 'Exit status: 0' in result

    result = target_sat.execute('rhc status')
    logger.debug(f"rhc status>>\n{result}\n<<End of rhc status")
    assert result.status == 0
    assert "Connected to Red Hat Subscription Management" in result.stdout
    assert "The Red Hat connector daemon is active" in result.stdout

    result = target_sat.execute('journalctl --unit=rhcd')
    logger.debug(f"journalctl log>>\n{result}\n<<End of log")
    assert "error" not in result.stdout
