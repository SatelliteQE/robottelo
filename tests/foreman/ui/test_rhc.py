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
from robottelo.config import settings
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.datafactory import gen_string
from robottelo.helpers import file_downloader
from robottelo.logging import logger


@pytest.fixture(scope='module')
def subscribe_rhc_satellite(clean_rhsm, module_target_sat):
    """subscribe rhc satellite to cdn"""
    if module_target_sat.os_version.major < 8:
        release_version = f'{module_target_sat.os_version.major}Server'
    else:
        release_version = f'{module_target_sat.os_version.major}'
    module_target_sat.register_contenthost(
        org=None,
        lce=None,
        username=settings.subscription.rhn_username,
        password=settings.subscription.rhn_password,
        releasever=release_version,
    )
    result = module_target_sat.subscription_manager_attach_pool([settings.subscription.rhn_poolid])[0]
    if 'Successfully attached a subscription' in result.stdout:
        # extras is not in RHEL8: https://access.redhat.com/solutions/5331391
        if module_target_sat.os_version.major < 8:
            module_target_sat.enable_repo(
                f'rhel-{module_target_sat.os_version.major}-server-extras-rpms', force=True
            )
        yield
    else:
        pytest.fail('Failed to attach system to pool. Aborting Test!.')


@pytest.fixture()
def fixture_enable_rhc_repos(module_target_sat):
    """Enable repos required for configuring RHC."""
    if module_target_sat.os_version.major == 8:
        module_target_sat.enable_repo(constants.REPOS['rhel8_bos']['id'])
        module_target_sat.enable_repo(constants.REPOS['rhel8_aps']['id'])
    else:
        module_target_sat.enable_repo(constants.REPOS['rhscl7']['id'])
        module_target_sat.enable_repo(constants.REPOS['rhel7']['id'])


@pytest.fixture(scope='module')
def module_rhc_org(module_target_sat):
    """Module level fixture for creating organization"""
    org = module_target_sat.api.Organization(
        name=gen_string('alpha')
        if not settings.rh_cloud.organization
        else settings.rh_cloud.organization
    ).create()
    # adding remote_execution_connect_by_ip=Yes at org level
    module_target_sat.api.Parameter(
        name='remote_execution_connect_by_ip',
        value='Yes',
        organization=org.id,
    ).create()
    return org


@pytest.fixture()
def fixture_setup_rhc_satellite(request, module_target_sat, module_rhc_org):
    """Create Organization and activation key after successful test execution"""
    yield
    if request.node.rep_call.passed:
        manifests_path = file_downloader(
            file_url=settings.fake_manifest.url['default'], hostname=module_target_sat.hostname
        )[0]
        module_target_sat.cli.Subscription.upload(
            {'file': manifests_path, 'organization-id': module_rhc_org.id}
        )
        # Create Activation key
        ak = module_target_sat.api.ActivationKey(
            name=gen_string('alpha')
            if not settings.rh_cloud.activation_key
            else settings.rh_cloud.activation_key,
            content_view=module_rhc_org.default_content_view,
            organization=module_rhc_org,
            environment=module_target_sat.api.LifecycleEnvironment(id=module_rhc_org.library.id),
            auto_attach=True,
        ).create()
        subscription = module_target_sat.api.Subscription(organization=module_rhc_org)
        default_subscription = subscription.search(
            query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
        )[0]
        ak.add_subscriptions(data={'quantity': 10, 'subscription_id': default_subscription.id})
        logger.debug(f"Activation key: {ak} \n Organization: {module_rhc_org}")


@pytest.mark.tier3
def test_positive_configure_cloud_connector(
    session,
    module_target_sat,
    subscribe_rhc_satellite,
    fixture_enable_rhc_repos,
    module_rhc_org,
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
    module_target_sat.add_rex_key(satellite=module_target_sat)

    # Set Host parameter source_display_name to something random.
    # To avoid 'name has already been taken' error when run multiple times
    # on a machine with the same hostname.
    host_id = module_target_sat.cli.Host.info({'name': module_target_sat.hostname})['id']
    module_target_sat.cli.Host.set_parameter(
        {'host-id': host_id, 'name': 'source_display_name', 'value': gen_string('alpha')}
    )

    with session:
        session.organization.select(org_name=module_rhc_org.name)
        if session.cloudinventory.is_cloud_connector_configured():
            pytest.skip(
                'Cloud Connector has already been configured on this system. '
                'It is possible to reconfigure it but then the test would not really '
                'check if everything is correctly configured from scratch. Skipping.'
            )
        session.cloudinventory.configure_cloud_connector()

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

    result = module_target_sat.cli.JobInvocation.get_output(
        {'id': invocation_id, 'host': module_target_sat.hostname}
    )
    logger.debug(f"Invocation output>>\n{result}\n<<End of invocation output")
    # if installation fails, it's often due to missing rhscl repo -> print enabled repos
    repolist = module_target_sat.execute('yum repolist')
    logger.debug(f"Repolist>>\n{repolist}\n<<End of repolist")
    assert module_target_sat.api.JobInvocation(id=invocation_id).read().status == 0
    assert "Install yggdrasil-worker-forwarder and rhc" in result
    assert "Restart rhcd" in result
    assert 'Exit status: 0' in result

    result = module_target_sat.execute('rhc status')
    logger.debug(f"rhc status>>\n{result}\n<<End of rhc status")
    assert result.status == 0
    assert "Connected to Red Hat Subscription Management" in result.stdout
    assert "The Red Hat connector daemon is active" in result.stdout

    result = module_target_sat.execute('journalctl --unit=rhcd')
    logger.debug(f"journalctl log>>\n{result}\n<<End of log")
    assert "error" not in result.stdout
