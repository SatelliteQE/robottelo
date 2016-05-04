"""WebUI tests for the Docker feature."""

from fauxfactory import gen_string, gen_url
from nailgun import entities
from random import randint, shuffle
from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import (
    DOCKER_0_EXTERNAL_REGISTRY,
    DOCKER_1_EXTERNAL_REGISTRY,
    DOCKER_REGISTRY_HUB,
    FOREMAN_PROVIDERS,
    REPO_TYPE,
)
from robottelo.datafactory import valid_data_list
from robottelo.decorators import (
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
)
from robottelo.helpers import install_katello_ca, remove_katello_ca
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_activationkey,
    make_container,
    make_registry,
    make_repository,
    make_resource,
    set_context,
)
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.products import Products
from robottelo.ui.session import Session

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
    :param str upstream_name: A valid name for an existing upstream repository.
        If ``None`` then defaults to ``busybox``.

    """
    if upstream_name is None:
        upstream_name = u'busybox'
    set_context(session, org=org)
    Products(session.browser).search(product).click()
    make_repository(
        session,
        name=name,
        repo_type=REPO_TYPE['docker'],
        url=DOCKER_REGISTRY_HUB,
        upstream_repo_name=upstream_name,
    )


class DockerTagTestCase(UITestCase):
    """Tests related to Content > Docker Tags page"""

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_search_docker_image(self):
        """Search for a docker image

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
    @tier1
    def test_positive_create_with_name(self):
        """Create one Docker-type repository using different names

        @Feature: Docker

        @Assert: A repository is created with a Docker upstream repository.
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
    @tier1
    def test_positive_create_repos_using_same_product(self):
        """Create multiple Docker-type repositories

        @Feature: Docker

        @Assert: Multiple docker repositories are created with a Docker
        upstream repository and they all belong to the same product.
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
                self.products.search(product.name).click()
                self.assertIsNotNone(self.repository.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_repos_using_multiple_products(self):
        """Create multiple Docker-type repositories on multiple products.

        @Feature: Docker

        @Assert: Multiple docker repositories are created with a Docker
        upstream repository and they all belong to their respective products.
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
                    self.products.search(pr.name).click()
                    self.assertIsNotNone(self.repository.search(name))

    @run_only_on('sat')
    @tier2
    def test_positive_sync(self):
        """Create and sync a Docker-type repository

        @Feature: Docker

        @Assert: A repository is created with a Docker repository and it is
        synchronized.
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
    @tier1
    def test_positive_update_name(self):
        """Create a Docker-type repository and update its name.

        @Feature: Docker

        @Assert: A repository is created with a Docker upstream repository and
        that its name can be updated.
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
                    self.products.search(product.name).click()
                    self.assertIsNotNone(self.repository.search(new_name))
                    name = new_name

    @run_only_on('sat')
    @tier1
    def test_positive_update_upstream_name(self):
        """Create a Docker-type repository and update its upstream name.

        @Feature: Docker

        @Assert: A repository is created with a Docker upstream repository and
        that its upstream name can be updated.
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
                    self.products.search(product.name).click()
                    self.repository.update(
                        repo_name, new_upstream_name=new_upstream_name)
                    self.products.search(product.name).click()
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'upstream', new_upstream_name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_url(self):
        """Create a Docker-type repository and update its URL.

        @Feature: Docker

        @Assert: A repository is created with a Docker upstream repository and
        that its URL can be updated.
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
            self.products.search(product.name).click()
            self.repository.update(name, new_url=new_url)
            self.products.search(product.name).click()
            self.assertTrue(self.repository.validate_field(
                name, 'url', new_url))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create and delete a Docker-type repository

        @Feature: Docker

        @Assert: A repository is created with a Docker upstream repository and
        then deleted.
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
    @tier2
    def test_positive_delete_random_repo(self):
        """Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        @Feature: Docker

        @Assert: Random repository can be deleted from random product without
        altering the other products.
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
    @tier2
    def test_positive_add_docker_repo(self):
        """Add one Docker-type repository to a non-composite content view

        @Feature: Docker

        @Assert: A repository is created with a Docker repository and the
        product is added to a non-composite content view
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
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')

    @run_only_on('sat')
    @tier2
    def test_positive_add_docker_repos(self):
        """Add multiple Docker-type repositories to a non-composite
        content view.

        @Feature: Docker

        @Assert: Repositories are created with Docker upstream repositories and
        the product is added to a non-composite content view.
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
            self.content_views.add_remove_repos(
                content_view.name, repos, repo_type='docker')

    @run_only_on('sat')
    @tier2
    def test_positive_add_synced_docker_repo(self):
        """Create and sync a Docker-type repository

        @Feature: Docker

        @Assert: A repository is created with a Docker repository and it is
        synchronized.
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
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')

    @run_only_on('sat')
    @tier2
    def test_positive_add_docker_repo_to_ccv(self):
        """Add one Docker-type repository to a composite content view

        @Feature: Docker

        @Assert: A repository is created with a Docker repository and the
        product is added to a content view which is then added to a composite
        content view.
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
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
            self.content_views.add_remove_cv(
                composite_name, [content_view.name])

    @run_only_on('sat')
    @tier2
    def test_positive_add_docker_repos_to_ccv(self):
        """Add multiple Docker-type repositories to a composite content
        view.

        @Feature: Docker

        @Assert: One repository is created with a Docker upstream repository
        and the product is added to a random number of content views which are
        then added to a composite content view.
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
            self.content_views.add_remove_cv(composite_name, cvs)

    @run_only_on('sat')
    @tier2
    def test_positive_publish_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it
        once.

        @Feature: Docker

        @Assert: One repository is created with a Docker upstream repository
        and the product is added to a content view which is then published only
        once.
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
                    self.content_views.add_remove_repos(
                        content_view.name, [repo_name], repo_type='docker')
                    self.content_views.publish(content_view.name)
                    self.assertIsNotNone(self.content_views.wait_until_element(
                        common_locators['alert.success']))

    @run_only_on('sat')
    @tier2
    def test_positive_publish_with_docker_repo_composite(self):
        """Add Docker-type repository to composite content view and
        publish it once.

        @Feature: Docker

        @Assert: One repository is created with a Docker upstream repository
        and the product is added to a content view which is then published only
        once and then added to a composite content view which is also published
        only once.
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
            self.content_views.add_remove_cv(
                composite_name, [content_view.name])
            self.content_views.publish(composite_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    @tier2
    def test_positive_publish_multiple_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it
        multiple times.

        @Feature: Docker

        @Assert: One repository is created with a Docker upstream repository
        and the product is added to a content view which is then published
        multiple times.
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
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            for _ in range(randint(2, 5)):
                self.content_views.publish(content_view.name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    @tier2
    def test_positive_publish_multiple_with_docker_repo_composite(self):
        """Add Docker-type repository to content view and publish it
        multiple times.

        @Assert: One repository is created with a Docker upstream repository
        and the product is added to a content view which is then added to a
        composite content view which is then published multiple times.

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
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
            self.content_views.add_remove_cv(
                composite_name, [content_view.name])
            for _ in range(randint(2, 5)):
                self.content_views.publish(composite_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    @tier2
    def test_positive_promote_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it.
        Then promote it to the next available lifecycle-environment.

        @Feature: Docker

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environment.
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
    @tier2
    def test_positive_promote_multiple_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it.
        Then promote it to multiple available lifecycle-environments.

        @Feature: Docker

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.
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
    @tier2
    def test_positive_promote_with_docker_repo_composite(self):
        """Add Docker-type repository to composite content view and
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
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
            self.content_views.add_remove_cv(
                composite_name, [content_view.name])
            self.content_views.publish(composite_name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))
            self.content_views.promote(composite_name, 'Version 1', lce.name)
            self.assertIsNotNone(self.content_views.wait_until_element(
                common_locators['alert.success']))

    @run_only_on('sat')
    @tier2
    def test_positive_promote_multiple_with_docker_repo_composite(self):
        """Add Docker-type repository to composite content view and
        publish it. Then promote it to the multiple available
        lifecycle-environments.

        @Feature: Docker

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.
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
            self.content_views.add_remove_repos(
                content_view.name, [repo_name], repo_type='docker')
            self.content_views.publish(content_view.name)

            composite_name = gen_string('alpha')
            self.content_views.create(composite_name, is_composite=True)
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
    @tier2
    def test_positive_add_docker_repo_cv(self):
        """Add Docker-type repository to a non-composite content view and
        publish it. Then create an activation key and associate it with the
        Docker content view.

        @Feature: Docker

        @Assert: Docker-based content view can be added to activation key
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
            self.assertIsNotNone(self.activationkey.search(ak_name))

    @stubbed()
    # Return to that case once BZ 1269829 is fixed
    @run_only_on('sat')
    @tier2
    def test_positive_remove_docker_repo_cv(self):
        """Add Docker-type repository to a non-composite content view and
        publish it. Create an activation key and associate it with the Docker
        content view. Then remove this content view from the activation key.

        @Feature: Docker

        @Assert: Docker-based content view can be added and then removed
        from the activation key.

        @Status: Manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_add_docker_repo_ccv(self):
        """Add Docker-type repository to a non-composite content view and
        publish it. Then add this content view to a composite content view and
        publish it. Create an activation key and associate it with the
        composite Docker content view.

        @Feature: Docker

        @Assert: Docker-based content view can be added to activation key
        """
        ak_name = gen_string('utf8')
        composite_name = gen_string('utf8')
        with Session(self.browser) as session:
            self.navigator.go_to_select_org(self.organization.name)
            self.navigator.go_to_content_views()
            self.content_views.create(composite_name, is_composite=True)
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
            self.assertIsNotNone(self.activationkey.search(ak_name))

    @stubbed()
    # Return to that case once BZ 1269829 is fixed
    @run_only_on('sat')
    @tier2
    def test_positive_remove_docker_repo_ccv(self):
        """Add Docker-type repository to a non-composite content view and
        publish it. Then add this content view to a composite content view and
        publish it. Create an activation key and associate it with the
        composite Docker content view. Then, remove the composite content view
        from the activation key.

        @Feature: Docker

        @Assert: Docker-based composite content view can be added and then
        removed from the activation key.

        @Status: Manual
        """


class DockerComputeResourceTestCase(UITestCase):
    """Tests specific to managing Docker-based Compute Resources."""

    @classmethod
    @skip_if_not_set('docker')
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerComputeResourceTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_create_internal(self):
        """Create a Docker-based Compute Resource in the Satellite 6
        instance.

        @Feature: Docker

        @Assert: Compute Resource can be created and listed.
        """
        with Session(self.browser) as session:
            for comp_name in valid_data_list():
                with self.subTest(comp_name):
                    make_resource(
                        session,
                        name=comp_name,
                        provider_type=FOREMAN_PROVIDERS['docker'],
                        parameter_list=[[
                            'URL',
                            settings.docker.get_unix_socket_url(),
                            'field'
                        ]],
                    )
                    self.assertIsNotNone(
                        self.compute_resource.search(comp_name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_internal(self):
        """Create a Docker-based Compute Resource in the Satellite 6
        instance then edit its attributes.

        @Feature: Docker

        @Assert: Compute Resource can be created, listed and its attributes can
        be updated.
        """
        comp_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=comp_name,
                provider_type=FOREMAN_PROVIDERS['docker'],
                parameter_list=[[
                    'URL',
                    settings.docker.get_unix_socket_url(),
                    'field'
                ]],
            )
            self.compute_resource.update(
                name=comp_name,
                parameter_list=[['URL', gen_url(), 'field']],
            )
            self.assertIsNotNone(self.compute_resource.wait_until_element(
                common_locators['notif.success']))

    @stubbed()
    @tier2
    def test_positive_list_containers_internal(self):
        """Create a Docker-based Compute Resource in the Satellite 6
        instance then list its running containers.

        @Assert: Compute Resource can be created, listed and existing running
        instances can be listed.

        @Feature: Docker

        @Status: Manual

        """

    @run_only_on('sat')
    @tier1
    def test_positive_create_external(self):
        """Create a Docker-based Compute Resource using an external
        Docker-enabled system.

        @Feature: Docker

        @Assert: Compute Resource can be created and listed.
        """
        with Session(self.browser) as session:
            for comp_name in valid_data_list():
                with self.subTest(comp_name):
                    make_resource(
                        session,
                        name=comp_name,
                        provider_type=FOREMAN_PROVIDERS['docker'],
                        parameter_list=[[
                            'URL',
                            settings.docker.external_url,
                            'field'
                        ]],
                    )
                    self.assertIsNotNone(
                        self.compute_resource.search(comp_name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_external(self):
        """Create a Docker-based Compute Resource using an external
        Docker-enabled system then edit its attributes.

        @Feature: Docker

        @Assert: Compute Resource can be created, listed and its
        attributes can be updated.
        """
        comp_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_resource(
                session,
                name=comp_name,
                provider_type=FOREMAN_PROVIDERS['docker'],
                parameter_list=[[
                    'URL',
                    settings.docker.external_url,
                    'field'
                ]],
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
    @tier2
    def test_positive_list_containers_external(self):
        """Create a Docker-based Compute Resource using an external
        Docker-enabled system then list its running containers.

        @Feature: Docker

        @Assert: Compute Resource can be created, listed and existing
        running instances can be listed.

        @Status: Manual
        """

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create a Docker-based Compute Resource then delete it.

        @Feature: Docker

        @Assert: Compute Resource can be created, listed and deleted.
        """
        comp_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            for url in (settings.docker.external_url,
                        settings.docker.get_unix_socket_url()):
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


class DockerContainerTestCase(UITestCase):
    """Tests specific to using ``Containers`` in local and external Docker
    Compute Resources

    """

    @classmethod
    @skip_if_not_set('docker')
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerContainerTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.lce = entities.LifecycleEnvironment(
            organization=cls.organization).create()
        cls.repo = entities.Repository(
            content_type=u'docker',
            docker_upstream_name=u'busybox',
            product=entities.Product(organization=cls.organization).create(),
            url=DOCKER_REGISTRY_HUB,
        ).create()
        cls.repo.sync()
        content_view = entities.ContentView(
            composite=False,
            organization=cls.organization,
        ).create()
        content_view.repository = [cls.repo]
        cls.content_view = content_view.update(['repository'])
        cls.content_view.publish()
        cls.cvv = content_view.read().version[0].read()
        promote(cls.cvv, cls.lce.id)
        cls.cr_internal = entities.DockerComputeResource(
            name=gen_string('alpha'),
            organization=[cls.organization],
            url=settings.docker.get_unix_socket_url(),
        ).create()
        cls.cr_external = entities.DockerComputeResource(
            name=gen_string('alpha'),
            organization=[cls.organization],
            url=settings.docker.external_url,
        ).create()
        cls.parameter_list = [
            {'main_tab_name': 'Image', 'sub_tab_name': 'Content View',
             'name': 'Lifecycle Environment', 'value': cls.lce.name},
            {'main_tab_name': 'Image', 'sub_tab_name': 'Content View',
             'name': 'Content View', 'value': cls.content_view.name},
            {'main_tab_name': 'Image', 'sub_tab_name': 'Content View',
             'name': 'Repository', 'value': cls.repo.name},
            {'main_tab_name': 'Image', 'sub_tab_name': 'Content View',
             'name': 'Tag', 'value': 'latest'},
        ]
        install_katello_ca()

    @classmethod
    def tearDownClass(cls):
        """Remove katello-ca certificate"""
        remove_katello_ca()
        super(DockerContainerTestCase, cls).tearDownClass()

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_compresource(self):
        """Create containers for local and external compute resources

        @Feature: Docker

        @Assert: The docker container is created for each compute resource
        """
        with Session(self.browser) as session:
            for compute_resource in (self.cr_internal, self.cr_external):
                with self.subTest(compute_resource):
                    make_container(
                        session,
                        org=self.organization.name,
                        resource_name=compute_resource.name + ' (Docker)',
                        name=gen_string('alphanumeric'),
                        parameter_list=self.parameter_list,
                    )

    @run_only_on('sat')
    @tier2
    def test_positive_power_on_off(self):
        """Create containers for local and external compute resource,
        then power them on and finally power them off

        @Feature: Docker

        @Assert: The docker container is created for each compute resource and
        the power status is showing properly
        """
        with Session(self.browser) as session:
            for compute_resource in (self.cr_internal, self.cr_external):
                with self.subTest(compute_resource):
                    name = gen_string('alphanumeric')
                    make_container(
                        session,
                        org=self.organization.name,
                        resource_name=compute_resource.name + ' (Docker)',
                        name=name,
                        parameter_list=self.parameter_list,
                    )
                    self.assertEqual(self.container.set_power_status(
                        compute_resource.name, name, True), u'On')
                    self.assertEqual(self.container.set_power_status(
                        compute_resource.name, name, False), u'Off')

    @stubbed()
    @run_only_on('sat')
    @tier2
    def test_positive_create_with_external_registry(self):
        """Create a container pulling an image from a custom external
        registry

        @Feature: Docker

        @Assert: The docker container is created and the image is pulled from
        the external registry

        @Status: Manual
        """

    @run_only_on('sat')
    @tier2
    def test_positive_delete(self):
        """Delete containers in local and external compute resources

        @Feature: Docker

        @Assert: The docker containers are deleted in local and external
        compute resources
        """
        with Session(self.browser) as session:
            for compute_resource in (self.cr_internal, self.cr_external):
                with self.subTest(compute_resource):
                    name = gen_string('alphanumeric')
                    make_container(
                        session,
                        org=self.organization.name,
                        resource_name=compute_resource.name + ' (Docker)',
                        name=name,
                        parameter_list=self.parameter_list,
                    )
                    self.container.delete(compute_resource.name, name)
                    self.assertIsNone(
                        self.container.search(compute_resource.name, name))

    # BZ 1266842 is a private bug, so we cannot fetch information about it
    @stubbed('Unstub when BZ1266842 is fixed')
    @run_only_on('sat')
    @tier2
    def test_positive_delete_using_api_call(self):
        """Create and delete containers using direct API calls and verify
        result of these operations through UI interface

        @Feature: Docker

        @Assert: The docker containers are deleted successfully and are not
        present on UI
        """
        for compute_resource in (self.cr_internal, self.cr_external):
            with self.subTest(compute_resource.url):
                # Create and delete docker container using API
                container = entities.DockerHubContainer(
                    command='top',
                    compute_resource=compute_resource,
                    organization=[self.organization],
                ).create()
                container.delete()
                # Check result of delete operation on UI
                with Session(self.browser) as session:
                    set_context(session, org=self.organization.name)
                    self.assertIsNone(self.container.search(
                        compute_resource.name, container.name))


class DockerRegistryTestCase(UITestCase):
    """Tests specific to performing CRUD methods against ``Registries``
    repositories.
    """

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create an external docker registry

        @Feature: Docker

        @Assert: the external registry is created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_registry(
                        session,
                        name=name,
                        url=DOCKER_0_EXTERNAL_REGISTRY,
                        description=gen_string('utf8'),
                    )
                    try:
                        self.assertIsNotNone(self.registry.search(name))
                    finally:
                        entities.Registry(name=name).search()[0].delete()

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Create an external docker registry and update its name

        @Feature: Docker

        @Assert: the external registry is updated with the new name
        """
        with Session(self.browser) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=DOCKER_0_EXTERNAL_REGISTRY,
                description=gen_string('utf8'),
            )
            try:
                registry_entity = entities.Registry(name=name).search()[0]
                self.assertIsNotNone(self.registry.search(name))
                for new_name in valid_data_list():
                    with self.subTest(new_name):
                        self.registry.update(name, new_name=new_name)
                        self.assertIsNotNone(self.registry.search(new_name))
                        name = new_name
            finally:
                registry_entity.delete()

    @run_only_on('sat')
    @tier1
    def test_positive_update_url(self):
        """Create an external docker registry and update its URL

        @Feature: Docker

        @Assert: the external registry is updated with the new URL
        """
        with Session(self.browser) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=DOCKER_0_EXTERNAL_REGISTRY,
            )
            try:
                registry_entity = entities.Registry(name=name).search()[0]
                self.assertIsNotNone(self.registry.search(name))
                new_url = DOCKER_1_EXTERNAL_REGISTRY
                self.registry.update(name, new_url=new_url)
                self.registry.search(name).click()
                self.assertIsNotNone(self.registry.wait_until_element(
                    locators['registry.url']).text, new_url)
            finally:
                registry_entity.delete()

    @run_only_on('sat')
    @tier1
    def test_positive_update_description(self):
        """Create an external docker registry and update its description

        @Feature: Docker

        @Assert: the external registry is updated with the new description
        """
        with Session(self.browser) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=DOCKER_0_EXTERNAL_REGISTRY,
                description=gen_string('alphanumeric'),
            )
            try:
                registry_entity = entities.Registry(name=name).search()[0]
                self.assertIsNotNone(self.registry.search(name))
                new_description = gen_string('utf8')
                self.registry.update(name, new_desc=new_description)
                self.registry.search(name).click()
                self.assertIsNotNone(self.registry.wait_until_element(
                    locators['registry.description']).text, new_description)
            finally:
                registry_entity.delete()

    @run_only_on('sat')
    @tier1
    def test_positive_update_username(self):
        """Create an external docker registry and update its username

        @Feature: Docker

        @Assert: the external registry is updated with the new username
        """
        with Session(self.browser) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=DOCKER_0_EXTERNAL_REGISTRY,
                username=gen_string('alphanumeric'),
            )
            try:
                registry_entity = entities.Registry(name=name).search()[0]
                self.assertIsNotNone(self.registry.search(name))
                new_username = gen_string('utf8')
                self.registry.update(name, new_username=new_username)
                self.registry.search(name).click()
                self.assertIsNotNone(self.registry.wait_until_element(
                    locators['registry.username']).text, new_username)
            finally:
                registry_entity.delete()

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create an external docker registry and then delete it

        @Feature: Docker

        @Assert: The external registry is deleted successfully
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_registry(
                        session,
                        name=name,
                        url=DOCKER_0_EXTERNAL_REGISTRY,
                        description=gen_string('utf8'),
                    )
                    self.registry.delete(name)
