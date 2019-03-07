# -*- encoding: utf-8 -*-
"""Test class for Host/System Unification

Feature details: https://fedorahosted.org/katello/wiki/ContentViews


:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import date, timedelta
from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import (
    call_entity_method_with_timeout,
    enable_rhrepo_and_fetchid,
    upload_manifest,
)
from robottelo.constants import (
    DISTRO_RHEL7,
    DOCKER_REGISTRY_HUB,
    DOCKER_UPSTREAM_NAME,
    ENVIRONMENT,
    FAKE_0_PUPPET_REPO,
    FAKE_0_PUPPET_MODULE,
    FAKE_0_YUM_REPO,
    FAKE_1_YUM_REPO,
    FAKE_9_YUM_REPO,
    FAKE_9_YUM_SECURITY_ERRATUM_COUNT,
    FILTER_CONTENT_TYPE,
    FILTER_ERRATA_TYPE,
    FILTER_ERRATA_DATE,
    FILTER_TYPE,
    REPO_TYPE,
)
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.base import UINoSuchElementError
from robottelo.ui.factory import (
    make_contentview,
    make_lifecycle_environment,
)
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.locators.menu import menu_locators
from robottelo.ui.locators.tab import tab_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


class ContentViewTestCase(UITestCase):
    """Implement tests for content view via UI"""

    @classmethod
    def setUpClass(cls):
        super(ContentViewTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    # pylint: disable=too-many-arguments
    def setup_to_create_cv(self, repo_name=None, repo_url=None, repo_type=None,
                           repo_unprotected=True, rh_repo=None, org_id=None,
                           docker_upstream_name=None):
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
                docker_upstream_name=docker_upstream_name,
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

        # Sync repository with custom timeout
        call_entity_method_with_timeout(
            entities.Repository(id=repo_id).sync, timeout=1500)
        return repo_id

    def _get_cv_version_environments(self, cv_version):
        """Return the list of environments promoted to the version of content
        view. The content view web page must be already opened.

        :param cv_version: The version of the current opened content view
        :type cv_version: str
        :rtype: list[str]
        """
        environment_elements = self.content_views.find_elements(
            locators.contentviews.version_environments % cv_version)
        return [env_element.text for env_element in environment_elements]

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create content views using different names

        :id: 804e51d7-f025-4ec2-a247-834afd351e89

        :expectedresults: Content views are created

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: 974f2adc-b7da-4a8c-a8b5-d231b6bda1ce

        :expectedresults: content views are not created; proper error thrown
            and system handles it gracefully

        :CaseImportance: Critical
        """
        with Session(self) as session:
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
    def test_positive_remove_package_from_exclusion_filter(self):
        """Remove package from content view exclusion filter

        :id: 2f0adc16-2305-4adf-8582-82e6110fa385

        :expectedresults: Package was successfully removed from content view
            filter and is present in next published content view version

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        package_name = 'cow'
        self.setup_to_create_cv(repo_name=repo_name)
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['package'],
                FILTER_TYPE['exclude'],
            )
            self.content_views.add_packages_to_filter(
                cv_name,
                filter_name,
                [package_name],
                ['Equal To'],
                ['2.2-3'],
                [None],
            )
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            self.assertIsNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    package_name,
                )
            )
            self.content_views.remove_packages_from_filter(
                cv_name,
                filter_name,
                [package_name],
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 2.0'))
            self.assertIsNotNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 2.0',
                    package_name,
                )
            )

    @skip_if_bug_open('bugzilla', 1478132)
    @tier1
    def test_positive_create_date_filter_rule_without_type(self):
        """Create content view erratum filter rule with start/end date and
        without type specified via API and make sure it's accessible via UI

        :id: 5a5cd6e7-8711-47c2-878d-4c0a18bf3b0e

        :BZ: 1386688

        :CaseImportance: Critical

        :expectedresults: filter rule is accessible via UI, type is set to all
            possible errata types and all the rest fields are correctly
            populated
        """
        start_date = date.today().strftime('%Y-%m-%d')
        end_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        # default date type on UI is 'updated', so we'll use different one
        date_type = FILTER_ERRATA_DATE['issued']
        content_view = entities.ContentView(
            organization=self.organization).create()
        cvf = entities.ErratumContentViewFilter(
            content_view=content_view).create()
        cvfr = entities.ContentViewFilterRule(
            end_date=end_date,
            content_view_filter=cvf,
            date_type=date_type,
            start_date=start_date,
        ).create()
        self.assertEqual(set(cvfr.types), set(FILTER_ERRATA_TYPE.values()))
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            result = self.content_views.fetch_erratum_date_range_filter_values(
                content_view.name, cvf.name)
            self.assertEqual(
                set(result['types']), set(FILTER_ERRATA_TYPE.values()))
            self.assertEqual(result['date_type'], date_type)
            self.assertEqual(result['start_date'], start_date)
            self.assertEqual(result['end_date'], end_date)

    @tier2
    def test_positive_add_all_security_errata_by_date_range_filter(self):
        """Create erratum date range filter to include only security errata and
        publish new content view version

        :id: c8f4453b-e654-4e8d-9156-5443bfb92f23

        :CaseImportance: High

        :expectedresults: all security errata is present in content view
            version
        """
        filter_name = gen_string('alphanumeric')
        start_date = '2010-01-01'
        end_date = date.today().strftime('%Y-%m-%d')
        content_view = entities.ContentView(
            organization=self.organization).create()
        product = entities.Product(organization=self.organization).create()
        repo = entities.Repository(
            product=product,
            url=FAKE_9_YUM_REPO,
        ).create()
        repo.sync()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.content_views.add_remove_repos(
                content_view.name, [repo.name])
            session.content_views.add_filter(
                content_view.name,
                filter_name,
                FILTER_CONTENT_TYPE['erratum by date and type'],
                FILTER_TYPE['include'],
            )
            session.content_views.edit_erratum_date_range_filter(
                content_view.name,
                filter_name,
                errata_types=['security'],
                date_type=FILTER_ERRATA_DATE['issued'],
                start_date=start_date,
                end_date=end_date,
                open_filter=False,
            )
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            session.content_views.publish(content_view.name)
            self.assertIsNotNone(
                self.content_views.version_search(
                    content_view.name, 'Version 1.0'
                )
            )
            result = session.content_views.fetch_version_errata(
                content_view.name, 'Version 1.0')
            self.assertEqual(len(result), FAKE_9_YUM_SECURITY_ERRATUM_COUNT)
            self.assertTrue(
                all(
                    errata[2] == FILTER_ERRATA_TYPE['security']
                    for errata in result
                )
            )

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update content views name to valid one.

        :id: 7d8eb36a-536e-49dc-9eb4-a5885ec77819

        :expectedresults: Content view is updated successfully and has proper
            name

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 211c319f-802a-4407-9c16-205a82d4afca

        :expectedresults: Content View is not updated. Appropriate error shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
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

        :id: f5e46a3b-c317-4575-9c66-ef1da1926f66

        :expectedresults: Content view is updated successfully and has proper
            description

        :CaseImportance: Critical
        """
        name = gen_string('alpha', 8)
        desc = gen_string('alpha', 15)
        with Session(self) as session:
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
                    self.content_views.search_and_click(name)
                    self.content_views.click(
                        tab_locators['contentviews.tab_details'])
                    self.assertEqual(
                        self.content_views.wait_until_element(
                            locators['contentviews.fetch_description']).text,
                        new_desc
                    )

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete content views

        :id: bcea6ef0-bc25-4cc7-9c0c-3591bb8810e5

        :expectedresults: Content view can be deleted and no longer appears in
            UI

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

    @run_only_on('sat')
    @upgrade
    @tier2
    def test_positive_subscribe_system_with_puppet_modules(self):
        """Attempt to subscribe a host to content view with puppet modules

        :id: c57fbdca-31e8-43f1-844d-b82b13c0c4de

        :setup: content view with puppet module

        :expectedresults: Systems can be subscribed to content view(s)

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        repo_url = FAKE_0_PUPPET_REPO
        module_name = 'httpd'
        # create an organization
        org = entities.Organization().create()
        # create a lifecycle environment
        env = entities.LifecycleEnvironment(organization=org).create()
        # create repositories
        self.setup_to_create_cv(
            org_id=org.id,
            repo_url=repo_url,
            repo_name=repo_name,
            repo_type=REPO_TYPE['puppet']
        )
        with Session(self) as session:
            # create content view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add puppet module to content view
            self.content_views.add_puppet_module(
                cv_name, module_name, filter_term='Latest')
            self.assertIsNotNone(
                self.content_views.fetch_puppet_module(
                    cv_name, module_name)
            )
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            # promote the content view
            status = self.content_views.promote(cv_name, version, env.name)
            self.assertIn('Promoted to {}'.format(env.name), status)
            self.assertIn(env.name, self._get_cv_version_environments(version))
            # create an activation key
            content_view = entities.ContentView(
                organization=org, name=cv_name).search()[0].read()
            activation_key = entities.ActivationKey(
                organization=org,
                environment=env,
                content_view=content_view
            ).create()
            with VirtualMachine(distro=DISTRO_RHEL7) as host_client:
                host_client.install_katello_ca()
                host_client.register_contenthost(
                    org.label, activation_key.name)
                self.assertTrue(host_client.subscribed)
                # assert the host_client exists in content hosts page
                self.assertIsNotNone(
                    self.contenthost.search(host_client.hostname))

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_restart_promote_via_dynflow(self):
        """attempt to restart a promotion

        :id: c7f4e673-5164-417f-a072-1cc51d176780

        :steps:
            1. (Somehow) cause a CV promotion to fail.  Not exactly sure how
                yet.
            2. Via Dynflow, restart promotion

        :expectedresults: Promotion is restarted.

        :caseautomation: notautomated


        :CaseLevel: Integration
        """

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_restart_publish_via_dynflow(self):
        """attempt to restart a publish

        :id: d7a1204f-5d7c-4978-bb78-f366786d006a

        :steps:
            1. (Somehow) cause a CV publish  to fail.  Not exactly sure how
                yet.
            2. Via Dynflow, restart publish

        :expectedresults: Publish is restarted.

        :caseautomation: notautomated


        :CaseLevel: Integration
        """

    # ROLES TESTING

    @run_only_on('sat')
    @tier2
    def test_positive_readonly_user_actions(self):
        """Attempt to view content views

        :id: ebdc37ed-7887-4f64-944c-f2f92c58a206

        :setup:

            1. create a user with the Content View read-only role
            2. create content view
            3. add a custom repository to content view

        :expectedresults: User with read-only role for content view can view
            the repository in the content view

        :CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        user_login = gen_string('alpha')
        user_password = gen_string('alphanumeric')
        role_name = gen_string('alpha')
        # create a role with content views read only permissions
        role = entities.Role(name=role_name).create()
        entities.Filter(
            organization=[self.organization],
            permission=entities.Permission(
                resource_type='Katello::ContentView').search(
                filters={'name': 'view_content_views'}),
            role=role,
            search=None
        ).create()
        # create read only products permissions and assign it to our role
        entities.Filter(
            organization=[self.organization],
            permission=entities.Permission(
                resource_type='Katello::Product').search(
                filters={'name': 'view_products'}),
            role=role,
            search=None
        ).create()
        # create a user and assign the above created role
        entities.User(
            default_organization=self.organization,
            organization=[self.organization],
            role=[role],
            login=user_login,
            password=user_password
        ).create()
        # create a repository
        self.setup_to_create_cv(repo_name=repo_name)
        # create a content view with the main admin account
        with Session(self) as session:
            # create the first content view
            make_contentview(
                session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add repository to the created content view
            self.content_views.add_remove_repos(cv_name, [repo_name])
        # login as the user created above
        with Session(self, user_login, user_password) as session:
            # to ensure that the created user has only the assigned
            # permissions, check that hosts menu tab does not exist
            self.assertIsNone(
                self.content_views.wait_until_element(
                    menu_locators.menu.hosts, timeout=5)
            )
            # assert that the created user is not a global admin user
            # check administer->users page
            with self.assertRaises(UINoSuchElementError) as context:
                session.nav.go_to_users()
            # assert that the administer->users menu element was not accessible
            _, locator = menu_locators.menu.users
            self.assertIn(locator, str(context.exception))
            # assert the user can access content views via the menu
            try:
                session.nav.go_to_content_views()
            except UINoSuchElementError as err:
                if menu_locators.menu.content_views[1] in err.message:
                    self.fail(
                        'content view read only user was not able to access'
                        ' content view via menu: {0}'.format(err.message)
                    )
                else:
                    raise err
            # assert the user can view the content view
            cv_element = self.content_views.search(cv_name)
            self.assertIsNotNone(cv_element)
            # open the content view
            self.content_views.click(cv_element)
            # assert the user can access all the content view tabs
            tabs_locators = [
                tab_locators.contentviews.tab_versions,
                (tab_locators.contentviews.tab_yum_content,
                 locators.contentviews.content_repo),
                (tab_locators.contentviews.tab_yum_content,
                 locators.contentviews.content_filters),
                tab_locators.contentviews.tab_file_repositories,
                tab_locators.contentviews.tab_puppet_modules,
                (tab_locators.contentviews.tab_docker_content,
                 locators.contentviews.docker_repo),
                tab_locators.contentviews.tab_ostree_content,
                tab_locators.contentviews.tab_history,
                tab_locators.contentviews.tab_details,
                tab_locators.contentviews.tab_tasks
            ]
            for locator in tabs_locators:
                try:
                    if isinstance(locator, tuple):
                        for sub_locator in locator:
                            self.content_views.click(sub_locator)
                    else:
                        self.content_views.click(locator)
                except UINoSuchElementError as err:
                    self.fail(
                        'content view read only user was not able to access'
                        ' a content view tab: {0}'.format(err.message)
                    )
            # assert that the user can view the repo in content view
            self.content_views.click(tab_locators.contentviews.tab_yum_content)
            self.content_views.click(locators.contentviews.content_repo)
            self.content_views.assign_value(
                locators.contentviews.repo_search, repo_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                locators.contentviews.select_repo % repo_name))

    @run_only_on('sat')
    @tier2
    def test_negative_readonly_user_add_remove_repo(self):
        """Attempt to add and remove content view's yum and docker repositories
        as a readonly user

        :id: 907bf51f-8ebc-420e-b594-af0dc823e5b4

        :Setup:

            1. Create a user with the Content View read-only role
            2. Create a content view
            3. Add custom yum and docker repositories to content view

        :expectedresults: User with read-only role for content view can not see
            'Add'/ 'Remove' repositories tabs as well as 'Add repository' and
            'Remove repository' buttons

        :CaseLevel: Integration

        :BZ: 1317828
        """
        user_login = gen_string('alpha')
        user_password = gen_string('alphanumeric')
        # Create a role with content views read only permissions
        role = entities.Role().create()
        for resource_type, perm_name in (
                ('Host', 'view_hosts'),
                ('Katello::ContentView', 'promote_or_remove_content_views'),
                ('Katello::ContentView', 'publish_content_views'),
                ('Katello::ContentView', 'view_content_views'),
                ('Katello::Product', 'view_products'),
        ):
            # Permission search doesn't filter permissions by name. Filtering
            # them by resource type and looking for one with specific name
            # instead
            perms_list = entities.Permission(
                resource_type=resource_type).search(query={'per_page': 100000})
            desired_perm = next(
                perm for perm in perms_list if perm.name == perm_name)
            entities.Filter(
                organization=[self.organization],
                permission=[desired_perm],
                role=role,
            ).create()
        # Create a user and assign the above created role
        entities.User(
            default_organization=self.organization,
            organization=[self.organization],
            role=[role],
            login=user_login,
            password=user_password,
        ).create()
        # Create yum and docker repositories
        repo_id = self.setup_to_create_cv()
        yum_repo = entities.Repository(id=repo_id).read()
        docker_repo = entities.Repository(
            content_type=REPO_TYPE['docker'],
            docker_upstream_name=DOCKER_UPSTREAM_NAME,
            product=entities.Product(organization=self.organization).create(),
            url=DOCKER_REGISTRY_HUB,
        ).create()
        # Create a content view
        content_view = entities.ContentView(
            organization=self.organization,
            repository=[docker_repo, yum_repo],
        ).create()
        # Log in as readonly user
        with Session(self, user_login, user_password):
            # Open the content view
            cv = self.content_views.search(content_view.name)
            self.assertIsNotNone(cv)
            self.content_views.click(cv)
            # Ensure 'Add'/'Remove' tabs and buttons are absent for both docker
            # and yum repos
            for tab in 'docker', 'yum':
                with self.subTest(tab):
                    if tab == 'docker':
                        self.content_views.click(
                            tab_locators['contentviews.tab_docker_content'])
                        self.content_views.click(
                            locators['contentviews.docker_repo'])
                    elif tab == 'yum':
                        self.content_views.click(
                            tab_locators['contentviews.tab_yum_content'])
                        self.content_views.click(
                            locators['contentviews.content_repo'])

                    for element_locator in (
                        tab_locators['contentviews.tab_repo_add'],
                        tab_locators['contentviews.tab_repo_remove'],
                        locators['contentviews.add_repo'],
                        locators['contentviews.remove_repo'],
                    ):
                        self.assertIsNone(
                            self.content_views.wait_until_element(
                                element_locator,
                                timeout=1,
                            )
                        )

    @run_only_on('sat')
    @tier2
    def test_positive_delete_version_without_refresh(self):
        """Publish content view few times in a row and then delete one version.

        :id: 4c11eaaa-a9c0-4fbc-91f2-e8290dce09f5

        :expectedresults: Version is deleted successfully and all other
            versions are present on the page

        :BZ: 1374134

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        cv = entities.ContentView(organization=org).create()
        cvv_names = []
        for i in range(5):
            cv.publish()
            cvv = cv.read().version[i].read()
            cvv_names.append('Version {0}'.format(cvv.version))
        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            cvv_delete = cvv_names.pop(0)
            self.content_views.delete_version(cv.name, cvv_delete)
            self.content_views.check_progress_bar_status(cvv_delete)
            self.assertIsNone(self.content_views.wait_until_element(
                locators['contentviews.version_name'] % cvv_delete, timeout=5))
            for cvv in cvv_names:
                self.assertIsNotNone(self.content_views.wait_until_element(
                    locators['contentviews.version_name'] % cvv))

    @run_only_on('sat')
    @tier2
    def test_positive_remove_promoted_cv_version_from_default_env(self):
        """Remove promoted content view version from Library environment

        :id: a8649444-b063-4fb4-b932-a3fae7d4021d

        :Steps:

            1. Create a content view
            2. Add a puppet module(s) to the content view
            3. Publish the content view
            4. Promote the content view version from Library -> DEV
            5. remove the content view version from Library environment

        :expectedresults:

            1. Content view version exist only in DEV and not in Library
            2. The puppet module(s) exists in content view version

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        env_dev_name = gen_string('alpha')
        puppet_repo_url = FAKE_0_PUPPET_REPO
        puppet_module_name = FAKE_0_PUPPET_MODULE
        # create a new organization
        org = entities.Organization().create()
        with Session(self) as session:
            # create the DEV lifecycle environment
            make_lifecycle_environment(
                session, org=org.name, name=env_dev_name)
            # create a puppet repository
            self.setup_to_create_cv(
                repo_url=puppet_repo_url,
                repo_type=REPO_TYPE['puppet'],
                org_id=org.id
            )
            # create a content view
            make_contentview(
                session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the puppet module to the created content view
            self.content_views.add_puppet_module(
                cv_name,
                puppet_module_name,
                filter_term='Latest',
            )
            self.assertIsNotNone(
                self.content_views.fetch_puppet_module(
                    cv_name, puppet_module_name)
            )
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            # promote the content view to DEV lifecycle environment
            status = self.content_views.promote(cv_name, version, env_dev_name)
            self.assertIn('Promoted to {}'.format(env_dev_name), status)
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                {ENVIRONMENT, env_dev_name}
            )
            # ensure that puppet module is in content view version
            self.assertIsNotNone(
                self.content_views.puppet_module_search(cv_name, version,
                                                        puppet_module_name)
            )
            # remove the content view version from Library environment
            self.content_views.remove_version_from_environments(
                cv_name, version, [ENVIRONMENT])
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                {env_dev_name}
            )
            # ensure that puppet module still in content view version
            self.assertIsNotNone(
                self.content_views.puppet_module_search(
                    cv_name,
                    version,
                    puppet_module_name
                )
            )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_qe_promoted_cv_version_from_default_env(self):
        """Remove QE promoted content view version from Library environment

        :id: 71ad8b72-68c4-4c98-9387-077f54ef0184

        :Steps:

            1. Create a content view
            2. Add docker repo(s) to it
            3. Publish content view
            4. Promote the content view version to multiple environments
                Library -> DEV -> QE
            5. remove the content view version from Library environment

        :expectedresults: Content view version exist only in DEV, QE and not in
            Library

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        env_dev_name = gen_string('alpha')
        env_qe_name = gen_string('alpha')
        docker_repo_name = gen_string('alpha')
        docker_repo_url = DOCKER_REGISTRY_HUB
        docker_upstream_name = DOCKER_UPSTREAM_NAME
        # create a new organization
        org = entities.Organization().create()
        with Session(self) as session:
            # create the DEV, QE lifecycle environments
            env_prior = None
            for env_name in [env_dev_name, env_qe_name]:
                make_lifecycle_environment(
                    session, org=org.name, name=env_name, prior=env_prior)
                env_prior = env_name
            # create a docker repository
            self.setup_to_create_cv(
                repo_name=docker_repo_name,
                repo_url=docker_repo_url,
                repo_type=REPO_TYPE['docker'],
                org_id=org.id,
                docker_upstream_name=docker_upstream_name
            )
            # create a content view
            make_contentview(
                session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the docker repo to the created content view
            self.content_views.add_remove_repos(
                cv_name, [docker_repo_name], repo_type='docker')
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            # promote the content view to DEV, QE lifecycle environments
            for env_name in [env_dev_name, env_qe_name]:
                status = self.content_views.promote(cv_name, version, env_name)
                self.assertIn('Promoted to {}'.format(env_name), status)
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                {ENVIRONMENT, env_dev_name, env_qe_name}
            )
            # remove the content view version from Library environment
            self.content_views.remove_version_from_environments(
                cv_name, version, [ENVIRONMENT])
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                {env_dev_name, env_qe_name}
            )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_prod_promoted_cv_version_from_default_env(self):
        """Remove PROD promoted content view version from Library environment

        :id: 6a874041-43c7-4682-ba06-571e49d5bbea

        :Steps:

            1. Create a content view
            2. Add yum repositories, puppet modules, docker repositories to CV
            3. Publish content view
            4. Promote the content view version to multiple environments
                Library -> DEV -> QE -> PROD
            5. remove the content view version from Library environment

        :expectedresults: Content view version exist only in DEV, QE, PROD and
            not in Library

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        # create env names [DEV, QE, PROD]
        env_names = [gen_string('alpha') for _ in range(3)]
        all_env_names_set = set(env_names)
        all_env_names_set.add(ENVIRONMENT)
        puppet_repo_url = FAKE_0_PUPPET_REPO
        puppet_module_name = FAKE_0_PUPPET_MODULE
        repos = [
            dict(
                repo_name=gen_string('alpha'),
                repo_url=FAKE_0_YUM_REPO,
                repo_type=REPO_TYPE['yum'],
            ),
            dict(
                repo_name=gen_string('alpha'),
                repo_url=DOCKER_REGISTRY_HUB,
                repo_type=REPO_TYPE['docker'],
                docker_upstream_name=DOCKER_UPSTREAM_NAME
            ),
            dict(
                repo_name=gen_string('alpha'),
                repo_url=puppet_repo_url,
                repo_type=REPO_TYPE['puppet'],
            ),
        ]
        # create a new organization
        org = entities.Organization().create()
        with Session(self) as session:
            # create the DEV, QE, PROD lifecycle environments
            env_prior = None
            for env_name in env_names:
                make_lifecycle_environment(
                    session, org=org.name, name=env_name, prior=env_prior)
                env_prior = env_name
            # create the repositories
            for repo in repos:
                self.setup_to_create_cv(
                    org_id=org.id,
                    **repo
                )
            # create a content view
            make_contentview(
                session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the repos to content view
            for repo in repos:
                repo_name = repo['repo_name']
                repo_type = repo['repo_type']
                if repo_type == 'puppet':
                    self.content_views.add_puppet_module(
                        cv_name,
                        puppet_module_name,
                        filter_term='Latest',
                    )
                    self.assertIsNotNone(
                        self.content_views.fetch_puppet_module(
                            cv_name, puppet_module_name)
                    )
                else:
                    self.content_views.add_remove_repos(
                        cv_name, [repo_name], repo_type=repo_type)
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            # promote the content view to DEV, QE, PROD lifecycle environments
            for env_name in env_names:
                status = self.content_views.promote(cv_name, version, env_name)
                self.assertIn('Promoted to {}'.format(env_name), status)
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                all_env_names_set
            )
            # remove the content view version from Library environment
            self.content_views.remove_version_from_environments(
                cv_name, version, [ENVIRONMENT])
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                set(env_names)
            )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_cv_version_from_env(self):
        """Remove promoted content view version from environment

        :id: d1da23ee-a5db-4990-9572-1a0919a9fe1c

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view version to multiple environments
                Library -> DEV -> QE -> STAGE -> PROD
            5. remove the content view version from PROD environment
            6. Assert: content view version exists only in Library, DEV, QE,
                STAGE and not in PROD
            7. Promote again from STAGE -> PROD

        :expectedresults: Content view version exist in Library, DEV, QE,
            STAGE, PROD

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        # create env names [DEV, QE, STAGE, PROD]
        env_names = [gen_string('alpha') for _ in range(4)]
        env_dev_name, env_qe_name, env_stage_name, env_prod_name = env_names
        all_env_names_set = set(env_names)
        all_env_names_set.add(ENVIRONMENT)
        puppet_repo_url = FAKE_0_PUPPET_REPO
        puppet_module_name = FAKE_0_PUPPET_MODULE
        repos = [
            dict(
                repo_name=gen_string('alpha'),
                repo_url=FAKE_0_YUM_REPO,
                repo_type=REPO_TYPE['yum'],
            ),
            dict(
                repo_name=gen_string('alpha'),
                repo_url=puppet_repo_url,
                repo_type=REPO_TYPE['puppet'],
            ),
        ]
        # create a new organization
        org = entities.Organization().create()
        with Session(self) as session:
            # create the DEV, QE, STAGE, PROD lifecycle environments
            env_prior = None
            for env_name in env_names:
                make_lifecycle_environment(
                    session, org=org.name, name=env_name, prior=env_prior)
                env_prior = env_name
            # create the repositories
            for repo in repos:
                self.setup_to_create_cv(
                    org_id=org.id,
                    **repo
                )
            # create a content view
            make_contentview(
                session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the repos to content view
            for repo in repos:
                repo_name = repo['repo_name']
                repo_type = repo['repo_type']
                if repo_type == 'puppet':
                    self.content_views.add_puppet_module(
                        cv_name,
                        puppet_module_name,
                        filter_term='Latest',
                    )
                    self.assertIsNotNone(
                        self.content_views.fetch_puppet_module(
                            cv_name, puppet_module_name)
                    )
                else:
                    self.content_views.add_remove_repos(
                        cv_name, [repo_name], repo_type=repo_type)
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            # promote the content view to all lifecycle environments
            for env_name in env_names:
                status = self.content_views.promote(cv_name, version, env_name)
                self.assertIn('Promoted to {}'.format(env_name), status)
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                all_env_names_set
            )
            # remove the content view version from PROD environment
            self.content_views.remove_version_from_environments(
                cv_name, version, [env_prod_name])
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                {ENVIRONMENT, env_dev_name, env_qe_name, env_stage_name}
            )
            # promote again to PROD
            self.content_views.promote(cv_name, version, env_prod_name)
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                all_env_names_set
            )

    @run_only_on('sat')
    @tier2
    def test_positive_remove_cv_version_from_multi_env(self):
        """Remove promoted content view version from multiple environment

        :id: 0d54c256-ac6d-4487-ab09-4e8dd257358e

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view version to multiple environments
                Library -> DEV -> QE -> STAGE -> PROD
            5. Remove content view version from QE, STAGE and PROD

        :expectedresults: Content view version exists only in Library, DEV

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        # create env names [DEV, QE, STAGE, PROD]
        env_names = [gen_string('alpha') for _ in range(4)]
        env_dev_name, env_qe_name, env_stage_name, env_prod_name = env_names
        all_env_names_set = set(env_names)
        all_env_names_set.add(ENVIRONMENT)
        puppet_repo_url = FAKE_0_PUPPET_REPO
        puppet_module_name = FAKE_0_PUPPET_MODULE
        repos = [
            dict(
                repo_name=gen_string('alpha'),
                repo_url=FAKE_0_YUM_REPO,
                repo_type=REPO_TYPE['yum'],
            ),
            dict(
                repo_name=gen_string('alpha'),
                repo_url=puppet_repo_url,
                repo_type=REPO_TYPE['puppet'],
            ),
        ]
        # create a new organization
        org = entities.Organization().create()
        with Session(self) as session:
            # create the DEV, QE, STAGE, PROD lifecycle environments
            env_prior = None
            for env_name in env_names:
                make_lifecycle_environment(
                    session, org=org.name, name=env_name, prior=env_prior)
                env_prior = env_name
            # create the repositories
            for repo in repos:
                self.setup_to_create_cv(
                    org_id=org.id,
                    **repo
                )
            # create a content view
            make_contentview(
                session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the repos to content view
            for repo in repos:
                repo_name = repo['repo_name']
                repo_type = repo['repo_type']
                if repo_type == 'puppet':
                    self.content_views.add_puppet_module(
                        cv_name,
                        puppet_module_name,
                        filter_term='Latest',
                    )
                    self.assertIsNotNone(
                        self.content_views.fetch_puppet_module(
                            cv_name, puppet_module_name)
                    )
                else:
                    self.content_views.add_remove_repos(
                        cv_name, [repo_name], repo_type=repo_type)
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            # promote the content view to all lifecycle environments
            for env_name in env_names:
                status = self.content_views.promote(cv_name, version, env_name)
                self.assertIn('Promoted to {}'.format(env_name), status)
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                all_env_names_set
            )
            # remove the content view version from QE, STAGE, PROD environments
            self.content_views.remove_version_from_environments(
                cv_name, version, [env_qe_name, env_stage_name, env_prod_name])
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                {ENVIRONMENT, env_dev_name}
            )

    @run_only_on('sat')
    @upgrade
    @tier2
    def test_positive_delete_cv_promoted_to_multi_env(self):
        """Delete published content view with version promoted to multiple
         environments

        :id: f16f2db5-7f5b-4ebb-863e-6c18ff745ce4

        :Steps:

            1. Create a content view
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view to multiple environment Library -> DEV
                -> QE -> STAGE -> PROD
            5. Delete the content view, this should delete the content with all
                it's published/promoted versions from all environments

        :expectedresults: The content view doesn't exists

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        # create env names [DEV, QE, STAGE, PROD]
        env_names = [gen_string('alpha') for _ in range(4)]
        all_env_names_set = set(env_names)
        all_env_names_set.add(ENVIRONMENT)
        puppet_repo_url = FAKE_0_PUPPET_REPO
        puppet_module_name = FAKE_0_PUPPET_MODULE
        repos = [
            dict(
                repo_name=gen_string('alpha'),
                repo_url=FAKE_0_YUM_REPO,
                repo_type=REPO_TYPE['yum'],
            ),
            dict(
                repo_name=gen_string('alpha'),
                repo_url=puppet_repo_url,
                repo_type=REPO_TYPE['puppet'],
            ),
        ]
        # create a new organization
        org = entities.Organization().create()
        with Session(self) as session:
            # create the DEV, QE, STAGE, PROD lifecycle environments
            env_prior = None
            for env_name in env_names:
                make_lifecycle_environment(
                    session, org=org.name, name=env_name, prior=env_prior)
                env_prior = env_name
            # create the repositories
            for repo in repos:
                self.setup_to_create_cv(
                    org_id=org.id,
                    **repo
                )
            # create a content view
            make_contentview(
                session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the repos to content view
            for repo in repos:
                repo_name = repo['repo_name']
                repo_type = repo['repo_type']
                if repo_type == 'puppet':
                    self.content_views.add_puppet_module(
                        cv_name,
                        puppet_module_name,
                        filter_term='Latest',
                    )
                    self.assertIsNotNone(
                        self.content_views.fetch_puppet_module(
                            cv_name, puppet_module_name)
                    )
                else:
                    self.content_views.add_remove_repos(
                        cv_name, [repo_name], repo_type=repo_type)
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            # promote the content view to all lifecycle environments
            for env_name in env_names:
                status = self.content_views.promote(cv_name, version, env_name)
                self.assertIn('Promoted to {}'.format(env_name), status)
            self.assertEqual(
                set(self._get_cv_version_environments(version)),
                all_env_names_set
            )
            # remove all the environments from version
            self.content_views.remove_version_from_environments(
                cv_name, version, list(all_env_names_set))
            # delete content view
            self.content_views.delete(cv_name)

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_remove_cv_version_from_env_with_host_registered(self):
        """Remove promoted content view version from environment that is used
        in association of an Activation key and content-host registration.

        :id: a8ca3de1-3f79-4029-8033-00315b6b854f

        :Steps:

            1. Create a content view cv1
            2. Add a yum repo and a puppet module to the content view
            3. Publish the content view
            4. Promote the content view to multiple environment Library -> DEV
                -> QE
            5. Create an Activation key with the QE environment
            6. Register a content-host using the Activation key
            7. Remove the content view cv1 version from QE environment.  The
                remove environment wizard should propose to replace the current
                QE environment of cv1 by an other (as QE environment of cv1 is
                attached to a content-host), choose DEV and content view cv1 as
                a replacement for Content-host and for Activation key.
            8. Refresh content-host subscription

        :expectedresults:

            1. Activation key exists
            2. Content-host exists
            3. QE environment of cv1 was replaced by DEV environment of cv1 in
                activation key
            4. QE environment of cv1 was replaced by DEV environment of cv1 in
                content-host
            5. At content-host some package from cv1 is installable

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_delete_cv_multi_env_promoted_with_host_registered(self):
        """Delete published content view with version promoted to multiple
         environments, with one of the environments used in association of an
         Activation key and content-host registration.

        :id: 73453c99-8f34-413d-8f95-e4a2f4c58a00

        :Steps:

            1. Create two content view cv1 and cv2
            2. Add a yum repo and a puppet module to both content views
            3. Publish the content views
            4. Promote the content views to multiple environment Library -> DEV
                -> QE
            5. Create an Activation key with the QE environment and cv1
            6. Register a content-host using the Activation key
            7. Delete the content view cv1.  The delete content view wizard
                should propose to replace the current QE environment of cv1 by
                an other (as QE environment of cv1 is attached to a
                content-host), choose DEV and content view cv2 as a replacement
                for Content-host and for Activation key.
            8. Refresh content-host subscription

        :expectedresults:

            1. The content view cv1 doesn't exist
            2. Activation key exists
            3. Content-host exists
            4. QE environment of cv1 was replaced by DEV environment of cv2 in
                activation key
            5. QE environment of cv1 was replaced by DEV environment of cv2 in
                content-host
            6. At content-host some package from cv2 is installable

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_remove_cv_version_from_multi_env_capsule_scenario(self):
        """Remove promoted content view version from multiple environment,
        with satellite setup to use capsule

        :id: ba731272-66e6-461e-8e9d-564b4092a92d

        :Steps:

            1. Create a content view
            2. Setup satellite to use a capsule and to sync all lifecycle
                environments
            3. Add a yum repo, puppet module and a docker repo to the content
                view
            4. Publish the content view
            5. Promote the content view to multiple environment Library -> DEV
                -> QE -> PROD
            6. Make sure the capsule is updated (content synchronization may be
                applied)
            7. Disconnect the capsule
            8. Remove the content view version from Library and DEV
                environments and assert successful completion
            9. Bring the capsule back online and assert that the task is
                completed in capsule
            10. Make sure the capsule is updated (content synchronization may
                be applied)

        :expectedresults: content view version in capsule is removed from
            Library and DEV and exists only in QE and PROD

        :caseautomation: notautomated

        :CaseLevel: System
        """
        # Note: This test case requires complete external capsule
        #  configuration.

    @stubbed()
    @tier2
    def test_positive_arbitrary_file_repo_addition(self):
        """Check a File Repository with Arbitrary File can be added to a
        Content View

        :id: 3837799a-1041-44b1-88b5-6f34c118e3a9

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)

        :Steps:
            1. Add the FR to the CV

        :expectedresults: Check FR is added to CV

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_arbitrary_file_repo_removal(self):
        """Check a File Repository with Arbitrary File can be removed from a
        Content View

        :id: f37f7013-569d-4318-95ec-b9fd1111e62d

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)
            4. Add the FR to the CV

        :Steps:
            1. Remove the FR from the CV

        :expectedresults: Check FR is removed from CV

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier3
    def test_positive_arbitrary_file_sync_over_capsule(self):
        """Check a File Repository with Arbitrary File can be added to a
        Content View is synced throughout capsules

        :id: ec56b501-daad-4757-a01a-2aec20ed1e2c

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)
            4. Add the FR to the CV
            5. Create a Capsule
            6. Connect the Capsule with Satellite/Foreman host

        :Steps:
            1. Start synchronization

        :expectedresults: Check CV with FR is synced over Capsule

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier2
    def test_positive_arbitrary_file_repo_promotion(self):
        """Check arbitrary files availability on Environment after Content
        View promotion

        :id: 1ea04f8d-3341-4d6c-b863-1a96dcebd830

        :Setup:
            1. Create a File Repository (FR)
            2. Upload an arbitrary file to it
            3. Create a Content View (CV)
            4. Add the FR to the CV
            5. Create an Environment

        :Steps:
            1. Promote the CV to the Environment

        :expectedresults: Check arbitrary files from FR is available on
            environment

        :caseautomation: notautomated

        :CaseLevel: Integration
        """
