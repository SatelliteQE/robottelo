# -*- encoding: utf-8 -*-
"""Test class for Repository UI

@Requirement: Repository

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

import time

from fauxfactory import gen_string
from nailgun import entities

from robottelo import manifests, ssh
from robottelo.api.utils import upload_manifest
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
    PRDS,
    PUPPET_MODULE_NTP_PUPPETLABS,
    REPO_DISCOVERY_URL,
    REPO_TYPE,
    REPOS,
    RPM_TO_UPLOAD,
    SAT6_TOOLS_TREE,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    stubbed,
    tier1,
    tier2,
)
from robottelo.decorators.host import skip_if_os
from robottelo.helpers import get_data_file, read_data_file
from robottelo.host_info import get_host_os_version
from robottelo.test import UITestCase
from robottelo.ui.factory import make_contentview, make_repository, set_context
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session
from selenium.common.exceptions import NoSuchElementException


@filtered_datapoint
def valid_repo_names_docker_sync():
    """Returns a list of valid repo names for docker sync test"""
    return [
        gen_string('alpha', 8).lower(),
        gen_string('numeric', 8),
        gen_string('alphanumeric', 8).lower(),
        gen_string('html', 8),
        gen_string('utf8', 8),
    ]


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
        strategy1, value1 = locators['repo.select']
        strategy2, value2 = locators['repo.select_checkbox']
        session.nav.go_to_select_org(self.session_org.name, force=False)
        session.nav.go_to_products()
        session.nav.click((strategy1, value1 % prd_name))
        session.nav.click((strategy2, value2 % repo_name))
        session.nav.click(locators['repo.sync_now'])

    def prd_sync_is_ok(self, repo_name):
        """Asserts whether the sync Result is successful."""
        strategy1, value1 = locators['repo.select_event']
        self.repository.click(tab_locators['prd.tab_tasks'])
        self.repository.click((strategy1, value1 % repo_name))
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

        @id: 3713c811-ea80-43ce-a753-344d1dcb7486

        @Assert: Repository is created successfully
        """
        prod = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(prod.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @tier2
    def test_positive_create_in_different_orgs(self):
        """Create repository in two different orgs with same name

        @id: 019c2242-8802-4bae-82c5-accf8f793dbc

        @Assert: Repository is created successfully for both organizations

        @CaseLevel: Integration
        """
        org_2 = entities.Organization(name=gen_string('alpha')).create()
        product_1 = entities.Product(organization=self.session_org).create()
        product_2 = entities.Product(organization=org_2).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(product_1.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    set_context(session, org=org_2.name)
                    self.products.search(product_2.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                        force_context=True,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @tier2
    def test_positive_create_puppet_repo_same_url_different_orgs(self):
        """Create two repos with the same URL in two different organizations.

        @id: f4cb00ed-6faf-4c79-9f66-76cd333299cb

        @Assert: Repositories are created and puppet modules are visible from
        different organizations.

        @CaseLevel: Integration
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
        with Session(self.browser) as session:
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
    def test_positive_create_repo_with_checksum(self):
        """Create repository with checksum type as sha256.

        @id: 06f37bb3-b0cf-4f1f-ae12-df13a6a7eaab

        @Assert: Repository is created with expected checksum type.
        """
        checksum = CHECKSUM_TYPE[u'sha256']
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(product.name).click()
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
    def test_negative_create_with_invalid_name(self):
        """Create repository with invalid names

        @id: 385d0222-6466-4bc0-9686-b215f41e4274

        @Assert: Repository is not created
        """
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        for repo_name in invalid_values_list(interface='ui'):
            with self.subTest(repo_name):
                with Session(self.browser) as session:
                    set_context(session, org=self.session_org.name)
                    self.products.search(product.name).click()
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

        @id: f9515a61-0c5e-4767-9fc9-b17d440418d8

        @Assert: Repository is not created
        """
        repo_name = gen_string('alphanumeric')
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.products.search(product.name).click()
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

        @id: cb864338-9d18-4e18-a2ee-37f22e7036b8

        @Assert: Repository is updated with expected url value
        """
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(product.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'url', FAKE_1_YUM_REPO))
                    self.products.search(product.name).click()
                    self.repository.update(repo_name, new_url=FAKE_2_YUM_REPO)
                    self.products.search(product.name).click()
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'url', FAKE_2_YUM_REPO))

    @run_only_on('sat')
    @tier1
    def test_positive_update_gpg(self):
        """Update content repository with new gpg-key

        @id: 51da6572-02d0-43d7-96cc-895b5bebfadb

        @Assert: Repository is updated with new gpg key
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
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
                gpg_key=gpgkey_1.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.assertTrue(self.repository.validate_field(
                repo_name, 'gpgkey', gpgkey_1.name))
            self.products.search(product.name).click()
            self.repository.update(repo_name, new_gpg_key=gpgkey_2.name)
            self.products.search(product.name).click()
            self.assertTrue(self.repository.validate_field(
                repo_name, 'gpgkey', gpgkey_2.name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_checksum_type(self):
        """Update content repository with new checksum type

        @id: eed4e77d-baa2-42c2-9774-f1bed52efe39

        @Assert: Repository is updated with expected checksum type.
        """
        repo_name = gen_string('alphanumeric')
        checksum_default = CHECKSUM_TYPE['default']
        checksum_update = CHECKSUM_TYPE['sha1']
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(product.name).click()
            make_repository(
                session,
                name=repo_name,
                url=FAKE_1_YUM_REPO,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.assertTrue(self.repository.validate_field(
                repo_name, 'checksum', checksum_default))
            self.products.search(product.name).click()
            self.repository.update(
                repo_name, new_repo_checksum=checksum_update)
            self.products.search(product.name).click()
            self.assertTrue(self.repository.validate_field(
                repo_name, 'checksum', checksum_update))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create content repository and then remove it

        @id: 9edc93b1-d4e5-453e-b4ee-0731df491397

        @Assert: Repository is deleted successfully
        """
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.session_org.name)
                    self.products.search(product.name).click()
                    make_repository(
                        session,
                        name=repo_name,
                        url=FAKE_1_YUM_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    self.repository.delete(repo_name)

    @run_only_on('sat')
    @stubbed
    @tier2
    def test_negative_delete_puppet_repo_associated_with_cv(self):
        """Delete a puppet repo associated with a content view - BZ#1271000

        @id: 72639e14-4089-4f40-bad7-e18021ad376f

        @Steps:

        1. Create a new product
        2. Create a new puppet repo, no sync source
        3. Upload a puppet module (say ntpd) to repo
        4. Create a CV, go to add puppet modules page
        5. Add latest version of the puppet module from Step 3
        6. View puppet repo details, it should show "Latest (Currently X.Y.Z)"
        7. Go back to product, drill down into repo and delete the puppet
        module from Step 3
        8. Go back to same CV puppet module details page

        @Assert: Proper error message saying that the puppet module version is
        not found

        @caseautomation: notautomated

        @CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    def test_positive_discover_repo_via_existing_product(self):
        """Create repository via repo-discovery under existing product

        @id: 9181950c-a756-456f-a46a-059e7a2add3c

        @Assert: Repository is discovered and created

        @CaseLevel: Integration
        """
        discovered_urls = 'fakerepo01/'
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
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

        @id: dc5281f8-1a8a-4a17-b746-728f344a1504

        @Assert: Repository is discovered and created

        @CaseLevel: Integration
        """
        product_name = gen_string('alpha')
        discovered_urls = 'fakerepo01/'
        with Session(self.browser) as session:
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
    def test_positive_sync_custom_repo_yum(self):
        """Create Custom yum repos and sync it via the repos page.

        @id: afa218f4-e97a-4240-a82a-e69538d837a1

        @Assert: Sync procedure for specific yum repository is successful

        @CaseLevel: Integration
        """
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
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
    def test_positive_sync_custom_repo_puppet(self):
        """Create Custom puppet repos and sync it via the repos page.

        @id: 135176cc-7664-41ee-8c41-b77e193f2f22

        @Assert: Sync procedure for specific puppet repository is successful

        @CaseLevel: Integration
        """
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
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
    def test_positive_sync_custom_repo_docker(self):
        """Create Custom docker repos and sync it via the repos page.

        @id: 942e0b4f-3524-4f00-812d-bdad306f81de

        @Assert: Sync procedure for specific docker repository is successful

        @CaseLevel: Integration
        """
        # Creates new product
        product = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in valid_repo_names_docker_sync():
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
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_create_custom_ostree_repo(self):
        """Create Custom ostree repository.

        @id: 852cccdc-7289-4d2f-b23a-7caad2dfa195

        @Assert: Create custom ostree repository should be successful
        """
        prod = entities.Product(organization=self.session_org).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    session.nav.go_to_select_org(
                        self.session_org.name, force=False)
                    self.products.click(self.products.search(prod.name))
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
    def test_positive_delete_custom_ostree_repo(self):
        """Delete custom ostree repository.

        @id: 87dcb236-4eb4-4897-9c2a-be1d0f4bc3e7

        @Assert: Delete custom ostree repository should be successful
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
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.delete(repo_name)

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_update_custom_ostree_repo_name(self):
        """Update custom ostree repository name.

        @id: 098ee88f-6cdb-45e0-850a-e1b71662f7ab

        @Steps: Update repo name

        @Assert: ostree repo name should be updated successfully
        """
        prod = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        new_repo_name = gen_string('numeric')
        # Creates new ostree repository using api
        entities.Repository(
            name=repo_name,
            content_type='ostree',
            url=FEDORA22_OSTREE_REPO,
            product=prod,
            unprotected=False,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.update(
                repo_name, new_name=new_repo_name)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(new_repo_name))

    @run_only_on('sat')
    @skip_if_os('RHEL6')
    @tier1
    def test_positive_update_custom_ostree_repo_url(self):
        """Update custom ostree repository url.

        @id: dfd392f9-6f1d-4d87-a43b-ced40606b8c2

        @Steps: Update ostree repo URL

        @Assert: ostree repo URL should be updated successfully
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
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.session_org.name, force=False)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.update(
                repo_name,
                new_url=FEDORA23_OSTREE_REPO
            )
            self.products.click(self.products.search(prod.name))
            # Validate the new repo URL
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'url', FEDORA23_OSTREE_REPO
                )
            )

    @tier1
    def test_positive_download_policy_displayed_for_yum_repos(self):
        """Verify that YUM repositories can be created with download policy

        @id: 8037a68b-66b8-4b42-a80b-fb08495f948d

        @Assert: Dropdown for download policy is displayed for yum repo
        """
        with Session(self.browser) as session:
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

        @id: f91c4fb8-301d-4f28-8a32-bbc52b907e1f

        @Assert: YUM repository with a download policy is created
        """
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
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

        @id: ee7637fe-3864-4b2f-a153-14312658d75a

        @Assert: YUM repository with a default download policy
        """
        repo_name = gen_string('alphanumeric')
        default_dl_policy = entities.Setting().search(
            query={'search': 'name=default_download_policy'}
        )
        self.assertTrue(default_dl_policy and
                        DOWNLOAD_POLICIES.get(default_dl_policy[0].value))
        default_dl_policy = DOWNLOAD_POLICIES.get(default_dl_policy[0].value)
        with Session(self.browser) as session:
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
    def test_positive_create_immediate_update_to_on_demand(self):
        """Update `immediate` download policy to `on_demand` for a newly
        created YUM repository

        @id: 4aa4d914-74f3-4c2e-9e8a-6e1b7fdb34ea

        @Assert: immediate download policy is updated to on_demand
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Immediate')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='On Demand')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'On Demand'
                )
            )

    @tier1
    def test_positive_create_immediate_update_to_background(self):
        """Update `immediate` download policy to `background` for a newly
        created YUM repository

        @id: d61bf6b6-6485-4d3a-816a-b533e96deb69

        @Assert: immediate download policy is updated to background
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Immediate')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Background')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Background'
                )
            )

    @tier1
    def test_positive_create_on_demand_update_to_immediate(self):
        """Update `on_demand` download policy to `immediate` for a newly
        created YUM repository

        @id: 51cac66d-05a4-47da-adb5-d2909725457e

        @Assert: on_demand download policy is updated to immediate
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'On Demand')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Immediate')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Immediate'
                )
            )

    @tier1
    def test_positive_create_on_demand_update_to_background(self):
        """Update `on_demand` download policy to `background` for a newly
        created YUM repository

        @id: 25b5ba4e-a1cf-41c2-8ca8-4fa3153570f8

        @Assert: on_demand download policy is updated to background
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'On Demand')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Background')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Background'
                )
            )

    @tier1
    def test_positive_create_background_update_to_immediate(self):
        """Update `background` download policy to `immediate` for a newly
        created YUM repository

        @id: 7a6efe70-8edb-4fa8-b2a4-93762d6e4bc5

        @Assert: background download policy is updated to immediate
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Background')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='Immediate')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'Immediate'
                )
            )

    @tier1
    def test_positive_create_background_update_to_on_demand(self):
        """Update `background` download policy to `on_demand` for a newly
        created YUM repository

        @id: d36b96b1-6e09-455e-82e7-36a23f8c6c06

        @Assert: background download policy is updated to on_demand
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Background')
        with Session(self.browser):
            self.products.search_and_click(self.session_prod.name)
            self.repository.update(repo_name, download_policy='On Demand')
            self.assertTrue(
                self.repository.validate_field(
                    repo_name, 'download_policy', 'On Demand'
                )
            )

    @tier1
    def test_negative_create_with_invalid_download_policy(self):
        """Verify that YUM repository cannot be created with invalid download
        policy

        @id: dded6dda-3576-4485-8f3c-bb7c091e7ff2

        @Assert: YUM repository is not created with invalid download policy
        """
        repo_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
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

        @id: e6c725f2-172e-49f6-ae92-c56af8a1200b

        @Assert: YUM repository is not updated to invalid download policy
        """
        repo_name = gen_string('alphanumeric')
        self._create_yum_repo_with_download_policy(repo_name, 'Immediate')
        with Session(self.browser):
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

        @id: 47d55251-5f89-443d-b980-a441da34e205

        @Assert: Dropdown for download policy is not displayed for non-yum repo
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
        with Session(self.browser):
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

    @tier2
    def test_positive_srpm_sync(self):
        """Synchronize repository with SRPMs

        @id: 1967a540-a265-4046-b87b-627524b63688

        @Assert: srpms can be listed in repository
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
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

    @tier2
    def test_positive_srpm_sync_publish_cv(self):
        """Synchronize repository with SRPMs, add repository to content view
        and publish content view

        @id: 2a57cbde-c616-440d-8bcb-6e18bd2d5c5f

        @Assert: srpms can be listed in content view
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
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
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
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

    @tier2
    def test_positive_srpm_sync_publish_promote_cv(self):
        """Synchronize repository with SRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        @id: 4563d1c1-cdce-4838-a67f-c0a5d4e996a6

        @Assert: srpms can be listed in content view in proper lifecycle
        environment
        """
        lce = entities.LifecycleEnvironment(
            organization=self.session_org).create()
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
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
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
            self.content_views.promote(cv_name, 'Version 1', lce.name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
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

    @tier2
    def test_positive_drpm_sync(self):
        """Synchronize repository with DRPMs

        @id: 5e703d9a-ea26-4062-9d5c-d31bfbe87417

        @Assert: drpms can be listed in repository
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
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

    @tier2
    def test_positive_drpm_sync_publish_cv(self):
        """Synchronize repository with DRPMs, add repository to content view
        and publish content view

        @id: cffa862c-f972-4aa4-96b2-5a4513cb3eef

        @Assert: drpms can be listed in content view
        """
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
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
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
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

    @tier2
    def test_positive_drpm_sync_publish_promote_cv(self):
        """Synchronize repository with DRPMs, add repository to content view,
        publish and promote content view to lifecycle environment

        @id: e33ee07c-4677-4be8-bd53-73689edfda34

        @Assert: drpms can be listed in content view in proper lifecycle
        environment
        """
        lce = entities.LifecycleEnvironment(
            organization=self.session_org).create()
        product = entities.Product(organization=self.session_org).create()
        repo_name = gen_string('alphanumeric')
        cv_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            self.products.search(product.name).click()
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
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
            self.content_views.promote(cv_name, 'Version 1', lce.name)
            self.assertIsNotNone(self.content_views.wait_until_element
                                 (common_locators['alert.success_sub_form']))
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
        """
        Verify that puppet modules list for specific repo is correct
        and does not affected by other repositories.

        @id: 82ef2987-cb71-4164-aee5-4496b974d1bd

        @Assert: Number of modules has no changed after a second repo
        was synced.
        """
        with Session(self.browser):
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

        @id: de596c56-1327-49e8-86d5-a1ab907f26aa

        @Assert: RH repo was disabled

        @CaseLevel: Integration
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        repos = self.sync.create_repos_tree(SAT6_TOOLS_TREE)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(org.name)
            # Enable RH repository
            self.sync.enable_rh_repos(repos)
            session.nav.go_to_sync_status()
            # Sync the repo and verify sync was successful
            self.assertTrue(self.sync.sync_noversion_rh_repos(
                PRDS['rhel'], [REPOS['rhst6']['name']]
            ))
            # Click the checkbox once more to disable the repo
            self.sync.enable_rh_repos(repos)
            # Verify the repo is disabled
            strategy, value = locators['rh.repo_checkbox']
            self.assertFalse(
                self.sync.wait_until_element((
                    strategy, value % SAT6_TOOLS_TREE[0][-1]
                )).is_selected()
            )

    @tier1
    def test_positive_upload_rpm(self):
        """Create yum repository and upload rpm package

        @id: 201d5742-cb1a-4534-ac02-91b5a4669d22

        @Assert: Upload is successful and package is listed
        """
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(self.session_prod.name).click()
            make_repository(session, name=repo_name)
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.upload_content(
                repo_name, get_data_file(RPM_TO_UPLOAD))
            # Check alert
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            # Check packages number
            number = self.repository.find_element(
                locators['repo.fetch_packages'])
            self.assertGreater(int(number.text), 0)
            # Check packages list
            self.repository.click(locators['repo.manage_content'])
            packages = [
                package.text for package in
                self.repository.find_elements(
                    locators['repo.content.packages'])
            ]
            self.assertIn(RPM_TO_UPLOAD.rstrip('.rpm'), packages)

    @tier1
    def test_negative_upload_rpm(self):
        """Create yum repository but upload any content except rpm

        @id: 77a098c2-3f63-4e9f-88b9-f0657b721611

        @Assert: Error is raised during upload and file is not listed
        """
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(self.session_prod.name).click()
            make_repository(session, name=repo_name)
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.upload_content(
                repo_name, get_data_file(PUPPET_MODULE_NTP_PUPPETLABS))
            # Check alert
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.error_sub_form']))
            # Check packages number
            number = self.repository.find_element(
                locators['repo.fetch_packages'])
            self.assertEqual(int(number.text), 0)

    @tier1
    def test_positive_upload_puppet(self):
        """Create puppet repository and upload puppet module

        @id: 2da4ddeb-3d6a-4b77-b44a-190a0c20a4f6

        @Assert: Upload is successful and module is listed
        """
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(self.session_prod.name).click()
            make_repository(
                session, name=repo_name, repo_type=REPO_TYPE['puppet'])
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.upload_content(
                repo_name, get_data_file(PUPPET_MODULE_NTP_PUPPETLABS))
            # Check alert
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            # Check packages number
            number = self.repository.find_element(
                locators['repo.fetch_puppet_modules'])
            self.assertGreater(int(number.text), 0)
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

        @id: 79ebea29-2c5c-476d-8d1a-54e6b9d49e17

        @Assert: Error is raised during upload and file is not listed
        """
        repo_name = gen_string('alpha')
        with Session(self.browser) as session:
            set_context(session, org=self.session_org.name)
            self.products.search(self.session_prod.name).click()
            make_repository(
                session, name=repo_name, repo_type=REPO_TYPE['puppet'])
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.upload_content(
                repo_name, get_data_file(RPM_TO_UPLOAD))
            # Check alert
            self.assertIsNotNone(self.activationkey.wait_until_element(
                common_locators['alert.error_sub_form']))
            # Check packages number
            number = self.repository.find_element(
                locators['repo.fetch_puppet_modules'])
            self.assertEqual(int(number.text), 0)


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

        @id: b1d3ef84-cf59-4d08-8123-abda3b2086ca

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Create link to local puppet mirror

        @Assert: Content source containing local GIT puppet mirror content
        is created

        @CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_local_update(self):
        """Update repository with local git puppet mirror.

        @id: d8b32e52-ee3e-4c99-b47f-8726ece6ab94

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Modify details for existing puppet repo (name, etc.)

        @Assert: Content source containing local GIT puppet mirror content
        is modified

        @CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_local_delete(self):
        """Delete repository with local git puppet mirror.

        @id: 45b02a5d-0536-4a89-8222-3584a69363ea

        @CaseLevel: Integration

        @Setup: Assure local GIT puppet has been created and found by pulp

        @Steps:

        1.  Delete link to local puppet mirror

        @Assert: Content source containing local GIT puppet mirror content
        no longer exists/is available.

        @CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_remote_create(self):
        """Create repository with remote git puppet mirror.

        @id: 50d90ae5-9c3d-4ec7-bdd8-9c418d56e167

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Create link to local puppet mirror

        @Assert: Content source containing remote GIT puppet mirror content
        is created

        @CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_remote_update(self):
        """Update repository with remote git puppet mirror.

        @id: df53b612-eadb-411a-abf0-07eae3ae1059

        @CaseLevel: Integration

        @Setup: Assure remote  GIT puppet has been created and found by pulp

        @Steps:

        1.  modify details for existing puppet repo (name, etc.)

        @Assert: Content source containing remote GIT puppet mirror content
        is modified

        @CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_remote_delete(self):
        """Delete repository with remote git puppet mirror.

        @id: 3971f330-2b91-44cb-89e4-350002ef0ee8

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Delete link to remote puppet mirror

        @Assert: Content source containing remote GIT puppet mirror content
        no longer exists/is available.

        @CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_sync(self):
        """Sync repository with git puppet mirror.
        @id: f46fa078-81d3-492b-86e9-c11fa97fae0b

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to sync content from mirror

        @Assert: Content is pulled down without error

        @Assert: Confirmation that various resources actually exist in
        local content repo

        @CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_sync_with_content_change(self):
        """Sync repository with changes in git puppet mirror.
        If module changes in GIT mirror but the version in manifest
        does not change, content still pulled.

        @id: 7b0484c2-df0a-46e8-95a7-1535435e6079

        @CaseLevel: Integration

        @Setup: Assure remote GIT puppet has been created and found by pulp

        @Steps:

        1.  Sync a git repo and observe the contents/checksum etc. of an
            existing puppet module
        2.  Assure a puppet module in git repo has changed but the manifest
            version for this module does not change.
        3.  Using pulp script, update repo mirror and re-sync within satellite
        4.  View contents/details of same puppet module

        @Assert: Puppet module has been updated in our content, even though
        the module's version number has not changed.

        @CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_sync_schedule(self):
        """Scheduled sync of git puppet mirror.

        @id: 1e15e4ad-35e8-493f-84f5-47ad180d2a7a

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to create a scheduled sync content from mirror

        @Assert: Content is pulled down without error  on expected schedule

        @CaseAutomation: notautomated
        """

    @stubbed()
    @tier2
    def test_positive_git_view_content(self):
        """View content in synced git puppet mirror

        @id: bb536b1b-13f6-448d-b1b2-44e2fdf93b5f

        @CaseLevel: Integration

        @Setup: git mirror (local or remote) exists as a content source

        @Steps:

        1.  Attempt to list contents of repo

        @Assert: Spot-checked items (filenames, dates, perhaps checksums?)
        are correct.

        @CaseAutomation: notautomated
        """
