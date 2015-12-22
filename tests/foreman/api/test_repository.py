"""Unit tests for the ``repositories`` paths."""
from fauxfactory import gen_string
from nailgun import client, entities
from random import randint
from requests.exceptions import HTTPError
from robottelo.api.utils import enable_rhrepo_and_fetchid, upload_manifest
from robottelo import manifests
from robottelo.config import settings
from robottelo.constants import (
    DOCKER_REGISTRY_HUB,
    FAKE_0_PUPPET_REPO,
    FAKE_2_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
    RPM_TO_UPLOAD,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
    tier2,
)
from robottelo.helpers import (
    get_data_file,
    read_data_file,
)
from robottelo.test import APITestCase


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


def _valid_names():
    """Returns a tuple of valid repo names."""
    return(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )


class RepositoryTestCase(APITestCase):
    """Tests for ``katello/api/v2/repositories``."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create an organization and product which can be re-used in tests."""
        super(RepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.product = entities.Product(organization=cls.org).create()

    @tier1
    @run_only_on('sat')
    def test_positive_create(self):
        """@Test: Create a repository and provide valid attributes.

        @Assert: A repository is created with the given attributes.

        @Feature: Repository
        """
        for attrs in _test_data():
            with self.subTest(attrs):
                repo = entities.Repository(
                    product=self.product,
                    **attrs
                ).create()
                repo_attrs = repo.read_json()
                for name, value in attrs.items():
                    self.assertIn(name, repo_attrs.keys())
                    self.assertEqual(value, repo_attrs[name])

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_gpg(self):
        """@Test: Create a repository and provide a GPG key ID.

        @Assert: A repository is created with the given GPG key ID.

        @Feature: Repository
        """
        # Create this dependency tree:
        #
        # repository -> product -.
        #           `-> gpg key --`-> organization
        #
        gpg_key = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org,
        ).create()
        repo = entities.Repository(
            gpg_key=gpg_key,
            product=self.product,
        ).create()

        # Verify that the given GPG key ID is used.
        self.assertEqual(gpg_key.id, repo.read().gpg_key.id)

    @tier2
    @run_only_on('sat')
    def test_positive_create_same_name_different_orgs(self):
        """@Test: Create two repos with the same name in two organizations.

        @Assert: The two repositories are successfully created and use the
        given name.

        @Feature: Repository
        """
        repo1 = entities.Repository().create()
        repo2 = entities.Repository(name=repo1.name).create()
        for repo in (repo1, repo2, repo1.read(), repo2.read()):
            self.assertEqual(repo.name, repo1.name)

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """@Test: Create a repository with attributes ``attrs`` and delete it.

        @Assert: The repository cannot be fetched after deletion.

        @Feature: Repository
        """
        for attrs in _test_data():
            with self.subTest(attrs):
                repo = entities.Repository(
                    product=self.product,
                    **attrs
                ).create()
                repo.delete()
                with self.assertRaises(HTTPError):
                    repo.read()

    @tier2
    @run_only_on('sat')
    def test_positive_update_gpg(self):
        """@Test: Create a repository and update its GPGKey

        @Assert: The updated repository points to a new GPG key.

        @Feature: Repository
        """
        # Create a repo and make it point to a GPG key.
        gpg_key_1 = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org,
        ).create()
        repo = entities.Repository(
            gpg_key=gpg_key_1,
            product=self.product,
        ).create()

        # Update the repo and make it point to a new GPG key.
        gpg_key_2 = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_BETA_FILE),
            organization=self.org,
        ).create()
        repo.gpg_key = gpg_key_2
        repo = repo.update()
        self.assertEqual(repo.gpg_key.id, gpg_key_2.id)

    @tier2
    @run_only_on('sat')
    def test_positive_update_contents(self):
        """@Test: Create a repository and upload RPM contents.

        @Assert: The repository's contents include one RPM.

        @Feature: Repository
        """
        # Create a repository and upload RPM content.
        repo = entities.Repository(product=self.product).create()
        with open(get_data_file(RPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})
        # Verify the repository's contents.
        self.assertEqual(repo.read_json()[u'content_counts'][u'rpm'], 1)

    @tier2
    def test_positive_synchronize(self):
        """@Test: Create a repo and sync it.

        @Assert: The repo has more than one RPM.

        @Feature: Repository
        """
        repo = entities.Repository(product=self.product).create()
        repo.sync()
        self.assertGreaterEqual(repo.read_json()[u'content_counts'][u'rpm'], 1)


class RepositoryUpdateTestCase(APITestCase):
    """Tests for updating repositories."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create a repository which can be repeatedly updated."""
        super(RepositoryUpdateTestCase, cls).setUpClass()
        cls.repository = entities.Repository().create()

    @tier1
    @run_only_on('sat')
    def test_positive_update(self):
        """@Test: Create a repository and update its attributes.

        @Assert: The repository's attributes are updated.

        @Feature: Repository
        """
        for attrs in _test_data():
            with self.subTest(attrs):
                client.put(
                    self.repository.path(),
                    attrs,
                    auth=settings.server.get_credentials(),
                    verify=False,
                ).raise_for_status()
                real_attrs = self.repository.read_json()
                for name, value in attrs.items():
                    self.assertIn(name, real_attrs.keys())
                    if name == 'content_type':
                        # Cannot update a repository's content type.
                        con_type = self.repository.get_fields()['content_type']
                        self.assertEqual(
                            con_type.default,
                            real_attrs[name]
                        )
                    else:
                        self.assertEqual(value, real_attrs[name])


class RepositorySyncTestCase(APITestCase):
    """Tests for ``/katello/api/repositories/:id/sync``."""

    @tier2
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    def test_positive_redhat_synchronize(self):
        """@Test: Sync RedHat Repository.

        @Feature: Repositories

        @Assert: Repository synced should fetch the data successfully.
        """
        org = entities.Organization().create()
        with manifests.clone() as manifest:
            upload_manifest(org.id, manifest.content)
        repo_id = enable_rhrepo_and_fetchid(
            basearch='x86_64',
            org_id=org.id,
            product=PRDS['rhel'],
            repo=REPOS['rhst7']['name'],
            reposet=REPOSET['rhst7'],
            releasever=None,
        )
        entities.Repository(id=repo_id).sync()


class DockerRepositoryTestCase(APITestCase):
    """Tests specific to using ``Docker`` repositories."""

    @classmethod
    def setUpClass(cls):  # noqa
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    @run_only_on('sat')
    def test_positive_create(self):
        """@Test: Create a Docker-type repository

        @Assert: A repository is created with a Docker repository.

        @Feature: Repository
        """
        product = entities.Product(organization=self.org).create()
        for name in _valid_names():
            with self.subTest(name):
                repo = entities.Repository(
                    content_type=u'docker',
                    docker_upstream_name=u'busybox',
                    name=name,
                    product=product,
                    url=DOCKER_REGISTRY_HUB,
                ).create()
                repo2 = repo.read()
                self.assertEqual(repo.name, repo2.name)
                self.assertEqual(
                    repo.docker_upstream_name,
                    repo2.docker_upstream_name
                )
                self.assertEqual(repo.content_type, repo2.content_type)

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1217603)
    def test_positive_synchronize(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Repository
        """
        from pprint import PrettyPrinter
        printer = PrettyPrinter().pprint

        product = entities.Product(organization=self.org).create()
        repository = entities.Repository(
            content_type=u'docker',
            docker_upstream_name=u'busybox',
            name=u'busybox',
            product=product,
            url=DOCKER_REGISTRY_HUB,
        ).create()
        printer(repository.id)
        printer(repository.sync())
        self.assertGreaterEqual(
            repository.read_json()[u'content_counts'][u'docker_image'],
            1
        )

    @tier1
    def test_positive_update_name(self):
        """@Test: Update a repository's name.

        @Assert: The repository's name is updated.

        @Feature: Repository

        The only data provided with the PUT request is a name. No other
        information about the repository (such as its URL) is provided.
        """
        for content_type in ('yum', 'docker'):
            with self.subTest(content_type):
                if content_type == 'docker' and bz_bug_is_open(1194476):
                    self.skipTest(1194476)
                repository = entities.Repository(
                    content_type=content_type
                ).create()
                name = repository.get_fields()['name'].gen_value()
                repository.name = name
                repository = repository.update()
                self.assertEqual(repository.name, name)
