# -*- encoding: utf-8 -*-
"""Test class for Content Credentials UI

:Requirement: ContentCredentials

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities

from robottelo.constants import (
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    VALID_GPG_KEY_FILE,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import tier2, upgrade
from robottelo.helpers import get_data_file, read_data_file


class TestGPGKeyProductAssociate(object):

    @classmethod
    def setup_class(cls):
        cls.key_content = read_data_file(VALID_GPG_KEY_FILE)
        cls.key_path = get_data_file(VALID_GPG_KEY_FILE)
        cls.organization = entities.Organization().create()

    def test_positive_create_via_import(self, session):
        name = gen_string('alpha')
        with session:
            session.organization.select(org_name=self.organization.name)
            session.contentcredential.create({
                'name': name,
                'content_type': 'GPG Key',
                'upload_file': self.key_path
            })
            assert session.contentcredential.search(name) == name

    @tier2
    def test_positive_add_empty_product(self, session):
        """Create gpg key with valid name and valid gpg key then associate
        it with empty (no repos) custom product

        :id: e18ae9f5-43d9-4049-92ca-1eafaca05096

        :expectedresults: gpg key is associated with product

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            organization=self.organization,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            values = session.contentcredential.read(name)
            assert len(values['products']['resources']) == 1
            assert values['products']['resources'][0]['Name'] == product.name
            assert values['products']['resources'][0]['Used as'] == 'GPG Key'

    @tier2
    def test_positive_add_product_with_repo(self, session):
        """Create gpg key with valid name and valid gpg key then associate it
        with custom product that has one repository

        :id: 7514b33a-da75-43bd-a84b-5a805c84511d

        :expectedresults: gpg key is associated with product as well as with
            the repository

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            organization=self.organization,
        ).create()
        # Creates new repository without GPGKey
        repo = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=product,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            values = session.contentcredential.read(name)
            assert len(values['products']['resources']) == 1
            assert values['products']['resources'][0]['Name'] == product.name
            assert len(values['repositories']['resources']) == 1
            assert values['repositories']['resources'][0]['Name'] == repo.name
            assert (
                values['repositories']['resources'][0]['Product'] ==
                product.name
            )
            assert values['repositories']['resources'][0]['Type'] == 'yum'
            assert (
                values['repositories']['resources'][0]['Used as'] ==
                'GPG Key'
            )

    @tier2
    def test_positive_add_product_with_repos(self, session):
        """Create gpg key with valid name and valid gpg key then associate it
        with custom product that has more than one repository

        :id: 0edffad7-0ab4-4bef-b16b-f6c8de55b0dc

        :expectedresults: gpg key is properly associated with repositories

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            organization=self.organization,
        ).create()
        # Creates new repository_1 without GPGKey
        repo1 = entities.Repository(
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # Creates new repository_2 without GPGKey
        repo2 = entities.Repository(
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            values = session.contentcredential.read(name)
            assert len(values['repositories']['resources']) == 2
            assert (
                set([repo1.name, repo2.name]) ==
                set([
                    repo['Name']
                    for repo
                    in values['repositories']['resources']])
            )

    @tier2
    def test_positive_add_repo_from_product_with_repo(self, session):
        """Create gpg key with valid name and valid gpg key then associate it
        to repository from custom product that has one repository

        :id: 5d78890f-4130-4dc3-9cfe-48999149422f

        :expectedresults: gpg key is associated with the repository but not
            with the product

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(organization=self.organization).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            values = session.contentcredential.read(name)
            assert len(values['repositories']['resources']) == 1
            assert values['repositories']['resources'][0]['Name'] == repo.name
            assert (
                values['repositories']['resources'][0]['Product'] ==
                product.name
            )

    @tier2
    def test_positive_add_repo_from_product_with_repos(self, session):
        """Create gpg key with valid name and valid gpg key then associate it
        to repository from custom product that has more than one repository

        :id: 1fb38e01-4c04-4609-842d-069f96157317

        :expectedresults: gpg key is associated with one of the repositories
            but not with the product

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(organization=self.organization).create()
        # Creates new repository with GPGKey
        repo1 = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        # Creates new repository without GPGKey
        entities.Repository(
            url=FAKE_2_YUM_REPO,
            product=product,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            values = session.contentcredential.read(name)
            assert len(values['products']['resources']) == 0
            assert len(values['repositories']['resources']) == 1
            assert values['repositories']['resources'][0]['Name'] == repo1.name

    @tier2
    def test_positive_update_key_for_empty_product(self, session):
        """Create gpg key with valid name and valid gpg key then associate it
        with empty (no repos) custom product then update the key

        :id: 519817c3-9b67-4859-8069-95987ebf9453

        :expectedresults: gpg key is associated with product before/after
            update

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            organization=self.organization,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            values = session.contentcredential.read(name)
            # Assert that GPGKey is associated with product
            assert len(values['products']['resources']) == 1
            assert values['products']['resources'][0]['Name'] == product.name
            session.contentcredential.update(
                name,
                {'details.name': new_name},
            )
            values = session.contentcredential.read(new_name)
            # Assert that GPGKey is still associated with product
            assert len(values['products']['resources']) == 1
            assert values['products']['resources'][0]['Name'] == product.name

    @tier2
    def test_positive_update_key_for_product_with_repo(self, session):
        """Create gpg key with valid name and valid gpg key then associate it
        with custom product that has one repository then update the key

        :id: 02cb0601-6aa2-4589-b61e-3d3785a7e100

        :expectedresults: gpg key is associated with product as well as with
            repository after update

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            organization=self.organization,
        ).create()
        # Creates new repository without GPGKey
        repo = entities.Repository(
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            session.contentcredential.update(
                name,
                {'details.name': new_name},
            )
            values = session.contentcredential.read(new_name)
            # Assert that GPGKey is still associated with product
            assert len(values['products']['resources']) == 1
            assert values['products']['resources'][0]['Name'] == product.name
            assert len(values['repositories']['resources']) == 1
            assert values['repositories']['resources'][0]['Name'] == repo.name

    @tier2
    @upgrade
    def test_positive_update_key_for_product_with_repos(self, session):
        """Create gpg key with valid name and valid gpg key then associate it
        with custom product that has more than one repository then update the
        key

        :id: 3ca4d9ff-8032-4c2a-aed9-00ac2d1352d1

        :expectedresults: gpg key is associated with product as well as with
            repositories after update

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product and associate GPGKey with it
        product = entities.Product(
            gpg_key=gpg_key,
            organization=self.organization,
        ).create()
        # Creates new repository_1 without GPGKey
        repo1 = entities.Repository(
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        # Creates new repository_2 without GPGKey
        repo2 = entities.Repository(
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            session.contentcredential.update(
                name,
                {'details.name': new_name},
            )
            values = session.contentcredential.read(new_name)
            assert len(values['repositories']['resources']) == 2
            assert (
                set([repo1.name, repo2.name]) ==
                set([
                    repo['Name']
                    for repo
                    in values['repositories']['resources']])
            )

    @tier2
    def test_positive_update_key_for_repo_from_product_with_repo(
            self, session):
        """Create gpg key with valid name and valid gpg key then associate it
        to repository from custom product that has one repository then update
        the key

        :id: 9827306e-76d7-4aef-8074-e97fc39d3bbb

        :expectedresults: gpg key is associated with repository after update
            but not with product.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            organization=self.organization,
        ).create()
        # Creates new repository with GPGKey
        repo = entities.Repository(
            gpg_key=gpg_key,
            product=product,
            url=FAKE_1_YUM_REPO,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            session.contentcredential.update(
                name,
                {'details.name': new_name},
            )
            values = session.contentcredential.read(new_name)
            # Assert that after update GPGKey is not associated with product
            assert len(values['products']['resources']) == 0
            # Assert that after update GPGKey is still associated
            # with repository
            assert len(values['repositories']['resources']) == 1
            assert values['repositories']['resources'][0]['Name'] == repo.name

    @tier2
    @upgrade
    def test_positive_update_key_for_repo_from_product_with_repos(
            self, session):
        """Create gpg key with valid name and valid gpg key then associate it
        to repository from custom product that has more than one repository
        then update the key

        :id: d4f2fa16-860c-4ad5-b04f-8ce24b5618e9

        :expectedresults: gpg key is associated with single repository
            after update but not with product

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        new_name = gen_string('alpha')
        gpg_key = entities.GPGKey(
            content=self.key_content,
            name=name,
            organization=self.organization,
        ).create()
        # Creates new product without selecting GPGkey
        product = entities.Product(
            organization=self.organization,
        ).create()
        # Creates new repository_1 with GPGKey
        repo1 = entities.Repository(
            url=FAKE_1_YUM_REPO,
            product=product,
            gpg_key=gpg_key,
        ).create()
        # Creates new repository_2 without GPGKey
        entities.Repository(
            product=product,
            url=FAKE_2_YUM_REPO,
        ).create()
        with session:
            session.organization.select(org_name=self.organization.name)
            session.contentcredential.update(
                name,
                {'details.name': new_name},
            )
            values = session.contentcredential.read(new_name)
            assert len(values['products']['resources']) == 0
            assert len(values['repositories']['resources']) == 1
            assert values['repositories']['resources'][0]['Name'] == repo1.name
