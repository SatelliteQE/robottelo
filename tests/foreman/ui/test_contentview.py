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
import random

from datetime import date, timedelta
from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import (
    call_entity_method_with_timeout,
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
    get_role_by_bz,
)
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.contentview import ContentView
from robottelo.cli.factory import (
    activationkey_add_subscription_to_repo,
    make_content_view,
    make_content_view_filter,
    make_content_view_filter_rule,
    make_lifecycle_environment as cli_make_lifecycle_environment,
    make_org,
    make_product,
    make_repository,
    setup_org_for_a_rh_repo,
)
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_CV,
    DEFAULT_PTABLE,
    DEFAULT_SUBSCRIPTION_NAME,
    DISTRO_RHEL7,
    DOCKER_REGISTRY_HUB,
    DOCKER_UPSTREAM_NAME,
    ENVIRONMENT,
    FAKE_0_INC_UPD_ERRATA,
    FAKE_0_INC_UPD_NEW_PACKAGE,
    FAKE_0_INC_UPD_NEW_UPDATEFILE,
    FAKE_0_INC_UPD_OLD_PACKAGE,
    FAKE_0_INC_UPD_OLD_UPDATEFILE,
    FAKE_0_INC_UPD_URL,
    FAKE_0_PUPPET_REPO,
    FAKE_0_PUPPET_MODULE,
    FAKE_0_YUM_REPO,
    FAKE_1_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    FAKE_3_YUM_REPO,
    FAKE_9_YUM_REPO,
    FAKE_9_YUM_SECURITY_ERRATUM_COUNT,
    FEDORA23_OSTREE_REPO,
    FILTER_CONTENT_TYPE,
    FILTER_ERRATA_TYPE,
    FILTER_ERRATA_DATE,
    FILTER_TYPE,
    PERMISSIONS,
    PRDS,
    PUPPET_MODULE_CUSTOM_FILE_NAME,
    PUPPET_MODULE_CUSTOM_NAME,
    REPOS,
    REPOSET,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
    REPO_TYPE,
    ZOO_CUSTOM_GPG_KEY,
)
from robottelo.datafactory import invalid_names_list, valid_data_list
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade
)
from robottelo.decorators.host import skip_if_os
from robottelo.helpers import (
    create_repo,
    get_data_file,
    read_data_file,
    repo_add_updateinfo,
)
from robottelo.ssh import upload_file
from robottelo.test import UITestCase
from robottelo.ui.base import UIError, UINoSuchElementError
from robottelo.ui.factory import (
    make_contentview,
    make_hostgroup,
    make_lifecycle_environment,
    set_context,
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
    def test_positive_publish_with_repo_with_disabled_http(self):
        """Attempt to publish content view with repository that set
        'publish via http' to False

        :id: 36ccb083-3433-4b54-911a-856e3dc85f39

        :customerscenario: true

        :steps:
            1.  Create a repo with 'publish via http' set to true, url set to
                some upstream repo
            2.  Sync the repo
            3.  Create a content view
            4.  Set 'publish via http' to false
            5.  Add this repo to the content view
            6.  Publish the content view

        :expectedresults: Content view is published successfully

        :BZ: 1355752

        :CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        # Creates a CV along with product and sync'ed repository
        repo_id = self.setup_to_create_cv(
            repo_name=repo_name, repo_unprotected=True)
        prod = entities.Repository(id=repo_id).read().product.read()
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Update repository publishing method
            self.products.search_and_click(prod.name)
            self.repository.update(repo_name, http=False)
            # Add repository to selected CV
            self.content_views.add_remove_repos(cv_name, [repo_name])
            # Publish content view
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))

    @run_only_on('sat')
    @tier2
    def test_positive_remove_filter(self):
        """create empty content views filter and remove it

        :id: 6c6deae7-13f1-4638-a960-d3565d93fd64

        :expectedresults: content views filter removed successfully

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 1cc8d921-92e5-4b51-8050-a7e775095f97

        :expectedresults: content views filter created and selected packages
            can be added for inclusion/exclusion

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
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
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )

    @run_only_on('sat')
    @tier2
    def test_positive_add_package_inclusion_filter_and_publish(self):
        """Add package to inclusion content views filter, publish CV and verify
        package was actually filtered

        :id: 58c32cb5-1392-478e-807a-9c023d5ca0ea

        :expectedresults: Package is included in content view version

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        package1_name = 'cow'
        package2_name = 'bear'
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
                FILTER_TYPE['include'],
            )
            self.content_views.add_packages_to_filter(
                cv_name,
                filter_name,
                [package1_name],
                ['All Versions'],
                [None],
                [None],
            )
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            self.assertIsNotNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    package1_name,
                )
            )
            self.assertIsNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    package2_name,
                )
            )

    @run_only_on('sat')
    @tier2
    def test_positive_add_package_exclusion_filter_and_publish(self):
        """Add package to exclusion content views filter, publish CV and verify
        package was actually filtered

        :id: 304dfb76-a222-48ab-b6de-578a2c81210c

        :expectedresults: Package is excluded from content view version

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        package1_name = 'cow'
        package2_name = 'bear'
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
                [package1_name],
                ['All Versions'],
                [None],
                [None],
            )
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            self.assertIsNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    package1_name,
                )
            )
            # Verify other packages were not affected by exclusion filter
            self.assertIsNotNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    package2_name,
                )
            )

    @run_in_one_thread
    @tier2
    def test_positive_publish_rh_content_with_errata_by_date_filter(self):
        """Publish a CV, containing only RH repo, having errata excluding by
        date filter

        :BZ: 1455990, 1492114

        :id: b4c120b6-129f-4344-8634-df5858c10fef

        :customerscenario: true

        :expectedresults: Errata exclusion by date filter doesn't affect
            packages - errata was successfully filtered out, however packages
            are still present

        :CaseImportance: High
        """
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': org['id'],
        })
        RepositorySet.enable({
            'basearch': 'x86_64',
            'name': REPOSET['rhva6'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
        })
        rhel_repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
        })
        Repository.synchronize({
            'name': REPOS['rhva6']['name'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
        })
        cv = make_content_view({'organization-id': org['id']})
        ContentView.add_repository({
            'id': cv['id'],
            'repository-id': rhel_repo['id'],
        })
        cvf = make_content_view_filter({
            'content-view-id': cv['id'],
            'inclusion': False,
            'repository-ids': rhel_repo['id'],
            'type': 'erratum',
        })
        make_content_view_filter_rule({
            'content-view-filter-id': cvf['filter-id'],
            'start-date': '2011-01-01',
            'types': ['enhancement', 'bugfix', 'security'],
        })
        ContentView.publish({'id': cv['id']})
        version = 'Version {}'.format(
            ContentView.info({'id': cv['id']})['versions'][-1]['version'])
        with Session(self):
            self.nav.go_to_select_org(org['name'])
            packages = self.content_views.fetch_version_packages(
                cv['name'], version)
            self.assertGreaterEqual(len(packages), 1)
            errata = self.content_views.fetch_version_errata(
                cv['name'], version)
            self.assertEqual(len(errata), 0)

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

    @run_only_on('sat')
    @tier2
    def test_positive_update_inclusive_filter_package_version(self):
        """Update version of package inside inclusive cv package filter

        :id: 8d6801de-ab82-49d6-bdeb-0f6e5c95b906

        :expectedresults: Version was updated, next content view version
            contains package with updated version

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        package_name = 'walrus'
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
                FILTER_TYPE['include'],
            )
            self.content_views.add_packages_to_filter(
                cv_name,
                filter_name,
                [package_name],
                ['Equal To'],
                ['0.71-1'],
                [None],
            )
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            self.assertIsNotNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    package_name,
                    '0.71'
                )
            )
            self.assertIsNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    package_name,
                    '5.21'
                )
            )
            self.content_views.update_package_filter(
                cv_name=cv_name,
                filter_name=filter_name,
                package_name=package_name,
                version_type='Equal To',
                version_value='0.71-1',
                new_version_value='5.21-1',
            )
            self.assertIsNotNone(
                self.content_views.wait_until_element(
                    common_locators['alert.success_sub_form'])
            )
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            self.assertIsNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 2.0',
                    package_name,
                    '0.71'
                )
            )
            self.assertIsNotNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 2.0',
                    package_name,
                    '5.21'
                )
            )

    @run_only_on('sat')
    @tier2
    def test_positive_update_exclusive_filter_package_version(self):
        """Update version of package inside exclusive cv package filter

        :id: a8aa8864-190a-46c3-aeed-4953c8f3f601

        :expectedresults: Version was updated, next content view version
            contains package with updated version

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        package_name = 'walrus'
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
                ['0.71-1'],
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
                    '0.71'
                )
            )
            self.assertIsNotNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    package_name,
                    '5.21'
                )
            )
            self.content_views.update_package_filter(
                cv_name=cv_name,
                filter_name=filter_name,
                package_name=package_name,
                version_type='Equal To',
                version_value='0.71-1',
                new_version_value='5.21-1',
            )
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            self.assertIsNotNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 2.0',
                    package_name,
                    '0.71'
                )
            )
            self.assertIsNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 2.0',
                    package_name,
                    '5.21'
                )
            )

    @tier2
    def test_positive_errata_inc_update_list_package(self):
        """Publish incremental update with a new errata for a custom repo

        :BZ: 1489778

        :id: fb43791c-60ee-4190-86be-34ccba411396

        :customerscenario: true

        :expectedresults: New errata and corresponding package are present
            in new content view version

        :CaseImportance: High

        :CaseLevel: Integration
        """
        # Create and publish a repo with 1 outdated package and some errata
        repo_name = gen_string('alphanumeric')
        repo_url = create_repo(
            repo_name,
            FAKE_0_INC_UPD_URL,
            [FAKE_0_INC_UPD_OLD_PACKAGE]
        )
        result = repo_add_updateinfo(
            repo_name, '{}{}'.format(
                FAKE_0_INC_UPD_URL, FAKE_0_INC_UPD_OLD_UPDATEFILE)
        )
        self.assertEqual(result.return_code, 0)
        # Create org, product, repo, sync & publish it
        org = make_org()
        product = make_product({'organization-id': org['id']})
        repo = make_repository({
            'product-id': product['id'],
            'url': repo_url,
        })
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({
            'organization-id': org['id'],
            'repository-ids': repo['id'],
        })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 1)
        cvv = content_view['versions'][0]
        # Add updated package to the repo and errata for the outdated package
        create_repo(
            repo_name,
            FAKE_0_INC_UPD_URL,
            [FAKE_0_INC_UPD_NEW_PACKAGE],
            wipe_repodata=True,
        )
        result = repo_add_updateinfo(
            repo_name, '{}{}'.format(
                FAKE_0_INC_UPD_URL, FAKE_0_INC_UPD_NEW_UPDATEFILE)
        )
        self.assertEqual(result.return_code, 0)
        # Sync the repo
        Repository.synchronize({'id': repo['id']})
        # Publish new CVV with the new errata
        result = ContentView.version_incremental_update({
            'content-view-version-id': cvv['id'],
            'errata-ids': FAKE_0_INC_UPD_ERRATA,
        })
        # Inc update output format is pretty weird - list of dicts where each
        # key's value is actual line from stdout
        result = [
            line.strip()
            for line_dict in result
            for line in line_dict.values()
        ]
        # Verify both the package and the errata are present in output (were
        # added successfully)
        self.assertIn(FAKE_0_INC_UPD_ERRATA, [line.strip() for line in result])
        self.assertIn(
            FAKE_0_INC_UPD_NEW_PACKAGE.rstrip('.rpm'),
            [line.strip() for line in result]
        )
        content_view = ContentView.info({'id': content_view['id']})
        cvv = content_view['versions'][-1]
        # Verify the package and the errata are shown on UI
        with Session(self):
            self.nav.go_to_select_org(org['name'])
            errata = self.content_views.fetch_version_errata(
                content_view['name'], 'Version {}'.format(cvv['version']))
            self.assertGreaterEqual(len(errata), 1)
            self.assertIn(FAKE_0_INC_UPD_ERRATA, set(err[0] for err in errata))
            packages = self.content_views.fetch_version_packages(
                content_view['name'], 'Version {}'.format(cvv['version']))
            self.assertEqual(len(packages), 2)
            packages = set('{}-{}-{}.{}.rpm'.format(*row) for row in packages)
            self.assertEqual(
                packages,
                {FAKE_0_INC_UPD_OLD_PACKAGE, FAKE_0_INC_UPD_NEW_PACKAGE}
            )

    @tier3
    def test_positive_composite_child_inc_update(self):
        """Incremental update with a new errata on a child content view should
        trigger incremental update of parent composite content view

        :BZ: 1304891

        :id: 1a870ad6-c79c-49fc-b449-8c7e74dd95ff

        :customerscenario: true

        :Steps:

            1. Create and publish a repo with 1 outdated package and some
               errata
            2. Create org, product, repo, content view, then sync, publish and
               promote it
            3. Create another content view with Satellite tools in it, publish
               and promote it to the same environment
            4. Create composite content view, add content views from previous
               steps in it (force using the latest versions)
            5. Promote composite content view
            6. Create activation key with subscriptions to both child content
               views
            7. Register a content host with activation key, install certs,
               katello agent, enable repositories
            8. Install outdated package in the content host
            9. Add updated package to the repo and errata for the outdated
               package
            10. Sync the repo in satellite
            11. On the WebUI, find new errata, make sure it's applicable for
                the host
            12. Install the errata to the host, agree with incremental update

        :expectedresults:

            1. Errata installation was successful
            2. Incremental version of composite content view was published
            3. Latest version of composite content view contains the errata and
               updated package

        :CaseImportance: Medium

        :CaseLevel: Integration
        """
        repo_name = gen_string('alphanumeric')
        repo_url = create_repo(
            repo_name,
            FAKE_0_INC_UPD_URL,
            [FAKE_0_INC_UPD_OLD_PACKAGE]
        )
        result = repo_add_updateinfo(
            repo_name, '{}{}'.format(
                FAKE_0_INC_UPD_URL, FAKE_0_INC_UPD_OLD_UPDATEFILE)
        )
        self.assertEqual(result.return_code, 0)
        org = make_org()
        lce = cli_make_lifecycle_environment({'organization-id': org['id']})
        product = make_product({'organization-id': org['id']})
        repo = make_repository({
            'product-id': product['id'],
            'url': repo_url,
        })
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({
            'organization-id': org['id'],
            'repository-ids': repo['id'],
        })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        self.assertEqual(len(content_view['versions']), 1)
        cvv = content_view['versions'][0]
        ContentView.version_promote({
            'id': cvv['id'],
            'organization-id': org['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        result = setup_org_for_a_rh_repo({
            'product': PRDS['rhel'],
            'repository-set': REPOSET['rhst7'],
            'repository': REPOS['rhst7']['name'],
            'organization-id': org['id'],
            'lifecycle-environment-id': lce['id'],
        }, force_manifest_upload=True)
        ak = ActivationKey.info({'id': result['activationkey-id']})
        sattools_cv = ContentView.info({'id': result['content-view-id']})
        composite_cv = make_content_view({
            'composite': True,
            'organization-id': org['id'],
        })
        for cv_id in (content_view['id'], sattools_cv['id']):
            ContentView.component_add({
                'composite-content-view-id': composite_cv['id'],
                'component-content-view-id': cv_id,
                'latest': True,
            })
        ContentView.publish({'id': composite_cv['id']})
        composite_cv = ContentView.info({'id': composite_cv['id']})
        self.assertEqual(len(composite_cv['versions']), 1)
        composite_cvv = composite_cv['versions'][0]
        ContentView.version_promote({
            'id': composite_cvv['id'],
            'organization-id': org['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        ActivationKey.update({
            'content-view-id': composite_cv['id'],
            'id': ak['id'],
            'organization-id': org['id'],
        })
        activationkey_add_subscription_to_repo({
            'activationkey-id': ak['id'],
            'organization-id': org['id'],
            'subscription': product['name'],
        })
        with VirtualMachine(distro=DISTRO_RHEL7) as client:
            client.install_katello_ca()
            client.register_contenthost(org['label'], ak['name'])
            self.assertTrue(client.subscribed)
            client.enable_repo(REPOS['rhst7']['id'])
            client.install_katello_agent()
            client.run(
                'yum install -y {0}'
                .format(FAKE_0_INC_UPD_OLD_PACKAGE.rstrip('.rpm'))
            )
            create_repo(
                repo_name,
                FAKE_0_INC_UPD_URL,
                [FAKE_0_INC_UPD_NEW_PACKAGE],
                wipe_repodata=True,
            )
            result = repo_add_updateinfo(
                repo_name, '{}{}'.format(
                    FAKE_0_INC_UPD_URL, FAKE_0_INC_UPD_NEW_UPDATEFILE)
            )
            self.assertEqual(result.return_code, 0)
            Repository.synchronize({'id': repo['id']})
            with Session(self):
                self.nav.go_to_select_org(org['name'])
                result = self.errata.install(
                    FAKE_0_INC_UPD_ERRATA, [client.hostname], really=True)
                self.assertEqual(result, 'success')
                expected_version = 'Version 1.1'
                self.assertIsNotNone(
                    self.content_views.version_search(
                        composite_cv['name'], expected_version)
                )
                errata = self.content_views.fetch_version_errata(
                    composite_cv['name'], expected_version)
                self.assertGreaterEqual(len(errata), 1)
                self.assertIn(
                    FAKE_0_INC_UPD_ERRATA, set(err[0] for err in errata))
                packages = self.content_views.fetch_version_packages(
                    composite_cv['name'], expected_version)
                packages = set(
                    '{}-{}-{}.{}.rpm'.format(*row) for row in packages)
                self.assertIn(FAKE_0_INC_UPD_NEW_PACKAGE, packages)

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

    @tier2
    def test_positive_add_all_security_errata_by_id_filter(self):
        """Create erratum filter to include only security errata and publish
        new content view version

        :id: bc0be8e8-af53-4db8-937d-93c49c937dcc

        :customerscenario: true

        :BZ: 1275756

        :CaseImportance: High

        :expectedresults: all security errata is present in content view
            version
        """
        filter_name = gen_string('alphanumeric')
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
            session.content_views.publish(content_view.name)
            self.assertIsNotNone(
                self.content_views.version_search(
                    content_view.name, 'Version 1.0'
                )
            )
            session.content_views.add_filter(
                content_view.name,
                filter_name,
                FILTER_CONTENT_TYPE['erratum by id'],
                FILTER_TYPE['include'],
            )
            session.content_views.edit_erratum_id_filter(
                content_view.name,
                filter_name,
                errata_types=['security'],
                open_filter=False,
            )
            session.content_views.add_remove_errata_to_filter(
                content_view.name,
                filter_name,
                select_all=True,
            )
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            session.content_views.publish(content_view.name)
            self.assertIsNotNone(
                self.content_views.version_search(
                    content_view.name, 'Version 2.0'
                )
            )
            result = session.content_views.fetch_version_errata(
                content_view.name, 'Version 2.0')
            self.assertEqual(len(result), FAKE_9_YUM_SECURITY_ERRATUM_COUNT)
            self.assertTrue(
                all(
                    errata[2] == FILTER_ERRATA_TYPE['security']
                    for errata in result
                )
            )

    @run_only_on('sat')
    @tier2
    def test_positive_update_filter_affected_repos(self):
        """Update content view package filter affected repos

        :id: 8f095b11-fd63-4a23-9586-a85d6191314f

        :expectedresults: Affected repos were updated, after new content view
            version publishing only updated repos are affected by content view
            filter

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo1_name = gen_string('alpha')
        repo2_name = gen_string('alpha')
        repo1_package_name = 'walrus'
        repo2_package_name = 'Walrus'
        self.setup_to_create_cv(repo_name=repo1_name)
        self.setup_to_create_cv(
            repo_name=repo2_name, repo_url=FAKE_3_YUM_REPO)
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(
                cv_name, [repo1_name, repo2_name])
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['package'],
                FILTER_TYPE['include'],
            )
            self.content_views.add_packages_to_filter(
                cv_name,
                filter_name,
                [repo1_package_name],
                ['Equal To'],
                ['0.71-1'],
                [None],
            )
            self.content_views.update_filter_affected_repos(
                cv_name,
                filter_name,
                [repo1_name],
            )
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            # Verify filter affected repo1
            self.assertIsNotNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    repo1_package_name,
                    '0.71'
                )
            )
            self.assertIsNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    repo1_package_name,
                    '5.21'
                )
            )
            # Verify repo2 was not affected and repo2 packages are present
            self.assertIsNotNone(
                self.content_views.package_search(
                    cv_name,
                    'Version 1.0',
                    repo2_package_name,
                    '5.6.6'
                )
            )

    @run_only_on('sat')
    @tier2
    def test_negative_add_same_package_filter_twice(self):
        """Update version of package inside exclusive cv package filter

        :id: 5a97de5a-679e-4150-adf7-b4a28290b834

        :expectedresults: Same package filter can not be added again

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        package_name = 'walrus'
        with Session(self) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            for filter_type in FILTER_TYPE['exclude'], FILTER_TYPE['include']:
                with self.subTest(filter_type):
                    filter_name = gen_string('alpha')
                    self.content_views.add_filter(
                        cv_name,
                        filter_name,
                        FILTER_CONTENT_TYPE['package'],
                        filter_type,
                    )
                    for _ in range(2):
                        self.content_views.add_packages_to_filter(
                            cv_name,
                            filter_name,
                            [package_name],
                            ['Equal To'],
                            ['0.71-1'],
                            [None],
                        )
                    self.assertIsNotNone(self.content_views.wait_until_element(
                        common_locators['alert.error_sub_form']))

    @run_only_on('sat')
    @tier2
    def test_positive_add_package_group_filter(self):
        """add package group to content views filter

        :id: 8c02a432-8b2a-4ba3-9613-7070b2dc2bcb

        :expectedresults: content views filter created and selected package
            groups can be added for inclusion/exclusion

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        with Session(self) as session:
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

        :id: bb9eef30-62c4-435c-9573-9f31210b8d7d

        :expectedresults: content views filter created and selected errata-id
            can be added for inclusion/exclusion

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        with Session(self) as session:
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

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_edit_rh_custom_spin(self):
        # Variations might be:
        #   * A filter on errata date (only content that matches date
        # in filter)
        #   * A filter on severity (only content of specific errata
        # severity.
        """Edit content views for a custom rh spin.  For example,
        modify a filter

        :id: 05639074-ef6d-4c6b-8ff6-53033821e686

        :expectedresults: edited content view save is successful and info is
            updated

        :CaseLevel: System
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
        with Session(self) as session:
            # Create content view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['erratum by date and type'],
                FILTER_TYPE['exclude']
            )
            # this assertion should find/open the cv and search for our filter
            self.assertIsNotNone(
                self.content_views.search_filter(cv_name, filter_name))
            # go to the filter open it, edit it and save
            self.content_views.edit_erratum_date_range_filter(
                cv_name,
                filter_name,
                errata_types=[FILTER_ERRATA_TYPE['enhancement'],
                              FILTER_ERRATA_TYPE['bugfix']],
                date_type=FILTER_ERRATA_DATE['issued'],
                start_date='2016-01-01',
                end_date='2016-06-01',
                open_filter=True
            )
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators.alert.success_sub_form))

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
    @tier1
    def test_positive_search_composite(self):
        """Search for content view by its composite property criteria

        :id: 214a721b-3993-4251-9b7c-0f6d2446c1d1

        :customerscenario: true

        :expectedresults: Composite content view is successfully found

        :BZ: 1259374

        :CaseImportance: High
        """
        composite_name = gen_string('alpha')
        with Session(self) as session:
            make_contentview(
                session,
                org=self.organization.name,
                name=composite_name,
                is_composite=True
            )
            self.assertIsNotNone(
                self.content_views.search(
                    composite_name, _raw_query='composite = true')
            )

    @run_in_one_thread
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

        :id: 3e6c2d8a-b62d-4ec7-8353-4a6a4cb58209

        :setup: Sync RH content

        :steps: Assure filter(s) applied to associated content

        :expectedresults: Filtered RH content only is available/can be seen in
            a view

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None
        }
        # Create new org to import manifest
        org = entities.Organization().create()
        self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
        with Session(self) as session:
            # Create content view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.content_views.add_filter(
                cv_name,
                filter_name,
                FILTER_CONTENT_TYPE['erratum by date and type'],
                FILTER_TYPE['exclude']
            )
            # The last executed function will create the filter and open the
            # edit filter form.
            # will not assert the filter existence here to not exit from the
            # filter edit form.
            # will edit the filter fields immediately with open_filter=False
            self.content_views.edit_erratum_date_range_filter(
                cv_name,
                filter_name,
                errata_types=[FILTER_ERRATA_TYPE['enhancement'],
                              FILTER_ERRATA_TYPE['bugfix']],
                date_type=FILTER_ERRATA_DATE['issued'],
                start_date='2016-01-01',
                end_date='2016-06-01',
                open_filter=False
            )
            # this assertion should find/open the cv and search for our filter
            self.assertIsNotNone(
                self.content_views.search_filter(cv_name, filter_name))

    @run_only_on('sat')
    @tier2
    def test_positive_check_composite_cv_addition_list_versions(self):
        """Create new content view and publish two times. After that remove
        first content view version from the list and try to add that view to
        composite one. Check what content view version is going to be added

        :id: ffd4ac4a-4152-433a-a411-567bab115b05

        :expectedresults: second non-composite content view version should be
            listed as default one to be added to composite view

        :CaseLevel: Integration

        :BZ: 1411074
        """
        non_composite_cv = gen_string('alpha')
        composite_cv = gen_string('alpha')
        with Session(self) as session:
            # Create unpublished component CV
            make_contentview(
                session,
                org=self.organization.name,
                name=non_composite_cv,
            )
            self.assertIsNotNone(
                self.content_views.search(non_composite_cv))
            # Publish content view two times to have two versions
            for _ in range(2):
                self.content_views.publish(non_composite_cv)
            # Delete first version for cv
            self.content_views.delete_version(non_composite_cv, 'Version 1.0')
            # Create composite CV
            make_contentview(
                session,
                org=self.organization.name,
                name=composite_cv,
                is_composite=True
            )
            self.assertIsNotNone(self.content_views.search(composite_cv))
            # Check version of content view that we like to add to composite
            # one
            self.content_views.search_and_click(composite_cv)
            self.content_views.click(
                tab_locators['contentviews.tab_content_views'])
            self.content_views.click(
                tab_locators['contentviews.tab_cv_add'])
            self.content_views.assign_value(
                common_locators['kt_search'], non_composite_cv)
            self.content_views.click(common_locators['kt_search_button'])
            version = self.content_views.get_element_value(
                locators['contentviews.add_cv_version_dropdown'])
            self.assertEqual(version, 'Always Use Latest (Currently 2.0)')

    @run_only_on('sat')
    @tier2
    def test_positive_add_non_composite_cv_to_composite(self):
        """Attempt to associate both published and unpublished
        non-composite content views with composite content view.

        :id: 93307c2a-a03f-44fa-972d-43f6e40b9de6

        :steps:

            1. Create an empty non-composite content view. Do not publish it
            2. Create a second non-composite content view. Publish it.
            3. Create a new composite content view.
            4. Add the published non-composite content view to the composite
                content view.
            5. Add the unpublished non-composite content view to the composite
                content view.

        :expectedresults:

            1. Unpublished non-composite content view is successfully added to
                composite content view.
            2. Published non-composite content view is successfully added to
                composite content view.
            3. Composite content view is successfully published

        :CaseLevel: Integration

        :BZ: 1367123
        """
        published_cv_name = gen_string('alpha')
        unpublished_cv_name = gen_string('alpha')
        composite_cv_name = gen_string('alpha')
        with Session(self) as session:
            # Create a published component content view
            make_contentview(
                session, org=self.organization.name, name=published_cv_name)
            self.assertIsNotNone(
                self.content_views.search(published_cv_name))
            self.content_views.publish(published_cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(
                    published_cv_name, 'Version 1.0'
                )
            )
            # Create an unpublished component content view
            make_contentview(
                session, org=self.organization.name, name=unpublished_cv_name)
            self.assertIsNotNone(
                self.content_views.search(unpublished_cv_name))
            # Create a composite content view
            make_contentview(
                session,
                org=self.organization.name,
                name=composite_cv_name,
                is_composite=True
            )
            self.assertIsNotNone(self.content_views.search(composite_cv_name))
            # Add the published content view to the composite one
            self.content_views.add_remove_cv(
                composite_cv_name, [published_cv_name])
            # Add the unpublished content view to the composite one
            self.content_views.add_remove_cv(
                composite_cv_name, [unpublished_cv_name])
            # assert that the version of unpublished content view added to
            # composite one is "Latest (Currently no version)"
            self.content_views.search_and_click(composite_cv_name)
            self.content_views.click(
                tab_locators['contentviews.tab_content_views'])
            self.content_views.click(
                tab_locators['contentviews.tab_cv_remove'])
            self.content_views.assign_value(
                common_locators['kt_search'], unpublished_cv_name)
            self.content_views.click(common_locators['kt_search_button'])
            version = self.content_views.wait_until_element(
                locators[('contentviews.composite_'
                          'list_cv_version_text')] % unpublished_cv_name
            ).text
            self.assertEqual(version, 'Latest (Currently no version)')
            # Publish the composite content view
            self.content_views.publish(composite_cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(
                    composite_cv_name, 'Version 1.0'
                )
            )

    @run_only_on('sat')
    @tier2
    def test_negative_add_dupe_repos(self):
        """attempt to associate the same repo multiple times within a
        content view

        :id: 24b98075-fca6-4d80-a778-066193c71e7f

        :expectedresults: User cannot add repos multiple times to the view

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        with Session(self) as session:
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            with self.assertRaises(UIError) as context:
                self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertEqual(
                str(context.exception),
                'Could not find repo "{0}" to add into CV'
                .format(repo_name)
            )

    @run_only_on('sat')
    @tier2
    def test_negative_add_dupe_modules(self):
        """attempt to associate duplicate puppet module(s) within a
        content view

        :id: ee33a306-9f91-439d-ac7c-d30f7e1a14cc

        :expectedresults: User cannot add modules multiple times to the view

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        module_name = 'samba'
        product = entities.Product(organization=self.organization).create()
        puppet_repository = entities.Repository(
            url=FAKE_0_PUPPET_REPO,
            content_type='puppet',
            product=product
        ).create()
        puppet_repository.sync()
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_puppet_module(
                cv_name,
                module_name,
                filter_term='Latest'
            )
            # ensure that the puppet module is added to content view
            self.assertIsNotNone(
                self.content_views.fetch_puppet_module(
                    cv_name, module_name)
            )
            # ensure that cannot add the same module a second time.
            with self.assertRaises(UINoSuchElementError) as context:
                self.content_views.add_puppet_module(
                    cv_name,
                    module_name,
                    filter_term='Latest'
                )
            # ensure that the select location of our module is in the
            # exception message
            _, location = locators.contentviews.select_module % module_name
            self.assertIn(location, str(context.exception))

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_promote_with_rh_content(self):
        """attempt to promote a content view containing RH content

        :id: 82f71639-3580-49fd-bd5a-8dba568b98d1

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be promoted

        :CaseLevel: System
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
        # Create new org to import manifest
        org = entities.Organization().create()
        with Session(self) as session:
            make_lifecycle_environment(
                session, org=org.name, name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element(
                (locators['content_env.select_name'] % env_name)))
            self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            status = self.content_views.promote(
                cv_name, 'Version 1.0', env_name)
            self.assertIn('Promoted to {}'.format(env_name), status)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @upgrade
    @tier3
    def test_positive_promote_with_rh_custom_spin(self):
        """attempt to promote a content view containing a custom RH
        spin - i.e., contains filters.

        :id: 7d93c81f-2815-4b0e-b72c-23a902fe34b1

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be promoted

        :CaseLevel: System
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
        with Session(self) as session:
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
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            status = self.content_views.promote(
                cv_name, 'Version 1.0', env_name)
            self.assertIn('Promoted to {}'.format(env_name), status)

    @run_only_on('sat')
    @tier2
    def test_positive_promote_with_custom_content(self):
        """attempt to promote a content view containing custom content

        :id: 7c2fd8f0-c83f-4725-8953-9590112fae50

        :setup: Multiple environments for an org; custom content synced

        :expectedresults: Content view can be promoted

        :CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        env_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        with Session(self) as session:
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            self.assertIsNotNone(
                session.nav.wait_until_element(
                    locators['content_env.select_name'] % env_name)
            )
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            status = self.content_views.promote(
                cv_name, 'Version 1.0', env_name)
            self.assertIn('Promoted to {}'.format(env_name), status)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_promote_composite_with_custom_content(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to promote composite content view containing custom
        content

        :id: 35efbd83-d32e-4831-9d5b-1adb15289f54

        :setup: Multiple environments for an org; custom content synced

        :steps: create a composite view containing multiple content types

        :expectedresults: Composite content view can be promoted

        :CaseLevel: Integration
        """
        env_name = gen_string('alpha')
        cv1_name = gen_string('alpha')
        cv2_name = gen_string('alpha')
        cv_composite_name = gen_string('alpha')
        custom_repo1_name = gen_string('alpha')
        custom_repo2_name = gen_string('alpha')
        custom_repo1_url = FAKE_0_YUM_REPO
        custom_repo2_url = FAKE_1_YUM_REPO
        puppet_repo1_url = FAKE_0_PUPPET_REPO
        puppet_repo2_url = FAKE_1_PUPPET_REPO
        puppet_module1 = 'httpd'
        puppet_module2 = 'ntp'
        rh7_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        org = entities.Organization().create()
        with Session(self) as session:
            # create a life cycle environment
            make_lifecycle_environment(
                session, org=org.name, name=env_name)
            # create repositories
            self.setup_to_create_cv(rh_repo=rh7_repo, org_id=org.id)
            self.setup_to_create_cv(
                repo_name=custom_repo1_name,
                repo_url=custom_repo1_url,
                org_id=org.id
            )
            self.setup_to_create_cv(
                repo_name=custom_repo2_name,
                repo_url=custom_repo2_url,
                org_id=org.id
            )
            self.setup_to_create_cv(
                repo_url=puppet_repo1_url,
                repo_type=REPO_TYPE['puppet'],
                org_id=org.id
            )
            self.setup_to_create_cv(
                repo_url=puppet_repo2_url,
                repo_type=REPO_TYPE['puppet'],
                org_id=org.id
            )
            # create the first content view
            make_contentview(session, org=org.name, name=cv1_name)
            self.assertIsNotNone(self.content_views.search(cv1_name))
            # add repositories to first content view
            self.content_views.add_remove_repos(
                cv1_name, [rh7_repo['name'], custom_repo1_name])
            # add the first puppet module to first content view
            self.content_views.add_puppet_module(
                cv1_name,
                puppet_module1,
                filter_term='Latest'
            )
            # publish the first content
            self.content_views.publish(cv1_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv1_name, 'Version 1.0'))
            # create the second content view
            make_contentview(session, org=org.name, name=cv2_name)
            self.assertIsNotNone(self.content_views.search(cv2_name))
            # add repositories to the second content view
            self.content_views.add_remove_repos(
                cv2_name, [custom_repo2_name])
            # add the second puppet module to the second content view
            self.content_views.add_puppet_module(
                cv2_name,
                puppet_module2,
                filter_term='Latest'
            )
            # publish the second content
            self.content_views.publish(cv2_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv2_name, 'Version 1.0'))
            # create a composite content view
            make_contentview(session, org=org.name, name=cv_composite_name,
                             is_composite=True)
            self.assertIsNotNone(self.content_views.search(cv_composite_name))
            # add the first and second content views to the composite one
            self.content_views.add_remove_cv(
                cv_composite_name, [cv1_name, cv2_name])
            # publish the composite content view
            version_name = self.content_views.publish(cv_composite_name)
            self.assertIsNotNone(
                self.content_views.version_search(
                    cv_composite_name, version_name))
            # promote the composite content view
            status = self.content_views.promote(
                cv_composite_name, version_name, env_name)
            self.assertIn('Promoted to {}'.format(env_name), status)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier3
    def test_positive_publish_with_rh_content(self):
        """attempt to publish a content view containing RH content

        :id: bd24dc13-b6c4-4a9b-acb2-cd6df30f436c

        :setup: RH content synced

        :expectedresults: Content view can be published

        :CaseLevel: System
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
        self.setup_to_create_cv(rh_repo=rh_repo, org_id=org.id)
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [rh_repo['name']])
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @upgrade
    @tier3
    def test_positive_publish_with_rh_custom_spin(self):
        """attempt to publish  a content view containing a custom RH
        spin - i.e., contains filters.

        :id: 6804f399-8f09-4c53-8f0d-8e681892e93c

        :setup: Multiple environments for an org; RH content synced

        :expectedresults: Content view can be published

        :CaseLevel: System
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
        with Session(self) as session:
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
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))

    @run_only_on('sat')
    @tier2
    def test_positive_publish_with_custom_content(self):
        """attempt to publish a content view containing custom content

        :id: 66b5efc7-2e43-438e-bd80-a754814222f9

        :setup: Multiple environments for an org; custom content synced

        :expectedresults: Content view can be published

        :CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        env_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        with Session(self) as session:
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element(
                locators['content_env.select_name'] % env_name))
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))

    @tier2
    def test_positive_publish_promote_with_custom_puppet_module(self):
        """Ensure that a custom puppet module file can be added to an existent
         puppet repo and it's module added to content view

        :id: 9562c548-5b65-4b79-acc7-382f8a21249d

        :customerscenario: true

        :steps:
            1. Create a product with a puppet repository
            2. Add a custom puppet module file
            3. Create a content view and add The puppet module
            4. Publish and promote the content view

        :expectedresults:
            1. Custom puppet module file successfully uploaded
            2. Puppet module successfully added to content view
            3. Content view successfully published and promoted

        :BZ: 1335833

        :CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        env = entities.LifecycleEnvironment(
            organization=self.organization).create()
        repo_id = self.setup_to_create_cv(
            repo_name=repo_name,
            repo_url=FAKE_0_PUPPET_REPO,
            repo_type=REPO_TYPE['puppet'],
            org_id=self.organization.id,
        )
        product = entities.Repository(id=repo_id).read().product.read()
        with Session(self) as session:
            set_context(session, org=self.organization.name)
            session.products.search_and_click(product.name)
            initial_modules_count = session.repository.fetch_content_count(
                repo_name, 'puppet')
            session.products.search_and_click(product.name)
            session.repository.upload_content(
                repo_name, get_data_file(PUPPET_MODULE_CUSTOM_FILE_NAME))
            session.products.search_and_click(product.name)
            self.assertEqual(
                session.repository.fetch_content_count(repo_name, 'puppet'),
                initial_modules_count + 1
            )
            make_contentview(session, org=self.organization.name, name=cv_name)
            session.content_views.add_puppet_module(
                cv_name,
                PUPPET_MODULE_CUSTOM_NAME,
                filter_term='Latest'
            )
            self.assertIsNotNone(session.content_views.fetch_puppet_module(
                cv_name, PUPPET_MODULE_CUSTOM_NAME))
            cv_version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            status = self.content_views.promote(cv_name, cv_version, env.name)
            self.assertIn('Promoted to {}'.format(env.name), status)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_publish_composite_with_custom_content(self):
        # Variations:
        # RHEL, custom content (i.e., google repos), puppet modules
        # Custom content (i.e., fedora), puppet modules
        # ...etc.
        """attempt to publish composite content view containing custom
        content

        :id: 73947204-408e-4e2e-b87f-ba2e52ee50b6

        :setup: Multiple environments for an org; custom content synced

        :expectedresults: Composite content view can be published

        :CaseLevel: Integration
        """
        env_name = gen_string('alpha')
        cv1_name = gen_string('alpha')
        cv2_name = gen_string('alpha')
        cv_composite_name = gen_string('alpha')
        custom_repo1_name = gen_string('alpha')
        custom_repo2_name = gen_string('alpha')
        custom_repo1_url = FAKE_0_YUM_REPO
        custom_repo2_url = FAKE_1_YUM_REPO
        puppet_repo1_url = FAKE_0_PUPPET_REPO
        puppet_repo2_url = FAKE_1_PUPPET_REPO
        puppet_module1 = 'httpd'
        puppet_module2 = 'ntp'
        rh7_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        org = entities.Organization().create()
        with Session(self) as session:
            # create a life cycle environment
            make_lifecycle_environment(
                session, org=org.name, name=env_name)
            # create repositories
            self.setup_to_create_cv(rh_repo=rh7_repo, org_id=org.id)
            self.setup_to_create_cv(
                repo_name=custom_repo1_name,
                repo_url=custom_repo1_url,
                org_id=org.id
            )
            self.setup_to_create_cv(
                repo_name=custom_repo2_name,
                repo_url=custom_repo2_url,
                org_id=org.id
            )
            self.setup_to_create_cv(
                repo_url=puppet_repo1_url,
                repo_type=REPO_TYPE['puppet'],
                org_id=org.id
            )
            self.setup_to_create_cv(
                repo_url=puppet_repo2_url,
                repo_type=REPO_TYPE['puppet'],
                org_id=org.id
            )
            # create the first content view
            make_contentview(session, org=org.name, name=cv1_name)
            self.assertIsNotNone(self.content_views.search(cv1_name))
            # add repositories to first content view
            self.content_views.add_remove_repos(
                cv1_name, [rh7_repo['name'], custom_repo1_name])
            # add the first puppet module to first content view
            self.content_views.add_puppet_module(
                cv1_name,
                puppet_module1,
                filter_term='Latest'
            )
            # publish the first content
            cv1_version = self.content_views.publish(cv1_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv1_name, 'Version 1.0'))
            # promote the first content view to environment
            status = self.content_views.promote(
                cv1_name, cv1_version, env_name)
            self.assertIn('Promoted to {}'.format(env_name), status)
            # create the second content view
            make_contentview(session, org=org.name, name=cv2_name)
            self.assertIsNotNone(self.content_views.search(cv2_name))
            # add repositories to the second content view
            self.content_views.add_remove_repos(
                cv2_name, [custom_repo2_name])
            # add the second puppet module to the second content view
            self.content_views.add_puppet_module(
                cv2_name,
                puppet_module2,
                filter_term='Latest'
            )
            # publish the second content
            self.content_views.publish(cv2_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv2_name, 'Version 1.0'))
            # create a composite content view
            make_contentview(session, org=org.name, name=cv_composite_name,
                             is_composite=True)
            self.assertIsNotNone(self.content_views.search(cv_composite_name))
            # add the first and second content views to the composite one
            self.content_views.add_remove_cv(
                cv_composite_name, [cv1_name, cv2_name])
            # publish the composite content view
            self.content_views.publish(cv_composite_name)
            self.assertIsNotNone(
                self.content_views.version_search(
                    cv_composite_name, 'Version 1.0'
                )
            )

    @run_only_on('sat')
    @tier2
    def test_positive_publish_version_changes_in_target_env(self):
        # Dev notes:
        # If Dev has version x, then when I promote version y into
        # Dev, version x goes away (ie when I promote version 1 to Dev,
        # version 3 goes away)
        """when publishing new version to environment, version
        gets updated

        :id: c9fa3def-baa2-497f-b6a6-f3b2d72d1ce9

        :setup: Multiple environments for an org; multiple versions of a
            content view created/published

        :steps:
            1. publish a view to an environment noting the CV version
            2. edit and republish a new version of a CV

        :expectedresults: Content view version is updated in target
            environment.

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        env_name = gen_string('alpha')
        # will promote environment to 3 versions
        versions_count = 3
        with Session(self) as session:
            # create environment lifecycle
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element(
                locators.content_env.select_name % env_name))
            # create content view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # begin publishing content view and promoting environment over all
            # the defined versions
            for _ in range(versions_count):
                # before each content view publishing add a new repository
                repo_name = gen_string('alpha')
                # create a repository
                self.setup_to_create_cv(repo_name=repo_name)
                # add the repository to the created content view
                self.content_views.add_remove_repos(cv_name, [repo_name])
                # publish the content view
                version_name = self.content_views.publish(cv_name)
                # assert the content view successfully published
                self.assertIsNotNone(
                    self.content_views.version_search(cv_name, 'Version 1.0'))
                # find this version environments
                environments = self._get_cv_version_environments(
                    version_name)
                # assert that Library is in environments of this version
                self.assertIn(ENVIRONMENT, environments)
                # assert that env_name is not in environments of this version
                self.assertNotIn(env_name, environments)
                # promote content view environment to this version
                status = self.content_views.promote(
                    cv_name, version_name, env_name)
                self.assertIn('Promoted to {}'.format(env_name), status)
                # find this version environments
                environments = self._get_cv_version_environments(
                    version_name)
                # assert that Library is still in environments of this version
                self.assertIn(ENVIRONMENT, environments)
                # assert that env_name is in environments of this version
                self.assertIn(env_name, environments)

    @run_only_on('sat')
    @tier2
    def test_positive_publish_version_changes_in_source_env(self):
        # Dev notes:
        # Similarly when I publish version y, version x goes away from
        # Library (ie when I publish version 2, version 1 disappears)
        """when publishing new version to environment, version
        gets updated

        :id: 576ac8b4-7efe-4267-a672-868a5f3eb28a

        :setup: Multiple environments for an org; multiple versions of a
            content view created/published

        :steps:
            1. publish a view to an environment
            2. edit and republish a new version of a CV

        :expectedresults: Content view version is updated in source
            environment.

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        env_name = gen_string('alpha')
        # will promote environment to 3 versions
        versions_count = 3
        with Session(self) as session:
            # create environment lifecycle
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            self.assertIsNotNone(session.nav.wait_until_element(
                locators.content_env.select_name % env_name))
            # create content view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # for the moment has no source/precedent version
            precedent_version_name = None
            # begin publishing content view and promoting environment over all
            # the defined versions
            for _ in range(versions_count):
                repo_name = gen_string('alpha')
                # create a repository
                self.setup_to_create_cv(repo_name=repo_name)
                # add the repository to the created content view
                self.content_views.add_remove_repos(cv_name, [repo_name])
                # publish the content view
                current_version_name = self.content_views.publish(cv_name)
                # assert the content view successfully published
                self.assertIsNotNone(
                    self.content_views.version_search(cv_name, 'Version 1.0'))
                # promote env_name to the current content view version
                status = self.content_views.promote(
                    cv_name,
                    current_version_name,
                    env_name
                )
                # assert env_name successfully promoted
                self.assertIn('Promoted to {}'.format(env_name), status)
                # find this content view version environments
                current_version_envs = self._get_cv_version_environments(
                    current_version_name)
                # assert that Library is in environments of this version
                self.assertIn(ENVIRONMENT, current_version_envs)
                # assert that env_name is in environments of this version
                self.assertIn(env_name, current_version_envs)
                # need to assert that the environments are not in the
                # precedent version
                if precedent_version_name:
                    # find the precedent version environments
                    precedent_version_envs = self._get_cv_version_environments(
                        precedent_version_name)
                    # assert that Library is not in environments of the
                    # precedent version
                    self.assertNotIn(ENVIRONMENT,
                                     precedent_version_envs)
                    # assert that env_name is not in the environments of the
                    # precedent version
                    self.assertNotIn(env_name, precedent_version_envs)
                # as exiting the loop, set the precedent version to this one
                # as in the nest loop will publish a new one
                precedent_version_name = current_version_name

    @run_only_on('sat')
    @tier2
    def test_positive_clone_within_same_env(self):
        """attempt to create new content view based on existing
        view within environment

        :id: 862c385b-d98c-4c29-8345-fd7a5900483a

        :expectedresults: Content view can be cloned

        :BZ: 1461017

        :CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        copy_cv_name = gen_string('alpha')
        self.setup_to_create_cv(repo_name=repo_name)
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(cv_name, [repo_name])
            # Publish the CV
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            # Copy the CV
            self.content_views.copy_view(cv_name, copy_cv_name)
            self.assertIsNotNone(self.content_views.search(copy_cv_name))
            self.assertEqual(
                repo_name,
                self.content_views.fetch_yum_content_repo_name(copy_cv_name)
            )

    @run_only_on('sat')
    @tier2
    def test_positive_clone_within_diff_env(self):
        """attempt to create new content view based on existing
        view, inside a different environment

        :id: 09b9307f-91de-4d3d-a6af-31c526ea816f

        :expectedresults: Content view can be published

        :BZ: 1461017

        :CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        env_name = gen_string('alpha')
        copy_cv_name = gen_string('alpha')
        copy_env_name = gen_string('alpha')
        # create a repository
        self.setup_to_create_cv(repo_name=repo_name)
        with Session(self) as session:
            # create a lifecycle environment
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            # create a content view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add repository to the created content view
            self.content_views.add_remove_repos(cv_name, [repo_name])
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            # promote env_name to the content view version
            status = self.content_views.promote(cv_name, version, env_name)
            # assert env_name successfully promoted
            self.assertIn('Promoted to {}'.format(env_name), status)
            # create a new lifecycle environment that we should promote to
            #  the published version of the copy of content view
            make_lifecycle_environment(
                session, org=self.organization.name, name=copy_env_name)
            # create a copy of content view with a new name
            self.content_views.copy_view(cv_name, copy_cv_name)
            # ensure that the copy of the content view exist
            self.assertIsNotNone(self.content_views.search(copy_cv_name))
            # ensure that the repository is in the copy of content view
            self.assertEqual(
                repo_name,
                self.content_views.fetch_yum_content_repo_name(copy_cv_name)
            )
            # publish the content view copy
            copy_version = self.content_views.publish(copy_cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(copy_cv_name, copy_version))
            # promote the other environment to the copy of content view version
            status = self.content_views.promote(
                copy_cv_name, copy_version, copy_env_name)
            self.assertIn('Promoted to {}'.format(copy_env_name), status)

    @run_in_one_thread
    @run_only_on('sat')
    @upgrade
    @skip_if_not_set('fake_manifest')
    @tier2
    def test_positive_subscribe_system_with_rh_custom_spin(self):
        """Attempt to subscribe a host to content view with rh repository
         and custom filter

        :id: 3ea6719b-df4d-4b0f-b4b4-69ce852f632e

        :setup: content view with rh repo and custom spin

        :expectedresults: Systems can be subscribed to content view(s)

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        filter_name = gen_string('alpha')
        subscription_name = DEFAULT_SUBSCRIPTION_NAME
        rh_repo = {
            'name': REPOS['rhst7']['name'],
            'product': PRDS['rhel'],
            'reposet': REPOSET['rhst7'],
            'basearch': 'x86_64',
            'releasever': None,
        }
        # create an organization
        org = entities.Organization().create()
        # create a lifecycle environment
        env = entities.LifecycleEnvironment(organization=org).create()
        # create a repository
        self.setup_to_create_cv(org_id=org.id, rh_repo=rh_repo)
        with Session(self) as session:
            # create content view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the repository to content view
            self.content_views.add_remove_repos(
                cv_name, [rh_repo['name']])
            # add a package exclude filter
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
            # add rh subscription to activation key
            sub = entities.Subscription(organization=org)
            subscription_id = None
            for subs in sub.search():
                if subs.read_json()['product_name'] == subscription_name:
                    subscription_id = subs.id
                    break
            self.assertIsNotNone(subscription_id)
            activation_key.add_subscriptions(data={
                'quantity': 1,
                'subscription_id': subscription_id,
            })
            # create a vm host client and ensure it can be subscribed
            with VirtualMachine(distro=DISTRO_RHEL7) as host_client:
                host_client.install_katello_ca()
                host_client.register_contenthost(
                    org.label, activation_key.name)
                self.assertTrue(host_client.subscribed)
                # assert the host_client exists in content hosts page
                self.assertIsNotNone(
                    self.contenthost.search(host_client.hostname))

    @run_only_on('sat')
    @upgrade
    @tier2
    def test_positive_subscribe_system_with_custom_content(self):
        """Attempt to subscribe a host to content view with custom repository

        :id: 715db997-707b-4868-b7cc-b6977fd6ac04

        :setup: content view with custom yum repo

        :expectedresults: Systems can be subscribed to content view(s)

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        repo_url = FAKE_0_YUM_REPO
        # create an organization
        org = entities.Organization().create()
        # create a lifecycle environment
        env = entities.LifecycleEnvironment(organization=org).create()
        # create a yum repository
        self.setup_to_create_cv(
            org_id=org.id, repo_name=repo_name, repo_url=repo_url)
        with Session(self) as session:
            # create content view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the repository to content view
            self.content_views.add_remove_repos(cv_name, [repo_name])
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
            # create a vm host client and ensure it can be subscribed
            with VirtualMachine(distro=DISTRO_RHEL7) as host_client:
                host_client.install_katello_ca()
                host_client.register_contenthost(
                    org.label, activation_key.name)
                self.assertTrue(host_client.subscribed)
                # assert the host_client exists in content hosts page
                self.assertIsNotNone(
                    self.contenthost.search(host_client.hostname))

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
    def test_positive_admin_user_actions(self):
        """Attempt to manage content views

        :id: c4d270fc-a3e6-4ae2-a338-41d864a5622a

        :steps: with global admin account:

            1. create a user with all content views permissions
            2. create lifecycle environment
            3. create 2 content views (one to delete, the other to manage)

        :setup: create a user with all content views permissions

        :expectedresults: The user can Read, Modify, Delete, Publish, Promote
            the content views

        :BZ: 1461017

        :CaseLevel: Integration
        """
        # note: the user to be created should not have permissions to access
        # products repositories
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        cv_new_name = gen_string('alpha')
        cv_copy_name = gen_string('alpha')
        env_name = gen_string('alpha')
        user_login = gen_string('alpha')
        user_password = gen_string('alphanumeric')
        role_name = gen_string('alpha')
        # create a role with all content views permissions
        role = entities.Role(name=role_name).create()
        entities.Filter(
            organization=[self.organization],
            permission=entities.Permission(
                resource_type='Katello::ContentView').search(),
            role=role,
            search=None
        ).create()
        # create environment permissions with read only and promote access
        # to content views
        env_permissions_entities = entities.Permission(
            resource_type='Katello::KTEnvironment').search()
        user_env_permissions = [
            'promote_or_remove_content_views_to_environments',
            'view_lifecycle_environments'
        ]
        user_env_permissions_entities = [
            entity
            for entity in env_permissions_entities
            if entity.name in user_env_permissions
        ]
        entities.Filter(
            organization=[self.organization],
            permission=user_env_permissions_entities,
            role=role,
            # allow access only to the mentioned here environments
            search='name = {0} or name = {1}'.format(ENVIRONMENT, env_name)
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
            # create a lifecycle environment
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            # create the first content view
            make_contentview(
                session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add repository to the created content view
            self.content_views.add_remove_repos(cv_name, [repo_name])
            # create a second content view as a copy of the first one
            self.content_views.copy_view(cv_name, cv_copy_name)
            self.assertIsNotNone(self.content_views.search(cv_copy_name))
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
                        'content view admin user was not able to access'
                        ' content view via menu: {0}'.format(err.message)
                    )
                else:
                    raise err
            # assert the user can view all the content views created
            # by admin user
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.assertIsNotNone(self.content_views.search(cv_copy_name))
            # assert that the user can delete a content view
            try:
                self.content_views.delete(cv_copy_name)
            except UINoSuchElementError as err:
                if locators.contentviews.remove[1] in err.message:
                    self.fail(
                        'content view admin user was not able to access'
                        ' the remove button: {0}'.format(err.message)
                    )
                else:
                    raise err
            # assert that the deleted content view do not exist any more
            self.assertIsNone(self.content_views.search(cv_copy_name))
            # open the content view
            self.content_views.search_and_click(cv_name)
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
                        'content view admin user was not able to access'
                        ' a content view tab: {0}'.format(err.message)
                    )
            # assert that user can edit the content view entity
            try:
                self.content_views.update(cv_name, cv_new_name)
            except UINoSuchElementError as err:
                if locators.contentviews.edit_name[1] in err.message:
                    self.fail(
                        'the content view admin user was not able to '
                        'click on the edit name button: {0}'.format(
                            err.message)
                    )
                elif locators.contentviews.save_name[1] in err.message:
                    self.fail(
                        'the content view admin user was not able to '
                        'click on the edit name save button: {0}'.format(
                            err.message)
                    )
                elif locators.contentviews.edit_description[1] in err.message:
                    self.fail(
                        'the content view admin user was not able to '
                        'click on the description name button: {0}'.format(
                            err.message)
                    )
                elif locators.contentviews.save_description[1] in err.message:
                    self.fail(
                        'the content view admin user was not able to click '
                        'on the description name save button: {0}'.format(
                            err.message)
                    )
                else:
                    raise err
            # assert that the content view exists with the new name
            self.assertIsNotNone(self.content_views.search(cv_new_name))
            # assert that the user can publish and promote the content view
            try:
                version = self.content_views.publish(cv_new_name)
            except UINoSuchElementError as err:
                if locators.contentviews.publish[1] in err.message:
                    self.fail(
                        'the content view admin user was not able to '
                        'click on the publish button: {0}'.format(err.message))
                else:
                    raise err
            self.assertIsNotNone(
                self.content_views.version_search(cv_new_name, version))
            try:
                status = self.content_views.promote(
                    cv_new_name, version, env_name)
            except UINoSuchElementError as err:
                if locators.contentviews.promote_button[1] in err.message:
                    self.fail(
                        'the content view admin user was not able to '
                        'click on the promote button: {0}'.format(err.message)
                    )
                else:
                    raise err
            self.assertIn('Promoted to {}'.format(env_name), status)

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
    def test_negative_non_admin_user_actions(self):
        """Attempt to manage content views

        :id: aae6eede-b40e-4e06-a5f7-59d9251aa35d

        :setup:

            1. create a user with the Content View read-only role
            2. create content view
            3. add a custom repository to content view

        :expectedresults: User with read only role for content view cannot
            Modify, Delete, Publish, Promote the content views

        :CaseLevel: Integration
        """
        # create a content view read only user with lifecycle environment
        # permissions: view_lifecycle_environments and
        # promote_or_remove_content_views_to_environments
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        cv_new_name = gen_string('alpha')
        env_name = gen_string('alpha')
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
        # create environment permissions with read only and promote access
        # to content views
        env_permissions_entities = entities.Permission(
            resource_type='Katello::KTEnvironment').search()
        user_env_permissions = [
            'promote_or_remove_content_views_to_environments',
            'view_lifecycle_environments'
        ]
        user_env_permissions_entities = [
            entity
            for entity in env_permissions_entities
            if entity.name in user_env_permissions
        ]
        entities.Filter(
            organization=[self.organization],
            permission=user_env_permissions_entities,
            role=role,
            # allow access only to the mentioned here environments
            search='name = {0} or name = {1}'.format(ENVIRONMENT, env_name)
        ).create()
        # create a user and assign the above created role
        entities.User(
            default_organization=self.organization,
            organization=[self.organization],
            role=[role],
            login=user_login,
            password=user_password
        ).create()
        # create a content views with the main admin account
        with Session(self) as session:
            # create a lifecycle environment
            make_lifecycle_environment(
                session, org=self.organization.name, name=env_name)
            # create a repository
            self.setup_to_create_cv(repo_name=repo_name)
            # create the first content view
            make_contentview(
                session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add repository to the created content view
            self.content_views.add_remove_repos(cv_name, [repo_name])
        # login as the user created above
        with Session(self, user_login, user_password):
            # to ensure that the created user has only the assigned
            # permissions, check that hosts menu tab does not exist
            self.assertIsNone(
                self.content_views.wait_until_element(
                    menu_locators.menu.hosts, timeout=5)
            )
            # assert the user can view the content views
            self.assertIsNotNone(self.content_views.search(cv_name))
            # assert that the user cannot delete the content view
            with self.assertRaises(UINoSuchElementError) as context:
                self.content_views.delete(cv_name)
            # ensure that the delete locator is in the exception message
            _, locator = common_locators['select_action'] % 'Remove'
            self.assertIn(locator, str(context.exception))
            # ensure the user cannot edit the content view
            with self.assertRaises(UINoSuchElementError) as context:
                self.content_views.update(cv_name, cv_new_name)
            # ensure that the edit locator is in the exception message
            _, locator = locators.contentviews.edit_name
            self.assertIn(locator, str(context.exception))
            # ensure that the content view still exist
            self.assertIsNotNone(self.content_views.search(cv_name))
            # ensure that the user cannot publish the content view
            with self.assertRaises(UINoSuchElementError) as context:
                self.content_views.publish(cv_new_name)
            self.assertIn(
                'element None was not found while trying to click',
                str(context.exception)
            )
        # publish the content view with the main admin account
        with Session(self) as session:
            # select the current organisation
            session.nav.go_to_select_org(self.organization.name)
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
        # login as the user created above and try to promote the content view
        with Session(self, user_login, user_password):
            with self.assertRaises(UINoSuchElementError) as context:
                self.content_views.promote(
                    cv_name, version, env_name)
            _, locator = locators.contentviews.promote_button % version
            self.assertIn(locator, str(context.exception))

    @run_only_on('sat')
    @tier2
    def test_negative_non_readonly_user_actions(self):
        """Attempt to view content views

        :id: 9cbc661a-dbe3-4b88-af27-4cf7b9544074

        :setup: create a user with the Content View without the content views
            read role

        :expectedresults: the user cannot access content views web resources

        :CaseLevel: Integration
        """
        env_name = gen_string('alpha')
        user_login = gen_string('alpha')
        user_password = gen_string('alphanumeric')
        role_name = gen_string('alpha')
        # create a role with all content views permissions except
        # view_content_views
        role = entities.Role(name=role_name).create()
        cv_permissions_entities = entities.Permission(
            resource_type='Katello::ContentView').search()
        user_cv_permissions = list(PERMISSIONS['Katello::ContentView'])
        user_cv_permissions.remove('view_content_views')
        user_cv_permissions_entities = [
            entity
            for entity in cv_permissions_entities
            if entity.name in user_cv_permissions
        ]
        # ensure I have some content views permissions
        self.assertGreater(len(user_cv_permissions_entities), 0)
        self.assertEqual(
            len(user_cv_permissions), len(user_cv_permissions_entities))
        entities.Filter(
            organization=[self.organization],
            permission=user_cv_permissions_entities,
            role=role,
            search=None
        ).create()
        # create environment permissions with read only and promote access
        # to content views
        env_permissions_entities = entities.Permission(
            resource_type='Katello::KTEnvironment').search()
        user_env_permissions = [
            'promote_or_remove_content_views_to_environments',
            'view_lifecycle_environments'
        ]
        user_env_permissions_entities = [
            entity
            for entity in env_permissions_entities
            if entity.name in user_env_permissions
        ]
        entities.Filter(
            organization=[self.organization],
            permission=user_env_permissions_entities,
            role=role,
            # allow access only to the mentioned here environments
            search='name = {0} or name = {1}'.format(ENVIRONMENT, env_name)
        ).create()
        # create a user and assign the above created role
        entities.User(
            default_organization=self.organization,
            organization=[self.organization],
            role=[role],
            login=user_login,
            password=user_password
        ).create()
        # login as the user created above
        with Session(self, user_login, user_password) as session:
            # to ensure that the created user has only the assigned
            # permissions, check that hosts menu tab does not exist
            self.assertIsNone(
                self.content_views.wait_until_element(
                    menu_locators.menu.hosts, timeout=5)
            )
            # ensure that user cannot go to content views via application menu
            with self.assertRaises(UINoSuchElementError) as context:
                session.nav.go_to_content_views()
            _, locator = menu_locators.menu.content_views
            self.assertIn(locator, str(context.exception))
            # ensure that user cannot access content views page using browser
            # URL directly
            content_views_url = ''.join(
                [settings.server.get_url(), '/content_views'])
            self.browser.get(content_views_url)
            # ensure that we have been redirected to some other url
            self.assertNotEqual(self.browser.current_url, content_views_url)
            # assert that we were redirected to katello/403
            self.assertTrue(self.browser.current_url.endswith('katello/403'))
            # to restore from last navigation and allow the test session
            # to finish normally with logging out
            # go to root url, this will allow the session to find the
            # logout button
            self.browser.get(settings.server.get_url())

    @run_only_on('sat')
    @tier2
    def test_positive_delete_default_version(self):
        """Delete a content-view version associated to 'Library'

        :id: 6000a3f5-a8c2-49a4-ba30-d73a18d39e0a

        :expectedresults: Deletion was performed successfully

        :CaseLevel: Integration
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
        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @tier2
    def test_positive_delete_non_default_version(self):
        """Delete a content-view version associated to non-default
        environment

        :id: 1c1beb36-e06b-419f-96db-43b4d85c5e25

        :expectedresults: Deletion was performed successfully

        :CaseLevel: Integration
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
        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @upgrade
    @tier2
    def test_positive_delete_version_with_ak(self):
        """Delete a content-view version that had associated activation
        key to it

        :id: 0da50b26-f82b-4663-9372-4c39270d4323

        :expectedresults: Deletion was performed successfully

        :CaseLevel: Integration
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

        with Session(self) as session:
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

    @tier2
    @upgrade
    def test_positive_delete_composite_version(self):
        """Delete a composite content-view version associated to 'Library'

        :id: b2d9b21d-1e0d-40f1-9bbc-3c88cddd4f5e

        :expectedresults: Deletion was performed successfully

        :CaseLevel: Integration

        :BZ: 1276479
        """
        org = entities.Organization().create()
        # Create and publish product/repository
        product = entities.Product(organization=org).create()
        repo = entities.Repository(
            product=product, url=FAKE_1_YUM_REPO).create()
        repo.sync()
        # Create and publish content view
        content_view = entities.ContentView(
            organization=org, repository=[repo]).create()
        content_view.publish()
        # Create and publish composite content view
        composite_cv = entities.ContentView(
            organization=org,
            composite=True,
            component=[content_view.read().version[0]],
        ).create()
        composite_cv.publish()
        composite_cv = composite_cv.read()
        # Get published content-view version id
        self.assertEqual(len(composite_cv.version), 1)
        cvv = composite_cv.version[0].read()
        self.assertEqual(len(cvv.environment), 1)
        # API returns version like '1.0'
        # WebUI displays version like 'Version 1.0'
        version = 'Version {0}'.format(cvv.version)
        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(composite_cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(
                composite_cv.name, version)

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
    @tier3
    def test_positive_delete_with_kickstart_repo_and_host_group(self):
        """Check that Content View associated with kickstart repository and
        which is used by a host group can be removed from the system

        :id: 7b076f55-72c9-4413-a592-92a47b51cb0a

        :customerscenario: true

        :expectedresults: Deletion was performed successfully

        :BZ: 1417072

        :CaseLevel: Integration
        """
        sat6_hostname = settings.server.hostname
        org = entities.Organization().create()
        # Create a new Life-Cycle environment
        lc_env = entities.LifecycleEnvironment(organization=org).create()

        # Create a Product and Kickstart Repository for OS distribution content
        product = entities.Product(organization=org).create()
        repo = entities.Repository(
            product=product, url=settings.rhel6_os).create()

        # Repo sync procedure
        call_entity_method_with_timeout(repo.sync, timeout=3600)

        # Create, Publish and promote CV
        content_view = entities.ContentView(organization=org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()
        promote(content_view.version[0], lc_env.id)

        # Get the Partition table ID
        ptable = entities.PartitionTable().search(
            query={
                u'search': u'name="{0}"'.format(DEFAULT_PTABLE)
            }
        )[0]
        # Get the arch ID
        arch = entities.Architecture().search(
            query={u'search': u'name="{0}"'.format(DEFAULT_ARCHITECTURE)}
        )[0].read()
        # Get the OS ID
        os = entities.OperatingSystem().search(query={
            u'search': u'name="RedHat" AND (major="{0}" OR major="{1}")'
                       .format(RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION)
        })[0]
        # Update the OS to associate arch and ptable
        os.architecture = [arch]
        os.ptable = [ptable]
        os = os.update(['architecture', 'ptable'])
        with Session(self) as session:
            hg_name = gen_string('alpha')
            make_hostgroup(
                session,
                name=hg_name,
                org=org.name,
                parameters_list=[
                    ['Host Group', 'Lifecycle Environment', lc_env.name],
                    ['Host Group', 'Content View', content_view.name],
                    ['Host Group', 'Content Source', sat6_hostname],
                    ['Host Group', 'Puppet CA', sat6_hostname],
                    ['Host Group', 'Puppet Master', sat6_hostname],
                    ['Operating System', 'Architecture', arch.name],
                    [
                        'Operating System',
                        'Operating system',
                        '{} {}.{}'.format(os.name, os.major, os.minor)
                    ],
                    ['Operating System', 'Partition table', ptable.name],
                    ['Operating System', 'Media Selection', 'synced_content'],
                    ['Operating System', 'Synced Content', repo.name],
                ],
            )
            self.assertIsNotNone(self.hostgroup.search(hg_name))
            self.content_views.search_and_click(content_view.name)
            self.content_views.perform_entity_action('Remove')
            self.assertIn(
                '{} cannot be deleted as one or more Content View Versions are'
                ' still promoted to a Lifecycle'.format(content_view.name),
                self.content_views.wait_until_element(
                    locators['contentviews.remove_warning']).text
            )
            self.content_views.delete_version(content_view.name, 'Version 1.0')
            self.content_views.check_progress_bar_status('Version 1.0')
            self.assertIsNone(self.content_views.wait_until_element(
                locators['contentviews.version_name'] % 'Version 1.0',
                timeout=5
            ))
            self.content_views.delete(content_view.name)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_add_custom_ostree(self):
        """Create a CV with custom ostree contents

        :id: 66626fcd-9d2b-4ff5-a596-b7754b044dbe

        :expectedresults: CV should be created successfully with custom ostree
            contents

        :CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        self.setup_to_create_cv(
            repo_name=repo_name,
            repo_url=FEDORA23_OSTREE_REPO,
            repo_type=REPO_TYPE['ostree'],
            repo_unprotected=False
        )
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [repo_name],
                repo_type='ostree'
            )

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_add_rh_ostree(self):
        """Create a CV with RH ostree contents

        :id: 2c6ee15f-a058-4569-a324-aec4bba1bd17

        :expectedresults: CV should be created successfully with RH ostree
            contents

        :CaseLevel: Integration
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
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [rh_repo['name']],
                repo_type='ostree'
            )

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_custom_ostree(self):
        """Create a CV with custom ostree contents and remove the
        contents.

        :id: 0e312f20-846b-440e-9c3a-392e889c9cdd

        :expectedresults: Content should be removed and CV should be updated
            successfully

        :CaseLevel: Integration
        """
        repo_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        self.setup_to_create_cv(
            repo_name=repo_name,
            repo_url=FEDORA23_OSTREE_REPO,
            repo_type=REPO_TYPE['ostree'],
            repo_unprotected=False
        )
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [repo_name],
                repo_type='ostree'
            )
            self.content_views.add_remove_repos(
                cv_name,
                [repo_name],
                add_repo=False,
                repo_type='ostree'
            )

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_rh_ostree(self):
        """Create a CV with RH ostree contents and remove the
        contents.

        :id: 852ce474-82a7-4199-9f12-5b9ad352e036

        :expectedresults: Content should be removed and CV should be updated
            successfully

        :CaseLevel: Integration
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
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [rh_repo['name']],
                repo_type='ostree'
            )
            self.content_views.add_remove_repos(
                cv_name,
                [rh_repo['name']],
                add_repo=False,
                repo_type='ostree'
            )

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_create_with_custom_ostree_other_contents(self):
        """Create a CV with custom ostree contents and other custom yum, puppet
        repos.

        :id: b139eb12-d960-4a45-9e22-3a22184c5415

        :expectedresults: CV should be created successfully with all custom
            contents

        :CaseLevel: Integration
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
        # sync repository with custom timeout
        call_entity_method_with_timeout(ostree_repo.sync, timeout=1500)
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
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add ostree repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [ostree_repo.name],
                repo_type='ostree'
            )
            # Add yum repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [yum_repo.name],
            )
            self.content_views.add_puppet_module(
                cv_name,
                puppet_module,
                filter_term='Latest',
            )
            module = self.content_views.fetch_puppet_module(
                cv_name, puppet_module)
            self.assertIsNotNone(module)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_create_with_rh_ostree_other_contents(self):
        """Create a CV with RH ostree contents and other RH yum repos.

        :id: 4398f5cc-62de-4a11-996b-24a7ad30ad3a

        :expectedresults: CV should be created successfully with all custom
            contents

        :CaseLevel: Integration
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
            # sync repository with custom timeout
            call_entity_method_with_timeout(
                entities.Repository(id=repo_id).sync, timeout=1500)
        with Session(self) as session:
            # Create content-view
            make_contentview(session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv_name,
                [rh_ah_repo['name']],
                repo_type='ostree'
            )
            self.content_views.add_remove_repos(
                cv_name,
                [rh_st_repo['name']],
                repo_type='yum'
            )

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_publish_with_custom_ostree(self):
        """Create a CV with custom ostree contents and publish it.

        :id: c5e8d2ba-8cb2-47d8-b352-60972cf291e9

        :expectedresults: CV should be published with OStree contents

        :CaseLevel: Integration
        """
        prod = entities.Product(organization=self.organization).create()
        # Creates new ostree repository using api
        ostree_repo = entities.Repository(
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        # sync repository with custom timeout
        call_entity_method_with_timeout(ostree_repo.sync, timeout=1500)
        cv = entities.ContentView(organization=self.organization).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv.name,
                [ostree_repo.name],
                repo_type='ostree'
            )
            self.content_views.publish(cv.name)
            self.assertIsNotNone(
                self.content_views.version_search(cv.name, 'Version 1.0'))

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_published_custom_ostree_version(self):
        """Remove published custom ostree contents version from selected CV.

        :id: 949d6ee7-330a-4423-b219-550693522c7f

        :expectedresults: Published version with OStree contents should be
            removed successfully.

        :CaseLevel: Integration
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
        # sync repository with custom timeout
        call_entity_method_with_timeout(ostree_repo.sync, timeout=1500)
        cv = entities.ContentView(organization=org).create()
        cv.repository = [ostree_repo]
        cv = cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        cv_info = cv.version[0].read()
        version = 'Version {0}'.format(cv_info.version)
        with Session(self) as session:
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

        :id: 05f4ddc8-a3ad-4caf-b417-3b437b48fa47

        :expectedresults: CV should be promoted with custom OStree contents

        :CaseLevel: Integration
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
        # sync repository with custom timeout
        call_entity_method_with_timeout(ostree_repo.sync, timeout=1500)
        cv = entities.ContentView(organization=self.organization).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv.name,
                [ostree_repo.name],
                repo_type='ostree'
            )
            self.content_views.publish(cv.name)
            self.assertIsNotNone(
                self.content_views.version_search(cv.name, 'Version 1.0'))
            status = self.content_views.promote(
                cv.name, 'Version 1.0', lc_env.name)
            self.assertIn('Promoted to {}'.format(lc_env.name), status)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @upgrade
    @tier2
    def test_positive_remove_promoted_custom_ostree_contents(self):
        """Remove promoted custom ostree contents from selected environment of
        CV.

        :id: a66c8a9e-953e-41a5-aaac-9d9473a3d9fc

        :expectedresults: Promoted custom OStree contents should be removed
            successfully

        :CaseLevel: Integration
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
        # sync repository with custom timeout
        call_entity_method_with_timeout(ostree_repo.sync, timeout=1500)
        cv = entities.ContentView(organization=org).create()
        cv.repository = [ostree_repo]
        cv = cv.update(['repository'])
        cv.publish()
        cv = cv.read()
        cv_info = cv.version[0].read()
        version = 'Version {0}'.format(cv_info.version)
        lc_env = entities.LifecycleEnvironment(organization=org).create()
        promote(cv.version[0], lc_env.id)

        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @upgrade
    @tier2
    def test_positive_publish_promote_with_custom_ostree_and_other(self):
        """Create a CV with ostree as well as yum and puppet type contents and
        publish and promote them to next environment.

        :id: cf86f9bc-e32a-4048-b793-fe6e9447f7e4

        :expectedresults: CV should be published and promoted with custom
            OStree and all other contents

        :CaseLevel: Integration
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
        # sync repository with custom timeout
        call_entity_method_with_timeout(ostree_repo.sync, timeout=1500)
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
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.content_views.add_puppet_module(
                cv.name,
                puppet_module,
                filter_term='Latest',
            )
            module = self.content_views.fetch_puppet_module(
                cv.name, puppet_module)
            self.assertIsNotNone(module)
            self.content_views.publish(cv.name)
            self.assertIsNotNone(
                self.content_views.version_search(cv.name, 'Version 1.0'))
            status = self.content_views.promote(
                cv.name, 'Version 1', lc_env.name)
            self.assertIn('Promoted to {}'.format(lc_env.name), status)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_published_version_of_mixed_contents(self):
        """Remove mixed(ostree, yum, puppet, docker) published content version
        from selected CV.

        :id: b4d69aff-b667-43df-ac1f-28c58c73d846

        :expectedresults: Published version with mixed(ostree, yum, puppet,
            docker) contents should be removed successfully.

        :CaseLevel: Integration
        """
        prod = entities.Product(organization=self.organization).create()
        # Creates new ostree repository using api
        ostree_repo = entities.Repository(
            content_type='ostree',
            url=FEDORA23_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        # sync repository with custom timeout
        call_entity_method_with_timeout(ostree_repo.sync, timeout=1500)
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
        with Session(self) as session:
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

        :id: 4b5f487d-9de9-4645-8d73-7272f564eb75

        :expectedresults: CV should be published with RH OStree contents

        :CaseLevel: Integration
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
        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            # Add repository to selected CV
            self.content_views.add_remove_repos(
                cv.name,
                [rh_ah_repo['name']],
                repo_type='ostree'
            )
            self.content_views.publish(cv.name)
            self.assertIsNotNone(
                self.content_views.version_search(cv.name, 'Version 1.0'))

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_published_rh_ostree_version(self):
        """Remove published rh ostree contents version from selected CV.

        :id: a5767568-df3a-43c0-beb7-474c82a445d4

        :expectedresults: Published version with RH OStree contents should be
            removed successfully.

        :CaseLevel: Integration
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
        with Session(self) as session:
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

        :id: 19b7a33f-d13e-454b-bfee-295296e78967

        :expectedresults: CV should be promoted with RH OStree contents

        :caseautomation: notautomated

        :CaseLevel: Integration
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
        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            status = self.content_views.promote(cv.name, version, lc_env.name)
            self.assertIn('Promoted to {}'.format(lc_env.name), status)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier2
    def test_positive_remove_promoted_rh_ostree_contents(self):
        """Remove promoted rh ostree contents from selected environment of CV.

        :id: 9e49e470-8b30-4941-9868-23d9718aaad9

        :expectedresults: Promoted rh OStree contents should be removed
            successfully

        :CaseLevel: Integration
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
        with Session(self) as session:
            session.nav.go_to_select_org(org.name)
            self.content_views.delete_version(cv.name, version)
            self.content_views.check_progress_bar_status(version)
            self.content_views.validate_version_deleted(cv.name, version)

    @run_in_one_thread
    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @upgrade
    @tier2
    def test_positive_publish_promote_with_rh_ostree_and_other(self):
        """Create a CV with rh ostree as well as rh yum contents and
        publish, promote them to next environment.

        :id: f1849f6a-6ad6-432f-a70c-7d61079f482a

        :expectedresults: CV should be published and promoted with rh ostree
            and all other contents

        :CaseLevel: Integration
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
            # sync repository with custom timeout
            call_entity_method_with_timeout(
                entities.Repository(id=repo_id).sync, timeout=1500)

        cv = entities.ContentView(organization=org).create()
        with Session(self) as session:
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
                self.content_views.version_search(cv.name, 'Version 1.0'))
            status = self.content_views.promote(
                cv.name, 'Version 1', lc_env.name)
            self.assertIn('Promoted to {}'.format(lc_env.name), status)

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_promote_CV_with_custom_user_role_and_filters(self):
        """Publish and promote cv with user with custom role and filter

        :id: a07fe3df-8645-4a0c-8c56-3f8314ae4878

        :expectedresults: CV should be published and promoted successfully

        :CaseLevel: Integration
        """
        myrole = get_role_by_bz(1306359)
        username = gen_string('alpha')
        user_password = gen_string('alphanumeric')
        entities.User(
            login=username,
            role=[myrole],
            password=user_password,
            organization=[self.organization],
        ).create()
        repo_name = gen_string('alpha')
        env_name = gen_string('alpha')
        cv_name = gen_string('alpha')
        with Session(self, username, user_password) as session:
            # Create Life-cycle environment
            make_lifecycle_environment(session, name=env_name)
            # Creates a CV along with product and sync'ed repository
            self.setup_to_create_cv(repo_name=repo_name)
            # Create content-view
            make_contentview(session, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # Add repository to selected CV
            self.content_views.add_remove_repos(cv_name, [repo_name])
            # Publish and promote CV to next environment
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            status = self.content_views.promote(cv_name, 'Version 1', env_name)
            self.assertIn('Promoted to {}'.format(env_name), status)

    @run_only_on('sat')
    @tier2
    def test_positive_create_puppet_env_with_module(self):
        """Check that puppet environment will be created automatically once
        content view that contains puppet module is published, no matter
        whether 'Force Puppet' option is enabled or disabled for that content
        view

        :id: af553367-e621-41e8-86cb-091ba7ba6c0a

        :customerscenario: true

        :expectedresults: puppet environment is created and has expected name

        :BZ: 1437110

        :CaseLevel: Integration
        """
        repo_url = FAKE_0_PUPPET_REPO
        puppet_module = 'httpd'
        self.setup_to_create_cv(
            repo_url=repo_url, repo_type=REPO_TYPE['puppet'])
        with Session(self) as session:
            for force_value in [True, False]:
                cv_name = gen_string('alpha')
                # Create content-view
                make_contentview(
                    session, org=self.organization.name, name=cv_name)
                self.content_views.update(
                    name=cv_name, force_puppet=force_value)
                self.content_views.add_puppet_module(
                    cv_name,
                    puppet_module,
                    filter_term='Latest',
                )
                self.content_views.publish(cv_name)
                # Form environment name variable for our test
                env_name = 'KT_{0}_{1}_{2}_{3}'.format(
                    self.organization.name,
                    ENVIRONMENT,
                    cv_name,
                    str(
                        entities.ContentView(
                            name=cv_name,
                            organization=self.organization,
                        ).search()[0].id
                    ),
                )
                self.assertIsNotNone(self.environment.search(env_name))

    @run_only_on('sat')
    @tier2
    def test_negative_create_puppet_env_without_module(self):
        """Check that puppet environment will not be created in case content
        view does not contains puppet module and 'Force Puppet' option is not
        enabled for that content view

        :id: 375e70d9-25a3-4f3f-af2e-cb3c09c57db7

        :expectedresults: puppet environment is not created automatically

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        with Session(self) as session:
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.content_views.update(name=cv_name, force_puppet=False)
            self.content_views.publish(cv_name)
            # Form environment name variable for our test
            env_name = 'KT_{0}_{1}_{2}_{3}'.format(
                self.organization.name,
                ENVIRONMENT,
                cv_name,
                str(
                    entities.ContentView(
                        name=cv_name,
                        organization=self.organization,
                    ).search()[0].id
                ),
            )
            self.assertIsNone(self.environment.search(env_name))

    @run_only_on('sat')
    @tier2
    def test_positive_create_puppet_env_without_module_and_force(self):
        """Check that puppet environment will be created automatically even if
        content view  does not contain puppet module, but has 'Force Puppet'
        option enabled

        :id: ce6ef30b-f304-4f7f-8d53-fb4deaee0419

        :expectedresults: puppet environment is created and has expected name

        :BZ: 1437110

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        with Session(self) as session:
            make_contentview(session, org=self.organization.name, name=cv_name)
            self.content_views.update(name=cv_name, force_puppet=True)
            self.content_views.publish(cv_name)
            # Form environment name variable for our test
            env_name = 'KT_{0}_{1}_{2}_{3}'.format(
                self.organization.name,
                ENVIRONMENT,
                cv_name,
                str(
                    entities.ContentView(
                        name=cv_name,
                        organization=self.organization,
                    ).search()[0].id
                ),
            )
            self.assertIsNotNone(self.environment.search(env_name))

    @run_only_on('sat')
    @tier2
    def test_positive_remove_cv_version_from_default_env(self):
        """Remove content view version from Library environment

        :id: 43c83c15-c883-45a7-be05-d9b26da99e3c

        :Steps:

            1. Create a content view
            2. Add a yum repo to it
            3. Publish content view
            4. remove the published version from Library environment

        :expectedresults: content view version is removed from Library
            environment

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        # create a new organization
        org = entities.Organization().create()
        # create a yum repository
        self.setup_to_create_cv(
            repo_name=repo_name,
            repo_url=FAKE_0_YUM_REPO,
            org_id=org.id
        )
        with Session(self) as session:
            # create a content view
            make_contentview(
                session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the repository to the created content view
            self.content_views.add_remove_repos(cv_name, [repo_name])
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            self.assertEqual(
                self._get_cv_version_environments(version), [ENVIRONMENT])
            # remove the content view version from Library environment
            self.content_views.remove_version_from_environments(
                cv_name, version, [ENVIRONMENT])
            self.assertEqual(self._get_cv_version_environments(version), [])

    @run_only_on('sat')
    @tier2
    def test_positive_remove_renamed_cv_version_from_default_env(self):
        """Remove version of renamed content view from Library environment

        :id: bd5ca409-f3ab-43b5-bb63-3b747aa75506

        :Steps:

            1. Create a content view
            2. Add a yum repo to the content view
            3. Publish the content view
            4. Rename the content view
            5. remove the published version from Library environment

        :expectedresults: content view version is removed from Library
            environment

        :CaseLevel: Integration
        """
        cv_name = gen_string('alpha')
        new_cv_name = gen_string('alpha')
        repo_name = gen_string('alpha')
        # create a new organization
        org = entities.Organization().create()
        # create a yum repository
        self.setup_to_create_cv(
            repo_name=repo_name,
            repo_url=FAKE_0_YUM_REPO,
            org_id=org.id
        )
        with Session(self) as session:
            # create a content view
            make_contentview(
                session, org=org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            # add the repository to the created content view
            self.content_views.add_remove_repos(cv_name, [repo_name])
            # publish the content view
            version = self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, version))
            # rename the content view
            self.content_views.update(cv_name, new_cv_name)
            self.assertIsNone(self.content_views.search(cv_name))
            # ensure the cv exits with the new name
            cv_element = self.content_views.search(new_cv_name)
            self.assertIsNotNone(cv_element)
            # open the content view
            self.content_views.click(cv_element)
            self.assertEqual(
                self._get_cv_version_environments(version), [ENVIRONMENT])
            # remove the content view version from Library environment
            self.content_views.remove_version_from_environments(
                new_cv_name, version, [ENVIRONMENT])
            self.assertEqual(self._get_cv_version_environments(version), [])

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
