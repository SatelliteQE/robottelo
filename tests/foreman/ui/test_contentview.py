# -*- encoding: utf-8 -*-
"""Test class for Host/System Unification

Feature details: https://fedorahosted.org/katello/wiki/ContentViews

"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.api.utils import enable_rhrepo_and_fetchid, upload_manifest
from robottelo import manifests
from robottelo.constants import (
    DEFAULT_CV,
    ENVIRONMENT,
    FAKE_0_PUPPET_REPO,
    FAKE_1_YUM_REPO,
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
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
)
from robottelo.helpers import read_data_file
from robottelo.ui.base import UIError
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
                           rh_repo=None, org_id=None):
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
            ).create().id
        elif rh_repo:
            # Uploads the manifest and returns the result.
            with manifests.clone() as manifest:
                upload_manifest(org_id, manifest.content)
            # Enables the RedHat repo and fetches it's Id.
            repo_id = enable_rhrepo_and_fetchid(
                basearch=rh_repo['basearch'],
                org_id=str(org_id),  # OrgId is passed as data in API hence str
                product=rh_repo['product'],
                repo=rh_repo['name'],
                reposet=rh_repo['reposet'],
                releasever=rh_repo['releasever'],
            )
        # Sync repository
        entities.Repository(id=repo_id).sync()

    @run_only_on('sat')
    @tier1
    def test_positive_create_wth_name(self):
        """Create content views using different names

        @feature: Content Views

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

        @feature: Content Views

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

        @feature: Content Views

        @steps:
        1. Create Product/repo and Sync it
        2. Create CV and add created repo in step1
        3. Publish and promote it to 'Library'
        4. Promote it to next environment

        @assert: content view is created, updated with repo publish and
        promoted to next selected env
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
                common_locators['alert.success']))
            # Publish and promote CV to next environment
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success']))
            self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success']))

    @skip_if_bug_open('bugzilla', 1297308)
    @run_only_on('sat')
    @tier2
    def test_positive_add_puppet_module(self):
        """create content view with puppet repository

        @feature: Content Views

        @steps:
        1. Create Product/puppet repo and Sync it
        2. Create CV and add puppet modules from created repo

        @assert: content view is created, updated with puppet module
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

        @feature: Content Views

        @assert: content views filter removed successfully
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

        @feature: Content Views

        @assert: content views filter created and selected packages
        can be added for inclusion/exclusion
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

        @feature: Content Views

        @assert: content views filter created and selected package groups
        can be added for inclusion/exclusion
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
                common_locators['alert.success']))

    @run_only_on('sat')
    @tier2
    def test_positive_add_errata_filter(self):
        """add errata to content views filter

        @feature: Content Views

        @assert: content views filter created and selected errata-id
        can be added for inclusion/exclusion
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
                common_locators['alert.success']))

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update content views name to valid one.

        @feature: Content Views

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

        @feature: Content Views

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
                        common_locators['alert.error']))
                    self.assertIsNone(self.content_views.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_description(self):
        """Update content views description to valid one.

        @feature: Content Views

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
                        common_locators['alert.success']))

    @run_only_on('sat')
    @tier1
    def test_negative_update_description(self):
        """Try to update content views description to invalid one.

        @feature: Content Views

        @assert: Content View is not updated. Appropriate error shown.
        """
        name = gen_string('alpha', 8)
        desc = gen_string('alpha', 15)
        new_description = gen_string('alpha', 256)
        with Session(self.browser) as session:
            make_contentview(session, org=self.organization.name,
                             name=name, description=desc)
            self.assertIsNotNone(self.content_views.search(name))
            self.content_views.update(name, new_description=new_description)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.error']))

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_edit_rh_custom_spin(self):
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.
        """edit content views for a custom rh spin.  For example,

        @feature: Content Views
        modify a filter

        @assert: edited content view save is successful and info is
        updated

        @status: Manual

        """

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete content views

        @feature: Content Views

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

    @skip_if_bug_open('bugzilla', 1297308)
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_create_composite(self):
        # Note: puppet repos cannot/should not be used in this test
        # It shouldn't work - and that is tested in a different case.
        # Individual modules from a puppet repo, however, are a valid
        # variation.
        """create a composite content views

        @feature: Content Views

        @setup: sync multiple content source/types (RH, custom, etc.)

        @assert: Composite content views are created
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
            session.nav.go_to_content_views()
            module = self.content_views.fetch_puppet_module(
                cv_name1, puppet_module)
            self.assertIsNotNone(module)
            self.content_views.publish(cv_name1)
            self.content_views.add_remove_repos(cv_name2, [rh_repo['name']])
            self.content_views.publish(cv_name2)
            self.content_views.create(composite_name, is_composite=True)
            session.nav.go_to_select_org(org.name)
            session.nav.go_to_content_views()
            self.content_views.add_remove_cv(
                composite_name, [cv_name1, cv_name2])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_add_rh_content(self):
        """Add Red Hat content to a content view

        @feature: Content Views

        @setup: Sync RH content

        @assert: RH Content can be seen in a view
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
                common_locators['alert.success']))

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

        @feature: Content Views

        @setup: Sync RH content

        @steps: 1. Assure filter(s) applied to associated content

        @assert: Filtered RH content only is available/can be seen in a view

        @status: Manual

        """

    @run_only_on('sat')
    @tier2
    def test_positive_add_custom_content(self):
        """associate custom content in a view

        @feature: Content Views

        @setup: Sync custom content

        @assert: Custom content can be seen in a view
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
                common_locators['alert.success']))

    @skip_if_bug_open('bugzilla', 1297308)
    @run_only_on('sat')
    @tier2
    def test_negative_add_puppet_repo_to_composite(self):
        # Again, individual modules should be ok.
        """attempt to associate puppet repos within a composite
        content view

        @feature: Content Views

        @assert: User cannot create a composite content view
        that contains direct puppet repos.

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

        @feature: Content Views

        @assert: User cannot add components to the view
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
            with self.assertRaises(UIError) as context:
                self.content_views.add_remove_cv(cv1_name, [cv2_name])
                self.assertEqual(
                    context.exception.message,
                    'Could not find ContentView tab, please make sure '
                    'selected view is composite'
                )

    @skip_if_bug_open('bugzilla', 1232270)
    @run_only_on('sat')
    @tier2
    def test_negative_add_dupe_repos(self):
        """attempt to associate the same repo multiple times within a
        content view

        @feature: Content Views

        @assert: User cannot add repos multiple times to the view
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
                common_locators['alert.success']))
            with self.assertRaises(UIError) as context:
                self.content_views.add_remove_repos(cv_name, [repo_name])
                self.assertEqual(
                    context.exception.message,
                    'Could not find repo "{0}" to add into CV'
                    .format(repo_name)
                )

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_negative_add_dupe_modules(self):
        """attempt to associate duplicate puppet module(s) within a
        content view

        @feature: Content Views

        @assert: User cannot add modules multiple times to the view

        @status: Manual

        """

    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_promote_with_rh_content(self):
        """attempt to promote a content view containing RH content

        @feature: Content Views

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted
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
                common_locators['alert.success']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))
            self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @stubbed()
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_promote_with_rh_custom_spin(self):
        """attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.

        @feature: Content Views

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted

        @status: Manual

        """

    @run_only_on('sat')
    @tier2
    def test_positive_promote_with_custom_content(self):
        """attempt to promote a content view containing custom content

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be promoted
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
                common_locators['alert.success']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))
            self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

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

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @steps: create a composite view containing multiple content types

        @assert: Content view can be promoted

        @status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_negative_promote_default(self):
        """attempt to promote a the default content views

        @feature: Content Views

        @assert: Default content views cannot be promoted

        @status: Manual

        """

    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_publish_with_rh_content(self):
        """attempt to publish a content view containing RH content

        @feature: Content Views

        @setup: RH content synced

        @assert: Content view can be published
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
                common_locators['alert.success']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @stubbed()
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_publish_with_rh_custom_spin(self):
        """attempt to publish  a content view containing a custom RH
        spin - i.e., contains filters.

        @feature: Content Views

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be published

        @status: Manual

        """

    @run_only_on('sat')
    @tier2
    def test_positive_publish_with_custom_content(self):
        """attempt to publish a content view containing custom content

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be published
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
                common_locators['alert.success']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

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

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be published

        @status: Manual

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

        @feature: Content Views

        @setup: Multiple environments for an org; multiple versions
        of a content view created/published

        @steps:
        1. publish a view to an environment noting the CV version
        2. edit and republish a new version of a CV

        @assert: Content view version is updated intarget environment.

        @status: Manual

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

        @feature: Content Views

        @setup: Multiple environments for an org; multiple versions
        of a content view created/published

        @steps:
        1. publish a view to an environment
        2. edit and republish a new version of a CV

        @assert: Content view version is updated in source environment.

        @status: Manual

        """

    @run_only_on('sat')
    @tier2
    def test_positive_clone_within_same_env(self):
        """attempt to create new content view based on existing
        view within environment

        @feature: Content Views

        @assert: Content view can be cloned
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
                    common_locators['alert.success'])
            )
            # Publish the CV
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success'])
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

        @feature: Content Views

        @assert: Content view can be published

        @status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_refresh_errata_to_new_view_in_same_env(self):
        """attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment

        @feature: Content Views

        @assert: Content view can be published

        @status: Manual

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

        @feature: Content Views

        @assert: Systems can be subscribed to content view(s)

        @status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_restart_promote_via_dynflow(self):
        """attempt to restart a promotion

        @feature: Content Views

        @steps:
        1. (Somehow) cause a CV promotion to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart promotion

        @assert: Promotion is restarted.

        @status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_restart_publish_via_dynflow(self):
        """attempt to restart a publish

        @feature: Content Views

        @steps:
        1. (Somehow) cause a CV publish  to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart publish

        @assert: Publish is restarted.

        @status: Manual

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

        @feature: Content Views

        @setup: create a user with the Content View admin role

        @assert: User with admin role for content view can perform all
        Variations above

        @status: Manual

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

        @feature: Content Views

        @setup: create a user with the Content View read-only role

        @assert: User with read-only role for content view can perform all
        Variations above

        @status: Manual

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

        @feature: Content Views

        @setup: create a user with the Content View admin role

        @assert: User withOUT admin role for content view canNOT perform any
        Variations above

        @status: Manual

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

        @feature: Content Views

        @setup: create a user withOUT the Content View read-only role

        @assert: User withOUT read-only role for content view can perform all
        Variations above

        @status: Manual

        """

    @run_only_on('sat')
    @tier2
    def test_positive_delete_default_version(self):
        """Delete a content-view version associated to 'Library'

        @Feature: ContentViewVersion

        @Assert: Deletion was performed successfully
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
        cv_info = entities.ContentView(id=cv.id).read_json()
        self.assertEqual(len(cv_info['versions']), 1)
        # API returns version like '1.0'
        version_num = cv_info['versions'][0]['version']
        # WebUI displays version like 'Version 1.0'
        version = 'Version {0}'.format(version_num)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            session.nav.go_to_content_views()
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @tier2
    def test_positive_delete_non_default_version(self):
        """Delete a content-view version associated to non-default
        environment

        @Feature: ContentViewVersion

        @Assert: Deletion was performed successfully
        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product).create()
        repo.sync()
        cv = entities.ContentView(
            name=gen_string('alpha'),
            organization=org,
        ).create()
        cv.repository = [repo]
        cv.update(['repository'])
        cv.publish()

        cv_info = cv.read_json()['versions'][0]
        version = 'Version {0}'.format(cv_info['version'])
        cvv = entities.ContentViewVersion(id=cv_info['id'])
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        cvv.promote(data={u'environment_id': lc_env.id})

        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            session.nav.go_to_content_views()
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @tier2
    def test_positive_delete_version_with_ak(self):
        """Delete a content-view version that had associated activation
        key to it

        @Feature: ContentViewVersion

        @Assert: Deletion was performed successfully
        """
        org = entities.Organization().create()
        cv = entities.ContentView(
            name=gen_string('alpha'),
            organization=org,
        ).create()
        cv.publish()

        cv_info = cv.read_json()['versions'][0]
        version = 'Version {0}'.format(cv_info['version'])
        cvv = entities.ContentViewVersion(id=cv_info['id'])
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
            # That call should be made to remove any reference from DOM to
            # search field on the page and prevent StaleElementException in
            # our search functionality as our code does not differentiate
            # search field locator for ActivationKey or ContentView or any
            # other possible entities in the application.
            session.nav.go_to_dashboard()
            session.nav.go_to_activation_keys()
            self.activationkey.update(
                ak.name,
                content_view=DEFAULT_CV,
                env=ENVIRONMENT,
            )
            session.nav.go_to_dashboard()
            session.nav.go_to_content_views()
            self.content_views.delete_version(cv.name, version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_custom_ostree(self):
        """Create a CV with custom ostree contents

        @Feature: Content View

        @Assert: CV should be created successfully with custom ostree contents

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_add_rh_ostree(self):
        """Create a CV with RH ostree contents

        @Feature: Content View

        @Assert: CV should be created successfully with RH ostree contents

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_custom_ostree(self):
        """Create a CV with custom ostree contents and remove the
        contents.

        @Feature: Content View

        @Assert: Content should be removed and CV should be updated
        successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_rh_ostree(self):
        """Create a CV with RH ostree contents and remove the
        contents.

        @Feature: Content View

        @Assert: Content should be removed and CV should be updated
        successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_with_custom_ostree_other_contents(self):
        """Create a CV with custom ostree contents and other custom yum, puppet
        repos.

        @Feature: Content View

        @Assert: CV should be created successfully with all custom contents

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_with_rh_ostree_other_contents(self):
        """Create a CV with RH ostree contents and other RH yum repos.

        @Feature: Content View

        @Assert: CV should be created successfully with all custom contents

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_publish_with_custom_ostree(self):
        """Create a CV with custom ostree contents and publish it.

        @Feature: Content View

        @Assert: CV should be published with OStree contents

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_published_custom_ostree_version(self):
        """Remove published custom ostree contents version from selected CV.

        @Feature: Content View

        @Assert: Published version with OStree contents should be removed
        successfully.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_promote_with_custom_ostree(self):
        """Create a CV with custom ostree contents and publish, promote it
        to next environment.

        @Feature: Content View

        @Assert: CV should be promoted with custom OStree contents

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_promoted_custom_ostree_contents(self):
        """Remove promoted custom ostree contents from selected environment of
        CV.

        @Feature: Content View

        @Assert: Promoted custom OStree contents should be removed successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_publish_promote_with_custom_ostree_and_other(self):
        """Create a CV with ostree as well as yum and puppet type contents and
        publish and promote them to next environment.

        @Feature: Content View

        @Assert: CV should be published and promoted with custom OStree and all
        other contents

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_published_version_of_mixed_contents(self):
        """Remove mixed(ostree, yum, puppet, docker) published content version
        from selected CV.

        @Feature: Content View

        @Assert: Published version with mixed(ostree, yum, puppet, docker)
        contents should be removed successfully.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_publish_with_rh_ostree(self):
        """Create a CV with RH ostree contents and publish it.

        @Feature: Content View

        @Assert: CV should be published with RH OStree contents

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_published_rh_ostree_version(self):
        """Remove published rh ostree contents version from selected CV.

        @Feature: Content View

        @Assert: Published version with RH OStree contents should be removed
        successfully.

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_promote_with_rh_ostree(self):
        """Create a CV with RH ostree contents and publish, promote it
        to next environment.

        @Feature: Content View

        @Assert: CV should be promoted with RH OStree contents

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_remove_promoted_rh_ostree_contents(self):
        """Remove promoted rh ostree contents from selected environment of CV.

        @Feature: Content View

        @Assert: Promoted rh OStree contents should be removed successfully

        @Status: Manual
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_publish_promote_with_rh_ostree_and_other(self):
        """Create a CV with rh ostree as well as rh yum and puppet type contents and
        publish, promote them to next environment.

        @Feature: Content View

        @Assert: CV should be published and promoted with rh ostree and all
        other contents

        @Status: Manual
        """
