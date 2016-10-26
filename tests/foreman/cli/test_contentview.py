"""Test class for Content Views

@Requirement: Contentview

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
import random

from fauxfactory import gen_alphanumeric, gen_string
from robottelo import manifests, ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    CLIFactoryError,
    make_activation_key,
    make_content_view,
    make_content_view_filter,
    make_content_view_filter_rule,
    make_filter,
    make_fake_host,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_repository,
    make_role,
    make_user,
)
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.subscription import Subscription
from robottelo.cli.user import User
from robottelo.constants import (
    DEFAULT_CV,
    DEFAULT_ROLE,
    DOCKER_REGISTRY_HUB,
    ENVIRONMENT,
    FAKE_0_PUPPET_REPO,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_1_YUM_REPO,
    FEDORA23_OSTREE_REPO,
    PERMISSIONS,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.decorators.host import skip_if_os
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase


class ContentViewTestCase(CLITestCase):
    """Content View CLI tests"""

    org = None
    product = None
    env1 = None
    env2 = None
    rhel_content_org = None
    rhel_repo_name = None
    rhel_repo = None

    def create_rhel_content(self):
        """Enable/Synchronize rhel content"""
        if ContentViewTestCase.rhel_content_org is not None:
            return

        try:
            ContentViewTestCase.rhel_content_org = make_org()
            with manifests.clone() as manifest:
                upload_file(manifest.content, manifest.filename)
            Subscription.upload({
                'file': manifest.filename,
                'organization-id': ContentViewTestCase.rhel_content_org['id'],
            })

            RepositorySet.enable({
                'name': REPOSET['rhva6'],
                'organization-id': ContentViewTestCase.rhel_content_org['id'],
                'product': PRDS['rhel'],
                'releasever': '6Server',
                'basearch': 'x86_64',
            })
            ContentViewTestCase.rhel_repo_name = REPOS['rhva6']['name']

            ContentViewTestCase.rhel_repo = Repository.info({
                u'name': ContentViewTestCase.rhel_repo_name,
                u'organization-id': self.rhel_content_org['id'],
                u'product': PRDS['rhel'],
            })

            Repository.synchronize({
                'name': ContentViewTestCase.rhel_repo_name,
                'organization-id': ContentViewTestCase.rhel_content_org['id'],
                'product': PRDS['rhel'],
            })
        except CLIReturnCodeError:
            # Make sure to reset rhel_content_org and let the exception
            # propagate.
            ContentViewTestCase.rhel_content_org = None
            raise

    # pylint: disable=unexpected-keyword-arg
    def setUp(self):
        """Tests for content-view via Hammer CLI"""

        super(ContentViewTestCase, self).setUp()

        if ContentViewTestCase.org is None:
            ContentViewTestCase.org = make_org(cached=True)
        if ContentViewTestCase.env1 is None:
            ContentViewTestCase.env1 = make_lifecycle_environment(
                {u'organization-id': ContentViewTestCase.org['id']})
        if ContentViewTestCase.env2 is None:
            ContentViewTestCase.env2 = make_lifecycle_environment(
                {u'organization-id': ContentViewTestCase.org['id'],
                 u'prior': ContentViewTestCase.env1['label']})
        if ContentViewTestCase.product is None:
            ContentViewTestCase.product = make_product(
                {u'organization-id': ContentViewTestCase.org['id']},
                cached=True)

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """create content views with different names

        @id: a154308c-3982-4cf1-a236-3051e740970e

        @assert: content views are created

        """
        for name in generate_strings_list(exclude_types=['cjk']):
            with self.subTest(name):
                content_view = make_content_view({
                    'name': name,
                    'organization-id': make_org(cached=True)['id'],
                })
                self.assertEqual(content_view['name'], name)

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    def test_negative_create_with_invalid_name(self):
        """create content views with invalid names

        @id: 83046271-76f9-4cda-b579-a2fe63493295

        @assert: content views are not created; proper error thrown and
        system handles it gracefully

        """
        org_id = make_org(cached=True)['id']
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    make_content_view({
                        'name': name,
                        'organization-id': org_id,
                    })

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_org_name(self):
        # Use an invalid org name
        """Create content view with invalid org name

        @id: f8b76e98-ccc8-41ac-af04-541650e8f5ba

        @assert: content views are not created; proper error thrown and
        system handles it gracefully

        """
        with self.assertRaises(CLIReturnCodeError):
            ContentView.create({'organization-id': gen_string('alpha')})

    @tier1
    def test_positive_create_empty_and_verify_files(self):
        """Create an empty content view and make sure no files are created at
        /var/lib/pulp/published.

        @id: 0e31573d-bf02-44ae-b3f4-d8aae450ba5e

        @Assert: Content view is published and no file is present at
        /var/lib/pulp/published.
        """
        content_view = make_content_view({'organization-id': self.org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        # Check content view files presence before deletion
        result = ssh.command(
            'find /var/lib/pulp/published -name "*{0}*"'
            .format(content_view['name'])
        )
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout), 0)
        self.assertEqual(len(content_view['versions']), 1)

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    def test_positive_update_name(self):
        """Update content view name

        @id: 35fccf2c-abc4-4ca8-a565-a7a6adaaf429

        @assert: Content view is updated with new name

        @BZ: 1359665
        """
        con_view = make_content_view({
            'name': gen_string('utf8'),
            'organization-id': make_org(cached=True)['id'],
        })
        new_name = gen_string('utf8')
        ContentView.update({
            'id': con_view['id'],
            'name': new_name,
        })
        con_view = ContentView.info({'id': con_view['id']})
        self.assertEqual(con_view['name'], new_name)

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_update_filter(self):
        # Variations might be:
        # * A filter on errata date (only content that matches date
        # in filter)
        # * A filter on severity (only content of specific errata
        # severity.
        """Edit content views for a rh content

        @id: 4beab1e4-fc58-460e-af24-cdd2c3d283e6

        @assert: Edited content view save is successful and info is updated

        @CaseLevel: Integration
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            'organization-id': self.rhel_content_org['id']
        })
        # Associate repo to CV
        ContentView.add_repository({
            'id': new_cv['id'],
            'organization-id': ContentViewTestCase.rhel_content_org['id'],
            'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        new_cv = ContentView.info({'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            ContentViewTestCase.rhel_repo_name,
        )
        cvf = make_content_view_filter({
            'content-view-id': new_cv['id'],
            'inclusion': 'true',
            'type': 'erratum',
        })
        cvf_rule = make_content_view_filter_rule({
            'content-view-filter-id': cvf['filter-id'],
            'types': ['bugfix', 'enhancement'],
        })
        cvf = ContentView.filter.info({'id': cvf['filter-id']})
        self.assertNotIn('security', cvf['rules'][0]['types'])
        ContentView.filter.rule.update({
            'id': cvf_rule['rule-id'],
            'types': 'security',
            'content-view-filter-id': cvf['filter-id'],
        })
        cvf = ContentView.filter.info({'id': cvf['filter-id']})
        self.assertEqual('security', cvf['rules'][0]['types'])

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_id(self):
        """delete content views

        @id: e96d6d47-8be4-4705-979f-e5c320eca293

        @assert: content view can be deleted

        """
        con_view = make_content_view({
            'organization-id': make_org(cached=True)['id'],
        })
        ContentView.delete({'id': con_view['id']})
        with self.assertRaises(CLIReturnCodeError):
            ContentView.info({'id': con_view['id']})

    @tier1
    @skip_if_bug_open('bugzilla', 1317057)
    def test_positive_delete_with_custom_repo_by_name_and_verify_files(self):
        """Delete content view containing custom repo and verify it was
        actually deleted from hard drive.

        @id: 9f381f77-ce43-4b68-8d00-459f40c9efb6

        @Assert: Content view was deleted and pulp folder doesn't contain
        content view files anymore

        @BZ: 1317057, 1265703
        """
        # Create and sync a repository
        new_product = make_product({u'organization-id': self.org['id']})
        new_repo = make_repository({u'product-id': new_product['id']})
        Repository.synchronize({'id': new_repo['id']})
        # Create a content view, add the repo and publish the content view
        content_view = make_content_view({'organization-id': self.org['id']})
        ContentView.add_repository({
            u'id': content_view['id'],
            u'organization-id': self.org['id'],
            u'repository-id': new_repo['id'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        # Check content view files presence before deletion
        result = ssh.command(
            'find /var/lib/pulp -name "*{0}*"'.format(content_view['name']))
        self.assertEqual(result.return_code, 0)
        self.assertNotEqual(len(result.stdout), 0)
        self.assertEqual(len(content_view['versions']), 1)
        # Completely delete the content view
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'lifecycle-environment-id':
                content_view['lifecycle-environments'][0]['id'],
        })
        ContentView.version_delete({
            'content-view': content_view['name'],
            'organization': self.org['name'],
            'version': content_view['versions'][0]['version'],
        })
        ContentView.delete({'id': content_view['id']})
        # Check content view files presence after deletion
        result = ssh.command(
            'find /var/lib/pulp -name "*{0}*"'.format(content_view['name']))
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stdout), 0)

    @tier2
    @run_only_on('sat')
    def test_positive_delete_version_by_name(self):
        """Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'remove-from-environment' command and delete content view version from
        that content view. Use content view version name as a parameter.

        @id: 6e903131-1aeb-478c-ad92-5dedcc22c3f9

        @assert: Content view version deleted successfully


        @CaseLevel: Integration
        """
        content_view = make_content_view({u'organization-id': self.org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 1)
        cvv = content_view['versions'][0]
        env_id = content_view['lifecycle-environments'][0]['id']
        ContentView.remove_from_environment({
            u'id': content_view['id'],
            u'lifecycle-environment-id': env_id,
        })
        ContentView.version_delete({
            u'content-view': content_view['name'],
            u'organization': self.org['name'],
            u'version': cvv['version'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 0)

    @tier1
    @run_only_on('sat')
    def test_positive_delete_version_by_id(self):
        """Create content view and publish it. After that try to
        disassociate content view from 'Library' environment through
        'remove-from-environment' command and delete content view version from
        that content view. Use content view version id as a parameter. Also,
        add repository to initial content view for better coverage.

        @id: 09457d48-2a92-401d-8dd0-45679a547e70

        @assert: Content view version deleted successfully

        """
        # Create new organization, product and repository
        new_org = make_org({u'name': gen_alphanumeric()})
        new_product = make_product({u'organization-id': new_org['id']})
        new_repo = make_repository({u'product-id': new_product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create new content-view and add repository to view
        new_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'organization-id': new_org['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a version1 of CV
        ContentView.publish({u'id': new_cv['id']})
        # Get the CV info
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['versions']), 1)
        # Store the associated environment_id
        env_id = new_cv['lifecycle-environments'][0]['id']
        # Store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Remove the CV from selected environment
        ContentView.remove_from_environment({
            u'id': new_cv['id'],
            u'lifecycle-environment-id': env_id,
        })
        # Delete the version
        ContentView.version_delete({u'id': version1_id})
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['versions']), 0)

    @tier2
    @run_only_on('sat')
    def test_negative_delete_version_by_id(self):
        """Create content view and publish it. Try to delete content
        view version while content view is still associated with lifecycle
        environment

        @id: 7334118b-e6c5-4db3-9167-3f006c43f863

        @assert: Content view version is not deleted


        @CaseLevel: Integration
        """
        content_view = make_content_view({u'organization-id': self.org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 1)
        cvv = content_view['versions'][0]
        # Try to delete content view version while it is in environment Library
        with self.assertRaises(CLIReturnCodeError):
            ContentView.version_delete({u'id': cvv['id']})
        # Check that version was not actually removed from the cv
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 1)

    @tier1
    @run_only_on('sat')
    def test_positive_remove_lce_by_id(self):
        """Remove content view from lifecycle environment

        @id: 1bf8a647-d82e-4145-b13b-f92bf6642532

        @Assert: Content view removed from environment successfully

        """
        new_org = make_org({u'name': gen_alphanumeric()})
        new_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        env = new_cv['lifecycle-environments'][0]
        ContentView.remove({
            u'id': new_cv['id'],
            u'environment-ids': env['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['lifecycle-environments']), 0)

    @tier2
    @run_only_on('sat')
    def test_positive_remove_lce_by_id_and_reassign_ak(self):
        """Remove content view environment and re-assign activation key to
        another environment and content view

        @id: 3e3ac439-fa85-42ce-8277-2258bc0c7cb4

        @Assert: Activation key re-assigned successfully


        @CaseLevel: Integration
        """
        new_org = make_org({u'name': gen_alphanumeric()})
        env = [
            make_lifecycle_environment({u'organization-id': new_org['id']})
            for _ in range(2)
        ]

        source_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': source_cv['id']})
        source_cv = ContentView.info({u'id': source_cv['id']})
        cvv = source_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[0]['id'],
        })

        destination_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': destination_cv['id']})
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        cvv = destination_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[1]['id'],
        })

        ac_key = make_activation_key({
            u'content-view-id': source_cv['id'],
            u'lifecycle-environment-id': env[0]['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(source_cv['activation-keys'][0], ac_key['name'])
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(len(destination_cv['activation-keys']), 0)

        ContentView.remove({
            u'id': source_cv['id'],
            u'environment-ids': env[0]['id'],
            u'key-content-view-id': destination_cv['id'],
            u'key-environment-id': env[1]['id'],
        })
        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(len(source_cv['activation-keys']), 0)
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(destination_cv['activation-keys'][0], ac_key['name'])

    @tier2
    @run_only_on('sat')
    def test_positive_remove_lce_by_id_and_reassign_chost(self):
        """Remove content view environment and re-assign content host to
        another environment and content view

        @id: 40900199-dcfc-4906-bf54-16c13882c05b

        @Assert: Content host re-assigned successfully


        @CaseLevel: Integration
        """
        new_org = make_org({u'name': gen_alphanumeric()})
        env = [
            make_lifecycle_environment({u'organization-id': new_org['id']})
            for _ in range(2)
        ]

        source_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': source_cv['id']})
        source_cv = ContentView.info({u'id': source_cv['id']})
        cvv = source_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[0]['id'],
        })

        destination_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': destination_cv['id']})
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        cvv = destination_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env[1]['id'],
        })

        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(source_cv['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': source_cv['id'],
            u'lifecycle-environment-id': env[0]['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })

        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(source_cv['content-host-count'], '1')
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(destination_cv['content-host-count'], '0')

        ContentView.remove({
            u'environment-ids': env[0]['id'],
            u'id': source_cv['id'],
            u'system-content-view-id': destination_cv['id'],
            u'system-environment-id': env[1]['id'],
        })
        source_cv = ContentView.info({u'id': source_cv['id']})
        self.assertEqual(source_cv['content-host-count'], '0')
        destination_cv = ContentView.info({u'id': destination_cv['id']})
        self.assertEqual(destination_cv['content-host-count'], '1')

    @tier1
    @run_only_on('sat')
    def test_positive_remove_version_by_id(self):
        """Delete content view version using 'remove' command

        @id: e8664353-6601-4566-8478-440be20a089d

        @Assert: Content view version deleted successfully

        """
        new_org = make_org({u'name': gen_alphanumeric()})
        new_cv = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        env = new_cv['lifecycle-environments'][0]
        cvv = new_cv['versions'][0]
        ContentView.remove_from_environment({
            u'id': new_cv['id'],
            u'lifecycle-environment-id': env['id'],
        })

        ContentView.remove({
            u'content-view-version-ids': cvv['id'],
            u'id': new_cv['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['versions']), 0)

    @tier2
    @run_only_on('sat')
    def test_positive_create_composite(self):
        # Note: puppet repos cannot/should not be used in this test
        # It shouldn't work - and that is tested in a different case
        # (test_negative_add_puppet_repo). Individual modules from a puppet
        # repo, however, are a valid variation.
        """create a composite content view

        @id: bded6acd-8da3-45ea-9e39-19bdc6c06341

        @setup: sync multiple content source/types (RH, custom, etc.)

        @assert: Composite content views are created


        @CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Create CV
        con_view = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
        })
        # Associate version to composite CV
        ContentView.add_version({
            u'content-view-version-id': version1_id,
            u'id': con_view['id'],
        })
        # Assert whether version was associated to composite CV
        con_view = ContentView.info({u'id': con_view['id']})
        self.assertEqual(
            con_view['components'][0]['id'],
            version1_id,
            'version was not associated to composite CV',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_remove_version_by_id_from_composite(self):
        """Create a composite content view and remove its content version by id

        @id: 0ff675d0-45d6-4f15-9e84-3b5ce98ce7de

        @assert: Composite content view info output does not contain any values

        @CaseLevel: Integration
        """
        # Create new repository
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create new content-view and add repository to view
        new_cv = make_content_view({u'organization-id': self.org['id']})
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'organization-id': self.org['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        # Get the CV info
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Create a composite CV
        comp_cv = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
            'component-ids': new_cv['versions'][0]['id']
        })
        ContentView.publish({u'id': comp_cv['id']})
        new_cv = ContentView.info({u'id': comp_cv['id']})
        env = new_cv['lifecycle-environments'][0]
        cvv = new_cv['versions'][0]
        ContentView.remove_from_environment({
            u'id': new_cv['id'],
            u'lifecycle-environment-id': env['id'],
        })
        ContentView.remove({
            u'content-view-version-ids': cvv['id'],
            u'id': new_cv['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(len(new_cv['versions']), 0)

    @tier2
    @run_only_on('sat')
    def test_positive_create_composite_with_component_ids(self):
        """create a composite content view with a component_ids option

        @id: 6d4b94da-258d-4690-a5b6-bacaf6b1671a

        @assert: Composite content view component ids are similar to the
        nested content view versions ids

        @CaseLevel: Integration
        """
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Publish a new version of CV twice
        for _ in range(2):
            ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version ids
        component_ids = [new_cv['versions'][0]['id'],
                         new_cv['versions'][1]['id']]
        # Create CV
        comp_cv = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
            'component-ids': component_ids
        })
        # Assert whether the composite content view components IDs are equal
        # to the component_ids input values
        comp_cv = ContentView.info({u'id': comp_cv['id']})
        self.assertEqual(
            [comp['id'] for comp in comp_cv['components']],
            component_ids,
            'IDs of the composite content view components differ from '
            'the input values',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_update_composite_with_component_ids(self):
        """Update a composite content view with a component_ids option

        @id: e6106ff6-c526-40f2-bdc0-ae291f7b267e

        @assert: Composite content view component ids are similar to the
        nested content view versions ids

        @CaseLevel: Integration
        """
        # Create a CV to add to the composite one
        cv = make_content_view({u'organization-id': self.org['id']})
        # Publish a new version of the CV
        ContentView.publish({u'id': cv['id']})
        new_cv = ContentView.info({u'id': cv['id']})
        # Let us now store the version ids
        component_ids = new_cv['versions'][0]['id']
        # Create a composite CV
        comp_cv = make_content_view({
            'composite': True,
            'organization-id': self.org['id']
        })
        # Update a composite content view with a component id version
        ContentView.update({
            'id': comp_cv['id'],
            'component-ids': component_ids,
        })
        # Assert whether the composite content view components IDs are equal
        # to the component_ids input values
        comp_cv = ContentView.info({u'id': comp_cv['id']})
        self.assertEqual(
            comp_cv['components'][0]['id'],
            component_ids,
            'IDs of the composite content view components differ from '
            'the input values',
        )

    # Content Views: Adding products/repos

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_add_rh_repo_by_id(self):
        """Associate Red Hat content to a content view

        @id: b31a85c3-aa56-461b-9e3a-f7754c742573

        @setup: Sync RH content

        @assert: RH Content can be seen in the content view


        @CaseLevel: Integration
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            u'organization-id': self.rhel_content_org['id']
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            self.rhel_repo_name,
            'Repo was not associated to CV',
        )

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    @tier2
    def test_positive_add_rh_repo_by_id_and_create_filter(self):
        """Associate Red Hat content to a content view and create filter

        @id: 7723247a-9367-4367-b251-bd079b79b8a2

        @setup: Sync RH content

        @steps: 1. Assure filter(s) applied to associated content

        @assert: Filtered RH content only is available/can be seen in a view


        @CaseLevel: Integration

        @BZ: 1359665
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            u'organization-id': self.rhel_content_org['id']
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            ContentViewTestCase.rhel_repo_name,
            'Repo was not associated to CV',
        )
        name = gen_string('alphanumeric')
        ContentView.filter.create({
            'content-view-id': new_cv['id'],
            'inclusion': 'true',
            'name': name,
            'type': 'rpm',
        })
        ContentView.filter.rule.create({
            'content-view-filter': name,
            'content-view-id': new_cv['id'],
            'name': 'walgrind',
        })

    @tier2
    @run_only_on('sat')
    def test_positive_add_custom_repo_by_id(self):
        """Associate custom content to a Content view

        @id: b813b222-b984-47e0-8d9b-2daa43f9a221

        @setup: Sync custom content

        @assert: Custom content can be seen in a view


        @CaseLevel: Integration
        """
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV',
        )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1343006)
    @tier1
    def test_positive_add_custom_repo_by_name(self):
        """Associate custom content to a content view with name

        @id: 62431e11-bec6-4444-abb0-e3758ba25fd8

        @assert: whether repos are added to cv.

        """
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': new_cv['name'],
            u'organization': self.org['name'],
            u'product': self.product['name'],
            u'repository': new_repo['name'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV',
        )

    @tier2
    @run_only_on('sat')
    def test_negative_add_puppet_repo(self):
        # Again, individual modules should be ok.
        """attempt to associate puppet repos within a custom content
        view

        @id: 7625c07b-edeb-48ef-85a2-4d1c09874a4b

        @assert: User cannot create a content view that contains direct puppet
        repos.


        @CaseLevel: Integration
        """
        new_repo = make_repository({
            u'content-type': u'puppet',
            u'product-id': self.product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate puppet repo to CV
        with self.assertRaises(CLIReturnCodeError):
            ContentView.add_repository({
                u'id': new_cv['id'],
                u'repository-id': new_repo['id'],
            })

    @tier2
    @run_only_on('sat')
    def test_negative_add_component_in_non_composite_cv(self):
        """attempt to associate components in a non-composite content
        view

        @id: 2a6f150d-e012-47c1-9423-d73f5d620dc9

        @assert: User cannot add components to the view


        @CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create component CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        # Fetch version id
        cv_version = ContentView.version_list({
            u'content-view-id': new_cv['id']
        })
        # Create non-composite CV
        with self.assertRaises(CLIFactoryError):
            make_content_view({
                u'component-ids': cv_version[0]['id'],
                u'organization-id': self.org['id'],
            })

    @tier2
    @run_only_on('sat')
    def test_negative_add_same_yum_repo_twice(self):
        """attempt to associate the same repo multiple times within a
        content view

        @id: 5fb09b30-5f5b-4473-a62b-8f41045ac2b6

        @assert: User cannot add repos multiple times to the view


        @CaseLevel: Integration
        """
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV',
        )
        repos_length = len(new_cv['yum-repositories'])
        # Re-associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            len(new_cv['yum-repositories']),
            repos_length,
            'No new entry of same repo is expected',
        )

    @tier2
    @run_only_on('sat')
    def test_negative_add_same_puppet_repo_twice(self):
        """attempt to associate duplicate puppet module(s) within a
        content view

        @id: 674cbae2-8493-466d-a2e4-dc11fb5c6b6f

        @assert: User cannot add puppet modules multiple times to the content
        view

        @CaseLevel: Integration
        """
        # see BZ #1222118
        repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': self.product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        # Sync REPO
        Repository.synchronize({'id': repository['id']})
        repository = Repository.info({'id': repository['id']})
        puppet_modules = int(repository['content-counts']['puppet-modules'])
        # Create CV
        content_view = make_content_view({
            u'organization-id': self.org['id'],
        })
        # Fetch puppet module
        puppet_result = PuppetModule.list({
            u'repository-id': repository['id'],
            u'per-page': False,
        })
        self.assertEqual(len(puppet_result), puppet_modules)
        for puppet_module in puppet_result:
            # Associate puppet module to CV
            ContentView.puppet_module_add({
                u'author': puppet_module['author'],
                u'content-view-id': content_view['id'],
                u'name': puppet_module['name'],
            })
            # Re-associate same puppet module to CV
            with self.assertRaises(CLIReturnCodeError):
                ContentView.puppet_module_add({
                    u'author': puppet_module['author'],
                    u'content-view-id': content_view['id'],
                    u'name': puppet_module['name'],
                })

    @tier2
    @run_only_on('sat')
    def test_negative_add_unpublished_cv_to_composite(self):
        """Attempt to associate unpublished non-composite content view with
        composite content view.

        @id: acee782f-2792-4c4e-b0c9-87d6b89992ef

        @steps:

        1. Create an empty non-composite content view. Do not publish it.
        2. Create a new composite content view

        @assert: Non-composite content view cannot be added to
        composite content view.

        @CaseLevel: Integration

        @BZ: 1367123
        """
        # Create component CV
        content_view = make_content_view({'organization-id': self.org['id']})
        # Create composite CV
        composite_cv = make_content_view({
            'organization-id': self.org['id'],
            'composite': True,
        })
        # Add unpublished component CV
        with self.assertRaises(CLIReturnCodeError) as context:
            ContentView.add_version({
                'id': composite_cv['id'],
                'content-view-version-content-view-id': content_view['id'],
            })
        self.assertRegexpMatches(
            context.exception.message,
            "Could not add version:\s*"
            "Error: one of content_view_versions not found"
        )

    @tier2
    @run_only_on('sat')
    def test_negative_add_non_composite_cv_to_composite(self):
        """Attempt to associate both published and unpublished
        non-composite content views with composite content view.

        @id: 4f6d3308-8083-4fc3-bb4f-5d5e1b886a96

        @steps:

        1. Create an empty non-composite content view. Do not publish it
        2. Create a second non-composite content view. Publish it.
        3. Create a new composite content view.
        4. Add the published non-composite content view to the composite
            content view.

        @assert:

        1. Unpublished non-composite content view cannot be added to
        composite content view
        2. Published non-composite content view is successfully added to
        composite content view.

        @CaseLevel: Integration

        @BZ: 1367123
        """
        # Create published component CV
        published_cv = make_content_view({'organization-id': self.org['id']})
        ContentView.publish({'id': published_cv['id']})
        # Create unpublished component CV
        unpublished_cv = make_content_view({'organization-id': self.org['id']})
        # Create composite CV
        composite_cv = make_content_view({
            'organization-id': self.org['id'],
            'composite': True,
        })
        # Add published CV
        ContentView.add_version({
            'id': composite_cv['id'],
            'content-view-version-content-view-id': published_cv['id']
        })
        published_cv = ContentView.info({'id': published_cv['id']})
        composite_cv = ContentView.info({'id': composite_cv['id']})
        self.assertEqual(
            composite_cv['components'][0]['id'],
            published_cv['versions'][0]['id']
        )
        # Add unpublished CV
        with self.assertRaises(CLIReturnCodeError) as context:
            ContentView.add_version({
                'id': composite_cv['id'],
                'content-view-version-content-view-id': unpublished_cv['id'],
            })
        self.assertRegexpMatches(
            context.exception.message,
            "Could not add version:\s*"
            "Error: one of content_view_versions not found"
        )

    # Content View: promotions
    # katello content view promote --label=MyView --env=Dev --org=ACME
    # katello content view promote --view=MyView --env=Staging --org=ACME

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_promote_rh_content(self):
        """attempt to promote a content view containing RH content

        @id: 53b3661b-b40f-466e-a742-bc4b8c1f6cd8

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted


        @CaseLevel: Integration
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': self.rhel_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        env1 = make_lifecycle_environment({
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': new_cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': env1['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        environment = {
            'id': env1['id'],
            'name': env1['name'],
        }
        self.assertIn(environment, new_cv['lifecycle-environments'])

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_promote_rh_and_custom_content(self):
        """attempt to promote a content view containing RH content and
        custom content using filters

        @id: f96e97ef-f73c-4506-855c-2392e06f3a6a

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted

        @CaseLevel: Integration
        """
        # Enable RH repo
        self.create_rhel_content()
        # Create custom repo
        new_repo = make_repository({
            'product-id': make_product({
                'organization-id': self.rhel_content_org['id']})['id']
        })
        # Sync custom repo
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({
            'organization-id': self.rhel_content_org['id'],
        })
        # Associate repos with CV
        ContentView.add_repository({
            'id': new_cv['id'],
            'repository-id': self.rhel_repo['id'],
        })
        ContentView.add_repository({
            'id': new_cv['id'],
            'repository-id': new_repo['id'],
        })
        cvf = make_content_view_filter({
            'content-view-id': new_cv['id'],
            'inclusion': 'false',
            'type': 'rpm',
        })
        make_content_view_filter_rule({
            'content-view-filter-id': cvf['filter-id'],
            'min-version': 5,
            'name': FAKE_1_CUSTOM_PACKAGE_NAME,
        })
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        env1 = make_lifecycle_environment({
            'organization-id': ContentViewTestCase.rhel_content_org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            'id': new_cv['versions'][0]['id'],
            'to-lifecycle-environment-id': env1['id'],
        })
        new_cv = ContentView.info({'id': new_cv['id']})
        environment = {
            'id': env1['id'],
            'name': env1['name'],
        }
        self.assertIn(environment, new_cv['lifecycle-environments'])

    @tier2
    @run_only_on('sat')
    def test_positive_promote_custom_content(self):
        """attempt to promote a content view containing custom content

        @id: 64c2f1c2-7443-4836-a108-060b913ad2b1

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be promoted


        @CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': new_cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertIn(
            {u'id': self.env1['id'], u'name': self.env1['name']},
            new_cv['lifecycle-environments'],
        )

    @tier2
    @run_only_on('sat')
    def test_positive_promote_ccv(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to promote a content view containing custom content

        @id: 9d31113d-39ec-4524-854c-7f03b0f028fe

        @setup: Multiple environments for an org; custom content synced

        @steps: create a composite view containing multiple content types

        @assert: Content view can be promoted


        @CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Create CV
        con_view = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
        })
        # Associate version to composite CV
        ContentView.add_version({
            u'content-view-version-id': version1_id,
            u'id': con_view['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': con_view['id']})
        # As version info is populated after publishing only
        con_view = ContentView.info({u'id': con_view['id']})
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': con_view['versions'][0]['id'],
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        con_view = ContentView.info({u'id': con_view['id']})
        self.assertIn(
            {u'id': self.env1['id'], u'name': self.env1['name']},
            con_view['lifecycle-environments'],
        )

    @tier2
    @run_only_on('sat')
    def test_negative_promote_default_cv(self):
        """attempt to promote a default content view

        @id: ef25a4d9-8852-4d2c-8355-e9b07eb0560b

        @assert: Default content views cannot be promoted


        @CaseLevel: Integration
        """
        result = ContentView.list(
            {u'organization-id': self.org['id']},
            per_page=False,
        )
        content_view = random.choice([
            cv for cv in result
            if cv['name'] == DEFAULT_CV
        ])
        cvv = ContentView.version_list({
            'content-view-id': content_view['content-view-id']})[0]
        # Promote the Default CV to the next env
        with self.assertRaises(CLIReturnCodeError):
            ContentView.version_promote({
                u'id': cvv['id'],
                u'to-lifecycle-environment-id': self.env1['id'],
            })

    @tier2
    @run_only_on('sat')
    def test_negative_promote_with_invalid_lce(self):
        """attempt to promote a content view using an invalid
        environment

        @id: b143552e-610e-4188-b754-e7462ced8cf3

        @assert: Content views cannot be promoted; handled gracefully


        @CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Promote the Published version of CV,
        # to the previous env which is Library
        with self.assertRaises(CLIReturnCodeError):
            ContentView.version_promote({
                u'id': new_cv['versions'][0]['id'],
                u'to-lifecycle-environment-id': new_cv[
                    'lifecycle-environments'][0]['id'],
            })

    # Content Views: publish
    # katello content definition publish --label=MyView

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_publish_rh_content(self):
        """attempt to publish a content view containing RH content

        @id: d4323759-d869-4d62-ab2e-f1ea3dbb38ba

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be published


        @CaseLevel: Integration
        """
        self.create_rhel_content()
        # Create CV
        new_cv = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            self.rhel_repo['name'],
            'Repo was not associated to CV',
        )
        self.assertEqual(
            new_cv['versions'][0]['version'], u'1.0',
            'Publishing new version of CV was not successful'
        )

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_publish_rh_and_custom_content(self):
        """attempt to publish  a content view containing a RH and custom
        repos and has filters

        @id: 0b116172-06a3-4327-81a8-17a098a1a564

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be published

        @CaseLevel: Integration
        """
        # Enable RH repo
        self.create_rhel_content()
        # Create custom repo
        new_repo = make_repository({
            'product-id': make_product({
                'organization-id': self.rhel_content_org['id']})['id']
        })
        # Sync custom repo
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({
            'organization-id': self.rhel_content_org['id'],
        })
        # Associate repos with CV
        ContentView.add_repository({
            'id': new_cv['id'],
            'repository-id': self.rhel_repo['id'],
        })
        ContentView.add_repository({
            'id': new_cv['id'],
            'repository-id': new_repo['id'],
        })
        cvf = make_content_view_filter({
            'content-view-id': new_cv['id'],
            'inclusion': 'false',
            'type': 'rpm',
        })
        make_content_view_filter_rule({
            'content-view-filter-id': cvf['filter-id'],
            'min-version': 5,
            'name': FAKE_1_CUSTOM_PACKAGE_NAME,
        })
        # Publish a new version of CV
        ContentView.publish({'id': new_cv['id']})
        new_cv = ContentView.info({'id': new_cv['id']})
        self.assertTrue(
            {self.rhel_repo['name'], new_repo['name']}.issubset(
                {repo['name'] for repo in new_cv['yum-repositories']})
        )
        self.assertEqual(new_cv['versions'][0]['version'], '1.0')

    @tier2
    @run_only_on('sat')
    def test_positive_publish_custom_content(self):
        """attempt to publish a content view containing custom content

        @id: 84158023-3980-45c6-87d8-faacea3c942f

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be published


        @CaseLevel: Integration
        """
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertEqual(
            new_cv['yum-repositories'][0]['name'],
            new_repo['name'],
            'Repo was not associated to CV',
        )
        self.assertEqual(
            new_cv['versions'][0]['version'],
            u'1.0',
            'Publishing new version of CV was not successful',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_publish_ccv(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to publish a composite content view containing custom
        content

        @id: fde99446-241f-422d-987b-fa1987b654ee

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be published


        @CaseLevel: Integration
        """
        repository = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': repository['id']})
        # Create CV
        content_view = make_content_view({
            u'organization-id': self.org['id'],
        })
        # Associate repo to CV
        ContentView.add_repository({
            u'id': content_view['id'],
            u'repository-id': repository['id'],
        })
        # Publish a new version of CV
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        # Let us now store the version1 id
        version1_id = content_view['versions'][0]['id']
        # Create composite CV
        composite_cv = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
        })
        # Associate version to composite CV
        ContentView.add_version({
            u'content-view-version-id': version1_id,
            u'id': composite_cv['id'],
        })
        # Assert whether version was associated to composite CV
        composite_cv = ContentView.info({u'id': composite_cv['id']})
        self.assertEqual(
            composite_cv['components'][0]['id'],
            version1_id,
            'version was not associated to composite CV',
        )
        # Publish a new version of CV
        ContentView.publish({u'id': composite_cv['id']})
        # Assert whether Version1 was created and exists in Library Env.
        composite_cv = ContentView.info({u'id': composite_cv['id']})
        self.assertEqual(
            composite_cv['lifecycle-environments'][0]['name'],
            ENVIRONMENT,
            'version1 does not exist in Library',
        )
        self.assertEqual(
            composite_cv['versions'][0]['version'],
            u'1.0',
            'Publishing new version of CV was not successful'
        )

    @tier2
    @run_only_on('sat')
    def test_positive_update_version_once(self):
        # Dev notes:
        # If Dev has version x, then when I promote version y into
        # Dev, version x goes away (ie when I promote version 1 to Dev,
        # version 3 goes away)
        """when publishing new version to environment, version
        gets updated

        @id: cef62d34-c006-4bd0-950e-29e732388c00

        @setup: Multiple environments for an org; multiple versions
        of a content view created/published

        @steps:
        1. publish a view to an environment noting the CV version
        2. edit and republish a new version of a CV

        @assert: Content view version is updated in target environment.


        @CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a version1 of CV
        ContentView.publish({u'id': new_cv['id']})
        # Only after we publish version1 the info is populated.
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Actual assert for this test happens HERE
        # Test whether the version1 now belongs to Library
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            version1['lifecycle-environments'][0]['label'],
            ENVIRONMENT,
            'Version 1 is not in Library',
        )
        # Promotion of version1 to Dev env
        ContentView.version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        # The only way to validate whether env has the version is to
        # validate that version has the env.
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            version1['lifecycle-environments'][1]['id'],
            self.env1['id'],
            'Promotion of version1 not successful to the env',
        )
        # Now Publish version2 of CV
        ContentView.publish({u'id': new_cv['id']})
        # Only after we publish version2 the info is populated.
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version2 id
        version2_id = new_cv['versions'][1]['id']
        # Test whether the version2 now belongs to Library
        version2 = ContentView.version_info({u'id': version2_id})
        self.assertEqual(
            version2['lifecycle-environments'][0]['label'],
            ENVIRONMENT,
            'Version 2 not in Library'
        )
        # Promotion of version2 to Dev env
        ContentView.version_promote({
            u'id': version2_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        # Actual assert for this test happens here.
        # Test whether the version2 now belongs to next env
        version2 = ContentView.version_info({u'id': version2_id})
        self.assertEqual(
            version2['lifecycle-environments'][1]['id'],
            self.env1['id'],
            'Promotion of version2 not successful to the env',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_update_version_multiple(self):
        # Dev notes:
        # Similarly when I publish version y, version x goes away from
        # Library (ie when I publish version 2, version 1 disappears)
        """when publishing new version to environment, version
        gets updated
        @id: e5704b86-9919-471b-8362-1831d1983e70

        @setup: Multiple environments for an org; multiple versions
        of a content view created/published

        @steps:
        1. publish a view to an environment
        2. edit and republish a new version of a CV

        @assert: Content view version is updated in source environment.


        @CaseLevel: Integration
        """
        # Create REPO
        new_repo = make_repository({u'product-id': self.product['id']})
        # Sync REPO
        Repository.synchronize({'id': new_repo['id']})
        # Create CV
        new_cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV
        ContentView.add_repository({
            u'id': new_cv['id'],
            u'repository-id': new_repo['id'],
        })
        # Publish a version1 of CV
        ContentView.publish({u'id': new_cv['id']})
        # Only after we publish version1 the info is populated.
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version1 id
        version1_id = new_cv['versions'][0]['id']
        # Test whether the version1 now belongs to Library
        version = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            version['lifecycle-environments'][0]['label'],
            ENVIRONMENT,
            'Version 1 is not in Library',
        )
        # Promotion of version1 to Dev env
        ContentView.version_promote({
            u'id': version1_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        # The only way to validate whether env has the version is to
        # validate that version has the env.
        # Test whether the version1 now belongs to next env
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            version1['lifecycle-environments'][1]['id'],
            self.env1['id'],
            'Promotion of version1 not successful to the env',
        )
        # Now Publish version2 of CV
        ContentView.publish({u'id': new_cv['id']})
        # As per Dev Notes:
        # Similarly when I publish version y, version x goes away from Library.
        # Actual assert for this test happens here.
        # Test that version1 does not exist in Library after publishing v2
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            len(version1['lifecycle-environments']),
            1,
            'Version1 may still exist in Library',
        )
        self.assertNotEqual(
            version1['lifecycle-environments'][0]['label'],
            ENVIRONMENT,
            'Version1 still exists in Library',
        )
        # Only after we publish version2 the info is populated.
        new_cv = ContentView.info({u'id': new_cv['id']})
        # Let us now store the version2 id
        version2_id = new_cv['versions'][1]['id']
        # Promotion of version2 to next env
        ContentView.version_promote({
            u'id': version2_id,
            u'to-lifecycle-environment-id': self.env1['id'],
        })
        # Actual assert for this test happens here.
        # Test that version1 does not exist in any/next env after,
        # promoting version2 to next env
        version1 = ContentView.version_info({u'id': version1_id})
        self.assertEqual(
            len(version1['lifecycle-environments']),
            0,
            'version1 still exists in the next env',
        )

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_chost_by_id(self):
        """Attempt to subscribe content host to content view

        @id: db0bfd9d-3150-427e-9683-a68af33813e7

        @assert: Content host can be subscribed to content view


        @CaseLevel: System
        """
        new_org = make_org()
        env = make_lifecycle_environment({u'organization-id': new_org['id']})
        content_view = make_content_view({u'organization-id': new_org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')
        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @run_in_one_thread
    @run_only_on('sat')
    @tier3
    def test_positive_subscribe_chost_by_id_using_rh_content(self):
        """Attempt to subscribe content host to content view that has
        Red Hat repository assigned to it

        @id: aeaaa363-5146-45ee-8c81-e54c7876fb81

        @assert: Content Host can be subscribed to content view with Red Hat
        repository


        @CaseLevel: System
        """
        self.create_rhel_content()
        env = make_lifecycle_environment({
            u'organization-id': self.rhel_content_org['id'],
        })
        content_view = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        ContentView.add_repository({
            u'id': content_view['id'],
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(
            content_view['yum-repositories'][0]['name'],
            self.rhel_repo_name,
        )
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')
        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': self.rhel_content_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    @tier3
    def test_positive_subscribe_chost_by_id_using_rh_content_and_filters(self):
        """Attempt to subscribe content host to filtered content view
        that has Red Hat repository assigned to it

        @id: 8d1e0daf-6130-4b50-827d-061e6c32749d

        @assert: Content Host can be subscribed to filtered content view with
        Red Hat repository


        @CaseLevel: System

        @BZ: 1359665
        """
        self.create_rhel_content()
        env = make_lifecycle_environment({
            u'organization-id': self.rhel_content_org['id'],
        })
        content_view = make_content_view({
            u'organization-id': self.rhel_content_org['id'],
        })
        ContentView.add_repository({
            u'id': content_view['id'],
            u'organization-id': ContentViewTestCase.rhel_content_org['id'],
            u'repository-id': ContentViewTestCase.rhel_repo['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(
            content_view['yum-repositories'][0]['name'],
            self.rhel_repo_name,
        )

        name = gen_string('utf8')
        ContentView.filter.create({
            'content-view-id': content_view['id'],
            'inclusion': 'true',
            'name': name,
            'type': 'rpm',
        })

        make_content_view_filter_rule({
            'content-view-filter': name,
            'content-view-id': content_view['id'],
            'name': gen_string('utf8'),
        })

        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })

        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': self.rhel_content_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_chost_by_id_using_custom_content(self):
        """Attempt to subscribe content host to content view that has
        custom repository assigned to it

        @id: 9758756a-2536-4777-a6a9-ed618453ebe7

        @assert: Content Host can be subscribed to content view with custom
        repository


        @CaseLevel: System
        """
        new_org = make_org()
        new_product = make_product({u'organization-id': new_org['id']})
        new_repo = make_repository({u'product-id': new_product['id']})
        env = make_lifecycle_environment({u'organization-id': new_org['id']})
        Repository.synchronize({'id': new_repo['id']})
        content_view = make_content_view({u'organization-id': new_org['id']})
        ContentView.add_repository({
            u'id': content_view['id'],
            u'organization-id': new_org['id'],
            u'repository-id': new_repo['id'],
        })

        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })

        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_chost_by_id_using_ccv(self):
        """Attempt to subscribe content host to composite content view

        @id: 4be340c0-9e58-4b96-ab37-d7e3b12c724f

        @assert: Content host can be subscribed to composite content view


        @CaseLevel: System
        """
        new_org = make_org()
        env = make_lifecycle_environment({u'organization-id': new_org['id']})
        content_view = make_content_view({
            'composite': True,
            'organization-id': new_org['id'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })

        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @tier3
    @run_only_on('sat')
    def test_positive_subscribe_chost_by_id_using_puppet_content(self):
        """Attempt to subscribe content host to content view that has
        puppet module assigned to it

        @id: 7f45a162-e944-4e2c-a892-b26d1d21c844

        @assert: Content Host can be subscribed to content view with puppet
        module

        @CaseLevel: System
        """
        # see BZ #1222118
        new_org = make_org()
        new_product = make_product({u'organization-id': new_org['id']})

        repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': new_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': repository['id']})

        content_view = make_content_view({u'organization-id': new_org['id']})

        puppet_result = PuppetModule.list({
            u'repository-id': repository['id'],
            u'per-page': False,
        })

        for puppet_module in puppet_result:
            # Associate puppet module to CV
            ContentView.puppet_module_add({
                u'content-view-id': content_view['id'],
                u'uuid': puppet_module['uuid'],
            })

        env = make_lifecycle_environment({u'organization-id': new_org['id']})

        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': env['id'],
        })

        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '0')

        make_fake_host({
            u'content-view-id': content_view['id'],
            u'lifecycle-environment-id': env['id'],
            u'name': gen_alphanumeric(),
            u'organization-id': new_org['id'],
        })
        content_view = ContentView.info({u'id': content_view['id']})
        self.assertEqual(content_view['content-host-count'], '1')

    @tier2
    @run_only_on('sat')
    def test_positive_clone_within_same_env(self):
        """Attempt to create, publish and promote new content view based on
        existing view within the same environment as the original content view

        @id: 4d7fa623-3516-4abe-a98c-98acbfb7e9c9

        @assert: Cloned content view can be published and promoted to the same
        environment as the original content view

        @CaseLevel: Integration
        """
        org = make_org()
        cloned_cv_name = gen_string('alpha')
        lc_env = make_lifecycle_environment({u'organization-id': org['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        new_cv = ContentView.copy({
            u'id': content_view['id'],
            u'name': cloned_cv_name,
        })[0]
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        cvv = new_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertIn(
            {'id': lc_env['id'], 'name': lc_env['name']},
            new_cv['lifecycle-environments']
        )

    @tier2
    @run_only_on('sat')
    def test_positive_clone_with_diff_env(self):
        """Attempt to create, publish and promote new content view based on
        existing view but promoted to a different environment

        @id: 308ffaa3-cd01-4a16-b84d-c60c32959235

        @Assert: Cloned content view can be published and promoted to a
        different environment as the original content view

        @CaseLevel: Integration
        """
        org = make_org()
        cloned_cv_name = gen_string('alpha')
        lc_env = make_lifecycle_environment({u'organization-id': org['id']})
        lc_env_cloned = make_lifecycle_environment({
            u'organization-id': org['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.publish({u'id': content_view['id']})
        content_view = ContentView.info({u'id': content_view['id']})
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        new_cv = ContentView.copy({
            u'id': content_view['id'],
            u'name': cloned_cv_name,
        })[0]
        ContentView.publish({u'id': new_cv['id']})
        new_cv = ContentView.info({u'id': new_cv['id']})
        cvv = new_cv['versions'][0]
        ContentView.version_promote({
            u'id': cvv['id'],
            u'to-lifecycle-environment-id': lc_env_cloned['id'],
        })
        new_cv = ContentView.info({u'id': new_cv['id']})
        self.assertIn(
            {'id': lc_env_cloned['id'], 'name': lc_env_cloned['name']},
            new_cv['lifecycle-environments']
        )

    @run_only_on('sat')
    @stubbed
    def test_positive_restart_dynflow_promote(self):
        """attempt to restart a failed content view promotion

        @id: 2be23f85-3f62-4319-87ea-41f28cf401dc

        @steps:
        1. (Somehow) cause a CV promotion to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart promotion

        @assert: Promotion is restarted.

        @caseautomation: notautomated

        """

    @run_only_on('sat')
    @stubbed
    def test_positive_restart_dynflow_publish(self):
        """attempt to restart a failed content view publish

        @id: 24468014-46b2-403e-8ed6-2daeda5a0163

        @steps:
        1. (Somehow) cause a CV publish  to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart publish

        @assert: Publish is restarted.

        @caseautomation: notautomated

        """

    # ROLES TESTING

    # pylint: disable=unexpected-keyword-arg
    @tier1
    @run_only_on('sat')
    def test_negative_user_with_no_create_view_cv_permissions(self):
        """Unauthorized users are not able to create/view content views

        @id: 17617893-27c2-4cb2-a2ed-47378ef90e7a

        @setup: Create a user without the Content View create/view permissions

        @assert: User with no content view create/view permissions cannot
        create or view the content view
        """
        password = gen_alphanumeric()
        no_rights_user = make_user({'password': password})
        no_rights_user['password'] = password
        org_id = make_org(cached=True)['id']
        for name in generate_strings_list(exclude_types=['cjk']):
            with self.subTest(name):
                # test that user can't create
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.with_user(
                        no_rights_user['login'],
                        no_rights_user['password'],
                    ).create({
                        'name': name,
                        'organization-id': org_id,
                    })
                # test that user can't read
                con_view = make_content_view({
                    'name': name,
                    'organization-id': org_id,
                })
                with self.assertRaises(CLIReturnCodeError):
                    ContentView.with_user(
                        no_rights_user['login'],
                        no_rights_user['password'],
                    ).info({'id': con_view['id']})

    @run_only_on('sat')
    @tier2
    def test_negative_user_with_read_only_cv_permission(self):
        """Read-only user is able to view content view

        @id: 588f57b5-9855-4c14-80d0-64b617c6b6dc

        @setup: create a user with the Content View read-only role

        @assert: User with read-only role for content view can view the content
        view but not Create / Modify / Promote / Publish

        @CaseLevel: Integration
        """
        cv = make_content_view({'organization-id': self.org['id']})
        password = gen_string('alphanumeric')
        user = make_user({'password': password})
        role = make_role()
        make_filter({
            'organization-ids': self.org['id'],
            'permissions': 'view_content_views',
            'role-id': role['id'],
        })
        User.add_role({
            'id': user['id'],
            'role-id': role['id'],
        })
        ContentView.with_user(user['login'], password).info({'id': cv['id']})
        # Verify read-only user can't either edit CV
        with self.assertRaises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).update({
                'id': cv['id'],
                'new-name': gen_string('alphanumeric'),
            })
        # or create a new one
        with self.assertRaises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).create({
                'name': gen_string('alphanumeric'),
                'organization-id': self.org['id'],
            })
        # or publish
        with self.assertRaises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).publish({
                'id': cv['id']})
        ContentView.publish({'id': cv['id']})
        cvv = ContentView.info({'id': cv['id']})['versions'][-1]
        # or promote
        with self.assertRaises(CLIReturnCodeError):
            ContentView.with_user(user['login'], password).version_promote({
                'id': cvv['id'],
                'organization-id': self.org['id'],
                'to-lifecycle-environment-id': self.env1['id'],
            })

    @run_only_on('sat')
    @tier2
    def test_positive_user_with_all_cv_permissions(self):
        """A user with all content view permissions is able to create,
        read, modify, promote, publish content views

        @id: ac40e9bb-9f1a-48d1-a0fe-9ac2be0f33f4

        @setup: create a user with all content view permissions

        @assert: User is able to perform create, read, modify, promote, publish
        content view

        @CaseLevel: Integration
        """
        cv = make_content_view({'organization-id': self.org['id']})
        password = gen_string('alphanumeric')
        user = make_user({'password': password})
        role = make_role()
        make_filter({
            'organization-ids': self.org['id'],
            'permissions': PERMISSIONS['Katello::ContentView'],
            'role-id': role['id'],
        })
        make_filter({
            'organization-ids': self.org['id'],
            'permissions': PERMISSIONS['Katello::KTEnvironment'],
            'role-id': role['id'],
        })
        User.add_role({
            'id': user['id'],
            'role-id': role['id'],
        })
        # Make sure user is not admin and has only expected roles assigned
        user = User.info({'id': user['id']})
        self.assertEqual(user['admin'], 'no')
        self.assertEqual(set(user['roles']), {DEFAULT_ROLE, role['name']})
        # Verify user can either edit CV
        ContentView.with_user(user['login'], password).info({'id': cv['id']})
        new_name = gen_string('alphanumeric')
        ContentView.with_user(user['login'], password).update({
            'id': cv['id'],
            'new-name': new_name,
        })
        cv = ContentView.info({'id': cv['id']})
        self.assertEqual(cv['name'], new_name)
        # or create a new one
        new_cv_name = gen_string('alphanumeric')
        new_cv = ContentView.with_user(user['login'], password).create({
            'name': new_cv_name,
            'organization-id': self.org['id'],
        })
        self.assertEqual(new_cv['name'], new_cv_name)
        # or publish
        ContentView.with_user(user['login'], password).publish({
            'id': cv['id']})
        cv = ContentView.info({'id': cv['id']})
        self.assertEqual(len(cv['versions']), 1)
        # or promote
        ContentView.with_user(user['login'], password).version_promote({
            'id': cv['versions'][-1]['id'],
            'organization-id': self.org['id'],
            'to-lifecycle-environment-id': self.env1['id'],
        })
        cv = ContentView.info({'id': cv['id']})
        self.assertIn(
            self.env1['id'],
            [env['id'] for env in cv['lifecycle-environments']],
        )


class OstreeContentViewTestCase(CLITestCase):
    """Tests for custom ostree contents in content views."""

    @classmethod
    @skip_if_os('RHEL6')
    def setUpClass(cls):
        """Create an organization, product, and repo with all content-types."""
        super(OstreeContentViewTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.product = make_product({u'organization-id': cls.org['id']})
        # Create new custom ostree repo
        cls.ostree_repo = make_repository({
            u'product-id': cls.product['id'],
            u'content-type': u'ostree',
            u'publish-via-http': u'false',
            u'url': FEDORA23_OSTREE_REPO,
        })
        Repository.synchronize({'id': cls.ostree_repo['id']})
        # Create new yum repository
        cls.yum_repo = make_repository({
            u'url': FAKE_1_YUM_REPO,
            u'product-id': cls.product['id'],
        })
        Repository.synchronize({'id': cls.yum_repo['id']})
        # Create new Puppet repository
        cls.puppet_repo = make_repository({
            u'url': FAKE_0_PUPPET_REPO,
            u'content-type': 'puppet',
            u'product-id': cls.product['id'],
        })
        Repository.synchronize({'id': cls.puppet_repo['id']})
        # Create new docker repository
        cls.docker_repo = make_repository({
            u'content-type': u'docker',
            u'docker-upstream-name': u'busybox',
            u'product-id': cls.product['id'],
            u'url': DOCKER_REGISTRY_HUB,
        })
        Repository.synchronize({'id': cls.docker_repo['id']})

    @tier2
    @run_only_on('sat')
    def test_positive_add_custom_ostree_content(self):
        """Associate custom ostree content in a view

        @id: 6e89094d-ffd3-4dc6-b925-f76531c56c20

        @Assert: Custom ostree content assigned and present in content view

        @CaseLevel: Integration
        """
        # Create CV
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': self.product['name'],
            u'repository': self.ostree_repo['name'],
        })
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(
            cv['ostree-repositories'][0]['name'],
            self.ostree_repo['name'],
            'Ostree Repo was not associated to CV',
        )

    @tier2
    @run_only_on('sat')
    def test_positive_publish_custom_ostree(self):
        """Publish a content view with custom ostree contents

        @id: ec66f1d3-9750-4dfc-a189-f3b0fd6af3e8

        @Assert: Content-view with Custom ostree published successfully

        @CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': self.product['name'],
            u'repository': self.ostree_repo['name'],
        })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(len(cv['versions']), 1)

    @tier2
    def test_positive_promote_custom_ostree(self):
        """Promote a content view with custom ostree contents

        @id: 5eb7b9e6-8757-4152-9114-42a5eb021bbc

        @Assert: Content-view with custom ostree contents promoted successfully

        @CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': self.product['name'],
            u'repository': self.ostree_repo['name'],
        })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        lc_env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        cv = ContentView.info({u'id': cv['id']})
        environment = {'id': lc_env['id'], 'name': lc_env['name']}
        self.assertIn(environment, cv['lifecycle-environments'])

    @tier2
    def test_positive_publish_promote_with_custom_ostree_and_other(self):
        """Publish & Promote a content view with custom ostree and other contents

        @id: 35668fa6-0a24-43ae-b562-26c5ac77e94d

        @Assert: Content-view with custom ostree and other contents promoted
        successfully

        @CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        repos = [
            self.ostree_repo,
            self.yum_repo,
            self.docker_repo,
        ]
        for repo in repos:
            ContentView.add_repository({
                u'name': cv['name'],
                u'organization': self.org['name'],
                u'product': self.product['name'],
                u'repository': repo['name'],
            })
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(
            cv['ostree-repositories'][0]['name'],
            self.ostree_repo['name'],
            'Ostree Repo was not associated to CV',
        )
        self.assertEqual(
            cv['yum-repositories'][0]['name'],
            self.yum_repo['name'],
            'Yum Repo was not associated to CV',
        )
        self.assertEqual(
            cv['docker-repositories'][0]['name'],
            self.docker_repo['name'],
            'Docker Repo was not associated to CV',
        )
        # Fetch puppet module
        puppet_result = PuppetModule.list({
            u'repository-id': self.puppet_repo['id'],
            u'per-page': False,
        })
        for puppet_module in puppet_result:
            # Associate puppet module to CV
            ContentView.puppet_module_add({
                u'content-view-id': cv['id'],
                u'uuid': puppet_module['uuid'],
            })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        lc_env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        cv = ContentView.info({u'id': cv['id']})
        environment = {
            'id': lc_env['id'],
            'name': lc_env['name'],
        }
        self.assertIn(environment, cv['lifecycle-environments'])


@run_in_one_thread
class ContentViewRedHatOstreeContent(CLITestCase):
    """Tests for publishing and promoting cv with RH ostree contents."""

    @classmethod
    @skip_if_os('RHEL6')
    @skip_if_not_set('fake_manifest')
    def setUpClass(cls):
        """Set up organization, product and RH atomic repository for tests."""
        super(ContentViewRedHatOstreeContent, cls).setUpClass()
        cls.org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            u'file': manifest.filename,
            u'organization-id': cls.org['id'],
        })
        RepositorySet.enable({
            u'basearch': None,
            u'name': REPOSET['rhaht'],
            u'organization-id': cls.org['id'],
            u'product': PRDS['rhah'],
            u'releasever': None,
        })
        cls.repo_name = REPOS['rhaht']['name']
        Repository.synchronize({
            u'name': cls.repo_name,
            u'organization-id': cls.org['id'],
            u'product': PRDS['rhah'],
        })

    @tier2
    def test_positive_add_rh_ostree_content(self):
        """Associate RH atomic ostree content in a view

        @id: 5e9dfb32-9cc7-4257-ab6b-f439fb9db2bd

        @Assert: RH atomic ostree content assigned and present in content view

        @CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhah'],
            u'repository': self.repo_name,
        })
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(
            cv['ostree-repositories'][0]['name'],
            self.repo_name,
            'Ostree Repo was not associated to CV',
        )

    @tier2
    def test_positive_publish_RH_ostree(self):
        """Publish a content view with RH ostree contents

        @id: 4ac5c7d1-9ab2-4a65-b4b8-1582b001125f

        @Assert: Content-view with RH ostree contents published successfully

        @CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhah'],
            u'repository': self.repo_name,
        })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(len(cv['versions']), 1)

    @tier2
    def test_positive_promote_RH_ostree(self):
        """Promote a content view with RH ostree contents

        @id: 71986705-fe45-4e0f-af0b-288c9c7ce61b

        @Assert: Content-view with RH ostree contents promoted successfully

        @CaseLevel: Integration
        """
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhah'],
            u'repository': self.repo_name,
        })
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        lc_env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        cv = ContentView.info({u'id': cv['id']})
        environment = {'id': lc_env['id'], 'name': lc_env['name']}
        self.assertIn(environment, cv['lifecycle-environments'])

    @tier2
    def test_positive_publish_promote_with_RH_ostree_and_other(self):
        """Publish & Promote a content view with RH ostree and other contents

        @id: 87c8ddb1-da32-4103-810d-8e5e28fa888f

        @Assert: Content-view with RH ostree and other contents promoted
        successfully

        @CaseLevel: Integration
        """
        RepositorySet.enable({
            'name': REPOSET['rhst7'],
            'organization-id': self.org['id'],
            'product': PRDS['rhel'],
            'releasever': None,
            'basearch': 'x86_64',
        })
        rpm_repo_name = REPOS['rhst7']['name']
        Repository.synchronize({
            u'name': rpm_repo_name,
            u'organization-id': self.org['id'],
            u'product': PRDS['rhel'],
        })
        cv = make_content_view({u'organization-id': self.org['id']})
        # Associate repo to CV with names.
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhah'],
            u'repository': self.repo_name,
        })
        ContentView.add_repository({
            u'name': cv['name'],
            u'organization': self.org['name'],
            u'product': PRDS['rhel'],
            u'repository': rpm_repo_name,
        })
        cv = ContentView.info({u'id': cv['id']})
        self.assertEqual(
            cv['ostree-repositories'][0]['name'],
            self.repo_name,
            'RH Ostree Repo was not associated to CV',
        )
        self.assertEqual(
            cv['yum-repositories'][0]['name'],
            rpm_repo_name,
            'RH rpm Repo was not associated to CV',
        )
        ContentView.publish({u'id': cv['id']})
        cv = ContentView.info({u'id': cv['id']})
        lc_env = make_lifecycle_environment({
            u'organization-id': self.org['id'],
        })
        # Promote the Published version of CV to the next env
        ContentView.version_promote({
            u'id': cv['versions'][0]['id'],
            u'to-lifecycle-environment-id': lc_env['id'],
        })
        cv = ContentView.info({u'id': cv['id']})
        environment = {
            'id': lc_env['id'],
            'name': lc_env['name'],
        }
        self.assertIn(environment, cv['lifecycle-environments'])
