# -*- encoding: utf-8 -*-
"""Test class for Repository UI

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import time

from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests, ssh
from robottelo.api.utils import create_role_permissions, upload_manifest
from robottelo.constants import (
    CHECKSUM_TYPE,
    DOCKER_REGISTRY_HUB,
    DOWNLOAD_POLICIES,
    FAKE_0_PUPPET_REPO,
    FAKE_1_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    FAKE_YUM_DRPM_REPO,
    FAKE_YUM_SRPM_REPO,
    FEDORA22_OSTREE_REPO,
    FEDORA23_OSTREE_REPO,
    INVALID_URL,
    PRDS,
    PUPPET_MODULE_NTP_PUPPETLABS,
    REPO_DISCOVERY_URL,
    REPO_TAB,
    REPO_TYPE,
    REPOS,
    RPM_TO_UPLOAD,
    SAT6_TOOLS_TREE,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.datafactory import (
    generate_strings_list,
    invalid_values_list,
    valid_docker_repository_names,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    tier4,
    upgrade,
)
from robottelo.decorators.host import skip_if_os
from robottelo.helpers import get_data_file, read_data_file
from robottelo.host_info import get_host_os_version
from robottelo.test import UITestCase
from robottelo.ui.base import UINoSuchElementError
from robottelo.ui.factory import make_contentview, make_repository, set_context
from robottelo.ui.locators import (
    common_locators,
    locators,
    menu_locators,
    tab_locators,
)
from robottelo.ui.session import Session
from selenium.common.exceptions import NoSuchElementException


class RepositoryTestCase(UITestCase):
    """Implements Repos tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(RepositoryTestCase, cls).setUpClass()
        # create instances to be shared across the sessions
        cls.session_loc = entities.Location().create()
        cls.session_prod = entities.Product(
            organization=cls.session_org).create()

    @classmethod
    def set_session_org(cls):
        """Creates new organization to be used for current session the
        session_user will login automatically with this org in context
        """
        cls.session_org = entities.Organization().create()

    def setup_navigate_syncnow(self, session, prd_name, repo_name):
        """Helps with Navigation for syncing via the repos page."""
        session.nav.go_to_select_org(self.session_org.name, force=False)
        session.nav.go_to_products()
        session.nav.click(locators['repo.select'] % prd_name)
        session.nav.click(locators['repo.select_checkbox'] % repo_name)
        session.nav.click(locators['repo.sync_now'])

    def prd_sync_is_ok(self, repo_name):
        """Asserts whether the sync Result is successful."""
        self.repository.click(tab_locators['prd.tab_tasks'])
        self.repository.click(locators['repo.select_event'] % repo_name)
        timeout = time.time() + 60 * 10
        spinner = self.repository.wait_until_element(
            locators['repo.result_spinner'], 20)
        # Waits until result spinner is visible on the UI or times out
        # after 10mins
        while spinner:
            if time.time() > timeout:
                break
            spinner = self.repository.wait_until_element(
                locators['repo.result_spinner'], 3)
        result = self.repository.wait_until_element(
            locators['repo.result_event']).text
        return result == 'success'

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create repository with different names and minimal input
        parameters

        :id: 3713c811-ea80-43ce-a753-344d1dcb7486

        :expectedresults: Repository is created successfully

        :CaseImportance: Critical
        """
        prod = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search_and_click(prod.name)
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @tier2
    @upgrade
    def test_positive_create_puppet_repo_same_url_different_orgs(self):
        """Create two repos with the same URL in two different organizations.

        :id: f4cb00ed-6faf-4c79-9f66-76cd333299cb

        :expectedresults: Repositories are created and puppet modules are
            visible from different organizations.

        :CaseLevel: Integration
        """
        url = 'https://omaciel.fedorapeople.org/f4cb00ed/'
        # Create first repository
        repo = entities.Repository(
            url=url,
            product=self.session_prod,
            content_type=REPO_TYPE['puppet'],
        ).create()
        repo.sync()
        # Create second repository
        org = entities.Organization().create()
        product = entities.Product(organization=org).create()
        new_repo = entities.Repository(
            url=url,
            product=product,
            content_type=REPO_TYPE['puppet'],
        ).create()
        new_repo.sync()
        with Session(self) as session:
            # Check packages number in first repository
            self.products.search_and_click(self.session_prod.name)
            self.assertIsNotNone(self.repository.search(repo.name))
            self.repository.search_and_click(repo.name)
            number = self.repository.find_element(
                locators['repo.fetch_puppet_modules'])
            self.assertEqual(int(number.text), 1)
            # Check packages number in first repository
            session.nav.go_to_select_org(org.name)
            self.products.search_and_click(product.name)
            self.assertIsNotNone(self.repository.search(new_repo.name))
            self.repository.search_and_click(new_repo.name)
            number = self.repository.find_element(
                locators['repo.fetch_puppet_modules'])
            self.assertEqual(int(number.text), 1)

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_create_repo_with_checksum(self):
        """Create repository with checksum type as sha256.

        :id: 06f37bb3-b0cf-4f1f-ae12-df13a6a7eaab

        :expectedresults: Repository is created with expected checksum type.

        :CaseImportance: Critical
        """
        checksum = CHECKSUM_TYPE[u'sha256']
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            for repo_name in generate_strings_list(
                    exclude_types=['numeric'], bug_id=1467722):
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search_and_click(product.name)
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                        repo_checksum=checksum,
                    )
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'checksum', checksum))

    @run_only_on('sat')
    @tier1
    def test_positive_create_repo_with_upstream_credentials(self):
        """Create repository with upstream username and password parameters

        :id: e6ca6e08-a2f7-4a67-9499-c4b12815d916

        :expectedresults: Repository is created with expected username and
            password field is hidden

        :CaseImportance: Critical
        """
        repo_name = gen_string('alpha')
        repo_username = gen_string('alpha')
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
                upstream_username=repo_username,
                upstream_password=gen_string('alpha')
            )
            self.assertTrue(self.repository.validate_field(
                repo_name, 'upstream_username', repo_username))
            self.products.search_and_click(product.name)
            self.assertTrue(self.repository.validate_field(
                repo_name, 'upstream_password', '******'))

    @run_only_on('sat')
    @tier1
    def test_positive_clear_repo_upstream_credentials(self):
        """Create repository with upstream username and password parameters.
        Then remove these parameters

        :id: 66977094-946f-401b-a8d4-5da5412cdacf

        :expectedresults: Upstream username and password parameters can be
            removed from repository

        :BZ: 1433481

        :CaseImportance: Critical
        """
        repo_name = gen_string('alpha')
        repo_username = gen_string('alpha')
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
                upstream_username=repo_username,
                upstream_password=gen_string('alpha')
            )
            self.repository.update(repo_name, new_upstream_username='')
            self.repository.click(locators['repo.upstream_password_clear'])
            for property_name in ['upstream_username', 'upstream_password']:
                self.products.search_and_click(product.name)
                self.assertTrue(self.repository.validate_field(
                    repo_name, property_name, ''))

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_create_as_non_admin_user_with_cv_published(self):
        """Create a repository as a non admin user in a product that already
        contain a repository that is used in a published content view.

        :id: 407864eb-50b8-4bc8-bbc7-0e6f8136d89f

        :expectedresults: New repository successfully created by non admin user

        :BZ: 1447829

        :CaseLevel: Integration
        """
        user_login = gen_string('alpha')
        user_password = gen_string('alphanumeric')
        repo_name = gen_string('alpha')
        user_permissions = {
            None: ['access_dashboard'],
            'Katello::Product': [
                'view_products',
                'create_products',
                'edit_products',
                'destroy_products',
                'sync_products',
                'export_products',
            ],
        }
        role = entities.Role().create()
        create_role_permissions(role, user_permissions)
        entities.User(
            login=user_login,
            password=user_password,
            role=[role],
            admin=False,
            default_organization=self.session_org,
            organization=[self.session_org],
        ).create()
        product = entities.Product(organization=self.session_org).create()
        repo = entities.Repository(
            product=product, url=FAKE_2_YUM_REPO).create()
        repo.sync()
        content_view = entities.ContentView(
            organization=self.session_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        with Session(self, user_login, user_password) as session:
            # ensure that the created user is not a global admin user
            # check administer->users page
            with self.assertRaises(UINoSuchElementError):
                session.nav.go_to_users()
            # ensure that the created user has only the assigned
            # permissions, check that hosts menu tab does not exist
            self.assertIsNone(
                self.content_views.wait_until_element(
                    menu_locators['menu.hosts'], timeout=5)
            )
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create repository with invalid names

        :id: 385d0222-6466-4bc0-9686-b215f41e4274

        :expectedresults: Repository is not created

        :CaseImportance: Critical
        """
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        for repo_name in invalid_values_list(interface='ui'):
            with self.subTest(repo_name):
                with Session(self) as session:
                    set_context(session, org=self.session_org.name)
                    self.products.search_and_click(product.name)
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    invalid = self.products.wait_until_element(
                        common_locators['common_invalid'])
                    self.assertIsNotNone(invalid)

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_names(self):
        """Try to create two repositories with same name

        :id: f9515a61-0c5e-4767-9fc9-b17d440418d8

        :expectedresults: Repository is not created

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertTrue(self.products.wait_until_element(
                common_locators['common_invalid']))

    @run_only_on('sat')
    @tier1
    def test_positive_update_url(self):
        """Update content repository with new URL

        :id: cb864338-9d18-4e18-a2ee-37f22e7036b8

        :expectedresults: Repository is updated with expected url value

        :CaseImportance: Critical
        """
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            for repo_name in generate_strings_list(
                    exclude_types=['numeric'], bug_id=1467722):
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search_and_click(product.name)
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'url', FAKE_1_YUM_REPO))
                    self.products.search_and_click(product.name)
                    self.repository.update(repo_name, new_url=FAKE_2_YUM_REPO)
                    self.products.search_and_click(product.name)
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'url', FAKE_2_YUM_REPO))

    @run_only_on('sat')
    @tier1
    def test_positive_update_gpg(self):
        """Update content repository with new gpg-key

        :id: 51da6572-02d0-43d7-96cc-895b5bebfadb

        :expectedresults: Repository is updated with new gpg key

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        key_1_content = read_data_file(VALID_GPG_KEY_FILE)
        key_2_content = read_data_file(VALID_GPG_KEY_BETA_FILE)
        # Create two new GPGKey's
        gpgkey_1 = entities.GPGKey(
            content=key_1_content,
            organization=self.session_org,
        ).create()
        gpgkey_2 = entities.GPGKey(
            content=key_2_content,
            organization=self.session_org,
        ).create()
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
                gpg_key=gpgkey_1.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.assertTrue(self.repository.validate_field(
                repo_name, 'gpgkey', gpgkey_1.name))
            self.products.search_and_click(product.name)
            self.repository.update(repo_name, new_gpg_key=gpgkey_2.name)
            self.products.search_and_click(product.name)
            self.assertTrue(self.repository.validate_field(
                repo_name, 'gpgkey', gpgkey_2.name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_checksum_type(self):
        """Update content repository with new checksum type

        :id: eed4e77d-baa2-42c2-9774-f1bed52efe39

        :expectedresults: Repository is updated with expected checksum type.

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        checksum_default = CHECKSUM_TYPE['default']
        checksum_update = CHECKSUM_TYPE['sha1']
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.assertTrue(self.repository.validate_field(
                repo_name, 'checksum', checksum_default))
            self.products.search_and_click(product.name)
            self.repository.update(
                repo_name, new_repo_checksum=checksum_update)
            self.products.search_and_click(product.name)
            self.assertTrue(self.repository.validate_field(
                repo_name, 'checksum', checksum_update))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create content repository and then remove it

        :id: 9edc93b1-d4e5-453e-b4ee-0731df491397

        :expectedresults: Repository is deleted successfully

        :CaseImportance: Critical
        """
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            for repo_name in generate_strings_list(
                    exclude_types=['numeric'], bug_id=1467722):
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search_and_click(product.name)
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    self.repository.delete(repo_name)

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_delete_puppet_repo_associated_with_cv(self):
        """Delete a puppet repo associated with a content view - BZ#1271000

        :id: 72639e14-4089-4f40-bad7-e18021ad376f

        :Steps:

            1. Create a new product
            2. Create a new puppet repo, no sync source
            3. Upload a puppet module (say ntpd) to repo
            4. Create a CV, go to add puppet modules page
            5. Add latest version of the puppet module from Step 3
            6. View puppet repo details, it should show "Latest (Currently
                X.Y.Z)"
            7. Go back to product, drill down into repo and delete the puppet
                module from Step 3
            8. Go back to same CV puppet module details page

        :expectedresults: Proper error message saying that the puppet module
            version is not found

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_discover_repo_via_existing_product(self):
        """Create repository via repo-discovery under existing product

        :id: 9181950c-a756-456f-a46a-059e7a2add3c

        :expectedresults: Repository is discovered and created

        :CaseLevel: Integration
        """
        discovered_urls = 'fakerepo01/'
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            session.nav.go_to_products()
            self.repository.discover_repo(
                url_to_discover=REPO_DISCOVERY_URL,
                discovered_urls=[discovered_urls],
                product=product.name,
            )

    @run_only_on('sat')
    @tier2
    def test_positive_discover_repo_via_new_product(self):
        """Create repository via repo discovery under new product

        :id: dc5281f8-1a8a-4a17-b746-728f344a1504

        :expectedresults: Repository is discovered and created

        :CaseLevel: Integration
        """
        product_name = gen_string('alpha')
        discovered_urls = 'fakerepo01/'
        with Session(self) as session:
            session.nav.go_to_select_org(self.session_org.name)
            session.nav.go_to_select_loc(self.session_loc.name)
            session.nav.go_to_products()
            self.repository.discover_repo(
                url_to_discover=REPO_DISCOVERY_URL,
                discovered_urls=[discovered_urls],
                product=product_name,
                new_product=True,
            )
            self.assertIsNotNone(self.products.search(product_name))

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_sync_custom_repo_yum(self):
        """Create Custom yum repos and sync it via the repos page.

        :id: afa218f4-e97a-4240-a82a-e69538d837a1

        :expectedresults: Sync procedure for specific yum repository is
            successful

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            for repo_name in generate_strings_list(
                    exclude_types=['numeric'], bug_id=1467722):
                with self.subTest(repo_name):
                    # Creates new yum repository using api
                    entities.Repository(
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                        product=product,
                    ).create()
                    self.setup_navigate_syncnow(
                        session,
                        product.name,
                        repo_name,
                    )
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    @tier2
    def test_positive_resync_custom_repo_after_invalid_update(self):
        """Create Custom yum repo and sync it via the repos page. Then try to
        change repo url to invalid one and re-sync that repository

        :id: 089b1e41-2017-429a-9c3f-b0291007a78f

        :customerscenario: true

        :expectedresults: Repository URL is not changed to invalid value and
            resync procedure for specific yum repository is successful

        :BZ: 1487173, 1262313

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alpha')
        with Session(self) as session:
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))
            self.repository.update(repo_name, new_url=INVALID_URL)
            if not bz_bug_is_open(1487173):
                self.assertIsNotNone(self.user.wait_until_element(
                    common_locators['alert.error_sub_form']))
            self.repository.click(common_locators['cancel'])
            self.products.search_and_click(product.name)
            self.assertTrue(self.repository.validate_field(
                repo_name, 'url', FAKE_1_YUM_REPO))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_sync_custom_repo_puppet(self):
        """Create Custom puppet repos and sync it via the repos page.

        :id: 135176cc-7664-41ee-8c41-b77e193f2f22

        :expectedresults: Sync procedure for specific puppet repository is
            successful

        :CaseLevel: Integration
        """
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    # Creates new puppet repository
                    entities.Repository(
                        name=repo_name,
                        url=FAKE_0_PUPPET_REPO,
                        product=product,
                        content_type=REPO_TYPE['puppet'],
                    ).create()
                    self.setup_navigate_syncnow(
                        session,
                        product.name,
                        repo_name,
                    )
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_sync_custom_repo_docker(self):
        """Create Custom docker repos and sync it via the repos page.

        :id: 942e0b4f-3524-4f00-812d-bdad306f81de

        :expectedresults: Sync procedure for specific docker repository is
            successful

        :CaseLevel: Integration
        """
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            for repo_name in valid_docker_repository_names():
                with self.subTest(repo_name):
                    # Creates new docker repository
                    entities.Repository(
                        name=repo_name,
                        url=DOCKER_REGISTRY_HUB,
                        product=product,
                        content_type=REPO_TYPE['docker'],
                    ).create()
                    self.setup_navigate_syncnow(
                        session, product.name, repo_name
                    )
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    @tier2
    def test_positive_resynchronize_rpm_repo(self):
        """Check that repository content is resynced after packages were
        removed from repository

        :id: dc415563-c9b8-4e3c-9d2a-f4ac251c7d35

        :expectedresults: Repository has updated non-zero package count

        :CaseLevel: Integration

        :BZ: 1318004
        """
        with Session(self) as session:
            repo = entities.Repository(
                url=FAKE_1_YUM_REPO,
                content_type='yum',
                product=self.session_prod,
            ).create()
            self.setup_navigate_syncnow(
                session,
                self.session_prod.name,
                repo.name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo.name))
            # Check packages count
            count = self.repository.fetch_content_count(repo.name, 'packages')
            self.assertGreaterEqual(count, 1)
            # Remove packages
            self.products.search_and_click(self.session_prod.name)
            self.repository.remove_content(repo.name)
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo.name, 'packages')
            self.assertEqual(count, 0)
            # Sync it again
            self.setup_navigate_syncnow(
                session,
                self.session_prod.name,
                repo.name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo.name))
            # Check packages number
            count = self.repository.fetch_content_count(repo.name, 'packages')
            self.assertGreaterEqual(count, 1)

    @run_only_on('sat')
    @tier2
    def test_positive_resynchronize_puppet_repo(self):
        """Check that repository content is resynced after packages were
        removed from repository

        :id: c82dfe9d-aa1c-4922-ab3f-5d66ba8375c5

        :expectedresults: Repository has updated non-zero package count

        :CaseLevel: Integration

        :BZ: 1318004
        """
        with Session(self) as session:
            repo = entities.Repository(
                url=FAKE_1_PUPPET_REPO,
                content_type='puppet',
                product=self.session_prod,
            ).create()
            self.setup_navigate_syncnow(
                session,
                self.session_prod.name,
                repo.name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo.name))
            # Check packages count
            count = self.repository.fetch_content_count(repo.name, 'puppet')
            self.assertGreaterEqual(count, 1)
            # Remove packages
            self.products.search_and_click(self.session_prod.name)
            self.repository.remove_content(repo.name)
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo.name, 'puppet')
            self.assertEqual(count, 0)
            # Sync repo again
            self.setup_navigate_syncnow(
                session,
                self.session_prod.name,
                repo.name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo.name))
            # Check packages count
            count = self.repository.fetch_content_count(repo.name, 'puppet')
            self.assertGreaterEqual(count, 1)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_create_custom_ostree_repo(self):
        """Create Custom ostree repository.

        :id: 852cccdc-7289-4d2f-b23a-7caad2dfa195

        :expectedresults: Create custom ostree repository should be successful

        :CaseImportance: Critical
        """
        prod = entities.Product(organization=self.session_org).create()
        with Session(self) as session:
            for repo_name in generate_strings_list(
                    exclude_types=['numeric'], bug_id=1467722):
                with self.subTest(repo_name):
                    session.nav.go_to_select_org(
                        self.session_org.name, force=False)
                    self.products.search_and_click(prod.name)
                    make_repository(
                        session,
                        name=repo_name,
                        repo_type=REPO_TYPE['ostree'],
                        url=FEDORA23_OSTREE_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    @upgrade
    def test_positive_delete_custom_ostree_repo(self):
        """Delete custom ostree repository.

        :id: 87dcb236-4eb4-4897-9c2a-be1d0f4bc3e7

        :expectedresults: Delete custom ostree repository should be successful

        :CaseImportance: Critical
        """
        prod = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        # Creates new ostree repository using api
        entities.Repository(
            name=repo_name,
            content_type='ostree',
            url=FEDORA22_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.delete(repo_name)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_update_custom_ostree_repo_name(self):
        """Update custom ostree repository name.

        :id: 098ee88f-6cdb-45e0-850a-e1b71662f7ab

        :Steps: Update repo name

        :expectedresults: ostree repo name should be updated successfully

        :CaseImportance: Critical
        """
        prod = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        new_repo_name_length = None
        if bz_bug_is_open(1467722):
            new_repo_name_length = 9
        new_repo_name = gen_string('numeric', length=new_repo_name_length)
        # Creates new ostree repository using api
        entities.Repository(
            name=repo_name,
            content_type='ostree',
            url=FEDORA22_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.update(
                repo_name, new_name=new_repo_name)
            self.products.search_and_click(prod.name)
            self.assertIsNotNone(self.repository.search(new_repo_name))

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_update_custom_ostree_repo_url(self):
        """Update custom ostree repository url.

        :id: dfd392f9-6f1d-4d87-a43b-ced40606b8c2

        :Steps: Update ostree repo URL

        :expectedresults: ostree repo URL should be updated successfully

        :CaseImportance: Critical
        """
        prod = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        # Creates new ostree repository using api
        entities.Repository(
            name=repo_name,
            content_type='ostree',
            url=FEDORA22_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.search_and_click(prod.name)
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.update(
                repo_name,
                new_url=FEDORA23_OSTREE_REPO
            )
            self.products.search_and_click(prod.name)
            # Validate the new repo URL
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'url', FEDORA23_OSTREE_REPO
                )
            )

    @tier1
    def test_positive_download_policy_displayed_for_yum_repos(self):
        """Verify that YUM repositories can be created with download policy

        :id: 8037a68b-66b8-4b42-a80b-fb08495f948d

        :expectedresults: Dropdown for download policy is displayed for yum
            repo

        :CaseImportance: Critical
        """
        with Session(self) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.search_and_click(self.session_prod.name)
            self.repository.navigate_to_entity()
            self.repository.click(locators['repo.new'])
            self.repository.assign_value(
                common_locators['name'], gen_string('alphanumeric'))
            self.repository.assign_value(locators['repo.type'], 'yum')
            self.assertIsNotNone(
                self.repository.find_element(locators['repo.download_policy'])
            )

    @tier1
    def test_positive_create_with_download_policy(self):
        """Create YUM repositories with available download policies

        :id: 8099fb98-963d-4370-bf51-6807f5efd6d3

        :expectedresults: YUM repository with a download policy is created

        :CaseImportance: Critical
        """
        repo_name = gen_string('alpha')
        with Session(self) as session:
            for policy in DOWNLOAD_POLICIES.values():
                with self.subTest(policy):
                    self.products.search_and_click(self.session_prod.name)
                    make_repository(
                        session,
                        name=repo_name,
                        repo_type=REPO_TYPE['yum'],
                        download_policy=policy
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @tier1
    def test_positive_create_with_default_download_policy(self):
        """Verify if the default download policy is assigned when creating
        a YUM repo without `download_policy` field

        :id: ee7637fe-3864-4b2f-a153-14312658d75a

        :expectedresults: YUM repository with a default download policy

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        default_dl_policy = entities.Setting().search(
            query={'search': 'name=default_download_policy'}
        )
        self.assertTrue(default_dl_policy and
                        DOWNLOAD_POLICIES.get(default_dl_policy[0].value))
        default_dl_policy = DOWNLOAD_POLICIES.get(default_dl_policy[0].value)
        with Session(self) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.search_and_click(self.session_prod.name)
            make_repository(session, name=repo_name, repo_type='yum')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', default_dl_policy
                )
            )

    def _create_yum_repo_with_download_policy(self, name, download_policy):
        """Helper method to create a new yum repository using API"""
        return entities.Repository(
            name=name,
            content_type='yum',
            product=self.session_prod,
            download_policy=download_policy.lower().replace(' ', '_')
        ).create()

    # All *_update_to_* tests below could be grouped in to a single test_case
    # using a loop But for clarity we decided to keep as separated tests

    @tier1
    @upgrade
    def test_positive_create_immediate_update_to_on_demand(self):
        """Update `immediate` download policy to `on_demand` for a newly
        created YUM repository

        :id: 4aa4d914-74f3-4c2e-9e8a-6e1b7fdb34ea

        :expectedresults: immediate download policy is updated to on_demand

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Immediate')
        with Session(self):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='On Demand')
            self.products.search_and_click(self.session_prod.name)
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'On Demand'
                )
            )

    @tier1
    @upgrade
    def test_positive_create_immediate_update_to_background(self):
        """Update `immediate` download policy to `background` for a newly
        created YUM repository

        :id: d61bf6b6-6485-4d3a-816a-b533e96deb69

        :expectedresults: immediate download policy is updated to background

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Immediate')
        with Session(self):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Background')
            self.products.search_and_click(self.session_prod.name)
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Background'
                )
            )

    @tier1
    def test_positive_create_on_demand_update_to_immediate(self):
        """Update `on_demand` download policy to `immediate` for a newly
        created YUM repository

        :id: 51cac66d-05a4-47da-adb5-d2909725457e

        :expectedresults: on_demand download policy is updated to immediate

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'On Demand')
        with Session(self):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Immediate')
            self.products.search_and_click(self.session_prod.name)
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Immediate'
                )
            )

    @tier1
    def test_positive_create_on_demand_update_to_background(self):
        """Update `on_demand` download policy to `background` for a newly
        created YUM repository

        :id: 25b5ba4e-a1cf-41c2-8ca8-4fa3153570f8

        :expectedresults: on_demand download policy is updated to background

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'On Demand')
        with Session(self):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Background')
            self.products.search_and_click(self.session_prod.name)
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Background'
                )
            )

    @tier1
    @upgrade
    def test_positive_create_background_update_to_immediate(self):
        """Update `background` download policy to `immediate` for a newly
        created YUM repository

        :id: 7a6efe70-8edb-4fa8-b2a4-93762d6e4bc5

        :expectedresults: background download policy is updated to immediate

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Background')
        with Session(self):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Immediate')
            self.products.search_and_click(self.session_prod.name)
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Immediate'
                )
            )

    @tier1
    def test_positive_create_background_update_to_on_demand(self):
        """Update `background` download policy to `on_demand` for a newly
        created YUM repository

        :id: d36b96b1-6e09-455e-82e7-36a23f8c6c06

        :expectedresults: background download policy is updated to on_demand

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Background')
        with Session(self):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='On Demand')
            self.products.search_and_click(self.session_prod.name)
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'On Demand'
                )
            )

    @tier1
    def test_negative_create_with_invalid_download_policy(self):
        """Verify that YUM repository cannot be created with invalid download
        policy

        :id: dded6dda-3576-4485-8f3c-bb7c091e7ff2

        :expectedresults: YUM repository is not created with invalid download
            policy

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        with Session(self) as session:
            self.products.search_and_click(self.session_prod.name)
            invalid = gen_string('alpha', 5)
            msg = "Could not locate element with visible text: %s" % invalid
            with self.assertRaisesRegexp(NoSuchElementException, msg):
                make_repository(
                    session,
                    name=repo_name,
                    repo_type='yum',
                    download_policy=invalid
                )

    @tier1
    def test_negative_update_to_invalid_download_policy(self):
        """Verify that YUM repository cannot be updated to invalid download
        policy

        :id: e6c725f2-172e-49f6-ae92-c56af8a1200b

        :expectedresults: YUM repository is not updated to invalid download
            policy

        :CaseImportance: Critical
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Immediate')
        with Session(self):
            self.products.search_and_click(self.session_prod.name)
            invalid = gen_string('alpha', 5)
            msg = "Could not locate element with visible text: %s" % invalid
            with self.assertRaisesRegexp(NoSuchElementException, msg):
                self.repository.update(
                    repo_name,
                    download_policy=invalid
                )

    @tier1
    def test_negative_download_policy_displayed_for_non_yum_repo(self):
        """Verify that non-YUM repositories cannot be created with download
        policy

        :id: 47d55251-5f89-443d-b980-a441da34e205

        :expectedresults: Dropdown for download policy is not displayed for
            non-yum repo

        :CaseImportance: Critical
        """
        os_version = get_host_os_version()
        # ostree is not supported for rhel6 so the following check
        if os_version.startswith('RHEL6'):
            non_yum_repo_types = [
                repo_type for repo_type in REPO_TYPE.values()
                if repo_type != 'yum' and repo_type != 'ostree'
            ]
        else:
            non_yum_repo_types = [
                repo_type for repo_type in REPO_TYPE.values()
                if repo_type != 'yum'
            ]
        with Session(self):
            for content_type in non_yum_repo_types:
                self.products.search_and_click(self.session_prod.name)
                with self.subTest(content_type):
                    self.repository.navigate_to_entity()
                    self.repository.click(locators['repo.new'])
                    self.repository.assign_value(
                        common_locators['name'], gen_string('alphanumeric'))
                    self.repository.assign_value(
                        locators['repo.type'], content_type)
                    self.assertIsNone(
                        self.repository.find_element(
                            locators['repo.download_policy']
                        )
                    )

    @skip_if_bug_open('bugzilla', 1378442)
    @tier2
    def test_positive_srpm_sync(self):
        """Synchronize repository with SRPMs

        :id: 1967a540-a265-4046-b87b-627524b63688

        :expectedresults: srpms can be listed in repository

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        with Session(self) as session:
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_SRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
            '/custom/{}/{}/ | grep .src.rpm'
            .format(
                self.session_org.label,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @skip_if_bug_open('bugzilla', 1378442)
    @tier2
    def test_positive_srpm_sync_publish_cv(self):
        """Synchronize repository with SRPMs, add repository to content view
        and publish content view

        :id: 2a57cbde-c616-440d-8bcb-6e18bd2d5c5f

        :expectedresults: srpms can be listed in content view

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self) as session:
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_SRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))

            make_contentview(session, org=self.session_org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
            '/1.0/custom/{}/{}/ | grep .src.rpm'
            .format(
                self.session_org.label,
                cv_name,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @skip_if_bug_open('bugzilla', 1378442)
    @tier2
    @upgrade
    def test_positive_srpm_sync_publish_promote_cv(self):
        """Synchronize repository with SRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        :id: 4563d1c1-cdce-4838-a67f-c0a5d4e996a6

        :expectedresults: srpms can be listed in content view in proper
            lifecycle environment

        :CaseLevel: Integration
        """
        lce = entities.LifecycleEnvironment(
            organization=self.session_org).create()
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self) as session:
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_SRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))

            make_contentview(session, org=self.session_org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            status = self.content_views.promote(cv_name, 'Version 1', lce.name)
            self.assertIn('Promoted to {}'.format(lce.name), status)
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}/'
            ' | grep .src.rpm'
            .format(
                self.session_org.label,
                lce.name,
                cv_name,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @skip_if_bug_open('bugzilla', 1378442)
    @tier2
    def test_positive_drpm_sync(self):
        """Synchronize repository with DRPMs

        :id: 5e703d9a-ea26-4062-9d5c-d31bfbe87417

        :expectedresults: drpms can be listed in repository

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        with Session(self) as session:
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_DRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/Library'
            '/custom/{}/{}/drpms/ | grep .drpm'
            .format(
                self.session_org.label,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @skip_if_bug_open('bugzilla', 1378442)
    @tier2
    def test_positive_drpm_sync_publish_cv(self):
        """Synchronize repository with DRPMs, add repository to content view
        and publish content view

        :id: cffa862c-f972-4aa4-96b2-5a4513cb3eef

        :expectedresults: drpms can be listed in content view

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self) as session:
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_DRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))

            make_contentview(session, org=self.session_org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/content_views/{}'
            '/1.0/custom/{}/{}/drpms/ | grep .drpm'
            .format(
                self.session_org.label,
                cv_name,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @skip_if_bug_open('bugzilla', 1378442)
    @tier2
    @upgrade
    def test_positive_drpm_sync_publish_promote_cv(self):
        """Synchronize repository with DRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        :id: e33ee07c-4677-4be8-bd53-73689edfda34

        :expectedresults: drpms can be listed in content view in proper
            lifecycle environment

        :CaseLevel: Integration
        """
        lce = entities.LifecycleEnvironment(
            organization=self.session_org).create()
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self) as session:
            self.products.search_and_click(product.name)
            make_repository(
                session,
                name=repo_name,
                url=FAKE_YUM_DRPM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.setup_navigate_syncnow(
                session,
                product.name,
                repo_name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo_name))

            make_contentview(session, org=self.session_org.name, name=cv_name)
            self.assertIsNotNone(self.content_views.search(cv_name))
            self.content_views.add_remove_repos(cv_name, [repo_name])
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.content_views.publish(cv_name)
            self.assertIsNotNone(
                self.content_views.version_search(cv_name, 'Version 1.0'))
            status = self.content_views.promote(cv_name, 'Version 1', lce.name)
            self.assertIn('Promoted to {}'.format(lce.name), status)
        result = ssh.command(
            'ls /var/lib/pulp/published/yum/https/repos/{}/{}/{}/custom/{}/{}'
            '/drpms/ | grep .drpm'
            .format(
                self.session_org.label,
                lce.name,
                cv_name,
                product.label,
                repo_name,
            )
        )
        self.assertEqual(result.return_code, 0)
        self.assertGreaterEqual(len(result.stdout), 1)

    @tier1
    def test_positive_list_puppet_modules_with_multiple_repos(self):
        """Verify that puppet modules list for specific repo is correct and
        does not affected by other repositories.

        :id: 82ef2987-cb71-4164-aee5-4496b974d1bd

        :expectedresults: Number of modules has no changed after a second repo
            was synced.

        :CaseImportance: Critical
        """
        with Session(self):
            # Create and sync first repo
            repo1 = entities.Repository(
                product=self.session_prod,
                content_type=REPO_TYPE['puppet'],
                url=FAKE_0_PUPPET_REPO,
            ).create()
            repo1.sync()
            # Find modules count
            self.products.search_and_click(self.session_prod.name)
            self.repository.search_and_click(repo1.name)
            content_count = self.repository.find_element(
                locators['repo.fetch_puppet_modules']).text
            self.repository.click(locators['repo.manage_content'])
            modules_num = len(self.repository.find_elements(
                locators['repo.content.puppet_modules']))
            self.assertEqual(content_count, str(modules_num))
            # Create and sync second repo
            repo2 = entities.Repository(
                product=self.session_prod,
                content_type=REPO_TYPE['puppet'],
                url=FAKE_1_PUPPET_REPO,
            ).create()
            repo2.sync()
            # Verify that number of modules from the first repo has not changed
            self.products.search_and_click(self.session_prod.name)
            self.repository.search_and_click(repo1.name)
            self.repository.click(locators['repo.manage_content'])
            self.assertEqual(
                modules_num,
                len(self.repository.find_elements(
                    locators['repo.content.puppet_modules']))
            )

    @run_in_one_thread
    @tier2
    def test_positive_reposet_disable(self):
        """Enable RH repo, sync it and then disable

        :id: de596c56-1327-49e8-86d5-a1ab907f26aa

        :expectedresults: RH repo was disabled

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        with Session(self) as session:
            repos = self.sync.create_repos_tree(SAT6_TOOLS_TREE)
            session.nav.go_to_select_org(org.name)
            # Enable RH repository
            self.sync.enable_rh_repos(repos, REPO_TAB['rpms'])
            session.nav.go_to_sync_status()
            # Sync the repo and verify sync was successful
            self.assertTrue(self.sync.sync_noversion_rh_repos(
                PRDS['rhel'], [REPOS['rhst6']['name']]
            ))
            # Click the checkbox once more to disable the repo
            self.sync.enable_rh_repos(repos, REPO_TAB['rpms'])
            # Verify the repo is disabled
            self.assertFalse(
                self.sync.wait_until_element(
                    locators['rh.repo_checkbox'] % repos[0][0][0]['repo_name']
                ).is_selected()
            )

    @run_in_one_thread
    @tier2
    def test_positive_reposet_disable_after_manifest_deleted(self):
        """Enable RH repo and sync it. Remove manifest and then disable
        repository

        :id: f22baa8e-80a4-4487-b1bd-f7265555d9a3

        :customerscenario: true

        :expectedresults: RH repo was disabled

        :BZ: 1344391

        :CaseLevel: Integration
        """
        org = entities.Organization().create()
        sub = entities.Subscription(organization=org)
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        with Session(self) as session:
            repos = self.sync.create_repos_tree(SAT6_TOOLS_TREE)
            session.nav.go_to_select_org(org.name)
            # Enable RH repository
            self.sync.enable_rh_repos(repos, REPO_TAB['rpms'])
            session.nav.go_to_sync_status()
            # Sync the repo and verify sync was successful
            self.assertTrue(self.sync.sync_noversion_rh_repos(
                PRDS['rhel'], [REPOS['rhst6']['name']]
            ))
            # Delete manifest
            sub.delete_manifest(data={'organization_id': org.id})
            # Disable the repo
            self.sync.enable_rh_repos(repos, REPO_TAB['rpms'])
            # Verify that product name is correct
            prod_loc = 'rh.{0}_prd_expander'.format(REPO_TAB['rpms'].lower())
            self.assertIsNotNone(self.sync.wait_until_element(
                locators[prod_loc] % (PRDS['rhel'] + ' (Orphaned)')))
            # Verify the repo is disabled
            self.assertFalse(
                self.sync.wait_until_element(
                    locators['rh.repo_checkbox'] % repos[0][0][0]['repo_name']
                ).is_selected()
            )

    @tier1
    @skip_if_bug_open('bugzilla', 1394390)
    def test_positive_upload_rpm(self):
        """Create yum repository and upload rpm package

        :id: 201d5742-cb1a-4534-ac02-91b5a4669d22

        :expectedresults: Upload is successful and package is listed

        :BZ: 1394390, 1154384

        :CaseImportance: Critical
        """
        repo_name = gen_string('alpha')
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            self.products.search_and_click(self.session_prod.name)
            make_repository(session, name=repo_name)
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.upload_content(
                repo_name, get_data_file(RPM_TO_UPLOAD))
            # Check alert, its message should contain file name
            alert = self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form'])
            self.assertIsNotNone(alert)
            self.assertIn(RPM_TO_UPLOAD, alert.text)
            # Check packages count
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo_name, 'packages')
            self.assertGreaterEqual(count, 1)
            # Check packages list
            self.repository.click(locators['repo.manage_content'])
            packages = [
                package.text for package in
                self.repository.find_elements(
                    locators['repo.content.packages'])
                ]
            self.assertIn(RPM_TO_UPLOAD.rstrip('.rpm'), packages)

    @skip_if_bug_open('bugzilla', 1461831)
    @tier1
    @upgrade
    def test_positive_upload_rpm_non_admin(self):
        """Create yum repository, then upload rpm package via UI by non-admin
        user.

        :id: ac230198-1256-4b9b-9f0f-391064bbc5df

        :expectedresults: Upload form is visible, upload is successful and
            package is listed

        :BZ: 1429624, 1461831

        :CaseImportance: Critical
        """
        role = entities.Role().create()
        entities.Filter(
            permission=entities.Permission(
                resource_type='Katello::Product').search(),
            role=role,
        ).create()
        password = gen_string('alphanumeric')
        user = entities.User(
            admin=False,
            default_organization=self.session_org,
            location=[self.session_loc],
            organization=[self.session_org],
            password=password,
            role=[role],
        ).create()
        repo = entities.Repository(product=self.session_prod).create()
        with Session(self, user=user.login, password=password):
            self.products.search_and_click(self.session_prod.name)
            self.assertIsNotNone(self.repository.search(repo.name))
            self.repository.upload_content(
                repo.name, get_data_file(RPM_TO_UPLOAD))
            # Check alert, its message should contain file name
            alert = self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form'])
            self.assertIsNotNone(alert)
            self.assertIn(RPM_TO_UPLOAD, alert.text)
            # Check packages count
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo.name, 'packages')
            self.assertGreaterEqual(count, 1)
            # Check packages list
            self.repository.click(locators['repo.manage_content'])
            packages = [
                package.text for package in
                self.repository.find_elements(
                    locators['repo.content.packages'])
                ]
            self.assertIn(RPM_TO_UPLOAD.rstrip('.rpm'), packages)

    @tier1
    def test_positive_create_non_admin(self):
        """Create yum repository via UI by non-admin user

        :id: 6af5357e-d200-49e0-bf41-6d977b732810

        :expectedresults: repository is successfully created

        :BZ: 1398574, 1437134

        :CaseImportance: Critical
        """
        role = entities.Role().create()
        entities.Filter(
            permission=entities.Permission(
                resource_type='Katello::Product').search(),
            role=role,
        ).create()
        password = gen_string('alphanumeric')
        user = entities.User(
            admin=False,
            default_organization=self.session_org,
            organization=[self.session_org],
            password=password,
            role=[role],
        ).create()
        with Session(self, user=user.login, password=password) as session:
            self.products.search_and_click(self.session_prod.name)
            repo_name = gen_string('alphanumeric')
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))

    @tier1
    def test_negative_upload_rpm(self):
        """Create yum repository but upload any content except rpm

        :id: 77a098c2-3f63-4e9f-88b9-f0657b721611

        :expectedresults: Error is raised during upload and file is not listed

        :CaseImportance: Critical
        """
        repo_name = gen_string('alpha')
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            self.products.search_and_click(self.session_prod.name)
            make_repository(session, name=repo_name)
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.upload_content(
                repo_name, get_data_file(PUPPET_MODULE_NTP_PUPPETLABS))
            # Check alert
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.error_sub_form']))
            # Check packages count
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo_name, 'packages')
            self.assertEqual(count, 0)

    @tier1
    @upgrade
    def test_positive_upload_puppet(self):
        """Create puppet repository and upload puppet module

        :id: 2da4ddeb-3d6a-4b77-b44a-190a0c20a4f6

        :expectedresults: Upload is successful and module is listed

        :BZ: 1154384

        :CaseImportance: Critical
        """
        repo_name = gen_string('alpha')
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            self.products.search_and_click(self.session_prod.name)
            make_repository(
                session, name=repo_name, repo_type=REPO_TYPE['puppet'])
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.upload_content(
                repo_name, get_data_file(PUPPET_MODULE_NTP_PUPPETLABS))
            # Check alert, its message should contain file name
            alert = self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form'])
            self.assertIsNotNone(alert)
            self.assertIn(PUPPET_MODULE_NTP_PUPPETLABS, alert.text)
            # Check packages count
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo_name, 'puppet')
            self.assertGreaterEqual(count, 1)
            # Check packages list
            self.repository.click(locators['repo.manage_content'])
            # Select all modules names from modules table
            packages = [
                package.text.split()[0] for package in
                self.repository.find_elements(
                    locators['repo.content.puppet_modules'])
            ]
            self.assertIn('ntp', packages)

    @tier1
    def test_negative_upload_puppet(self):
        """Create puppet repository but upload any content except puppet module

        :id: 79ebea29-2c5c-476d-8d1a-54e6b9d49e17

        :expectedresults: Error is raised during upload and file is not listed

        :CaseImportance: Critical
        """
        repo_name = gen_string('alpha')
        with Session(self) as session:
            set_context(session, org=self.session_org.name)
            self.products.search_and_click(self.session_prod.name)
            make_repository(
                session, name=repo_name, repo_type=REPO_TYPE['puppet'])
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.upload_content(
                repo_name, get_data_file(RPM_TO_UPLOAD))
            # Check alert
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.error_sub_form']))
            # Check packages number
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo_name, 'puppet')
            self.assertEqual(count, 0)

    @run_only_on('sat')
    @tier1
    def test_positive_remove_content_rpm(self):
        """Synchronize repository and remove content from it

        :id: 054763e5-b6a8-4f06-a9f7-6819fbc7aba8

        :expectedresults: Content Counts shows zero rpm packages

        :CaseImportance: Critical
        """
        with Session(self) as session:
            repo = entities.Repository(
                url=FAKE_1_YUM_REPO,
                content_type='yum',
                product=self.session_prod,
            ).create()
            self.setup_navigate_syncnow(
                session,
                self.session_prod.name,
                repo.name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo.name))
            # Check packages count
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo.name, 'packages')
            self.assertGreaterEqual(count, 1)
            # Remove packages
            self.products.search_and_click(self.session_prod.name)
            self.repository.remove_content(repo.name)
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo.name, 'packages')
            self.assertEqual(count, 0)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_content_puppet(self):
        """Synchronize repository and remove content from it

        :id: be178e21-5d64-46d4-8a41-c3f0f62dabe0

        :expectedresults: Content Counts shows zero puppet modules
        """
        with Session(self) as session:
            repo = entities.Repository(
                url=FAKE_1_PUPPET_REPO,
                content_type='puppet',
                product=self.session_prod,
            ).create()
            self.setup_navigate_syncnow(
                session,
                self.session_prod.name,
                repo.name,
            )
            self.assertTrue(self.prd_sync_is_ok(repo.name))
            # Check packages count
            count = self.repository.fetch_content_count(repo.name, 'puppet')
            self.assertGreaterEqual(count, 1)
            # Remove packages
            self.products.search_and_click(self.session_prod.name)
            self.repository.remove_content(repo.name)
            self.products.search_and_click(self.session_prod.name)
            count = self.repository.fetch_content_count(repo.name, 'puppet')
            self.assertEqual(count, 0)


class GitPuppetMirrorTestCase(UITestCase):
    """Tests for creating the hosts via CLI."""

    # Notes for Puppet GIT puppet mirror content
    #
    # This feature does not allow us to actually sync/update content in a
    # GIT repo.
    # Instead, we're essentially "snapshotting" what contains in a repo at any
    # given time. The ability to update the GIT puppet mirror comes is/should
    # be provided by pulp itself, via script.  However, we should be able to
    # create a sync schedule against the mirror to make sure it is periodically
    # update to contain the latest and greatest.

    @stubbed()
    @tier2
    def test_positive_git_local_create(self):
        """Create repository with local git puppet mirror.

        :id: b1d3ef84-cf59-4d08-8123-abda3b2086ca

        :CaseLevel: Integration

        :Setup: Assure local GIT puppet has been created and found by pulp

        :Steps: Create link to local puppet mirror

        :expectedresults: Content source containing local GIT puppet mirror
            content is created

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_local_update(self):
        """Update repository with local git puppet mirror.

        :id: d8b32e52-ee3e-4c99-b47f-8726ece6ab94

        :CaseLevel: Integration

        :Setup: Assure local GIT puppet has been created and found by pulp

        :Steps: Modify details for existing puppet repo (name, etc.)

        :expectedresults: Content source containing local GIT puppet mirror
            content is modified

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    @upgrade
    def test_positive_git_local_delete(self):
        """Delete repository with local git puppet mirror.

        :id: 45b02a5d-0536-4a89-8222-3584a69363ea

        :CaseLevel: Integration

        :Setup: Assure local GIT puppet has been created and found by pulp

        :Steps: Delete link to local puppet mirror

        :expectedresults: Content source containing local GIT puppet mirror
            content no longer exists/is available.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_remote_create(self):
        """Create repository with remote git puppet mirror.

        :id: 50d90ae5-9c3d-4ec7-bdd8-9c418d56e167

        :CaseLevel: Integration

        :Setup: Assure remote GIT puppet has been created and found by pulp

        :Steps: Create link to local puppet mirror

        :expectedresults: Content source containing remote GIT puppet mirror
            content is created

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_remote_update(self):
        """Update repository with remote git puppet mirror.

        :id: df53b612-eadb-411a-abf0-07eae3ae1059

        :CaseLevel: Integration

        :Setup: Assure remote  GIT puppet has been created and found by pulp

        :Steps: modify details for existing puppet repo (name, etc.)

        :expectedresults: Content source containing remote GIT puppet mirror
            content is modified

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    @upgrade
    def test_positive_git_remote_delete(self):
        """Delete repository with remote git puppet mirror.

        :id: 3971f330-2b91-44cb-89e4-350002ef0ee8

        :CaseLevel: Integration

        :Setup: Assure remote GIT puppet has been created and found by pulp

        :Steps: Delete link to remote puppet mirror

        :expectedresults: Content source containing remote GIT puppet mirror
            content no longer exists/is available.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_sync(self):
        """Sync repository with git puppet mirror.

        :id: f46fa078-81d3-492b-86e9-c11fa97fae0b

        :CaseLevel: Integration

        :Setup: git mirror (local or remote) exists as a content source

        :Steps: Attempt to sync content from mirror

        :expectedresults:

            1. Content is pulled down without error
            2. Confirmation that various resources actually exist in local
                content repo

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    @upgrade
    def test_positive_git_sync_with_content_change(self):
        """Sync repository with changes in git puppet mirror.
        If module changes in GIT mirror but the version in manifest
        does not change, content still pulled.

        :id: 7b0484c2-df0a-46e8-95a7-1535435e6079

        :CaseLevel: Integration

        :Setup: Assure remote GIT puppet has been created and found by pulp

        :Steps:

            1.  Sync a git repo and observe the contents/checksum etc. of an
                existing puppet module
            2.  Assure a puppet module in git repo has changed but the manifest
                version for this module does not change.
            3.  Using pulp script, update repo mirror and re-sync within
                satellite
            4.  View contents/details of same puppet module

        :expectedresults: Puppet module has been updated in our content, even
            though the module's version number has not changed.

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_sync_schedule(self):
        """Scheduled sync of git puppet mirror.

        :id: 1e15e4ad-35e8-493f-84f5-47ad180d2a7a

        :CaseLevel: Integration

        :Setup: git mirror (local or remote) exists as a content source

        :Steps: Attempt to create a scheduled sync content from mirror

        :expectedresults: Content is pulled down without error  on expected
            schedule

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_view_content(self):
        """View content in synced git puppet mirror

        :id: bb536b1b-13f6-448d-b1b2-44e2fdf93b5f

        :CaseLevel: Integration

        :Setup: git mirror (local or remote) exists as a content source

        :Steps: Attempt to list contents of repo

        :expectedresults: Spot-checked items (filenames, dates, perhaps
            checksums?) are correct.

        :CaseAutomation: notautomated
        """


class FileRepositoryTestCase(UITestCase):
    """Implements File Repo tests in UI"""

    @stubbed()
    @tier1
    def test_positive_create_with_name(self):
        """Check File Repository creation

        :id: 9f90c42e-a077-4f0a-b5ec-2b342ff2d9fe

        :Setup:
            1. Navigate to Content -> Products
            2. Create a Product

        :Steps:
            1. Click "New Repository" button
            2. Define a valid name and choose type "file" repo
            3. Check repo is listed under "Repositories" product's tab

        :expectedresults: File Repository is created and listed as product's
            repository

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_upload_file(self):
        """Check arbitrary file can be uploaded to File Repository

        :id: 2a9b74a4-cba8-430d-a699-fea543496466

        :Setup:
            1. Navigate to Content -> Products
            2. Create a Product
            3. Create a File Repository without specifying repo url
            4. Click on the created repository

        :Steps:
            1. Click "Browse" button and select a file
            2. Click Upload
            3. Click the link in "Files" on "Content Type" table

        :expectedresults: uploaded file is available under File Repository

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier4
    def test_positive_upload_large_file(self):
        """Check large file can be handled by File Repository

        :id: 750b9190-d064-4b84-8527-d8367dafd4ab

        :Setup:
            1. Navigate to Content -> Products
            2. Create a Product
            3. Create a File Repository
            4. Click on the created repository

        :Steps:
            1. Click "Browse" button and select a large file
                (3GB - can use a Sallite ISO)
            2. Click Upload
            3. Click the link in "Files" on "Content Type" table

        :expectedresults: uploaded file is available under File Repository

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier4
    def test_positive_upload_0_byte_file(self):
        """Check 0 byte file can be handled by File Repository

        :id: c1891368-5e55-4e52-84a9-944e1c2af8e9

        :Setup:
            1. Navigate to Content -> Products
            2. Create a Product
            3. Create a File Repository without specifying repo url
            4. Click on the created repository

        :Steps:
            1. Click "Browse" button and select a o byte file (create it
                with touch "file_name"
            2. Click Upload
            3. Click the link in "Files" on "Content Type" table

        :expectedresults: uploaded file is available under File Repository

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_filer_permissions(self):
        """Check file permissions after file upload to File Repository

        :id: f6771475-19bd-47ce-9f55-432d62e1dfa4

        :Setup:
            1. Navigate to Content -> Products
            2. Create a Product
            3. Create a File Repository without specifying repo url
            4. Click on the created repository

        :Steps:
            1. Click "Browse" button and select a file
            2. Click Upload
            3. Click the link in "Files" on "Content Type" table

        :expectedresults: uploaded file permissions are kept after upload

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_remove_file(self):
        """Check arbitrary file can be removed from File Repository

        :id: 3f2b08dd-2aa1-4ac9-8bdf-f604f47eec2a

        :Setup:
            1. Navigate to Content -> Products
            2. Create a Product
            3. Create a File Repository without specifying repo url
            4. Click on the created repository
            5. Click "Browse" button and select a file
            6. Click Upload
            7. Click the link in "Files" on "Content Type" table

        :Steps:
            1. Select arbitrary file
            2. Click "Remove Files" button
            3. Click "Remove" on modal

        :expectedresults: file is not listed under File Repository after
            removal

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier4
    @upgrade
    def test_positive_remote_directory_sync(self):
        """Check an entire remote directory can be synced to File Repository
        through http

        :id: 7e25bb59-08b6-4b22-9040-396af3a1202a

        :Setup:
            1. Create a directory to be synced with a pulp manifest on its root
            2. Made the directory available through http
            3. Navigate to Content -> Products
            4. Create a Product
            5. Create a File Repository without specifying repo url

        :Steps:
            1. Fill url with directory http url to be synced
            2. Click "Save" button
            3. Select create repository
            4. Click "Sync Now"


        :expectedresults: entire directory is synced over http

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    @upgrade
    def test_positive_local_directory_sync(self):
        """Check an entire local directory can be synced to File Repository

        :id: a561fd42-709c-4427-b27b-2c871e0bcfdf

        :Setup:
            1. Create a local (on Satellite/Foreman itself) directory to be
                synced with a pulp manifest on its root
            2. Navigate to Content -> Products
            3. Create a Product
            4. Create a File Repository without specifying repo url

        :Steps:
            1. Fill url with directory file:///path_to_directory url to be
                synced
            2. Click "Save" button
            3. Select create repository
            4. Click "Sync Now"

        :expectedresults: entire local directory is synced

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_symlink_sync(self):
        """Check symlinks are synced to File Repository

        :id: 928c840d-94d0-4b8e-9a2f-e4581126611e

        :Setup:
            1. Create a local (on Satellite/Foreman itself) directory
            2. Add symlinks to directory
            3. Add a pulp manifest on its root
            4. Navigate to Content -> Products
            5. Create a Product
            6. Create a File Repository without specifying repo url

        :Steps:
            1. Fill url with directory file:///path_to_directory url to be
                synced
            2. Click "Save" button
            3. Select create repository
            4. Click "Sync Now"

        :expectedresults: directory synchronization follow symlinks

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_positive_hidden_files_sync(self):
        """Check hidden files are synced accordingly to pulp manifest

        :id: da1fba32-b77f-43b2-b7a0-7c2e650a939b

        :Setup:
            1. Create a local (on Satellite/Foreman itself) directory
            2. Add hidden files to directory
            3. Add a pulp manifest on its root which include hidden files
            4. Navigate to Content -> Products
            5. Create a Product
            6. Create a File Repository without specifying repo url

        :Steps:
            1. Fill url with directory file:///path_to_directory url to be
                synced
            2. Click "Save" button
            3. Select create repository
            4. Click "Sync Now"

        :expectedresults: directory synchronization includes hidden files as
            configured on pulp manifest

        :CaseAutomation: notautomated
        """

    @stubbed()
    @tier1
    def test_negative_hidden_files_sync(self):
        """Check hidden files aren't synced accordingly to pulp manifest

        :id: 82963ee9-6166-4671-ba87-54666496c5e8

        :Setup:
            1. Create a local (on Satellite/Foreman itself) directory
            2. Add hidden files to directory
            3. Add a pulp manifest on its root which does include hidden files
            4. Navigate to Content -> Products
            5. Create a Product
            6. Create a File Repository without specifying repo url

        :Steps:
            1. Fill url with directory file:///path_to_directory url to be
                synced
            2. Click "Save" button
            3. Select create repository
            4. Click "Sync Now"

        :expectedresults: directory synchronization does not include hidden
            files as configured on pulp manifest

        :CaseAutomation: notautomated
        """
