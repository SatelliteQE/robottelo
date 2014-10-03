"""Unit tests for the ``content_views`` paths."""
from fauxfactory import gen_integer, gen_string, gen_utf8
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.common.helpers import get_server_credentials
from robottelo.common import decorators
from robottelo import entities
from unittest import TestCase
import ddt
# (too-many-public-methods) pylint:disable=R0904


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


@decorators.run_only_on('sat')
class ContentViewTestCaseStub(TestCase):
    """Incomplete tests for content views."""
    # Each of these tests should be given a better name when they're
    # implemented. In the meantime, let's not worry about bad names.
    # (invalid-name) pylint:disable=C0103

    @decorators.stubbed
    def test_cv_edit_rh_custom_spin(self):
        """
        @test: edit content views for a custom rh spin.  For example,
        @feature: Content Views
        modify a filter
        @assert: edited content view save is successful and info is
        updated
        @status: Manual
        """
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.

    # Content Views: Adding products/repos
    # katello content definition add_filter --label=MyView
    #   --filter=stable --org=ACME
    # katello content definition add_product --label=MyView
    #   --product=product1 --org=ACME
    # katello content definition add_repo --label=MyView
    #   --repo=repo1 --org=ACME

    @decorators.stubbed
    def test_associate_view_rh(self):
        """
        @test: associate Red Hat content in a view
        @feature: Content Views
        @setup: Sync RH content
        @assert: RH Content can be seen in a view
        @status: Manual
        """

    @decorators.stubbed
    def test_associate_view_rh_custom_spin(self):
        """
        @test: associate Red Hat content in a view
        @feature: Content Views
        @setup: Sync RH content
        @steps: 1. Assure filter(s) applied to associated content
        @assert: Filtered RH content only is available/can be seen in a view
        @status: Manual
        """
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.

    @decorators.stubbed
    def test_associate_view_custom_content(self):
        """
        @test: associate Red Hat content in a view
        @feature: Content Views
        @setup: Sync custom content
        @assert: Custom content can be seen in a view
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_associate_puppet_repo_negative(self):
        """
        @test: attempt to associate puppet repos within a custom
        content view
        @feature: Content Views
        @assert: User cannot create a composite content view
        that contains direct puppet repos.
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_associate_components_composite_negative(self):
        """
        @test: attempt to associate components n a non-composite
        content view
        @feature: Content Views
        @assert: User cannot add components to the view
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_associate_composite_dupe_repos_negative(self):
        """
        @test: attempt to associate the same repo multiple times within a
        content view
        @feature: Content Views
        @assert: User cannot add repos multiple times to the view
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_associate_composite_dupe_modules_negative(self):
        """
        @test: attempt to associate duplicate puppet module(s) within a
        content view
        @feature: Content Views
        @assert: User cannot add modules multiple times to the view
        @status: Manual
        """

    # Content View: promotions
    # katello content view promote --label=MyView --env=Dev --org=ACME
    # katello content view promote --view=MyView --env=Staging --org=ACME

    @decorators.stubbed
    def test_cv_promote_rh(self):
        """
        @test: attempt to promote a content view containing RH content
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_promote_rh_custom_spin(self):
        """
        @test: attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_promote_custom_content(self):
        """
        @test: attempt to promote a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be promoted
        """
        # con_view = ApiCrud.record_create_recursive(ContentViewDefinition())
        # self.assertIntersects(data, con_view)
        # task = con_view._meta.api_class.publish(con_view)
        # task.poll(5, 100)  # poll every 5th second, max of 100 seconds
        # self.assertEqual('success', task.result())
        # published = ApiCrud.record_resolve(con_view)
        # env = EnvironmentKatello(organization=published.organization)
        # created_env = ApiCrud.record_create_recursive(env)
        # task2 = published._meta.api_class.promote(
        #     published.versions[0]['id'],
        #     created_env.id
        #     )
        # task2.poll(5, 100)  # poll every 5th second, max of 100 seconds
        # self.assertEqual('success', task2.result())

    @decorators.stubbed
    def test_cv_promote_composite(self):
        """
        @test: attempt to promote a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @steps: create a composite view containing multiple content types
        @assert: Content view can be promoted
        @status: Manual
        """
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.

    @decorators.stubbed
    def test_cv_promote_badid_negative(self):
        """
        @test: attempt to promote a content view using an invalid id
        @feature: Content Views
        @assert: Content views cannot be promoted; handled gracefully
        """
        # env = EnvironmentKatello()
        # created_env = ApiCrud.record_create_recursive(env)
        # task = ContentViewDefinition._meta.api_class.promote(
        #     1,
        #     created_env.id
        #     )
        # self.assertIn(
        #     'errors', task.json,
        #     "Invalid id shouldn't be promoted")

    # Content Views: publish
    # katello content definition publish --label=MyView

    @decorators.stubbed
    def test_cv_publish_rh(self, data):
        """
        @test: attempt to publish a content view containing RH content
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        """
        # See method test_subscribe_system_to_cv in module test_contentview_v2

    @decorators.stubbed
    def test_cv_publish_rh_custom_spin(self):
        """
        @test: attempt to publish  a content view containing a custom RH
        spin - i.e., contains filters.
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_publish_custom_content(self):
        """
        @test: attempt to publish a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be published
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_publish_composite(self):
        """
        @test: attempt to publish  a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be published
        @status: Manual
        """
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.

    @decorators.stubbed
    def test_cv_publish_badlabel_negative(self):
        """
        @test: attempt to publish a content view containing invalid strings
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view is not published; condition is handled
        gracefully;
        no tracebacks
        @status: Manual
        """
        # Variations might be:
        # zero length, too long, symbols, etc.

    @decorators.stubbed
    def test_cv_publish_version_changes_in_target_env(self):
        """
        @test: when publishing new version to environment, version
        gets updated
        @feature: Content Views
        @setup: Multiple environments for an org; multiple versions
        of a content view created/published
        @steps:
        1. publish a view to an environment noting the CV version
        2. edit and republish a new version of a CV
        @assert: Content view version is updated intarget environment.
        @status: Manual
        """
        # Dev notes:
        # If Dev has version x, then when I promote version y into
        # Dev, version x goes away (ie when I promote version 1 to Dev,
        # version 3 goes away)

    @decorators.stubbed
    def test_cv_publish_version_changes_in_source_env(self):
        """
        @test: when publishing new version to environment, version
        gets updated
        @feature: Content Views
        @setup: Multiple environments for an org; multiple versions
        of a content view created/published
        @steps:
        1. publish a view to an environment
        2. edit and republish a new version of a CV
        @assert: Content view version is updated in source environment.
        @status: Manual
        """
        # Dev notes:
        # Similarly when I publish version y, version x goes away from
        # Library (ie when I publish version 2, version 1 disappears)

    @decorators.stubbed
    def test_cv_clone_within_same_env(self):
        """
        @test: attempt to create new content view based on existing
        view within environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """
        # Dev note: "not implemented yet"

    @decorators.stubbed
    def test_cv_clone_within_diff_env(self):
        """
        @test: attempt to create new content view based on existing
        view, inside a different environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """
        # Dev note: "not implemented yet"

    @decorators.stubbed
    def test_cv_refresh_errata_to_new_view_in_same_env(self):
        """
        @test: attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_subscribe_system(self):
        """
        @test: attempt to  subscribe systems to content view(s)
        @feature: Content Views
        @assert: Systems can be subscribed to content view(s)
        @status: Manual
        """
        # Notes:
        # this should be limited to only those content views
        # to which you have permission, but there are/will be
        # other tests for that.
        # Variations:
        # * rh content
        # * rh custom spins
        # * custom content
        # * composite
        # * CVs with puppet modules

    @decorators.stubbed
    def test_custom_cv_subscribe_system(self):
        """
        @test: attempt to  subscribe systems to content view(s)
        @feature: Content Views
        @assert: Systems can be subscribed to content view(s)
        """
        # This test is implemented in tests/foreman/smoke/test_api_smoke.py.
        # See the end of method TestSmoke.test_smoke.

    @decorators.stubbed
    def test_cv_dynflow_restart_promote(self):
        """
        @test: attempt to restart a promotion
        @feature: Content Views
        @steps:
        1. (Somehow) cause a CV promotion to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart promotion
        @assert: Promotion is restarted.
        @status: Manual
        """

    @decorators.stubbed
    def test_cv_dynflow_restart_publish(self):
        """
        @test: attempt to restart a publish
        @feature: Content Views
        @steps:
        1. (Somehow) cause a CV publish  to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart publish
        @assert: Publish is restarted.
        @status: Manual
        """

    # ROLES TESTING
    # All this stuff is speculative at best.

    @decorators.stubbed
    def test_cv_roles_admin_user(self):
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user with the Content View admin role
        @assert: User with admin role for content view can perform all
        Variations above
        @status: Manual
        """
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user with admin permissions
        # for Content Views
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify, Delete, Promote Publish, Subscribe

    @decorators.stubbed
    def test_cv_roles_readonly_user(self):
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user with the Content View read-only role
        @assert: User with read-only role for content view can perform all
        Variations above
        @status: Manual
        """
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user with read-only permissions
        # for Content Views
        # THIS IS EVEN ASSUMING WE HAVE A "READ-ONLY" ROLE IN THE FIRST PLACE
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify,  Promote?, Publish?, Subscribe??

    @decorators.stubbed
    def test_cv_roles_admin_user_negative(self):
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user with the Content View admin role
        @assert: User withOUT admin role for content view canNOT perform any
        Variations above
        @status: Manual
        """
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user withOUT admin permissions
        # for Content Views
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify, Delete, Promote Publish, Subscribe

    @decorators.stubbed
    def test_cv_roles_readonly_user_negative(self):
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user withOUT the Content View read-only role
        @assert: User withOUT read-only role for content view can perform all
        Variations above
        @status: Manual
        """
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user withOUT read-only permissions
        # for Content Views
        # THIS IS EVEN ASSUMING WE HAVE A "READ-ONLY" ROLE IN THE FIRST PLACE
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify,  Promote?, Publish?, Subscribe??
