# -*- encoding: utf-8 -*-
"""Test class for GPG Key UI"""

from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
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
    data,
    run_only_on,
    skip_if_bug_open,
    stubbed,
)
from robottelo.common.helpers import (
    generate_strings_list,
    get_data_file,
    invalid_names_list,
    read_data_file,
    valid_data_list,
)
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
    def setUpClass(cls):
        cls.key_content = read_data_file(VALID_GPG_KEY_FILE)
        cls.key_path = get_data_file(VALID_GPG_KEY_FILE)
        cls.organization = entities.Organization().create()
        super(GPGKey, cls).setUpClass()

    # Positive Create

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_positive_create_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        via file import

        @feature: GPG Keys

        @assert: gpg key is created

        """
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_path=self.key_path,
                name=name,
                org=self.organization.name,
                upload_key=True,
            )
            self.assertIsNotNone(self.gpgkey.search(name))

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_positive_create_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string

        @feature: GPG Keys

        @assert: gpg key is created

        """
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_content=self.key_content,
                name=name,
                org=self.organization.name,
            )
            self.assertIsNotNone(self.gpgkey.search(name))

    # Negative Create

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_negative_create_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key via
        file import then try to create new one with same name

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        kwargs = {
            'key_path': self.key_path,
            'name': name,
            'org': self.organization.name,
            'upload_key': True,
        }
        with Session(self.browser) as session:
            make_gpgkey(session, **kwargs)
            self.assertIsNotNone(self.gpgkey.search(name))
            make_gpgkey(session, **kwargs)
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['alert.error'])
            )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_negative_create_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string import then try to create new one with same name

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        kwargs = {
            'key_content': self.key_content,
            'name': name,
            'org': self.organization.name,
        }
        with Session(self.browser) as session:
            make_gpgkey(session, **kwargs)
            self.assertIsNotNone(self.gpgkey.search(name))
            make_gpgkey(session, **kwargs)
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['alert.error'])
            )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_negative_create_3(self, name):
        """@test: Create gpg key with valid name and no gpg key

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        with Session(self.browser) as session:
            with self.assertRaises(UIError):
                make_gpgkey(session, name=name, org=self.organization.name)
            self.assertIsNone(self.gpgkey.search(name))

    @data(*invalid_names_list())
    def test_negative_create_4(self, name):
        """@test: Create gpg key with invalid name and valid gpg key via
        file import

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_path=self.key_path,
                name=name,
                org=self.organization.name,
                upload_key=True,
            )
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['alert.error'])
            )
            self.assertIsNone(self.gpgkey.search(name))

    def test_negative_create_5(self):
        """@test: Create gpg key with blank name and valid gpg key via
        file import

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        name = ' '
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_path=self.key_path,
                name=name,
                org=self.organization.name,
                upload_key=True,
            )
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['haserror'])
            )
            self.assertIsNone(self.gpgkey.search(name))

    @data(*invalid_names_list())
    def test_negative_create_6(self, name):
        """@test: Create gpg key with invalid name and valid gpg key text via
        cut and paste/string

        @feature: GPG Keys

        @assert: gpg key is not created

        """
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_content=self.key_content,
                name=name,
                org=self.organization.name,
            )
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['alert.error'])
            )
            self.assertIsNone(self.gpgkey.search(name))

    # Positive Delete

    @data(*valid_data_list())
    def test_positive_delete_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then delete it

        @feature: GPG Keys

        @assert: gpg key is deleted

        """
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_path=self.key_path,
                name=name,
                org=self.organization.name,
                upload_key=True,
            )
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
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_content=self.key_content,
                name=name,
                org=self.organization.name,
            )
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
        name = gen_string('alpha', 6)
        new_name = gen_string('alpha', 6)
        with Session(self.browser) as session:
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
                common_locators['alert.success']
            ))

    @skip_if_bug_open('bugzilla', 1204602)
    def test_positive_update_2(self):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then update its gpg key file

        @feature: GPG Keys

        @assert: gpg key is updated

        @bz: 1204602

        """
        name = gen_string('alpha', 6)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        with Session(self.browser) as session:
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
                common_locators['alert.success']
            ))

    def test_positive_update_3(self):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its name

        @feature: GPG Keys

        @assert: gpg key is updated

        """
        name = gen_string('alpha', 6)
        new_name = gen_string('alpha', 6)
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_content=self.key_content,
                name=name,
                org=self.organization.name,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertIsNotNone(self.gpgkey.wait_until_element(
                common_locators['alert.success']
            ))

    @skip_if_bug_open('bugzilla', 1204602)
    def test_positive_update_4(self):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then update its gpg key text

        @feature: GPG Keys

        @assert: gpg key is updated

        @bz: 1204602

        """
        name = gen_string('alpha', 6)
        new_key_path = get_data_file(VALID_GPG_KEY_BETA_FILE)
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_content=self.key_content,
                name=name,
                org=self.organization.name,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_key=new_key_path)
            self.assertIsNotNone(self.gpgkey.wait_until_element(
                common_locators['alert.success']
            ))

    # Negative Update

    @data(*invalid_names_list())
    def test_negative_update_1(self, new_name):
        """@test: Create gpg key with valid name and valid gpg key via file
        import then fail to update its name

        @feature: GPG Keys

        @assert: gpg key is not updated

        """
        name = gen_string('alpha', 6)
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_path=self.key_path,
                name=name,
                org=self.organization.name,
                upload_key=True,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['alert.error'])
            )
            self.assertIsNone(self.gpgkey.search(new_name))

    @data(*invalid_names_list())
    def test_negative_update_2(self, new_name):
        """@test: Create gpg key with valid name and valid gpg key text via
        cut and paste/string then fail to update its name

        @feature: GPG Keys

        @assert: gpg key is not updated

        """
        name = gen_string('alpha', 6)
        with Session(self.browser) as session:
            make_gpgkey(
                session,
                key_content=self.key_content,
                name=name,
                org=self.organization.name,
            )
            self.assertIsNotNone(self.gpgkey.search(name))
            self.gpgkey.update(name, new_name)
            self.assertIsNotNone(
                self.gpgkey.wait_until_element(common_locators['alert.error'])
            )
            self.assertIsNone(self.gpgkey.search(new_name))

    @data(*valid_data_list())
    def test_consume_content_1(self, key_name):
        """@test: Hosts can install packages using gpg key associated with
        single custom repository

        @feature: GPG Keys

        @assert: host can install package from custom repository

        @status: manual

        """
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
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # step3: Creates new repository with GPGKey
        repo = entities.Repository(
            name=gen_string('alpha', 8),
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
            name=gen_string('alpha', 8),
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
        cls.key_content = read_data_file(VALID_GPG_KEY_FILE)
        cls.key_path = get_data_file(VALID_GPG_KEY_FILE)
        cls.organization = entities.Organization().create()
        super(GPGKeyProductAssociate, cls).setUpClass()

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_1(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with empty (no repos) custom product

        @feature: GPG Keys

        @assert: gpg key is associated with product

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(name, product=True)
            )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_2(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has one repository

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as
        with the repository

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            url=FAKE_1_YUM_REPO,
            product=product,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product and repository
            for product_ in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(name, product=product_)
                )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_3(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has more than one repository

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        the repositories

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product and repository
            for product_ in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(name, product=product_)
                )

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
        with Session(self.browser) as session:
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
                product=gen_string('alpha', 8),
            )
            for product in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(name, product=product)
                )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_5(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository

        @feature: GPG Keys

        @assert: gpg key is associated with the repository but not with
        the product

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository with GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.assert_product_repo(name, product=True)
            )
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(name, product=False)
            )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_6(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has more than
        one repository

        @feature: GPG Keys

        @assert: gpg key is associated with one of the repositories but
        not with the product

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository with GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            url=FAKE_2_YUM_REPO,
            product=product,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.assert_product_repo(name, product=True)
            )
            # Assert that GPGKey is not associated with product
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(name, product=False)
            )

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
        new_name = gen_string('alpha', 8)
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(name, product=True)
            )
            # Update the Key name
            self.gpgkey.update(name, new_name)
            # Again assert that GPGKey is associated with product
            self.assertEqual(
                product.name,
                self.gpgkey.assert_product_repo(new_name, product=True)
            )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_9(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has one repository
        then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        reposiotry before/after update

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()

        new_name = gen_string('alpha', 8)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that before update GPGKey is associated with product, repo
            for product_ in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(name, product=product_)
                )
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is associated with product, repo
            for product_ in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(new_name, product=product_)
                )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_10(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has more than one
        repository then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        reposiories before/after update

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()

        new_name = gen_string('alpha', 8)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that before update GPGKey is associated with product, repo
            for product_ in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(name, product=product_)
                )
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is associated with product, repo
            for product_ in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(new_name, product=product_)
                )

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
        new_name = gen_string("alpha", 8)
        entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create_json()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_products()
            # Perform repo discovery
            self.repository.discover_repo(
                REPO_DISCOVERY_URL,
                ['fakerepo01/'],
                gpg_key=name,
                new_product=True,
                product=gen_string('alpha', 8),
            )
            for product in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(name, product=product)
                )
            self.gpgkey.update(name, new_name)
            for product in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(new_name, product=product)
                )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_12(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository
        then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with repository
        before/after update but not with product.

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository with GPGKey
        entities.Repository(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()

        new_name = gen_string('alpha', 8)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.assert_product_repo(name, product=True)
            )
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(name, product=False)
            )
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.assert_product_repo(new_name, product=True)
            )
            # Assert that after update GPGKey is still associated
            # with repository
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(new_name, product=False)
            )

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_13(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has more than
        one repository then update the key

        @feature: GPG Keys

        @assert: gpg key is associated with single repository
        before/after update but not with product

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository_1 with GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()

        new_name = gen_string('alpha', 8)
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.assert_product_repo(name, product=True)
            )
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(name, product=False)
            )
            self.gpgkey.update(name, new_name)
            # Assert that after update GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.assert_product_repo(new_name, product=True)
            )
            # Assert that after update GPGKey is not associated with repository
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(new_name, product=False)
            )

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
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(name, product=True)
            )
            self.gpgkey.delete(name, True)
            # Assert GPGKey cannot be found and isn't assicated with product
            for result in (
                    self.gpgkey.search(name),
                    self.gpgkey.assert_key_from_product(name, product.name)):
                self.assertIsNone(result)

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_16(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it with custom product that has one repository then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with the
        repository during creation but removed from product after deletion

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            url=FAKE_1_YUM_REPO,
            product=product,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product, repository
            for product_ in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(name, product=product_)
                )
            self.gpgkey.delete(name, True)
            # Assert GPGKey cannot be found and isn't assicated with product
            for result in (
                    self.gpgkey.search(name),
                    self.gpgkey.assert_key_from_product(name, product.name)):
                self.assertIsNone(result)

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_17(self, name):
        """@test: Create gpg key with valid name and valid gpg key
        then associate it with custom product that has
        more than one repository then delete it

        @feature: GPG Keys

        @assert: gpg key is associated with product as well as with
        repositories during creation but removed from product after deletion

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository_1 without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is associated with product, repository
            for product_ in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(name, product=product_)
                )
            self.gpgkey.delete(name, True)
            # Assert GPGKey cannot be found and isn't assicated with product
            for result in (
                    self.gpgkey.search(name),
                    self.gpgkey.assert_key_from_product(name, product.name)):
                self.assertIsNone(result)

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
        product_name = gen_string('alpha', 8)
        entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create_json()
        with Session(self.browser) as session:
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
            for product_ in (True, False):
                self.assertIsNotNone(
                    self.gpgkey.assert_product_repo(name, product=product_)
                )
            self.gpgkey.delete(name, True)
            for result in (
                    self.gpgkey.search(name),
                    self.gpgkey.assert_key_from_product(name, product_name)):
                self.assertIsNone(result)

    @data(*generate_strings_list(remove_str='numeric', bug_id=1184480))
    def test_key_associate_19(self, name):
        """@test: Create gpg key with valid name and valid gpg key then
        associate it to repository from custom product that has one repository
        then delete the key

        @feature: GPG Keys

        @assert: gpg key is associated with single repository
        during creation but removed from repository after deletion

        """
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(
            name=gen_string('alpha', 8),
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.assert_product_repo(name, product=True)
            )
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(name, product=False)
            )
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert that after deletion GPGKey is not associated with product
            self.assertIsNone(self.gpgkey.assert_key_from_product(
                name,
                product.name,
                repo.name
            ))

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
        # Creates New GPGKey
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without GPGKey association
        product = entities.Product(
            name=gen_string('alpha', 8),
            organization=self.organization,
        ).create()
        # Creates new repository_1 with GPGKey association
        repo1 = entities.Repository(
            gpg_key=gpg_key,
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        entities.Repository(
            name=gen_string('alpha', 8),
            product=product,
            url=FAKE_2_YUM_REPO,
            # notice that we're not making this repo point to the GPG key
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            session.nav.go_to_gpg_keys()
            # Assert that GPGKey is not associated with product
            self.assertIsNone(
                self.gpgkey.assert_product_repo(name, product=True)
            )
            # Assert that GPGKey is associated with repository
            self.assertIsNotNone(
                self.gpgkey.assert_product_repo(name, product=False)
            )
            self.gpgkey.delete(name, True)
            self.assertIsNone(self.gpgkey.search(name))
            # Assert key shouldn't be associated with product or repository
            # after deletion
            self.assertIsNone(self.gpgkey.assert_key_from_product(
                name,
                product.name,
                repo1.name
            ))

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
