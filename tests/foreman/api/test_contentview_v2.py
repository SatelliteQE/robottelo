"""Unit tests for the ``content_views`` paths.

A full API reference for content views can be found here:
http://theforeman.org/api/apidoc/v2/content_views.html

"""
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.common.helpers import get_server_credentials
from robottelo.common import decorators
from robottelo.factory import FactoryError
from robottelo import entities, orm
from unittest import TestCase
import ddt
# (too many public methods) pylint: disable=R0904


@ddt.ddt
class ContentViewTestCase(TestCase):
    """Tests for content views."""
    def test_subscribe_system_to_cv(self):
        """@Test: Subscribe a system to a content view.

        @Feature: ContentView

        @Assert: It is possible to create a system and set its
        'content_view_id' attribute.

        """
        # Create an organization, lifecycle environment and content view.
        organization = entities.Organization().create()
        lifecycle_environment = entities.LifecycleEnvironment(
            organization=organization['id']
        ).create()
        content_view = entities.ContentView(
            organization=organization['id']
        ).create()

        # Publish the newly created content view.
        response = entities.ContentView(id=content_view['id']).publish()
        self.assertEqual(
            u'success',
            entities.ForemanTask(id=response['id']).poll()['result']
        )

        # Fetch and promote the newly published content view version.
        content_view_version = client.get(
            entities.ContentViewVersion().path(),
            auth=get_server_credentials(),
            data={u'content_view_id': content_view['id']},
            verify=False,
        ).json()['results'][0]
        response = entities.ContentViewVersion(
            id=content_view_version['id']
        ).promote(environment_id=lifecycle_environment['id'])
        self.assertEqual(
            u'success',
            entities.ForemanTask(id=response['id']).poll()['result']
        )

        # Create a system that is subscribed to the published and promoted
        # content view. Associating this system with the organization and
        # environment created above is not particularly important, but doing so
        # means a shorter test where fewer entities are created, as
        # System.organization and System.environment are required attributes.
        system = entities.System(
            content_view=content_view['id'],
            environment=lifecycle_environment['id'],
            organization=organization['id'],
        ).create()

        # See bugzilla bug #1122267.
        self.assertEqual(
            system['content_view_id'],  # This is good.
            content_view['id']
        )
        self.assertEqual(
            system['environment']['id'],  # This is bad.
            lifecycle_environment['id']
        )
        # self.assertEqual(
        #     system['organization_id'],  # And this is unavailable.
        #     organization['id']
        # )

    def test_positive_create_1(self):
        """@Test: Create a composite content view.

        @Assert: Creation succeeds.

        @Feature: ContentView

        """
        content_view = entities.ContentView(
            id=entities.ContentView(composite=True).create()['id']
        )
        self.assertTrue(content_view.read_json()['composite'])

    @decorators.data('', ' ')
    def test_negative_create(self, name):
        """@Test: Create a content view and provide invalid attributes.

        @Assert: No content view is created.

        @Feature: ContentView

        """
        with self.assertRaises(FactoryError):
            entities.ContentView(name=name).create()


@ddt.ddt
class ContentViewUpdateTestCase(TestCase):
    """Tests for updating content views."""
    @classmethod
    def setUpClass(cls):
        """Create a content view."""
        cls.content_view = entities.ContentView(
            id=entities.ContentView().create()['id']
        )

    @decorators.data(
        {'name': entities.ContentView.name.get_value()},
        {'description': entities.ContentView.description.get_value()},
    )
    def test_positive_update(self, attrs):
        """@Test: Update a content view and provide valid attributes.

        @Assert: The update succeeds.

        @Feature: ContentView

        """
        client.put(
            self.content_view.path(),
            attrs,
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()

        # Read the content view and validate its attributes.
        new_attrs = self.content_view.read_json()
        for name, value in attrs.items():
            self.assertIn(name, new_attrs.keys())
            self.assertEqual(new_attrs[name], value)

    @decorators.data(
        {'label': entities.ContentView.label.get_value()},  # Immutable.
        {'name': orm.StringField(len=256).get_value()},
    )
    def test_negative_update(self, attrs):
        """@Test: Update a content view and provide an invalid attribute.

        @Assert: The content view's attributes are not updated.

        @Feature: ContentView

        """
        response = client.put(
            self.content_view.path(),
            attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        with self.assertRaises(HTTPError):
            response.raise_for_status()
