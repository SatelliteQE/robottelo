# -*- encoding: utf-8 -*-
"""Unit tests for the Docker feature."""
from ddt import ddt
from fauxfactory import gen_choice, gen_string, gen_url
from nailgun import entities
from random import randint, shuffle
from requests.exceptions import HTTPError
from robottelo.api.utils import promote
from robottelo.common.constants import DOCKER_REGISTRY_HUB
from robottelo.common.decorators import (
    data,
    run_only_on,
    skip_if_bug_open,
    stubbed,
)
from robottelo.common.helpers import (
    get_external_docker_url,
    get_internal_docker_url,
    valid_data_list,
)
from robottelo.test import APITestCase


DOCKER_PROVIDER = 'Docker'
EXTERNAL_DOCKER_URL = get_external_docker_url()
INTERNAL_DOCKER_URL = get_internal_docker_url()
STRING_TYPES = ['alpha', 'alphanumeric', 'cjk', 'utf8', 'latin1']
INVALID_DOCKER_UPSTREAM_NAMES = (
    # boundaries
    gen_string('alphanumeric', 2),
    gen_string('alphanumeric', 31),
    u'{0}/{1}'.format(
        gen_string('alphanumeric', 3),
        gen_string('alphanumeric', 3)
    ),
    u'{0}/{1}'.format(
        gen_string('alphanumeric', 4),
        gen_string('alphanumeric', 2)
    ),
    u'{0}/{1}'.format(
        gen_string('alphanumeric', 31),
        gen_string('alphanumeric', 30)
    ),
    u'{0}/{1}'.format(
        gen_string('alphanumeric', 30),
        gen_string('alphanumeric', 31)
    ),
    # not allowed non alphanumeric character
    u'{0}+{1}_{2}/{2}-{1}_{0}.{3}'.format(
        gen_string('alphanumeric', randint(3, 6)),
        gen_string('alphanumeric', randint(3, 6)),
        gen_string('alphanumeric', randint(3, 6)),
        gen_string('alphanumeric', randint(3, 6)),
    ),
    u'{0}-{1}_{2}/{2}+{1}_{0}.{3}'.format(
        gen_string('alphanumeric', randint(3, 6)),
        gen_string('alphanumeric', randint(3, 6)),
        gen_string('alphanumeric', randint(3, 6)),
        gen_string('alphanumeric', randint(3, 6)),
    ),
)
VALID_DOCKER_UPSTREAM_NAMES = (
    # boundaries
    gen_string('alphanumeric', 3).lower(),
    gen_string('alphanumeric', 30).lower(),
    u'{0}/{1}'.format(
        gen_string('alphanumeric', 4).lower(),
        gen_string('alphanumeric', 3).lower(),
    ),
    u'{0}/{1}'.format(
        gen_string('alphanumeric', 30).lower(),
        gen_string('alphanumeric', 30).lower(),
    ),
    # allowed non alphanumeric character
    u'{0}-{1}_{2}/{2}-{1}_{0}.{3}'.format(
        gen_string('alphanumeric', randint(3, 6)).lower(),
        gen_string('alphanumeric', randint(3, 6)).lower(),
        gen_string('alphanumeric', randint(3, 6)).lower(),
        gen_string('alphanumeric', randint(3, 6)).lower(),
    ),
    u'-_-_/-_.',
)


def _create_repository(product, name=None, upstream_name=None):
    """Creates a Docker-based repository.

    :param product: A ``Product`` object.
    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name for an existing Docker image.
        If ``None`` then defaults to ``busybox``.
    :return: A ``Repository`` object.

    """
    if name is None:
        name = gen_string(gen_choice(STRING_TYPES), 15)
    if upstream_name is None:
        upstream_name = u'busybox'
    return entities.Repository(
        content_type=u'docker',
        docker_upstream_name=upstream_name,
        name=name,
        product=product,
        url=DOCKER_REGISTRY_HUB,
    ).create()


@run_only_on('sat')
@ddt
class DockerRepositoryTestCase(APITestCase):
    """Tests specific to performing CRUD methods against ``Docker``
    repositories.

    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_create_one_docker_repo(self, name):
        """@Test: Create one Docker-type repository

        @Assert: A repository is created with a Docker image.

        @Feature: Docker

        """
        repo = _create_repository(
            entities.Product(organization=self.org).create(),
            name,
        )
        self.assertEqual(repo.name, name)
        self.assertEqual(repo.docker_upstream_name, 'busybox')
        self.assertEqual(repo.content_type, 'docker')

    @data(*VALID_DOCKER_UPSTREAM_NAMES)
    def test_create_docker_repo_valid_upstream_name(self, upstream_name):
        """@Test: Create a Docker-type repository with a valid docker upstream
        name

        @Assert: A repository is created with the specified upstream name.

        @Feature: Docker

        """
        repo = _create_repository(
            entities.Product(organization=self.org).create(),
            upstream_name=upstream_name,
        )
        self.assertEqual(repo.docker_upstream_name, upstream_name)
        self.assertEqual(repo.content_type, u'docker')

    @data(*INVALID_DOCKER_UPSTREAM_NAMES)
    def test_create_docker_repo_invalid_upstream_name(self, upstream_name):
        """@Test: Create a Docker-type repository with a invalid docker
        upstream name.

        @Assert: A repository is not created and a proper error is raised.

        @Feature: Docker

        """
        product = entities.Product(organization=self.org).create()
        with self.assertRaises(HTTPError):
            _create_repository(product, upstream_name=upstream_name)

    def test_create_multiple_docker_repo(self):
        """@Test: Create multiple Docker-type repositories

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to the same product.

        @Feature: Docker

        """
        product = entities.Product(organization=self.org).create()
        for _ in range(randint(2, 5)):
            repo = _create_repository(product)
            product = product.read()
            self.assertIn(repo.id, [repo_.id for repo_ in product.repository])

    def test_create_multiple_docker_repo_multiple_products(self):
        """@Test: Create multiple Docker-type repositories on multiple products.

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to their respective products.

        @Feature: Docker

        """
        for _ in range(randint(2, 5)):
            product = entities.Product(organization=self.org).create()
            for _ in range(randint(2, 3)):
                repo = _create_repository(product)
                product = product.read()
                self.assertIn(
                    repo.id,
                    [repo_.id for repo_ in product.repository],
                )

    def test_sync_docker_repo(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        """
        repo = _create_repository(
            entities.Product(organization=self.org).create()
        )
        repo.sync()
        attrs = repo.read_json()
        self.assertGreaterEqual(attrs[u'content_counts'][u'docker_image'], 1)

    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_update_docker_repo_name(self, new_name):
        """@Test: Create a Docker-type repository and update its name.

        @Assert: A repository is created with a Docker image and that its
        name can be updated.

        @Feature: Docker

        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        self.assertNotEqual(repo.name, new_name)
        # Update the repository name to random value
        repo.name = new_name
        repo = repo.update()
        self.assertEqual(repo.name, new_name)

    def test_update_docker_repo_upstream_name(self):
        """@Test: Create a Docker-type repository and update its upstream name.

        @Assert: A repository is created with a Docker image and that its
        upstream name can be updated.

        @Feature: Docker

        """
        new_upstream_name = u'fedora/ssh'
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        self.assertNotEqual(repo.docker_upstream_name, new_upstream_name)

        # Update the repository upstream name
        repo.docker_upstream_name = new_upstream_name
        repo = repo.update()
        self.assertEqual(repo.docker_upstream_name, new_upstream_name)

    def test_update_docker_repo_url(self):
        """@Test: Create a Docker-type repository and update its URL.

        @Assert: A repository is created with a Docker image and that its
        URL can be updated.

        @Feature: Docker

        """
        new_url = gen_url()
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        self.assertEqual(repo.url, DOCKER_REGISTRY_HUB)

        # Update the repository URL
        repo.url = new_url
        repo = repo.update()
        self.assertEqual(repo.url, new_url)
        self.assertNotEqual(repo.url, DOCKER_REGISTRY_HUB)

    def test_delete_docker_repo(self):
        """@Test: Create and delete a Docker-type repository

        @Assert: A repository is created with a Docker image and then deleted.

        @Feature: Docker

        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        # Delete it
        repo.delete()
        with self.assertRaises(HTTPError):
            repo.read()

    def test_delete_random_docker_repo(self):
        """@Test: Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        @Assert: Random repository can be deleted from random product without
        altering the other products.

        @Feature: Docker

        """
        repos = []
        products = [
            entities.Product(organization=self.org).create()
            for _
            in range(randint(2, 5))
        ]
        for product in products:
            repo = _create_repository(product)
            self.assertEqual(repo.content_type, u'docker')
            repos.append(repo)

        # Delete a random repository
        shuffle(repos)
        repo = repos.pop()
        repo.delete()
        with self.assertRaises(HTTPError):
            repo.read()

        # Check if others repositories are not touched
        for repo in repos:
            repo = repo.read()
            self.assertIn(repo.product.id, [prod.id for prod in products])


@run_only_on('sat')
@ddt
class DockerContentViewTestCase(APITestCase):
    """Tests specific to using ``Docker`` repositories with Content Views."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(DockerContentViewTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    def test_add_docker_repo_to_content_view(self):
        """@Test: Add one Docker-type repository to a non-composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a non-composite content view

        @Feature: Docker

        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        # Create content view and associate docker repo
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertIn(repo.id, [repo_.id for repo_ in content_view.repository])

    def test_add_multiple_docker_repos_to_content_view(self):
        """@Test: Add multiple Docker-type repositories to a
        non-composite content view.

        @Assert: Repositories are created with Docker images and the
        product is added to a non-composite content view.

        @Feature: Docker

        """
        product = entities.Product(organization=self.org).create()
        repos = [
            _create_repository(product, name=gen_string('alpha'))
            for _
            in range(randint(2, 5))
        ]
        self.assertEqual(len(product.read().repository), len(repos))

        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = repos
        content_view = content_view.update(['repository'])

        self.assertEqual(len(content_view.repository), len(repos))

        content_view.repository = [
            repo.read() for repo in content_view.repository
        ]

        self.assertEqual(
            {repo.id for repo in repos},
            {repo.id for repo in content_view.repository}
        )

        for repo in repos + content_view.repository:
            self.assertEqual(repo.content_type, u'docker')
            self.assertEqual(repo.docker_upstream_name, u'busybox')

    def test_add_synced_docker_repo_to_content_view(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        repo.sync()
        attrs = repo.read_json()
        self.assertGreaterEqual(attrs[u'content_counts'][u'docker_image'], 1)

        # Create content view and associate docker repo
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertIn(repo.id, [repo_.id for repo_ in content_view.repository])

    def test_add_docker_repo_to_composite_content_view(self):
        """@Test: Add one Docker-type repository to a composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a content view which is then added to a composite
        content view.

        @Feature: Docker

        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())

        # Create content view and associate docker repo
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertIn(repo.id, [repo_.id for repo_ in content_view.repository])

        # Publish it and grab its version ID (there should only be one version)
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)

        # Create composite content view and associate content view to it
        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        comp_content_view.component = content_view.version
        comp_content_view = comp_content_view.update(['component'])
        self.assertIn(
            content_view.version[0].id,
            [component.id for component in comp_content_view.component]
        )

    def test_add_multiple_docker_repos_to_composite_content_view(self):
        """@Test: Add multiple Docker-type repositories to a composite
        content view.

        @Assert: One repository is created with a Docker image and the
        product is added to a random number of content views which are then
        added to a composite content view.

        @Feature: Docker

        """
        cv_versions = []
        product = entities.Product(organization=self.org).create()
        for _ in range(randint(2, 5)):
            # Create content view and associate docker repo
            content_view = entities.ContentView(
                composite=False,
                organization=self.org,
            ).create()
            repo = _create_repository(product)
            content_view.repository = [repo]
            content_view = content_view.update(['repository'])
            self.assertIn(
                repo.id,
                [repo_.id for repo_ in content_view.repository]
            )

            # Publish it and grab its version ID (there should be one version)
            content_view.publish()
            content_view = content_view.read()
            cv_versions.append(content_view.version[0])

        # Create composite content view and associate content view to it
        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        for cv_version in cv_versions:
            comp_content_view.component.append(cv_version)
            comp_content_view = comp_content_view.update(['component'])
            self.assertIn(
                cv_version.id,
                [component.id for component in comp_content_view.component]
            )

    def test_publish_once_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish
        it once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once.

        @Feature: Docker

        """
        product = entities.Product(organization=self.org).create()
        repo = _create_repository(product)

        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertIn(repo.id, [repo_.id for repo_ in content_view.repository])

        # Not published yet?
        attrs = content_view.read_json()
        self.assertIsNone(attrs['last_published'])
        self.assertEqual(attrs['next_version'], 1)

        # Publish it and check that it was indeed published.
        content_view.publish()
        attrs = content_view.read_json()
        self.assertIsNotNone(attrs['last_published'])
        self.assertGreater(attrs['next_version'], 1)

    @skip_if_bug_open('bugzilla', 1217635)
    def test_publish_once_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite
        content view and publish it once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once and then
        added to a composite content view which is also published only once.

        @Feature: Docker

        """
        product = entities.Product(organization=self.org).create()
        repo = _create_repository(product)
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertIn(repo.id, [repo_.id for repo_ in content_view.repository])

        # Not published yet?
        attrs = content_view.read_json()
        self.assertIsNone(attrs['last_published'])
        self.assertEqual(attrs['next_version'], 1)

        # Publish it and check that it was indeed published.
        content_view.publish()
        attrs = content_view.read_json()
        self.assertIsNotNone(attrs['last_published'])
        self.assertGreater(attrs['next_version'], 1)

        # Create composite content view…
        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        cv_version = entities.ContentViewVersion(id=attrs['versions'][0]['id'])
        comp_content_view.component = [cv_version]
        comp_content_view = comp_content_view.update(['component'])
        self.assertIn(
            cv_version.id,  # pylint:disable=no-member
            [component.id for component in comp_content_view.component]
        )
        # … publish it…
        comp_content_view.publish()
        # … and check that it was indeed published
        attrs = comp_content_view.read_json()
        self.assertIsNotNone(attrs['last_published'])
        self.assertGreater(attrs['next_version'], 1)

    def test_publish_multiple_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it
        multiple times.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published multiple times.

        @Feature: Docker

        """
        product = entities.Product(organization=self.org).create()
        repo = _create_repository(product)
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(
            [repo.id], [repo_.id for repo_ in content_view.repository])
        self.assertIsNone(content_view.read_json()['last_published'])

        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            content_view.publish()
        self.assertIsNotNone(content_view.read_json()['last_published'])
        self.assertEqual(len(content_view.read().version), publish_amount)

    def test_publish_multiple_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it
        multiple times.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then added to a composite content
        view which is then published multiple times.

        @Feature: Docker

        """
        product = entities.Product(organization=self.org).create()
        repo = _create_repository(product)
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(
            [repo.id], [repo_.id for repo_ in content_view.repository])
        self.assertIsNone(content_view.read_json()['last_published'])

        content_view.publish()
        self.assertIsNotNone(content_view.read_json()['last_published'])
        cvv = content_view.read().version[0].read()

        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        comp_content_view.component = [cvv]
        comp_content_view = comp_content_view.update(['component'])
        self.assertEqual(
            [cvv.id], [comp.id for comp in comp_content_view.component])
        self.assertIsNone(comp_content_view.read_json()['last_published'])

        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            comp_content_view.publish()
        self.assertIsNotNone(comp_content_view.read_json()['last_published'])
        self.assertEqual(len(comp_content_view.read().version), publish_amount)

    def test_promote_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then promote it to the next available lifecycle-environment.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environment.

        @Feature: Docker

        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        repo = _create_repository(product)

        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(
            [repo.id], [repo_.id for repo_ in content_view.repository])

        content_view.publish()
        content_view = content_view.read()
        cvv = content_view.version[0].read()
        self.assertEqual(len(cvv.environment), 1)

        promote(cvv, lce.id)
        self.assertEqual(len(cvv.read().environment), 2)

    def test_promote_multiple_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then promote it to multiple available lifecycle-environments.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.

        @Feature: Docker

        """

        product = entities.Product(organization=self.org).create()
        repo = _create_repository(product)

        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(
            [repo.id], [repo_.id for repo_ in content_view.repository])

        content_view.publish()
        cvv = content_view.read().version[0]
        self.assertEqual(len(cvv.read().environment), 1)

        for i in range(1, randint(3, 6)):
            lce = entities.LifecycleEnvironment(organization=self.org).create()
            promote(cvv, lce.id)
            self.assertEqual(len(cvv.read().environment), i+1)

    def test_promote_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then add that content view to composite one. Publish and promote that
        composite content view to the next available lifecycle-environment.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environment.

        @Feature: Docker

        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        product = entities.Product(organization=self.org).create()
        repo = _create_repository(product)
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(
            [repo.id], [repo_.id for repo_ in content_view.repository])

        content_view.publish()
        cvv = content_view.read().version[0].read()

        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        comp_content_view.component = [cvv]
        comp_content_view = comp_content_view.update(['component'])
        self.assertEqual(cvv.id, comp_content_view.component[0].id)

        comp_content_view.publish()
        comp_cvv = comp_content_view.read().version[0]
        self.assertEqual(len(comp_cvv.read().environment), 1)

        promote(comp_cvv, lce.id)
        self.assertEqual(len(comp_cvv.read().environment), 2)

    def test_promote_multiple_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then add that content view to composite one. Publish and promote that
        composite content view to the multiple available lifecycle-environments

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.

        @Feature: Docker

        """
        product = entities.Product(organization=self.org).create()
        repo = _create_repository(product)
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(
            [repo.id], [repo_.id for repo_ in content_view.repository])

        content_view.publish()
        cvv = content_view.read().version[0].read()

        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        comp_content_view.component = [cvv]
        comp_content_view = comp_content_view.update(['component'])
        self.assertEqual(cvv.id, comp_content_view.component[0].id)

        comp_content_view.publish()
        comp_cvv = comp_content_view.read().version[0]
        self.assertEqual(len(comp_cvv.read().environment), 1)

        for i in range(1, randint(3, 6)):
            lce = entities.LifecycleEnvironment(organization=self.org).create()
            promote(comp_cvv, lce.id)
            self.assertEqual(len(comp_cvv.read().environment), i+1)


@run_only_on('sat')
@ddt
class DockerActivationKeyTestCase(APITestCase):
    """Tests specific to adding ``Docker`` repositories to Activation Keys."""

    @classmethod
    def setUpClass(cls):
        """Create necessary objects which can be re-used in tests."""
        super(DockerActivationKeyTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.lce = entities.LifecycleEnvironment(organization=cls.org).create()
        cls.product = entities.Product(organization=cls.org).create()
        cls.repo = _create_repository(cls.product)
        content_view = entities.ContentView(
            composite=False,
            organization=cls.org,
        ).create()
        content_view.repository = [cls.repo]
        cls.content_view = content_view.update(['repository'])
        cls.content_view.publish()
        cls.cvv = content_view.read().version[0].read()
        promote(cls.cvv, cls.lce.id)

    def test_add_docker_repo_to_activation_key(self):
        """@Test: Add Docker-type repository to a non-composite content view
        and publish it. Then create an activation key and associate it with the
        Docker content view.

        @Assert: Docker-based content view can be added to activation key

        @Feature: Docker

        """
        ak = entities.ActivationKey(
            content_view=self.content_view,
            environment=self.lce,
            name=gen_string('utf8'),
            organization=self.org,
        ).create()
        self.assertEqual(ak.content_view.id, self.content_view.id)
        self.assertEqual(ak.content_view.read().repository[0].id, self.repo.id)

    def test_remove_docker_repo_to_activation_key(self):
        """@Test: Add Docker-type repository to a non-composite content view
        and publish it. Create an activation key and associate it with the
        Docker content view. Then remove this content view from the activation
        key.

        @Assert: Docker-based content view can be added and then removed from
        the activation key.

        @Feature: Docker

        """
        ak = entities.ActivationKey(
            content_view=self.content_view,
            environment=self.lce,
            name=gen_string('utf8'),
            organization=self.org,
        ).create()
        self.assertEqual(ak.content_view.id, self.content_view.id)
        ak.content_view = None
        self.assertIsNone(ak.update(['content_view']).content_view)

    def test_add_docker_repo_composite_view_to_activation_key(self):
        """@Test:Add Docker-type repository to a non-composite content view and
        publish it. Then add this content view to a composite content view and
        publish it. Create an activation key and associate it with the
        composite Docker content view.

        @Assert: Docker-based content view can be added to activation key

        @Feature: Docker

        """
        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        comp_content_view.component = [self.cvv]
        comp_content_view = comp_content_view.update(['component'])
        self.assertEqual(self.cvv.id, comp_content_view.component[0].id)

        comp_content_view.publish()
        comp_cvv = comp_content_view.read().version[0].read()
        promote(comp_cvv, self.lce.id)

        ak = entities.ActivationKey(
            content_view=comp_content_view,
            environment=self.lce,
            name=gen_string('utf8'),
            organization=self.org,
        ).create()
        self.assertEqual(ak.content_view.id, comp_content_view.id)

    def test_remove_docker_repo_composite_view_to_activation_key(self):
        """@Test: Add Docker-type repository to a non-composite content view
        and publish it. Then add this content view to a composite content view
        and publish it. Create an activation key and associate it with the
        composite Docker content view. Then, remove the composite content view
        from the activation key.

        @Assert: Docker-based composite content view can be added and then
        removed from the activation key.

        @Feature: Docker

        """
        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        comp_content_view.component = [self.cvv]
        comp_content_view = comp_content_view.update(['component'])
        self.assertEqual(self.cvv.id, comp_content_view.component[0].id)

        comp_content_view.publish()
        comp_cvv = comp_content_view.read().version[0].read()
        promote(comp_cvv, self.lce.id)

        ak = entities.ActivationKey(
            content_view=comp_content_view,
            environment=self.lce,
            name=gen_string('utf8'),
            organization=self.org,
        ).create()
        self.assertEqual(ak.content_view.id, comp_content_view.id)
        ak.content_view = None
        self.assertIsNone(ak.update(['content_view']).content_view)


@ddt
class DockerClientTestCase(APITestCase):
    """Tests specific to using ``Docker`` as a client to pull Docker images
    from a Satellite 6 instance."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerClientTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @stubbed()
    @run_only_on('sat')
    def test_docker_client_pull_image(self):
        """@Test: A Docker-enabled client can use ``docker pull`` to pull a
        Docker image off a Satellite 6 instance.

        @Steps:

        1. Publish and promote content view with Docker content
        2. Register Docker-enabled client against Satellite 6.

        @Assert: Client can pull Docker images from server and run it.

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_docker_client_upload_image(self):
        """@Test: A Docker-enabled client can create a new ``Dockerfile``
        pointing to an existing Docker image from a Satellite 6 and modify it.
        Then, using ``docker build`` generate a new image which can then be
        uploaded back onto the Satellite 6 as a new repository.

        @Steps:

        1. Publish and promote content view with Docker content
        2. Register Docker-enabled client against Satellite 6.

        @Assert: Client can create a new image based off an existing Docker
        image from a Satellite 6 instance, add a new package and upload the
        modified image (plus layer) back to the Satellite 6.

        @Status: Manual

        """


@run_only_on('sat')
@ddt
class DockerComputeResourceTestCase(APITestCase):
    """Tests specific to managing Docker-based Compute Resources."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerComputeResourceTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_create_internal_docker_compute_resource(self, name):
        """@Test: Create a Docker-based Compute Resource in the Satellite 6
        instance.

        @Assert: Compute Resource can be created and listed.

        @Feature: Docker

        """
        compute_resource = entities.DockerComputeResource(
            name=name,
            url=INTERNAL_DOCKER_URL,
        ).create()
        self.assertEqual(compute_resource.name, name)
        self.assertEqual(compute_resource.provider, DOCKER_PROVIDER)
        self.assertEqual(compute_resource.url, INTERNAL_DOCKER_URL)

    def test_update_internal_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the Satellite 6
        instance then edit its attributes.

        @Assert: Compute Resource can be created, listed and its attributes can
        be updated.

        @Feature: Docker

        """
        compute_resource = entities.DockerComputeResource(
            name=gen_string('alpha'),
            organization=[self.org],
            url=INTERNAL_DOCKER_URL,
        ).create()
        self.assertEqual(compute_resource.url, INTERNAL_DOCKER_URL)
        compute_resource.url = gen_url()
        self.assertEqual(
            compute_resource.url,
            compute_resource.update(['url']).url,
        )

    @stubbed()
    def test_list_containers_internal_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the
        Satellite 6 instance then list its running containers.

        @Assert: Compute Resource can be created, listed and existing
        running instances can be listed.

        @Feature: Docker

        @Status: Manual

        """

    @data(
        gen_string('alpha'),
        gen_string('alphanumeric'),
        gen_string('numeric'),
        gen_string('latin1'),
        gen_string('utf8'),
        gen_string('html'),
    )
    def test_create_external_docker_compute_resource(self, name):
        """@Test: Create a Docker-based Compute Resource using an external
        Docker-enabled system.

        @Assert: Compute Resource can be created and listed.

        @Feature: Docker

        """
        compute_resource = entities.DockerComputeResource(
            name=name,
            url=EXTERNAL_DOCKER_URL,
        ).create()
        self.assertEqual(compute_resource.name, name)
        self.assertEqual(compute_resource.provider, DOCKER_PROVIDER)
        self.assertEqual(compute_resource.url, EXTERNAL_DOCKER_URL)

    def test_update_external_docker_compute_resource(self):
        """@Test:@Test: Create a Docker-based Compute Resource using an
        external Docker-enabled system then edit its attributes.

        @Assert: Compute Resource can be created, listed and its attributes can
        be updated.

        @Feature: Docker

        """
        compute_resource = entities.DockerComputeResource(
            name=gen_string('alpha'),
            organization=[self.org],
            url=EXTERNAL_DOCKER_URL,
        ).create()
        self.assertEqual(compute_resource.url, EXTERNAL_DOCKER_URL)
        compute_resource.url = gen_url()
        self.assertEqual(
            compute_resource.url,
            compute_resource.update(['url']).url,
        )

    @stubbed()
    def test_list_containers_external_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource using
        an external Docker-enabled system then list its running containers.

        @Assert: Compute Resource can be created, listed and existing
        running instances can be listed.

        @Feature: Docker

        @Status: Manual

        """

    @data(
        EXTERNAL_DOCKER_URL,
        INTERNAL_DOCKER_URL,
    )
    def test_delete_docker_compute_resource(self, url):
        """@Test: Create a Docker-based Compute Resource then delete it.

        @Assert: Compute Resource can be created, listed and deleted.

        @Feature: Docker

        """
        compute_resource = entities.DockerComputeResource(url=url).create()
        self.assertEqual(compute_resource.url, url)
        self.assertEqual(compute_resource.provider, DOCKER_PROVIDER)
        compute_resource.delete()
        with self.assertRaises(HTTPError):
            compute_resource.read()


@run_only_on('sat')
class DockerContainersTestCase(APITestCase):
    """Tests specific to using ``Containers`` in local and external Docker
    Compute Resources

    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerContainersTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.cr_internal = entities.DockerComputeResource(
            name=gen_string('alpha'),
            organization=[cls.org],
            url=INTERNAL_DOCKER_URL,
        ).create()
        cls.cr_external = entities.DockerComputeResource(
            name=gen_string('alpha'),
            organization=[cls.org],
            url=EXTERNAL_DOCKER_URL,
        ).create()

    def setUp(self):
        """Generate default ``DockerHubContainer`` keyword arguments.

        Generate a dict of arguments that can be used when instantiating a
        ``DockerHubContainer`` and save it as ``self.dhc_kwargs``.

        """
        self.container_name = gen_string('alphanumeric')
        self.dhc_kwargs = {
            'command': 'top',
            'name': self.container_name,
            'organization': [self.org],
        }

    def test_create_container_local_compute_resource(self):
        """@Test: Create a container in a local compute resource

        @Feature: Docker

        @Assert: The docker container is created in the local compute resource

        """
        container = entities.DockerHubContainer(
            compute_resource=self.cr_internal,
            **self.dhc_kwargs
        ).create()
        self.assertEqual(
            container.compute_resource.read().name,
            self.cr_internal.name,
        )

    def test_create_container_external_compute_resource(self):
        """@Test: Create a container in an external compute resource

        @Feature: Docker

        @Assert: The docker container is created in the external compute
        resource

        """
        container = entities.DockerHubContainer(
            compute_resource=self.cr_external,
            **self.dhc_kwargs
        ).create()
        self.assertEqual(
            container.compute_resource.read().name,
            self.cr_external.name,
        )

    def test_create_container_local_compute_resource_power(self):
        """@Test: Create a container in a local compute resource, then power it
        on and finally power it off

        @Feature: Docker

        @Assert: The docker container is created in the local compute resource
        and the power status is showing properly

        """
        container = entities.DockerHubContainer(
            compute_resource=self.cr_internal,
            **self.dhc_kwargs
        ).create()
        self.assertEqual(
            container.compute_resource.read().url,
            INTERNAL_DOCKER_URL,
        )
        self.assertEqual(
            container.power(data={u'power_action': 'status'})['running'],
            True,
        )
        container.power(data={u'power_action': 'stop'})
        self.assertEqual(
            container.power(data={u'power_action': 'status'})['running'],
            False,
        )

    def test_create_container_external_compute_resource_power(self):
        """@Test: Create a container in an external compute resource, then
        power it on and finally power it off

        @Feature: Docker

        @Assert: The docker container is created in the external compute
        resource and the power status is showing properly

        """
        container = entities.DockerHubContainer(
            compute_resource=self.cr_external,
            **self.dhc_kwargs
        ).create()
        self.assertEqual(
            container.compute_resource.read().url,
            EXTERNAL_DOCKER_URL,
        )
        self.assertEqual(
            container.power(data={u'power_action': 'status'})['running'],
            True,
        )
        container.power(data={u'power_action': 'stop'})
        self.assertEqual(
            container.power(data={u'power_action': 'status'})['running'],
            False,
        )

    def test_create_container_local_compute_resource_read_log(self):
        """@Test: Create a container in a local compute resource and read its
        log

        @Feature: Docker

        @Assert: The docker container is created in the local compute resource
        and its log can be read

        """
        self.dhc_kwargs['command'] = 'ls'
        container = entities.DockerHubContainer(
            compute_resource=self.cr_internal,
            **self.dhc_kwargs
        ).create()
        self.assertIsNotNone(container.logs()['logs'])
        self.assertNotEqual(container.logs()['logs'], u'')

    def test_create_container_external_compute_resource_read_log(self):
        """@Test: Create a container in an external compute resource and read
        its log

        @Feature: Docker

        @Assert: The docker container is created in the external compute
        resource and its log can be read

        """
        self.dhc_kwargs['command'] = 'date'
        container = entities.DockerHubContainer(
            compute_resource=self.cr_external,
            **self.dhc_kwargs
        ).create()
        self.assertIsNotNone(container.logs()['logs'])
        self.assertNotEqual(container.logs()['logs'], u'')

    @stubbed()
    def test_create_container_external_registry(self):
        """@Test: Create a container pulling an image from a custom external
        registry

        @Feature: Docker

        @Assert: The docker container is created and the image is pulled from
        the external registry

        @Status: Manual

        """

    def test_delete_container_local_compute_resource(self):
        """@Test: Delete a container in a local compute resource

        @Feature: Docker

        @Assert: The docker container is deleted in the local compute resource

        """
        container = entities.DockerHubContainer(
            compute_resource=self.cr_internal,
            **self.dhc_kwargs
        ).create()
        self.assertEqual(container.name, self.container_name)
        container.delete()
        with self.assertRaises(HTTPError):
            container.read()

    def test_delete_container_external_compute_resource(self):
        """@Test: Delete a container in an external compute resource

        @Feature: Docker

        @Assert: The docker container is deleted in the local compute resource

        """
        container = entities.DockerHubContainer(
            compute_resource=self.cr_external,
            **self.dhc_kwargs
        ).create()
        self.assertEqual(container.name, self.container_name)
        container.delete()
        with self.assertRaises(HTTPError):
            container.read()


@ddt
class DockerRegistriesTestCase(APITestCase):
    """Tests specific to performing CRUD methods against ``Registries``
    repositories.

    """

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_create_registry(self, name):
        """@Test: Create an external docker registry

        @Feature: Docker

        @Assert: External registry is created successfully

        """
        url = gen_url(subdomain=gen_string('alpha'))
        description = gen_string('alphanumeric')
        registry = entities.Registry(
            name=name,
            url=url,
            description=description,
        ).create()
        self.assertEqual(registry.name, name)
        self.assertEqual(registry.url, url)
        self.assertEqual(registry.description, description)

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_update_registry_name(self, new_name):
        """@Test: Create an external docker registry and update its name

        @Feature: Docker

        @Assert: the external registry is updated with the new name

        """
        name = gen_string('alpha')
        registry = entities.Registry(name=name).create()
        self.assertEqual(registry.name, name)
        registry.name = new_name
        registry = registry.update()
        self.assertEqual(registry.name, new_name)

    @run_only_on('sat')
    def test_update_registry_url(self):
        """@Test: Create an external docker registry and update its URL

        @Feature: Docker

        @Assert: the external registry is updated with the new URL

        """
        url = gen_url(subdomain=gen_string('alpha'))
        new_url = gen_url(subdomain=gen_string('alpha'))
        registry = entities.Registry(url=url).create()
        self.assertEqual(registry.url, url)
        registry.url = new_url
        registry = registry.update()
        self.assertEqual(registry.url, new_url)

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_update_registry_description(self, new_desc):
        """@Test: Create an external docker registry and update its description

        @Feature: Docker

        @Assert: the external registry is updated with the new description

        """
        desc = gen_string('utf8')
        registry = entities.Registry(description=desc).create()
        self.assertEqual(registry.description, desc)
        registry.description = new_desc
        registry = registry.update()
        self.assertEqual(registry.description, new_desc)

    @run_only_on('sat')
    def test_update_registry_username(self):
        """@Test: Create an external docker registry and update its username

        @Feature: Docker

        @Assert: the external registry is updated with the new username

        """
        username = gen_string('alpha')
        new_username = gen_string('alpha')
        registry = entities.Registry(
            username=username,
            password=gen_string('alpha'),
        ).create()
        self.assertEqual(registry.username, username)
        registry.username = new_username
        registry = registry.update()
        self.assertEqual(registry.username, new_username)

    @run_only_on('sat')
    @data(*valid_data_list())
    def test_delete_registry(self, name):
        """@Test: Create an external docker registry and then delete it

        @Feature: Docker

        @Assert: The external registry is deleted successfully

        """
        registry = entities.Registry(name=name).create()
        registry.delete()
        with self.assertRaises(HTTPError):
            registry.read()
