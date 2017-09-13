# -*- encoding: utf-8 -*-
"""Test class for GPG Key UI

:Requirement: Gpgkey

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import random
from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import (
    DISTRO_RHEL6,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    REPO_DISCOVERY_URL,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
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
    upgrade
)
from robottelo.helpers import get_data_file, read_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_gpgkey
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


def get_random_gpgkey_name():
    """Creates a random gpgkey name"""
    return random.choice(valid_data_list())


class GPGKey(UITestCase):
    """Implements tests for GPG Keys via UI"""

    @classmethod
    def setUpClass(cls):
        super(GPGKey, cls).setUpClass()
        cls.key_content = read_data_file(VALID_GPG_KEY_FILE)
        cls.key_path = get_data_file(VALID_GPG_KEY_FILE)
        cls.organization = entities.Organization().create()

    # Positive Create

    @run_only_on('sat')
    @tier1
    def test_positive_create_via_import(self):
        """Create gpg key with valid name and valid gpg key via file
        import

        :id: 3a6f3a58-da2d-4fd7-9ceb-c95f7c9dce7c

        :expectedresults: gpg key is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_gpgkey(
                        session,
                        key_path=self.key_path,
                        name=name,
                        org=self.organization.name,
                        upload_key=True,
                    )
                    self.assertIsNotNone(self.gpgkey.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_via_paste(self):
        """Create gpg key with valid name and valid gpg key text via
        cut and paste/string

        :id: 8b5d112c-b52c-458d-bddd-56bd26afdeb1

        :expectedresults: gpg key is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_gpgkey(
                        session,
                        key_content=self.key_content,
                        name=name,
                        org=self.organization.name,
                    )
                    self.assertIsNotNone(self.gpgkey.search(name))

    # Negative Create

    @run_only_on('sat')
    @tier1
    def test_negative_create_via_import_and_same_name(self):
        """Create gpg key with valid name and valid gpg key via file import
        then try to create new one with same name and same content

        :id: d5e28e8a-e0ef-4c74-a18b-e2646a2cdba5

        :expectedresults: gpg key is not created

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        kwargs = {
            'key_path': self.key_path,
            'name': name,
            'org': self.organization.name,
            'upload_key': True,
        }
        with Session(self) as session:
            make_gpgkey(session, **kwargs)
            self.assertIsNotNone(self.gpgkey.search(name))
            make_gpgkey(session, **kwargs)
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['alert.error'])
            )

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_negative_create_via_paste_and_same_name(self):
        """Create gpg key with valid name and valid gpg key text via cut and
        paste/string import then try to create new one with same name and same
        content

        :id: c6b256a5-6b9b-4927-a6c6-048ba36d2834

        :expectedresults: gpg key is not created

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        kwargs = {
            'key_content': self.key_content,
            'name': name,
            'org': self.organization.name,
        }
        with Session(self) as session:
            make_gpgkey(session, **kwargs)
            self.assertIsNotNone(self.gpgkey.search(name))
            make_gpgkey(session, **kwargs)
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['alert.error'])
            )

    @run_only_on('sat')
    @tier1
    def test_negative_create_without_content(self):
        """Create gpg key with valid name and no gpg key

        :id: 20167716-48c5-4f28-afe2-07fa22aeb240

        :expectedresults: gpg key is not created

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        with Session(self) as session:
            make_gpgkey(session, name=name, org=self.organization.name)
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['alert.error'])
            )
            self.assertIsNone(self.gpgkey.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_via_import_and_invalid_name(self):
        """Create gpg key with invalid name and valid gpg key via file import

        :id: bc5f96e6-e997-4995-ad04-614e66480b7f

        :expectedresults: gpg key is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_names_list():
                with self.subTest(name):
                    make_gpgkey(
                        session,
                        key_path=self.key_path,
                        name=name,
                        org=self.organization.name,
                        upload_key=True,
                    )
                    self.assertIsNotNone(
                        self.gpgkey.wait_until_element(
                            common_locators['alert.error'])
                    )
                    self.assertIsNone(self.gpgkey.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_via_paste_and_invalid_name(self):
        """Create gpg key with invalid name and valid gpg key text via cut and
        paste/string

        :id: 652857de-c522-4c68-a758-13d0b37cc62a

        :expectedresults: gpg key is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_names_list():
                with self.subTest(name):
                    make_gpgkey(
                        session,
                        key_content=self.key_content,
                        name=name,
                        org=self.organization.name,
                    )
                    self.assertIsNotNone(
                        self.gpgkey.wait_until_element(
                            common_locators['alert.error'])
                    )
                    self.assertIsNone(self.gpgkey.search(name))

    # Positive Delete

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete_for_imported_content(self):
        """Create gpg key with valid name and valid gpg key via file import
        then delete it

        :id: 495547c0-8e38-49cc-9be4-3f24a20d3af7

        :expectedresults: gpg key is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_gpgkey(
                        session,
                        key_path=self.key_path,
                        name=name,
                        org=self.organization.name,
                        upload_key=True,
                    )
                    self.assertIsNotNone(self.gpgkey.search(name))
                    self.gpgkey.delete(name)

    @run_only_on('sat')
    @tier1
    def test_positive_delete_for_pasted_content(self):
        """Create gpg key with valid name and valid gpg key text via cut and
        paste/string then delete it

        :id: 77c97202-a877-4647-b7e2-3a9b68945fc4

        :expectedresults: gpg key is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_gpgkey(
                        session,
                        key_content=self.key_content,
                        name=name,
                        org=self.organization.name,
                    )
                    self.assertIsNotNone(self.gpgkey.search(name))
                    self.gpgkey.delete(name)

    # Positive Update

    @run_only_on('sat')
    @tier1
    def test_positive_update_name_for_imported_content(self):
        """Create gpg key with valid name and valid gpg key via file
        import then update its name

        :id: 85e211fb-bcb4-4895-af3e-febb189be5c0

        :expectedresults: gpg key is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        with Session(self) as session:
            make_gpgkey(
                session,
                key_path=self.key_path,
                name=name,
                org=self.organization.name,
                upload_key=True,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertIsNotNone(self.gpgkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.assertIsNotNone(self.gpgkey.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_file_for_imported_content(self):
        """Create gpg key with valid name and valid gpg key via file
        import then update its gpg key file

        :id: 9f74b337-3ea5-48a1-af6e-d72ab41c2348

        :expectedresults: gpg key is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        with Session(self) as session:
            make_gpgkey(
                session,
                key_path=self.key_path,
                name=name,
                org=self.organization.name,
                upload_key=True,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_key=new_key_path)
            self.assertIsNotNone(self.gpgkey.wait_until_element(
                common_locators['alert.success_sub_form']))

    @run_only_on('sat')
    @tier1
    def test_positive_update_name_for_pasted_content(self):
        """Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its name

        :id: 4336b539-15fd-4a40-bb98-0b0248f8abd8

        :expectedresults: gpg key is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        with Session(self) as session:
            make_gpgkey(
                session,
                key_content=self.key_content,
                name=name,
                org=self.organization.name,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertIsNotNone(self.gpgkey.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.assertIsNotNone(self.gpgkey.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_file_for_pasted_content(self):
        """Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its gpg key text

        :id: 07902ef6-a918-433a-9dad-d5376c3dd001

        :expectedresults: gpg key is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        with Session(self) as session:
            make_gpgkey(
                session,
                key_content=self.key_content,
                name=name,
                org=self.organization.name,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_key=new_key_path)
            self.assertIsNotNone(self.gpgkey.wait_until_element(
                common_locators['alert.success_sub_form']))

    # Negative Update

    @run_only_on('sat')
    @tier1
    def test_negative_update_name_for_imported_content(self):
        """Create gpg key with valid name and valid gpg key via file
        import then fail to update its name

        :id: 969aad7c-ba4c-4d1d-84a5-c9e1b9130867

        :expectedresults: gpg key is not updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_gpgkey(
                session,
                key_path=self.key_path,
                name=name,
                org=self.organization.name,
                upload_key=True,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.gpgkey.update(name, new_name)
                    self.assertIsNotNone(self.gpgkey.wait_until_element(
                        common_locators['alert.error_sub_form']
                    ))
                    self.assertIsNone(self.gpgkey.search(new_name))

    @run_only_on('sat')
    @skip_if_not_set('clients')
    @tier3
    @upgrade
    def test_positive_consume_content_using_repo(self):
        """Hosts can install packages using gpg key associated with single
        custom repository

        :id: c6b78312-91d3-47a2-a6c6-f906a4522fe4

        :expectedresults: host can install package from custom repository

        :CaseLevel: System
        """
        key_name = gen_string('alphanumeric')
        # step1: Create gpg-key
        gpgkey = entities.GPGKey(
            content=read_data_file(ZOO_CUSTOM_GPG_KEY),
            name=key_name,
            organization=self.organization,
        ).create()
        # step 1.2: Create new lifecycle environments
        lc_env = entities.LifecycleEnvironment(
            organization=self.organization
        ).create()
        # step2: Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # step3: Creates new repository with GPGKey
        repo = entities.Repository(
            name=gen_string('alpha'),
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpgkey,
        ).create()
        # step 3.1: sync repository
        repo.sync()
        # step 4: Create content view
        content_view = entities.ContentView(
            organization=self.organization
        ).create()
        # step 5: Associate repository to new content view
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        # step 6: Publish content view
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        # step 6.2: Promote content view to lifecycle_env
        content_view.version[0].promote(data={u'environment_id': lc_env.id})
        # step 7: Create activation key
        act_key = entities.ActivationKey(
            content_view=content_view,
            environment=lc_env,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        for sub in entities.Subscription(
                organization=self.organization).search():
            if sub.read_json()['product_name'] == product.name:
                act_key.add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': sub.id,
                })
                break
        # Create VM
        package_name = 'cow'
        with VirtualMachine(distro=DISTRO_RHEL6) as vm:
            # Download and Install rpm
            result = vm.run(
                "wget -nd -r -l1 --no-parent -A '*-latest.noarch.rpm'"
                " http://{0}/pub/"
                .format(settings.server.hostname)
            )
            self.assertEqual(result.return_code, 0)
            result = vm.run(
                'rpm -i katello-ca-consumer*.noarch.rpm'
            )
            self.assertEqual(
                result.return_code, 0,
                'failed to install katello-ca rpm: {0} and return code: {1}'
                .format(result.stderr, result.return_code)
            )
            # Register client with foreman server using activation-key
            result = vm.run(
                u'subscription-manager register --activationkey {0} '
                '--org {1} --force'
                .format(act_key.name, self.organization.label)
            )
            # Commenting following lines because:
            # When we register a host without associating the installed OS
            # subscriptions, SM register command succeed with exit code '1'.
            # self.assertEqual(
            #    result.return_code, 0,
            #    "failed to register client:: {0} and return code: {1}"
            #    .format(result.stderr, result.return_code)
            # )

            # Validate if gpgcheck flag is enabled in repo file
            repo_file = '/etc/yum.repos.d/redhat.repo'
            result = vm.run(
                'cat {0} | grep gpgcheck | cut -d " " -f3'
                .format(repo_file)
            )
            self.assertEqual(u'1', result.stdout[0])
            # Install contents from sat6 server
            result = vm.run('yum install -y {0}'.format(package_name))
            self.assertEqual(
                result.return_code, 0,
                'Package install failed: {0} and return code: {1}'
                .format(result.stderr, result.return_code)
            )
            # Verify if package is installed by query it
            result = vm.run('rpm -q {0}'.format(package_name))
            self.assertEqual(result.return_code, 0)

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_consume_content_using_repos(self):
        """Hosts can install packages using gpg key associated with
        multiple custom repositories

        :id: bef406dd-1266-4c87-8eac-9bbdb6f81085

        :expectedresults: host can install package from custom repositories

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier3
    def test_positive_consume_content_using_repos_and_different_keys(self):
        """Hosts can install packages using different gpg keys
        associated with multiple custom repositories

        :id: ad48a055-72d3-4f4b-a0dc-faee1e29e28e

        :expectedresults: host can install package from custom repositories

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @run_only_on('sat')
    @tier1
    def test_positive_info(self):
        """Create single gpg key and get its info

        :id: c8b75db1-9394-4a99-9d91-0d388aacfd1a

        :expectedresults: specific information for gpg key matches the creation
            values

        :caseautomation: notautomated

        :CaseImportance: Critical
        """


class GPGKeyProductAssociateTestCase(UITestCase):
    """Implements Product Association tests for GPG Keys via UI"""

    @classmethod
    def setUpClass(cls):
        super(GPGKeyProductAssociateTestCase, cls).setUpClass()
        cls.key_content = read_data_file(VALID_GPG_KEY_FILE)
        cls.key_path = get_data_file(VALID_GPG_KEY_FILE)
        cls.organization = entities.Organization().create()

    @run_only_on('sat')
    @tier2
    def test_positive_add_empty_product(self):
        """Create gpg key with valid name and valid gpg key then associate
        it with empty (no repos) custom product

        :id: e18ae9f5-43d9-4049-92ca-1eafaca05096

        :expectedresults: gpg key is associated with product

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product.name)
            )

    @run_only_on('sat')
    @tier2
    def test_positive_add_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key then associate it
        with custom product that has one repository

        :id: 7514b33a-da75-43bd-a84b-5a805c84511d

        :expectedresults: gpg key is associated with product as well as with
            the repository

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository without GPGKey
        repo = entities.Repository(
            name=gen_string('alpha'),
            url=FAKE_1_YUM_REPO,
            product=product,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that GPGKey is associated with product and repository
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    name, repo.name, entity_type='Repository'
                )
            )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1411800)
    @tier2
    def test_positive_add_product_and_search(self):
        """Create gpg key with valid name and valid gpg key
        then associate it with custom product that has one repository
        After search and select product through gpg key interface

        :id: 0bef0c1b-4811-489e-89e9-609d57fc45ee

        :expectedresults: Associated product can be found and selected through
            gpg key 'Product' tab

        :BZ: 1411800

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            name=gen_string('alpha'),
            url=FAKE_1_YUM_REPO,
            product=product,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            product_element = self.gpgkey.get_product_repo(name, product.name)
            self.gpgkey.click(product_element)
            self.assertIsNone(self.gpgkey.wait_until_element(
                common_locators['alert.error']))
            self.assertIsNotNone(self.products.wait_until_element(
                locators['prd.title'] % product.name))

    @run_only_on('sat')
    @tier2
    def test_positive_add_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key then associate it
        with custom product that has more than one repository

        :id: 0edffad7-0ab4-4bef-b16b-f6c8de55b0dc

        :expectedresults: gpg key is properly associated with repositories

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository_1 without GPGKey
        repo1 = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # Creates new repository_2 without GPGKey
        repo2 = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that GPGKey is associated with product and repository
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            for repo in [repo1, repo2]:
                self.assertIsNotNone(
                    self.gpgkey.get_product_repo(
                        name, repo.name, entity_type='Repository'
                    )
                )

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_add_product_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key
        then associate it with custom product using Repo discovery method

        :id: 7490a5a6-8575-45eb-addc-298ed3b62649

        :expectedresults: gpg key is associated with product as well as with
            the repositories

        :BZ: 1210180, 1461804

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        product_name = gen_string('alpha')
        with Session(self) as session:
            make_gpgkey(
                session,
                key_content=self.key_content,
                name=name,
                org=self.organization.name,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            session.nav.go_to_products()
            self.repository.discover_repo(
                REPO_DISCOVERY_URL,
                ['fakerepo01/'],
                gpg_key=name,
                new_product=True,
                product=product_name,
            )
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product_name)
            )
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    name, 'fakerepo01', entity_type='Repository'
                )
            )

    @run_only_on('sat')
    @tier2
    def test_positive_add_repo_from_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key then associate it
        to repository from custom product that has one repository

        :id: 5d78890f-4130-4dc3-9cfe-48999149422f

        :expectedresults: gpg key is associated with the repository but not
            with the product

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(
            name=gen_string('alpha'),
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    name, repo.name, entity_type='Repository')
            )

    @run_only_on('sat')
    @tier2
    def test_positive_add_repo_from_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key then associate it
        to repository from custom product that has more than one repository

        :id: 1fb38e01-4c04-4609-842d-069f96157317

        :expectedresults: gpg key is associated with one of the repositories
            but not with the product

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository with GPGKey
        repo1 = entities.Repository(
            name=gen_string('alpha'),
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        # Creates new repository without GPGKey
        repo2 = entities.Repository(
            name=gen_string('alpha'),
            url=FAKE_2_YUM_REPO,
            product=product,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            # Assert that GPGKey is associated with first repository
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    name, repo1.name, entity_type='Repository'
                )
            )
            # Assert that GPGKey is not associated with second repository
            self.assertIsNone(
                self.gpgkey.get_product_repo(
                    name, repo2.name, entity_type='Repository'
                )
            )

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_add_repos_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key then
        associate it to repos from custom product using Repo discovery method

        :id: d841f0f2-8623-443f-8deb-212cee9a247e

        :expectedresults: gpg key is associated with product and all the
            repositories

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_empty_product(self):
        """Create gpg key with valid name and valid gpg key then associate it
        with empty (no repos) custom product then update the key

        :id: 519817c3-9b67-4859-8069-95987ebf9453

        :expectedresults: gpg key is associated with product before/after
            update

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        new_name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            # Update the Key name
            self.gpgkey.update(name, new_name)
            # Again assert that GPGKey is associated with product
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(new_name, product.name)
            )

    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key then associate it
        with custom product that has one repository then update the key

        :id: 02cb0601-6aa2-4589-b61e-3d3785a7e100

        :expectedresults: gpg key is associated with product as well as with
            repository before/after update

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository without GPGKey
        repo = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()

        new_name = gen_string('alpha')
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that before update GPGKey is associated with product, repo
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    name, repo.name, entity_type='Repository'
                )
            )
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is associated with product, repo
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(new_name, product.name)
            )
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    new_name, repo.name, entity_type='Repository'
                )
            )

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_update_key_for_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key then associate it
        with custom product that has more than one repository then update the
        key

        :id: 3ca4d9ff-8032-4c2a-aed9-00ac2d1352d1

        :expectedresults: gpg key is associated with product as well as with
            repositories before/after update

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository_1 without GPGKey
        repo1 = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # Creates new repository_2 without GPGKey
        repo2 = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()

        new_name = gen_string('alpha')
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that before update GPGKey is associated with product, repo
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            for repo in [repo1, repo2]:
                self.assertIsNotNone(
                    self.gpgkey.get_product_repo(
                        name, repo.name, entity_type='Repository'
                    )
                )
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is associated with product, repo
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(new_name, product.name)
            )
            for repo in [repo1, repo2]:
                self.assertIsNotNone(
                    self.gpgkey.get_product_repo(
                        new_name, repo.name, entity_type='Repository'
                    )
                )

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_update_key_for_product_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key
        then associate it with custom product using Repo discovery
        method then update the key

        :id: 49279be8-cbea-477e-a1ff-c07171e7084e

        :expectedresults: gpg key is associated with product as well as with
            repository before/after update

        :BZ: 1210180, 1461804

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        new_name = gen_string('alpha')
        product_name = gen_string('alpha')
        entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_products()
            # Perform repo discovery
            self.repository.discover_repo(
                REPO_DISCOVERY_URL,
                ['fakerepo01/'],
                gpg_key=name,
                new_product=True,
                product=product_name,
            )
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product_name)
            )
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    name, 'fakerepo01', entity_type='Repository'
                )
            )
            self.gpgkey.update(name, new_name)
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(new_name, product_name)
            )
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    new_name, 'fakerepo01', entity_type='Repository'
                )
            )

    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_repo_from_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key then associate it
        to repository from custom product that has one repository then update
        the key

        :id: 9827306e-76d7-4aef-8074-e97fc39d3bbb

        :expectedresults: gpg key is associated with repository before/after
            update but not with product.

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()

        new_name = gen_string('alpha')
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    name, repo.name, entity_type='Repository'
                )
            )
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.get_product_repo(new_name, product.name)
            )
            # Assert that after update GPGKey is still associated
            # with repository
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    new_name, repo.name, entity_type='Repository'
                )
            )

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_update_key_for_repo_from_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key then associate it
        to repository from custom product that has more than one repository
        then update the key

        :id: d4f2fa16-860c-4ad5-b04f-8ce24b5618e9

        :expectedresults: gpg key is associated with single repository
            before/after update but not with product

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository_1 with GPGKey
        repo1 = entities.Repository(
            name=gen_string('alpha'),
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        # Creates new repository_2 without GPGKey
        repo2 = entities.Repository(
            name=gen_string('alpha'),
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()

        new_name = gen_string('alpha')
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            # Assert that GPGKey is associated with first repository
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    name, repo1.name, entity_type='Repository'
                )
            )
            # Assert that GPGKey is not associated with second repository
            self.assertIsNone(
                self.gpgkey.get_product_repo(
                    name, repo2.name, entity_type='Repository'
                )
            )
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.get_product_repo(new_name, product.name)
            )
            # Assert that after update GPGKey is associated with first
            # repository
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    new_name, repo1.name, entity_type='Repository'
                )
            )
            # Assert that after update GPGKey is not associated with second
            # repository
            self.assertIsNone(
                self.gpgkey.get_product_repo(
                    new_name, repo2.name, entity_type='Repository'
                )
            )

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_update_key_for_repos_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key
        then associate it to repos from custom product
        using Repo discovery method then update the key

        :id: d0777db3-109a-4c63-9387-7cff235c5f46

        :expectedresults: gpg key is associated with product and all
            repositories before/after update

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_empty_product(self):
        """Create gpg key with valid name and valid gpg key then
        associate it with empty (no repos) custom product then delete it

        :id: b9766403-61b2-4a88-a744-a25d53d577fb

        :expectedresults: gpg key is associated with product during creation
            but removed from product after deletion

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            self.gpgkey.delete(name)
            # Assert GPGKey isn't associated with product
            prd_element = self.products.search(product.name)
            self.assertIsNone(
                self.gpgkey.assert_key_from_product(name, prd_element))

    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key then
        associate it with custom product that has one repository then delete it

        :id: 75057dd2-9083-47a8-bea7-4f073bdb667e

        :expectedresults: gpg key is associated with product as well as with
            the repository during creation but removed from product after
            deletion

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository without GPGKey
        repo = entities.Repository(
            name=gen_string('alpha'),
            url=FAKE_1_YUM_REPO,
            product=product,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(name, product.name)
            )
            self.assertIsNotNone(
                self.gpgkey.get_product_repo(
                    name, repo.name, entity_type='Repository'
                )
            )
            self.gpgkey.delete(name)
            # Assert GPGKey isn't associated with product
            prd_element = self.products.search(product.name)
            self.assertIsNone(
                self.gpgkey.assert_key_from_product(name, prd_element))
            prd_element = self.products.search(product.name)
            self.assertIsNone(
                self.gpgkey.assert_key_from_product(
                    name, prd_element, repo.name)
            )

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_delete_key_for_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key then
        associate it with custom product that has more than one repository then
        delete it

        :id: cb5d4efd-863a-4b8e-b1f8-a0771e90ff5e

        :expectedresults: gpg key is associated with product as well as with
            repositories during creation but removed from product after
            deletion

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=gen_string('alpha'),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=gen_string('alpha'),
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.gpgkey.delete(name)
            # Assert GPGKey isn't associated with product
            prd_element = self.products.search(product.name)
            self.assertIsNone(
                self.gpgkey.assert_key_from_product(name, prd_element))

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_delete_key_for_product_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg then associate
        it with custom product using Repo discovery method then delete it

        :id: 513ae138-84d9-4c43-8d4e-7b9fb797208d

        :expectedresults: gpg key is associated with product as well as with
            the repositories during creation but removed from product after
            deletion

        :BZ: 1210180, 1461804

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        product_name = gen_string('alpha')
        entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_products()
            # Perform repo discovery
            self.repository.discover_repo(
                REPO_DISCOVERY_URL,
                ['fakerepo01/'],
                gpg_key=name,
                new_product=True,
                product=product_name,
            )
            self.gpgkey.delete(name)
            prd_element = self.products.search(product_name)
            self.assertIsNone(
                self.gpgkey.assert_key_from_product(name, prd_element))

    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_repo_from_product_with_repo(self):
        """Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository
        then delete the key

        :id: 92ba492e-79af-48fe-84cb-763102b42fa7

        :expectedresults: gpg key is associated with single repository during
            creation but removed from repository after deletion

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(
            name=gen_string('alpha'),
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.gpgkey.delete(name)
            # Assert that after deletion GPGKey is not associated with product
            prd_element = self.products.search(product.name)
            self.assertIsNone(self.gpgkey.assert_key_from_product(
                name, prd_element, repo.name))

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_delete_key_for_repo_from_product_with_repos(self):
        """Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has more than
        one repository then delete the key

        :id: 5f204a44-bf7b-4a9c-9974-b701e0d38860

        :expectedresults: gpg key is associated with single repository but not
            with product during creation but removed from repository after
            deletion

        :BZ: 1461804

        :CaseLevel: Integration
        """
        name = get_random_gpgkey_name()
        # Creates New GPGKey
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without GPGKey association
        product = entities.Product(
            name=gen_string('alpha'),
            organization=self.organization,
        ).create()
        # Creates new repository_1 with GPGKey association
        repo = entities.Repository(
            gpg_key=gpg_key,
            name=gen_string('alpha'),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        entities.Repository(
            name=gen_string('alpha'),
            product=product,
            url=FAKE_2_YUM_REPO,
            # notice that we're not making this repo point to the GPG key
        ).create()
        with Session(self) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.gpgkey.delete(name)
            # Assert key shouldn't be associated with product or repository
            # after deletion
            prd_element = self.products.search(product.name)
            self.assertIsNone(self.gpgkey.assert_key_from_product(
                name, prd_element))
            prd_element = self.products.search(product.name)
            self.assertIsNone(self.gpgkey.assert_key_from_product(
                name, prd_element, repo.name))

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_delete_key_for_repos_using_repo_discovery(self):
        """Create gpg key with valid name and valid gpg key then
        associate it to repos from custom product using Repo discovery method
        then delete the key

        :id: b1ece282-0cba-4816-9e6a-312c63894168

        :expectedresults: gpg key is associated with product and all
            repositories during creation but removed from product and all
            repositories after deletion

        :caseautomation: notautomated

        :CaseLevel: Integration
        """
