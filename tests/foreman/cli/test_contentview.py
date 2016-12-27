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
    make_content_host,
    make_content_view,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_repository,
    make_user,
)
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.puppetmodule import PuppetModule
from robottelo.cli.subscription import Subscription
from robottelo.constants import (
    DEFAULT_CV,
    DOCKER_REGISTRY_HUB,
    DOCKER_UPSTREAM_NAME,
    ENVIRONMENT,
    FAKE_0_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    tier3,
)
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

    @staticmethod
    def _get_content_view_version_lce_names_set(content_view_id, version_id):
        """returns a set of content view version lifecycle environment names

        :rtype: set
        """
        lifecycle_environments = ContentView.version_info({
            'content-view-id': content_view_id,
            'id': version_id
        })['lifecycle-environments']
        return {lce['name'] for lce in lifecycle_environments}

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

    @run_only_on('sat')
    @stubbed
    def test_positive_update_filter(self):
        # Variations might be:
        # * A filter on errata date (only content that matches date
        # in filter)
        # * A filter on severity (only content of specific errata
        # severity.
        """Edit content views for a rh content

        @id: 4beab1e4-fc58-460e-af24-cdd2c3d283e6

        @assert: Edited content view save is successful and info is updated

        @caseautomation: notautomated

        """

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

        make_content_host({
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
        ContentView.filter_create({
            'content-view-id': new_cv['id'],
            'inclusion': 'true',
            'name': name,
            'type': 'rpm',
        })
        ContentView.filter_rule_create({
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

    @run_only_on('sat')
    @stubbed
    def test_positive_promote_rh_and_custom_content(self):
        """attempt to promote a content view containing RH content and
        custom content using filters

        @id: f96e97ef-f73c-4506-855c-2392e06f3a6a

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted

        @caseautomation: notautomated

        """

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
        # Promote the Default CV to the next env
        with self.assertRaises(CLIReturnCodeError):
            ContentView.version_promote({
                u'id': content_view['content-view-id'],
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

    @run_only_on('sat')
    @stubbed
    def test_positive_publish_rh_and_custom_content(self):
        """attempt to publish  a content view containing a RH and custom
        repos and has filters

        @id: 0b116172-06a3-4327-81a8-17a098a1a564

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be published

        @caseautomation: notautomated

        """

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
        self.assertIn(
            ENVIRONMENT,
            [env['label'] for env in version1['lifecycle-environments']],
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
        self.assertIn(
            self.env1['id'],
            [env['id'] for env in version1['lifecycle-environments']],
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
        self.assertIn(
            ENVIRONMENT,
            [env['label'] for env in version2['lifecycle-environments']],
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
        self.assertIn(
            self.env1['id'],
            [env['id'] for env in version2['lifecycle-environments']],
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
        self.assertIn(
            ENVIRONMENT,
            [env['label'] for env in version['lifecycle-environments']],
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
        self.assertIn(
            self.env1['id'],
            [env['id'] for env in version1['lifecycle-environments']],
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
        self.assertNotIn(
            ENVIRONMENT,
            [env['label'] for env in version1['lifecycle-environments']],
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
        make_content_host({
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
        make_content_host({
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
        ContentView.filter_create({
            'content-view-id': content_view['id'],
            'inclusion': 'true',
            'name': name,
            'type': 'rpm',
        })

        ContentView.filter_rule_create({
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

        make_content_host({
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

        make_content_host({
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

        make_content_host({
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

        make_content_host({
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

    @run_only_on('sat')
    @tier2
    def test_positive_remove_renamed_cv_version_from_default_env(self):
        """Remove version of renamed content view from Library environment

        @id: aa9bbfda-72e8-45ec-b26d-fdf2691980cf

        @Steps:

        1. Create a content view
        2. Add a yum repo to the content view
        3. Publish the content view
        4. Rename the content view
        5. remove the published version from Library environment

        @Assert: content view version is removed from Library environment

        @CaseLevel: Integration
        """
        new_name = gen_string('alpha')
        org = make_org()
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': custom_yum_repo['id'],
        })
        ContentView.publish({u'id': content_view['id']})
        # ensure that the published content version is in Library environment
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        self.assertIn(
            ENVIRONMENT,
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # rename the content view
        ContentView.update({
            'id': content_view['id'],
            'new-name': new_name
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertEqual(new_name, content_view['name'])
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': ENVIRONMENT
        })
        # ensure that the published content version is not in Library
        # environment
        self.assertNotIn(
            ENVIRONMENT,
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_promoted_cv_version_from_default_env(self):
        """Remove promoted content view version from Library environment

        @id: 6643837a-560a-47de-aa4d-90778914dcfa

        @Steps:

        1. Create a content view
        2. Add a puppet module(s) to the content view
        3. Publish the content view
        4. Promote the content view version from Library -> DEV
        5. remove the content view version from Library environment

        @Assert:

        1. Content view version exist only in DEV and not in Library
        2. The puppet module(s) exists in content view version

        @CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        ContentView.version_promote({
            'id': content_view_version['id'],
            'to-lifecycle-environment-id': lce_dev['id']
        })
        # ensure that the published content version is in Library and DEV
        # environments
        content_view_version_info = ContentView.version_info({
            'organization-id': org['id'],
            'content-view-id': content_view['id'],
            'id': content_view_version['id']
        })
        content_view_version_lce_names = {
            lce['name']
            for lce in content_view_version_info['lifecycle-environments']
        }
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name']},
            content_view_version_lce_names
        )
        initial_puppet_modules_ids = {
            puppet_module['id']
            for puppet_module in content_view_version_info.get(
                'puppet-modules', [])
        }
        self.assertGreater(len(initial_puppet_modules_ids), 0)
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': ENVIRONMENT
        })
        # ensure content view version not in Library and only in DEV
        # environment and that puppet module still exist
        content_view_version_info = ContentView.version_info({
            'organization-id': org['id'],
            'content-view-id': content_view['id'],
            'id': content_view_version['id']
        })
        content_view_version_lce_names = {
            lce['name']
            for lce in content_view_version_info['lifecycle-environments']
        }
        self.assertEqual({lce_dev['name']}, content_view_version_lce_names)
        puppet_modules_ids = {
                puppet_module['id']
                for puppet_module in content_view_version_info.get(
                    'puppet-modules', [])
        }
        self.assertEqual(initial_puppet_modules_ids, puppet_modules_ids)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_qe_promoted_cv_version_from_default_env(self):
        """Remove QE promoted content view version from Library environment

        @id: e286697f-4113-40a3-b8e8-9ca50647e6d5

        @Steps:

        1. Create a content view
        2. Add docker repo(s) to it
        3. Publish content view
        4. Promote the content view version to multiple environments
           Library -> DEV -> QE
        5. remove the content view version from Library environment

        @Assert: Content view version exist only in DEV, QE
        and not in Library

        @CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        docker_product = make_product({u'organization-id': org['id']})
        docker_repository = make_repository({
            'content-type': 'docker',
            'docker-upstream-name': DOCKER_UPSTREAM_NAME,
            'name': gen_string('alpha', 20),
            'product-id': docker_product['id'],
            'url': DOCKER_REGISTRY_HUB,
        })
        Repository.synchronize({'id': docker_repository['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': docker_repository['id'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV and QE
        # environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': ENVIRONMENT
        })
        # ensure content view version is not in Library and only in DEV and QE
        # environments
        self.assertEqual(
            {lce_dev['name'], lce_qe['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_prod_promoted_cv_version_from_default_env(self):
        """Remove PROD promoted content view version from Library environment

        @id: ffe3d64e-c3d2-4889-9454-ccc6b10f4db7

        @Steps:

        1. Create a content view
        2. Add yum repositories, puppet modules, docker repositories to CV
        3. Publish content view
        4. Promote the content view version to multiple environments
           Library -> DEV -> QE -> PROD
        5. remove the content view version from Library environment

        @Assert: Content view version exist only in DEV, QE, PROD
        and not in Library

        @CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        lce_prod = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_qe['name']
        })
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        docker_product = make_product({u'organization-id': org['id']})
        docker_repository = make_repository({
            'content-type': 'docker',
            'docker-upstream-name': DOCKER_UPSTREAM_NAME,
            'name': gen_string('alpha', 20),
            'product-id': docker_product['id'],
            'url': DOCKER_REGISTRY_HUB,
        })
        Repository.synchronize({'id': docker_repository['id']})
        content_view = make_content_view({u'organization-id': org['id']})
        for repo in [custom_yum_repo, docker_repository]:
            ContentView.add_repository({
                'id': content_view['id'],
                'organization-id': org['id'],
                'repository-id': repo['id'],
            })
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_prod]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV, QE and
        # PROD environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # remove content view version from Library lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': ENVIRONMENT
        })
        # ensure content view version is not in Library and only in DEV, QE
        # and PROD environments
        self.assertEqual(
            {lce_dev['name'], lce_qe['name'], lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_cv_version_from_env(self):
        """Remove promoted content view version from environment

        @id: 577757ac-b184-4ece-9310-182dd5ceb718

        @Steps:

        1. Create a content view
        2. Add a yum repo and a puppet module to the content view
        3. Publish the content view
        4. Promote the content view version to multiple environments
           Library -> DEV -> QE -> STAGE -> PROD
        5. remove the content view version from PROD environment
        6. Assert: content view version exists only in Library, DEV, QE, STAGE
           and not in PROD
        7. Promote again from STAGE -> PROD

        @Assert: Content view version exist in Library, DEV, QE, STAGE, PROD

        @CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        lce_stage = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_qe['name']
        })
        lce_prod = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_stage['name']
        })
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': custom_yum_repo['id'],
        })
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV, QE,
        # STAGE and PROD environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name'],
             lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # remove content view version from PROD lifecycle environment
        ContentView.remove_from_environment({
            'id': content_view['id'],
            'organization-id': org['id'],
            'lifecycle-environment': lce_prod['name']
        })
        # ensure content view version is not in PROD and only in Library, DEV,
        # QE and STAGE environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # promote content view version to PROD environment again
        ContentView.version_promote({
            'id': content_view_version['id'],
            'to-lifecycle-environment-id': lce_prod['id']
        })
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name'],
             lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_cv_version_from_multi_env(self):
        """Remove promoted content view version from multiple environment

        @id: 997cfd7d-9029-47e2-a41e-84f4370b5ce5

        @Steps:

        1. Create a content view
        2. Add a yum repo and a puppet module to the content view
        3. Publish the content view
        4. Promote the content view version to multiple environments
           Library -> DEV -> QE -> STAGE -> PROD
        5. Remove content view version from QE, STAGE and PROD

        @Assert: Content view version exists only in Library, DEV

        @CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        lce_stage = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_qe['name']
        })
        lce_prod = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_stage['name']
        })
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': custom_yum_repo['id'],
        })
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV, QE,
        # STAGE and PROD environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name'],
             lce_prod['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )
        # remove content view version from QE, STAGE, PROD lifecycle
        # environments
        for lce in [lce_qe, lce_stage, lce_prod]:
            ContentView.remove_from_environment({
                'id': content_view['id'],
                'organization-id': org['id'],
                'lifecycle-environment': lce['name']
            })
        # ensure content view version is not in PROD and only in Library, DEV,
        # QE and STAGE environments
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name']},
            self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        )

    @run_only_on('sat')
    @tier2
    def test_positive_delete_cv_promoted_to_multi_env(self):
        """Delete published content view with version promoted to multiple
         environments

        @id: 93dd7518-5901-4a71-a4c3-0f1215238b26

        @Steps:

        1. Create a content view
        2. Add a yum repo and a puppet module to the content view
        3. Publish the content view
        4. Promote the content view to multiple environment
           Library -> DEV -> QE -> STAGE -> PROD
        5. Delete the content view
           (may delete the published versions environments prior this step)

        @Assert: The content view doesn't exists

        @CaseLevel: Integration
        """
        org = make_org()
        lce_dev = make_lifecycle_environment({'organization-id': org['id']})
        lce_qe = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_dev['name']
        })
        lce_stage = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_qe['name']
        })
        lce_prod = make_lifecycle_environment({
            'organization-id': org['id'],
            'prior': lce_stage['name']
        })
        custom_yum_product = make_product({u'organization-id': org['id']})
        custom_yum_repo = make_repository({
            u'content-type': 'yum',
            u'product-id': custom_yum_product['id'],
            u'url': FAKE_1_YUM_REPO,
        })
        Repository.synchronize({'id': custom_yum_repo['id']})
        puppet_product = make_product({u'organization-id': org['id']})
        puppet_repository = make_repository({
            u'content-type': u'puppet',
            u'product-id': puppet_product['id'],
            u'url': FAKE_0_PUPPET_REPO,
        })
        Repository.synchronize({'id': puppet_repository['id']})
        puppet_modules = PuppetModule.list({
            u'repository-id': puppet_repository['id'],
            u'per-page': False,
        })
        self.assertGreater(len(puppet_modules), 0)
        puppet_module = random.choice(puppet_modules)
        content_view = make_content_view({u'organization-id': org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'organization-id': org['id'],
            'repository-id': custom_yum_repo['id'],
        })
        ContentView.puppet_module_add({
            u'content-view-id': content_view['id'],
            u'uuid': puppet_module['uuid'],
        })
        ContentView.publish({u'id': content_view['id']})
        content_view_versions = ContentView.info({
            u'id': content_view['id']
        })['versions']
        self.assertGreater(len(content_view_versions), 0)
        content_view_version = content_view_versions[-1]
        for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
            ContentView.version_promote({
                'id': content_view_version['id'],
                'to-lifecycle-environment-id': lce['id']
            })
        # ensure that the published content version is in Library, DEV, QE,
        # STAGE and PROD environments
        promoted_lce_names_set = self._get_content_view_version_lce_names_set(
                content_view['id'],
                content_view_version['id']
            )
        self.assertEqual(
            {ENVIRONMENT, lce_dev['name'], lce_qe['name'], lce_stage['name'],
             lce_prod['name']},
            promoted_lce_names_set
        )
        # remove from all promoted lifecycle environments
        for lce_name in promoted_lce_names_set:
            ContentView.remove_from_environment({
                'id': content_view['id'],
                'organization-id': org['id'],
                'lifecycle-environment': lce_name
            })
        # ensure content view in content views list
        content_views = ContentView.list({'organization-id': org['id']})
        self.assertIn(
            content_view['name'],
            [cv['name'] for cv in content_views]
        )
        # delete the content view
        ContentView.delete({'id': content_view['id']})
        # ensure the content view is not in content views list
        content_views = ContentView.list({'organization-id': org['id']})
        self.assertNotIn(
            content_view['name'],
            [cv['name'] for cv in content_views]
        )

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_remove_cv_version_from_env_with_host_registered(self):
        """Remove promoted content view version from environment that is used
        in association of an Activation key and content-host registration.

        @id: 001a2b76-a87b-4c11-8837-f5fe3c04a075

        @Steps:

        1. Create a content view cv1
        2. Add a yum repo and a puppet module to the content view
        3. Publish the content view
        4. Promote the content view to multiple environment
           Library -> DEV -> QE
        5. Create an Activation key with the QE environment
        6. Register a content-host using the Activation key
        7. Remove the content view cv1 version from QE environment.
           Note - prior removing replace the current QE environment of cv1 by
           DEV and content view cv1 for Content-host and for Activation key.
        8. Refresh content-host subscription

        @Assert:

        1. Activation key exists
        2. Content-host exists
        3. QE environment of cv1 was replaced by DEV environment of cv1
           in activation key
        4. QE environment of cv1 was replaced by DEV environment of cv1
           in content-host
        5. At content-host some package from cv1 is installable

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_delete_cv_multi_env_promoted_with_host_registered(self):
        """Delete published content view with version promoted to multiple
         environments, with one of the environments used in association of an
         Activation key and content-host registration.

        @id: 82442d23-45b5-4d39-b867-c5d46bbcbbf9

        @Steps:

        1. Create two content view cv1 and cv2
        2. Add a yum repo and a puppet module to both content views
        3. Publish the content views
        4. Promote the content views to multiple environment
           Library -> DEV -> QE
        5. Create an Activation key with the QE environment and cv1
        6. Register a content-host using the Activation key
        7. Delete the content view cv1.
           Note - prior deleting replace the current QE environment of cv1 by
           DEV and content view cv2 for Content-host and for Activation key.
        8. Refresh content-host subscription

        @Assert:

        1. The content view cv1 doesn't exist
        2. Activation key exists
        3. Content-host exists
        4. QE environment of cv1 was replaced by DEV environment of cv2
           in activation key
        5. QE environment of cv1 was replaced by DEV environment of cv2
           in content-host
        6. At content-host some package from cv2 is installable

        @caseautomation: notautomated

        @CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_remove_cv_version_from_multi_env_capsule_scenario(self):
        """Remove promoted content view version from multiple environment,
        with satellite setup to use capsule

        @id: 3725fef6-73a4-4dcb-a306-70e6ba826a3d

        @Steps:

        1. Create a content view
        2. Setup satellite to use a capsule and to sync all lifecycle
           environments
        3. Add a yum repo, puppet module and a docker repo to the content view
        4. Publish the content view
        5. Promote the content view to multiple environment
           Library -> DEV -> QE -> PROD
        6. Make sure the capsule is updated (content synchronization may be
           applied)
        7. Disconnect the capsule
        8. Remove the content view version from Library and DEV environments
           and assert successful completion
        9. Bring the capsule back online and assert that the task is completed
           in capsule
        10. Make sure the capsule is updated (content synchronization may be
            applied)

        @Assert: content view version in capsule is removed from Library
        and DEV and exists only in QE and PROD

        @caseautomation: notautomated

        @CaseLevel: System
        """
        # Note: This test case requires complete external capsule
        #  configuration.

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
    @stubbed()
    def test_negative_user_with_read_only_cv_permission(self):
        """Read-only user is able to view content view

        @id: 588f57b5-9855-4c14-80d0-64b617c6b6dc

        @setup: create a user with the Content View read-only role

        @assert: User with read-only role for content view can view the content
        view but not Create / Modify / Promote / Publish

        @caseautomation: notautomated

        """

    @run_only_on('sat')
    @stubbed()
    def test_positive_user_with_all_cv_permissions(self):
        """A user with all content view permissions is able to create,
        read, modify, promote, publish content views

        @id: ac40e9bb-9f1a-48d1-a0fe-9ac2be0f33f4

        @setup: create a user with all content view permissions

        @assert: User is able to perform create, read, modify, promote, publish
        content view

        @caseautomation: notautomated

        """
