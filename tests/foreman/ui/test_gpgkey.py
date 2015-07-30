# -*- encoding: utf-8 -*-
"""Test class for GPG Key UI"""

from ddt import ddt
from fauxfactory import gen_string
from nailgun import client, entities
from robottelo.common import conf
from robottelo.common.constants import (
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    REPO_DISCOVERY_URL,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
    ZOO_CUSTOM_GPG_KEY,
)
from robottelo.common.decorators import (
    data, run_only_on, skip_if_bug_open, stubbed)
from robottelo.common.helpers import (
    get_data_file, read_data_file, valid_data_list, invalid_names_list,
    generate_strings_list, get_server_credentials)
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_gpgkey
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine


@run_only_on('sat')
@ddt
class GPGKey(UITestCase):
    """Implements tests for GPG Keys via UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        org_attrs = entities.Organization().create_json()
        cls.org_name = org_attrs['name']
        cls.org_id = org_attrs['id']
        cls.org_label = org_attrs['label']

        super(GPGKey, cls).setUpClass()

    # Positive Create

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_positive_create_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        via file import

        @feature: GPG Keys

        @assert: gpg key is created

        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_positive_create_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string

        @feature: GPG Keys

        @assert: gpg key is created

        """
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))

    # Negative Create

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_negative_create_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key via
        file import then try to create new one with same name

        @feature: GPG Keys

        @assert: gpg key is not created

        """

        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            make_gpgkey(session, org=self.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.wait_until_element
                                 (common_locators["alert.error"]))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_negative_create_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string import then try to create new one with same name

        @feature: GPG Keys

        @assert: gpg key is not created

        """

        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            make_gpgkey(session, org=self.org_name,
                        name=name, key_content=key_content)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_negative_create_3(self, name):
        """@test: Create gpg key with valid name and no gpg key

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        with Session(self.browser) as session:
            with self.assertRaises(UIError):
                make_gpgkey(
                    session, org=self.org_name, name=name)
            self.assertIsNone(self.gpgkey.search(name))

    @data(*invalid_names_list())
    def test_negative_create_4(self, name):
        """@test: Create gpg key with invalid name and valid gpg key via
        file import

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))
            self.assertIsNone(self.gpgkey.search(name))

    def test_negative_create_5(self):
        """@test: Create gpg key with blank name and valid gpg key via
        file import

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        name = " "
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["haserror"]))
            self.assertIsNone(self.gpgkey.search(name))

    @data(*invalid_names_list())
    def test_negative_create_6(self, name):
        """@test: Create gpg key with invalid name and valid gpg key text via
        cut and paste/string

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, key_content=key_content)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))
            self.assertIsNone(self.gpgkey.search(name))

    # Positive Delete

    @data(*valid_data_list())
    def test_positive_delete_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then delete it

        @feature: GPG Keys

        @assert: gpg key is deleted

        """
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))

    @data(*valid_data_list())
    def test_positive_delete_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then delete it

        @feature: GPG Keys

        @assert: gpg key is deleted

        """
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))

    # Positive Update

    def test_positive_update_1(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then update its name

        @feature: GPG Keys

        @assert: gpg key is updated

        """
        name = gen_string("alpha", 6)
        new_name = gen_string("alpha", 6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.success"]))

    @skip_if_bug_open('bugzilla', 1204602)
    def test_positive_update_2(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then update its gpg key file

        @feature: GPG Keys

        @assert: gpg key is updated

        @bz: 1204602

        """
        name = gen_string("alpha", 6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_key=new_key_path)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.success"]))

    def test_positive_update_3(self):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its name

        @feature: GPG Keys

        @assert: gpg key is updated

        """
        name = gen_string("alpha", 6)
        new_name = gen_string("alpha", 6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.success"]))

    @skip_if_bug_open('bugzilla', 1204602)
    def test_positive_update_4(self):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its gpg key text

        @feature: GPG Keys

        @assert: gpg key is updated

        @bz: 1204602

        """
        name = gen_string("alpha", 6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_key=new_key_path)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.success"]))

    # Negative Update

    @data(*invalid_names_list())
    def test_negative_update_1(self, new_name):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then fail to update its name

        @feature: GPG Keys

        @assert: gpg key is not updated

        """
        name = gen_string("alpha", 6)
        key_path = get_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, upload_key=True,
                        key_path=key_path)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))
            self.assertIsNone(self.gpgkey.search(new_name))

    @data(*invalid_names_list())
    def test_negative_update_2(self, new_name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then fail to update its name

        @feature: GPG Keys

        @assert: gpg key is not updated

        """
        name = gen_string("alpha", 6)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertTrue(self.gpgkey.wait_until_element
                            (common_locators["alert.error"]))
            self.assertIsNone(self.gpgkey.search(new_name))

    @data(*valid_data_list())
    def test_consume_content_1(self, key_name):
        """@test: Hosts can install packages using gpg key associated with
        single custom repository

        @feature: GPG Keys

        @assert: host can install package from custom repository

        @status: manual

        """

        product_name = gen_string('alpha', 8)
        repository_name = gen_string('alpha', 8)
        activation_key_name = gen_string('alpha', 8)
        key_content = read_data_file(ZOO_CUSTOM_GPG_KEY)
        # step1: Create gpg-key
        gpgkey_id = entities.GPGKey(
            content=key_content,
            name=key_name,
            organization=self.org_id
        ).create_json()['id']
        # step 1.2: Create new lifecycle environments
        lc_env_id = entities.LifecycleEnvironment(
            organization=self.org_id
        ).create_json()['id']
        # step2: Creates new product without selecting GPGkey
        product_id = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create_json()['id']
        # step3: Creates new repository with GPGKey
        repo = entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_id,
            gpg_key=gpgkey_id,
        ).create()
        # step 3.1: sync repository
        repo.sync()
        # step 4: Create content view
        content_view = entities.ContentView(
            organization=self.org_id
        ).create()
        # step 5: Associate repository to new content view
        client.put(
            content_view.path(),
            {u'repository_ids': [repo.id]},
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()
        # step 6: Publish content view
        content_view.publish()
        # step 6.2: Promote content view to lifecycle_env
        cv = entities.ContentView(id=content_view.id).read_json()
        self.assertEqual(len(cv['versions']), 1)
        entities.ContentViewVersion(
            id=cv['versions'][0]['id']
        ).promote({u'environment_id': lc_env_id})
        # step 7: Create activation key
        ak_id = entities.ActivationKey(
            name=activation_key_name,
            environment=lc_env_id,
            organization=self.org_id,
            content_view=content_view.id,
        ).create().id
        for subscription in entities.Subscription(
                organization=self.org_id).search():
            if subscription.read_json()['product_name'] == product_name:
                entities.ActivationKey(id=ak_id).add_subscriptions({
                    'quantity': 1,
                    'subscription_id': subscription.id,
                })
                break
        # Create VM
        package_name = 'cow'
        with VirtualMachine(distro='rhel66') as vm:
            # Download and Install rpm
            result = vm.run(
                "wget -nd -r -l1 --no-parent -A '*.noarch.rpm' http://{0}/pub/"
                .format(conf.properties['main.server.hostname'])
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
                .format(activation_key_name, self.org_label)
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
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_consume_content_2(self):
        """@test: Hosts can install packages using gpg key associated with
        multiple custom repositories

        @feature: GPG Keys

        @assert: host can install package from custom repositories

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_consume_content_3(self):
        """@test: Hosts can install packages using different gpg keys
        associated with multiple custom repositories

        @feature: GPG Keys

        @assert: host can install package from custom repositories

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_list_key_1(self):
        """@test: Create gpg key and list it

        @feature: GPG Keys

        @assert: gpg key is displayed/listed

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_search_key_1(self):
        """@test: Create gpg key and search/find it

        @feature: GPG Keys

        @assert: gpg key can be found

        @status: manual

        """

        pass

    @stubbed()
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_info_key_1(self):
        """@test: Create single gpg key and get its info

        @feature: GPG Keys

        @assert: specific information for gpg key matches the creation values

        @status: manual

        """

        pass


@run_only_on('sat')
@ddt
class GPGKeyProductAssociate(UITestCase):
    """Implements Product Association tests for GPG Keys via UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        org_attrs = entities.Organization().create_json()
        cls.org_name = org_attrs['name']
        cls.org_id = org_attrs['id']

        super(GPGKeyProductAssociate, cls).setUpClass()

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with empty (no repos) custom product

        @feature: GPG Keys

        @assert: gpg key is associated with product

        """
        product_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product and associate GPGKey with it
        entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has one repository

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as
        with the repository

        """

        product_name = gen_string("alpha", 8)
        repository_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create_json()
        # Creates new repository without GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_3(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has more than one repository

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        the repositories

        """

        product_name = gen_string("alpha", 8)
        repository_1_name = gen_string("alpha", 8)
        repository_2_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create_json()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id']
        ).create_json()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id']
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @skip_if_bug_open('bugzilla', 1085035)
    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_4(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product using Repo discovery method

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        the repositories

        @BZ: 1085035

        """

        product_name = gen_string("alpha", 8)
        url = REPO_DISCOVERY_URL
        discovered_urls = ["fakerepo01/"]
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        with Session(self.browser) as session:
            make_gpgkey(session, org=self.org_name,
                        name=name, key_content=key_content)
            self.assertIsNotNone(self.gpgkey.search(name))
            session.nav.go_to_products()
            self.repository.discover_repo(url, discovered_urls,
                                          product=product_name,
                                          new_product=True,
                                          gpg_key=name)
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_5(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository

        @feature: GPG Keys

        @assert: gpg key is associated with the repository but not with
        the product

        """

        product_name = gen_string("alpha", 8)
        repository_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create_json()
        # Creates new repository with GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_6(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has more than
        one repository

        @feature: GPG Keys

        @assert: gpg key is associated with one of the repositories but
        not with the product

        """

        product_name = gen_string("alpha", 8)
        repository_1_name = gen_string("alpha", 8)
        repository_2_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create_json()
        # Creates new repository with GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create_json()
        # Creates new repository without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is not associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))

    @skip_if_bug_open('bugzilla', 1085924)
    @stubbed()
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_7(self):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repos from custom product using Repo discovery method

        @feature: GPG Keys

        @assert: gpg key is associated with product and all the repositories

        @status: manual

        @BZ: 1085924

        """

        pass

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_8(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it with empty (no repos) custom product then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product before/after update

        """
        new_name = gen_string("alpha", 8)
        product_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product and associate GPGKey with it
        entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Update the Key name
            self.gpgkey.update(name, new_name)
            # Again assert that GPGKey is associated with product
            self.assertEqual(product_name, self.gpgkey.assert_product_repo
                             (new_name, product=True))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_9(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has one repository
        then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        reposiotry before/after update

        """

        product_name = gen_string("alpha", 8)
        new_name = gen_string("alpha", 8)
        repository_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create_json()
        # Creates new repository without GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that before update GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that before update GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=True))
            # Assert that after update GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=False))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_10(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has more than one
        repository then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        reposiories before/after update

        """

        product_name = gen_string("alpha", 8)
        new_name = gen_string("alpha", 8)
        repository_1_name = gen_string("alpha", 8)
        repository_2_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create_json()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create_json()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that before update GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that before update GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=True))
            # Assert that after update GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=False))

    @skip_if_bug_open('bugzilla', 1210180)
    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_11(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product using Repo discovery
        method then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        repository before/after update

        @BZ: 1085035

        """

        prd_name = gen_string("alpha", 8)
        new_name = gen_string("alpha", 8)
        url = REPO_DISCOVERY_URL
        discovered_urls = ["fakerepo01/"]
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_products()
            # Perform repo discovery
            self.repository.discover_repo(url, discovered_urls,
                                          product=prd_name, new_product=True,
                                          gpg_key=name)
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.update(name, new_name)
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=True))
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=False))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_12(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository
        then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with repository
        before/after update but not with product.

        """

        product_name = gen_string("alpha", 8)
        new_name = gen_string("alpha", 8)
        repository_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create_json()
        # Creates new repository with GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (new_name, product=True))
            # Assert that after update GPGKey is still associated
            # with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=False))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_13(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has more than
        one repository then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with single repository
        before/after update but not with product

        """

        product_name = gen_string("alpha", 8)
        new_name = gen_string("alpha", 8)
        repository_1_name = gen_string("alpha", 8)
        repository_2_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create_json()
        # Creates new repository_1 with GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create_json()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (new_name, product=True))
            # Assert that after update GPGKey is not associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (new_name, product=False))

    @skip_if_bug_open('bugzilla', 1085924)
    @stubbed()
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_14(self):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it to repos from custom product
        using Repo discovery method then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product and all repositories
        before/after update

        @status: manual

        @BZ: 1085924

        """

        pass

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_15(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with empty (no repos) custom
        product then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product during creation but
        removed from product after deletion

        """

        product_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product and associate GPGKey with it
        entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert that after deletion GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_16(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it with custom product that has one repository then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with the
        repository during creation but removed from product after deletion

        """

        product_name = gen_string("alpha", 8)
        repository_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create_json()
        # Creates new repository without GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert that after deletion GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_17(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has
        more than one repository then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        repositories during creation but removed from product after deletion

        """

        product_name = gen_string("alpha", 8)
        repository_1_name = gen_string("alpha", 8)
        repository_2_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product and associate GPGKey with it
        product_attrs = entities.Product(
            name=product_name,
            gpg_key=gpgkey_attrs['id'],
            organization=self.org_id
        ).create_json()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
        ).create_json()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert that after deletion GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name))

    @skip_if_bug_open('bugzilla', 1085035)
    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_18(self, name):
        """@test: Create gpg key with valid name and valid gpg then associate
        it with custom product using Repo discovery method then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        the repositories during creation but removed from product
        after deletion

        @BZ: 1085035

        """

        prd_name = gen_string("alpha", 8)
        url = REPO_DISCOVERY_URL
        discovered_urls = ["fakerepo01/"]
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_products()
            # Perform repo discovery
            self.repository.discover_repo(url, discovered_urls,
                                          product=prd_name, new_product=True,
                                          gpg_key=name)
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=True))
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, prd_name))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_19(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository
        then delete the key

        @feature: GPG Keys

        @assert: gpg key is associated with single repository
        during creation but removed from repository after deletion

        """

        product_name = gen_string("alpha", 8)
        repository_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product without selecting GPGkey
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create_json()
        # Creates new repository with GPGKey
        entities.Repository(
            name=repository_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert that after deletion GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name, repository_name))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_20(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has more than
        one repository then delete the key

        @feature: GPG Keys

        @assert: gpg key is associated with single repository but not
        with product during creation but removed from
        repository after deletion

        """

        product_name = gen_string("alpha", 8)
        repository_1_name = gen_string("alpha", 8)
        repository_2_name = gen_string("alpha", 8)
        key_content = read_data_file(VALID_GPG_KEY_FILE)
        # Creates New GPGKey
        gpgkey_attrs = entities.GPGKey(
            name=name,
            content=key_content,
            organization=self.org_id
        ).create_json()
        # Creates new product without GPGKey association
        product_attrs = entities.Product(
            name=product_name,
            organization=self.org_id
        ).create_json()
        # Creates new repository_1 with GPGKey association
        entities.Repository(
            name=repository_1_name,
            url=FAKE_1_YUM_REPO,
            product=product_attrs['id'],
            gpg_key=gpgkey_attrs['id'],
        ).create_json()
        entities.Repository(
            name=repository_2_name,
            url=FAKE_2_YUM_REPO,
            product=product_attrs['id'],
            # notice that we're not making this repo point to the GPG key
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.org_name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_product_repo
                              (name, product=True))
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(self.gpgkey.assert_product_repo
                                 (name, product=False))
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert key shouldn't be associated with product or repository
            # after deletion
            self.assertIsNone(self.gpgkey.assert_key_from_product
                              (name, product_name, repository_1_name))

    @skip_if_bug_open('bugzilla', 1085924)
    @stubbed()
    @data("""DATADRIVENGOESHERE
        name is alpha
        name is numeric
        name is alphanumeric
        name is utf-8
        name is latin1
        name is html
        gpg key file is valid always
""")
    def test_key_associate_21(self):
        """  @test: Create gpg key with valid name and valid gpg key then
        associate it to repos from custom product using Repo discovery method
        then delete the key

        @feature: GPG Keys

        @assert: gpg key is associated with product and all repositories
        during creation but removed from product and all repositories
        after deletion

        @status: manual

        @BZ: 1085924

        """

        pass
