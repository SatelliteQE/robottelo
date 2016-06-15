"""Unit tests for the ``repositories`` paths."""
from fauxfactory import gen_string
from nailgun import entities
from nailgun.entity_mixins import TaskFailedError
from requests.exceptions import HTTPError
from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid, upload_manifest
from robottelo.constants import (
    DOCKER_REGISTRY_HUB,
    FAKE_0_PUPPET_REPO,
    FAKE_7_PUPPET_REPO,
    FAKE_2_YUM_REPO,
    FAKE_5_YUM_REPO,
    PRDS,
    REPOS,
    REPOSET,
    RPM_TO_UPLOAD,
    VALID_GPG_KEY_BETA_FILE,
    VALID_GPG_KEY_FILE,
)
from robottelo.datafactory import (
    invalid_http_credentials,
    invalid_names_list,
    invalid_values_list,
    valid_data_list,
    valid_http_credentials,
    valid_labels_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
    tier2,
)
from robottelo.helpers import get_data_file, read_data_file
from robottelo.test import APITestCase


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
    def test_positive_create_with_name(self):
        """Create a repository with valid name.

        @Assert: A repository is created with the given name.

        @Feature: Repository
        """
        for name in valid_data_list():
            with self.subTest(name):
                repo = entities.Repository(
                    product=self.product, name=name).create()
                self.assertEqual(name, repo.name)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_label(self):
        """Create a repository providing label which is different from its name

        @Assert: A repository is created with expected label.

        @Feature: Repository
        """
        for label in valid_labels_list():
            with self.subTest(label):
                repo = entities.Repository(
                    product=self.product, label=label).create()
                self.assertEqual(repo.label, label)
                self.assertNotEqual(repo.name, label)

    @tier1
    @run_only_on('sat')
    def test_positive_create_yum(self):
        """Create yum repository.

        @Assert: A repository is created and has yum type.

        @Feature: Repository
        """
        repo = entities.Repository(
            product=self.product,
            content_type='yum',
            url=FAKE_2_YUM_REPO,
        ).create()
        self.assertEqual(repo.content_type, 'yum')
        self.assertEqual(repo.url, FAKE_2_YUM_REPO)

    @tier1
    @run_only_on('sat')
    def test_positive_create_puppet(self):
        """Create puppet repository.

        @Assert: A repository is created and has puppet type.

        @Feature: Repository
        """
        repo = entities.Repository(
            product=self.product,
            content_type='puppet',
            url=FAKE_0_PUPPET_REPO,
        ).create()
        self.assertEqual(repo.content_type, 'puppet')

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_auth_yum_repo(self):
        """Create yum repository with basic HTTP authentication

        @Assert: yum repository is created

        @Feature: HTTP Authentication Repository
        """
        url = FAKE_5_YUM_REPO
        for creds in valid_http_credentials(url_encoded=True):
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                repo = entities.Repository(
                    product=self.product,
                    content_type='yum',
                    url=url_encoded,
                ).create()
                self.assertEqual(repo.content_type, 'yum')
                self.assertEqual(repo.url, url_encoded)

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_auth_puppet_repo(self):
        """Create Puppet repository with basic HTTP authentication

        @Assert: Puppet repository is created

        @Feature: HTTP Authentication Repository
        """
        url = FAKE_7_PUPPET_REPO
        for creds in valid_http_credentials(url_encoded=True):
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                repo = entities.Repository(
                    product=self.product,
                    content_type='puppet',
                    url=url_encoded,
                ).create()
                self.assertEqual(repo.content_type, 'puppet')
                self.assertEqual(repo.url, url_encoded)

    @tier1
    @run_only_on('sat')
    def test_positive_create_checksum(self):
        """Create a repository with valid checksum type.

        @Assert: A repository is created and has expected checksum type.

        @Feature: Repository
        """
        for checksum_type in 'sha1', 'sha256':
            with self.subTest(checksum_type):
                repo = entities.Repository(
                    product=self.product, checksum_type=checksum_type).create()
                self.assertEqual(checksum_type, repo.checksum_type)

    @tier1
    @run_only_on('sat')
    def test_positive_create_unprotected(self):
        """Create a repository with valid unprotected flag values.

        @Assert: A repository is created and has expected unprotected flag
        state.

        @Feature: Repository
        """
        for unprotected in True, False:
            repo = entities.Repository(
                product=self.product, unprotected=unprotected).create()
            self.assertEqual(repo.unprotected, unprotected)

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_gpg(self):
        """Create a repository and provide a GPG key ID.

        @Assert: A repository is created with the given GPG key ID.

        @Feature: Repository
        """
        gpg_key = entities.GPGKey(
            content=read_data_file(VALID_GPG_KEY_FILE),
            organization=self.org,
        ).create()
        repo = entities.Repository(
            gpg_key=gpg_key,
            product=self.product,
        ).create()
        # Verify that the given GPG key ID is used.
        self.assertEqual(gpg_key.id, repo.gpg_key.id)

    @tier2
    @run_only_on('sat')
    def test_positive_create_same_name_different_orgs(self):
        """Create two repos with the same name in two different organizations.

        @Assert: The two repositories are successfully created and have given
        name.

        @Feature: Repository
        """
        repo1 = entities.Repository(product=self.product).create()
        repo2 = entities.Repository(name=repo1.name).create()
        self.assertEqual(repo1.name, repo2.name)

    @tier1
    @run_only_on('sat')
    def test_negative_create_name(self):
        """Attempt to create repository with invalid names only.

        @Assert: A repository is not created and error is raised.

        @Feature: Repository
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(HTTPError):
                    entities.Repository(name=name).create()

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Attempt to create a repository providing a name of already existent
        entity

        @Assert: Second repository is not created

        @Feature: Repository
        """
        name = gen_string('alphanumeric')
        entities.Repository(product=self.product, name=name).create()
        with self.assertRaises(HTTPError):
            entities.Repository(product=self.product, name=name).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_label(self):
        """Attempt to create repository with invalid label.

        @Assert: A repository is not created and error is raised.

        @Feature: Repository
        """
        with self.assertRaises(HTTPError):
            entities.Repository(label=gen_string('utf8')).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_url(self):
        """Attempt to create repository with invalid url.

        @Assert: A repository is not created and error is raised.

        @Feature: Repository
        """
        for url in invalid_names_list():
            with self.subTest(url):
                with self.assertRaises(HTTPError):
                    entities.Repository(url=url).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_auth_url_with_special_characters(self):
        """Verify that repository URL cannot contain unquoted special characters

        @Assert: A repository is not created and error is raised.

        @Feature: HTTP Authentication Repository
        """
        # get a list of valid credentials without quoting them
        for cred in [creds for creds in valid_http_credentials()
                     if creds['quote'] is True]:
            with self.subTest(cred):
                url = FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])
                with self.assertRaises(HTTPError):
                    entities.Repository(url=url).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_auth_url_too_long(self):
        """Verify that repository URL length is limited

        @Assert: A repository is not created and error is raised.

        @Feature: HTTP Authentication Repository
        """
        for cred in invalid_http_credentials():
            with self.subTest(cred):
                url = FAKE_5_YUM_REPO.format(cred['login'], cred['pass'])
                with self.assertRaises(HTTPError):
                    entities.Repository(url=url).create()

    @tier1
    @run_only_on('sat')
    def test_negative_create_checksum(self):
        """Attempt to create repository with invalid checksum type.

        @Assert: A repository is not created and error is raised.

        @Feature: Repository
        """
        with self.assertRaises(HTTPError):
            entities.Repository(checksum_type=gen_string('alpha')).create()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Update repository name to another valid name.

        @Assert: The repository name can be updated.

        @Feature: Repository
        """
        repo = entities.Repository(product=self.product).create()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                repo.name = new_name
                repo = repo.update(['name'])
                self.assertEqual(new_name, repo.name)

    @tier1
    @run_only_on('sat')
    def test_positive_update_checksum(self):
        """Update repository checksum type to another valid one.

        @Assert: The repository checksum type can be updated.

        @Feature: Repository
        """
        repo = entities.Repository(
            product=self.product, checksum_type='sha1').create()
        repo.checksum_type = 'sha256'
        repo = repo.update(['checksum_type'])
        self.assertEqual(repo.checksum_type, 'sha256')

    @tier1
    @run_only_on('sat')
    def test_positive_update_url(self):
        """Update repository url to another valid one.

        @Assert: The repository url can be updated.

        @Feature: Repository
        """
        repo = entities.Repository(product=self.product).create()
        repo.url = FAKE_2_YUM_REPO
        repo = repo.update(['url'])
        self.assertEqual(repo.url, FAKE_2_YUM_REPO)

    @tier1
    @run_only_on('sat')
    def test_positive_update_unprotected(self):
        """Update repository unprotected flag to another valid one.

        @Assert: The repository unprotected flag can be updated.

        @Feature: Repository
        """
        repo = entities.Repository(
            product=self.product, unprotected=False).create()
        repo.unprotected = True
        repo = repo.update(['unprotected'])
        self.assertEqual(repo.unprotected, True)

    @tier2
    @run_only_on('sat')
    def test_positive_update_gpg(self):
        """Create a repository and update its GPGKey

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

    @run_only_on('sat')
    @tier2
    def test_positive_update_contents(self):
        """Create a repository and upload RPM contents.

        @Assert: The repository's contents include one RPM.

        @Feature: Repository
        """
        # Create a repository and upload RPM content.
        repo = entities.Repository(product=self.product).create()
        with open(get_data_file(RPM_TO_UPLOAD), 'rb') as handle:
            repo.upload_content(files={'content': handle})
        # Verify the repository's contents.
        self.assertEqual(repo.read().content_counts['rpm'], 1)

    @run_only_on('sat')
    @tier1
    def test_negative_update_name(self):
        """Attempt to update repository name to invalid one

        @Assert: Repository is not updated

        @Feature: Repository
        """
        repo = entities.Repository(product=self.product).create()
        for new_name in invalid_values_list():
            repo.name = new_name
            with self.subTest(new_name):
                with self.assertRaises(HTTPError):
                    repo.update(['name'])

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1311113)
    @tier1
    def test_negative_update_label(self):
        """Attempt to update repository label to another one.

        @Assert: Repository is not updated and error is raised

        @Feature: Repository
        """
        repo = entities.Repository(product=self.product).create()
        repo.label = gen_string('alpha')
        with self.assertRaises(HTTPError):
            repo.update(['label'])

    @run_only_on('sat')
    @tier1
    def test_negative_update_auth_url_with_special_characters(self):
        """Verify that repository URL credentials cannot be updated to contain
        the forbidden characters

        @Assert: Repository url not updated

        @Feature: HTTP Authentication Repository
        """
        new_repo = entities.Repository(product=self.product).create()
        # get auth repos with credentials containing unquoted special chars
        auth_repos = [
            repo.format(cred['login'], cred['pass'])
            for cred in valid_http_credentials() if cred['quote']
            for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
        ]

        for url in auth_repos:
            with self.subTest(url):
                new_repo.url = url
                with self.assertRaises(HTTPError):
                    new_repo = new_repo.update()

    @run_only_on('sat')
    @tier1
    def test_negative_update_auth_url_too_long(self):
        """Update the original url for a repository to value which is too long

        @Assert: Repository url not updated

        @Feature: HTTP Authentication Repository
        """
        new_repo = entities.Repository(product=self.product).create()
        # get auth repos with credentials containing unquoted special chars
        auth_repos = [
            repo.format(cred['login'], cred['pass'])
            for cred in invalid_http_credentials()
            for repo in (FAKE_5_YUM_REPO, FAKE_7_PUPPET_REPO)
        ]

        for url in auth_repos:
            with self.subTest(url):
                new_repo.url = url
                with self.assertRaises(HTTPError):
                    new_repo = new_repo.update()

    @tier2
    def test_positive_synchronize(self):
        """Create a repo and sync it.

        @Assert: The repo has at least one RPM.

        @Feature: Repository
        """
        repo = entities.Repository(product=self.product).create()
        repo.sync()
        self.assertGreaterEqual(repo.read().content_counts['rpm'], 1)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_positive_synchronize_auth_yum_repo(self):
        """Check if secured repository can be created and synced

        @Assert: Repository is created and synced

        @Feature: HTTP Authentication Repository
        """
        url = FAKE_5_YUM_REPO
        for creds in [cred for cred in valid_http_credentials(url_encoded=True)
                      if cred['http_valid']]:
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                repo = entities.Repository(
                    product=self.product,
                    content_type='yum',
                    url=url_encoded,
                ).create()
                # Assertion that repo is not yet synced
                self.assertEqual(repo.content_counts['rpm'], 0)
                # Synchronize it
                repo.sync()
                # Verify it has finished
                self.assertGreaterEqual(repo.read().content_counts['rpm'], 1)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_negative_synchronize_auth_yum_repo(self):
        """Check if secured repo fails to synchronize with invalid credentials

        @Assert: Repository is created but synchronization fails

        @Feature: HTTP Authentication Repository
        """
        url = FAKE_5_YUM_REPO
        for creds in [cred for cred in valid_http_credentials(url_encoded=True)
                      if not cred['http_valid']]:
            url_encoded = url.format(
                creds['login'], creds['pass']
            )
            with self.subTest(url):
                repo = entities.Repository(
                    product=self.product,
                    content_type='yum',
                    url=url_encoded,
                ).create()
                # Try to synchronize it
                with self.assertRaises(TaskFailedError):
                    repo.sync()

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1328092)
    @tier2
    def test_positive_synchronize_auth_puppet_repo(self):
        """Check if secured puppet repository can be created and synced

        @Assert: Repository is created and synced

        @Feature: HTTP Authentication Repository
        """
        url = FAKE_7_PUPPET_REPO
        for creds in [cred for cred in valid_http_credentials(url_encoded=True)
                      if cred['http_valid']]:
            url_encoded = url.format(creds['login'], creds['pass'])
            with self.subTest(url):
                repo = entities.Repository(
                    product=self.product,
                    content_type='puppet',
                    url=url_encoded,
                ).create()
                # Assertion that repo is not yet synced
                self.assertEqual(repo.content_counts['puppet_module'], 0)
                # Synchronize it
                repo.sync()
                # Verify it has finished
                self.assertEqual(
                    repo.read().content_counts['puppet_module'], 1)

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Create a repository with different names and then delete it.

        @Assert: The repository deleted successfully.

        @Feature: Repository
        """
        for name in valid_data_list():
            with self.subTest(name):
                repo = entities.Repository(
                    product=self.product, name=name).create()
                repo.delete()
                with self.assertRaises(HTTPError):
                    repo.read()


@run_in_one_thread
class RepositorySyncTestCase(APITestCase):
    """Tests for ``/katello/api/repositories/:id/sync``."""

    @tier2
    @run_only_on('sat')
    @skip_if_not_set('fake_manifest')
    def test_positive_sync_rh(self):
        """Sync RedHat Repository.

        @Feature: Repositories

        @Assert: Synced repo should fetch the data successfully.
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
        """Create a Docker-type repository

        @Assert: A repository is created with a Docker repository.

        @Feature: Repository
        """
        product = entities.Product(organization=self.org).create()
        for name in valid_data_list():
            with self.subTest(name):
                repo = entities.Repository(
                    content_type=u'docker',
                    docker_upstream_name=u'busybox',
                    name=name,
                    product=product,
                    url=DOCKER_REGISTRY_HUB,
                ).create()
                self.assertEqual(repo.name, name)
                self.assertEqual(
                    repo.docker_upstream_name, u'busybox')
                self.assertEqual(repo.content_type, u'docker')

    @tier2
    @run_only_on('sat')
    def test_positive_synchronize(self):
        """Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository and it is
        synchronized.

        @Feature: Repository
        """
        product = entities.Product(organization=self.org).create()
        repo = entities.Repository(
            content_type=u'docker',
            docker_upstream_name=u'busybox',
            name=u'busybox',
            product=product,
            url=DOCKER_REGISTRY_HUB,
        ).create()
        repo.sync()
        self.assertGreaterEqual(
            repo.read().content_counts['docker_manifest'], 1)

    @tier1
    @skip_if_bug_open('bugzilla', 1194476)
    def test_positive_update_name(self):
        """Update a repository's name.

        @Assert: The repository's name is updated.

        @Feature: Repository
        """
        repository = entities.Repository(
            content_type='docker'
        ).create()
        # The only data provided with the PUT request is a name. No other
        # information about the repository (such as its URL) is provided.
        new_name = gen_string('alpha')
        repository.name = new_name
        repository = repository.update(['name'])
        self.assertEqual(new_name, repository.name)
