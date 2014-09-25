"""Unit tests for the ``repositories`` paths."""
from fauxfactory import FauxFactory
from random import randint
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.common.constants import (
    VALID_GPG_KEY_FILE, VALID_GPG_KEY_BETA_FILE, FAKE_0_PUPPET_REPO,
    FAKE_2_YUM_REPO, RPM_TO_UPLOAD)
from robottelo.common import decorators
from robottelo.common import manifests
from robottelo.common.helpers import (
    get_server_credentials, get_data_file, read_data_file)
from robottelo import entities
from unittest import TestCase
import ddt
# (too many public methods) pylint: disable=R0904


@ddt.ddt
class RepositoryTestCase(TestCase):
    """Tests for ``katello/api/v2/repositories``."""
    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        cls.org_id = entities.Organization().create()['id']
        cls.prod_id = entities.Product(organization=cls.org_id).create()['id']

    @decorators.run_only_on('sat')
    @decorators.data(
        {'content_type': 'puppet', 'url': FAKE_0_PUPPET_REPO},
        {'name': FauxFactory.generate_string('alphanumeric', randint(10, 50))},
        {'name': FauxFactory.generate_string('alpha', randint(10, 50))},
        {'name': FauxFactory.generate_string('cjk', randint(10, 50))},
        {'name': FauxFactory.generate_string('latin1', randint(10, 50))},
        {'name': FauxFactory.generate_string('numeric', randint(10, 50))},
        {'name': FauxFactory.generate_string('utf8', randint(10, 50))},
        {'unprotected': True},
        {'url': FAKE_2_YUM_REPO},
    )
    def test_create_attrs(self, attrs):
        """@Test: Create a repository and provide valid attributes.

        @Assert: A repository is created with the given attributes.

        @Feature: Repository

        """
        repo_id = entities.Repository(
            product=self.prod_id,
            **attrs
        ).create()['id']
        real_attrs = entities.Repository(id=repo_id).read_json()
        for name, value in attrs.items():
            self.assertIn(name, real_attrs.keys())
            self.assertEqual(value, real_attrs[name])

    @decorators.run_only_on('sat')
    def test_create_gpgkey(self):
        """@Test: Create a repository and provide a GPG key ID.

        @Assert: A repository is created with the given GPG key ID.

        @Feature: Repository

        """
        # Create this dependency tree:
        #
        # repository -> product -.
        #           `-> gpg key --`-> organization
        #
        gpgkey_id = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org_id,
        ).create()['id']
        repo_id = entities.Repository(
            gpg_key=gpgkey_id,
            product=self.prod_id,
        ).create()['id']

        # Verify that the given GPG key ID is used.
        repo_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(repo_attrs['gpg_key_id'], gpgkey_id)

    @decorators.run_only_on('sat')
    def test_create_same_name(self):
        """@Test: Create two repos with the same name in two organizations.

        @Assert: The two repositories are sucessfully created and use the given
        name.

        @Feature: Repository

        """
        name = entities.Repository.name.get_value()
        repo1_attrs = entities.Repository(
            name=name,
            product=self.prod_id
        ).create()
        repo2_attrs = entities.Repository(name=name).create()
        for attrs in (
                repo1_attrs,
                repo2_attrs,
                entities.Repository(id=repo1_attrs['id']).read_json(),
                entities.Repository(id=repo2_attrs['id']).read_json()):
            self.assertEqual(attrs['name'], name)

    @decorators.run_only_on('sat')
    @decorators.data(
        {'content_type': 'puppet', 'url': FAKE_0_PUPPET_REPO},
        {'name': FauxFactory.generate_string('alphanumeric', randint(10, 50))},
        {'name': FauxFactory.generate_string('alpha', randint(10, 50))},
        {'name': FauxFactory.generate_string('cjk', randint(10, 50))},
        {'name': FauxFactory.generate_string('latin1', randint(10, 50))},
        {'name': FauxFactory.generate_string('numeric', randint(10, 50))},
        {'name': FauxFactory.generate_string('utf8', randint(10, 50))},
        {'unprotected': True},
        {'url': FAKE_2_YUM_REPO},
    )
    def test_delete(self, attrs):
        """@Test: Create a repository with attributes ``attrs`` and delete it.

        @Assert: The repository cannot be fetched after deletion.

        @Feature: Repository

        """
        repo_id = entities.Repository(
            product=self.prod_id,
            **attrs
        ).create()['id']
        entities.Repository(id=repo_id).delete()
        with self.assertRaises(HTTPError):
            entities.Repository(id=repo_id).read_json()

    @decorators.run_only_on('sat')
    def test_update_gpgkey(self):
        """@Test: Create a repository and update its GPGKey

        @Assert: The updated repository points to a new GPG key.

        @Feature: Repository

        """
        # Create a repo and make it point to a GPG key.
        key_1_id = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org_id,
        ).create()['id']
        repo_id = entities.Repository(
            gpg_key=key_1_id,
            product=self.prod_id,
        ).create()['id']

        # Update the repo and make it point to a new GPG key.
        key_2_id = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_BETA_FILE),
            organization=self.org_id,
        ).create()['id']
        client.put(
            entities.Repository(id=repo_id).path(),
            {u'gpg_key_id': key_2_id},
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()

        # Verify the repository's attributes.
        attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(attrs['gpg_key_id'], key_2_id)

    @decorators.run_only_on('sat')
    def test_update_contents(self):
        """@Test: Create a repository and upload RPM contents.

        @Assert: The repository's contents include one RPM.

        @Feature: Repository

        """
        # Create a repository and upload RPM content.
        repo_id = entities.Repository(product=self.prod_id).create()['id']
        client.post(
            entities.Repository(id=repo_id).path(which='upload_content'),
            {},
            auth=get_server_credentials(),
            files={u'content': open(get_data_file(RPM_TO_UPLOAD), 'rb')},
            verify=False,
        ).raise_for_status()

        # Verify the repository's contents.
        attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(attrs[u'content_counts'][u'rpm'], 1)

    def test_sync(self):
        """@Test: Create a repo and sync it.

        @Assert: The repo has more than one RPM.

        @Feature: Repository

        """
        repo_id = entities.Repository(product=self.prod_id).create()['id']
        task_id = entities.Repository(id=repo_id).sync()
        entities.ForemanTask(id=task_id).poll()
        attrs = entities.Repository(id=repo_id).read_json()
        self.assertGreaterEqual(attrs[u'content_counts'][u'rpm'], 1)


@ddt.ddt
class RepositoryUpdateTestCase(TestCase):
    """Tests for updating repositories."""
    @classmethod
    def setUpClass(cls):
        """Create a repository which can be repeatedly updated."""
        cls.repository = entities.Repository(
            id=entities.Repository().create()['id']
        )

    @decorators.run_only_on('sat')
    @decorators.data(
        {'name': FauxFactory.generate_string('alphanumeric', randint(10, 50))},
        {'name': FauxFactory.generate_string('alpha', randint(10, 50))},
        {'name': FauxFactory.generate_string('cjk', randint(10, 50))},
        {'name': FauxFactory.generate_string('latin1', randint(10, 50))},
        {'name': FauxFactory.generate_string('numeric', randint(10, 50))},
        {'name': FauxFactory.generate_string('utf8', randint(10, 50))},
        {'unprotected': True},
        {'url': FAKE_2_YUM_REPO},
    )
    def test_update(self, attrs):
        """@Test: Create a repository and update its attributes.

        @Assert: The repository's attributes are updated.

        @Feature: Repository

        """
        client.put(
            self.repository.path(),
            attrs,
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()
        real_attrs = self.repository.read_json()
        for name, value in attrs.items():
            self.assertIn(name, real_attrs.keys())
            self.assertEqual(value, real_attrs[name])


def enable_rhrepo_and_fetchid(basearch, org_id, product, repo,
                              reposet, releasever):
    """Enable a RedHat Repository and fetches it's Id.

    :param str org_id: The organization Id.
    :param str product: The product name in which repository exists.
    :param str reposet: The reposet name in which repository exists.
    :param str repo: The repository name who's Id is to be fetched.
    :param str basearch: The architecture of the repository.
    :param str releasever: The releasever of the repository.
    :return: Returns the repository Id.
    :rtype: str

    """
    prd_id = entities.Product().fetch_rhproduct_id(name=product, org_id=org_id)
    reposet_id = entities.Product(id=prd_id).fetch_reposet_id(name=reposet)
    task_id = entities.Product(id=prd_id).enable_rhrepo(
        base_arch=basearch,
        release_ver=releasever,
        reposet_id=reposet_id,
    )
    task_result = entities.ForemanTask(id=task_id).poll()['result']
    if task_result != "success":
        raise entities.APIResponseError(
            "Enabling the RedHat Repository '{}' failed".format(repo))
    return entities.Repository().fetch_repoid(name=repo, org_id=org_id)


class RepositorySyncTestCase(TestCase):
    """Tests for ``/katello/api/repositories/:id/sync``."""

    @decorators.run_only_on('sat')
    def test_redhat_sync_1(self):
        """@Test: Sync RedHat Repository.

        @Feature: Repositories

        @Assert: Repository synced should fetch the data successfully.

        """
        cloned_manifest_path = manifests.clone()
        org_id = entities.Organization().create()['id']
        repo = "Red Hat Enterprise Linux 6 Server - RH Common RPMs x86_64 6.3"
        task_id = entities.Organization(
            id=org_id).upload_manifest(path=cloned_manifest_path)
        task_result = entities.ForemanTask(id=task_id).poll()['result']
        self.assertEqual(u'success', task_result)
        repo_id = entities.enable_rhrepo_and_fetchid(
            "x86_64",
            org_id,
            "Red Hat Enterprise Linux Server",
            repo,
            "Red Hat Enterprise Linux 6 Server - RH Common (RPMs)",
            "6.3",
        )
        task_id = entities.Repository(id=repo_id).sync()
        task_result = entities.ForemanTask(id=task_id).poll()['result']
        self.assertEqual(
            task_result,
            u'success',
            u"Sync for repository '{0}' failed.".format(repo))
