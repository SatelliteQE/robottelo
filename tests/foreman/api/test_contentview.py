# -*- encoding: utf-8 -*-
"""Unit tests for the ``content_views`` paths."""
from ddt import ddt
from fauxfactory import gen_integer, gen_string, gen_utf8
from nailgun import client
from requests.exceptions import HTTPError
from robottelo import entities
from robottelo.common.constants import PUPPET_MODULE_NTP_PUPPETLABS
from robottelo.common.decorators import (
    bz_bug_is_open, data, run_only_on, stubbed)
from robottelo.common.helpers import get_server_credentials
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


# Some tests repeatedly publish content views or promote content view versions.
# How many times should that be done? A higher number means a more interesting
# but longer test.
REPEAT = 3


@run_only_on('sat')
class ContentViewTestCase(APITestCase):
    """Tests for content views."""

    def test_subscribe_system_to_cv(self):
        """@Test: Subscribe a system to a content view.

        @Feature: ContentView

        @Assert: It is possible to create a system and set its
        'content_view_id' attribute.

        """
        # organization
        # ├── lifecycle environment
        # └── content view
        org = entities.Organization()
        org.id = org.create()['id']
        lifecycle_env = entities.LifecycleEnvironment(organization=org.id)
        lifecycle_env.id = lifecycle_env.create()['id']
        content_view = entities.ContentView(organization=org.id)
        content_view.id = content_view.create()['id']

        # Publish the content view.
        self.assertEqual('success', content_view.publish()['result'])

        # Get the content view version's ID.
        response = client.get(
            entities.ContentViewVersion().path(),
            auth=get_server_credentials(),
            data={u'content_view_id': content_view.id},
            verify=False,
        )
        response.raise_for_status()
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        cv_version = entities.ContentViewVersion(id=results[0]['id'])

        # Promote the content view version.
        self.assertEqual(
            'success',
            cv_version.promote(environment_id=lifecycle_env.id)['result']
        )

        # Create a system that is subscribed to the published and promoted
        # content view. Associating this system with the organization and
        # environment created above is not particularly important, but doing so
        # means a shorter test where fewer entities are created, as
        # System.organization and System.environment are required attributes.
        system_attrs = entities.System(
            content_view=content_view.id,
            environment=lifecycle_env.id,
            organization=org.id,
        ).create()

        # See BZ #1151240
        self.assertEqual(system_attrs['content_view_id'], content_view.id)
        self.assertEqual(system_attrs['environment']['id'], lifecycle_env.id)
        self.assertEqual(system_attrs['organization_id'], org.id)


@ddt
class ContentViewCreateTestCase(APITestCase):
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

    @data(
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

    @data(
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


class CVPublishPromoteTestCase(APITestCase):
    """Tests for publishing and promoting content views."""

    @classmethod
    def setUpClass(cls):
        """Set up organization, product and repositories for tests."""
        super(CVPublishPromoteTestCase, cls).setUpClass()

        cls.org = entities.Organization()
        cls.org.id = cls.org.create_json()['id']

        cls.product = entities.Product(organization=cls.org.id)
        cls.product.id = cls.product.create_json()['id']

        cls.yum_repo = entities.Repository(product=cls.product.id)
        cls.yum_repo.id = cls.yum_repo.create_json()['id']
        cls.yum_repo.sync()

        cls.puppet_repo = entities.Repository(
            content_type='puppet',
            product=cls.product.id,
        )
        cls.puppet_repo.id = cls.puppet_repo.create_json()['id']
        cls.puppet_repo.upload(PUPPET_MODULE_NTP_PUPPETLABS)

    def test_positive_publish_1(self):
        """@Test: Publish a content view several times.

        @Assert: Content view has the correct number of versions after each
        promotion.

        @Feature: ContentView

        """
        content_view = entities.ContentView()
        content_view.id = content_view.create_json()['id']
        for _ in range(REPEAT):
            self.assertEqual(content_view.publish()['result'], 'success')
        self.assertEqual(len(content_view.read_json()['versions']), REPEAT)

    def test_positive_publish_2(self):
        """@Test: Give a content view yum packages and publish it repeatedly.

        @Assert: The yum repo is referenced from the content view, the content
        view can be published several times, and each content view version has
        at least one package.

        @Feature: ContentView

        """
        content_view = entities.ContentView(organization=self.org.id)
        content_view.id = content_view.create_json()['id']
        content_view.set_repository_ids([self.yum_repo.id])

        # Check that the yum repo is referenced.
        self.assertEqual(len(content_view.read_json()['repositories']), 1)

        # Publish the content view several times and check that each version
        # has some software packages.
        for _ in range(REPEAT):
            response = content_view.publish()
            self.assertEqual(
                response['result'],
                'success',
                response['humanized']['errors']
            )
        for cvv_id in (  # content view version ID
                version['id']
                for version
                in content_view.read_json()['versions']):
            cvv = entities.ContentViewVersion(id=cvv_id)
            self.assertGreater(cvv.read_json()['package_count'], 0)

    def test_positive_publish_3(self):
        """@Test: Publish a content view that has puppet modules several times.

        @Assert: The puppet module is referenced fromt he content view, the
        content view can be published several times, and each version
        references the puppet module.

        @Feature: ContentView

        """
        content_view = entities.ContentView(organization=self.org.id)
        content_view.id = content_view.create_json()['id']
        puppet_module = content_view.available_puppet_modules()['results'][0]
        content_view.add_puppet_module(
            puppet_module['author'],
            puppet_module['name']
        )

        # Check that the puppet module is referenced.
        self.assertEqual(len(content_view.read_json()['puppet_modules']), 1)

        # Publish the content view several times and check that each version
        # has the puppet module added above.
        for _ in range(REPEAT):
            self.assertEqual('success', content_view.publish()['result'])
        for cvv_id in (  # content view version ID
                version['id']
                for version
                in content_view.read_json()['versions']):
            cvv = entities.ContentViewVersion(id=cvv_id)
            self.assertEqual(len(cvv.read_json()['puppet_modules']), 1)

    def test_positive_promote_1(self):
        """@Test: Promote a content view version ``REPEAT`` times.

        @Assert: The content view version points to ``REPEAT + 1`` lifecycle
        environments after the promotions.

        @Feature: ContentView

        """
        content_view = entities.ContentView(organization=self.org.id)
        content_view.id = content_view.create_json()['id']
        self.assertEqual(content_view.publish()['result'], 'success')

        # Promote the content view version several times.
        cvv = entities.ContentViewVersion(
            id=content_view.read_json()['versions'][0]['id']  # only one ver
        )
        for _ in range(REPEAT):
            lc_env_id = entities.LifecycleEnvironment(
                organization=self.org.id
            ).create_json()['id']
            response = cvv.promote(lc_env_id)
            self.assertEqual(
                response['result'],
                'success',
                response['humanized']['errors']
            )

        # Does it show up in the correct number of lifecycle environments?
        self.assertEqual(
            len(content_view.read_json()['versions'][0]['environment_ids']),
            REPEAT + 1
        )

    def test_positive_promote_2(self):
        """@Test: Give a content view a yum repo, publish it once and promote
        the content view version ``REPEAT + 1`` times.

        @Assert: The content view has one repository, the content view version
        is in ``REPEAT + 1`` lifecycle environments and it has at least one
        package.

        @Feature: ContentView

        """
        content_view = entities.ContentView(organization=self.org.id)
        content_view.id = content_view.create_json()['id']
        content_view.set_repository_ids([self.yum_repo.id])
        self.assertEqual(content_view.publish()['result'], 'success')

        # Promote the content view version.
        cvv = entities.ContentViewVersion(
            id=content_view.read_json()['versions'][0]['id']  # only one ver
        )
        for _ in range(REPEAT):
            lc_env_id = entities.LifecycleEnvironment(
                organization=self.org.id
            ).create_json()['id']
            response = cvv.promote(lc_env_id)
            self.assertEqual(
                response['result'],
                'success',
                response['humanized']['errors']
            )

        # Everything's done - check some content view attributes...
        cv_attrs = content_view.read_json()
        self.assertEqual(len(cv_attrs['repositories']), 1)
        self.assertEqual(len(cv_attrs['versions']), 1)

        # ...and some content view version attributes.
        cvv_attrs = entities.ContentViewVersion(
            id=cv_attrs['versions'][0]['id']
        ).read_json()
        self.assertEqual(len(cvv_attrs['environments']), REPEAT + 1)
        self.assertGreater(cvv_attrs['package_count'], 0)

    def test_positive_promote_3(self):
        """@Test: Give a content view a puppet module, publish it once and
        promote the content view version ``REPEAT + 1`` times.

        @Assert: The content view has one puppet module, the content view
        version is in ``REPEAT + 1`` lifecycle environments and it has one
        puppet module.

        @Feature: ContentView

        """
        content_view = entities.ContentView(organization=self.org.id)
        content_view.id = content_view.create_json()['id']
        puppet_module = content_view.available_puppet_modules()['results'][0]
        content_view.add_puppet_module(
            puppet_module['author'],
            puppet_module['name']
        )
        self.assertEqual(content_view.publish()['result'], u'success')

        # Promote the content view version.
        cvv = entities.ContentViewVersion(
            id=content_view.read_json()['versions'][0]['id']  # only one ver
        )
        for _ in range(REPEAT):
            lc_env_id = entities.LifecycleEnvironment(
                organization=self.org.id
            ).create_json()['id']
            self.assertEqual(cvv.promote(lc_env_id)['result'], 'success')

        # Everything's done. Check some content view attributes...
        cv_attrs = content_view.read_json()
        self.assertEqual(len(cv_attrs['versions']), 1)
        self.assertEqual(len(cv_attrs['puppet_modules']), 1)

        # ...and some content view version attributes.
        cvv_attrs = entities.ContentViewVersion(
            id=cv_attrs['versions'][0]['id']
        ).read_json()
        self.assertEqual(len(cvv_attrs['environments']), REPEAT + 1)
        self.assertEqual(len(cvv_attrs['puppet_modules']), 1)


@ddt
class ContentViewUpdateTestCase(APITestCase):
    """Tests for updating content views."""

    @classmethod
    def setUpClass(cls):
        """Create a content view."""
        cls.content_view = entities.ContentView(
            id=entities.ContentView().create()['id']
        )

    @data(
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

    @data(
        {u'label': gen_utf8(30), u'bz-bug': 1147100},  # Immutable.
        {u'name': gen_utf8(256)},
    )
    def test_negative_update_1(self, attrs):
        """@Test: Update a content view and provide an invalid attribute.

        @Assert: The content view's attributes are not updated.

        @Feature: ContentView

        """
        bug_id = attrs.pop('bz-bug', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        response = client.put(
            self.content_view.path(),
            attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        with self.assertRaises(HTTPError):
            response.raise_for_status()


@run_only_on('sat')
class ContentViewTestCaseStub(APITestCase):
    """Incomplete tests for content views."""
    # Each of these tests should be given a better name when they're
    # implemented. In the meantime, let's not worry about bad names.
    # (invalid-name) pylint:disable=C0103

    @stubbed
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

    @stubbed
    def test_associate_view_rh(self):
        """
        @test: associate Red Hat content in a view
        @feature: Content Views
        @setup: Sync RH content
        @assert: RH Content can be seen in a view
        @status: Manual
        """

    @stubbed
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

    @stubbed
    def test_associate_view_custom_content(self):
        """
        @test: associate Red Hat content in a view
        @feature: Content Views
        @setup: Sync custom content
        @assert: Custom content can be seen in a view
        @status: Manual
        """

    @stubbed
    def test_cv_associate_puppet_repo_negative(self):
        """
        @test: attempt to associate puppet repos within a custom
        content view
        @feature: Content Views
        @assert: User cannot create a composite content view
        that contains direct puppet repos.
        @status: Manual
        """

    @stubbed
    def test_cv_associate_components_composite_negative(self):
        """
        @test: attempt to associate components n a non-composite
        content view
        @feature: Content Views
        @assert: User cannot add components to the view
        @status: Manual
        """

    @stubbed
    def test_cv_associate_composite_dupe_repos_negative(self):
        """
        @test: attempt to associate the same repo multiple times within a
        content view
        @feature: Content Views
        @assert: User cannot add repos multiple times to the view
        @status: Manual
        """

    @stubbed
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

    @stubbed
    def test_cv_promote_rh(self):
        """
        @test: attempt to promote a content view containing RH content
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @stubbed
    def test_cv_promote_rh_custom_spin(self):
        """
        @test: attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @stubbed
    def test_cv_promote_custom_content(self):
        """
        @test: attempt to promote a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be promoted
        """

    @stubbed
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

    @stubbed
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

    @stubbed
    def test_cv_publish_rh(self):
        """
        @test: attempt to publish a content view containing RH content
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        """
        # See method test_subscribe_system_to_cv in module test_contentview_v2

    @stubbed
    def test_cv_publish_rh_custom_spin(self):
        """
        @test: attempt to publish  a content view containing a custom RH
        spin - i.e., contains filters.
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        @status: Manual
        """

    @stubbed
    def test_cv_publish_custom_content(self):
        """
        @test: attempt to publish a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be published
        @status: Manual
        """

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
    def test_cv_clone_within_same_env(self):
        """
        @test: attempt to create new content view based on existing
        view within environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """
        # Dev note: "not implemented yet"

    @stubbed
    def test_cv_clone_within_diff_env(self):
        """
        @test: attempt to create new content view based on existing
        view, inside a different environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """
        # Dev note: "not implemented yet"

    @stubbed
    def test_cv_refresh_errata_to_new_view_in_same_env(self):
        """
        @test: attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """

    @stubbed
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

    @stubbed
    def test_custom_cv_subscribe_system(self):
        """
        @test: attempt to  subscribe systems to content view(s)
        @feature: Content Views
        @assert: Systems can be subscribed to content view(s)
        """
        # This test is implemented in tests/foreman/smoke/test_api_smoke.py.
        # See the end of method TestSmoke.test_smoke.

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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

    @stubbed
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
