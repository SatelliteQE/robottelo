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
from robottelo.constants import (
    CHECKSUM_TYPE,
    DOCKER_REGISTRY_HUB,
    FAKE_0_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    FEDORA22_OSTREE_REPO,
    FEDORA23_OSTREE_REPO,
    REPO_DISCOVERY_URL,
    REPO_TYPE,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import run_only_on, stubbed, tier1, tier2
from robottelo.helpers import read_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_repository, set_context
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


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
    def setUpClass(cls):  # noqa
        super(RepositoryTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.loc = entities.Location().create()

    def setup_navigate_syncnow(self, session, prd_name, repo_name):
        """Helps with Navigation for syncing via the repos page."""
        strategy1, value1 = locators['repo.select']
        strategy2, value2 = locators['repo.select_checkbox']
        session.nav.go_to_select_org(self.organization.name)
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
        prod = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.organization.name)
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
        product_1 = entities.Product(organization=self.organization).create()
        product_2 = entities.Product(organization=org_2).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.organization.name)
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

    @run_only_on('sat')
    @tier1
    def test_positive_create_repo_with_checksum(self):
        """Create repository with checksum type as sha256.

        @id: 06f37bb3-b0cf-4f1f-ae12-df13a6a7eaab

        @Assert: Repository is created with expected checksum type.
        """
        checksum = CHECKSUM_TYPE[u'sha256']
        # Creates new product
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.organization.name)
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
        product = entities.Product(organization=self.organization).create()
        for repo_name in invalid_values_list(interface='ui'):
            with self.subTest(repo_name):
                with Session(self.browser) as session:
                    set_context(session, org=self.organization.name)
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
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            set_context(session, org=self.organization.name)
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
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.organization.name)
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
            organization=self.organization,
        ).create()
        gpgkey_2 = entities.GPGKey(
            content=key_2_content,
            organization=self.organization,
        ).create()
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            set_context(session, org=self.organization.name)
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
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            set_context(session, org=self.organization.name)
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
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    set_context(session, org=self.organization.name)
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
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
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
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_select_loc(self.loc.name)
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
        product = entities.Product(organization=self.organization).create()
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
        product = entities.Product(organization=self.organization).create()
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
        product = entities.Product(organization=self.organization).create()
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
                        session, product.name, repo_name,)
                    # prd_sync_is_ok returns boolean values and not objects
                    self.assertTrue(self.prd_sync_is_ok(repo_name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_custom_ostree_repo(self):
        """Create Custom ostree repository.

        @id: 852cccdc-7289-4d2f-b23a-7caad2dfa195

        @Assert: Create custom ostree repository should be successful
        """
        prod = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for repo_name in generate_strings_list():
                with self.subTest(repo_name):
                    session.nav.go_to_select_org(self.organization.name)
                    self.products.click(self.products.search(prod.name))
                    make_repository(
                        session,
                        name=repo_name,
                        repo_type=REPO_TYPE['ostree'],
                        url=FEDORA23_OSTREE_REPO,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))

    @run_only_on('sat')
    @tier1
    def test_positive_delete_custom_ostree_repo(self):
        """Delete custom ostree repository.

        @id: 87dcb236-4eb4-4897-9c2a-be1d0f4bc3e7

        @Assert: Delete custom ostree repository should be successful
        """
        prod = entities.Product(organization=self.organization).create()
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
            session.nav.go_to_select_org(self.organization.name)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.delete(repo_name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_custom_ostree_repo_name(self):
        """Update custom ostree repository name.

        @id: 098ee88f-6cdb-45e0-850a-e1b71662f7ab

        @Steps: Update repo name

        @Assert: ostree repo name should be updated successfully
        """
        prod = entities.Product(organization=self.organization).create()
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
            session.nav.go_to_select_org(self.organization.name)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.update(
                repo_name, new_name=new_repo_name)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(new_repo_name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_custom_ostree_repo_url(self):
        """Update custom ostree repository url.

        @id: dfd392f9-6f1d-4d87-a43b-ced40606b8c2

        @Steps: Update ostree repo URL

        @Assert: ostree repo URL should be updated successfully
        """
        prod = entities.Product(organization=self.organization).create()
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
            session.nav.go_to_select_org(self.organization.name)
            self.products.click(self.products.search(prod.name))
            self.assertIsNotNone(self.repository.search(repo_name))
            self.repository.update(
                repo_name,
                new_url=FEDORA23_OSTREE_REPO
            )
            self.products.click(self.products.search(prod.name))
            # Validate the new repo URL
            self.assertTrue(self.repository.validate_field(
                            repo_name, 'url', FEDORA23_OSTREE_REPO))
