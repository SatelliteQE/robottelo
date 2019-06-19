"""Unit tests for the ``organizations`` paths.

Each ``APITestCase`` subclass tests a single URL. A full list of URLs to be
tested can be found here:
http://theforeman.org/api/apidoc/v2/organizations.html


:Requirement: Organization

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: OrganizationsLocations

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_string
from nailgun import client, entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.constants import DEFAULT_ORG
from robottelo.datafactory import filtered_datapoint, invalid_values_list
from robottelo.decorators import tier1, tier2, upgrade
from robottelo.test import APITestCase
from six.moves import http_client


@filtered_datapoint
def valid_org_data_list():
    """List of valid data for input testing.

    Note: The maximum allowed length of org name is 242 only. This is an
    intended behavior (Also note that 255 is the standard across other
    entities.)
    """
    return [
        gen_string('alphanumeric', randint(1, 242)),
        gen_string('alpha', randint(1, 242)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 242)),
        gen_string('numeric', randint(1, 242)),
        gen_string('utf8', randint(1, 85)),
        gen_string('html', randint(1, 85)),
    ]


class OrganizationTestCase(APITestCase):
    """Tests for the ``organizations`` path."""

    @tier1
    def test_positive_create(self):
        """Create an organization using a 'text/plain' content-type.

        :id: 6f67a3f0-0c1d-498c-9a35-28207b0faec2

        :expectedresults: HTTP 415 is returned.

        :CaseImportance: Critical
        """
        organization = entities.Organization()
        organization.create_missing()
        response = client.post(
            organization.path(),
            organization.create_payload(),
            auth=settings.server.get_credentials(),
            headers={'content-type': 'text/plain'},
            verify=False,
        )
        self.assertEqual(
            http_client.UNSUPPORTED_MEDIA_TYPE, response.status_code)

    @tier1
    def test_positive_create_with_name_and_description(self):
        """Create an organization and provide a name and description.

        :id: afeea84b-61ca-40bf-bb16-476432919115

        :expectedresults: The organization has the provided attributes and an
            auto-generated label.

        :CaseImportance: Critical
        """
        for name in valid_org_data_list():
            with self.subTest(name):
                org = entities.Organization(
                    name=name,
                    description=name,
                ).create()
                self.assertEqual(org.name, name)
                self.assertEqual(org.description, name)

                # Was a label auto-generated?
                self.assertTrue(hasattr(org, 'label'))
                self.assertIsInstance(org.label, type(u''))
                self.assertGreater(len(org.label), 0)

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create an org with an incorrect name.

        :id: 9c6a4b45-a98a-4d76-9865-92d992fa1a22

        :expectedresults: The organization cannot be created.

        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Organization(name=name).create()

    @tier1
    def test_negative_create_with_same_name(self):
        """Create two organizations with identical names.

        :id: a0f5333c-cc83-403c-9bf7-08fb372909dc

        :expectedresults: The second organization cannot be created.

        :CaseImportance: Critical
        """
        name = entities.Organization().create().name
        with self.assertRaises(HTTPError):
            entities.Organization(name=name).create()

    @tier1
    def test_positive_search(self):
        """Create an organization, then search for it by name.

        :id: f6f1d839-21f2-4676-8683-9f899cbdec4c

        :expectedresults: Searching returns at least one result.

        :CaseImportance: Critical
        """
        org = entities.Organization().create()
        orgs = entities.Organization().search(
            query={u'search': u'name="{0}"'.format(org.name)}
        )
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0].id, org.id)
        self.assertEqual(orgs[0].name, org.name)

    @tier1
    def test_negative_create_with_wrong_path(self):
        """Attempt to create an organization using foreman API path
        (``api/v2/organizations``)

        :id: 499ae5ef-b1e4-4fb8-967a-57d525e06326

        :BZ: 1241068

        :expectedresults: API returns 404 error with 'Route overriden by
            Katello' message

        :CaseImportance: Critical
        """
        org = entities.Organization()
        org._meta['api_path'] = 'api/v2/organizations'
        with self.assertRaises(HTTPError) as err:
            org.create()
        self.assertEqual(err.exception.response.status_code, 404)
        self.assertIn(
            'Route overriden by Katello', err.exception.response.text)

    @tier2
    def test_default_org_id_check(self):
        """test to check the default_organization id

        :id: df066396-a069-4e9e-b3c1-c6d34a755ec0

        :BZ: 1713269

        :expectedresults: The default_organization ID remain 1.

        :CaseImportance: Low
        """
        default_org_id = entities.Organization().search(
            query={'search': 'name="{}"'.format(DEFAULT_ORG)})[0].id
        self.assertEqual(default_org_id, 1)


class OrganizationUpdateTestCase(APITestCase):
    """Tests for the ``organizations`` path."""

    @classmethod
    def setUpClass(cls):
        """Create an organization."""
        super(OrganizationUpdateTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @tier1
    def test_positive_update_name(self):
        """Update an organization's name with valid values.

        :id: 68f2ba13-2538-407c-9f33-2447fca28cd5

        :expectedresults: The organization's name is updated.

        :CaseImportance: Critical
        """
        for name in valid_org_data_list():
            with self.subTest(name):
                setattr(self.organization, 'name', name)
                self.organization = self.organization.update(['name'])
                self.assertEqual(self.organization.name, name)

    @tier1
    def test_positive_update_description(self):
        """Update an organization's description with valid values.

        :id: bd223197-1021-467e-8714-c1a767ae89af

        :expectedresults: The organization's description is updated.

        :CaseImportance: Critical
        """
        for desc in valid_org_data_list():
            with self.subTest(desc):
                setattr(self.organization, 'description', desc)
                self.organization = self.organization.update(['description'])
                self.assertEqual(self.organization.description, desc)

    @tier2
    def test_positive_update_user(self):
        """Update an organization, associate user with it.

        :id: 2c0c0061-5b4e-4007-9f54-b61d6e65ef58

        :expectedresults: User is associated with organization.

        :CaseLevel: Integration
        """
        user = entities.User().create()
        self.organization.user = [user]
        self.organization = self.organization.update(['user'])
        self.assertEqual(len(self.organization.user), 1)
        self.assertEqual(self.organization.user[0].id, user.id)

    @tier2
    def test_positive_update_subnet(self):
        """Update an organization, associate subnet with it.

        :id: 3aa0b9cb-37f7-4e7e-a6ec-c1b407225e54

        :expectedresults: Subnet is associated with organization.

        :CaseLevel: Integration
        """
        subnet = entities.Subnet().create()
        self.organization.subnet = [subnet]
        self.organization = self.organization.update(['subnet'])
        self.assertEqual(len(self.organization.subnet), 1)
        self.assertEqual(self.organization.subnet[0].id, subnet.id)

    @tier2
    def test_positive_add_and_remove_hostgroup(self):
        """Add a hostgroup to an organization and then remove it

        :id: 7eb1aca7-fd7b-404f-ab18-21be5052a11f

        :bz: 1395229

        :expectedresults: Hostgroup is added to organization and then removed

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        hostgroup = entities.HostGroup().create()
        org.hostgroup = [hostgroup]
        org = org.update(['hostgroup'])
        self.assertEqual(len(org.hostgroup), 1)
        org.hostgroup = []
        org = org.update(['hostgroup'])
        self.assertEqual(len(org.hostgroup), 0)

    @upgrade
    @tier2
    def test_positive_add_and_remove_smart_proxy(self):
        """Add a smart proxy to an organization

        :id: e21de720-3fa2-429b-bd8e-b6a48a13146d

        :expectedresults: Smart proxy is successfully added to organization

        :bz: 1395229

        :CaseLevel: Integration
        """
        # Every Satellite has a built-in smart proxy, so let's find it
        smart_proxy = entities.SmartProxy().search(query={
            'search': 'url = https://{0}:9090'.format(settings.server.hostname)
        })
        # Check that proxy is found and unpack it from the list
        self.assertGreater(len(smart_proxy), 0)
        smart_proxy = smart_proxy[0]
        # By default, newly created organization uses built-in smart proxy,
        # so we need to remove it first
        org = entities.Organization().create()
        org.smart_proxy = []
        org = org.update(['smart_proxy'])
        # Verify smart proxy was actually removed
        self.assertEqual(len(org.smart_proxy), 0)

        # Add smart proxy to organization
        org.smart_proxy = [smart_proxy]
        org = org.update(['smart_proxy'])
        # Verify smart proxy was actually added
        self.assertEqual(len(org.smart_proxy), 1)
        self.assertEqual(org.smart_proxy[0].id, smart_proxy.id)

        org.smart_proxy = []
        org = org.update(['smart_proxy'])
        # Verify smart proxy was actually removed
        self.assertEqual(len(org.smart_proxy), 0)

    @tier1
    def test_negative_update(self):
        """Update an organization's attributes with invalid values.

        :id: b7152d0b-5ab0-4d68-bfdf-f3eabcb5fbc6

        :expectedresults: The organization's attributes are not updated.

        :CaseImportance: Critical
        """
        dataset = (
            {'name': gen_string(str_type='utf8', length=256)},
            # Immutable. See BZ 1089996.
            {'label': gen_string(str_type='utf8')},
        )
        for attrs in dataset:
            with self.subTest(attrs):
                with self.assertRaises(HTTPError):
                    entities.Organization(
                        id=self.organization.id,
                        **attrs
                    ).update(attrs.keys())
