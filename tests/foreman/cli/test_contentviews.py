# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Host/System Unification
Feature details: https://fedorahosted.org/katello/wiki/ContentViewCLI
"""
import unittest

from ddt import ddt
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    make_content_view, make_org, make_repository, make_product,
    make_lifecycle_environment, make_user)
from robottelo.cli.org import Org
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.repository import Repository
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import data, bzbug
from robottelo.common.helpers import generate_string
from tests.foreman.cli.basecli import BaseCLI

from robottelo.api.apicrud import ApiCrud
from robottelo.records.content_view_definition import ContentViewDefinitionApi
from robottelo.records.user import User
from robottelo.records.role import add_permission_to_user

PUPPET_REPO_URL = "http://davidd.fedorapeople.org/repos/random_puppet/"


def positive_create_data():
    """Random data for positive creation"""

    return (
        {'name': generate_string("latin1", 10)},
        {'name': generate_string("utf8", 10)},
        {'name': generate_string("alpha", 10)},
        {'name': generate_string("alphanumeric", 10)},
        {'name': generate_string("numeric", 20)},
        {'name': generate_string("html", 10)},
    )


def negative_create_data():
    """Random data for negative creation"""

    return (
        {'name': ' '},
        {'name': generate_string('alpha', 300)},
        {'name': generate_string('numeric', 300)},
        {'name': generate_string('alphanumeric', 300)},
        {'name': generate_string('utf8', 300)},
        {'name': generate_string('latin1', 300)},
        {'name': generate_string('html', 300)},
    )


@ddt
class TestContentView(BaseCLI):
    """
    Content View CLI tests
    """

    # Notes:
    # * For most tests in CLI, you should be able to observe whether
    # or not a view has been created, via variations on the
    # `katello content view list` command
    # * Remember that all positive tests should assert a status code
    # of "0"; negative tests should return a non-zero status code

    # Content View: Creation
    # katello content definition create --definition=MyView

    org = None
    product = None
    env1 = None
    env2 = None

    def setUp(self):
        """
        Tests for content-view via Hammer CLI
        """

        super(TestContentView, self).setUp()

        if TestContentView.org is None:
            TestContentView.org = make_org()
        if TestContentView.env1 is None:
            TestContentView.env1 = make_lifecycle_environment(
                {u'organization-id': TestContentView.org['label']})
        if TestContentView.env2 is None:
            TestContentView.env2 = make_lifecycle_environment(
                {u'organization-id': TestContentView.org['label'],
                 u'prior': TestContentView.env1['label']})
        if TestContentView.product is None:
            TestContentView.product = make_product(
                {u'organization-id': TestContentView.org['label']})

    @data(*positive_create_data())
    def test_cv_create_cli(self, test_data):
        # variations (subject to change):
        # ascii string, alphanumeric, latin-1, utf8, etc.
        """
        @test: create content views (positive)
        @feature: Content Views
        @assert: content views are created
        """
        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        test_data['organization-id'] = org_obj['label']
        con_view = make_content_view(test_data)

        result = ContentView.info({'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Failed to find object")
        self.assertEqual(con_view['name'], result.stdout['name'])

    @data(*negative_create_data())
    def test_cv_create_cli_negative(self, test_data):
        # variations (subject to change):
        # zero length, symbols, html, etc.
        """
        @test: create content views (negative)
        @feature: Content Views
        @assert: content views are not created; proper error thrown and
        system handles it gracefully
        """

        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        test_data['organization-id'] = org_obj['label']
        result = ContentView.create(test_data)
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0,
                           "There should be an exception here")

    def test_cv_create_cli_badorg_negative(self):
        # Use an invalid org name
        """
        @test: create content views (negative)
        @feature: Content Views
        @assert: content views are not created; proper error thrown and
        system handles it gracefully
        """

        org_name = generate_string("alpha", 10)
        con_name = generate_string("alpha", 10)
        result = ContentView.create({'name': con_name,
                                     'organization-id': org_name})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(
            len(result.stderr), 0, "There should be an exception here.")

    def test_cv_edit(self):
        """
        @test: edit content views - name, description, etc.
        @feature: Content Views
        @assert: edited content view save is successful and info is
        updated
        """

        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")
        con_name = generate_string("alpha", 10)
        con_view = make_content_view({'name': con_name,
                                      'organization-id': org_obj['label']})
        result = ContentView.info({'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Failed to find object")
        self.assertEqual(con_view['name'], result.stdout['name'])

        con_view_update = generate_string("alpha", 10)
        result = ContentView.update({'id': con_view['id'],
                                     'name': con_view_update})
        self.assertEqual(result.return_code, 0, "Failed to update object")
        self.assertEqual(
            len(result.stderr), 0, "Should not have gotten an error")

        result = ContentView.info({'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Failed to find object")
        self.assertEqual(con_view_update, result.stdout['name'])

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

    def test_cv_delete(self):
        """
        @test: delete content views
        @feature: Content Views
        @assert: edited content view can be deleted and no longer
        appears in any content view UI
        updated
        """

        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        con_view_name = generate_string("alpha", 10)
        con_view = make_content_view({'name': con_view_name,
                                      'organization-id': org_obj['label']})

        result = ContentView.info({'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Failed to find object")
        self.assertEqual(con_view['name'], result.stdout['name'])

        result = ContentView.delete({'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Failed to delete object")
        self.assertEqual(
            len(result.stderr), 0, "Should not have gotten an error")

        result = ContentView.info({'id': con_view['id']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0,
                           "There should be an exception here")

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
        @status: Manual
        """

        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        con_view_name = generate_string("alpha", 10)
        con_view = make_content_view({'name': con_view_name,
                                      'organization-id': org_obj['label'],
                                      'composite': True})

        result = ContentView.info({'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Failed to find object")
        self.assertEqual(con_view['name'], result.stdout['name'])

    # Content Views: Adding products/repos
    # katello content definition add_filter --label=MyView
    #   --filter=stable --org=ACME
    # katello content definition add_product --label=MyView
    #   --product=product1 --org=ACME
    # katello content definition add_repo --label=MyView
    #   --repo=repo1 --org=ACME

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

    def test_associate_view_custom_content(self):
        """
        @test: associate Red Hat content in a view
        @feature: Content Views
        @setup: Sync custom content
        @assert: Custom content can be seen in a view
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Fetch it
        result = Repository.info(
            {
                u'id': new_repo['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not synchronized")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})
        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Content-View was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not associated to selected CV")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "ContentView was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['repositories'][0]['name'],
            new_repo['name'],
            "Repo was not associated to CV"
        )

    def test_cv_associate_puppet_repo_negative(self):
        # Again, individual modules should be ok.
        """
        @test: attempt to associate puppet repos within a custom
        content view
        @feature: Content Views
        @assert: User cannot create a composite content view
        that contains direct puppet repos.
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id'],
                                    u'content-type': u'puppet',
                                    u'url': PUPPET_REPO_URL})
        # Fetch it
        result = Repository.info(
            {
                u'id': new_repo['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})

        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Content-View was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Associate puppet repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertNotEqual(
            result.return_code,
            0,
            "Puppet repo should not be associated")
        self.assertGreater(
            len(result.stderr), 0, "Error was expected")

    def test_cv_associate_components_composite_negative(self):
        """
        @test: attempt to associate components in a non-composite
        content view
        @feature: Content Views
        @assert: User cannot add components to the view
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Fetch it
        result = Repository.info(
            {
                u'id': new_repo['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not synchronized")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Create component CV
        new_cv = make_content_view({u'organization-id': self.org['label']})
        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Content-View was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not associated to selected CV")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publish CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Fetch version id
        cv_version = ContentView.version_list(
            {
                u'content-view-id': new_cv['id']
            }
        )
        self.assertEqual(cv_version.return_code, 0,
                         "Version list for selected CV was not found")
        self.assertEqual(len(cv_version.stderr), 0, "No error was expected")

        # Create non-composite CV
        with self.assertRaises(Exception):
            result = make_content_view(
                {
                    u'organization-id': self.org['label'],
                    u'component-ids':  cv_version.stdout[0]['id']
                }
            )

    def test_cv_associate_composite_dupe_repos_negative(self):
        """
        @test: attempt to associate the same repo multiple times within a
        content view
        @feature: Content Views
        @assert: User cannot add repos multiple times to the view
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Fetch it
        result = Repository.info(
            {
                u'id': new_repo['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not synchronized")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})
        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Content-View was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not associated to selected CV")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "ContentView was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        self.assertEqual(
            result.stdout['repositories'][0]['name'],
            new_repo['name'],
            "Repo was not associated to CV"
        )
        # Re-associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not associated to selected CV")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "ContentView was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")
        with self.assertRaises(Exception):
            self.assertEqual(
                result.stdout['repositories'][1]['name'],
                new_repo['name'],
                "No new entry of same repo is expected")

    @bzbug('1089905')
    def test_cv_associate_composite_dupe_modules_negative(self):
        """
        @test: attempt to associate duplicate puppet module(s) within a
        content view
        @feature: Content Views
        @assert: User cannot add modules multiple times to the view
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id'],
                                    u'content-type': u'puppet',
                                    u'url': PUPPET_REPO_URL})
        # Fetch it
        result = Repository.info(
            {
                u'id': new_repo['id']
            }
        )

        self.assertEqual(
            result.return_code,
            0,
            "Repository was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Repository was not synchronized")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})

        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code,
            0,
            "Content-View was not found")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Fetch puppet module
        puppet_result = PuppetModule.list({u'repository-id': new_repo['id'],
                                           u'per-page': False})
        self.assertEqual(
            puppet_result.return_code,
            0,
            "List of puppet modules was not generated")
        self.assertEqual(
            len(puppet_result.stderr), 0, "No error was expected")

        # Associate puppet module to CV
        result = ContentView.puppet_module_add(
            {
                u'content-view-id': new_cv['id'],
                u'name': puppet_result.stdout[0]['name']
            }
        )
        self.assertEqual(
            result.return_code,
            0,
            "Puppet module was not associated")
        self.assertEqual(
            len(result.stderr), 0, "No error was expected")

        # Re-associate same puppet module to CV
        result = ContentView.puppet_module_add(
            {
                u'content-view-id': new_cv['id'],
                u'name': puppet_result.stdout[0]['name']
            }
        )
        self.assertNotEqual(
            result.return_code,
            0,
            "Same puppet module should not be associated twice")
        self.assertGreater(
            len(result.stderr), 0, "Error was expected")

    # Content View: promotions
    # katello content view promote --label=MyView --env=Dev --org=ACME
    # katello content view promote --view=MyView --env=Staging --org=ACME

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

    def test_cv_promote_custom_content(self):
        """
        @test: attempt to promote a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be promoted
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Fetch it
        result = Repository.info({u'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repository was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repo was not synchronized")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})
        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(result.return_code, 0,
                         "Repo was not associated to selected CV")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing a new version of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Promote the Published version of CV to the next env
        result = ContentView.version_promote(
            {u'id': result.stdout['versions'][0]['id'],
             u'environment-id': self.env1['id']})
        self.assertEqual(result.return_code, 0,
                         "Promoting a version of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(result.stdout['environments'][1]['id'],
                         self.env1['id'],
                         "Promotion of version not successful to the env")

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
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Fetch it
        result = Repository.info({u'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repository was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repo was not synchronized")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})
        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(result.return_code, 0,
                         "Repo was not associated to selected CV")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing a new version of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Create CV
        con_view = make_content_view({'organization-id': self.org['label'],
                                      'composite': True})

        # Assert whether content view creation was successful
        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Associate version to composite CV
        result = ContentView.add_version({u'id': con_view['id'],
                                          u'version-id': version1_id})
        self.assertEqual(result.return_code, 0,
                         "Repo was not associated to selected CV")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Assert whether version was associated to composite CV
        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(result.stdout['components'][0]['id'],
                         version1_id,
                         "version was not associated to composite CV")

        # Publish a new version of CV
        result = ContentView.publish({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing a version of composite CV not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # As version info is populated after publishing only
        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Promote the Published version of CV to the next env

        result = ContentView.version_promote(
            {u'id': result.stdout['versions'][0]['id'],
             u'environment-id': self.env1['id']})
        self.assertEqual(result.return_code, 0,
                         "Promoting a version of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(result.stdout['environments'][1]['id'],
                         self.env1['id'],
                         "Promotion of version not successful to the env")

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_default_negative(self):
        """
        @test: attempt to promote a the default content views
        @feature: Content Views
        @assert: Default content views cannot be promoted
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_badlabel_negative(self):
        """
        @test: attempt to promote a content view using an invalid label
        @feature: Content Views
        @assert: Content views cannot be promoted; handled gracefully
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_badenvironment_negative(self):
        """
        @test: attempt to promote a content view using an invalid environment
        @feature: Content Views
        @assert: Content views cannot be promoted; handled gracefully
        @status: Manual
        """

    @unittest.skip(NOT_IMPLEMENTED)
    def test_cv_promote_badorg_negative(self):
        """
        @test: attempt to promote a content view using an invalid org
        @feature: Content Views
        @assert: Content views cannot be promoted; handled gracefully
        @status: Manual
        """

    # Content Views: publish
    # katello content definition publish --label=MyView

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

    def test_cv_publish_custom_content(self):
        """
        @test: attempt to publish a content view containing custom content
        @feature: Content Views
        @setup: Multiple environments for an org; custom content synced
        @assert: Content view can be published
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Fetch it
        result = Repository.info({u'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repository was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repo was not synchronized")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})
        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(result.return_code, 0,
                         "Repo was not associated to selected CV")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing a new version of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(result.stdout['repositories'][0]['name'],
                         new_repo['name'], "Repo was not associated to CV")
        self.assertEqual(result.stdout['versions'][0]['version'], u'1',
                         "Publishing new version of CV was not successful")

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
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Fetch it
        result = Repository.info({u'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repository was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repo was not synchronized")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})
        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(result.return_code, 0,
                         "Repo was not associated to selected CV")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing a new version of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Create CV
        con_view = make_content_view({'organization-id': self.org['label'],
                                      'composite': True})

        # Assert whether content view creation was successful
        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Associate version to composite CV
        result = ContentView.add_version({u'id': con_view['id'],
                                          u'version-id': version1_id})
        self.assertEqual(result.return_code, 0,
                         "Repo was not associated to selected CV")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Assert whether version was associated to composite CV
        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(result.stdout['components'][0]['id'],
                         version1_id,
                         "version was not associated to composite CV")

        # Publish a new version of CV
        result = ContentView.publish({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing a version of composite CV not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Assert whether Version1 was created and exists in Library Env.
        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(result.stdout['environments'][0]['name'],
                         u'Library', "version1 does not exist in Library")
        self.assertEqual(result.stdout['versions'][0]['version'], u'1',
                         "Publishing new version of CV was not successful")

    @unittest.skip(NOT_IMPLEMENTED)
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
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Fetch it
        result = Repository.info({u'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repository was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repo was not synchronized")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})
        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(result.return_code, 0,
                         "Repo was not associated to selected CV")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Publish a version1 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing version1 of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Only after we publish version1 the info is populated.
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Actual assert for this test happens HERE
        # Test whether the version1 now belongs to Library
        result_version = ContentView.version_info({u'id': version1_id})
        self.assertEqual(result_version.return_code, 0,
                         "ContentView version was not found")
        self.assertEqual(len(result_version.stderr), 0,
                         "No error was expected")
        self.assertEqual(result_version.stdout['environments'][0]['label'],
                         u'Library', "This version not in Library")

        # Promotion of version1 to Dev env
        result = ContentView.version_promote(
            {u'id': version1_id,
             u'environment-id': self.env1['id']})
        self.assertEqual(result.return_code, 0,
                         "Promoting version1 of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # The only way to validate whether env has the version is to
        # validate that version has the env.
        result = ContentView.version_info(
            {u'id': version1_id})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(result.stdout['environments'][1]['id'],
                         self.env1['id'],
                         "Promotion of version1 not successful to the env")

        # Now Publish version2 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing version2 of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Only after we publish version2 the info is populated.
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Let us now store the version2 id
        version2_id = result.stdout['versions'][1]['id']

        # Test whether the version2 now belongs to Library
        result_version = ContentView.version_info(
            {u'id': version2_id})
        self.assertEqual(result_version.return_code, 0,
                         "ContentView version was not found")
        self.assertEqual(len(result_version.stderr), 0,
                         "No error was expected")
        self.assertEqual(result_version.stdout['environments'][0]['label'],
                         u'Library', "This version not in Library")

        # Promotion of version2 to Dev env
        result = ContentView.version_promote(
            {u'id': version2_id,
             u'environment-id': self.env1['id']})
        self.assertEqual(result.return_code, 0,
                         "Promoting version2 of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Actual assert for this test happens here.
        # Test whether the version2 now belongs to next env
        result = ContentView.version_info({u'id': version2_id})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(result.stdout['environments'][1]['id'],
                         self.env1['id'],
                         "Promotion of version2 not successful to the env")

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
        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Fetch it
        result = Repository.info({u'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repository was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0, "Repo was not synchronized")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['label']})
        # Fetch it
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "Content-View was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(result.return_code, 0,
                         "Repo was not associated to selected CV")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Publish a version1 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing version1 of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Only after we publish version1 the info is populated.
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Test whether the version1 now belongs to Library
        result_version = ContentView.version_info({u'id': version1_id})
        self.assertEqual(result_version.return_code, 0,
                         "ContentView version was not found")
        self.assertEqual(len(result_version.stderr), 0,
                         "No error was expected")
        self.assertEqual(result_version.stdout['environments'][0]['label'],
                         u'Library', "This version not in Library")

        # Promotion of version1 to Dev env
        result = ContentView.version_promote(
            {u'id': version1_id,
             u'environment-id': self.env1['id']})
        self.assertEqual(result.return_code, 0,
                         "Promoting version1 of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # The only way to validate whether env has the version is to
        # validate that version has the env.
        # Test whether the version1 now belongs to next env
        result = ContentView.version_info(
            {u'id': version1_id})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(result.stdout['environments'][1]['id'],
                         self.env1['id'],
                         "Promotion of version1 not successful to the env")

        # Now Publish version2 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing version2 of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # As per Dev Notes:
        # Similarly when I publish version y, version x goes away from Library.
        # Actual assert for this test happens here.
        # Test that version1 doesnot exist in Library after publishing version2
        result = ContentView.version_info({u'id': version1_id})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(len(result.stdout['environments']), 1,
                         "Version1 may still exist in Library")
        self.assertNotEqual(result.stdout['environments'][0]['label'],
                            u'Library', "Version1 still exists in Library")

        # Only after we publish version2 the info is populated.
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Let us now store the version2 id
        version2_id = result.stdout['versions'][1]['id']

        # Promotion of version2 to next env
        result = ContentView.version_promote(
            {u'id': version2_id,
             u'environment-id': self.env1['id']})
        self.assertEqual(result.return_code, 0,
                         "Promoting version2 of CV was not successful")
        self.assertEqual(len(result.stderr), 0, "No error was expected")

        # Actual assert for this test happens here.
        # Test that version1 doesnot exist in any/next env after,
        # promoting version2 to next env
        result = ContentView.version_info({u'id': version1_id})
        self.assertEqual(result.return_code, 0, "ContentView was not found")
        self.assertEqual(len(result.stderr), 0, "No error was expected")
        self.assertEqual(len(result.stdout['environments']), 0,
                         "version1 still exists in the next env")

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

    @data(*positive_create_data())
    def test_cv_roles_admin_user_negative(self, test_data):
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
        @setup: create a user without the Content View admin role
        @assert: User with admin role for content view can't perform all
        Variations above
        @status: Manual
        """

        no_rights_user = make_user()

        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        test_data['organization-id'] = org_obj['label']

        # test that user can't create
        result = ContentView.with_user(
            no_rights_user["login"],
            no_rights_user["password"]
            ).create(
            test_data
            )
        self.assertGreater(
            result.return_code, 0, "User shouldn't be able to create object")
        self.assertGreater(
            len(result.stderr), 0, "There should have been an exception here")

        # test that user can't read
        con_view = make_content_view(test_data)

        result = ContentView.with_user(
            no_rights_user["login"],
            no_rights_user["password"]
            ).info(
            {'id': con_view['id']})
        self.assertGreater(
            result.return_code, 0,
            "User shouldn't be able to create object")
        self.assertGreater(
            len(result.stderr), 0,
            "There should have been an exception here")

    @data(*positive_create_data())
    @bzbug("1092111")
    def test_cv_roles_readonly_user(self, test_data):
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
        readonly_rights_user = User()
        ApiCrud.record_create(readonly_rights_user)
        perm = ApiCrud.record_resolve(
            ContentViewDefinitionApi.permissions.resolve
            )
        add_permission_to_user(readonly_rights_user, perm)

        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        test_data['organization-id'] = org_obj['label']

        # test that user can read
        con_view = make_content_view(test_data)

        result = ContentView.with_user(
            readonly_rights_user.login,
            readonly_rights_user.password
            ).info({'id': con_view['id']})

        self.assertEqual(result.return_code, 0, "Failed to find object")
        self.assertEqual(con_view['name'], result.stdout['name'])

    @data(*positive_create_data())
    @bzbug("1092111")
    def test_cv_roles_readonly_user_negative(self, test_data):
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
        readonly_rights_user = User()
        ApiCrud.record_create(readonly_rights_user)
        readonly_rights_user = User()
        ApiCrud.record_create(readonly_rights_user)
        perm = ApiCrud.record_resolve(
            ContentViewDefinitionApi.permissions.resolve
            )
        add_permission_to_user(readonly_rights_user, perm)

        org_obj = make_org()

        result = Org.info({'id': org_obj['id']})
        self.assertEqual(result.return_code, 0, "Failed to create object")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an exception here")

        test_data['organization-id'] = org_obj['label']

        # test that user can't create
        result = ContentView.with_user(
            readonly_rights_user.login,
            readonly_rights_user.password
            ).create(test_data)
        self.assertGreater(
            result.return_code, 0, "User shouldn't be able to create object")
        self.assertGreater(
            len(result.stderr), 0, "There should have been an exception here")
