"""Unit tests for the ``subscription`` paths.

A full API reference for subscriptions can be found here:
https://<sat6.com>/apidoc/v2/subscriptions.html


:Requirement: Subscription

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: SubscriptionManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import entities
from nailgun.config import ServerConfig
from nailgun.entity_mixins import TaskFailedError

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.cli.subscription import Subscription
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.test import APITestCase
from robottelo.test import settings
from robottelo.vm import VirtualMachine


@run_in_one_thread
class SubscriptionsTestCase(APITestCase):
    """Tests for the ``subscriptions`` path."""

    @skip_if_not_set('fake_manifest')
    @tier1
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
    @tier1
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
            self.assertGreater(len(sub.search()), 0)
        finally:
            sub.delete_manifest(data={'organization_id': org.id})

    @skip_if_not_set('fake_manifest')
    @tier1
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
            self.assertGreater(len(org_sub.search()), 0)
            self.upload_manifest(new_org.id, manifests.clone())
            self.assertGreater(len(new_org_sub.search()), 0)
        finally:
            org_sub.delete_manifest(data={'organization_id': org.id})

    @skip_if_not_set('fake_manifest')
    @tier1
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
        self.assertGreater(len(sub.search()), 0)
        sub.delete_manifest(data={'organization_id': org.id})
        self.assertEqual(len(sub.search()), 0)

    @skip_if_not_set('fake_manifest')
    @tier2
    def test_negative_upload(self):
        """Upload the same manifest to two organizations.

        :id: 60ca078d-cfaf-402e-b0db-34d8901449fe

        :expectedresults: The manifest is not uploaded to the second
            organization.
        """
        orgs = [entities.Organization().create() for _ in range(2)]
        with manifests.clone() as manifest:
            upload_manifest(orgs[0].id, manifest.content)
            with self.assertRaises(TaskFailedError):
                upload_manifest(orgs[1].id, manifest.content)
        self.assertEqual(len(entities.Subscription(organization=orgs[1]).search()), 0)

    @tier2
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
            url='https://{}'.format(settings.server.hostname),
            verify=False,
        )
        user2_password = gen_string('alphanumeric')
        user2 = entities.User(
            admin=True, password=user2_password, organization=[org], default_organization=org
        ).create()
        sc2 = ServerConfig(
            auth=(user2.login, user2_password),
            url='https://{}'.format(settings.server.hostname),
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
        self.assertEquals(0, len(Subscription.list({'organization-id': org.id})))

    @tier2
    def test_positive_subscription_status_disabled(self):
        """Verify that Content host Subscription status is 'Unknown Subscription Status'
         for a golden ticket manifest

        :id: d7d7e20a-e386-43d5-9619-da933aa06694

        :expectedresults: subscription status is 'Unknown Subscription Status'

        :BZ: 1789924

        :CaseImportance: Medium
        """
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
        lce = entities.LifecycleEnvironment(organization=org).create()
        cv = entities.ContentView(
            organization=org, repository=[rh_repo_id, custom_repo.id],
        ).create()
        cv.publish()
        cvv = cv.read().version[0].read()
        promote(cvv, lce.id)
        ak = entities.ActivationKey(
            content_view=cv, max_hosts=100, organization=org, environment=lce, auto_attach=True
        ).create()
        subscription = entities.Subscription(organization=org).search(
            query={'search': 'name="{}"'.format(DEFAULT_SUBSCRIPTION_NAME)}
        )[0]
        ak.add_subscriptions(data={'quantity': 1, 'subscription_id': subscription.id})
        with VirtualMachine(distro=DISTRO_RHEL7) as vm:
            vm.install_katello_ca()
            vm.register_contenthost(org.label, ak.name)
            assert vm.subscribed
            host = entities.Host().search(query={'search': 'name={}'.format(vm.hostname)})
            host_id = host[0].id
            host_content = entities.Host(id=host_id).read_raw().content
            assert "Unknown subscription status" in str(host_content)
