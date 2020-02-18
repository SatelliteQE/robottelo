"""Unit tests for the ``activation_keys`` paths.

:Requirement: Activationkey

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ActivationKeys

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_integer
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities
from requests.exceptions import HTTPError
from six.moves import http_client

from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.datafactory import filtered_datapoint
from robottelo.datafactory import invalid_names_list
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import stubbed
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.helpers import get_nailgun_config
from robottelo.test import APITestCase


@filtered_datapoint
def _good_max_hosts():
    """Return a list of valid ``max_hosts`` values."""
    return [gen_integer(*limits) for limits in ((1, 20), (10000, 20000))]


@filtered_datapoint
def _bad_max_hosts():
    """Return a list of invalid ``max_hosts`` values."""
    return [gen_integer(-100, -1), 0, gen_string('alpha')]


class ActivationKeyTestCase(APITestCase):
    """Tests for the ``activation_keys`` path."""

    @tier1
    def test_positive_create_unlimited_hosts(self):
        """Create a plain vanilla activation key.

        :id: 1d73b8cc-a754-4637-8bae-d9d2aaf89003

        :expectedresults: Check that activation key is created and its
            "unlimited_hosts" attribute defaults to true.

        :CaseImportance: Critical
        """
        self.assertTrue(entities.ActivationKey().create().unlimited_hosts)

    @tier1
    def test_positive_create_limited_hosts(self):
        """Create an activation key with limited hosts.

        :id: 9bbba620-fd98-4139-a44b-af8ce330c7a4

        :expectedresults: Check that activation key is created and that hosts
            number is limited

        :CaseImportance: Critical
        """
        for max_host in _good_max_hosts():
            with self.subTest(max_host):
                act_key = entities.ActivationKey(
                    max_hosts=max_host, unlimited_hosts=False
                ).create()
                self.assertEqual(act_key.max_hosts, max_host)
                self.assertFalse(act_key.unlimited_hosts)

    @tier1
    def test_positive_create_with_name(self):
        """Create an activation key providing the initial name.

        :id: 749e0d28-640e-41e5-89d6-b92411ce73a3

        :expectedresults: Activation key is created and contains provided name.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                act_key = entities.ActivationKey(name=name).create()
                self.assertEqual(name, act_key.name)

    @tier2
    def test_positive_create_with_description(self):
        """Create an activation key and provide a description.

        :id: 64d93726-6f96-4a2e-ab29-eb5bfa2ff8ff

        :expectedresults: Created entity contains the provided description.

        :CaseImportance: High
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                act_key = entities.ActivationKey(description=desc).create()
                self.assertEqual(desc, act_key.description)

    @tier2
    def test_negative_create_with_no_host_limit(self):
        """Create activation key without providing limitation for hosts number

        :id: a9e756e1-886d-4f0d-b685-36ce4247517d

        :expectedresults: Activation key is not created

        :CaseImportance: Critical
        """
        with self.assertRaises(HTTPError):
            entities.ActivationKey(unlimited_hosts=False).create()

    @tier3
    def test_negative_create_with_invalid_host_limit(self):
        """Create activation key with invalid limit values for hosts number.

        :id: c018b177-2074-4f1a-a7e0-9f38d6c9a1a6

        :expectedresults: Activation key is not created

        :CaseImportance: Low
        """
        for max_host in _bad_max_hosts():
            with self.subTest(max_host):
                with self.assertRaises(HTTPError):
                    entities.ActivationKey(max_hosts=max_host, unlimited_hosts=False).create()

    @tier3
    def test_negative_create_with_invalid_name(self):
        """Create activation key providing an invalid name.

        :id: 5f7051be-0320-4d37-9085-6904025ad909

        :expectedresults: Activation key is not created

        :CaseImportance: Low
        """
        for name in invalid_names_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.ActivationKey(name=name).create()

    @tier2
    def test_positive_update_limited_host(self):
        """Create activation key then update it to limited hosts.

        :id: 34ca8303-8135-4694-9cf7-b20f8b4b0a1e

        :expectedresults: Activation key is created, updated to limited host

        :CaseImportance: High
        """
        # unlimited_hosts defaults to True.
        act_key = entities.ActivationKey().create()
        for max_host in _good_max_hosts():
            want = {'max_hosts': max_host, 'unlimited_hosts': False}
            for key, value in want.items():
                setattr(act_key, key, value)
            with self.subTest(want):
                act_key = act_key.update(want.keys())
                actual = {attr: getattr(act_key, attr) for attr in want.keys()}
                self.assertEqual(want, actual)

    @tier2
    def test_positive_update_name(self):
        """Create activation key providing the initial name, then update
        its name to another valid name.

        :id: f219f2dc-8759-43ab-a277-fbabede6795e

        :expectedresults: Activation key is created, and its name can be
            updated.

        :CaseImportance: High
        """
        act_key = entities.ActivationKey().create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                updated = entities.ActivationKey(id=act_key.id, name=new_name).update(['name'])
                self.assertEqual(new_name, updated.name)

    @tier3
    def test_negative_update_limit(self):
        """Create activation key then update its limit to invalid value.

        :id: 0f857d2f-81ed-4b8b-b26e-34b4f294edbc

        :expectedresults:

            1. Activation key is created
            2. Update fails
            3. Record is not changed

        :CaseImportance: Low
        """
        act_key = entities.ActivationKey().create()
        want = {'max_hosts': act_key.max_hosts, 'unlimited_hosts': act_key.unlimited_hosts}
        for max_host in _bad_max_hosts():
            with self.subTest(max_host):
                act_key.max_hosts = max_host
                act_key.unlimited_hosts = False
                with self.assertRaises(HTTPError):
                    act_key.update(want.keys())
                act_key = act_key.read()
                actual = {attr: getattr(act_key, attr) for attr in want.keys()}
                self.assertEqual(want, actual)

    @tier3
    def test_negative_update_name(self):
        """Create activation key then update its name to an invalid name.

        :id: da85a32c-942b-4ab8-a133-36b028208c4d

        :expectedresults: Activation key is created, and its name is not
            updated.

        :CaseImportance: Low
        """
        act_key = entities.ActivationKey().create()
        for new_name in invalid_names_list():
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    entities.ActivationKey(id=act_key.id, name=new_name).update(['name'])
                new_key = entities.ActivationKey(id=act_key.id).read()
                self.assertNotEqual(new_key.name, new_name)
                self.assertEqual(new_key.name, act_key.name)

    @tier3
    def test_negative_update_max_hosts(self):
        """Create an activation key with ``max_hosts == 1``, then update that
        field with a string value.

        :id: 3bcff792-105a-4577-b7c2-5b0de4f79c77

        :expectedresults: The update fails with an HTTP 422 return code.

        :CaseImportance: Low
        """
        act_key = entities.ActivationKey(max_hosts=1).create()
        with self.assertRaises(HTTPError):
            entities.ActivationKey(id=act_key.id, max_hosts='foo').update(['max_hosts'])
        self.assertEqual(act_key.read().max_hosts, 1)

    @tier2
    def test_positive_get_releases_status_code(self):
        """Get an activation key's releases. Check response format.

        :id: e1ea4797-8d92-4bec-ae6b-7a26599825ab

        :expectedresults: HTTP 200 is returned with an ``application/json``
            content-type

        :CaseLevel: Integration
        """
        act_key = entities.ActivationKey().create()
        path = act_key.path('releases')
        response = client.get(path, auth=settings.server.get_credentials(), verify=False)
        status_code = http_client.OK
        self.assertEqual(status_code, response.status_code)
        self.assertIn('application/json', response.headers['content-type'])

    @tier2
    def test_positive_get_releases_content(self):
        """Get an activation key's releases. Check response contents.

        :id: 2fec3d71-33e9-40e5-b934-90b03afc26a1

        :expectedresults: A list of results is returned.

        :CaseLevel: Integration
        """
        act_key = entities.ActivationKey().create()
        response = client.get(
            act_key.path('releases'), auth=settings.server.get_credentials(), verify=False
        ).json()
        self.assertIn('results', response.keys())
        self.assertEqual(type(response['results']), list)

    @tier2
    def test_positive_add_host_collections(self):
        """Associate an activation key with several host collections.

        :id: 1538808c-621e-4cf9-9b9b-840c5dd54644

        :expectedresults:

            1. By default, an activation key is associated with no host
               collections.
            2. After associating an activation key with some set of host
               collections and reading that activation key, the correct host
               collections are listed.

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org = entities.Organization().create()  # re-use this to speed up test

        # An activation key has no host collections by default.
        act_key = entities.ActivationKey(organization=org).create()
        self.assertEqual(len(act_key.host_collection), 0)

        # Give activation key one host collection.
        act_key.host_collection.append(entities.HostCollection(organization=org).create())
        act_key = act_key.update(['host_collection'])
        self.assertEqual(len(act_key.host_collection), 1)

        # Give activation key second host collection.
        act_key.host_collection.append(entities.HostCollection(organization=org).create())
        act_key = act_key.update(['host_collection'])
        self.assertEqual(len(act_key.host_collection), 2)

    @tier2
    @upgrade
    def test_positive_remove_host_collection(self):
        """Disassociate host collection from the activation key

        :id: 31992ac4-fe55-45bb-bd17-a191928ec2ab

        :expectedresults:

            1. By default, an activation key is associated with no host
               collections.
            2. Associating host collection with activation key add it to the
               list.
            3. Disassociating host collection from the activation key actually
               removes it from the list

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org = entities.Organization().create()

        # An activation key has no host collections by default.
        act_key = entities.ActivationKey(organization=org).create()
        self.assertEqual(len(act_key.host_collection), 0)

        host_collection = entities.HostCollection(organization=org).create()

        # Associate host collection with activation key.
        act_key.add_host_collection(data={'host_collection_ids': [host_collection.id]})
        self.assertEqual(len(act_key.read().host_collection), 1)

        # Disassociate host collection from the activation key.
        act_key.remove_host_collection(data={'host_collection_ids': [host_collection.id]})
        self.assertEqual(len(act_key.read().host_collection), 0)

    @tier1
    def test_positive_update_auto_attach(self):
        """Create an activation key, then update the auto_attach
        field with the inverse boolean value.

        :id: ec225dad-2d27-4b37-989d-1ba2c7f74ac4

        :expectedresults: The value is changed.

        :CaseImportance: Critical
        """
        act_key = entities.ActivationKey().create()
        act_key_2 = entities.ActivationKey(
            id=act_key.id, auto_attach=(not act_key.auto_attach)
        ).update(['auto_attach'])
        self.assertNotEqual(act_key.auto_attach, act_key_2.auto_attach)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create activation key and then delete it.

        :id: aa28d8fb-e07d-45fa-b43a-fc90c706d633

        :expectedresults: Activation key is successfully deleted.

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                act_key = entities.ActivationKey().create()
                act_key.delete()
                with self.assertRaises(HTTPError):
                    entities.ActivationKey(id=act_key.id).read()

    @tier2
    def test_positive_remove_user(self):
        """Delete any user who has previously created an activation key
        and check that activation key still exists

        :id: 02ce92d4-8f49-48a0-bf9e-5d401f84cf46

        :expectedresults: Activation Key can be read

        :BZ: 1291271
        """
        password = gen_string('alpha')
        user = entities.User(password=password, login=gen_string('alpha'), admin=True).create()
        cfg = get_nailgun_config()
        cfg.auth = (user.login, password)
        ak = entities.ActivationKey(cfg).create()
        user.delete()
        try:
            entities.ActivationKey(id=ak.id).read()
        except HTTPError:
            self.fail("Activation Key can't be read")

    @upgrade
    @run_in_one_thread
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_fetch_product_content(self):
        """Associate RH & custom product with AK and fetch AK's product content

        :id: 424f3dfb-0112-464b-b633-e8c9bce6e0f1

        :expectedresults: Both Red Hat and custom product subscriptions are
            assigned as Activation Key's product content

        :BZ: 1426386

        :CaseLevel: Integration

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
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
            product=entities.Product(organization=org).create()
        ).create()
        custom_repo.sync()
        cv = entities.ContentView(
            organization=org, repository=[rh_repo_id, custom_repo.id]
        ).create()
        cv.publish()
        ak = entities.ActivationKey(content_view=cv, organization=org).create()
        org_subscriptions = entities.Subscription(organization=org).search()
        for subscription in org_subscriptions:
            provided_products_ids = [prod.id for prod in subscription.read().provided_product]
            if (
                custom_repo.product.id in provided_products_ids
                or rh_repo.product.id in provided_products_ids
            ):
                ak.add_subscriptions(data={'quantity': 1, 'subscription_id': subscription.id})
        ak_subscriptions = ak.product_content()['results']
        self.assertEqual(
            {custom_repo.product.id, rh_repo.product.id},
            {subscr['product']['id'] for subscr in ak_subscriptions},
        )

    @upgrade
    @skip_if_not_set('fake_manifest')
    @tier2
    @stubbed()
    def test_positive_add_future_subscription(self):
        """Add a future-dated subscription to an activation key.

        :id: ee5debc7-f901-45ab-b55c-04d1a208c3e6

        :steps:

            1. Import a manifest that contains a future-dated subscription
            2. Add the subscription to the activation key

        :expectedresults: The future-dated sub is successfully added to the key

        :CaseAutomation: NotAutomated

        :CaseLevel: Integration

        :CaseImportance: Critical
        """


class ActivationKeySearchTestCase(APITestCase):
    """Tests that search for activation keys."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and an activation key belonging to it."""
        super(ActivationKeySearchTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.act_key = entities.ActivationKey(organization=cls.org).create()

    @tier1
    def test_positive_search_by_org(self):
        """Search for all activation keys in an organization.

        :id: aedba598-2e47-44a8-826c-4dc304ba00be

        :expectedresults: Only activation keys in the organization are
            returned.

        :CaseImportance: Critical
        """
        act_keys = entities.ActivationKey(organization=self.org).search()
        self.assertEqual(len(act_keys), 1)
        self.assertEqual(act_keys[0].id, self.act_key.id)
