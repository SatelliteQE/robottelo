"""WebUI tests for the Docker feature."""

from fauxfactory import gen_string, gen_url
from nailgun import entities
from random import randint, shuffle
from robottelo.api.utils import promote
from robottelo.constants import (
    DOCKER_REGISTRY_HUB,
    FOREMAN_PROVIDERS,
    REPO_TYPE,
)
from robottelo.decorators import run_only_on, stubbed
from robottelo.helpers import (
    get_external_docker_url,
    get_internal_docker_url,
    valid_data_list,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_activationkey,
    make_registry,
    make_repository,
    make_resource,
)
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session
# (too-many-public-methods) pylint:disable=R0904

EXTERNAL_DOCKER_URL = get_external_docker_url()
INTERNAL_DOCKER_URL = get_internal_docker_url()

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


def _create_repository(session, org, name, product, upstream_name=None):
    """Creates a Docker-based repository.

    :param session: The browser session.
    :param str org: Name of Organization where product should be created
    :param str name: Name for the repository
    :param str product: Name of product where repository should be created.
    :param str upstream_name: A valid name for an existing Docker image.
        If ``None`` then defaults to ``busybox``.

    """
    if upstream_name is None:
        upstream_name = u'busybox'
    make_repository(
        session,
        org=org,
        name=name,
        product=product,
        repo_type=REPO_TYPE['docker'],
        url=DOCKER_REGISTRY_HUB,
        upstream_repo_name=upstream_name,
    )


class DockerTagsTestCase(UITestCase):
    """Tests related to Content > Docker Tags page"""

    @stubbed()
    @run_only_on('sat')
    def test_search_docker_image(self):
        """@Test: Search for a docker image

        @Feature: Docker

        @Assert: The docker tag can be searched and found

        @Status: Manual

        """


class DockerRepositoryTestCase(UITestCase):
    """Tests specific to performing CRUD methods against ``Docker``
    repositories.

    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @run_only_on('sat')
    def test_create_one_docker_repo(self):
        """@Test: Create one Docker-type repository

        @Assert: A repository is created with a Docker image.

        @Feature: Docker

        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    product = entities.Product(
                        organization=self.organization
                    ).create()
                    _create_repository(
                        session,
                        org=self.organization.name,
                        name=name,
                        product=product.name,
                    )
                    self.assertIsNotNone(self.repository.search(name))

    @run_only_on('sat')
    def test_create_multiple_docker_repo(self):
        """@Test: Create multiple Docker-type repositories

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to the same product.

        @Feature: Docker

        """
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            for _ in range(randint(2, 5)):
                name = gen_string('utf8')
                _create_repository(
                    session,
                    org=self.organization.name,
                    name=name,
                    product=product.name,
                )
                self.navigator.go_to_products()
                self.products.search(product.name).click()
                self.assertIsNotNone(self.repository.search(name))

    @run_only_on('sat')
    def test_create_multiple_docker_repo_multiple_products(self):
        """@Test: Create multiple Docker-type repositories on multiple products.

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to their respective products.

        @Feature: Docker

        """
        with Session(self.browser) as session:
            for _ in range(randint(2, 3)):
                pr = entities.Product(organization=self.organization).create()
                for _ in range(randint(2, 3)):
                    name = gen_string('utf8')
                    _create_repository(
                        session,
                        org=self.organization.name,
                        name=name,
                        product=pr.name,
                    )
                    self.navigator.go_to_products()
                    self.products.search(pr.name).click()
                    self.assertIsNotNone(self.repository.search(name))

    @run_only_on('sat')
    def test_sync_docker_repo(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository and it is
        synchronized.

        @Feature: Docker

        """
        repo_name = gen_string('alphanumeric')
        product = entities.Product(organization=self.organization).create()
        with Session(self.browser) as session:
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            # Synchronize it
            self.navigator.go_to_sync_status()
            synced = self.sync.sync_custom_repos(product.name, [repo_name])
            self.assertTrue(synced)

    @run_only_on('sat')
    def test_update_docker_repo_name(self):
        """@Test: Create a Docker-type repository and update its name.

        @Assert: A repository is created with a Docker image and that its name
        can be updated.

        @Feature: Docker

        """
        with Session(self.browser) as session:
            name = gen_string('alphanumeric')
            product = entities.Product(
                organization=self.organization).create()
            _create_repository(
                session,
                org=self.organization.name,
                name=name,
                product=product.name,
            )
            self.assertIsNotNone(self.repository.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.repository.update(name, new_name=new_name)
                    self.navigator.go_to_products()
                    self.products.search(product.name).click()
                    self.assertIsNotNone(self.repository.search(new_name))
                    name = new_name

    @run_only_on('sat')
    def test_update_docker_repo_upstream_name(self):
        """@Test: Create a Docker-type repository and update its upstream name.

        @Assert: A repository is created with a Docker image and that its
        upstream name can be updated.

        @Feature: Docker

        """
        with Session(self.browser) as session:
            repo_name = gen_string('alphanumeric')
            product = entities.Product(organization=self.organization).create()
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.assertTrue(self.repository.validate_field(
                repo_name, 'upstream', 'busybox'))
            for new_upstream_name in VALID_DOCKER_UPSTREAM_NAMES:
                with self.subTest(new_upstream_name):
                    self.navigator.go_to_products()
                    self.products.search(product.name).click()
                    self.repository.update(
                        repo_name, new_upstream_name=new_upstream_name)
                    self.navigator.go_to_products()
                    self.products.search(product.name).click()
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'upstream', new_upstream_name))

    @run_only_on('sat')
    def test_update_docker_repo_url(self):
        """@Test: Create a Docker-type repository and update its URL.

        @Assert: A repository is created with a Docker image and that its URL
        can be updated.

        @Feature: Docker

        """
        with Session(self.browser) as session:
            name = gen_string('alphanumeric')
            new_url = gen_url()
            product = entities.Product(
                organization=self.organization).create()
            _create_repository(
                session,
                org=self.organization.name,
                name=name,
                product=product.name,
            )
            self.assertIsNotNone(self.repository.search(name))
            self.assertTrue(self.repository.validate_field(
                name, 'url', DOCKER_REGISTRY_HUB))
            self.navigator.go_to_products()
            self.products.search(product.name).click()
            self.repository.update(name, new_url=new_url)
            self.navigator.go_to_products()
            self.products.search(product.name).click()
            self.assertTrue(self.repository.validate_field(
                name, 'url', new_url))

    @run_only_on('sat')
    def test_delete_docker_repo(self):
        """@Test: Create and delete a Docker-type repository

        @Assert: A repository is created with a Docker image and then deleted.

        @Feature: Docker

        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    product = entities.Product(
                        organization=self.organization
                    ).create()
                    _create_repository(
                        session,
                        org=self.organization.name,
                        name=name,
                        product=product.name,
                    )
                    self.assertIsNotNone(self.repository.search(name))
                    self.repository.delete(name)
                    self.assertIsNone(self.repository.search(name))

    @run_only_on('sat')
    def test_delete_random_docker_repo(self):
        """@Test: Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        @Assert: Random repository can be deleted from random product without
        altering the other products.

        @Feature: Docker

        """
        entities_list = []
        products = [
            entities.Product(organization=self.organization).create()
            for _
            in range(randint(2, 5))
        ]
        with Session(self.browser) as session:
            for product in products:
                repo_name = gen_string('alphanumeric')
                _create_repository(
                    session,
                    org=self.organization.name,
                    name=repo_name,
                    product=product.name,
                )
                self.assertIsNotNone(self.repository.search(repo_name))
                entities_list.append([product.name, repo_name])

            # Delete a random repository
            shuffle(entities_list)
            del_entity = entities_list.pop()
            self.navigator.go_to_products()
            self.products.search(del_entity[0]).click()
            self.repository.delete(del_entity[1])
            self.assertIsNone(self.repository.search(del_entity[1]))

            # Check if others repositories are not touched
            for product_name, repo_name in entities_list:
                self.navigator.go_to_products()
                self.products.search(product_name).click()
                self.assertIsNotNone(self.repository.search(repo_name))


class DockerContentViewTestCase(UITestCase):
    """Tests specific to using ``Docker`` repositories with Content Views."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(DockerContentViewTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    def setUp(self):
        """Create new product per each test"""
        super(DockerContentViewTestCase, self).setUp()
        self.product = entities.Product(
            organization=self.organization).create()

    @run_only_on('sat')
    def test_add_docker_repo_to_content_view(self):
        """@Test: Add one Docker-type repository to a non-composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a non-composite content view

        @Feature: Docker

        """
        repo_name = gen_string('alphanumeric')
        content_view = entities.ContentView(
            composite=False,
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')

    @run_only_on('sat')
    def test_add_multiple_docker_repos_to_content_view(self):
        """@Test: Add multiple Docker-type repositories to a non-composite
        content view.

        @Assert: Repositories are created with Docker images and the product is
        added to a non-composite content view.

        @Feature: Docker

        """
        repos = []
        content_view = entities.ContentView(
            composite=False,
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            for _ in range(randint(2, 3)):
                repo_name = gen_string('alphanumeric')
                _create_repository(
                    session,
                    org=self.organization.name,
                    name=repo_name,
                    product=self.product.name,
                )
                self.assertIsNotNone(self.repository.search(repo_name))
                repos.append(repo_name)
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, repos, repo_type='docker')

    @run_only_on('sat')
    def test_add_synced_docker_repo_to_content_view(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository and it is
        synchronized.

        @Feature: Docker

        """
        repo_name = gen_string('alphanumeric')
        content_view = entities.ContentView(
            composite=False,
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_sync_status()
            synced = self.sync.sync_custom_repos(
                self.product.name, [repo_name])
            self.assertTrue(synced)
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')

    @run_only_on('sat')
    def test_add_docker_repo_to_composite_content_view(self):
        """@Test: Add one Docker-type repository to a composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a content view which is then added to a composite
        content view.

        @Feature: Docker

        """
        repo_name = gen_string('alphanumeric')
        content_view = entities.ContentView(
            composite=False,
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
            self.navigator.go_to_content_views()
            self.content_views.add_remove_cv(
                composite_name, [content_view.name])

    @run_only_on('sat')
    def test_add_multiple_docker_repos_to_composite_content_view(self):
        """@Test: Add multiple Docker-type repositories to a composite content
        view.

        @Assert: One repository is created with a Docker image and the product
        is added to a random number of content views which are then added to a
        composite content view.

        @Feature: Docker

        """
        cvs = []
        with Session(self.browser) as session:
            for _ in range(randint(2, 3)):
                repo_name = gen_string('alphanumeric')
                _create_repository(
                    session,
                    org=self.organization.name,
                    name=repo_name,
                    product=self.product.name,
                )
                self.assertIsNotNone(self.repository.search(repo_name))
                content_view = entities.ContentView(
                    composite=False,
                    organization=self.organization,
                ).create()
                self.navigator.go_to_content_views()
                self.content_views.add_remove_repos(
                    content_view.name, [repo_name], repo_type='docker')
                self.content_views.publish(content_view.name)
                cvs.append(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
            self.navigator.go_to_content_views()
            self.content_views.add_remove_cv(composite_name, cvs)

    @run_only_on('sat')
    def test_publish_once_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it
        once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once.

        @Feature: Docker

        """
        with Session(self.browser) as session:
            for repo_name in valid_data_list():
                with self.subTest(repo_name):
                    content_view = entities.ContentView(
                        composite=False,
                        organization=self.organization,
                    ).create()
                    _create_repository(
                        session,
                        org=self.organization.name,
                        name=repo_name,
                        product=self.product.name,
                    )
                    self.assertIsNotNone(self.repository.search(repo_name))
                    self.navigator.go_to_content_views()
                    self.content_views.add_remove_repos(
                        content_view.name, [repo_name], repo_type='docker')
                    self.content_views.publish(content_view.name)
                    self.assertIsNotNone(self.content_views.wait_until_element(
                        common_locators['alert.success']))

    @run_only_on('sat')
    def test_publish_once_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite content view and
        publish it once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once and then
        added to a composite content view which is also published only once.

        @Feature: Docker

        """
        repo_name = gen_string('alphanumeric')
        content_view = entities.ContentView(
            composite=False,
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
            self.navigator.go_to_content_views()
            self.content_views.add_remove_cv(
                composite_name, [content_view.name])
            self.content_views.publish(composite_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    def test_publish_multiple_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it
        multiple times.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published multiple times.

        @Feature: Docker

        """
        repo_name = gen_string('utf8')
        with Session(self.browser) as session:
            content_view = entities.ContentView(
                composite=False,
                organization=self.organization,
            ).create()
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            for _ in range(randint(2, 5)):
                self.content_views.publish(content_view.name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    def test_publish_multiple_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it
        multiple times.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then added to a composite content
        view which is then published multiple times.

        @Feature: Docker

        """
        repo_name = gen_string('alphanumeric')
        content_view = entities.ContentView(
            composite=False,
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
            self.navigator.go_to_content_views()
            self.content_views.add_remove_cv(
                composite_name, [content_view.name])
            for _ in range(randint(2, 5)):
                self.content_views.publish(composite_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    def test_promote_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then promote it to the next available lifecycle-environment.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environment.

        @Feature: Docker

        """
        repo_name = gen_string('utf8')
        lce = entities.LifecycleEnvironment(
            organization=self.organization).create()
        with Session(self.browser) as session:
            content_view = entities.ContentView(
                composite=False,
                organization=self.organization,
            ).create()
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))
            self.content_views.promote(
                content_view.name, 'Version 1', lce.name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    def test_promote_multiple_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then promote it to multiple available lifecycle-environments.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.

        @Feature: Docker

        """
        repo_name = gen_string('utf8')
        with Session(self.browser) as session:
            content_view = entities.ContentView(
                composite=False,
                organization=self.organization,
            ).create()
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))
            for _ in range(randint(2, 5)):
                lce = entities.LifecycleEnvironment(
                    organization=self.organization).create()
                self.content_views.promote(
                    content_view.name, 'Version 1', lce.name)
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']))

    @run_only_on('sat')
    def test_promote_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite content view and
        publish it. Then promote it to the next available
        lifecycle-environment.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environment.

        @Feature: Docker

        """
        repo_name = gen_string('alphanumeric')
        lce = entities.LifecycleEnvironment(
            organization=self.organization).create()
        content_view = entities.ContentView(
            composite=False,
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
            self.navigator.go_to_content_views()
            self.content_views.add_remove_cv(
                composite_name, [content_view.name])
            self.content_views.publish(composite_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))
            self.content_views.promote(composite_name, 'Version 1', lce.name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    def test_promote_multiple_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite content view and
        publish it. Then promote it to the multiple available
        lifecycle-environments.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.

        @Feature: Docker

        """
        repo_name = gen_string('alphanumeric')
        content_view = entities.ContentView(
            composite=False,
            organization=self.organization,
        ).create()
        with Session(self.browser) as session:
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=self.product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))
            self.navigator.go_to_content_views()
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
            self.navigator.go_to_content_views()
            self.content_views.add_remove_cv(
                composite_name, [content_view.name])
            self.content_views.publish(composite_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))
            for _ in range(randint(2, 5)):
                lce = entities.LifecycleEnvironment(
                    organization=self.organization).create()
                self.content_views.promote(
                    composite_name, 'Version 1', lce.name)
                self.assertIsNotNone(self.content_views.wait_until_element(
                    common_locators['alert.success']))


class DockerActivationKeyTestCase(UITestCase):
    """Tests specific to adding ``Docker`` repositories to Activation Keys."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerActivationKeyTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.lce = entities.LifecycleEnvironment(
            organization=cls.organization).create()
        cls.repo = entities.Repository(
            content_type=u'docker',
            docker_upstream_name=u'busybox',
            product=entities.Product(organization=cls.organization).create(),
            url=DOCKER_REGISTRY_HUB,
        ).create()
        content_view = entities.ContentView(
            composite=False,
            organization=cls.organization,
        ).create()
        content_view.repository = [cls.repo]
        cls.content_view = content_view.update(['repository'])
        cls.content_view.publish()
        cls.cvv = content_view.read().version[0].read()
        promote(cls.cvv, cls.lce.id)

    @run_only_on('sat')
    def test_add_docker_repo_to_activation_key(self):
        """@Test:Add Docker-type repository to a non-composite content view and
        publish it. Then create an activation key and associate it with the
        Docker content view.

        @Assert: Docker-based content view can be added to activation key

        @Feature: Docker

        """
        ak_name = gen_string('utf8')
        with Session(self.browser) as session:
            make_activationkey(
                session,
                org=self.organization.name,
                name=ak_name,
                env=self.lce.name,
                content_view=self.content_view.name,
            )
            self.assertIsNotNone(self.activationkey.search_key(ak_name))

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

    @run_only_on('sat')
    def test_add_docker_repo_composite_view_to_activation_key(self):
        """@Test:Add Docker-type repository to a non-composite content view and
        publish it. Then add this content view to a composite content view and
        publish it. Create an activation key and associate it with the
        composite Docker content view.

        @Assert: Docker-based content view can be added to activation key

        @Feature: Docker

        """
        ak_name = gen_string('utf8')
        composite_name = gen_string('utf8')
        with Session(self.browser) as session:
            self.navigator.go_to_select_org(self.organization.name)
            self.navigator.go_to_content_views()
            self.content_views.create(composite_name, is_composite=True)
            self.navigator.go_to_content_views()
            self.content_views.add_remove_cv(
                composite_name, [self.content_view.name])
            self.content_views.publish(composite_name)
            self.content_views.promote(
                composite_name, 'Version 1', self.lce.name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))
            make_activationkey(
                session,
                org=self.organization.name,
                name=ak_name,
                env=self.lce.name,
                content_view=composite_name,
            )
            self.assertIsNotNone(self.activationkey.search_key(ak_name))

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


class DockerComputeResourceTestCase(UITestCase):
    """Tests specific to managing Docker-based Compute Resources."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerComputeResourceTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @run_only_on('sat')
    def test_create_internal_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the Satellite 6
        instance.

        @Assert: Compute Resource can be created and listed.

        @Feature: Docker

        """
        with Session(self.browser) as session:
            for comp_name in valid_data_list():
                with self.subTest(comp_name):
                    make_resource(
                        session,
                        name=comp_name,
                        provider_type=FOREMAN_PROVIDERS['docker'],
                        parameter_list=[['URL', INTERNAL_DOCKER_URL, 'field']],
                    )
                    self.assertIsNotNone(
                        self.compute_resource.search(comp_name))

    @run_only_on('sat')
    def test_update_internal_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the Satellite 6
        instance then edit its attributes.

        @Assert: Compute Resource can be created, listed and its attributes can
        be updated.

        @Feature: Docker

        """
        comp_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=comp_name,
                provider_type=FOREMAN_PROVIDERS['docker'],
                parameter_list=[['URL', INTERNAL_DOCKER_URL, 'field']],
            )
            self.compute_resource.update(
                name=comp_name,
                parameter_list=[['URL', gen_url(), 'field']],
            )
            self.assertIsNotNone(self.compute_resource.wait_until_element(
                common_locators['notif.success']))

    @stubbed()
    @run_only_on('sat')
    def test_list_containers_internal_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the Satellite 6
        instance then list its running containers.

        @Assert: Compute Resource can be created, listed and existing running
        instances can be listed.

        @Feature: Docker

        @Status: Manual

        """

    @run_only_on('sat')
    def test_create_external_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource using an external
        Docker-enabled system.

        @Assert: Compute Resource can be created and listed.

        @Feature: Docker

        """
        with Session(self.browser) as session:
            for comp_name in valid_data_list():
                with self.subTest(comp_name):
                    make_resource(
                        session,
                        name=comp_name,
                        provider_type=FOREMAN_PROVIDERS['docker'],
                        parameter_list=[['URL', EXTERNAL_DOCKER_URL, 'field']],
                    )
                    self.assertIsNotNone(
                        self.compute_resource.search(comp_name))

    @run_only_on('sat')
    def test_update_external_docker_compute_resource(self):
        """@Test:@Test: Create a Docker-based Compute Resource using an
        external Docker-enabled system then edit its attributes.

        @Assert: Compute Resource can be created, listed and its
        attributes can be updated.

        @Feature: Docker

        """
        comp_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=comp_name,
                provider_type=FOREMAN_PROVIDERS['docker'],
                parameter_list=[['URL', EXTERNAL_DOCKER_URL, 'field']],
            )
            self.compute_resource.update(
                name=comp_name,
                parameter_list=[['Username', gen_string('alpha'), 'field'],
                                ['Password', gen_string('alpha'), 'field']],
            )
            self.assertIsNotNone(self.compute_resource.wait_until_element(
                common_locators['notif.success']))

    @stubbed()
    @run_only_on('sat')
    def test_list_containers_external_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource using an external
        Docker-enabled system then list its running containers.

        @Assert: Compute Resource can be created, listed and existing
        running instances can be listed.

        @Feature: Docker

        @Status: Manual

        """

    @run_only_on('sat')
    def test_delete_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource then delete it.

        @Assert: Compute Resource can be created, listed and deleted.

        @Feature: Docker

        """
        comp_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            for url in (EXTERNAL_DOCKER_URL, INTERNAL_DOCKER_URL):
                with self.subTest(url):
                    make_resource(
                        session,
                        name=comp_name,
                        provider_type=FOREMAN_PROVIDERS['docker'],
                        parameter_list=[['URL', url, 'field']],
                    )
                    self.assertIsNotNone(
                        self.compute_resource.search(comp_name))
                    self.compute_resource.delete(comp_name)


class DockerContainersTestCase(UITestCase):
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


class DockerRegistriesTestCase(UITestCase):
    """Tests specific to performing CRUD methods against ``Registries``
    repositories.

    """

    @run_only_on('sat')
    def test_create_registry(self):
        """@Test: Create an external docker registry

        @Feature: Docker

        @Assert: the external registry is created

        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_registry(
                        session,
                        name=name,
                        url=gen_url(subdomain=gen_string('alpha')),
                        description=gen_string('utf8'),
                    )
                    self.assertIsNotNone(self.registry.search(name))

    @run_only_on('sat')
    def test_update_registry_name(self):
        """@Test: Create an external docker registry and update its name

        @Feature: Docker

        @Assert: the external registry is updated with the new name

        """
        with Session(self.browser) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=gen_url(subdomain=gen_string('alpha')),
                description=gen_string('utf8'),
            )
            self.assertIsNotNone(self.registry.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.registry.update(name, new_name=new_name)
                    self.assertIsNotNone(self.registry.search(new_name))
                    name = new_name

    @run_only_on('sat')
    def test_update_registry_url(self):
        """@Test: Create an external docker registry and update its URL

        @Feature: Docker

        @Assert: the external registry is updated with the new URL

        """
        with Session(self.browser) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=gen_url(subdomain=gen_string('alpha')),
            )
            self.assertIsNotNone(self.registry.search(name))

            new_url = gen_url(subdomain=gen_string('alpha'))
            self.registry.update(name, new_url=new_url)
            self.registry.search(name).click()
            self.assertIsNotNone(self.registry.wait_until_element(
                locators['registry.url']).text, new_url)

    @run_only_on('sat')
    def test_update_registry_description(self):
        """@Test: Create an external docker registry and update its description

        @Feature: Docker

        @Assert: the external registry is updated with the new description

        """
        with Session(self.browser) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=gen_url(subdomain=gen_string('alpha')),
                description=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(self.registry.search(name))

            new_description = gen_string('utf8')
            self.registry.update(name, new_desc=new_description)
            self.registry.search(name).click()
            self.assertIsNotNone(self.registry.wait_until_element(
                locators['registry.description']).text, new_description)

    @run_only_on('sat')
    def test_update_registry_username(self):
        """@Test: Create an external docker registry and update its username

        @Feature: Docker

        @Assert: the external registry is updated with the new username

        """
        with Session(self.browser) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=gen_url(subdomain=gen_string('alpha')),
                username=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(self.registry.search(name))

            new_username = gen_string('utf8')
            self.registry.update(name, new_username=new_username)
            self.registry.search(name).click()
            self.assertIsNotNone(self.registry.wait_until_element(
                locators['registry.username']).text, new_username)

    @run_only_on('sat')
    def test_delete_registry(self):
        """@Test: Create an external docker registry and then delete it

        @Feature: Docker

        @Assert: The external registry is deleted successfully

        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_registry(
                        session,
                        name=name,
                        url=gen_url(subdomain=gen_string('alpha')),
                        description=gen_string('utf8'),
                    )
                    self.registry.delete(name)
