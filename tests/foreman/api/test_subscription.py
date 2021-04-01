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

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import upload_manifest
from robottelo.cli.subscription import Subscription
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.decorators import skip_if_not_set
from robottelo.test import APITestCase
from robottelo.test import settings


@pytest.fixture(scope='class')
def golden_ticket_host_setup(request):
    org = entities.Organization().create()
    with manifests.clone(name='golden_ticket') as manifest:
        upload_manifest(org.id, manifest.content)
    rh_repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=org.id,
        product=PRDS['rhel'],
        repo=REPOS['rhst7']['name'],
        reposet=REPOSET['rhst7'],
        releasever=None,
    )
    rh_repo = entities.Repository(id=rh_repo_id).read()
    rh_repo.sync()
    custom_repo = entities.Repository(
        product=entities.Product(organization=org).create(),
    ).create()
    custom_repo.sync()
    ak = entities.ActivationKey(
        content_view=org.default_content_view,
        max_hosts=100,
        organization=org,
        environment=entities.LifecycleEnvironment(id=org.library.id),
        auto_attach=True,
    ).create()
    request.cls.org_setup = org
    request.cls.ak_setup = ak


@pytest.mark.run_in_one_thread
class SubscriptionsTestCase(APITestCase):
    """Tests for the ``subscriptions`` path."""

    @skip_if_not_set('fake_manifest')
    @pytest.mark.tier1
    def test_positive_create(self):
        """Upload a manifest.

        :id: 6faf9d96-9b45-4bdc-afa9-ec3fbae83d41

        :expectedresults: Manifest is uploaded successfully

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)

    @skip_if_not_set('fake_manifest')
    @pytest.mark.tier1
    def test_positive_refresh(self):
        """Upload a manifest and refresh it afterwards.

        :id: cd195db6-e81b-42cb-a28d-ec0eb8a53341

        :expectedresults: Manifest is refreshed successfully

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with manifests.original_manifest() as manifest:
            upload_manifest(org.id, manifest.content)
        try:
            sub.refresh_manifest(data={'organization_id': org.id})
            assert len(sub.search()) > 0
        finally:
            sub.delete_manifest(data={'organization_id': org.id})

    @skip_if_not_set('fake_manifest')
    @pytest.mark.tier1
    def test_positive_create_after_refresh(self):
        """Upload a manifest,refresh it and upload a new manifest to an other
         organization.

        :id: 1869bbb6-c31b-49a9-bc92-402a90071a11

        :customerscenario: true

        :expectedresults: the manifest is uploaded successfully to other org

        :BZ: 1393442

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        org_sub = entities.Subscription(organization=org)
        new_org = entities.Organization().create()
        new_org_sub = entities.Subscription(organization=new_org)
        self.upload_manifest(org.id, manifests.original_manifest())
        try:
            org_sub.refresh_manifest(data={'organization_id': org.id})
            assert len(org_sub.search()) > 0
            self.upload_manifest(new_org.id, manifests.clone())
            assert len(new_org_sub.search()) > 0
        finally:
            org_sub.delete_manifest(data={'organization_id': org.id})

    @skip_if_not_set('fake_manifest')
    @pytest.mark.tier1
    def test_positive_delete(self):
        """Delete an Uploaded manifest.

        :id: 4c21c7c9-2b26-4a65-a304-b978d5ba34fc

        :expectedresults: Manifest is Deleted successfully

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        assert len(sub.search()) > 0
        sub.delete_manifest(data={'organization_id': org.id})
        assert len(sub.search()) == 0

    @skip_if_not_set('fake_manifest')
    @pytest.mark.tier2
    def test_negative_upload(self):
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
    def test_positive_delete_manifest_as_another_user(self):
        """Verify that uploaded manifest if visible and deletable
            by a different user than the one who uploaded it

        :id: 4861bdbc-785a-436d-98cf-13cfef7d6907

        :expectedresults: manifest is refreshed

        :BZ: 1669241

        :CaseImportance: Medium
        """
        org = entities.Organization().create()
        user1_password = gen_string('alphanumeric')
        user1 = entities.User(
            admin=True, password=user1_password, organization=[org], default_organization=org
        ).create()
        sc1 = ServerConfig(
            auth=(user1.login, user1_password),
            url=f'https://{settings.server.hostname}',
            verify=False,
        )
        user2_password = gen_string('alphanumeric')
        user2 = entities.User(
            admin=True, password=user2_password, organization=[org], default_organization=org
        ).create()
        sc2 = ServerConfig(
            auth=(user2.login, user2_password),
            url=f'https://{settings.server.hostname}',
            verify=False,
        )
        # use the first admin to upload a manifest
        with manifests.clone() as manifest:
            entities.Subscription(sc1, organization=org).upload(
                data={'organization_id': org.id}, files={'content': manifest.content}
            )
        # try to search and delete the manifest with another admin
        entities.Subscription(sc2, organization=org).delete_manifest(
            data={'organization_id': org.id}
        )
        assert len(Subscription.list({'organization-id': org.id})) == 0

    @pytest.mark.tier2
    @pytest.mark.usefixtures("golden_ticket_host_setup")
    @pytest.mark.usefixtures("rhel77_contenthost_class")
    def test_positive_subscription_status_disabled(self):
        """Verify that Content host Subscription status is set to 'Disabled'
         for a golden ticket manifest

        :id: d7d7e20a-e386-43d5-9619-da933aa06694

        :expectedresults: subscription status is 'Disabled'

        :BZ: 1789924

        :CaseImportance: Medium
        """
        self.content_host.install_katello_ca()
        self.content_host.register_contenthost(self.org_setup.label, self.ak_setup.name)
        assert self.content_host.subscribed
        host = entities.Host().search(query={'search': f'name={self.content_host.hostname}'})
        host_id = host[0].id
        host_content = entities.Host(id=host_id).read_raw().content
        assert 'Simple Content Access' in str(host_content)


@pytest.mark.tier2
def test_positive_candlepin_events_processed_by_STOMP(rhel7_contenthost):
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
    org = entities.Organization().create()
    repo = entities.Repository(product=entities.Product(organization=org).create()).create()
    repo.sync()
    ak = entities.ActivationKey(
        content_view=org.default_content_view,
        max_hosts=100,
        organization=org,
        environment=entities.LifecycleEnvironment(id=org.library.id),
        auto_attach=True,
    ).create()
    rhel7_contenthost.install_katello_ca()
    rhel7_contenthost.register_contenthost(org.name, ak.name)
    host = entities.Host().search(query={'search': f'name={rhel7_contenthost.hostname}'})
    host_id = host[0].id
    host_content = entities.Host(id=host_id).read_json()
    assert host_content["subscription_status"] == 2
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    subscription = entities.Subscription(organization=org).search(
        query={'search': f'name="{DEFAULT_SUBSCRIPTION_NAME}"'}
    )[0]
    entities.HostSubscription(host=host_id).add_subscriptions(
        data={'subscriptions': [{'id': subscription.cp_id, 'quantity': 1}]}
    )
    host_content = entities.Host(id=host_id).read_json()
    assert host_content["subscription_status"] == 0
    response = entities.Ping().search_json()["services"]["candlepin_events"]
    assert response["status"] == "ok"
    assert "0 Failed" in response["message"]
