# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Host/System Unification
Feature details: https://fedorahosted.org/katello/wiki/ContentViews
"""
from robottelo.common.constants import NOT_IMPLEMENTED
import unittest

from tests.ui.baseui import BaseUI


class TestContentViewsUI(BaseUI):

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_create(self):
        # variations (subject to change):
        # ascii string, alphanumeric, latin-1, utf8, etc.
        """
        @feature: Content Views
        @test: create content views (positive)
        @assert: content views are created
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_create_negative(self):
        # variations (subject to change):
        # zero length, symbols, html, etc.
        """
        @feature: Content Views
        @test: create content views (negative)
        @assert: content views are not created; proper error thrown and
        system handles it gracefully
        @status: Manual
        """
    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_edit(self):
        """
        @feature: Content Views
        @test: edit content views - name, description, etc.
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
        @feature: Content Views
        @test: edit content views for a custom rh spin.  For example,
        modify a filter
        @assert: edited content view save is successful and info is
        updated
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_delete(self):
        """
        @feature: Content Views
        @test: delete content views
        @assert: edited content view can be deleted and no longer
        appears in any content view UI
        updated
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_composite_create(self):
        # Note: puppet repos cannot/should not be used in this test
        # It shouldn't work - and that is tested in a different case.
        # Individual modules from a puppet repo, however, are a valid
        # variation.
        """
        @feature: Content Views
        @test: create a composite content views
        @setup: sync multiple content source/types (RH, custom, etc.)
        @assert: Composite content views are created
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_associate_view_rh(self):
        """
        @feature: Content Views
        @test: associate Red Hat content in a view
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
        @feature: Content Views
        @test: associate Red Hat content in a view
        @setup: Sync RH content
        @steps: 1. Assure filter(s) applied to associated content
        @assert: Filtered RH content only is available/can be seen in a view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_associate_view_custom_content(self):
        """
        @feature: Content Views
        @test: associate Red Hat content in a view
        @setup: Sync custom content
        @assert: Custom content can be seen in a view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_associate_puppet_repo_negative(self):
        # Again, individual modules should be ok.
        """
        @feature: Content Views
        @test: attempt to associate puppet repos within a custom
        content view
        @assert: User cannot create a composite content view
        that contains direct puppet repos.
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_associate_components_composite_negative(self):
        """
        @feature: Content Views
        @test: attempt to associate components n a non-composite
        content view
        @assert: User cannot add components to the view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_associate_composite_dupe_repos_negative(self):
        """
        @feature: Content Views
        @test: attempt to associate the same repo multiple times within a
        content view
        @assert: User cannot add repos multiple times to the view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_associate_composite_dupe_modules_negative(self):
        """
        @feature: Content Views
        @test: attempt to associate duplicate puppet module(s) within a
        content view
        @assert: User cannot add modules multiple times to the view
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_rh(self):
        """
        @feature: Content Views
        @test: attempt to promote a content view containing RH content
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_rh_custom_spin(self):
        """
        @feature: Content Views
        @test: attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be promoted
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_custom_content(self):
        """
        @feature: Content Views
        @test: attempt to promote a content view containing custom content
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
        @feature: Content Views
        @test: attempt to promote a content view containing custom content
        @setup: Multiple environments for an org; custom content synced
        @steps: create a composite view containing multiple content types
        @assert: Content view can be promoted
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_default_negative(self):
        """
        @feature: Content Views
        @test: attempt to promote a the default content views
        @assert: Default content views cannot be promoted
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_publish_rh(self):
        """
        @feature: Content Views
        @test: attempt to publish a content view containing RH content
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_publish_rh_custom_spin(self):
        """
        @feature: Content Views
        @test: attempt to publish  a content view containing a custom RH
        spin - i.e., contains filters.
        @setup: Multiple environments for an org; RH content synced
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_publish_custom_content(self):
        """
        @feature: Content Views
        @test: attempt to publish a content view containing custom content
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
        @feature: Content Views
        @test: attempt to publish  a content view containing custom content
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
        @feature: Content Views
        @test: when publishing new version to environment, version
        gets updated
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
        @feature: Content Views
        @test: when publishing new version to environment, version
        gets updated
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
        @feature: Content Views
        @test: attempt to create new content view based on existing
        view within environment
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_clone_within_diff_env(self):
        # Dev note: "not implemented yet"
        """
        @feature: Content Views
        @test: attempt to create new content view based on existing
        view, inside a different environment
        @assert: Content view can be published
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_refresh_errata_to_new_view_in_same_env(self):
        """
        @feature: Content Views
        @test: attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment
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
        @feature: Content Views
        @test: attempt to  subscribe systems to content view(s)
        @assert: Systems can be subscribed to content view(s)
        @status: Manual
        """

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
        @feature: Content Views
        @test: attempt to view content views
        @setup: create a user with the Content View admin role
        @assert: User with admin role for content view can perform all
        Variations above
        @status: Manual
        """

    # ROLES TESTING
    # All this stuff is speculative at best.

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
        @feature: Content Views
        @test: attempt to view content views
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
        @feature: Content Views
        @test: attempt to view content views
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
        @feature: Content Views
        @test: attempt to view content views
        @setup: create a user withOUT the Content View read-only role
        @assert: User withOUT read-only role for content view can perform all
        Variations above
        @status: Manual
        """
