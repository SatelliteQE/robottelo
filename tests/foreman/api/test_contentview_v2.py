"""Unit tests for the ``content_views`` paths."""
from fauxfactory import gen_integer, gen_string, gen_utf8
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.common.helpers import get_server_credentials
from robottelo.common import decorators
from robottelo import entities
from unittest import TestCase
import ddt
# (too many public methods) pylint: disable=R0904


def _publish(content_view):
    """Publishes ``content_view`` and waits for it to finish.

    :param dict content_view: A dictionary representing a content view.
    :returns: A string representing the status of the publish action.
    :rtype: str

    """
    response = entities.ContentView(id=content_view['id']).publish()
    # FIXME: Update ``entities.ContentView.publish`` to automatically wait
    # for task to complete.
    return entities.ForemanTask(id=response['id']).poll()['result']


def _promote(content_view, lifecycle, version):
    """Promotes ``version`` of ``content_view`` to ``lifecycle`` and waits
    for it to finish.

    :param dict content_view: A dictionary representing a content view.
    :param dict lifecycle: A dictionaty representing a lifecycle environment.
    :param int version: Integer representing of version to publish.
    :returns: A string representing the status of the promote action.
    :rtype: str

    """
    # Re-fetch cotent view
    content_view = entities.ContentView(id=content_view['id']).read_json()
    # Promote it
    response = entities.ContentViewVersion(
        id=content_view['versions'][version]['id']).promote(lifecycle['id'])
    # FIXME: Update ``entities.ContentViewVersion.promote`` to automatically
    # wait for task to complete.
    return entities.ForemanTask(id=response['id']).poll()['result']


@decorators.run_only_on('sat')
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
        response = _publish(content_view)
        self.assertEqual(
            response,
            u'success',
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


@ddt.ddt
class ContentViewCreateTestCase(TestCase):
    """Tests for creating content views."""

    def test_positive_create_1(self):
        """@Test: Create an empty non-composite content view.

        @Assert: Creation succeeds and content-view is non-composite.

        @Feature: ContentView

        """
        content_view = entities.ContentView(
            id=entities.ContentView(composite=False).create()['id']
        )
        self.assertFalse(content_view.read_json()['composite'])

    def test_positive_create_2(self):
        """@Test: Create an empty composite content view.

        @Assert: Creation succeeds and content-view is composite.

        @Feature: ContentView

        """
        content_view = entities.ContentView(
            id=entities.ContentView(composite=True).create()['id']
        )
        self.assertTrue(content_view.read_json()['composite'])

    @decorators.data(
        gen_string('alpha', gen_integer(3, 30)),
        gen_string('alphanumeric', gen_integer(3, 30)),
        gen_string('cjk', gen_integer(3, 30)),
        gen_string('html', gen_integer(3, 30)),
        gen_string('latin1', gen_integer(3, 30)),
        gen_string('numeric', gen_integer(3, 30)),
        gen_string('utf8', gen_integer(3, 30)),
    )
    def test_positive_create_3(self, name):
        """@Test: Create empty content-view with random names.

        @Assert: Content-view is created and had random name.

        @Feature: ContentView

        """
        content_view = entities.ContentView(
            name=name
        ).create()['id']
        attrs = entities.ContentView(id=content_view).read_json()
        self.assertEqual(attrs['name'], name)

    @decorators.data(
        gen_string('alpha', gen_integer(3, 30)),
        gen_string('alphanumeric', gen_integer(3, 30)),
        gen_string('cjk', gen_integer(3, 30)),
        gen_string('html', gen_integer(3, 30)),
        gen_string('latin1', gen_integer(3, 30)),
        gen_string('numeric', gen_integer(3, 30)),
        gen_string('utf8', gen_integer(3, 30)),
    )
    def test_positive_create_4(self, description):
        """@Test: Create empty content view with random description.

        @Assert: Content-view is created and has random description.

        @Feature: ContentView

        """
        content_view = entities.ContentView(
            description=description
        ).create()['id']
        attrs = entities.ContentView(id=content_view).read_json()
        self.assertEqual(attrs['description'], description)


@ddt.ddt
class ContentViewPublishTestCase(TestCase):
    """Tests for publishing content views."""

    def test_positive_publish_1(self):
        """@Test: Publish empty content view once.

        @Assert: Content-view is published and has 1 version.

        @Feature: ContentView

        """
        content_view = entities.ContentView(
            id=entities.ContentView().create()['id'])
        # Publish it
        response = _publish(content_view)
        self.assertEqual(response, u'success')

        # Assert that it only has 1 version, present in one environment
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            1,
            u'There should only be 1 version published.')
        self.assertEqual(
            len(content_view['versions'][0]['environment_ids']),
            1,
            u"Content view should be present in 1 lifecycle only")

    def test_positive_publish_2(self):
        """@Test: Publish empty content view random times.

        @Assert: Content-view is published n-times and has n versions.

        @Feature: ContentView

        """
        content_view = entities.ContentView(
            id=entities.ContentView().create()['id'])
        # Publish it random times
        repeat = gen_integer(2, 5)
        for _ in range(0, repeat):
            response = _publish(content_view)
            self.assertEqual(response, u'success')

        # Assert that it only has 1 version, present in one environment
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            repeat,
            u'Did not publish {0} times.'.format(repeat))
        # Last published version should be listed in lifecycle
        self.assertEqual(
            len(content_view['versions'][repeat - 1]['environment_ids']),
            1,
            u"Content view should be present in 1 lifecycle only")


@ddt.ddt
class ContentViewPromoteTestCase(TestCase):
    """Tests for promoting content views."""

    def test_positive_promote_1(self):
        """@Test: Publish and promote empty content view once.

        @Assert: Content-view is published, has 1 version and was promoted
        to Library + 1 environment.

        @Feature: ContentView

        """
        org = entities.Organization(
            id=entities.Organization().create()['id']
        )
        lifecycle = entities.LifecycleEnvironment(
            organization=org['id']
        ).create()
        content_view = entities.ContentView(organization=org['id']).create()
        # Publish it
        response = _publish(content_view)
        self.assertEqual(response, u'success')

        # Assert that it only has 1 version, present in one environment
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(len(content_view['versions']), 1)
        self.assertEqual(
            len(content_view['versions'][0]['environment_ids']),
            1,
            u"Content view should be present in 1 lifecycle only")
        # Promote it to lifecycle
        response = _promote(content_view, lifecycle, 0)
        self.assertEqual(response, u'success')

        # Check that content view exists in 2 lifecycles
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            1,
            u'There should only be 1 version published.')
        self.assertEqual(
            len(content_view['versions'][0]['environment_ids']),
            2,
            u"Content view should be present on 2 lifecycles only")

    def test_positive_promote_2(self):
        """@Test: Publish and promote empty content view random times.

        @Assert: Content-view is published n-times, has n versions and was
        promoted to Library + random > 1 environments.

        @Feature: ContentView

        """
        org = entities.Organization(
            id=entities.Organization().create()['id']
        )
        content_view = entities.ContentView(organization=org['id']).create()
        # Publish it random times
        repeat = gen_integer(2, 5)
        for _ in range(0, repeat):
            response = _publish(content_view)
            self.assertEqual(response, u'success')

        # Promote it to random lifecycle
        for _ in range(0, repeat):
            # Create new lifecycle environment
            lifecycle = entities.LifecycleEnvironment(
                organization=org['id']
            ).create()
            # Promote
            response = _promote(content_view, lifecycle, repeat - 1)
            self.assertEqual(response, u'success')

        # Check that content view exists in all lifecycles
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            repeat,
            u'There should only be 1 version published.')
        self.assertEqual(
            len(content_view['versions'][repeat - 1]['environment_ids']),
            repeat + 1,
            u"Content view should be present on 2 lifecycles only")


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
        {u'name': entities.ContentView.name.get_value()},
        {u'description': entities.ContentView.description.get_value()},
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
        {u'label': gen_utf8(30), u'bz-bug': 1147100},  # Immutable.
        {u'name': gen_utf8(256)},
    )
    def test_negative_update_1(self, attrs):
        """@Test: Update a content view and provide an invalid attribute.

        @Assert: The content view's attributes are not updated.

        @Feature: ContentView

        """
        bug_id = attrs.pop('bz-bug', None)
        if bug_id is not None and decorators.bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        response = client.put(
            self.content_view.path(),
            attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        with self.assertRaises(HTTPError):
            response.raise_for_status()
