"""Unit tests for the ``subscription`` paths.

A full API reference for subscriptions can be found here:
https://<sat6.com>/apidoc/v2/subscriptions.html


:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: SubscriptionManagement

:team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from manifester import Manifester
from nailgun import entities
from nailgun.config import ServerConfig
from nailgun.entity_mixins import TaskFailedError
from requests.exceptions import HTTPError

from robottelo.cli.subscription import Subscription
from robottelo.config import settings
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET


pytestmark = [pytest.mark.run_in_one_thread]


@pytest.fixture(scope='module')
def rh_repo(module_sca_manifest_org, module_target_sat):
    rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_sca_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    return rh_repo


@pytest.fixture(scope='module')
def custom_repo(rh_repo, module_sca_manifest_org):
    custom_repo = entities.Repository(
        product=entities.Product(organization=module_sca_manifest_org).create(),
    ).create()
    custom_repo.sync()
    return custom_repo


@pytest.fixture(scope='module')
def module_ak(module_sca_manifest_org, rh_repo, custom_repo):
    """rh_repo and custom_repo are included here to ensure their execution before the AK"""
    module_ak = entities.ActivationKey(
        content_view=module_sca_manifest_org.default_content_view,
        max_hosts=100,
        organization=module_sca_manifest_org,
        environment=entities.LifecycleEnvironment(id=module_sca_manifest_org.library.id),
        auto_attach=True,
    ).create()
    return module_ak


@pytest.fixture(scope='function')
def duplicate_manifest():
    """Provides a function-scoped manifest that can be used alongside function_entitlement_manifest
    when two manifests are required in a single test"""
    with Manifester(manifest_category=settings.manifest.entitlement) as manifest:
        yield manifest


@pytest.mark.tier1
@pytest.mark.pit_server
def test_positive_create(module_entitlement_manifest, module_target_sat):
    """Upload a manifest.

    :id: 6faf9d96-9b45-4bdc-afa9-ec3fbae83d41

    :expectedresults: Manifest is uploaded successfully

    :CaseImportance: Critical
    """
    org = entities.Organization().create()
    module_target_sat.upload_manifest(org.id, module_entitlement_manifest.content)


@pytest.mark.tier1
def test_positive_refresh(function_entitlement_manifest_org, request):
    """Upload a manifest and refresh it afterwards.

    :id: cd195db6-e81b-42cb-a28d-ec0eb8a53341

    :expectedresults: Manifest is refreshed successfully

    :CaseImportance: Critical
    """
    org = function_entitlement_manifest_org
    sub = entities.Subscription(organization=org)
    request.addfinalizer(lambda: sub.delete_manifest(data={'organization_id': org.id}))
    sub.refresh_manifest(data={'organization_id': org.id})
    assert sub.search()


@pytest.mark.tier1
def test_positive_create_after_refresh(
    function_entitlement_manifest_org, duplicate_manifest, target_sat
):
    """Upload a manifest,refresh it and upload a new manifest to an other
     organization.

    :id: 1869bbb6-c31b-49a9-bc92-402a90071a11

    :customerscenario: true

    :expectedresults: the manifest is uploaded successfully to other org

    :BZ: 1393442

    :CaseImportance: Critical
    """
    org_sub = entities.Subscription(organization=function_entitlement_manifest_org)
    new_org = entities.Organization().create()
    new_org_sub = entities.Subscription(organization=new_org)
    try:
        org_sub.refresh_manifest(data={'organization_id': function_entitlement_manifest_org.id})
        assert org_sub.search()
        target_sat.upload_manifest(new_org.id, duplicate_manifest.content)
        assert new_org_sub.search()
    finally:
        org_sub.delete_manifest(data={'organization_id': function_entitlement_manifest_org.id})


@pytest.mark.tier1
def test_positive_delete(function_entitlement_manifest_org):
    """Delete an Uploaded manifest.

    :id: 4c21c7c9-2b26-4a65-a304-b978d5ba34fc

    :expectedresults: Manifest is Deleted successfully

    :CaseImportance: Critical
    """
    sub = entities.Subscription(organization=function_entitlement_manifest_org)
    assert sub.search()
    sub.delete_manifest(data={'organization_id': function_entitlement_manifest_org.id})
    assert len(sub.search()) == 0


@pytest.mark.tier2
def test_negative_upload(function_entitlement_manifest, target_sat):
    """Upload the same manifest to two organizations.

    :id: 60ca078d-cfaf-402e-b0db-34d8901449fe

    :expectedresults: The manifest is not uploaded to the second
        organization.
    """
    orgs = [entities.Organization().create() for _ in range(2)]
    with function_entitlement_manifest as manifest:
        target_sat.upload_manifest(orgs[0].id, manifest.content)
        with pytest.raises(TaskFailedError):
            target_sat.upload_manifest(orgs[1].id, manifest.content)
    assert len(entities.Subscription(organization=orgs[1]).search()) == 0


@pytest.mark.tier2
def test_positive_delete_manifest_as_another_user(
    function_org, function_entitlement_manifest, target_sat
):
    """Verify that uploaded manifest if visible and deletable
        by a different user than the one who uploaded it

    :id: 4861bdbc-785a-436d-98cf-13cfef7d6907

    :expectedresults: manifest is refreshed

    :customerscenario: true

    :BZ: 1669241

    :CaseImportance: Medium
    """
    user1_password = gen_string('alphanumeric')
    user1 = target_sat.api.User(
        admin=True,
        password=user1_password,
        organization=[function_org],
        default_organization=function_org,
    ).create()
    sc1 = ServerConfig(
        auth=(user1.login, user1_password),
        url=target_sat.url,
        verify=False,
    )
    user2_password = gen_string('alphanumeric')
    user2 = target_sat.api.User(
        admin=True,
        password=user2_password,
        organization=[function_org],
        default_organization=function_org,
    ).create()
    sc2 = ServerConfig(
        auth=(user2.login, user2_password),
        url=target_sat.url,
        verify=False,
    )
    # use the first admin to upload a manifest
    with function_entitlement_manifest as manifest:
        entities.Subscription(sc1, organization=function_org).upload(
            data={'organization_id': function_org.id}, files={'content': manifest.content}
        )
    # try to search and delete the manifest with another admin
    entities.Subscription(sc2, organization=function_org).delete_manifest(
        data={'organization_id': function_org.id}
    )
    assert len(Subscription.list({'organization-id': function_org.id})) == 0


@pytest.mark.tier2
def test_positive_subscription_status_disabled(
    module_ak, rhel_contenthost, module_sca_manifest_org, target_sat
):
    """Verify that Content host Subscription status is set to 'Disabled'
     for a golden ticket manifest

    :id: d7d7e20a-e386-43d5-9619-da933aa06694

    :expectedresults: subscription status is 'Disabled'

    :customerscenario: true

    :BZ: 1789924

    :CaseImportance: Medium
    """
    rhel_contenthost.install_katello_ca(target_sat)
    rhel_contenthost.register_contenthost(module_sca_manifest_org.label, module_ak.name)
    assert rhel_contenthost.subscribed
    host_content = entities.Host(id=rhel_contenthost.nailgun_host.id).read_raw().content
    assert 'Simple Content Access' in str(host_content)


@pytest.mark.tier2
@pytest.mark.e2e
@pytest.mark.pit_client
@pytest.mark.pit_server
def test_sca_end_to_end(
    module_ak, rhel7_contenthost, module_sca_manifest_org, rh_repo, custom_repo, target_sat
):
    """Perform end to end testing for Simple Content Access Mode

    :id: c6c4b68c-a506-46c9-bd1d-22e4c1926ef8

    :BZ: 1890643, 1890661, 1890664

    :expectedresults: All tests pass and clients have access
        to repos without needing to add subscriptions

    :parametrized: yes

    :CaseImportance: Critical
    """
    rhel7_contenthost.install_katello_ca(target_sat)
    rhel7_contenthost.register_contenthost(module_sca_manifest_org.label, module_ak.name)
    assert rhel7_contenthost.subscribed
    # Check to see if Organization is in SCA Mode
    assert entities.Organization(id=module_sca_manifest_org.id).read().simple_content_access is True
    # Verify that you cannot attach a subscription to an activation key in SCA Mode
    subscription = entities.Subscription(organization=module_sca_manifest_org).search(
        query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    with pytest.raises(HTTPError) as ak_context:
        module_ak.add_subscriptions(data={'quantity': 1, 'subscription_id': subscription.id})
    assert 'Simple Content Access' in ak_context.value.response.text
    # Verify that you cannot attach a subscription to an Host in SCA Mode
    with pytest.raises(HTTPError) as host_context:
        entities.HostSubscription(host=rhel7_contenthost.nailgun_host.id).add_subscriptions(
            data={'subscriptions': [{'id': subscription.id, 'quantity': 1}]}
        )
    assert 'Simple Content Access' in host_context.value.response.text
    # Create a content view with repos and check to see that the client has access
    content_view = entities.ContentView(organization=module_sca_manifest_org).create()
    content_view.repository = [rh_repo, custom_repo]
    content_view.update(['repository'])
    content_view.publish()
    assert len(content_view.repository) == 2
    host = rhel7_contenthost.nailgun_host
    host.content_facet_attributes = {'content_view_id': content_view.id}
    host.update(['content_facet_attributes'])
    rhel7_contenthost.run('subscription-manager repos --enable *')
    repos = rhel7_contenthost.run('subscription-manager refresh && yum repolist')
    assert content_view.repository[1].name in repos.stdout
    assert 'Red Hat Satellite Tools' in repos.stdout
    # install package and verify it succeeds or is already installed
    package = rhel7_contenthost.run('yum install -y python-pulp-manifest')
    assert 'Complete!' in package.stdout or 'already installed' in package.stdout


@pytest.mark.tier2
def test_positive_candlepin_events_processed_by_stomp(
    rhel7_contenthost, function_entitlement_manifest, function_org, target_sat
):
    """Verify that Candlepin events are being read and processed by
        attaching subscriptions, validating host subscriptions status,
        and viewing processed and failed Candlepin events

    :id: efd20ffd-8f98-4536-abb6-d080f9d23169

    :steps:

        1. Add subscriptions to content host
        2. Verify subscription status is invalid at
            <your-satellite-url>/api/v2/hosts
        3. Import a Manifest
        4. Attach subs to content host
        5. Verify subscription status is valid
        6. Check ping api for processed and failed events
            /katello/api/v2/ping

    :expectedresults: Candlepin events are being read and processed
                        correctly without any failures
    :BZ: 1826515

    :parametrized: yes

    :CaseImportance: High
    """
    repo = entities.Repository(
        product=entities.Product(organization=function_org).create()
    ).create()
    repo.sync()
    ak = entities.ActivationKey(
        content_view=function_org.default_content_view,
        max_hosts=100,
        organization=function_org,
        environment=entities.LifecycleEnvironment(id=function_org.library.id),
        auto_attach=True,
    ).create()
    rhel7_contenthost.install_katello_ca(target_sat)
    rhel7_contenthost.register_contenthost(function_org.name, ak.name)
    host = entities.Host().search(query={'search': f'name={rhel7_contenthost.hostname}'})
    host_id = host[0].id
    host_content = entities.Host(id=host_id).read_json()
    assert host_content['subscription_status'] == 2
    with function_entitlement_manifest as manifest:
        target_sat.upload_manifest(function_org.id, manifest.content)
    subscription = entities.Subscription(organization=function_org).search(
        query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    entities.HostSubscription(host=host_id).add_subscriptions(
        data={'subscriptions': [{'id': subscription.cp_id, 'quantity': 1}]}
    )
    host_content = entities.Host(id=host_id).read_json()
    assert host_content['subscription_status'] == 0
    response = entities.Ping().search_json()['services']['candlepin_events']
    assert response['status'] == 'ok'
    assert '0 Failed' in response['message']


def test_positive_expired_SCA_cert_handling(module_sca_manifest_org, rhel7_contenthost, target_sat):
    """Verify that a content host with an expired SCA cert can
        re-register successfully

    :id: 27bca6b8-dd9c-4977-81d2-319588ee59b3

    :steps:

        1. Import an SCA-enabled manifest
        2. Register a content host to the Default Organization View using an activation key
        3. Unregister the content host
        4. Enable and synchronize a repository
        5. Re-register the host using the same activation key as in step 3 above

    :expectedresults: the host is re-registered successfully and its SCA entitlement
                      certificate is refreshed

    :CustomerScenario: true

    :team: Phoenix-subscriptions

    :BZ: 1949353

    :parametrized: yes

    :CaseImportance: High
    """
    ak = entities.ActivationKey(
        content_view=module_sca_manifest_org.default_content_view,
        max_hosts=100,
        organization=module_sca_manifest_org,
        environment=entities.LifecycleEnvironment(id=module_sca_manifest_org.library.id),
        auto_attach=True,
    ).create()
    # registering the content host with no content enabled/synced in the org
    # should create a client SCA cert with no content
    rhel7_contenthost.install_katello_ca(target_sat)
    rhel7_contenthost.register_contenthost(
        org=module_sca_manifest_org.label, activation_key=ak.name
    )
    assert rhel7_contenthost.subscribed
    rhel7_contenthost.unregister()
    # syncing content with the content host unregistered should invalidate
    # the previous client SCA cert
    rh_repo_id = target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_sca_manifest_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    # re-registering the host should test whether Candlepin gracefully handles
    # registration of a host with an expired SCA cert
    rhel7_contenthost.register_contenthost(module_sca_manifest_org.label, ak.name)
    assert rhel7_contenthost.subscribed


@pytest.mark.stubbed
@pytest.mark.tier2
def test_positive_os_restriction_on_repos():
    """Verify that you can specify OS restrictions on custom repos

    :id: fd40842f-48c3-4505-a670-235d8a5f466b

    :steps:
        1. Register Content Host with RHEL/EPEL 6 and 7 repos synced
        2. Set Restriction to OS on repos
        3. Subscription-manager refresh
        4. Verify enabled repos

    :expectedresults: Custom EPEL repos with OS restrictions set are
        disabled based on its corresponding RHEL version

    :customerscenario: true

    :BZ: 1526564

    :CaseImportance: High

    :CaseAutomation: NotAutomated
    """


def test_positive_async_endpoint_for_manifest_refresh(target_sat, module_entitlement_manifest_org):
    """Verify that manifest refresh is using an async endpoint. Previously this was a single,
    synchronous endpoint. The endpoint to retrieve manifests is now split into two: an async
    endpoint to start "exporting" the manifest, and a second endpoint to download the
    exported manifest.

    :id: c25c5290-44ae-4f56-82cf-d118fefeff86

    :steps:
        1. Refresh a manifest
        2. Check the production.log for "Sending GET request to upstream Candlepin"

    :expectedresults: Manifest refresh succeeds with no errors and production.log
        has new debug message

    :customerscenario: true

    :BZ: 2066323
    """
    sub = target_sat.api.Subscription(organization=module_entitlement_manifest_org)
    # set log level to 'debug' and restart services
    target_sat.cli.Admin.logging({'all': True, 'level-debug': True})
    target_sat.cli.Service.restart()
    # refresh manifest and assert new log message to confirm async endpoint
    sub.refresh_manifest(data={'organization_id': module_entitlement_manifest_org.id})
    results = target_sat.execute(
        'grep "Sending GET request to upstream Candlepin" /var/log/foreman/production.log'
    )
    assert 'Sending GET request to upstream Candlepin' in str(results)
    # set log level back to default
    target_sat.cli.Admin.logging({'all': True, 'level-production': True})
    target_sat.cli.Service.restart()
