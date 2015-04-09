"""Unit tests for the Docker feature."""
import httplib

from ddt import ddt
from fauxfactory import gen_choice, gen_string, gen_url
from nailgun import client
from random import randint, shuffle
from requests.exceptions import HTTPError
from robottelo import entities
from robottelo.common.constants import DOCKER_REGISTRY_HUB
from robottelo.common.decorators import (
    data, run_only_on, skip_if_bug_open, stubbed)
from robottelo.common.helpers import (
    get_external_docker_url,
    get_internal_docker_url,
    get_server_credentials,
)
from robottelo.test import APITestCase
# (too-many-public-methods) pylint:disable=R0904


DOCKER_PROVIDER = 'Docker'
EXTERNAL_DOCKER_URL = get_external_docker_url()
INTERNAL_DOCKER_URL = get_internal_docker_url()
STRING_TYPES = ['alpha', 'alphanumeric', 'cjk', 'utf8', 'latin1']


def _create_repository(prod_id, name=None, upstream_name=None):
    """Creates a Docker-based repository.

    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name for an existing Docker image.
        If ``None`` then defaults to ``busybox``.

    :return: A dictionary representing the created repository.

    """
    if name is None:
        name = gen_string(gen_choice(STRING_TYPES), 15)
    if upstream_name is None:
        upstream_name = u'busybox'
    return entities.Repository(
        product=prod_id,
        content_type=u'docker',
        name=name,
        docker_upstream_name=upstream_name,
        url=DOCKER_REGISTRY_HUB
    ).create_json()


def _add_repo_to_content_view(repo_id, cv_id):
    """Adds a repository to an existing content view.

    :param int repo_id: The ID for an existing repository.
    :param int cv_id: The ID for an existing content view.

    """
    client.put(
        entities.ContentView(id=cv_id).path(),
        auth=get_server_credentials(),
        verify=False,
        data={u'repository_ids': [repo_id]}
    ).raise_for_status()


def _add_content_view_to_composite_view(cv_id, cv_version_id):
    """Adds a published content view to a composite content view.

    :param int cv_id: The ID for an existing composite content view.
    :param int cv_version_id: The ID for a published non-composite
        content view.

    """
    client.put(
        entities.ContentView(id=cv_id).path(),
        auth=get_server_credentials(),
        verify=False,
        data={u'component_ids': [cv_version_id]}
    ).raise_for_status()


@ddt
class DockerRepositoryTestCase(APITestCase):
    """Tests specific to performing CRUD methods against ``Docker``
    repositories.

    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
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
    def test_create_one_docker_repo(self, name):
        """@Test: Create one Docker-type repository

        @Assert: A repository is created with a Docker image.

        @Feature: Docker

        """
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = _create_repository(prod_id, name)['id']
        real_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(real_attrs['name'], name)
        self.assertEqual(real_attrs['docker_upstream_name'], u'busybox')
        self.assertEqual(real_attrs['content_type'], u'docker')

    @run_only_on('sat')
    def test_create_multiple_docker_repo(self):
        """@Test: Create multiple Docker-type repositories

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to the same product.

        @Feature: Docker

        """
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        for _ in range(randint(1, 5)):
            repo_id = _create_repository(prod_id)['id']
            prod_attrs = entities.Product(id=prod_id).read_json()
            self.assertIn(
                repo_id,
                [repo['id'] for repo in prod_attrs['repositories']],
            )

    @run_only_on('sat')
    def test_create_multiple_docker_repo_multiple_products(self):
        """@Test: Create multiple Docker-type repositories on multiple products.

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to their respective products.

        @Feature: Docker

        """
        for _ in range(randint(1, 5)):
            prod_id = entities.Product(
                organization=self.org_id
            ).create_json()['id']
            for _ in range(randint(1, 3)):
                repo_id = _create_repository(prod_id)['id']
                prod_attrs = entities.Product(id=prod_id).read_json()
                self.assertIn(
                    repo_id,
                    [repo['id'] for repo in prod_attrs['repositories']],
                )

    @run_only_on('sat')
    def test_sync_docker_repo(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        """
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']
        repo_id = _create_repository(prod_id)['id']

        entities.Repository(id=repo_id).sync()
        attrs = entities.Repository(id=repo_id).read_json()
        self.assertGreaterEqual(attrs[u'content_counts'][u'docker_image'], 1)

    @run_only_on('sat')
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
        name = u'Busybox'
        upstream_name = u'busybox'
        content_type = u'docker'
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = _create_repository(prod_id, name, upstream_name)['id']
        real_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(real_attrs['name'], name)
        self.assertEqual(real_attrs['docker_upstream_name'], upstream_name)
        self.assertEqual(real_attrs['content_type'], content_type)

        # Update the repository name to random value
        real_attrs['name'] = new_name
        client.put(
            entities.Repository(id=repo_id).path(),
            real_attrs,
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()
        new_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(new_attrs['name'], new_name)
        self.assertNotEqual(new_attrs['name'], name)

    @skip_if_bug_open('bugzilla', 1193669)
    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_update_docker_repo_upstream_name(self, name):
        """@Test: Create a Docker-type repository and update its upstream name.

        @Assert: A repository is created with a Docker image and that its
        upstream name can be updated.

        @Feature: Docker

        @BZ: 1193669

        """
        upstream_name = u'busybox'
        new_upstream_name = u'fedora/ssh'
        content_type = u'docker'
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = _create_repository(prod_id, name, upstream_name)['id']
        real_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(real_attrs['name'], name)
        self.assertEqual(real_attrs['docker_upstream_name'], upstream_name)
        self.assertEqual(real_attrs['content_type'], content_type)

        # Update the repository upstream name
        real_attrs['docker_upstream_name'] = new_upstream_name
        client.put(
            entities.Repository(id=repo_id).path(),
            real_attrs,
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()
        new_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(new_attrs['docker_upstream_name'], new_upstream_name)
        self.assertNotEqual(new_attrs['name'], upstream_name)

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_update_docker_repo_url(self, name):
        """@Test: Create a Docker-type repository and update its URL.

        @Assert: A repository is created with a Docker image and that its
        URL can be updated.

        @Feature: Docker

        """
        new_url = gen_url(scheme='https')
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = _create_repository(prod_id, name)['id']
        real_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(real_attrs['url'], DOCKER_REGISTRY_HUB)

        # Update the repository URL
        real_attrs['url'] = new_url
        client.put(
            entities.Repository(id=repo_id).path(),
            real_attrs,
            auth=get_server_credentials(),
            verify=False,
        ).raise_for_status()
        new_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(new_attrs['url'], new_url)
        self.assertNotEqual(new_attrs['url'], DOCKER_REGISTRY_HUB)

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_delete_docker_repo(self, name):
        """@Test: Create and delete a Docker-type repository

        @Assert: A repository is created with a Docker image and then deleted.

        @Feature: Docker

        """
        upstream_name = u'busybox'
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = _create_repository(prod_id, name, upstream_name)['id']
        real_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(real_attrs['name'], name)
        self.assertEqual(real_attrs['docker_upstream_name'], upstream_name)
        self.assertEqual(real_attrs['content_type'], u'docker')

        # Delete it
        entities.Repository(id=repo_id).delete()
        with self.assertRaises(HTTPError):
            entities.Repository(id=repo_id).read_json()

    @run_only_on('sat')
    def test_delete_random_docker_repo(self):
        """@Test: Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        @Assert: Random repository can be deleted from random product without
        altering the other products.

        @Feature: Docker

        """
        upstream_name = u'busybox'
        product_ids = []
        repository_ids = []

        for _ in range(0, randint(1, 5)):
            product_ids.append(
                entities.Product(organization=self.org_id).create_json()['id'])

        for product_id in product_ids:
            name = gen_string('utf8', 15)
            repo_id = _create_repository(product_id, name, upstream_name)['id']
            real_attrs = entities.Repository(id=repo_id).read_json()
            self.assertEqual(real_attrs['name'], name)
            self.assertEqual(real_attrs['docker_upstream_name'], upstream_name)
            self.assertEqual(real_attrs['content_type'], u'docker')
            repository_ids.append(repo_id)

        # Delete a ramdom repository
        shuffle(repository_ids)
        repository_id = repository_ids.pop()
        entities.Repository(id=repository_id).delete()
        with self.assertRaises(HTTPError):
            entities.Repository(id=repository_id).read_json()

        # Check if others repositories are not touched
        for repository_id in repository_ids:
            repository = entities.Repository(id=repository_id).read_json()
            self.assertIn(repository['product']['id'], product_ids)


@ddt
class DockerContentViewTestCase(APITestCase):
    """Tests specific to using ``Docker`` repositories with Content Views."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(DockerContentViewTestCase, cls).setUpClass()
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
    def test_add_docker_repo_to_content_view(self, name):
        """@Test: Add one Docker-type repository to a non-composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a non-composite content view

        @Feature: Docker

        """
        upstream_name = u'busybox'
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = _create_repository(prod_id, name, upstream_name)['id']
        real_attrs = entities.Repository(id=repo_id).read_json()
        self.assertEqual(real_attrs['name'], name)
        self.assertEqual(real_attrs['docker_upstream_name'], upstream_name)
        self.assertEqual(real_attrs['content_type'], u'docker')

        # Create content view and associate docker repo
        content_view = entities.ContentView(
            organization=self.org_id, composite=False
        ).create_json()
        _add_repo_to_content_view(repo_id, content_view['id'])
        new_attrs = entities.ContentView(id=content_view['id']).read_json()
        self.assertIn(repo_id, new_attrs['repository_ids'])

    @stubbed()
    @run_only_on('sat')
    def test_add_multiple_docker_repos_to_content_view(self):
        """@Test: Add multiple Docker-type repositories to a
        non-composite content view.

        @Assert: Repositories are created with Docker images and the
        product is added to a non-composite content view.

        @Feature: Docker

        @Status: Manual

        """

    @run_only_on('sat')
    def test_add_synced_docker_repo_to_content_view(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        """
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']
        repo_id = _create_repository(prod_id)['id']

        entities.Repository(id=repo_id).sync()
        attrs = entities.Repository(id=repo_id).read_json()
        self.assertGreaterEqual(attrs[u'content_counts'][u'docker_image'], 1)

        # Create content view and associate docker repo
        content_view = entities.ContentView(
            organization=self.org_id, composite=False
        ).create_json()
        _add_repo_to_content_view(repo_id, content_view['id'])
        new_attrs = entities.ContentView(id=content_view['id']).read_json()
        self.assertIn(repo_id, new_attrs['repository_ids'])

    @run_only_on('sat')
    @data(
        gen_string('alpha', 15),
        gen_string('alphanumeric', 15),
        gen_string('numeric', 15),
        gen_string('latin1', 15),
        gen_string('utf8', 15),
        gen_string('html', 15),
    )
    def test_add_docker_repo_to_composite_content_view(self, name):
        """@Test: Add one Docker-type repository to a composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a content view which is then added to a composite
        content view.

        @Feature: Docker

        """
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = _create_repository(prod_id, name)['id']

        # Create content view and associate docker repo
        content_view = entities.ContentView(
            organization=self.org_id, composite=False
        ).create_json()
        _add_repo_to_content_view(repo_id, content_view['id'])

        new_attrs = entities.ContentView(id=content_view['id']).read_json()
        self.assertIn(repo_id, new_attrs['repository_ids'])

        # Publish it...
        entities.ContentView(id=content_view['id']).publish()
        # ... and grab its version ID (there should only be one version)
        new_attrs = entities.ContentView(id=content_view['id']).read_json()
        version_id = new_attrs['versions'][0]['id']

        # Create composite content view and associate content view to
        # it
        comp_content_view_id = entities.ContentView(
            organization=self.org_id, composite=True
        ).create_json()['id']
        _add_content_view_to_composite_view(
            comp_content_view_id, version_id)

        new_attrs = entities.ContentView(
            id=comp_content_view_id
        ).read_json()
        self.assertIn(version_id, new_attrs['component_ids'])

    @run_only_on('sat')
    def test_add_multiple_docker_repos_to_composite_content_view(self):
        """@Test: Add multiple Docker-type repositories to a composite
        content view.

        @Assert: One repository is created with a Docker image and the
        product is added to a random number of content views which are then
        added to a composite content view.

        @Feature: Docker

        """
        prod_ids = []
        cv_version_ids = []

        for _ in range(randint(1, 5)):
            prod_ids.append(
                entities.Product(organization=self.org_id).create_json()['id']
            )

        for prod_id in prod_ids:
            repo_id = _create_repository(prod_id)['id']

            # Create content view and associate docker repo
            content_view = entities.ContentView(
                organization=self.org_id, composite=False
            ).create_json()
            _add_repo_to_content_view(repo_id, content_view['id'])

            new_attrs = entities.ContentView(id=content_view['id']).read_json()
            self.assertIn(repo_id, new_attrs['repository_ids'])

            # Publish it...
            entities.ContentView(id=content_view['id']).publish()
            # ... and grab its version ID (there should only be one version)
            new_attrs = entities.ContentView(id=content_view['id']).read_json()
            cv_version_ids.append(new_attrs['versions'][0]['id'])

        # Create composite content view and associate content view to
        # it
        comp_content_view_id = entities.ContentView(
            organization=self.org_id, composite=True
        ).create_json()['id']
        for version_id in cv_version_ids:
            _add_content_view_to_composite_view(
                comp_content_view_id, version_id)

            new_attrs = entities.ContentView(
                id=comp_content_view_id).read_json()
            self.assertIn(version_id, new_attrs['component_ids'])

    @run_only_on('sat')
    def test_publish_once_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish
        it once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once.

        @Feature: Docker

        """
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = _create_repository(prod_id)['id']

        content_view = entities.ContentView(
            organization=self.org_id, composite=False).create_json()
        _add_repo_to_content_view(repo_id, content_view['id'])

        new_attrs = entities.ContentView(id=content_view['id']).read_json()
        self.assertIn(repo_id, new_attrs['repository_ids'])
        # Not published yet?
        self.assertIsNone(new_attrs['last_published'])
        self.assertEqual(new_attrs['next_version'], 1)

        # Publish it...
        entities.ContentView(id=content_view['id']).publish()
        # ... and check that it was indeed published
        new_attrs = entities.ContentView(id=content_view['id']).read_json()
        self.assertIsNotNone(new_attrs['last_published'])
        self.assertGreater(new_attrs['next_version'], 1)

    @run_only_on('sat')
    def test_publish_once_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite
        content view and publish it once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once and then
        added to a composite content view which is also published only once.

        @Feature: Docker

        """
        prod_id = entities.Product(
            organization=self.org_id
        ).create_json()['id']

        repo_id = _create_repository(prod_id)['id']

        content_view = entities.ContentView(
            organization=self.org_id, composite=False).create_json()
        _add_repo_to_content_view(repo_id, content_view['id'])

        new_attrs = entities.ContentView(id=content_view['id']).read_json()
        self.assertIn(repo_id, new_attrs['repository_ids'])
        # Not published yet?
        self.assertIsNone(new_attrs['last_published'])
        self.assertEqual(new_attrs['next_version'], 1)

        # Publish it...
        entities.ContentView(id=content_view['id']).publish()
        # ... and check that it was indeed published
        new_attrs = entities.ContentView(id=content_view['id']).read_json()
        version_id = new_attrs['versions'][0]['id']
        self.assertIsNotNone(new_attrs['last_published'])
        self.assertGreater(new_attrs['next_version'], 1)

        # Create composite content view...
        comp_content_view_id = entities.ContentView(
            organization=self.org_id, composite=True
        ).create_json()['id']
        # ... add content view to it...
        _add_content_view_to_composite_view(
            comp_content_view_id, version_id)
        new_attrs = entities.ContentView(
            id=comp_content_view_id).read_json()
        self.assertIn(version_id, new_attrs['component_ids'])
        # ... publish it...
        entities.ContentView(id=content_view['id']).publish()
        # ... and check that it was indeed published
        new_attrs = entities.ContentView(
            id=comp_content_view_id).read_json()
        self.assertIsNotNone(new_attrs['last_published'])
        self.assertGreater(new_attrs['next_version'], 1)

    @stubbed()
    @run_only_on('sat')
    def test_publish_multiple_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it
        multiple times.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published multiple times.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_publish_multiple_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it
        multiple times.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then added to a composite content
        view which is then published multiple times.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_promote_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then promote it to the next available lifecycle-environment.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environment.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_promote_multiple_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then promote it to multiple available lifecycle-environments.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_promote_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite content view and
        publish it. Then promote it to the next available
        lifecycle-environment.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environment.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_promote_multiple_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite content view and
        publish it. Then promote it to the multiple available
        lifecycle-environments.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.

        @Feature: Docker

        @Status: Manual

        """


@ddt
class DockerActivationKeyTestCase(APITestCase):
    """Tests specific to adding ``Docker`` repositories to Activation Keys."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerActivationKeyTestCase, cls).setUpClass()
        cls.org_id = entities.Organization().create_json()['id']

    @stubbed()
    @run_only_on('sat')
    def test_add_docker_repo_to_activation_key(self):
        """@Test:Add Docker-type repository to a non-composite
        content view and publish it. Then create an activation key
        and associate it with the Docker content view.

        @Assert: Docker-based content view can be added to activation key

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_remove_docker_repo_to_activation_key(self):
        """@Test:Add Docker-type repository to a non-composite
        content view and publish it. Create an activation key
        and associate it with the Docker content view. Then remove
        this content view from the activation key.

        @Assert: Docker-based content view can be added and then removed
        from the activation key.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_add_docker_repo_composite_view_to_activation_key(self):
        """@Test:Add Docker-type repository to a non-composite
        content view and publish it. Then add this content view to a composite
        content view and publish it. Create an activation key and associate it
        with the composite Docker content view.

        @Assert: Docker-based content view can be added to activation key

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_remove_docker_repo_composite_view_to_activation_key(self):
        """@Test:Add Docker-type repository to a non-composite
        content view and publish it. Then add this content view to a composite
        content view and publish it. Create an activation key and associate it
        with the composite Docker content view. Then, remove the composite
        content view from the activation key.

        @Assert: Docker-based composite content view can be added and then
        removed from the activation key.

        @Feature: Docker

        @Status: Manual

        """


@ddt
class DockerClientTestCase(APITestCase):
    """Tests specific to using ``Docker`` as a client to pull Docker images from
    a Satellite 6 instance."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerClientTestCase, cls).setUpClass()
        cls.org_id = entities.Organization().create_json()['id']

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


@ddt
class DockerComputeResourceTestCase(APITestCase):
    """Tests specific to managing Docker-based Compute Resources."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerComputeResourceTestCase, cls).setUpClass()
        cls.org_id = entities.Organization().create_json()['id']

    @run_only_on('sat')
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
        compute_resource_id = entities.ComputeResource(
            name=name,
            provider=DOCKER_PROVIDER,
            url=INTERNAL_DOCKER_URL
        ).create_json()['id']

        compute_resource = entities.ComputeResource(
            id=compute_resource_id).read_json()

        self.assertEqual(compute_resource['name'], name)
        self.assertEqual(compute_resource['url'], INTERNAL_DOCKER_URL)
        self.assertEqual(compute_resource['provider'], DOCKER_PROVIDER)

    @stubbed()
    @run_only_on('sat')
    def test_update_internal_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the
        Satellite 6 instance then edit its attributes.

        @Assert: Compute Resource can be created, listed and its
        attributes can be updated.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_list_containers_internal_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the
        Satellite 6 instance then list its running containers.

        @Assert: Compute Resource can be created, listed and existing
        running instances can be listed.

        @Feature: Docker

        @Status: Manual

        """

    @run_only_on('sat')
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
        compute_resource_id = entities.ComputeResource(
            name=name,
            provider=DOCKER_PROVIDER,
            url=EXTERNAL_DOCKER_URL
        ).create_json()['id']

        compute_resource = entities.ComputeResource(
            id=compute_resource_id).read_json()

        self.assertEqual(compute_resource['name'], name)
        self.assertEqual(compute_resource['url'], EXTERNAL_DOCKER_URL)
        self.assertEqual(compute_resource['provider'], DOCKER_PROVIDER)

    @stubbed()
    @run_only_on('sat')
    def test_update_external_docker_compute_resource(self):
        """@Test:@Test: Create a Docker-based Compute Resource using
        an external Docker-enabled system then edit its attributes.

        @Assert: Compute Resource can be created, listed and its
        attributes can be updated.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_list_containers_external_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource using
        an external Docker-enabled system then list its running containers.

        @Assert: Compute Resource can be created, listed and existing
        running instances can be listed.

        @Feature: Docker

        @Status: Manual

        """

    @run_only_on('sat')
    @data(
        EXTERNAL_DOCKER_URL,
        INTERNAL_DOCKER_URL,
    )
    def test_delete_docker_compute_resource(self, url):
        """@Test: Create a Docker-based Compute Resource then delete it.

        @Assert: Compute Resource can be created, listed and deleted.

        @Feature: Docker

        """
        compute_resource_id = entities.ComputeResource(
            provider=DOCKER_PROVIDER,
            url=url
        ).create_json()['id']

        compute_resource = entities.ComputeResource(
            id=compute_resource_id).read_json()
        self.assertEqual(compute_resource['url'], url)
        self.assertEqual(compute_resource['provider'], DOCKER_PROVIDER)

        entities.ComputeResource(id=compute_resource_id).delete()

        self.assertEqual(
            httplib.NOT_FOUND,
            entities.ComputeResource(
                id=compute_resource_id).read_raw().status_code
        )


class DockerContainersTestCase(APITestCase):
    """Tests specific to using ``Containers`` in local and external Docker
    Compute Resources

    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerContainersTestCase, cls).setUpClass()
        cls.org_id = entities.Organization().create_json()['id']
        # TODO: create Docker-based compute resources (internal/external)

    @stubbed()
    @run_only_on('sat')
    def test_create_container_local_compute_resource(self):
        """@Test: Create a container in a local compute resource

        @Feature: Docker

        @Assert: The docker container is created in the local compute resource

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_create_container_external_compute_resource(self):
        """@Test: Create a container in an external compute resource

        @Feature: Docker

        @Assert: The docker container is created in the external compute
        resource

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_create_container_local_compute_resource_power(self):
        """@Test: Create a container in a local compute resource, then power it
        on and finally power it off

        @Feature: Docker

        @Assert: The docker container is created in the local compute resource
        and the power status is showing properly

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_create_container_external_compute_resource_power(self):
        """@Test: Create a container in an external compute resource, then
        power it on and finally power it off

        @Feature: Docker

        @Assert: The docker container is created in the external compute
        resource and the power status is showing properly

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_create_container_local_compute_resource_read_log(self):
        """@Test: Create a container in a local compute resource and read its
        log

        @Feature: Docker

        @Assert: The docker container is created in the local compute resource
        and its log can be read

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_create_container_external_compute_resource_read_log(self):
        """@Test: Create a container in an external compute resource and read
        its log

        @Feature: Docker

        @Assert: The docker container is created in the external compute
        resource and its log can be read

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_create_container_external_registry(self):
        """@Test: Create a container pulling an image from a custom external
        registry

        @Feature: Docker

        @Assert: The docker container is created and the image is pulled from
        the external registry

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_delete_container_local_compute_resource(self):
        """@Test: Delete a container in a local compute resource

        @Feature: Docker

        @Assert: The docker container is deleted in the local compute resource

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_delete_container_external_compute_resource(self):
        """@Test: Delete a container in an external compute resource

        @Feature: Docker

        @Assert: The docker container is deleted in the local compute resource

        @Status: Manual

        """


@ddt
class DockerRegistriesTestCase(APITestCase):
    """Tests specific to performing CRUD methods against ``Registries``
    repositories.

    """

    @stubbed()
    @run_only_on('sat')
    def test_create_registry(self):
        """@Test: Create an external docker registry

        @Feature: Docker

        @Assert: the external registry is created

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_update_registry_name(self):
        """@Test: Create an external docker registry and update its name

        @Feature: Docker

        @Assert: the external registry is updated with the new name

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_update_registry_url(self):
        """@Test: Create an external docker registry and update its URL

        @Feature: Docker

        @Assert: the external registry is updated with the new URL

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_update_registry_description(self):
        """@Test: Create an external docker registry and update its description

        @Feature: Docker

        @Assert: the external registry is updated with the new description

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_update_registry_username(self):
        """@Test: Create an external docker registry and update its username

        @Feature: Docker

        @Assert: the external registry is updated with the new username

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_delete_registry(self):
        """@Test: Create an external docker registry

        @Feature: Docker

        @Assert: the external registry is created

        @Status: Manual

        """
