# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Host/System Unification
Feature details:http://people.redhat.com/~dcleal/apiv2/apidoc.html"""
from ddt import ddt
from robottelo.api.apicrud import ApiCrud, ApiException
from robottelo.common.decorators import data, skip_if_bz_bug_open
from robottelo.common.decorators import stubbed
from robottelo.records.content_view_definition import ContentViewDefinition
from robottelo.records.environment import EnvironmentKatello
from robottelo.test import APITestCase


@ddt
class TestContentView(APITestCase):

    @data(*ContentViewDefinition.enumerate(label="", description=""))
    def test_cv_create_api(self, data):
        # variations (subject to change):
        # ascii string, alphanumeric, latin-1, utf8, etc.
        """
        @test: create content views (positive)
        @feature: Content Views
        @assert: content views are created
        """

        depends = ApiCrud.record_create_dependencies(data)
        result = ApiCrud.record_create(depends)
        self.assertIntersects(data, result)

    @data(*ContentViewDefinition.enumerate(name=""))
    def test_cv_create_api_negative_0(self, data):
        # variations (subject to change):
        # zero length, symbols, html, etc.
        """
        @test: create content views (negative)
        @feature: Content Views
        @assert: content views are not created; proper error thrown and
        system handles it gracefully
        """

        try:
            depends = ApiCrud.record_create_dependencies(data)
            result = ApiCrud.record_create(depends)
            self.assertIntersects(data, result)
            correctly_failing = False
        except ApiException:
            correctly_failing = True
        self.assertTrue(correctly_failing)

    @data(*ContentViewDefinition.enumerate(name="  "))
    def test_cv_create_api_negative_1(self, data):
        # variations (subject to change):
        # zero length, symbols, html, etc.
        """
        @test: create content views (negative)
        @feature: Content Views
        @assert: content views are not created; proper error thrown and
        system handles it gracefully
        """

        try:
            depends = ApiCrud.record_create_dependencies(data)
            result = ApiCrud.record_create(depends)
            self.assertIntersects(data, result)
            correctly_failing = False
        except ApiException:
            correctly_failing = True
        self.assertTrue(correctly_failing)

    @data(*ContentViewDefinition.enumerate(label="", description=""))
    def test_cv_create_api_badorg_negative(self, data):
        # Use an invalid org name
        """
        @test: create content views (negative)
        @feature: Content Views
        @assert: content views are not created; proper error thrown and
        system handles it gracefully
        """
        try:
            data.organization.name = ""
            depends = ApiCrud.record_create_dependencies(data)
            result = ApiCrud.record_create(depends)
            self.assertIntersects(data, result)
            correctly_failing = False
        except ApiException:
            correctly_failing = True
        self.assertTrue(correctly_failing)

    @data(*ContentViewDefinition.enumerate(label="", description=""))
    def test_cv_edit(self, data):
        """
        @test: edit content views - name, description, etc.
        @feature: Content Views
        @assert: edited content view save is successful and info is
        updated
        """

        con_view = ContentViewDefinition()
        depends = ApiCrud.record_create_dependencies(con_view)
        t = ApiCrud.record_create(depends)
        t['organization_id'] = depends['organization_id']
        con_view.name = data.name
        ApiCrud.record_update(t)

    @stubbed
    def test_cv_edit_rh_custom_spin(self):
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.
        """
        @test: edit content views for a custom rh spin.  For example,
        @feature: Content Views
        modify a filter
        @assert: edited content view save is successful and info is
        updated
        @status: Manual
        """

    @data(*ContentViewDefinition.enumerate(description=""))
    def test_cv_delete(self, data):
        """
        @test: delete content views
        @feature: Content Views
        @assert: edited content view can be deleted and no longer
        appears in any content view UI
        updated
        """

        data.label = "conview_del"
        depends = ApiCrud.record_create_dependencies(data)
        t = ApiCrud.record_create(depends)
        t['organization_id'] = depends['organization_id']
        self.assertTrue(ApiCrud.record_exists(t))
        ApiCrud.record_remove(t)
        self.assertFalse(ApiCrud.record_exists(t))

    @data(*ContentViewDefinition.enumerate(label="", description=""))
    def test_cv_composite_create(self, data):
        # Note: puppet repos cannot/should not be used in this test
        # It shouldn't work - and that is tested in a different case.
        # Individual modules from a puppet repo, however, are a valid
        # variation.
        """
        @test: create a composite content views
        @feature: Content Views
        @setup: sync multiple content source/types (RH, custom, etc.)
        @assert: Composite content views are created
       """

        data.composite = True
        depends = ApiCrud.record_create_dependencies(data)
        result = ApiCrud.record_create(depends)
        self.assertIntersects(data, result)

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
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.
        """
        @test: associate Red Hat content in a view
        @feature: Content Views
        @setup: Sync RH content
        @steps: 1. Assure filter(s) applied to associated content
        @assert: Filtered RH content only is available/can be seen in a view
        @status: Manual
        """

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
        # Again, individual modules should be ok.
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
        con_view = ApiCrud.record_create_recursive(ContentViewDefinition())
        self.assertIntersects(data, con_view)
        task = con_view._meta.api_class.publish(con_view)
        task.poll(5, 100)  # poll every 5th second, max of 100 seconds
        self.assertEqual('success', task.result())
        published = ApiCrud.record_resolve(con_view)
        env = EnvironmentKatello(organization=published.organization)
        created_env = ApiCrud.record_create_recursive(env)
        task2 = published._meta.api_class.promote(
            published.versions[0]['id'],
            created_env.id
            )
        task2.poll(5, 100)  # poll every 5th second, max of 100 seconds
        self.assertEqual('success', task2.result())

    def test_cv_promote_composite(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """
        @test: attempt to promote a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @steps: create a composite view containing multiple content types
        @assert: Content view can be promoted
        @status: Manual
        """

    def test_cv_promote_default_negative(self):
        """
        @test: attempt to promote a the default content views
        @feature: Content Views
        @assert: Default content views cannot be promoted
        """
        env = EnvironmentKatello()
        created_env = ApiCrud.record_create_recursive(env)
        task = ContentViewDefinition._meta.api_class.promote(
            1,
            created_env.id
            )
        self.assertIn(
            'errors', task.json,
            "Default cv shouldn't be promoted")

    @stubbed
    def test_cv_promote_badid_negative(self):
        """
        @test: attempt to promote a content view using an invalid id
        @feature: Content Views
        @assert: Content views cannot be promoted; handled gracefully
        """
        env = EnvironmentKatello()
        created_env = ApiCrud.record_create_recursive(env)
        task = ContentViewDefinition._meta.api_class.promote(
            1,
            created_env.id
            )
        self.assertIn(
            'errors', task.json,
            "Invalid id shouldn't be promoted")

    def test_cv_promote_badenvironment_negative(self):
        """
        @test: attempt to promote a content view using an invalid environment
        @feature: Content Views
        @assert: Content views cannot be promoted; handled gracefully
        """
        con_view = ApiCrud.record_create_recursive(ContentViewDefinition())
        self.assertIntersects(data, con_view)
        task = con_view._meta.api_class.publish(con_view)
        task.poll(5, 100)  # poll every 5th second, max of 100 seconds
        self.assertEqual('success', task.result())
        published = ApiCrud.record_resolve(con_view)
        task = published._meta.api_class.promote(
            published.versions[0]['id'],
            -1
            )

        self.assertIn(
            'errors', task.json,
            "Shouldn't be promoted to invalid env")

    # Content Views: publish
    # katello content definition publish --label=MyView
    @data(*ContentViewDefinition.enumerate(label="", description=""))
    def test_cv_publish_rh(self, data):
        """
        @test: attempt to publish a content view containing RH content
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        """

        con_view = ApiCrud.record_create_recursive(data)
        self.assertIntersects(data, con_view)
        task = con_view._meta.api_class.publish(con_view)
        task.poll(5, 100)  # poll every 5th second, max of 100 seconds
        self.assertEqual('success', task.result())

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
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """
        @test: attempt to publish  a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be published
        @status: Manual
        """

    @stubbed
    def test_cv_publish_badlabel_negative(self):
        # Variations might be:
        # zero length, too long, symbols, etc.
        """
        @test: attempt to publish a content view containing invalid strings
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view is not published; condition is handled
        gracefully;
        no tracebacks
        @status: Manual
        """

    @stubbed
    def test_cv_publish_version_changes_in_target_env(self):
        # Dev notes:
        # If Dev has version x, then when I promote version y into
        # Dev, version x goes away (ie when I promote version 1 to Dev,
        # version 3 goes away)
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

    @stubbed
    def test_cv_publish_version_changes_in_source_env(self):
        # Dev notes:
        # Similarly when I publish version y, version x goes away from
        # Library (ie when I publish version 2, version 1 disappears)
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

    @stubbed
    def test_cv_clone_within_same_env(self):
        # Dev note: "not implemented yet"
        """
        @test: attempt to create new content view based on existing
        view within environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """

    @stubbed
    def test_cv_clone_within_diff_env(self):
        # Dev note: "not implemented yet"
        """
        @test: attempt to create new content view based on existing
        view, inside a different environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """

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
        """
        @test: attempt to  subscribe systems to content view(s)
        @feature: Content Views
        @assert: Systems can be subscribed to content view(s)
        @status: Manual
        """

    @skip_if_bz_bug_open('1094758')
    def test_custom_cv_subscribe_system(self):
        """
        @test: attempt to  subscribe systems to content view(s)
        @feature: Content Views
        @assert: Systems can be subscribed to content view(s)
        """
        # s = System()
        # scd = ApiCrud.record_create_dependencies(s)
        # task = scd.content_view._meta.api_class.publish(scd.content_view)
        # task.poll(5, 100)
        # scc = ApiCrud.record_create(scd)
        # self.assertIntersects(s, scc)
        self.fail('System record should be implemented')

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
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user with admin permissions
        # for Content Views
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify, Delete, Promote Publish, Subscribe
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user with the Content View admin role
        @assert: User with admin role for content view can perform all
        Variations above
        @status: Manual
        """

    @stubbed
    def test_cv_roles_readonly_user(self):
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user with read-only permissions
        # for Content Views
        # THIS IS EVEN ASSUMING WE HAVE A "READ-ONLY" ROLE IN THE FIRST PLACE
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify,  Promote?, Publish?, Subscribe??
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user with the Content View read-only role
        @assert: User with read-only role for content view can perform all
        Variations above
        @status: Manual
        """

    @stubbed
    def test_cv_roles_admin_user_negative(self):
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user withOUT admin permissions
        # for Content Views
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify, Delete, Promote Publish, Subscribe
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user with the Content View admin role
        @assert: User withOUT admin role for content view canNOT perform any
        Variations above
        @status: Manual
        """

    @stubbed
    def test_cv_roles_readonly_user_negative(self):
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user withOUT read-only permissions
        # for Content Views
        # THIS IS EVEN ASSUMING WE HAVE A "READ-ONLY" ROLE IN THE FIRST PLACE
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify,  Promote?, Publish?, Subscribe??
        """
        @test: attempt to view content views
        @feature: Content Views
        @setup: create a user withOUT the Content View read-only role
        @assert: User withOUT read-only role for content view can perform all
        Variations above
        @status: Manual
        """
