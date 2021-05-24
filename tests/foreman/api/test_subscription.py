"""Unit tests for the ``subscription`` paths.

A full API reference for subscriptions can be found here:
https://<sat6.com>/apidoc/v2/subscriptions.html


:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: SubscriptionManagement

:Assignee: chiggins

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities
from nailgun.config import ServerConfig
from nailgun.entity_mixins import TaskFailedError
from requests.exceptions import HTTPError

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import upload_manifest
from robottelo.cli.subscription import Subscription
from robottelo.config import settings
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET


pytestmark = [pytest.mark.run_in_one_thread]


@pytest.fixture(scope='module')
def rh_repo(module_org):
    with manifests.clone(name='golden_ticket') as manifest:
        upload_manifest(module_org.id, manifest.content)
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    return rh_repo


@pytest.fixture(scope='module')
def custom_repo(rh_repo, module_org):
    custom_repo = entities.Repository(
        product=entities.Product(organization=module_org).create(),
    ).create()
    custom_repo.sync()
    return custom_repo


@pytest.fixture(scope='module')
def module_ak(module_org, rh_repo, custom_repo):
    """rh_repo and custom_repo are included here to ensure their execution before the AK"""
    module_ak = entities.ActivationKey(
        content_view=module_org.default_content_view,
        max_hosts=100,
        organization=module_org,
        environment=entities.LifecycleEnvironment(id=module_org.library.id),
        auto_attach=True,
    ).create()
    return module_ak


@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier1
def test_positive_create():
    """Upload a manifest.

    :id: 6faf9d96-9b45-4bdc-afa9-ec3fbae83d41

    :expectedresults: Manifest is uploaded successfully

    :CaseImportance: Critical
    """
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)


@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier1
def test_positive_refresh(request):
    """Upload a manifest and refresh it afterwards.

    :id: cd195db6-e81b-42cb-a28d-ec0eb8a53341

    :expectedresults: Manifest is refreshed successfully

    :CaseImportance: Critical
    """
    org = entities.Organization().create()
    sub = entities.Subscription(organization=org)
    with manifests.original_manifest() as manifest:
        upload_manifest(org.id, manifest.content)
    request.addfinalizer(lambda: sub.delete_manifest(data={'organization_id': org.id}))
    sub.refresh_manifest(data={'organization_id': org.id})
    assert sub.search()


@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier1
def test_positive_create_after_refresh(function_org):
    """Upload a manifest,refresh it and upload a new manifest to an other
     organization.

    :id: 1869bbb6-c31b-49a9-bc92-402a90071a11

    :customerscenario: true

    :expectedresults: the manifest is uploaded successfully to other org

    :BZ: 1393442

    :CaseImportance: Critical
    """
    org_sub = entities.Subscription(organization=function_org)
    new_org = entities.Organization().create()
    new_org_sub = entities.Subscription(organization=new_org)
    upload_manifest(function_org.id, manifests.original_manifest().content)
    try:
        org_sub.refresh_manifest(data={'organization_id': function_org.id})
        assert org_sub.search()
        upload_manifest(new_org.id, manifests.clone().content)
        assert new_org_sub.search()
    finally:
        org_sub.delete_manifest(data={'organization_id': function_org.id})


@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier1
def test_positive_delete(function_org):
    """Delete an Uploaded manifest.

    :id: 4c21c7c9-2b26-4a65-a304-b978d5ba34fc

    :expectedresults: Manifest is Deleted successfully

    :CaseImportance: Critical
    """
    sub = entities.Subscription(organization=function_org)
    with manifests.clone() as manifest:
        upload_manifest(function_org.id, manifest.content)
    assert sub.search()
    sub.delete_manifest(data={'organization_id': function_org.id})
    assert len(sub.search()) == 0


@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
def test_negative_upload():
    """Upload the same manifest to two organizations.

    :id: 60ca078d-cfaf-402e-b0db-34d8901449fe

    :expectedresults: The manifest is not uploaded to the second
        organization.
    """
    orgs = [entities.Organization().create() for _ in range(2)]
    with manifests.clone() as manifest:
        upload_manifest(orgs[0].id, manifest.content)
        with pytest.raises(TaskFailedError):
            upload_manifest(orgs[1].id, manifest.content)
    assert len(entities.Subscription(organization=orgs[1]).search()) == 0


@pytest.mark.tier2
def test_positive_delete_manifest_as_another_user(function_org):
    """Verify that uploaded manifest if visible and deletable
        by a different user than the one who uploaded it

    :id: 4861bdbc-785a-436d-98cf-13cfef7d6907

    :expectedresults: manifest is refreshed

    :BZ: 1669241

    :CaseImportance: Medium
    """
    user1_password = gen_string('alphanumeric')
    user1 = entities.User(
        admin=True,
        password=user1_password,
        organization=[function_org],
        default_organization=function_org,
    ).create()
    sc1 = ServerConfig(
        auth=(user1.login, user1_password),
        url=f'https://{settings.server.hostname}',
        verify=False,
    )
    user2_password = gen_string('alphanumeric')
    user2 = entities.User(
        admin=True,
        password=user2_password,
        organization=[function_org],
        default_organization=function_org,
    ).create()
    sc2 = ServerConfig(
        auth=(user2.login, user2_password),
        url=f'https://{settings.server.hostname}',
        verify=False,
    )
    # use the first admin to upload a manifest
    with manifests.clone() as manifest:
        entities.Subscription(sc1, organization=function_org).upload(
            data={'organization_id': function_org.id}, files={'content': manifest.content}
        )
    # try to search and delete the manifest with another admin
    entities.Subscription(sc2, organization=function_org).delete_manifest(
        data={'organization_id': function_org.id}
    )
    assert len(Subscription.list({'organization-id': function_org.id})) == 0


@pytest.mark.tier2
def test_positive_subscription_status_disabled(module_ak, rhel7_contenthost, module_org):
    """Verify that Content host Subscription status is set to 'Disabled'
     for a golden ticket manifest

    :id: d7d7e20a-e386-43d5-9619-da933aa06694

    :expectedresults: subscription status is 'Disabled'

    :BZ: 1789924

    :CaseImportance: Medium
    """
    rhel7_contenthost.install_katello_ca()
    rhel7_contenthost.register_contenthost(module_org.label, module_ak.name)
    assert rhel7_contenthost.subscribed
    host_content = entities.Host(id=rhel7_contenthost.nailgun_host.id).read_raw().content
    assert 'Simple Content Access' in str(host_content)


@pytest.mark.tier2
def test_sca_end_to_end(module_ak, rhel7_contenthost, module_org, rh_repo, custom_repo):
    """Perform end to end testing for Simple Content Access Mode

    :id: c6c4b68c-a506-46c9-bd1d-22e4c1926ef8

    :BZ: 1890643, 1890661, 1890664

    :expectedresults: All tests pass and clients have access
        to repos without needing to add subscriptions

    :CaseImportance: Critical
    """
    rhel7_contenthost.install_katello_ca()
    rhel7_contenthost.register_contenthost(module_org.label, module_ak.name)
    assert rhel7_contenthost.subscribed
    # Check to see if Organization is in SCA Mode
    assert entities.Organization(id=module_org.id).read().simple_content_access is True
    # Verify that you cannot attach a subscription to an activation key in SCA Mode
    subscription = entities.Subscription(organization=module_org).search(
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
    content_view = entities.ContentView(organization=module_org).create()
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
def test_positive_candlepin_events_processed_by_stomp(rhel7_contenthost, function_org):
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
    rhel7_contenthost.install_katello_ca()
    rhel7_contenthost.register_contenthost(function_org.name, ak.name)
    host = entities.Host().search(query={'search': f'name={rhel7_contenthost.hostname}'})
    host_id = host[0].id
    host_content = entities.Host(id=host_id).read_json()
    assert host_content['subscription_status'] == 2
    with manifests.clone() as manifest:
        upload_manifest(function_org.id, manifest.content)
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


def test_positive_expired_SCA_cert_handling(module_org, rhel7_contenthost):
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
<<<<<<< HEAD
    
=======

>>>>>>> 35823aa12 (Add ':CustomerScenario: true' token)
    :Assignee: dsynk

    :BZ: 1949353

    :CaseImportance: High
    """
    with manifests.clone(name='golden_ticket') as manifest:
        upload_manifest(module_org.id, manifest.content)
    ak = entities.ActivationKey(
        content_view=module_org.default_content_view,
        max_hosts=100,
        organization=module_org,
        environment=entities.LifecycleEnvironment(id=module_org.library.id),
        auto_attach=True,
    ).create()
    # registering the content host with no content enabled/synced in the org
    # should create a client SCA cert with no content
    rhel7_contenthost.install_katello_ca()
    rhel7_contenthost.register_contenthost(org=module_org.label, activation_key=ak.name)
    assert rhel7_contenthost.subscribed
    rhel7_contenthost.unregister()
    # syncing content with the content host unregistered should invalidate
    # the previous client SCA cert
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    # re-registering the host should test whether Candlepin gracefully handles
    # registration of a host with an expired SCA cert
    rhel7_contenthost.register_contenthost(module_org.label, ak.name)
    assert rhel7_contenthost.subscribed
