# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Host/System Unification
Feature details: https://fedorahosted.org/katello/wiki/ContentViews
"""

import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest

from ddt import ddt
from robottelo.common.constants import NOT_IMPLEMENTED, REPO_TYPE
from robottelo.common.decorators import data, bzbug
from robottelo.common.helpers import (generate_string, valid_names_list,
                                      invalid_names_list)
from robottelo.ui.factory import make_org
from robottelo.ui.locators import (locators, common_locators)
from robottelo.ui.session import Session
from tests.foreman.ui.baseui import BaseUI


@ddt
class TestContentViewsUI(BaseUI):
    """ Implement tests for content view via UI"""

    org_name = None

    def setUp(self):
        super(TestContentViewsUI, self).setUp()

        # Make sure to use the Class' org_name instance
        if TestContentViewsUI.org_name is None:
            TestContentViewsUI.org_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=TestContentViewsUI.org_name)

    @bzbug('1083086')
    @data(*valid_names_list())
    def test_cv_create(self, name):
        """
        @test: create content views (positive)
        @feature: Content Views
        @assert: content views are created
        @BZ: 1083086
        """

        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_content_views()
            self.content_views.create(name)
            self.assertIsNotNone(
                self.content_views.search(name),
                'Failed to find content view %s from %s org' % (
                    name, self.org_name))

    @bzbug('1083086')
    @data(*invalid_names_list())
    def test_cv_create_negative(self, name):
        # variations (subject to change):
        # zero length, symbols, html, etc.
        """
        @test: create content views (negative)
        @feature: Content Views
        @assert: content views are not created; proper error thrown and
        system handles it gracefully
        @BZ: 1083086
        """

        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_content_views()
            self.content_views.create(name)
            self.assertTrue(
                self.content_views.wait_until_element(
                    locators['contentviews.has_error']),
                'No validation error found for "%s" from %s org' % (
                    name, self.org_name))
            self.assertIsNone(self.content_views.search(name))

    def test_cv_end_2_end(self):
        """
        @test: create content view
        @feature: Content Views
        @steps: 1. Create Product/repo and Sync it
                2. Create CV and add created repo in step1
                3. Publish and promote it to 'Library'
                4. Promote it to next environment
        @assert: content view is created, updated with repo
                publish and promoted to next selected env
        """

        repo_name = generate_string("alpha", 8)
        prd_name = generate_string("alpha", 8)
        env_name = generate_string("alpha", 8)
        repo_url = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
        name = generate_string("alpha", 8)
        publish_version = "Version 1"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(env_name)
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=repo_url)
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_sync_status()
        sync = self.sync.sync_custom_repos(prd_name, [repo_name])
        self.assertIsNotNone(sync)
        self.navigator.go_to_content_views()
        self.content_views.create(name)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_content_views()
        self.content_views.add_remove_repos(name, [repo_name])
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))
        self.content_views.publish(name, "publishing version_1")
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))
        self.content_views.promote(name, publish_version, env_name)
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))

    def test_associate_puppet_module(self):
        """
        @test: create content view
        @feature: Content Views
        @steps: 1. Create Product/puppet repo and Sync it
                2. Create CV and add puppet modules from created repo
        @assert: content view is created, updated with puppet module
        """

        repo_name = generate_string("alpha", 8)
        prd_name = generate_string("alpha", 8)
        url = "http://davidd.fedorapeople.org/repos/random_puppet/"
        name = generate_string("alpha", 8)
        puppet_module = "httpd"
        module_ver = 'Latest'
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=url,
                               repo_type=REPO_TYPE['puppet'])
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_sync_status()
        sync = self.sync.sync_custom_repos(prd_name, [repo_name])
        self.assertIsNotNone(sync)
        self.navigator.go_to_content_views()
        self.content_views.create(name)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_content_views()
        module = self.content_views.add_puppet_module(name,
                                                      puppet_module,
                                                      filter_term=module_ver)
        self.assertIsNotNone(module)

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_edit(self):
        """
        @test: edit content views - name, description, etc.
        @feature: Content Views
        @assert: edited content view save is successful and info is
        updated
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
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

    @bzbug('1079145')
    def test_cv_delete(self):
        """
        @test: delete content views
        @feature: Content Views
        @assert: edited content view can be deleted and no longer
        appears in any content view UI
        updated
        @status: Manual
        @BZ: 1079145
        """

        self.fail('Test is not blocked anymore by bz 1079145 and should be '
                  'implemented')

    def test_cv_composite_create(self):
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

        repo_name = generate_string("alpha", 8)
        prd_name = generate_string("alpha", 8)
        url = "http://davidd.fedorapeople.org/repos/random_puppet/"
        puppet_module = "httpd"
        module_ver = 'Latest'
        cv_name = generate_string("alpha", 8)
        composite_name = generate_string("alpha", 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_products()
        self.products.create(prd_name)
        self.assertIsNotNone(self.products.search(prd_name))
        self.repository.create(repo_name, product=prd_name, url=url,
                               repo_type=REPO_TYPE['puppet'])
        self.assertIsNotNone(self.repository.search(repo_name))
        self.navigator.go_to_sync_status()
        sync = self.sync.sync_custom_repos(prd_name, [repo_name])
        self.assertIsNotNone(sync)
        self.navigator.go_to_content_views()
        self.content_views.create(cv_name)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_content_views()
        module = self.content_views.add_puppet_module(cv_name,
                                                      puppet_module,
                                                      filter_term=module_ver)
        self.assertIsNotNone(module)
        self.content_views.publish(cv_name)
        self.content_views.create(composite_name, is_composite=True)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_content_views()
        self.content_views.add_remove_cv(composite_name, [cv_name])
        self.assertTrue(self.content_views.wait_until_element
                        (common_locators["alert.success"]))
        # TODO: Need to add RH contents

    @unittest.skip(NOT_IMPLEMENTED)
    def test_associate_view_rh(self):
        """
        @test: associate Red Hat content in a view
        @feature: Content Views
        @setup: Sync RH content
        @assert: RH Content can be seen in a view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
    def test_associate_view_custom_content(self):
        """
        @test: associate Red Hat content in a view
        @feature: Content Views
        @setup: Sync custom content
        @assert: Custom content can be seen in a view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_associate_components_composite_negative(self):
        """
        @test: attempt to associate components n a non-composite
        content view
        @feature: Content Views
        @assert: User cannot add components to the view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_associate_composite_dupe_repos_negative(self):
        """
        @test: attempt to associate the same repo multiple times within a
        content view
        @feature: Content Views
        @assert: User cannot add repos multiple times to the view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_associate_composite_dupe_modules_negative(self):
        """
        @test: attempt to associate duplicate puppet module(s) within a
        content view
        @feature: Content Views
        @assert: User cannot add modules multiple times to the view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_rh(self):
        """
        @test: attempt to promote a content view containing RH content
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_rh_custom_spin(self):
        """
        @test: attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_custom_content(self):
        """
        @test: attempt to promote a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_default_negative(self):
        """
        @test: attempt to promote a the default content views
        @feature: Content Views
        @assert: Default content views cannot be promoted
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_publish_rh(self):
        """
        @test: attempt to publish a content view containing RH content
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_publish_rh_custom_spin(self):
        """
        @test: attempt to publish  a content view containing a custom RH
        spin - i.e., contains filters.
        @feature: Content Views
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_publish_custom_content(self):
        """
        @test: attempt to publish a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_clone_within_same_env(self):
        # Dev note: "not implemented yet"
        """
        @test: attempt to create new content view based on existing
        view within environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_clone_within_diff_env(self):
        # Dev note: "not implemented yet"
        """
        @test: attempt to create new content view based on existing
        view, inside a different environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_refresh_errata_to_new_view_in_same_env(self):
        """
        @test: attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment
        @feature: Content Views
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
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

    @unittest.skip(NOT_IMPLEMENTED)
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
