# -*- encoding: utf-8 -*-
"""Test class for Content Views"""
import random
import unittest2

from ddt import ddt
from fauxfactory import gen_alphanumeric, gen_string
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    CLIFactoryError,
    make_activation_key,
    make_content_host,
    make_content_view,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_repository,
    make_user,
)
from robottelo import manifests
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.subscription import Subscription
from robottelo.constants import FAKE_0_PUPPET_REPO, NOT_IMPLEMENTED
from robottelo.decorators import (
    data,
    run_only_on,
    skip_if_bug_open,
    stubbed,
)
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


def positive_create_data():
    """Random data for positive creation"""

    return (
        {'name': gen_string("latin1")},
        {'name': gen_string("utf8")},
        {'name': gen_string("alpha")},
        {'name': gen_string("alphanumeric")},
        {'name': gen_string("numeric", 20)},
        {'name': gen_string("html")},
    )


def negative_create_data():
    """Random data for negative creation"""

    return (
        {'name': ' '},
        {'name': gen_string('alpha', 300)},
        {'name': gen_string('numeric', 300)},
        {'name': gen_string('alphanumeric', 300)},
        {'name': gen_string('utf8', 300)},
        {'name': gen_string('latin1', 300)},
        {'name': gen_string('html', 300)},
    )


@run_only_on('sat')
@ddt
class TestContentView(CLITestCase):
    """Content View CLI tests"""

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
    rhel_content_org = None
    rhel_repo_name = None
    rhel_repo = None
    rhel_product_name = 'Red Hat Enterprise Linux Workstation'

    def create_rhel_content(self):
        if TestContentView.rhel_content_org is not None:
            return

        TestContentView.rhel_content_org = make_org()
        manifest = manifests.clone()
        upload_file(manifest)
        Subscription.upload({
            'file': manifest,
            'organization-id': TestContentView.rhel_content_org['id'],
        })

        RepositorySet.enable({
            'name': (
                'Red Hat Enterprise Virtualization Agents '
                'for RHEL 6 Workstation (RPMs)'
            ),
            'organization-id': TestContentView.rhel_content_org['id'],
            'product': 'Red Hat Enterprise Linux Workstation',
            'releasever': '6Workstation',
            'basearch': 'x86_64',
        })
        TestContentView.rhel_repo_name = (
            'Red Hat Enterprise Virtualization Agents '
            'for RHEL 6 Workstation '
            'RPMs x86_64 6Workstation'
        )

        result = Repository.info({
            u'name': TestContentView.rhel_repo_name,
            u'product': TestContentView.rhel_product_name,
            u'organization-id': self.rhel_content_org['id']
        })
        TestContentView.rhel_repo = result.stdout

        result = Repository.synchronize({
            'name': TestContentView.rhel_repo_name,
            'organization-id': TestContentView.rhel_content_org['id'],
            'product': TestContentView.rhel_product_name,
        })
        if result.return_code != 0:
            TestContentView.rhel_content_org = None
            self.fail("Couldn't synchronize repo")

    def setUp(self):  # noqa
        """Tests for content-view via Hammer CLI"""

        super(TestContentView, self).setUp()

        if TestContentView.org is None:
            TestContentView.org = make_org(cached=True)
        if TestContentView.env1 is None:
            TestContentView.env1 = make_lifecycle_environment(
                {u'organization-id': TestContentView.org['id']})
        if TestContentView.env2 is None:
            TestContentView.env2 = make_lifecycle_environment(
                {u'organization-id': TestContentView.org['id'],
                 u'prior': TestContentView.env1['label']})
        if TestContentView.product is None:
            TestContentView.product = make_product(
                {u'organization-id': TestContentView.org['id']},
                cached=True)

    @data(*positive_create_data())
    def test_cv_create_cli(self, test_data):
        # variations (subject to change):
        # ascii string, alphanumeric, latin-1, utf8, etc.
        """@test: create content views (positive)

        @feature: Content Views

        @assert: content views are created

        """
        try:
            test_data['organization-id'] = make_org(cached=True)['id']
            content_view = make_content_view(test_data)
        except CLIFactoryError as err:
            self.fail(err)

        self.assertEqual(content_view['name'], test_data['name'])

    @data(*negative_create_data())
    def test_cv_create_cli_negative(self, test_data):
        # variations (subject to change):
        # zero length, symbols, html, etc.
        """@test: create content views (negative)

        @feature: Content Views

        @assert: content views are not created; proper error thrown and
        system handles it gracefully

        """
        try:
            test_data['organization-id'] = make_org(cached=True)['id']
        except CLIFactoryError as err:
            self.fail(err)

        with self.assertRaises(CLIFactoryError):
            make_content_view(test_data)

    def test_cv_create_cli_badorg_negative(self):
        # Use an invalid org name
        """@test: create content views (negative)

        @feature: Content Views

        @assert: content views are not created; proper error thrown and
        system handles it gracefully

        """

        org_name = gen_string("alpha")
        con_name = gen_string("alpha")
        result = ContentView.create({'name': con_name,
                                     'organization-id': org_name})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    def test_cv_edit(self):
        """@test: edit content views - name, description, etc.

        @feature: Content Views

        @assert: edited content view save is successful and info is
        updated

        """
        try:
            con_view = make_content_view({
                'name': gen_string('utf8'),
                'organization-id': make_org(cached=True)['id']
            })
        except CLIFactoryError as err:
            self.fail(err)

        new_name = gen_string('utf8')
        result = ContentView.update({
            'id': con_view['id'],
            'name': new_name,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({'id': con_view['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['name'], new_name)

    @unittest2.skip(NOT_IMPLEMENTED)
    def test_cv_edit_rh_custom_spin(self):
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.
        """@test: edit content views for a custom rh spin.  For example,

        @feature: Content Views
        modify a filter

        @assert: edited content view save is successful and info is
        updated

        @status: Manual

        """

    def test_cv_delete(self):
        """@test: delete content views

        @feature: Content Views

        @assert: edited content view can be deleted and no longer
        appears in any content view UI updated

        """
        try:
            con_view = make_content_view({
                'organization-id': make_org(cached=True)['id']
            })
        except CLIFactoryError as err:
            self.fail(err)

        result = ContentView.delete({'id': con_view['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({'id': con_view['id']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    def test_delete_cv_version_name(self):
        """@test: Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'remove-from-environment' command and delete content view version from
        that content view. Use content view version name as a parameter.

        @feature: Content Views

        @assert: Content view version deleted successfully

        """
        cv = make_content_view({u'organization-id': self.org['id']})
        result = ContentView.publish({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['versions']), 1)
        cvv = result.stdout['versions'][0]

        env_id = result.stdout['lifecycle-environments'][0]['id']
        result = ContentView.remove_from_environment({
            u'id': cv['id'],
            u'lifecycle-environment-id': env_id,
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.version_delete({
            u'organization': self.org['name'],
            u'content-view': cv['name'],
            u'version': cvv['version'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['versions']), 0)

    def test_delete_cv_version_id(self):
        """@test: Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'remove-from-environment' command and delete content view version from
        that content view. Use content view version id as a parameter. Also,
        add repository to initial content view for better coverage.

        @feature: Content Views

        @assert: Content view version deleted successfully

        """
        # Create new organization, product and repository
        new_org = make_org({u'name': gen_alphanumeric()})
        new_product = make_product({u'organization-id': new_org['id']})
        new_repo = make_repository({u'product-id': new_product['id']})
        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        # Create new content-view and add repository to view
        new_cv = make_content_view({u'organization-id': new_org['id']})
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
            u'organization-id': new_org['id'],
        })
        self.assertEqual(result.return_code, 0)
        # Publish a version1 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        # Get the CV info
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['versions']), 1)
        # Store the associated environment_id
        env_id = result.stdout['lifecycle-environments'][0]['id']
        # Store the version1 id
        version1_id = result.stdout['versions'][0]['id']
        # Remove the CV from selected environment
        result = ContentView.remove_from_environment({
            u'id': new_cv['id'],
            u'lifecycle-environment-id': env_id,
        })
        self.assertEqual(result.return_code, 0)
        # Delete the version
        result = ContentView.version_delete({u'id': version1_id})
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['versions']), 0)

    def test_delete_cv_version_negative(self):
        """@test: Create content view and publish it. Try to delete content
        view version while content view is still associated with lifecycle
        environment

        @feature: Content Views

        @assert: Content view version is not deleted

        """
        cv = make_content_view({u'organization-id': self.org['id']})
        result = ContentView.publish({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['versions']), 1)
        cvv = result.stdout['versions'][0]
        # Try to delete content view version while it is in environment Library
        result = ContentView.version_delete({u'id': cvv['id']})
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)
        # Check that version was not actually removed from the cv
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout['versions']), 1)

    def test_remove_cv_environment(self):
        """@Test: Remove content view from lifecycle environment assignment

        @Feature: Content Views

        @Assert: Content view removed from environment successfully

        """
        new_org = make_org({u'name': gen_alphanumeric()})
        new_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': new_cv['id']})
        result = ContentView.info({u'id': new_cv['id']})
        env = result.stdout['lifecycle-environments'][0]

        result = ContentView.remove({
            u'id': new_cv['id'],
            u'environment-ids': env['id'],
            u'organization-id': new_org['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(result.stdout['lifecycle-environments']), 0)

    def test_remove_cv_env_and_reassign_key(self):
        """Test: Remove content view environment and re-assign activation key
        to another environment and content view

        @Feature: Content Views

        @Assert: Activation key re-assigned successfully

        """
        new_org = make_org({u'name': gen_alphanumeric()})
        env = [
            make_lifecycle_environment({u'organization-id': new_org['id']})
            for _ in range(2)
        ]

        source_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': source_cv['id']})
        result = ContentView.info({u'id': source_cv['id']})
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[0]['id'],
        })
        self.assertEqual(result.return_code, 0)

        destination_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': destination_cv['id']})
        result = ContentView.info({u'id': destination_cv['id']})
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[1]['id'],
        })
        self.assertEqual(result.return_code, 0)

        ac_key = make_activation_key({
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
            u'lifecycle-environment-id': env[0]['id'],
            u'content-view-id': source_cv['id'],
        })
        result = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(result.stdout['activation-keys'][0], ac_key['name'])
        result = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(len(result.stdout['activation-keys']), 0)

        result = ContentView.remove({
            u'id': source_cv['id'],
            u'environment-ids': env[0]['id'],
            u'key-content-view-id': destination_cv['id'],
            u'key-environment-id': env[1]['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(len(result.stdout['activation-keys']), 0)
        result = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(result.stdout['activation-keys'][0], ac_key['name'])

    def test_remove_cv_env_and_reassign_content_host(self):
        """Test: Remove content view environment and re-assign content host
        to another environment and content view

        @Feature: Content Views

        @Assert: Content host re-assigned successfully

        """
        new_org = make_org({u'name': gen_alphanumeric()})
        env = [
            make_lifecycle_environment({u'organization-id': new_org['id']})
            for _ in range(2)
        ]

        source_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': source_cv['id']})
        result = ContentView.info({u'id': source_cv['id']})
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[0]['id'],
        })
        self.assertEqual(result.return_code, 0)

        destination_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': destination_cv['id']})
        result = ContentView.info({u'id': destination_cv['id']})
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[1]['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(result.stdout['content-host-count'], '0')

        make_content_host({
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
            u'lifecycle-environment-id': env[0]['id'],
            u'content-view-id': source_cv['id'],
        })

        result = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(result.stdout['content-host-count'], '1')
        result = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(result.stdout['content-host-count'], '0')

        result = ContentView.remove({
            u'name': source_cv['name'],
            u'organization': new_org['name'],
            u'environment-ids': env[0]['id'],
            u'system-content-view-id': destination_cv['id'],
            u'system-environment-id': env[1]['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(result.stdout['content-host-count'], '0')
        result = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(result.stdout['content-host-count'], '1')

    def test_remove_cv_version(self):
        """@Test: Delete content view version through 'remove' command

        @Feature: Content Views

        @Assert: Content view version deleted successfully

        """
        new_org = make_org({u'name': gen_alphanumeric()})
        new_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': new_cv['id']})
        result = ContentView.info({u'id': new_cv['id']})
        env = result.stdout['lifecycle-environments'][0]
        cvv = result.stdout['versions'][0]
        result = ContentView.remove_from_environment({
            u'id': new_cv['id'],
            u'lifecycle-environment-id': env['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.remove({
            u'id': new_cv['id'],
            u'content-view-version-ids': cvv['id'],
            u'organization-id': new_org['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(result.stdout['versions']), 0)

    def test_cv_composite_create(self):
        # Note: puppet repos cannot/should not be used in this test
        # It shouldn't work - and that is tested in a different case.
        # Individual modules from a puppet repo, however, are a valid
        # variation.
        """@test: create a composite content view

        @feature: Content Views

        @setup: sync multiple content source/types (RH, custom, etc.)

        @assert: Composite content views are created

        """

        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({u'id': new_cv['id'],
                                             u'repository-id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0,
                         "Publishing a new version of CV was not successful")
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Create CV
        try:
            con_view = make_content_view({
                'organization-id': self.org['id'],
                'composite': True
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Associate version to composite CV
        result = ContentView.add_version({
            u'id': con_view['id'],
            u'content-view-version-id': version1_id,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Assert whether version was associated to composite CV
        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(result.stdout['components'][0]['id'],
                         version1_id,
                         "version was not associated to composite CV")

    # Content Views: Adding products/repos
    # katello content definition add_filter --label=MyView
    #   --filter=stable --org=ACME
    # katello content definition add_product --label=MyView
    #   --product=product1 --org=ACME
    # katello content definition add_repo --label=MyView
    #   --repo=repo1 --org=ACME

    def test_associate_view_rh(self):
        """@test: associate Red Hat content in a view

        @feature: Content Views

        @setup: Sync RH content

        @assert: RH Content can be seen in a view

        """
        self.create_rhel_content()
        # Create CV
        try:
            new_cv = make_content_view({
                u'organization-id': self.rhel_content_org['id']
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': TestContentView.rhel_repo['id'],
            u'organization-id': TestContentView.rhel_content_org['id'],
        })

        self.assertEqual(
            result.return_code, 0,
            'Repository was not associated to selected CV'
        )
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['yum-repositories'][0]['name'], self.rhel_repo_name,
            'Repo was not associated to CV'
        )

    def test_associate_view_rh_custom_spin(self):
        """@test: associate Red Hat content in a view

        @feature: Content Views

        @setup: Sync RH content

        @steps: 1. Assure filter(s) applied to associated content

        @assert: Filtered RH content only is available/can be seen in a view

        """
        self.create_rhel_content()
        # Create CV
        try:
            new_cv = make_content_view({
                u'organization-id': self.rhel_content_org['id']
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': TestContentView.rhel_repo['id'],
            u'organization-id': TestContentView.rhel_content_org['id'],
        })

        self.assertEqual(
            result.return_code, 0,
            'Repository was not associated to selected CV'
        )
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['yum-repositories'][0]['name'],
            TestContentView.rhel_repo_name,
            'Repo was not associated to CV'
        )

        name = gen_string('alphanumeric')
        result_flt = ContentView.filter_create({
            'content-view-id': new_cv['id'],
            'type': 'rpm',
            'inclusion': 'true',
            'name': name,
        })
        self.assertEqual(result_flt.return_code, 0)
        self.assertEqual(len(result_flt.stderr), 0)

        result_rl = ContentView.filter_rule_create({
            'content-view-id': new_cv['id'],
            'name': 'walgrind',
            'content-view-filter': name,
        })
        self.assertEqual(
            result.return_code, 0,
            'Filter rule was not created'
        )
        self.assertEqual(len(result_rl.stderr), 0)

    def test_associate_view_custom_content(self):
        """@test: associate Red Hat content in a view

        @feature: Content Views

        @setup: Sync custom content

        @assert: Custom content can be seen in a view

        """
        try:
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(
            result.return_code, 0,
            'Repository was not synchronized'
        )
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            'Repository was not associated to selected CV'
        )
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV'
        )

    def test_add_custom_repos_with_name(self):
        """@test: add custom repos to cv with names

        @feature: Content Views - add_repos via names

        @assert: whether repos are added to cv.

        """
        try:
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(
            result.return_code, 0,
            'Repository was not synchronized'
        )
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV with names.
        result = ContentView.add_repository({
            u'name': new_cv['name'],
            u'repository': new_repo['name'],
            u'organization': self.org['name'],
            u'product': self.product['name'],
        })
        self.assertEqual(
            result.return_code, 0,
            'Repository was not associated to selected CV'
        )
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV'
        )

    def test_cv_associate_puppet_repo_negative(self):
        # Again, individual modules should be ok.
        """@test: attempt to associate puppet repos within a custom
        content view

        @feature: Content Views

        @assert: User cannot create a composite content view
        that contains direct puppet repos.

        """
        try:
            new_repo = make_repository({
                u'product-id': self.product['id'],
                u'content-type': u'puppet',
                u'url': FAKE_0_PUPPET_REPO,
            })
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate puppet repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    def test_cv_associate_components_composite_negative(self):
        """@test: attempt to associate components in a non-composite
        content view

        @feature: Content Views

        @assert: User cannot add components to the view

        """
        try:
            # Create REPO
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Create component CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Fetch version id
        cv_version = ContentView.version_list({
            u'content-view-id': new_cv['id']
        })
        self.assertEqual(cv_version.return_code, 0)
        self.assertEqual(len(cv_version.stderr), 0)

        # Create non-composite CV
        with self.assertRaises(CLIFactoryError):
            result = make_content_view({
                u'organization-id': self.org['id'],
                u'component-ids': cv_version.stdout[0]['id'],
            })

    def test_cv_associate_composite_dupe_repos_negative(self):
        """@test: attempt to associate the same repo multiple times within a
        content view

        @feature: Content Views

        @assert: User cannot add repos multiple times to the view

        """
        try:
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(
            result.return_code, 0,
            'Repository was not synchronized'
        )
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            'Repository was not associated to selected CV'
        )
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['yum-repositories'][0]['name'], new_repo['name'],
            'Repo was not associated to CV'
        )
        repos_length = len(result.stdout['yum-repositories'])

        # Re-associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            'Repository was not associated to selected CV'
        )
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            len(result.stdout['yum-repositories']), repos_length,
            'No new entry of same repo is expected'
        )

    @skip_if_bug_open('bugzilla', 1162799)
    @skip_if_bug_open('bugzilla', 1222118)
    def test_cv_associate_composite_dupe_modules_negative(self):
        """@test: attempt to associate duplicate puppet module(s) within a
        content view

        @feature: Content Views

        @assert: User cannot add modules multiple times to the view

        @bz: 1162799, 1222118

        """
        try:
            repository = make_repository({
                u'content-type': u'puppet',
                u'product-id': self.product['id'],
                u'url': FAKE_0_PUPPET_REPO,
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': repository['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = Repository.info({'id': repository['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        puppet_modules = int(result.stdout['content-counts']['puppet-modules'])

        # Create CV
        try:
            content_view = make_content_view({
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Fetch puppet module
        puppet_result = PuppetModule.list({
            u'repository-id': repository['id'],
            u'per-page': False,
        })
        self.assertEqual(puppet_result.return_code, 0)
        self.assertEqual(len(puppet_result.stderr), 0)
        self.assertEqual(len(puppet_result.stdout), puppet_modules)

        for puppet_module in puppet_result.stdout:
            # Associate puppet module to CV
            result = ContentView.puppet_module_add({
                u'content-view-id': content_view['id'],
                u'name': puppet_module['name']
            })
            self.assertEqual(result.return_code, 0)
            self.assertEqual(len(result.stderr), 0)

            # Re-associate same puppet module to CV
            result = ContentView.puppet_module_add({
                u'content-view-id': content_view['id'],
                u'name': puppet_module['name'],
            })
            self.assertNotEqual(
                result.return_code, 0,
                'An already added puppet module should not be added twice'
            )
            self.assertGreater(len(result.stderr), 0)

    # Content View: promotions
    # katello content view promote --label=MyView --env=Dev --org=ACME
    # katello content view promote --view=MyView --env=Staging --org=ACME

    @skip_if_bug_open('bugzilla', 1156629)
    def test_cv_promote_rh(self):
        """@test: attempt to promote a content view containing RH content

        @feature: Content Views

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted

        @bz: 1156629

        """
        self.create_rhel_content()
        # Create CV
        try:
            new_cv = make_content_view({
                u'organization-id': self.rhel_content_org['id']
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': self.rhel_repo['id']
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            "Publishing a new version of CV was not successful")
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        env1 = make_lifecycle_environment({
            u'organization-id': TestContentView.rhel_content_org['id']
        })

        # Promote the Published version of CV to the next env
        result = ContentView.version_promote({
            u'id': result.stdout['versions'][0]['id'],
            u'to-lifecycle-environment-id': env1['id'],
        })
        self.assertEqual(result.return_code, 0,
                         "Promoting a version of CV was not successful")
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        environment = {
            'id': env1['id'],
            'name': env1['name'],
        }
        self.assertIn(environment, result.stdout['lifecycle-environments'])

    @unittest2.skip(NOT_IMPLEMENTED)
    def test_cv_promote_rh_custom_spin(self):
        """@test: attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.

        @feature: Content Views

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted

        @status: Manual

        """

    @skip_if_bug_open('bugzilla', 1156629)
    def test_cv_promote_custom_content(self):
        """@test: attempt to promote a content view containing custom content

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be promoted

        @bz: 1156629

        """
        try:
            # Create REPO
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Promote the Published version of CV to the next env
        result = ContentView.version_promote({
            u'id': result.stdout['versions'][0]['id'],
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertIn(
            {u'id': self.env1['id'], u'name': self.env1['name']},
            result.stdout['lifecycle-environments'],
        )

    @skip_if_bug_open('bugzilla', 1156629)
    def test_cv_promote_composite(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """@test: attempt to promote a content view containing custom content

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @steps: create a composite view containing multiple content types

        @assert: Content view can be promoted

        @bz: 1156629

        """
        try:
            # Create REPO
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Create CV
        try:
            con_view = make_content_view({
                'organization-id': self.org['id'],
                'composite': True
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Associate version to composite CV
        result = ContentView.add_version({
            u'id': con_view['id'],
            u'content-view-version-id': version1_id,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # As version info is populated after publishing only
        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Promote the Published version of CV to the next env
        result = ContentView.version_promote({
            u'id': result.stdout['versions'][0]['id'],
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': con_view['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertIn(
            {u'id': self.env1['id'], u'name': self.env1['name']},
            result.stdout['lifecycle-environments'],
        )

    def test_cv_promote_defaultcv_negative(self):
        """@test: attempt to promote the default content views

        @feature: Content Views

        @assert: Default content views cannot be promoted

        """
        result = ContentView.list(
            {u'organization-id': self.org['id']},
            per_page=False
        )
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        content_view = random.choice([
            cv for cv in result.stdout
            if cv['name'] == u'Default Organization View'
        ])

        # Promote the Default CV to the next env
        result = ContentView.version_promote({
            u'id': content_view['content-view-id'],
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(
            len(result.stderr), 0,
            'There should be an exception here.'
        )

    @skip_if_bug_open('bugzilla', 1156629)
    def test_cv_promote_badenvironment_negative(self):
        """@test: attempt to promote a content view using an invalid environment

        @feature: Content Views

        @assert: Content views cannot be promoted; handled gracefully

        @BZ: 1156629

        """
        try:
            # Create REPO
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Promote the Published version of CV,
        # to the previous env which is Library
        result = ContentView.version_promote({
            u'id': result.stdout['versions'][0]['id'],
            u'to-lifecycle-environment-id': result.stdout[
                'lifecycle-environments'][0]['id'],
        })
        self.assertNotEqual(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

    # Content Views: publish
    # katello content definition publish --label=MyView

    def test_cv_publish_rh(self):
        """@test: attempt to publish a content view containing RH content

        @feature: Content Views

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be published

        """
        self.create_rhel_content()
        # Create CV
        try:
            new_cv = make_content_view({
                u'organization-id': self.rhel_content_org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': TestContentView.rhel_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            'Publishing a new version of CV was not successful'
        )
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['yum-repositories'][0]['name'],
            self.rhel_repo['name'],
            'Repo was not associated to CV'
        )
        self.assertEqual(
            result.stdout['versions'][0]['version'], u'1.0',
            'Publishing new version of CV was not successful'
        )

    @unittest2.skip(NOT_IMPLEMENTED)
    def test_cv_publish_rh_custom_spin(self):
        """@test: attempt to publish  a content view containing a custom RH
        spin - i.e., contains filters.

        @feature: Content Views

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be published

        @status: Manual

        """

    def test_cv_publish_custom_content(self):
        """@test: attempt to publish a content view containing custom content

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be published

        """
        try:
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            'Publishing a new version of CV was not successful'
        )
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['yum-repositories'][0]['name'], new_repo['name'],
            'Repo was not associated to CV'
        )
        self.assertEqual(
            result.stdout['versions'][0]['version'], u'1.0',
            'Publishing new version of CV was not successful'
        )

    def test_cv_publish_composite(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """@test: attempt to publish  a content view containing custom content

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be published

        """
        try:
            repository = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': repository['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            content_view = make_content_view({
                u'organization-id': self.org['id'],
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': content_view['id'],
            u'repository-id': repository['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a new version of CV
        result = ContentView.publish({u'id': content_view['id']})
        self.assertEqual(
            result.return_code, 0,
            'Publishing a new version of CV was not successful'
        )
        self.assertEqual(len(result.stderr), 0)

        result = ContentView.info({u'id': content_view['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Create composite CV
        try:
            composite_cv = make_content_view({
                'organization-id': self.org['id'],
                'composite': True
            })
        except CLIFactoryError as err:
            self.fail(err)

        # Associate version to composite CV
        result = ContentView.add_version({
            u'id': composite_cv['id'],
            u'content-view-version-id': version1_id,
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Assert whether version was associated to composite CV
        result = ContentView.info({u'id': composite_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['components'][0]['id'], version1_id,
            'version was not associated to composite CV'
        )

        # Publish a new version of CV
        result = ContentView.publish({u'id': composite_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            'Publishing a version of composite CV not successful'
        )
        self.assertEqual(len(result.stderr), 0)

        # Assert whether Version1 was created and exists in Library Env.
        result = ContentView.info({u'id': composite_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['lifecycle-environments'][0]['name'], u'Library',
            'version1 does not exist in Library'
        )
        self.assertEqual(
            result.stdout['versions'][0]['version'], u'1.0',
            'Publishing new version of CV was not successful'
        )

    def test_cv_publish_version_changes_in_target_env(self):
        # Dev notes:
        # If Dev has version x, then when I promote version y into
        # Dev, version x goes away (ie when I promote version 1 to Dev,
        # version 3 goes away)
        """@test: when publishing new version to environment, version
        gets updated

        @feature: Content Views

        @setup: Multiple environments for an org; multiple versions
        of a content view created/published

        @steps:
        1. publish a view to an environment noting the CV version
        2. edit and republish a new version of a CV

        @assert: Content view version is updated intarget environment.

        """
        try:
            # Create REPO
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a version1 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            "Publishing version1 of CV was not successful"
        )
        self.assertEqual(len(result.stderr), 0)

        # Only after we publish version1 the info is populated.
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Actual assert for this test happens HERE
        # Test whether the version1 now belongs to Library
        result_version = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            result_version.return_code, 0,
            "ContentView version 1 was not found"
        )
        self.assertEqual(len(result_version.stderr), 0)
        self.assertEqual(
            result_version.stdout['lifecycle-environments'][0]['label'],
            u'Library',
            'Version 1 is not in Library'
        )

        # Promotion of version1 to Dev env
        result = ContentView.version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            "Promoting version1 of CV was not successful"
        )
        self.assertEqual(len(result.stderr), 0)

        # The only way to validate whether env has the version is to
        # validate that version has the env.
        result = ContentView.version_info({u'id': version1_id})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['lifecycle-environments'][1]['id'],
            self.env1['id'],
            "Promotion of version1 not successful to the env"
        )

        # Now Publish version2 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            "Publishing version2 of CV was not successful"
        )
        self.assertEqual(len(result.stderr), 0)

        # Only after we publish version2 the info is populated.
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Let us now store the version2 id
        version2_id = result.stdout['versions'][1]['id']

        # Test whether the version2 now belongs to Library
        result_version = ContentView.version_info({u'id': version2_id})
        self.assertEqual(
            result_version.return_code, 0,
            "ContentView version 2 was not found"
        )
        self.assertEqual(len(result_version.stderr), 0)
        self.assertEqual(
            result_version.stdout['lifecycle-environments'][0]['label'],
            u'Library',
            'Version 2 not in Library'
        )

        # Promotion of version2 to Dev env
        result = ContentView.version_promote({
            u'id': version2_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            "Promoting version2 of CV was not successful"
        )
        self.assertEqual(len(result.stderr), 0)

        # Actual assert for this test happens here.
        # Test whether the version2 now belongs to next env
        result = ContentView.version_info({u'id': version2_id})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['lifecycle-environments'][1]['id'],
            self.env1['id'],
            "Promotion of version2 not successful to the env"
        )

    def test_cv_publish_version_changes_in_source_env(self):
        # Dev notes:
        # Similarly when I publish version y, version x goes away from
        # Library (ie when I publish version 2, version 1 disappears)
        """@test: when publishing new version to environment, version
        gets updated
        @feature: Content Views

        @setup: Multiple environments for an org; multiple versions
        of a content view created/published

        @steps:
        1. publish a view to an environment
        2. edit and republish a new version of a CV

        @assert: Content view version is updated in source environment.

        """
        try:
            # Create REPO
            new_repo = make_repository({u'product-id': self.product['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Sync REPO
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Create CV
        try:
            new_cv = make_content_view({u'organization-id': self.org['id']})
        except CLIFactoryError as err:
            self.fail(err)

        # Associate repo to CV
        result = ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Publish a version1 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            "Publishing version1 of CV was not successful"
        )
        self.assertEqual(len(result.stderr), 0)

        # Only after we publish version1 the info is populated.
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Let us now store the version1 id
        version1_id = result.stdout['versions'][0]['id']

        # Test whether the version1 now belongs to Library
        result_version = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            result_version.return_code, 0,
            "ContentView version 1 was not found"
        )
        self.assertEqual(len(result_version.stderr), 0)
        self.assertEqual(
            result_version.stdout['lifecycle-environments'][0]['label'],
            u'Library',
            'Version 1 is not in Library'
        )

        # Promotion of version1 to Dev env
        result = ContentView.version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            "Promoting version1 of CV was not successful"
        )
        self.assertEqual(len(result.stderr), 0)

        # The only way to validate whether env has the version is to
        # validate that version has the env.
        # Test whether the version1 now belongs to next env
        result = ContentView.version_info({u'id': version1_id})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            result.stdout['lifecycle-environments'][1]['id'],
            self.env1['id'],
            "Promotion of version1 not successful to the env"
        )

        # Now Publish version2 of CV
        result = ContentView.publish({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0,
            "Publishing version2 of CV was not successful"
        )
        self.assertEqual(len(result.stderr), 0)

        # As per Dev Notes:
        # Similarly when I publish version y, version x goes away from Library.
        # Actual assert for this test happens here.
        # Test that version1 doesnot exist in Library after publishing version2
        result = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            result.return_code, 0, "ContentView version 1 was not found"
        )
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            len(result.stdout['lifecycle-environments']), 1,
            "Version1 may still exist in Library"
        )
        self.assertNotEqual(
            result.stdout['lifecycle-environments'][0]['label'],
            u'Library',
            'Version1 still exists in Library'
        )

        # Only after we publish version2 the info is populated.
        result = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            result.return_code, 0, "ContentView version 2 was not found"
        )
        self.assertEqual(len(result.stderr), 0)

        # Let us now store the version2 id
        version2_id = result.stdout['versions'][1]['id']

        # Promotion of version2 to next env
        result = ContentView.version_promote({
            u'id': version2_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        self.assertEqual(
            result.return_code, 0,
            "Promoting version2 of CV was not successful"
        )
        self.assertEqual(len(result.stderr), 0)

        # Actual assert for this test happens here.
        # Test that version1 doesnot exist in any/next env after,
        # promoting version2 to next env
        result = ContentView.version_info({u'id': version1_id})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)
        self.assertEqual(
            len(result.stdout['lifecycle-environments']), 0,
            "version1 still exists in the next env"
        )

    def test_cv_subscribe_system(self):
        """@test: Attempt to subscribe content host to content view

        @feature: Content Views

        @assert: Content host can be subscribed to content view

        """
        new_org = make_org()
        env = make_lifecycle_environment({u'organization-id': new_org['id']})
        cv = make_content_view({u'organization-id': new_org['id']})
        result = ContentView.publish({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '0')

        make_content_host({
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
            u'lifecycle-environment-id': env['id'],
            u'content-view-id': cv['id'],
        })
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '1')

    def test_cv_subscribe_system_rh(self):
        """@test: Attempt to subscribe content host to content view that has
        Red Hat repository assigned to it

        @feature: Content Views

        @assert: Content Host can be subscribed to content view with Red Hat
        repository

        """
        self.create_rhel_content()
        env = make_lifecycle_environment({
            u'organization-id': self.rhel_content_org['id'],
        })
        cv = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        result = ContentView.add_repository({
            u'id': cv['id'],
            u'repository-id': TestContentView.rhel_repo['id'],
            u'organization-id': TestContentView.rhel_content_org['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stdout['yum-repositories'][0]['name'],
            self.rhel_repo_name,
        )
        result = ContentView.publish({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '0')

        make_content_host({
            u'name': gen_alphanumeric(),
            u'organization-id': self.rhel_content_org['id'],
            u'lifecycle-environment-id': env['id'],
            u'content-view-id': cv['id'],
        })
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '1')

    def test_cv_subscribe_system_rh_spin(self):
        """@test: Attempt to subscribe content host to filtered content view
        that has Red Hat repository assigned to it

        @feature: Content Views

        @assert: Content Host can be subscribed to filtered content view with
        Red Hat repository

        """
        self.create_rhel_content()
        env = make_lifecycle_environment({
            u'organization-id': self.rhel_content_org['id'],
        })
        cv = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        result = ContentView.add_repository({
            u'id': cv['id'],
            u'repository-id': TestContentView.rhel_repo['id'],
            u'organization-id': TestContentView.rhel_content_org['id'],
        })
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(
            result.stdout['yum-repositories'][0]['name'],
            self.rhel_repo_name,
        )

        name = gen_string('utf8')
        result = ContentView.filter_create({
            'content-view-id': cv['id'],
            'type': 'rpm',
            'inclusion': 'true',
            'name': name,
        })
        self.assertEqual(result.return_code, 0)

        result_rl = ContentView.filter_rule_create({
            'content-view-id': cv['id'],
            'name': gen_string('utf8'),
            'content-view-filter': name,
        })
        self.assertEqual(result_rl.return_code, 0)

        result = ContentView.publish({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '0')

        make_content_host({
            u'name': gen_alphanumeric(),
            u'organization-id': self.rhel_content_org['id'],
            u'lifecycle-environment-id': env['id'],
            u'content-view-id': cv['id'],
        })
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '1')

    def test_cv_subscribe_system_custom(self):
        """@test: Attempt to subscribe content host to content view that has
        custom repository assigned to it

        @feature: Content Views

        @assert: Content Host can be subscribed to content view with custom
        repository

        """
        new_org = make_org()
        new_product = make_product({u'organization-id': new_org['id']})
        new_repo = make_repository({u'product-id': new_product['id']})
        env = make_lifecycle_environment({u'organization-id': new_org['id']})
        result = Repository.synchronize({'id': new_repo['id']})
        self.assertEqual(result.return_code, 0)
        cv = make_content_view({u'organization-id': new_org['id']})
        result = ContentView.add_repository({
            u'id': cv['id'],
            u'repository-id': new_repo['id'],
            u'organization-id': new_org['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.publish({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '0')

        make_content_host({
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
            u'lifecycle-environment-id': env['id'],
            u'content-view-id': cv['id'],
        })
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '1')

    def test_cv_subscribe_system_composite(self):
        """@test: Attempt to subscribe content host to composite content view

        @feature: Content Views

        @assert: Content host can be subscribed to composite content view

        """
        new_org = make_org()
        env = make_lifecycle_environment({u'organization-id': new_org['id']})
        cv = make_content_view({
            'organization-id': new_org['id'],
            'composite': True,
        })
        result = ContentView.publish({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '0')

        make_content_host({
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
            u'lifecycle-environment-id': env['id'],
            u'content-view-id': cv['id'],
        })
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '1')

    @skip_if_bug_open('bugzilla', 1222118)
    def test_cv_subscribe_system_puppet(self):
        """@test: Attempt to subscribe content host to content view that has
        puppet module assigned to it

        @feature: Content Views

        @assert: Content Host can be subscribed to content view with puppet
        module

        @bz: 1222118

        """
        new_org = make_org()
        new_product = make_product({u'organization-id': new_org['id']})

        repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': new_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        result = Repository.synchronize({'id': repository['id']})
        self.assertEqual(result.return_code, 0)

        cv = make_content_view({u'organization-id': new_org['id']})

        puppet_result = PuppetModule.list({
            u'repository-id': repository['id'],
            u'per-page': False,
        })
        self.assertEqual(puppet_result.return_code, 0)

        for puppet_module in puppet_result.stdout:
            # Associate puppet module to CV
            result = ContentView.puppet_module_add({
                u'content-view-id': cv['id'],
                u'name': puppet_module['name']
            })
            self.assertEqual(result.return_code, 0)

        env = make_lifecycle_environment({u'organization-id': new_org['id']})

        result = ContentView.publish({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        cvv = result.stdout['versions'][0]
        result = ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        self.assertEqual(result.return_code, 0)

        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '0')

        make_content_host({
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
            u'lifecycle-environment-id': env['id'],
            u'content-view-id': cv['id'],
        })
        result = ContentView.info({u'id': cv['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(result.stdout['content-host-count'], '1')

    @unittest2.skip(NOT_IMPLEMENTED)
    def test_cv_clone_within_same_env(self):
        # Dev note: "not implemented yet"
        """@test: attempt to create new content view based on existing
        view within environment
        @feature: Content Views

        @assert: Content view can be published

        @status: Manual

        """

    @unittest2.skip(NOT_IMPLEMENTED)
    def test_cv_clone_within_diff_env(self):
        # Dev note: "not implemented yet"
        """@test: attempt to create new content view based on existing
        view, inside a different environment

        @feature: Content Views

        @assert: Content view can be published

        @status: Manual

        """

    @unittest2.skip(NOT_IMPLEMENTED)
    def test_cv_refresh_errata_to_new_view_in_same_env(self):
        """@test: attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment

        @feature: Content Views

        @assert: Content view can be published

        @status: Manual

        """

    @unittest2.skip(NOT_IMPLEMENTED)
    def test_cv_dynflow_restart_promote(self):
        """@test: attempt to restart a promotion

        @feature: Content Views

        @steps:
        1. (Somehow) cause a CV promotion to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart promotion

        @assert: Promotion is restarted.

        @status: Manual

        """

    @unittest2.skip(NOT_IMPLEMENTED)
    def test_cv_dynflow_restart_publish(self):
        """@test: attempt to restart a publish

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
        """@test: attempt to view content views

        @feature: Content Views

        @setup: create a user without the Content View admin role

        @assert: User with admin role for content view can't perform all
        Variations above

        @status: Manual

        """
        password = gen_alphanumeric()
        no_rights_user = make_user({'password': password})
        no_rights_user['password'] = password

        try:
            test_data['organization-id'] = make_org(cached=True)['id']
        except CLIFactoryError as err:
            self.fail(err)

        # test that user can't create
        result = ContentView.with_user(
            no_rights_user["login"],
            no_rights_user["password"]
        ).create(
            test_data
        )
        self.assertGreater(result.return_code, 0)
        self.assertGreater(len(result.stderr), 0)

        # test that user can't read
        try:
            con_view = make_content_view(test_data)
        except CLIFactoryError as err:
            self.fail(err)

        result = ContentView.with_user(
            no_rights_user["login"],
            no_rights_user["password"]
        ).info(
            {'id': con_view['id']}
        )
        self.assertGreater(
            result.return_code, 0,
            "User shouldn't be able to create object")
        self.assertGreater(
            len(result.stderr), 0,
            "There should have been an exception here")

    @stubbed()
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
        """@test: attempt to view content views

        @feature: Content Views

        @setup: create a user with the Content View read-only role

        @assert: User with read-only role for content view can perform all
        Variations above

        @status: Manual

        """

    @stubbed()
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
        """@test: attempt to view content views

        @feature: Content Views

        @setup: create a user withOUT the Content View read-only role

        @assert: User withOUT read-only role for content view can perform all
        Variations above

        @status: Manual

        """
