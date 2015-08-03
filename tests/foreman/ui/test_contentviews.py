# -*- encoding: utf-8 -*-
"""Test class for Host/System Unification

Feature details: https://fedorahosted.org/katello/wiki/ContentViews

"""

from ddt import ddt
from fauxfactory import gen_string
from nailgun import client, entities
from robottelo.api import utils
from robottelo.common import manifests
from robottelo.common.constants import (
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
from robottelo.common.decorators import (
    data, run_only_on, skip_if_bug_open, stubbed)
from robottelo.common.helpers import (
    invalid_names_list, valid_data_list, get_server_credentials,
    read_data_file)
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_contentview, make_lifecycle_environment
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session
from robottelo.test import UITestCase


@run_only_on('sat')
@ddt
class TestContentViewsUI(UITestCase):
    """Implement tests for content view via UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        org_attrs = entities.Organization().create_json()
        cls.org_name = org_attrs['name']
        cls.org_id = org_attrs['id']

        super(TestContentViewsUI, cls).setUpClass()

    def setup_to_create_cv(self, repo_name=None, repo_url=None, repo_type=None,
                           rh_repo=None, org_id=None):
        """Create product/repo and sync it"""

        if not rh_repo:
            repo_name = repo_name or gen_string("alpha", 8)

            # Creates new custom product via API's
            product_attrs = entities.Product(
                organization=org_id or self.org_id
            ).create_json()

            # Creates new custom repository via API's
            repo_attrs = entities.Repository(
                name=repo_name,
                url=(repo_url or FAKE_1_YUM_REPO),
                content_type=(repo_type or REPO_TYPE['yum']),
                product=product_attrs['id'],
            ).create_json()
            repo_id = repo_attrs['id']
        elif rh_repo:
            # Clone the manifest and fetch it's path.
            manifest_path = manifests.clone()
            # Uploads the manifest and returns the result.
            entities.Organization(id=org_id).upload_manifest(
                path=manifest_path
            )
            # Enables the RedHat repo and fetches it's Id.
            repo_id = utils.enable_rhrepo_and_fetchid(
                basearch=rh_repo['basearch'],
                org_id=str(org_id),  # OrgId is passed as data in API hence str
                product=rh_repo['product'],
                repo=rh_repo['name'],
                reposet=rh_repo['reposet'],
                releasever=rh_repo['releasever'],
            )

        # Sync repository
        entities.Repository(id=repo_id).sync()

    @skip_if_bug_open('bugzilla', 1083086)
    @data(*valid_data_list())
    def test_cv_create(self, name):
        """@test: create content views (positive)

        @feature: Content Views

        @assert: content views are created

        @BZ: 1083086

        """

        with Session(self.browser) as session:
            make_contentview(session, org=self.org_name,
                             name=name)
            self.assertIsNotNone(
                self.content_views.search(name),
                'Failed to find content view %s from %s org' % (
                    name, self.org_name))

    @skip_if_bug_open('bugzilla', 1083086)
    @data(*invalid_names_list())
    def test_cv_create_negative(self, name):
        # variations (subject to change):
        # zero length, symbols, html, etc.
        """@test: create content views (negative)

        @feature: Content Views

        @assert: content views are not created; proper error thrown and
        system handles it gracefully

        @BZ: 1083086

        """

        with Session(self.browser) as session:
            make_contentview(session, org=self.org_name,
                             name=name)
            self.assertTrue(
                self.content_views.wait_until_element(
                    locators['contentviews.has_error']),
                'No validation error found for "%s" from %s org' % (
                    name, self.org_name))
            self.assertIsNone(self.content_views.search(name))

    def test_cv_end_2_end(self):
        """@test: create content view with yum repo, publish it
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

        repo_name = gen_string("alpha", 8)
        env_name = gen_string("alpha", 8)
        cv_name = gen_string("alpha", 8)
        publish_version = "Version 1"
        strategy, value = locators["content_env.select_name"]
        with Session(self.browser) as session:
            # Create Life-cycle environment
            make_lifecycle_environment(session, org=self.org_name,
                                       name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element
                                 ((strategy, value % env_name)))
            # Creates a CV along with product and sync'ed repository
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))
            # Publish and promote CV to next environment
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))
            self.content_views.promote(cv_name, publish_version, env_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    def test_associate_puppet_module(self):
        """@test: create content view with puppet repository

        @feature: Content Views

        @steps:
        1. Create Product/puppet repo and Sync it
        2. Create CV and add puppet modules from created repo

        @assert: content view is created, updated with puppet module

        """

        repo_url = FAKE_0_PUPPET_REPO
        cv_name = gen_string("alpha", 8)
        puppet_module = "httpd"
        module_ver = 'Latest'
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_url=repo_url,
                                    repo_type=REPO_TYPE['puppet'])
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_puppet_module(
                cv_name,
                puppet_module,
                filter_term=module_ver
            )
        # Workaround to fetch added puppet module name:
        # UI doesn't refresh and populate the added module name
        # until we logout and navigate again to puppet-module tab
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_content_views()
            module = self.content_views.fetch_puppet_module(cv_name,
                                                            puppet_module)
            self.assertIsNotNone(module)

    def test_remove_filter(self):
        """@test: create empty content views filter and remove it(positive)

        @feature: Content Views

        @assert: content views filter removed successfully

        """
        cv_name = gen_string("alpha", 8)
        filter_name = gen_string("alpha", 8)
        content_type = FILTER_CONTENT_TYPE['package']
        filter_type = FILTER_TYPE['exclude']
        with Session(self.browser) as session:
            make_contentview(session, org=self.org_name,
                             name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_filter(cv_name, filter_name,
                                          content_type, filter_type)
            self.content_views.remove_filter(cv_name, [filter_name])
            self.assertIsNone(self.content_views.search_filter
                              (cv_name, filter_name))

    def test_create_package_filter(self):
        """@test: create content views package filter(positive)

        @feature: Content Views

        @assert: content views filter created and selected packages
        can be added for inclusion/exclusion

        """

        cv_name = gen_string("alpha", 8)
        filter_name = gen_string("alpha", 8)
        repo_name = gen_string("alpha", 8)
        content_type = FILTER_CONTENT_TYPE['package']
        filter_type = FILTER_TYPE['include']
        package_names = ['cow', 'bird', 'crow', 'bear']
        version_types = ['Equal To', 'Greater Than', 'Less Than', 'Range']
        values = ['0.3', '0.5', '0.5', '4.1']
        max_values = [None, None, None, '4.6']
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.content_views.add_filter(cv_name, filter_name,
                                          content_type, filter_type)
            self.content_views.add_packages_to_filter(cv_name, filter_name,
                                                      package_names,
                                                      version_types,
                                                      values, max_values)

    def test_create_package_group_filter(self):
        """@test: create content views package group filter(positive)

        @feature: Content Views

        @assert: content views filter created and selected package groups
        can be added for inclusion/exclusion

        """
        cv_name = gen_string("alpha", 8)
        filter_name = gen_string("alpha", 8)
        repo_name = gen_string("alpha", 8)
        content_type = FILTER_CONTENT_TYPE['package group']
        filter_type = FILTER_TYPE['include']
        package_group = 'mammals'
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.content_views.add_filter(cv_name, filter_name,
                                          content_type, filter_type)
            self.content_views.add_remove_package_groups_to_filter(
                cv_name,
                filter_name,
                [package_group]
            )
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    def test_create_errata_filter(self):
        """@test: create content views errata filter(positive)

        @feature: Content Views

        @assert: content views filter created and selected errata-id
        can be added for inclusion/exclusion

        """

        cv_name = gen_string("alpha", 8)
        filter_name = gen_string("alpha", 8)
        repo_name = gen_string("alpha", 8)
        content_type = FILTER_CONTENT_TYPE['erratum by id']
        filter_type = FILTER_TYPE['include']
        errata_ids = ['RHEA-2012:0001', 'RHEA-2012:0004']
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.content_views.add_filter(cv_name, filter_name,
                                          content_type, filter_type)
            self.content_views.add_remove_errata_to_filter(cv_name,
                                                           filter_name,
                                                           errata_ids)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    @data(*valid_data_list())
    def test_positive_cv_update_name(self, new_name):
        """@test: Positive update content views - name.

        @feature: Content Views

        @assert: edited content view save is successful and info is
        updated

        """
        name = gen_string("alpha", 8)
        desc = gen_string("alpha", 15)
        with Session(self.browser) as session:
            make_contentview(session, org=self.org_name,
                             name=name, description=desc)
            self.assertIsNotNone(self.content_views.search(name))
            self.content_views.update(name, new_name)
            self.assertIsNotNone(self.content_views.search(new_name))

    @data(*invalid_names_list())
    def test_negative_cv_update_name(self, new_name):
        """@test: Negative update content views - name.

        @feature: Content Views

        @assert: Content View is not updated,  Appropriate error shown.

        """

        name = gen_string("alpha", 8)
        desc = gen_string("alpha", 15)
        with Session(self.browser) as session:
            make_contentview(session, org=self.org_name,
                             name=name, description=desc)
            self.assertIsNotNone(self.content_views.search(name))
            self.content_views.update(name, new_name)
            invalid = self.content_views.wait_until_element(common_locators
                                                            ["alert.error"])
            self.assertIsNotNone(invalid)
            self.assertIsNone(self.content_views.search(new_name))

    @data(*valid_data_list())
    def test_positive_cv_update_description(self, new_description):
        """@test: Positive update content views - description.

        @feature: Content Views

        @assert: edited content view save is successful and info is
        updated

        """

        name = gen_string("alpha", 8)
        desc = gen_string("alpha", 15)
        with Session(self.browser) as session:
            make_contentview(session, org=self.org_name,
                             name=name, description=desc)
            self.assertIsNotNone(self.content_views.search(name))
            self.content_views.update(name, new_description=new_description)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    def test_negative_cv_update_description(self):
        """@test: Negative update content views - description.

        @feature: Content Views

        @assert: Content View is not updated,  Appropriate error shown.

        """

        name = gen_string("alpha", 8)
        desc = gen_string("alpha", 15)
        new_description = gen_string("alpha", 256)
        with Session(self.browser) as session:
            make_contentview(session, org=self.org_name,
                             name=name, description=desc)
            self.assertIsNotNone(self.content_views.search(name))
            self.content_views.update(name, new_description=new_description)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.error"]))

    @stubbed()
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
        appears in any content view UI

        """

        name = gen_string('latin1', 8)

        with Session(self.browser) as session:
            make_contentview(session, org=self.org_name,
                             name=name)
            self.assertIsNotNone(
                self.content_views.search(name),
                'Failed to find content view %s from %s org' % (
                    name, self.org_name))
            self.content_views.delete(name, True)
            self.assertIsNone(
                self.content_views.search(name),
                'Content view %s from %s org was not deleted' % (
                    name, self.org_name))

    def test_cv_composite_create(self):
        # Note: puppet repos cannot/should not be used in this test
        # It shouldn't work - and that is tested in a different case.
        # Individual modules from a puppet repo, however, are a valid
        # variation.
        """@test: create a composite content views

        @feature: Content Views

        @setup: sync multiple content source/types (RH, custom, etc.)

        @assert: Composite content views are created

        """

        puppet_module = "httpd"
        module_ver = 'Latest'
        cv_name1 = gen_string("alpha", 8)
        cv_name2 = gen_string("alpha", 8)
        composite_name = gen_string("alpha", 8)
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': '7Server',
        }
        # Create new org to import manifest
        org_attrs = entities.Organization().create_json()
        org_id = org_attrs['id']
        org_name = org_attrs['name']
        with Session(self.browser) as session:
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org_id)
            # Create content-view
            make_contentview(session, org=org_name, name=cv_name2)
            self.assertIsNotNone(self.content_views.search(cv_name2))
            self.setup_to_create_cv(repo_url=FAKE_0_PUPPET_REPO,
                                    repo_type=REPO_TYPE['puppet'],
                                    org_id=org_id)
            # Create content-view
            make_contentview(session, org=org_name, name=cv_name1)
            self.assertIsNotNone(self.content_views.search(cv_name1))
            self.content_views.add_puppet_module(
                cv_name1,
                puppet_module,
                filter_term=module_ver
            )
        # Workaround to fetch added puppet module name:
        # UI doesn't refresh and populate the added module name
        # until we logout and navigate again to puppet-module tab
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org_name)
            session.nav.go_to_content_views()
            module = self.content_views.fetch_puppet_module(cv_name1,
                                                            puppet_module)
            self.assertIsNotNone(module)
            self.content_views.publish(cv_name1)
            self.content_views.add_remove_repos(cv_name2, [rh_repo['name']])
            self.content_views.publish(cv_name2)
            self.content_views.create(composite_name, is_composite=True)
        # UI doesn't populate the created content-view name to add it into
        # existing composite-view until we logout and navigate again to
        # puppet-module tab
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org_name)
            session.nav.go_to_content_views()
            self.content_views.add_remove_cv(composite_name,
                                             [cv_name1, cv_name2])
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    def test_associate_view_rh_1(self):
        """@test: associate Red Hat content in a view

        @feature: Content Views

        @setup: Sync RH content

        @assert: RH Content can be seen in a view

        """
        cv_name = gen_string("alpha", 8)
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': '7Server',
        }
        # Create new org to import manifest
        org_attrs = entities.Organization().create_json()
        org_id = org_attrs['id']
        with Session(self.browser) as session:
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org_id)
            # Create content-view
            make_contentview(session, org=org_attrs['name'], name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    @stubbed()
    def test_associate_view_rh_custom_spin(self):
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.
        """@test: associate Red Hat content in a view

        @feature: Content Views

        @setup: Sync RH content

        @steps: 1. Assure filter(s) applied to associated content

        @assert: Filtered RH content only is available/can be seen in a view

        @status: Manual

        """

    def test_associate_view_custom_content(self):
        """@test: associate custom content in a view

        @feature: Content Views

        @setup: Sync custom content

        @assert: Custom content can be seen in a view

        """

        cv_name = gen_string("alpha", 8)
        repo_name = gen_string("alpha", 8)
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    def test_cv_associate_puppet_repo_negative(self):
        # Again, individual modules should be ok.
        """@test: attempt to associate puppet repos within a composite
        content view

        @feature: Content Views

        @assert: User cannot create a composite content view
        that contains direct puppet repos.

        """
        composite_name = gen_string("alpha", 8)
        puppet_module = "httpd"
        module_ver = 'Latest'
        with Session(self.browser) as session:
            make_contentview(
                session,
                org=self.org_name,
                name=composite_name,
                is_composite=True
            )
            self.assertIsNotNone(self.content_views.search(composite_name))
            with self.assertRaises(UIError) as context:
                self.content_views.add_puppet_module(
                    composite_name, puppet_module, filter_term=module_ver)
                self.assertEqual(
                    context.exception.message,
                    'Could not find tab to add puppet_modules'
                )

    def test_cv_associate_components_composite_negative(self):
        """@test: attempt to associate components to a non-composite
        content view

        @feature: Content Views

        @assert: User cannot add components to the view

        """
        cv1_name = gen_string("alpha", 8)
        cv2_name = gen_string("alpha", 8)
        with Session(self.browser) as session:
            make_contentview(
                session, org=self.org_name, name=cv1_name)
            self.assertIsNotNone(self.content_views.search(cv1_name))
            make_contentview(
                session, org=self.org_name, name=cv2_name)
            self.assertIsNotNone(self.content_views.search(cv2_name))
            with self.assertRaises(UIError) as context:
                self.content_views.add_remove_cv(cv1_name, [cv2_name])
                self.assertEqual(
                    context.exception.message,
                    'Could not find ContentView tab, please make sure '
                    'selected view is composite'
                )

    @skip_if_bug_open('bugzilla', 1232270)
    def test_cv_associate_composite_dupe_repos_negative(self):
        """@test: attempt to associate the same repo multiple times within a
        content view

        @feature: Content Views

        @assert: User cannot add repos multiple times to the view

        """
        cv_name = gen_string("alpha", 8)
        repo_name = gen_string("alpha", 8)
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators["alert.success"]))
            with self.assertRaises(UIError) as context:
                self.content_views.add_remove_repos(cv_name, [repo_name])
                self.assertEqual(
                    context.exception.message,
                    'Could not find repo "{0}" to add into CV'
                    .format(repo_name)
                )

    @stubbed()
    def test_cv_associate_composite_dupe_modules_negative(self):
        """@test: attempt to associate duplicate puppet module(s) within a
        content view

        @feature: Content Views

        @assert: User cannot add modules multiple times to the view

        @status: Manual

        """

    def test_cv_promote_rh_1(self):
        """@test: attempt to promote a content view containing RH content

        @feature: Content Views

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted

        """
        cv_name = gen_string("alpha", 8)
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': '7Server',
        }
        env_name = gen_string("alpha", 8)
        publish_version = "Version 1"
        strategy, value = locators["content_env.select_name"]
        # Create new org to import manifest
        org_attrs = entities.Organization().create_json()
        org_id = org_attrs['id']
        org_name = org_attrs['name']
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=org_name,
                                       name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element
                                 ((strategy, value % env_name)))
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org_id)
            # Create content-view
            make_contentview(session, org=org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))
            self.content_views.promote(cv_name, publish_version, env_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    @stubbed()
    def test_cv_promote_rh_custom_spin(self):
        """@test: attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.

        @feature: Content Views

        @setup: Multiple environments for an org; RH content synced

        @assert: Content view can be promoted

        @status: Manual

        """

    def test_cv_promote_custom_content(self):
        """@test: attempt to promote a content view containing custom content

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be promoted

        """
        repo_name = gen_string("alpha", 8)
        env_name = gen_string("alpha", 8)
        publish_version = "Version 1"
        cv_name = gen_string("alpha", 8)
        strategy, value = locators["content_env.select_name"]
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element
                                 ((strategy, value % env_name)))
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))
            self.content_views.promote(cv_name, publish_version, env_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    @stubbed()
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

        @status: Manual

        """

    @stubbed()
    def test_cv_promote_default_negative(self):
        """@test: attempt to promote a the default content views

        @feature: Content Views

        @assert: Default content views cannot be promoted

        @status: Manual

        """

    def test_cv_publish_rh_1(self):
        """@test: attempt to publish a content view containing RH content

        @feature: Content Views

        @setup: RH content synced

        @assert: Content view can be published

        """
        cv_name = gen_string("alpha", 8)
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': '7Server',
        }
        # Create new org to import manifest
        org_attrs = entities.Organization().create_json()
        org_id = org_attrs['id']
        with Session(self.browser) as session:
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org_id)
            # Create content-view
            make_contentview(session, org=org_attrs['name'], name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    @stubbed()
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

        repo_name = gen_string("alpha", 8)
        env_name = gen_string("alpha", 8)
        cv_name = gen_string("alpha", 8)
        strategy, value = locators["content_env.select_name"]
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element
                                 ((strategy, value % env_name)))
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators["alert.success"]))

    @stubbed()
    def test_cv_publish_composite(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """@test: attempt to publish  a content view containing custom content

        @feature: Content Views

        @setup: Multiple environments for an org; custom content synced

        @assert: Content view can be published

        @status: Manual

        """

    @stubbed()
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

        @status: Manual

        """

    @stubbed()
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

        @status: Manual

        """

    def test_cv_clone_within_same_env(self):
        # Dev note: "not implemented yet"
        """@test: attempt to create new content view based on existing
        view within environment

        @feature: Content Views

        @assert: Content view can be published

        """
        repo_name = gen_string('alpha', 8)
        cv_name = gen_string('alpha', 8)
        copy_cv_name = gen_string('alpha', 8)
        with Session(self.browser) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.org_name, name=cv_name)
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
    def test_cv_clone_within_diff_env(self):
        # Dev note: "not implemented yet"
        """@test: attempt to create new content view based on existing
        view, inside a different environment

        @feature: Content Views

        @assert: Content view can be published

        @status: Manual

        """

    @stubbed()
    def test_cv_refresh_errata_to_new_view_in_same_env(self):
        """@test: attempt to refresh errata in a new view, based on
        an existing view, from within the same  environment

        @feature: Content Views

        @assert: Content view can be published

        @status: Manual

        """

    @stubbed()
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
        """@test: attempt to  subscribe systems to content view(s)

        @feature: Content Views

        @assert: Systems can be subscribed to content view(s)

        @status: Manual

        """

    @stubbed()
    def test_cv_dynflow_restart_promote(self):
        """@test: attempt to restart a promotion

        @feature: Content Views

        @steps:
        1. (Somehow) cause a CV promotion to fail.  Not exactly sure how yet.
        2. Via Dynflow, restart promotion

        @assert: Promotion is restarted.

        @status: Manual

        """

    @stubbed()
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

    @stubbed()
    def test_cv_roles_admin_user(self):
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

        @setup: create a user with the Content View admin role

        @assert: User with admin role for content view can perform all
        Variations above

        @status: Manual

        """

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
    def test_cv_roles_admin_user_negative(self):
        # Note:
        # Obviously all of this stuff should work with 'admin' user
        # but these tests require creating a user withOUT admin permissions
        # for Content Views
        # Dev note: none of this stuff is integrated with foreman rbac yet
        # As such, all variations in here subject to change.
        # Variations:
        #  * Read, Modify, Delete, Promote Publish, Subscribe
        """@test: attempt to view content views

        @feature: Content Views

        @setup: create a user with the Content View admin role

        @assert: User withOUT admin role for content view canNOT perform any
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

    def test_delete_version_default(self):
        """@Test: Delete a content-view version associated to 'Library'

        @Assert: Deletion fails

        @Feature: ContentViewVersion

        """
        key_content = read_data_file(ZOO_CUSTOM_GPG_KEY)
        org = entities.Organization().create()
        gpgkey_id = entities.GPGKey(
            content=key_content,
            organization=org.id
        ).create_json()['id']
        # Creates new product without selecting GPGkey
        product_id = entities.Product(
            organization=org.id
        ).create_json()['id']
        # Creates new repository with GPGKey
        repo = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=product_id,
            gpg_key=gpgkey_id,
        ).create()
        # sync repository
        repo.sync()
        # Create content view
        cv = entities.ContentView(
            organization=org.id
        ).create()
        # Associate repository to new content view
        client.put(
            cv.path(),
            {u'repository_ids': [repo.id]},
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()
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

    def test_delete_version_non_default(self):
        """@Test: Delete a content-view version associated to non-default
        environment

        @Assert: Deletion fails

        @Feature: ContentViewVersion

        """
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        repo = entities.Repository(product=product).create()
        repo.sync()
        cv = entities.ContentView(
            name=gen_string('alpha'),
            organization=org,
        ).create()
        cv.set_repository_ids([repo.id])
        cv.publish()

        cv_info = cv.read_json()['versions'][0]
        version = 'Version {0}'.format(cv_info['version'])
        cvv = entities.ContentViewVersion(id=cv_info['id'])
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        cvv.promote(lc_env.id)

        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            session.nav.go_to_content_views()
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    def test_delete_version_with_ak(self):
        """@Test: Delete a content-view version that had associated activation
        key to it

        @Assert: Deletion fails

        @Feature: ContentViewVersion

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
        cvv.promote(lc_env.id)

        ak = entities.ActivationKey(
            name=gen_string('alphanumeric'),
            environment=lc_env.id,
            organization=org,
            content_view=cv,
        ).create_json()

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
                ak['name'],
                content_view=DEFAULT_CV,
                env=ENVIRONMENT,
            )
            session.nav.go_to_dashboard()
            session.nav.go_to_content_views()
            self.content_views.delete_version(cv.name, version)
            self.content_views.validate_version_deleted(cv.name, version)
