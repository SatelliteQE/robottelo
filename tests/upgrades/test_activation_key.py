"""Test Activation Key related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from nailgun import entities
from requests.exceptions import HTTPError
from robottelo.test import APITestCase
from upgrade_tests import pre_upgrade, post_upgrade


class scenario_positive_activation_key(APITestCase):
    """Activation key is intact post upgrade and verify activation key update/delete

    :steps:

        1. In Preupgrade Satellite, create activation key with different entities
        2. Upgrade the satellite to next/latest version
        3. Update existing activation key with different entities
        4. Postupgrade, Verify the activation key is intact, update and delete

    :expectedresults: Activation key should create, update and delete successfully.
    """
    @classmethod
    def setUpClass(cls):
        cls.ak_name = 'preupgrade_activation_key'
        cls.org_name = 'preupgrade_ak_org_name'
        cls.cv_name = 'preupgrade_ak_cv'

    @pre_upgrade
    def test_pre_create_activation_key(self):
        """Activation key with different entities are created

        :id: preupgrade-a7443b54-eb2e-497b-8a50-92abeae01496

        :steps: In Preupgrade Satellite, Create activation key with different entities.

        :expectedresults: Activation key should create successfully.
        """
        org = entities.Organization(name=self.org_name).create()
        custom_repo = entities.Repository(
            product=entities.Product(organization=org).create(),
        ).create()
        custom_repo.sync()
        cv = entities.ContentView(
            organization=org,
            repository=[custom_repo.id],
            name=self.cv_name
        ).create()
        cv.publish()
        ak = entities.ActivationKey(content_view=cv, organization=org, name=self.ak_name).create()
        org_subscriptions = entities.Subscription(organization=org).search()
        for subscription in org_subscriptions:
            ak.add_subscriptions(data={
                'quantity': 1,
                'subscription_id': subscription.id,
            })
        ak_subscriptions = ak.product_content()['results']
        self.assertEqual(
            {custom_repo.product.id},
            {subscr['product']['id'] for subscr in ak_subscriptions}
        )
        ak.host_collection.append(entities.HostCollection().create())
        ak.update(['host_collection'])
        self.assertEqual(len(ak.host_collection), 1)

    @post_upgrade
    def test_post_crud_activation_key(self):
        """Activation key is intact post upgrade and update/delete activation key works

        :id: postupgrade-a7443b54-eb2e-497b-8a50-92abeae01496

        :steps:

            1. Postupgrade, Verify activation key has same entities associated.
            2. Update existing activation key with new entities
            3. Delete activation key.

        :expectedresults: Activation key should update and delete successfully.
        """
        org = entities.Organization().search(query={
            'search': 'name={0}'.format(self.org_name)
        })
        ak = entities.ActivationKey(organization=org[0]).search(query={
            'search': 'name={0}'.format(self.ak_name)
        })
        cv = entities.ContentView(organization=org[0]).search(query={
            'search': 'name={0}'.format(self.cv_name)
        })

        # verify activation key is intact after upgrade
        self.assertEqual(self.ak_name, ak[0].name)
        self.assertEqual(self.cv_name, cv[0].name)

        # update activation key after upgrade
        ak[0].host_collection.append(entities.HostCollection().create())
        ak[0].update(['host_collection'])
        self.assertEqual(len(ak[0].host_collection), 2)
        custom_repo2 = entities.Repository(
            product=entities.Product(organization=org[0]).create(),
        ).create()
        custom_repo2.sync()
        cv2 = entities.ContentView(
            organization=org[0],
            repository=[custom_repo2.id]
        ).create()
        cv2.publish()
        org_subscriptions = entities.Subscription(organization=org[0]).search()
        for subscription in org_subscriptions:
            provided_products_ids = [
                prod.id for prod in subscription.read().provided_product]
            if custom_repo2.product.id in provided_products_ids:
                ak[0].add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': subscription.id,
                })
        ak_subscriptions = ak[0].product_content()['results']
        self.assertIn(
            custom_repo2.product.id,
            {subscr['product']['id'] for subscr in ak_subscriptions}
        )

        # Delete activation key
        ak[0].delete()
        with self.assertRaises(HTTPError):
            entities.ActivationKey(id=ak[0].id).read()
