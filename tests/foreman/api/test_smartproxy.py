"""Tests for the ``smart_proxies`` paths.

:Requirement: Smartproxy

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Capsule

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
from fauxfactory import gen_url
from nailgun import entities
from requests import HTTPError

from robottelo.api.utils import one_to_many_names
from robottelo.cleanup import capsule_cleanup
from robottelo.config import settings
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier1
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.helpers import default_url_on_new_port
from robottelo.helpers import get_available_capsule_port
from robottelo.test import APITestCase


@run_in_one_thread
class CapsuleTestCase(APITestCase):
    """Tests for Smart Proxy (Capsule) entity."""

    def _create_smart_proxy(self, **kwargs):
        """Create a Smart Proxy and register the cleanup function"""
        proxy = entities.SmartProxy(**kwargs).create()
        # Add proxy id to cleanup list
        self.addCleanup(capsule_cleanup, proxy.id)
        return proxy

    @skip_if_not_set('fake_capsules')
    @tier1
    def test_negative_create_with_url(self):
        """Proxy creation with random URL

        :id: e48a6260-97e0-4234-a69c-77bbbcde85d6

        :expectedresults: Proxy is not created

        :CaseLevel: Component

        """
        # Create a random proxy
        with self.assertRaises(HTTPError) as context:
            entities.SmartProxy(url=gen_url(scheme='https')).create()
        self.assertRegexpMatches(context.exception.response.text, u'Unable to communicate')

    @skip_if_not_set('fake_capsules')
    @tier1
    def test_positive_create_with_name(self):
        """Proxy creation with valid name

        :id: 0ffe0dc5-675e-45f4-b7e1-a14d3dd81f6e

        :expectedresults: Proxy is created

        :CaseLevel: Component

        """
        for name in valid_data_list():
            with self.subTest(name):
                new_port = get_available_capsule_port()
                with default_url_on_new_port(9090, new_port) as url:
                    proxy = self._create_smart_proxy(name=name, url=url)
                    self.assertEquals(proxy.name, name)

    @skip_if_not_set('fake_capsules')
    @tier1
    @upgrade
    def test_positive_delete(self):
        """Proxy deletion

        :id: 872bf12e-736d-43d1-87cf-2923966b59d0

        :expectedresults: Proxy is deleted

        :CaseLevel: Component

        :BZ: 1398695
        """
        new_port = get_available_capsule_port()
        with default_url_on_new_port(9090, new_port) as url:
            proxy = entities.SmartProxy(url=url).create()
            proxy.delete()
        with self.assertRaises(HTTPError):
            proxy.read()

    @skip_if_not_set('fake_capsules')
    @tier1
    def test_positive_update_name(self):
        """Proxy name update

        :id: f279640e-d7e9-48a3-aed8-7bf406e9d6f2

        :expectedresults: Proxy has the name updated

        :CaseLevel: Component

        """
        new_port = get_available_capsule_port()
        with default_url_on_new_port(9090, new_port) as url:
            proxy = self._create_smart_proxy(url=url)
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    proxy.name = new_name
                    proxy = proxy.update(['name'])
                    self.assertEqual(proxy.name, new_name)

    @skip_if_not_set('fake_capsules')
    @tier1
    def test_positive_update_url(self):
        """Proxy url update

        :id: 0305fd54-4e0c-4dd9-a537-d342c3dc867e

        :expectedresults: Proxy has the url updated

        :CaseLevel: Component

        """
        # Create fake capsule
        port = get_available_capsule_port()
        with default_url_on_new_port(9090, port) as url:
            proxy = self._create_smart_proxy(url=url)
        # Open another tunnel to update url
        new_port = get_available_capsule_port()
        with default_url_on_new_port(9090, new_port) as url:
            proxy.url = url
            proxy = proxy.update(['url'])
            self.assertEqual(proxy.url, url)

    @skip_if_not_set('fake_capsules')
    @tier1
    def test_positive_update_organization(self):
        """Proxy name update with the home proxy

        :id: 62631275-7a92-4d34-a949-c56e0c4063f1

        :expectedresults: Proxy has the name updated

        :CaseLevel: Component

        """
        organizations = [entities.Organization().create() for _ in range(2)]
        newport = get_available_capsule_port()
        with default_url_on_new_port(9090, newport) as url:
            proxy = self._create_smart_proxy(url=url)
            proxy.organization = organizations
            proxy = proxy.update(['organization'])
            self.assertEqual(
                {org.id for org in proxy.organization}, {org.id for org in organizations}
            )

    @skip_if_not_set('fake_capsules')
    @tier1
    def test_positive_update_location(self):
        """Proxy name update with the home proxy

        :id: e08eaaa9-7c11-4cda-bbe7-6d1f7c732569

        :expectedresults: Proxy has the name updated

        :CaseLevel: Component

        """
        locations = [entities.Location().create() for _ in range(2)]
        new_port = get_available_capsule_port()
        with default_url_on_new_port(9090, new_port) as url:
            proxy = self._create_smart_proxy(url=url)
            proxy.location = locations
            proxy = proxy.update(['location'])
            self.assertEqual({loc.id for loc in proxy.location}, {loc.id for loc in locations})

    @skip_if_not_set('fake_capsules')
    @tier2
    @upgrade
    def test_positive_refresh_features(self):
        """Refresh smart proxy features, search for proxy by id

        :id: d0237546-702e-4d1a-9212-8391295174da

        :expectedresults: Proxy features are refreshed

        :CaseLevel: Integration

        """
        # Since we want to run multiple commands against our fake capsule, we
        # need the tunnel kept open in order not to allow different concurrent
        # test to claim it. Thus we want to manage the tunnel manually.

        # get an available port for our fake capsule
        new_port = get_available_capsule_port()
        with default_url_on_new_port(9090, new_port) as url:
            proxy = self._create_smart_proxy(url=url)
            proxy.refresh()

    @skip_if_not_set('fake_capsules')
    @tier2
    def test_positive_import_puppet_classes(self):
        """Import puppet classes from proxy

        :id: 385efd1b-6146-47bf-babf-0127ce5955ed

        :expectedresults: Puppet classes are imported from proxy

        :CaseLevel: Integration

        :BZ: 1398695
        """
        new_port = get_available_capsule_port()
        with default_url_on_new_port(9090, new_port) as url:
            proxy = self._create_smart_proxy(url=url)
            result = proxy.import_puppetclasses()
            self.assertEqual(
                result['message'],
                "Successfully updated environment and puppetclasses from "
                "the on-disk puppet installation",
            )


@run_in_one_thread
class SmartProxyMissingAttrTestCase(APITestCase):
    """Tests to see if the server returns the attributes it should.

    Satellite should return a full description of an entity each time an entity
    is created, read or updated. These tests verify that certain attributes
    really are returned. The ``one_to_*_names`` functions know what names
    Satellite may assign to fields.
    """

    @classmethod
    def setUpClass(cls):
        """Find a ``SmartProxy``.

        Every Satellite has a built-in smart proxy, so searching for an
        existing smart proxy should always succeed.
        """
        super(SmartProxyMissingAttrTestCase, cls).setUpClass()
        smart_proxy = entities.SmartProxy().search(
            query={'search': 'url = https://{0}:9090'.format(settings.server.hostname)}
        )
        # Check that proxy is found and unpack it from the list
        assert len(smart_proxy) > 0, "No smart proxy is found"
        smart_proxy = smart_proxy[0]
        cls.smart_proxy_attrs = set(smart_proxy.update_json([]).keys())

    @tier1
    def test_positive_update_loc(self):
        """Update a smart proxy. Inspect the server's response.

        :id: 42d6b749-c047-4fd2-90ee-ffab7be558f9

        :expectedresults: The response contains some value for the ``location``
            field.

        :BZ: 1262037

        :CaseImportance: High

        :CaseLevel: Component

        """
        names = one_to_many_names('location')
        self.assertGreaterEqual(
            len(names & self.smart_proxy_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.smart_proxy_attrs),
        )

    @tier1
    def test_positive_update_org(self):
        """Update a smart proxy. Inspect the server's response.

        :id: fbde9f87-33db-4b95-a5f7-71a618460c84

        :expectedresults: The response contains some value for the
            ``organization`` field.

        :BZ: 1262037

        :CaseImportance: High

        :CaseLevel: Component

        """
        names = one_to_many_names('organization')
        self.assertGreaterEqual(
            len(names & self.smart_proxy_attrs),
            1,
            'None of {0} are in {1}'.format(names, self.smart_proxy_attrs),
        )
