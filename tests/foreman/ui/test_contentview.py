# -*- encoding: utf-8 -*-
"""Test class for Host/System Unification

Feature details: https://fedorahosted.org/katello/wiki/ContentViews


@Requirement: Contentview

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""
import random

from fauxfactory import gen_string
from nailgun import entities, entity_mixins
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo import manifests
from robottelo.constants import (
    CUST_PERMS_LIST,
    DEFAULT_CV,
    DOCKER_REGISTRY_HUB,
    ENVIRONMENT,
    FAKE_0_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    FEDORA23_OSTREE_REPO,
    FILTER_CONTENT_TYPE,
    FILTER_TYPE,
    PRDS,
    REPOS,
    REPOSET,
    REPO_TYPE,
    ZOO_CUSTOM_GPG_KEY,
)
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.decorators.host import skip_if_os
from robottelo.helpers import read_data_file
from robottelo.ui.base import UIError, UINoSuchElementError
from robottelo.ui.factory import make_contentview, make_lifecycle_environment
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session
from robottelo.test import UITestCase


class ContentViewTestCase(UITestCase):
    """Implement tests for content view via UI"""

    @classmethod
    def setUpClass(cls):
        super(ContentViewTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    # pylint: disable=too-many-arguments
    def setup_to_create_cv(self, repo_name=None, repo_url=None, repo_type=None,
                           repo_unprotected=True, rh_repo=None, org_id=None):
        """Create product/repo and sync it"""

        if not rh_repo:
            repo_name = repo_name or gen_string('alpha')

            # Creates new custom product via API's
            product = entities.Product(
                organization=org_id or self.organization
            ).create()
            # Creates new custom repository via API's
            repo_id = entities.Repository(
                name=repo_name,
                url=(repo_url or FAKE_1_YUM_REPO),
                content_type=(repo_type or REPO_TYPE['yum']),
                product=product,
                unprotected=repo_unprotected,
            ).create().id
        elif rh_repo:
            # Uploads the manifest and returns the result.
            with manifests.clone() as manifest:
                upload_manifest(org_id, manifest.content)
            # Enables the RedHat repo and fetches it's Id.
            repo_id = enable_rhrepo_and_fetchid(
                basearch=rh_repo['basearch'],
                # OrgId is passed as data in API hence str
                org_id=str(org_id),
                product=rh_repo['product'],
                repo=rh_repo['name'],
                reposet=rh_repo['reposet'],
                releasever=rh_repo['releasever'],
            )
        old_task_timeout = entity_mixins.TASK_TIMEOUT
        # Update timeout to 10 minutes to finish sync
        entity_mixins.TASK_TIMEOUT = 600
        # Sync repository
        entities.Repository(id=repo_id).sync()
        entity_mixins.TASK_TIMEOUT = old_task_timeout
        return repo_id

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create content views using different names

        @id: 804e51d7-f025-4ec2-a247-834afd351e89

        @assert: Content views are created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_contentview(
                        session, org=self.organization.name, name=name)
                    self.assertIsNotNone(
                        self.content_views.search(name),
                        'Failed to find content view %s from %s org' % (
                            name, self.organization.name)
                    )

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """try to create content views using invalid names

        @id: 974f2adc-b7da-4a8c-a8b5-d231b6bda1ce

        @assert: content views are not created; proper error thrown and
        system handles it gracefully
        """
        with Session(self.browser) as session:
            # invalid_names_list is used instead of invalid_values_list
            # because save button will not be enabled if name is blank
            for name in invalid_names_list():
                with self.subTest(name):
                    make_contentview(
                        session, org=self.organization.name, name=name)
                    self.assertTrue(
                        self.content_views.wait_until_element(
                            locators['contentviews.has_error']),
                        'No validation error found for "%s" from %s org' % (
                            name, self.organization.name))
                    self.assertIsNone(self.content_views.search(name))

    @run_only_on('sat')
    @tier2
    def test_positive_end_to_end(self):
        """create content view with yum repo, publish it
        and promote it to Library +1 env

        @id: 74c1b00d-c582-434f-bf73-588532588d50

        @steps:
        1. Create Product/repo and Sync it
        2. Create CV and add created repo in step1
        3. Publish and promote it to 'Library'
        4. Promote it to next environment

        @assert: content view is created, updated with repo publish and
        promoted to next selected env

        @CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        env_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        strategy, value = locators['content_env.select_name']
        with Session(self.browser) as session:
            # Create Life-cycle environment
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            self.assertIsNotNone(
                session.nav.wait_until_element(
                    (strategy, value % env_name))
            )
            # Creates a CV along with product and sync'ed repository
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            # Publish and promote CV to next environment
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
            self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @tier2
    def test_positive_add_puppet_module(self):
        """create content view with puppet repository

        @id: c772d55b-6762-4c25-bbaf-83e7c200fe8a

        @steps:
        1. Create Product/puppet repo and Sync it
        2. Create CV and add puppet modules from created repo

        @assert: content view is created, updated with puppet module

        @CaseLevel: Integration
        """
        repo_url = FAKE_0_PUPPET_REPO
        cv_name = gen_string('alpha')
        puppet_module = 'httpd'
        with Session(self.browser) as session:
            self.setup_to_create_cv(
                repo_url=repo_url, repo_type=REPO_TYPE['puppet'])
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_puppet_module(
                cv_name,
                puppet_module,
                filter_term='Latest',
            )
        # Workaround to fetch added puppet module name:
        # UI doesn't refresh and populate the added module name
        # until we logout and navigate again to puppet-module tab
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_content_views()
            module = self.content_views.fetch_puppet_module(
                cv_name, puppet_module)
            self.assertIsNotNone(module)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_filter(self):
        """create empty content views filter and remove it

        @id: 6c6deae7-13f1-4638-a960-d3565d93fd64

        @assert: content views filter removed successfully

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_contentview(
                session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['package'],
                FILTER_TYPE['exclude'],
            )
            self.content_views.remove_filter(cv_name, [filter_name])
            self.assertIsNone(self.content_views.search_filter(
                cv_name, filter_name))

    @run_only_on('sat')
    @tier2
    def test_positive_add_package_filter(self):
        """add package to content views filter

        @id: 1cc8d921-92e5-4b51-8050-a7e775095f97

        @assert: content views filter created and selected packages
        can be added for inclusion/exclusion

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['package'],
                FILTER_TYPE['include'],
            )
            self.content_views.add_packages_to_filter(
                cv_name,
                filter_name,
                ['cow', 'bird', 'crow', 'bear'],
                ['Equal To', 'Greater Than', 'Less Than', 'Range'],
                ['0.3', '0.5', '0.5', '4.1'],
                [None, None, None, '4.6'],
            )

    @run_only_on('sat')
    @tier2
    def test_positive_add_package_group_filter(self):
        """add package group to content views filter

        @id: 8c02a432-8b2a-4ba3-9613-7070b2dc2bcb

        @assert: content views filter created and selected package groups
        can be added for inclusion/exclusion

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['package group'],
                FILTER_TYPE['include'],
            )
            self.content_views.add_remove_package_groups_to_filter(
                cv_name,
                filter_name,
                ['mammals']
            )
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @tier2
    def test_positive_add_errata_filter(self):
        """add errata to content views filter

        @id: bb9eef30-62c4-435c-9573-9f31210b8d7d

        @assert: content views filter created and selected errata-id
        can be added for inclusion/exclusion

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['erratum by id'],
                FILTER_TYPE['include'],
            )
            self.content_views.add_remove_errata_to_filter(
                cv_name, filter_name, ['RHEA-2012:0001', 'RHEA-2012:0004'])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update content views name to valid one.

        @id: 7d8eb36a-536e-49dc-9eb4-a5885ec77819

        @assert: Content view is updated successfully and has proper name
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_contentview(
                session,
                org=self.organization.name,
                name=name,
                description=gen_string('alpha', 15),
            )
            self.assertIsNotNone(self.content_views.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.content_views.update(name, new_name)
                    self.assertIsNotNone(self.content_views.search(new_name))
                    name = new_name  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Try to update content views name to invalid one.

        @id: 211c319f-802a-4407-9c16-205a82d4afca

        @assert: Content View is not updated. Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_contentview(
                session, org=self.organization.name, name=name)
            self.assertIsNotNone(self.content_views.search(name))
            # invalid_names_list is used instead of invalid_values_list
            # because save button will not be enabled if name is blank
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.content_views.update(name, new_name)
                    self.assertIsNotNone(self.content_views.wait_until_element(
                        common_locators['alert.error_sub_form']))
                    self.assertIsNone(self.content_views.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_description(self):
        """Update content views description to valid one.

        @id: f5e46a3b-c317-4575-9c66-ef1da1926f66

        @assert: Content view is updated successfully and has proper
        description
        """
        name = gen_string('alpha', 8)
        desc = gen_string('alpha', 15)
        with Session(self.browser) as session:
            make_contentview(
                session,
                org=self.organization.name,
                name=name,
                description=desc,
            )
            self.assertIsNotNone(self.content_views.search(name))
            for new_desc in valid_data_list():
                with self.subTest(new_desc):
                    self.content_views.update(name, new_description=new_desc)
                    self.assertIsNotNone(self.content_views.wait_until_element(
                        common_locators['alert.success_sub_form']))

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_edit_rh_custom_spin(self):
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.
        """Edit content views for a custom rh spin.  For example,
        modify a filter

        @id: 05639074-ef6d-4c6b-8ff6-53033821e686

        @assert: edited content view save is successful and info is
        updated

        @caseautomation: notautomated


        @CaseLevel: System
        """

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete content views

        @id: bcea6ef0-bc25-4cc7-9c0c-3591bb8810e5

        @assert: Content view can be deleted and no longer appears in UI
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_contentview(
                        session, org=self.organization.name, name=name)
                    self.assertIsNotNone(
                        self.content_views.search(name),
                        'Failed to find content view %s from %s org' % (
                            name, self.organization.name)
                    )
                    self.content_views.delete(name)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_create_composite(self):
        # Note: puppet repos cannot/should not be used in this test
        # It shouldn't work - and that is tested in a different case.
        # Individual modules from a puppet repo, however, are a valid
        # variation.
        """create a composite content views

        @id: 550f1970-5cbd-4571-bb7b-17e97639b715

        @setup: sync multiple content source/types (RH, custom, etc.)

        @assert: Composite content views are created

        @CaseLevel: System
        """
        puppet_module = 'httpd'
        cv_name1 = gen_string('alpha')
        cv_name2 = gen_string('alpha')
        composite_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        with Session(self.browser) as session:
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name2)
            self.assertIsNotNone(self.content_views.search(cv_name2))
            self.setup_to_create_cv(
                repo_url=FAKE_0_PUPPET_REPO,
                repo_type=REPO_TYPE['puppet'],
                org_id=org.id,
            )
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name1)
            self.assertIsNotNone(self.content_views.search(cv_name1))
            self.content_views.add_puppet_module(
                cv_name1,
                puppet_module,
                filter_term='Latest',
            )
        # Workaround to fetch added puppet module name:
        # UI doesn't refresh and populate the added module name
        # until we logout and navigate again to puppet-module tab
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            module = self.content_views.fetch_puppet_module(
                cv_name1, puppet_module)
            self.assertIsNotNone(module)
            self.content_views.publish(cv_name1)
            self.content_views.add_remove_repos(cv_name2, [rh_repo['name']])
            self.content_views.publish(cv_name2)
            self.content_views.create(composite_name, is_composite=True)
            session.nav.go_to_select_org(org.name)
            self.content_views.add_remove_cv(
                composite_name, [cv_name1, cv_name2])

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_add_rh_content(self):
        """Add Red Hat content to a content view

        @id: c370fd79-0c0d-4685-99cb-848556c786c1

        @setup: Sync RH content

        @assert: RH Content can be seen in a view

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        with Session(self.browser) as session:
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @stubbed()
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_add_rh_custom_spin(self):
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.
        """associate Red Hat content in a view

        @id: 3e6c2d8a-b62d-4ec7-8353-4a6a4cb58209

        @setup: Sync RH content

        @steps: 1. Assure filter(s) applied to associated content

        @assert: Filtered RH content only is available/can be seen in a view

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    def test_positive_add_custom_content(self):
        """associate custom content in a view

        @id: 7128fc8b-0e8c-4f00-8541-2ca2399650c8

        @setup: Sync custom content

        @assert: Custom content can be seen in a view

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @tier2
    def test_negative_add_puppet_repo_to_composite(self):
        # Again, individual modules should be ok.
        """attempt to associate puppet repos within a composite
        content view

        @id: 283fa7da-ca40-4ce2-b3c5-da58ae01b8e7

        @assert: User cannot create a composite content view
        that contains direct puppet repos.

        @CaseLevel: Integration
        """
        composite_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_contentview(
                session,
                org=self.organization.name,
                name=composite_name,
                is_composite=True
            )
            self.assertIsNotNone(self.content_views.search(composite_name))
            with self.assertRaises(UIError) as context:
                self.content_views.add_puppet_module(
                    composite_name, 'httpd', filter_term='Latest')
            self.assertEqual(
                context.exception.message,
                'Could not find tab to add puppet_modules'
            )

    @run_only_on('sat')
    @tier2
    def test_negative_add_components_to_non_composite(self):
        """attempt to associate components to a non-composite
        content view

        @id: fa3e6aea-7ee3-46a6-a5ba-248de3c20a8f

        @assert: User cannot add components to the view

        @CaseLevel: Integration
        """
        cv1_name = gen_string('alpha')
        cv2_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_contentview(
                session, org=self.organization.name, name=cv1_name)
            self.assertIsNotNone(self.content_views.search(cv1_name))
            make_contentview(
                session, org=self.organization.name, name=cv2_name)
            self.assertIsNotNone(self.content_views.search(cv2_name))
            with self.assertRaises(UINoSuchElementError) as context:
                self.content_views.add_remove_cv(cv1_name, [cv2_name])
            self.assertEqual(
                context.exception.message,
                'Could not find ContentView tab, please make sure '
                'selected view is composite'
            )

    @run_only_on('sat')
    @tier2
    def test_negative_add_unpublished_cv_to_composite(self):
        """Attempt to associate unpublished non-composite content view with
        composite content view.

        @id: dc253606-3425-489d-bc01-266787d36841

        @steps:

        1. Create an empty non-composite content view. Do not publish it.
        2. Create a new composite content view

        @assert: Non-composite content view is not listed as available to be
        added to composite content view.

        @CaseLevel: Integration

        @BZ: 1367123
        """
        unpublished_cv_name = gen_string('alpha')
        composite_cv_name = gen_string('alpha')
        with Session(self.browser) as session:
            # Create unpublished component CV
            make_contentview(
                session, org=self.organization.name, name=unpublished_cv_name)
            self.assertIsNotNone(
                self.content_views.search(unpublished_cv_name))
            # Create composite CV
            make_contentview(
                session,
                org=self.organization.name,
                name=composite_cv_name,
                is_composite=True
            )
            self.assertIsNotNone(self.content_views.search(composite_cv_name))
            # Add component to composite CV
            with self.assertRaises(UINoSuchElementError):
                self.content_views.add_remove_cv(
                    composite_cv_name, [unpublished_cv_name])

    @run_only_on('sat')
    @tier2
    def test_negative_add_non_composite_cv_to_composite(self):
        """Attempt to associate both published and unpublished
        non-composite content views with composite content view.

        @id: 93307c2a-a03f-44fa-972d-43f6e40b9de6

        @steps:

        1. Create an empty non-composite content view. Do not publish it
        2. Create a second non-composite content view. Publish it.
        3. Create a new composite content view.
        4. Add the published non-composite content view to the composite
            content view.

        @assert:

        1. Unpublished non-composite content view is not listed as available
            to be added to composite content view.
        2. Published non-composite content view is listed as available to be
            added to composite content view.
        3. Published non-composite content view is successfully added to
            composite content view.

        @CaseLevel: Integration

        @BZ: 1367123
        """
        published_cv_name = gen_string('alpha')
        unpublished_cv_name = gen_string('alpha')
        composite_cv_name = gen_string('alpha')
        with Session(self.browser) as session:
            # Create published component CV
            make_contentview(
                session, org=self.organization.name, name=published_cv_name)
            self.assertIsNotNone(
                self.content_views.search(published_cv_name))
            self.content_views.publish(published_cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            # Create unpublished component CV
            make_contentview(
                session, org=self.organization.name, name=unpublished_cv_name)
            self.assertIsNotNone(
                self.content_views.search(unpublished_cv_name))
            # Create composite CV
            make_contentview(
                session,
                org=self.organization.name,
                name=composite_cv_name,
                is_composite=True
            )
            self.assertIsNotNone(self.content_views.search(composite_cv_name))
            # Add published component to composite CV
            self.content_views.add_remove_cv(
                composite_cv_name, [published_cv_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            # Add unpublished component to composite CV
            with self.assertRaises(UINoSuchElementError):
                self.content_views.add_remove_cv(
                    composite_cv_name, [unpublished_cv_name])

    @run_only_on('sat')
    @tier2
    def test_negative_add_dupe_repos(self):
        """attempt to associate the same repo multiple times within a
        content view

        @id: 24b98075-fca6-4d80-a778-066193c71e7f

        @assert: User cannot add repos multiple times to the view

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            with self.assertRaises(UIError) as context:
                self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertEqual(
                context.exception.message,
                u'Could not find repo "{0}" to add into CV'
                .format(repo_name)
            )

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_negative_add_dupe_modules(self):
        """attempt to associate duplicate puppet module(s) within a
        content view

        @id: ee33a306-9f91-439d-ac7c-d30f7e1a14cc

        @assert: User cannot add modules multiple times to the view

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_promote_with_rh_content(self):
        """attempt to promote a content view containing RH content

        @id: 82f71639-3580-49fd-bd5a-8dba568b98d1

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted

        @CaseLevel: System
        """
        cv_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        env_name = gen_string('alpha')
        strategy, value = locators['content_env.select_name']
        # Create new org to import manifest
        org = entities.Organization().create()
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session, org=org.name, name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element(
                (strategy, value % env_name)))
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_promote_with_rh_custom_spin(self):
        """attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.

        @id: 7d93c81f-2815-4b0e-b72c-23a902fe34b1

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted

        @CaseLevel: System
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        env_name = gen_string('alpha')
        # Create new org to import manifest
        org = entities.Organization().create()
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session, org=org.name, name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['content_env.select_name'] % env_name))
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add rh repo
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            # add a filter
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['package'],
                FILTER_TYPE['exclude'],
            )
            # assert the added filter visible
            self.assertIsNotNone(
                self.content_views.search_filter(cv_name, filter_name))
            # exclude some package in the created filter
            self.content_views.add_packages_to_filter(
                cv_name,
                filter_name,
                ['gofer'],
                ['All Versions'],
                [None],
                [None]
            )
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @tier2
    def test_positive_promote_with_custom_content(self):
        """attempt to promote a content view containing custom content

        @id: 7c2fd8f0-c83f-4725-8953-9590112fae50

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be promoted

        @CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        env_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        strategy, value = locators['content_env.select_name']
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element
                                 ((strategy, value % env_name)))
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_promote_composite_with_custom_content(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to promote composite content view containing custom
        content

        @id: 35efbd83-d32e-4831-9d5b-1adb15289f54

        @setup: Multiple environments for an org; custom content synced

        @steps: create a composite view containing multiple content types

        @assert: Content view can be promoted

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_publish_with_rh_content(self):
        """attempt to publish a content view containing RH content

        @id: bd24dc13-b6c4-4a9b-acb2-cd6df30f436c

        @setup: RH content synced

        @assert: Content view can be published

        @CaseLevel: System
        """
        cv_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        with Session(self.browser) as session:
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_publish_with_rh_custom_spin(self):
        """attempt to publish  a content view containing a custom RH
        spin - i.e., contains filters.

        @id: 6804f399-8f09-4c53-8f0d-8e681892e93c

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be published

        @CaseLevel: System
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        env_name = gen_string('alpha')
        # Create new org to import manifest
        org = entities.Organization().create()
        with Session(self.browser) as session:
            # create a lifecycle environment
            make_lifecycle_environment(
                session, org=org.name, name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['content_env.select_name'] % env_name))
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
            # Create content view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add rh repo
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            # Add a package exclude filter
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['package'],
                FILTER_TYPE['exclude'],
            )
            # assert the added filter visible
            self.assertIsNotNone(
                self.content_views.search_filter(cv_name, filter_name))
            # exclude some package in the created filter
            self.content_views.add_packages_to_filter(
                cv_name,
                filter_name,
                ['gofer'],
                ['All Versions'],
                [None],
                [None]
            )
            # Publish the content view
            self.content_views.publish(cv_name)
            # Assert the content view successfully published
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @tier2
    def test_positive_publish_with_custom_content(self):
        """attempt to publish a content view containing custom content

        @id: 66b5efc7-2e43-438e-bd80-a754814222f9

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be published

        @CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        env_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        strategy, value = locators['content_env.select_name']
        with Session(self.browser) as session:
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element(
                (strategy, value % env_name)))
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_publish_composite_with_custom_content(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to publish composite content view containing custom
        content

        @id: 73947204-408e-4e2e-b87f-ba2e52ee50b6

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be published

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_publish_version_changes_in_target_env(self):
        # Dev notes:
        # If Dev has version x, then when I promote version y into
        # Dev, version x goes away (ie when I promote version 1 to Dev,
        # version 3 goes away)
        """when publishing new version to environment, version
        gets updated

        @id: c9fa3def-baa2-497f-b6a6-f3b2d72d1ce9

        @setup: Multiple environments for an org; multiple versions
        of a content view created/published

        @steps:
        1. publish a view to an environment noting the CV version
        2. edit and republish a new version of a CV

        @assert: Content view version is updated intarget environment.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_publish_version_changes_in_source_env(self):
        # Dev notes:
        # Similarly when I publish version y, version x goes away from
        # Library (ie when I publish version 2, version 1 disappears)
        """when publishing new version to environment, version
        gets updated

        @id: 576ac8b4-7efe-4267-a672-868a5f3eb28a

        @setup: Multiple environments for an org; multiple versions
        of a content view created/published

        @steps:
        1. publish a view to an environment
        2. edit and republish a new version of a CV

        @assert: Content view version is updated in source environment.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    def test_positive_clone_within_same_env(self):
        """attempt to create new content view based on existing
        view within environment

        @id: 862c385b-d98c-4c29-8345-fd7a5900483a

        @assert: Content view can be cloned

        @CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        copy_cv_name = gen_string('alpha')
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            # Publish the CV
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            # Copy the CV
            self.content_views.copy_view(cv_name, copy_cv_name)
            self.assertIsNotNone(self.content_views.search(copy_cv_name))
            self.assertEqual(
                repo_name,
                self.content_views.fetch_yum_content_repo_name(copy_cv_name)
            )

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_clone_within_diff_env(self):
        # Dev note: "not implemented yet"
        """attempt to create new content view based on existing
        view, inside a different environment

        @id: 09b9307f-91de-4d3d-a6af-31c526ea816f

        @assert: Content view can be published

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_refresh_errata_to_new_view_in_same_env(self):
        """attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment

        @id: e990bf30-04d2-4784-a1e0-e0424babbddd

        @assert: Content view can be published

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_subscribe_system(self):
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
        """attempt to subscribe systems to content view(s)

        @id: 3ea6719b-df4d-4b0f-b4b4-69ce852f632e

        @assert: Systems can be subscribed to content view(s)

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_restart_promote_via_dynflow(self):
        """attempt to restart a promotion

        @id: c7f4e673-5164-417f-a072-1cc51d176780

        @steps:
        1. (Somehow) cause a CV promotion to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart promotion

        @assert: Promotion is restarted.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_restart_publish_via_dynflow(self):
        """attempt to restart a publish

        @id: d7a1204f-5d7c-4978-bb78-f366786d006a

        @steps:
        1. (Somehow) cause a CV publish  to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart publish

        @assert: Publish is restarted.

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    # ROLES TESTING
    # All this stuff is speculative at best.

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_admin_user_actions(self):
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user with admin permissions
        # for Content Views
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify, Delete, Promote Publish, Subscribe
        """attempt to view content views

        @id: c4d270fc-a3e6-4ae2-a338-41d864a5622a

        @setup: create a user with the Content View admin role

        @assert: User with admin role for content view can perform all
        Variations above

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_readonly_user_actions(self):
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user with read-only permissions
        # for Content Views
        # THIS IS EVEN ASSUMING WE HAVE A "READ-ONLY" ROLE IN THE FIRST PLACE
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify,  Promote?, Publish?, Subscribe??
        """attempt to view content views

        @id: ebdc37ed-7887-4f64-944c-f2f92c58a206

        @setup: create a user with the Content View read-only role

        @assert: User with read-only role for content view can perform all
        Variations above

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_negative_non_admin_user_actions(self):
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user withOUT admin permissions
        # for Content Views
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify, Delete, Promote Publish, Subscribe
        """attempt to view content views

        @id: aae6eede-b40e-4e06-a5f7-59d9251aa35d

        @setup: create a user with the Content View admin role

        @assert: User withOUT admin role for content view canNOT perform any
        Variations above

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_negative_non_readonly_user_actions(self):
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user withOUT read-only permissions
        # for Content Views
        # THIS IS EVEN ASSUMING WE HAVE A "READ-ONLY" ROLE IN THE FIRST PLACE
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify,  Promote?, Publish?, Subscribe??
        """attempt to view content views

        @id: 9cbc661a-dbe3-4b88-af27-4cf7b9544074

        @setup: create a user withOUT the Content View read-only role

        @assert: User withOUT read-only role for content view can perform all
        Variations above

        @caseautomation: notautomated


        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    def test_positive_delete_default_version(self):
        """Delete a content-view version associated to 'Library'

        @id: 6000a3f5-a8c2-49a4-ba30-d73a18d39e0a

        @Assert: Deletion was performed successfully

        @CaseLevel: Integration
        """
        key_content = read_data_file(ZOO_CUSTOM_GPG_KEY)
        org = entities.Organization().create()
        gpgkey = entities.GPGKey(
            content=key_content,
            organization=org,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(organization=org).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(
            url=FAKE_1_YUM_REPO,
            gpg_key=gpgkey,
            product=product,
        ).create()
        # sync repository
        repo.sync()
        # Create content view
        cv = entities.ContentView(organization=org).create()
        cv.repository = [repo]
        cv = cv.update(['repository'])
        self.assertEqual(len(cv.repository), 1)
        # Publish content view
        cv.publish()
        # Get published content-view version info
        cvv = entities.ContentView(id=cv.id).read().version
        self.assertEqual(len(cvv), 1)
        # API returns version like '1.0'
        # WebUI displays version like 'Version 1.0'
        version = 'Version {0}'.format(cvv[0].read().version)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @tier2
    def test_positive_delete_non_default_version(self):
        """Delete a content-view version associated to non-default
        environment

        @id: 1c1beb36-e06b-419f-96db-43b4d85c5e25

        @Assert: Deletion was performed successfully

        @CaseLevel: Integration
        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product).create()
        repo.sync()
        cv = entities.ContentView(organization=org).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()

        cvv = cv.read().version[0].read()
        version = 'Version {0}'.format(cvv.version)
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        cvv.promote(data={u'environment_id': lc_env.id})
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @tier2
    def test_positive_delete_version_with_ak(self):
        """Delete a content-view version that had associated activation
        key to it

        @id: 0da50b26-f82b-4663-9372-4c39270d4323

        @Assert: Deletion was performed successfully

        @CaseLevel: Integration
        """
        org = entities.Organization().create()
        cv = entities.ContentView(organization=org).create()
        cv.publish()
        cvv = cv.read().version[0].read()
        version = 'Version {0}'.format(cvv.version)
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        cvv.promote(data={u'environment_id': lc_env.id})

        ak = entities.ActivationKey(
            name=gen_string('alphanumeric'),
            environment=lc_env.id,
            organization=org,
            content_view=cv,
        ).create()

        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            session.nav.go_to_content_views()
            self.content_views.validate_version_cannot_be_deleted(
                cv.name,
                version,
            )
            self.activationkey.update(
                ak.name,
                content_view=DEFAULT_CV,
                env=ENVIRONMENT,
            )
            self.content_views.delete_version(cv.name, version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_add_custom_ostree(self):
        """Create a CV with custom ostree contents

        @id: 66626fcd-9d2b-4ff5-a596-b7754b044dbe

        @Assert: CV should be created successfully with custom ostree contents

        @CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        self.setup_to_create_cv(
            repo_name=repo_name,
            repo_url=FEDORA23_OSTREE_REPO,
            repo_type=REPO_TYPE['ostree'],
            repo_unprotected=False
        )
        with Session(self.browser) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [repo_name],
                repo_type='ostree'
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_add_rh_ostree(self):
        """Create a CV with RH ostree contents

        @id: 2c6ee15f-a058-4569-a324-aec4bba1bd17

        @Assert: CV should be created successfully with RH ostree contents

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhaht']['name'],
            'product': PRDS['rhah'],
            'reposet': REPOSET['rhaht'],
            'basearch': None,
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
        with Session(self.browser) as session:
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [rh_repo['name']],
                repo_type='ostree'
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_custom_ostree(self):
        """Create a CV with custom ostree contents and remove the
        contents.

        @id: 0e312f20-846b-440e-9c3a-392e889c9cdd

        @Assert: Content should be removed and CV should be updated
        successfully

        @CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        self.setup_to_create_cv(
            repo_name=repo_name,
            repo_url=FEDORA23_OSTREE_REPO,
            repo_type=REPO_TYPE['ostree'],
            repo_unprotected=False
        )
        with Session(self.browser) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [repo_name],
                repo_type='ostree'
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            self.content_views.add_remove_repos(
                cv_name,
                [repo_name],
                add_repo=False,
                repo_type='ostree'
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_rh_ostree(self):
        """Create a CV with RH ostree contents and remove the
        contents.

        @id: 852ce474-82a7-4199-9f12-5b9ad352e036

        @Assert: Content should be removed and CV should be updated
        successfully

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhaht']['name'],
            'product': PRDS['rhah'],
            'reposet': REPOSET['rhaht'],
            'basearch': None,
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
        with Session(self.browser) as session:
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [rh_repo['name']],
                repo_type='ostree'
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            self.content_views.add_remove_repos(
                cv_name,
                [rh_repo['name']],
                add_repo=False,
                repo_type='ostree'
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_create_with_custom_ostree_other_contents(self):
        """Create a CV with custom ostree contents and other custom yum, puppet
        repos.

        @id: b139eb12-d960-4a45-9e22-3a22184c5415

        @Assert: CV should be created successfully with all custom contents

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        puppet_module = 'httpd'
        prod = entities.Product(organization=self.organization).create()
        # Creates new ostree repository using api
        ostree_repo = entities.Repository(
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        old_task_timeout = entity_mixins.TASK_TIMEOUT
        # Update timeout to 10 minutes to finish sync
        entity_mixins.TASK_TIMEOUT = 600
        ostree_repo.sync()
        entity_mixins.TASK_TIMEOUT = old_task_timeout
        yum_repo = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=prod,
        ).create()
        yum_repo.sync()
        puppet_repo = entities.Repository(
            url=FAKE_0_PUPPET_REPO,
            content_type='puppet',
            product=prod,
        ).create()
        puppet_repo.sync()
        with Session(self.browser) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add ostree repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [ostree_repo.name],
                repo_type='ostree'
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            # Add yum repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [yum_repo.name],
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            self.content_views.add_puppet_module(
                cv_name,
                puppet_module,
                filter_term='Latest',
            )
        # Workaround to fetch added puppet module name:
        # UI doesn't refresh and populate the added module name
        # until we logout and navigate again to puppet-module tab
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            module = self.content_views.fetch_puppet_module(
                cv_name, puppet_module)
            self.assertIsNotNone(module)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_create_with_rh_ostree_other_contents(self):
        """Create a CV with RH ostree contents and other RH yum repos.

        @id: 4398f5cc-62de-4a11-996b-24a7ad30ad3a

        @Assert: CV should be created successfully with all custom contents

        @CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        rh_ah_repo = {
            'name': REPOS['rhaht']['name'],
            'product': PRDS['rhah'],
            'reposet': REPOSET['rhaht'],
            'basearch': None,
            'releasever': None,
        }
        rh_st_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        for rh_repo in [rh_ah_repo, rh_st_repo]:
            # Enables the RedHat repo and fetches it's Id.
            repo_id = enable_rhrepo_and_fetchid(
                basearch=rh_repo['basearch'],
                # OrgId is passed as data in API hence str
                org_id=str(org.id),
                product=rh_repo['product'],
                repo=rh_repo['name'],
                reposet=rh_repo['reposet'],
                releasever=rh_repo['releasever'],
            )
            old_task_timeout = entity_mixins.TASK_TIMEOUT
            # Update timeout to 10 minutes to finish sync
            entity_mixins.TASK_TIMEOUT = 600
            # Sync repository
            entities.Repository(id=repo_id).sync()
            entity_mixins.TASK_TIMEOUT = old_task_timeout
        with Session(self.browser) as session:
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [rh_ah_repo['name']],
                repo_type='ostree'
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            self.content_views.add_remove_repos(
                cv_name,
                [rh_st_repo['name']],
                repo_type='yum'
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_publish_with_custom_ostree(self):
        """Create a CV with custom ostree contents and publish it.

        @id: c5e8d2ba-8cb2-47d8-b352-60972cf291e9

        @Assert: CV should be published with OStree contents

        @CaseLevel: Integration
        """
        prod = entities.Product(organization=self.organization).create()
        # Creates new ostree repository using api
        ostree_repo = entities.Repository(
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        old_task_timeout = entity_mixins.TASK_TIMEOUT
        # Update timeout to 10 minutes to finish sync
        entity_mixins.TASK_TIMEOUT = 600
        ostree_repo.sync()
        entity_mixins.TASK_TIMEOUT = old_task_timeout
        cv = entities.ContentView(organization=self.organization).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv.name,
                [ostree_repo.name],
                repo_type='ostree'
            )
            self.content_views.publish(cv.name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_published_custom_ostree_version(self):
        """Remove published custom ostree contents version from selected CV.

        @id: 949d6ee7-330a-4423-b219-550693522c7f

        @Assert: Published version with OStree contents should be removed
        successfully.

        @CaseLevel: Integration
        """
        org = entities.Organization().create()
        prod = entities.Product(organization=org).create()
        # Creates new ostree repository using api
        ostree_repo = entities.Repository(
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        old_task_timeout = entity_mixins.TASK_TIMEOUT
        # Update timeout to 10 minutes to finish sync
        entity_mixins.TASK_TIMEOUT = 600
        ostree_repo.sync()
        entity_mixins.TASK_TIMEOUT = old_task_timeout
        cv = entities.ContentView(organization=org).create()
        cv.repository = [ostree_repo]
        cv = cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        cv_info = cv.version[0].read()
        version = 'Version {0}'.format(cv_info.version)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_promote_with_custom_ostree(self):
        """Create a CV with custom ostree contents and publish, promote it
        to next environment.

        @id: 05f4ddc8-a3ad-4caf-b417-3b437b48fa47

        @Assert: CV should be promoted with custom OStree contents

        @CaseLevel: Integration
        """
        prod = entities.Product(organization=self.organization).create()
        lc_env = entities.LifecycleEnvironment(
            organization=self.organization
        ).create()
        # Creates new ostree repository using api
        ostree_repo = entities.Repository(
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        old_task_timeout = entity_mixins.TASK_TIMEOUT
        # Update timeout to 10 minutes to finish sync
        entity_mixins.TASK_TIMEOUT = 600
        ostree_repo.sync()
        entity_mixins.TASK_TIMEOUT = old_task_timeout
        cv = entities.ContentView(organization=self.organization).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv.name,
                [ostree_repo.name],
                repo_type='ostree'
            )
            self.content_views.publish(cv.name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            self.content_views.promote(cv.name, 'Version 1', lc_env.name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_promoted_custom_ostree_contents(self):
        """Remove promoted custom ostree contents from selected environment of
        CV.

        @id: a66c8a9e-953e-41a5-aaac-9d9473a3d9fc

        @Assert: Promoted custom OStree contents should be removed successfully

        @CaseLevel: Integration
        """
        org = entities.Organization().create()
        prod = entities.Product(organization=org).create()
        # Creates new ostree repository using api
        ostree_repo = entities.Repository(
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        old_task_timeout = entity_mixins.TASK_TIMEOUT
        # Update timeout to 10 minutes to finish sync
        entity_mixins.TASK_TIMEOUT = 600
        ostree_repo.sync()
        entity_mixins.TASK_TIMEOUT = old_task_timeout
        cv = entities.ContentView(organization=org).create()
        cv.repository = [ostree_repo]
        cv = cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        cv_info = cv.version[0].read()
        version = 'Version {0}'.format(cv_info.version)
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        promote(cv.version[0], lc_env.id)

        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_publish_promote_with_custom_ostree_and_other(self):
        """Create a CV with ostree as well as yum and puppet type contents and
        publish and promote them to next environment.

        @id: cf86f9bc-e32a-4048-b793-fe6e9447f7e4

        @Assert: CV should be published and promoted with custom OStree and all
        other contents

        @CaseLevel: Integration
        """
        puppet_module = 'httpd'
        lc_env = entities.LifecycleEnvironment(
            organization=self.organization
        ).create()
        prod = entities.Product(organization=self.organization).create()
        # Creates new ostree repository using api
        ostree_repo = entities.Repository(
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        old_task_timeout = entity_mixins.TASK_TIMEOUT
        # Update timeout to 10 minutes to finish sync
        entity_mixins.TASK_TIMEOUT = 600
        ostree_repo.sync()
        entity_mixins.TASK_TIMEOUT = old_task_timeout
        yum_repo = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=prod,
        ).create()
        yum_repo.sync()
        puppet_repo = entities.Repository(
            url=FAKE_0_PUPPET_REPO,
            content_type='puppet',
            product=prod,
        ).create()
        puppet_repo.sync()
        cv = entities.ContentView(organization=self.organization).create()
        cv.repository = [ostree_repo, yum_repo]
        cv = cv.update(['repository'])
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.content_views.add_puppet_module(
                cv.name,
                puppet_module,
                filter_term='Latest',
            )
        # Workaround to fetch added puppet module name:
        # UI doesn't refresh and populate the added module name
        # until we logout and navigate again to puppet-module tab
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            module = self.content_views.fetch_puppet_module(
                cv.name, puppet_module)
            self.assertIsNotNone(module)
            self.content_views.publish(cv.name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            self.content_views.promote(cv.name, 'Version 1', lc_env.name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_published_version_of_mixed_contents(self):
        """Remove mixed(ostree, yum, puppet, docker) published content version
        from selected CV.

        @id: b4d69aff-b667-43df-ac1f-28c58c73d846

        @Assert: Published version with mixed(ostree, yum, puppet, docker)
        contents should be removed successfully.

        @CaseLevel: Integration
        """
        prod = entities.Product(organization=self.organization).create()
        # Creates new ostree repository using api
        ostree_repo = entities.Repository(
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        old_task_timeout = entity_mixins.TASK_TIMEOUT
        # Update timeout to 10 minutes to finish sync
        entity_mixins.TASK_TIMEOUT = 600
        ostree_repo.sync()
        entity_mixins.TASK_TIMEOUT = old_task_timeout
        # Create new yum repository
        yum_repo = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=prod,
        ).create()
        yum_repo.sync()
        # Create new Puppet repository
        puppet_repo = entities.Repository(
            url=FAKE_0_PUPPET_REPO,
            content_type='puppet',
            product=prod,
        ).create()
        puppet_repo.sync()
        # Create new docker repository
        docker_repo = entities.Repository(
            content_type=u'docker',
            docker_upstream_name=u'busybox',
            product=prod,
            url=DOCKER_REGISTRY_HUB,
        ).create()
        docker_repo.sync()
        cv = entities.ContentView(organization=self.organization).create()
        cv.repository = [ostree_repo, yum_repo, docker_repo]
        cv = cv.update(['repository'])
        puppet_module = random.choice(
            cv.available_puppet_modules()['results']
        )
        self.assertEqual(len(cv.read().puppet_module), 0)
        entities.ContentViewPuppetModule(
            author=puppet_module['author'],
            name=puppet_module['name'],
            content_view=cv,
        ).create()
        self.assertEqual(len(cv.read().puppet_module), 1)

        cv.publish()
        cv = cv.read()
        cv_info = cv.version[0].read()
        version = 'Version {0}'.format(cv_info.version)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_publish_with_rh_ostree(self):
        """Create a CV with RH ostree contents and publish it.

        @id: 4b5f487d-9de9-4645-8d73-7272f564eb75

        @Assert: CV should be published with RH OStree contents

        @CaseLevel: Integration
        """
        rh_ah_repo = {
            'name': REPOS['rhaht']['name'],
            'product': PRDS['rhah'],
            'reposet': REPOSET['rhaht'],
            'basearch': None,
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        self.setup_to_create_cv(rh_repo=rh_ah_repo, org_id=org.id)
        cv = entities.ContentView(organization=org).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv.name,
                [rh_ah_repo['name']],
                repo_type='ostree'
            )
            self.content_views.publish(cv.name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_published_rh_ostree_version(self):
        """Remove published rh ostree contents version from selected CV.

        @id: a5767568-df3a-43c0-beb7-474c82a445d4

        @Assert: Published version with RH OStree contents should be removed
        successfully.

        @CaseLevel: Integration
        """
        rh_ah_repo = {
            'name': REPOS['rhaht']['name'],
            'product': PRDS['rhah'],
            'reposet': REPOSET['rhaht'],
            'basearch': None,
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        repo_id = self.setup_to_create_cv(rh_repo=rh_ah_repo, org_id=org.id)
        cv = entities.ContentView(organization=org).create()
        cv.repository = [entities.Repository(id=repo_id)]
        cv = cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        cv_info = cv.version[0].read()
        version = 'Version {0}'.format(cv_info.version)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_promote_with_rh_ostree(self):
        """Create a CV with RH ostree contents and publish, promote it
        to next environment.

        @id: 19b7a33f-d13e-454b-bfee-295296e78967

        @Assert: CV should be promoted with RH OStree contents

        @caseautomation: notautomated

        @CaseLevel: Integration
        """
        rh_ah_repo = {
            'name': REPOS['rhaht']['name'],
            'product': PRDS['rhah'],
            'reposet': REPOSET['rhaht'],
            'basearch': None,
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        repo_id = self.setup_to_create_cv(rh_repo=rh_ah_repo, org_id=org.id)
        cv = entities.ContentView(organization=org).create()
        cv.repository = [entities.Repository(id=repo_id)]
        cv = cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        cv_info = cv.version[0].read()
        version = 'Version {0}'.format(cv_info.version)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.promote(cv.name, version, lc_env.name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_promoted_rh_ostree_contents(self):
        """Remove promoted rh ostree contents from selected environment of CV.

        @id: 9e49e470-8b30-4941-9868-23d9718aaad9

        @Assert: Promoted rh OStree contents should be removed successfully

        @CaseLevel: Integration
        """
        rh_ah_repo = {
            'name': REPOS['rhaht']['name'],
            'product': PRDS['rhah'],
            'reposet': REPOSET['rhaht'],
            'basearch': None,
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        repo_id = self.setup_to_create_cv(rh_repo=rh_ah_repo, org_id=org.id)
        cv = entities.ContentView(organization=org).create()
        cv.repository = [entities.Repository(id=repo_id)]
        cv = cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        cv_info = cv.version[0].read()
        version = 'Version {0}'.format(cv_info.version)
        promote(cv.version[0], lc_env.id)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_publish_promote_with_rh_ostree_and_other(self):
        """Create a CV with rh ostree as well as rh yum contents and
        publish, promote them to next environment.

        @id: f1849f6a-6ad6-432f-a70c-7d61079f482a

        @Assert: CV should be published and promoted with rh ostree and all
        other contents

        @CaseLevel: Integration
        """
        rh_ah_repo = {
            'name': REPOS['rhaht']['name'],
            'product': PRDS['rhah'],
            'reposet': REPOSET['rhaht'],
            'basearch': None,
            'releasever': None,
        }
        rh_st_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        for rh_repo in [rh_ah_repo, rh_st_repo]:
            # Enables the RedHat repo and fetches it's Id.
            repo_id = enable_rhrepo_and_fetchid(
                basearch=rh_repo['basearch'],
                # OrgId is passed as data in API hence str
                org_id=str(org.id),
                product=rh_repo['product'],
                repo=rh_repo['name'],
                reposet=rh_repo['reposet'],
                releasever=rh_repo['releasever'],
            )
            old_task_timeout = entity_mixins.TASK_TIMEOUT
            # Update timeout to 10 minutes to finish sync
            entity_mixins.TASK_TIMEOUT = 600
            # Sync repository
            entities.Repository(id=repo_id).sync()
            entity_mixins.TASK_TIMEOUT = old_task_timeout

        cv = entities.ContentView(organization=org).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            # Add ostree repository to selected CV
            self.content_views.add_remove_repos(
                cv.name,
                [rh_ah_repo['name']],
                repo_type='ostree'
            )
            # Add RH yum repository to selected CV
            self.content_views.add_remove_repos(
                cv.name,
                [rh_st_repo['name']],
                repo_type='yum'
            )
            self.content_views.publish(cv.name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            self.content_views.promote(cv.name, 'Version 1', lc_env.name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_promote_CV_with_custom_user_role_and_filters(self):
        """Publish and promote cv with user with custom role and filter

        @id: a07fe3df-8645-4a0c-8c56-3f8314ae4878

        @Assert: CV should be published and promoted successfully

        @CaseLevel: Integration
        """
        role = entities.Role().create()
        for perm in CUST_PERMS_LIST:
            permissions = entities.Permission(name=perm).search()
            entities.Filter(permission=permissions, role=role).create()
        username = gen_string('alpha')
        user_password = gen_string('alphanumeric')
        entities.User(
            login=username,
            role=[role],
            password=user_password,
            organization=[self.organization],
        ).create()
        repo_name = gen_string('alpha')
        env_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        with Session(self.browser, username, user_password) as session:
            # Create Life-cycle environment
            make_lifecycle_environment(session, name=env_name)
            # Creates a CV along with product and sync'ed repository
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            # Publish and promote CV to next environment
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
            self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
