"""Unit tests for the ``repositories`` paths."""
from ddt import ddt
from fauxfactory import gen_string
from nailgun import client, entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.api import utils
from robottelo.common import manifests
from robottelo.common.constants import (
    DOCKER_REGISTRY_HUB,
    FAKE_0_PUPPET_REPO,
    FAKE_2_YUM_REPO,
    RPM_TO_UPLOAD,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.common.decorators import bz_bug_is_open, data, run_only_on
from robottelo.common.helpers import (
    get_server_credentials, get_data_file, read_data_file)
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


# FIXME: Use unittest's subTest context manager instead of this and @ddt.data.
# Only available in Python 3.2 and above.
def _test_data():
    """Return a tuple of dicts. The dicts can be used to make products."""
    return (
        {'content_type': 'puppet', 'url': FAKE_0_PUPPET_REPO},
        {'checksum_type': 'sha1'},
        {'checksum_type': 'sha256'},
        {'name': gen_string('alphanumeric', randint(10, 50))},
        {'name': gen_string('alpha', randint(10, 50))},
        {'name': gen_string('cjk', randint(10, 50))},
        {'name': gen_string('latin1', randint(10, 50))},
        {'name': gen_string('numeric', randint(10, 50))},
        {'name': gen_string('utf8', randint(10, 50))},
        {'unprotected': True},
        {'url': FAKE_2_YUM_REPO},
    )


@ddt
class RepositoryTestCase(APITestCase):
    """Tests for ``katello/api/v2/repositories``."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create an organization and product which can be re-used in tests."""
        cls.org_id = entities.Organization().create_json()['id']
        cls.prod_id = entities.Product(
            organization=cls.org_id
        ).create_json()['id']

    @run_only_on('sat')
    @data(*_test_data())  # (star-args) pylint:disable=W0142
    def test_create_attrs(self, attrs):
        """@Test: Create a repository and provide valid attributes.

        @Assert: A repository is created with the given attributes.

        @Feature: Repository

        """
        repo_id = entities.Repository(  # (star-args) pylint:disable=W0142
            product=self.prod_id,
            **attrs
        ).create_json()['id']
        real_attrs = entities.Repository(id=repo_id).read_json()
        for name, value in attrs.items():
            self.assertIn(name, real_attrs.keys())
            self.assertEqual(value, real_attrs[name])

    @run_only_on('sat')
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
        ).create_json()['id']
        repo_id = entities.Repository(
            gpg_key=gpgkey_id,
            product=self.prod_id,
        ).create_json()['id']

        # Verify that the given GPG key ID is used.
        repo_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(repo_attrs['gpg_key_id'], gpgkey_id)

    @run_only_on('sat')
    def test_create_same_name(self):
        """@Test: Create two repos with the same name in two organizations.

        @Assert: The two repositories are sucessfully created and use the given
        name.

        @Feature: Repository

        """
        repo1 = entities.Repository()
        repo1.name = name = repo1.get_fields()['name'].gen_value()
        repo1 = repo1.create()
        repo2 = entities.Repository(name=name).create()
        for repo in (repo1, repo2, repo1.read(), repo2.read()):
            self.assertEqual(repo.name, name)

    @run_only_on('sat')
    @data(*_test_data())  # (star-args) pylint:disable=W0142
    def test_delete(self, attrs):
        """@Test: Create a repository with attributes ``attrs`` and delete it.

        @Assert: The repository cannot be fetched after deletion.

        @Feature: Repository

        """
        repo_id = entities.Repository(  # (star-args) pylint:disable=W0142
            product=self.prod_id,
            **attrs
        ).create_json()['id']
        entities.Repository(id=repo_id).delete()
        with self.assertRaises(HTTPError):
            entities.Repository(id=repo_id).read_json()

    @run_only_on('sat')
    def test_update_gpgkey(self):
        """@Test: Create a repository and update its GPGKey

        @Assert: The updated repository points to a new GPG key.

        @Feature: Repository

        """
        # Create a repo and make it point to a GPG key.
        key_1_id = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org_id,
        ).create_json()['id']
        repo_id = entities.Repository(
            gpg_key=key_1_id,
            product=self.prod_id,
        ).create_json()['id']

        # Update the repo and make it point to a new GPG key.
        key_2_id = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_BETA_FILE),
            organization=self.org_id,
        ).create_json()['id']
        client.put(
            entities.Repository(id=repo_id).path(),
            {u'gpg_key_id': key_2_id},
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()

        # Verify the repository's attributes.
        attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(attrs['gpg_key_id'], key_2_id)

    @run_only_on('sat')
    def test_update_contents(self):
        """@Test: Create a repository and upload RPM contents.

        @Assert: The repository's contents include one RPM.

        @Feature: Repository

        """
        # Create a repository and upload RPM content.
        repo_id = entities.Repository(product=self.prod_id).create_json()['id']
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
        repo_id = entities.Repository(product=self.prod_id).create_json()['id']
        entities.Repository(id=repo_id).sync()
        attrs = entities.Repository(id=repo_id).read_json()
        self.assertGreaterEqual(attrs[u'content_counts'][u'rpm'], 1)


@ddt
class RepositoryUpdateTestCase(APITestCase):
    """Tests for updating repositories."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create a repository which can be repeatedly updated."""
        cls.repository = entities.Repository(
            id=entities.Repository().create_json()['id']
        )

    @run_only_on('sat')
    @data(*_test_data())  # (star-args) pylint:disable=W0142
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
            if name == 'content_type':
                # Cannot update a repository's content type.
                self.assertEqual(
                    entities.Repository.content_type.default,
                    real_attrs[name]
                )
            else:
                self.assertEqual(value, real_attrs[name])


class RepositorySyncTestCase(APITestCase):
    """Tests for ``/katello/api/repositories/:id/sync``."""

    @run_only_on('sat')
    def test_redhat_sync_1(self):
        """@Test: Sync RedHat Repository.

        @Feature: Repositories

        @Assert: Repository synced should fetch the data successfully.

        """
        cloned_manifest_path = manifests.clone()
        org_id = entities.Organization().create_json()['id']
        repo = "Red Hat Enterprise Linux 6 Server - RH Common RPMs x86_64 6.3"
        entities.Organization(id=org_id).upload_manifest(
            path=cloned_manifest_path
        )
        repo_id = utils.enable_rhrepo_and_fetchid(
            "x86_64",
            org_id,
            "Red Hat Enterprise Linux Server",
            repo,
            "Red Hat Enterprise Linux 6 Server - RH Common (RPMs)",
            "6.3",
        )
        entities.Repository(id=repo_id).sync()


@ddt
class DockerRepositoryTestCase(APITestCase):
    """Tests specific to using ``Docker`` repositories."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create an organization and product which can be re-used in tests."""
        cls.org_id = entities.Organization().create_json()['id']

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_create_docker_repo(self, name):
        """@Test: Create a Docker-type repository

        @Assert: A repository is created with a Docker repository.

        @Feature: Repository

        """
        upstream_name = u'busybox'
        content_type = u'docker'
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = entities.Repository(
            product=prod_id,
            content_type=content_type,
            name=name,
            docker_upstream_name=upstream_name,
            url=DOCKER_REGISTRY_HUB
        ).create_json()['id']
        real_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(real_attrs['name'], name)
        self.assertEqual(real_attrs['docker_upstream_name'], upstream_name)
        self.assertEqual(real_attrs['content_type'], content_type)

    @run_only_on('sat')
    def test_sync_docker_repo(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Repository

        """
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']
        repo_id = entities.Repository(
            product=prod_id,
            content_type=u'docker',
            name=u'busybox',
            docker_upstream_name=u'busybox',
            url=DOCKER_REGISTRY_HUB
        ).create_json()['id']

        entities.Repository(id=repo_id).sync()
        attrs = entities.Repository(id=repo_id).read_json()
        self.assertGreaterEqual(attrs[u'content_counts'][u'docker_image'], 1)

    @data('yum', 'docker')
    def test_update_name(self, content_type):
        """@Test: Update a repository's name.

        @Assert: The repository's name is updated.

        @Feature: Repository

        The only data provided with the PUT request is a name. No other
        information about the repository (such as its URL) is provided.

        """
        if content_type == 'docker' and bz_bug_is_open(1194476):
            self.skipTest(1194476)
        repository = entities.Repository(content_type=content_type).create()
        name = repository.get_fields()['name'].gen_value()
        client.put(
            repository.path(),
            {'name': name},
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()
        self.assertEqual(name, repository.read().name)
