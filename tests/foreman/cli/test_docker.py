# pylint: attribute-defined-outside-init
"""Unit tests for the Docker feature."""
from fauxfactory import gen_alpha, gen_choice, gen_string, gen_url
from random import choice, randint
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.docker import Docker
from robottelo.cli.factory import (
    make_activation_key,
    make_compute_resource,
    make_container,
    make_content_view,
    make_lifecycle_environment,
    make_org,
    make_product,
    make_registry,
    make_repository,
)
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.contentview import ContentView
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.config import settings
from robottelo.constants import DOCKER_REGISTRY_HUB
from robottelo.datafactory import valid_data_list
from robottelo.decorators import run_only_on, skip_if_bug_open, stubbed
from robottelo.helpers import install_katello_ca, remove_katello_ca
from robottelo.test import CLITestCase

STRING_TYPES = ['alpha', 'alphanumeric', 'cjk', 'utf8', 'latin1']

DOCKER_PROVIDER = 'Docker'
REPO_CONTENT_TYPE = 'docker'
REPO_UPSTREAM_NAME = 'busybox'


def _make_docker_repo(product_id, name=None, upstream_name=None):
    """Creates a Docker-based repository.

    :param product_id: ID of the ``Product``.
    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name for an existing Docker image.
        If ``None`` then defaults to ``busybox``.
    :return: A ``Repository`` object.

    """
    return make_repository({
        'content-type': REPO_CONTENT_TYPE,
        'docker-upstream-name': upstream_name or REPO_UPSTREAM_NAME,
        'name': name or gen_string(gen_choice(STRING_TYPES), 15),
        'product-id': product_id,
        'url': DOCKER_REGISTRY_HUB,
    })


class DockerImageTestCase(CLITestCase):
    """Tests related to docker image command"""

    def test_bugzilla_1190122(self):
        """@Test: docker image displays tags information for a docker image

        @Feature: Docker

        @Assert: docker image displays tags information for a docker image

        """
        organization = make_org()
        product = make_product({
            u'organization-id': organization['id'],
        })
        repository = make_repository({
            u'content-type': REPO_CONTENT_TYPE,
            u'docker-upstream-name': REPO_UPSTREAM_NAME,
            u'product-id': product['id'],
            u'url': DOCKER_REGISTRY_HUB,
        })
        Repository.synchronize({'id': repository['id']})
        # Grab all available images related to repository
        images_list = Docker.image.list({
            u'repository-id': repository['id'],
        })
        # Some images do not have tags associated with it, ignore those because
        # we want to check the tag information
        images = [
            image for image in images_list if int(image['tag-count']) > 0
        ]
        for image in images:
            result = Docker.image.info({'id': image['id']})
            # Extract the list of repository ids of the available image's tags
            tag_repository_ids = []
            for tag in result['tags']:
                tag_repository_ids.append(tag['repository-id'])
                self.assertGreater(len(tag['tag']), 0)
            self.assertIn(repository['id'], tag_repository_ids)


class DockerRepositoryTestCase(CLITestCase):
    """Tests specific to performing CRUD methods against ``Docker``
    repositories.

    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
        cls.org_id = make_org()['id']

    @run_only_on('sat')
    def test_create_one_docker_repo(self):
        """@Test: Create one Docker-type repository

        @Assert: A repository is created with a Docker image.

        @Feature: Docker

        """
        for name in valid_data_list():
            with self.subTest(name):
                repo = _make_docker_repo(
                    make_product({'organization-id': self.org_id})['id'],
                    name,
                )
                self.assertEqual(repo['name'], name)
                self.assertEqual(
                    repo['upstream-repository-name'], REPO_UPSTREAM_NAME)
                self.assertEqual(repo['content-type'], REPO_CONTENT_TYPE)

    @run_only_on('sat')
    def test_create_multiple_docker_repo(self):
        """@Test: Create multiple Docker-type repositories

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to the same product.

        @Feature: Docker

        """
        product = make_product({'organization-id': self.org_id})
        repo_names = set()
        for _ in range(randint(2, 5)):
            repo = _make_docker_repo(product['id'])
            repo_names.add(repo['name'])
        product = Product.info({
            'id': product['id'],
            'organization-id': self.org_id,
        })
        self.assertEqual(
            repo_names,
            set([repo_['repo-name'] for repo_ in product['content']]),
        )

    @run_only_on('sat')
    def test_create_multiple_docker_repo_multiple_products(self):
        """@Test: Create multiple Docker-type repositories on multiple
        products.

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to their respective products.

        @Feature: Docker

        """
        for _ in range(randint(2, 5)):
            product = make_product({'organization-id': self.org_id})
            repo_names = set()
            for _ in range(randint(2, 3)):
                repo = _make_docker_repo(product['id'])
                repo_names.add(repo['name'])
            product = Product.info({
                'id': product['id'],
                'organization-id': self.org_id,
            })
            self.assertEqual(
                repo_names,
                set([repo_['repo-name'] for repo_ in product['content']]),
            )

    @run_only_on('sat')
    def test_sync_docker_repo(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        """
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        self.assertEqual(int(repo['content-counts']['docker-images']), 0)
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertGreaterEqual(
            int(repo['content-counts']['docker-images']), 1)

    @run_only_on('sat')
    def test_update_docker_repo_name(self):
        """@Test: Create a Docker-type repository and update its name.

        @Assert: A repository is created with a Docker image and that its
        name can be updated.

        @Feature: Docker

        """
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        for new_name in valid_data_list():
            with self.subTest(new_name):
                Repository.update({
                    'id': repo['id'],
                    'new-name': new_name,
                    'url': repo['url'],
                })
                repo = Repository.info({'id': repo['id']})
                self.assertEqual(repo['name'], new_name)

    @run_only_on('sat')
    def test_update_docker_repo_upstream_name(self):
        """@Test: Create a Docker-type repository and update its upstream name.

        @Assert: A repository is created with a Docker image and that its
        upstream name can be updated.

        @Feature: Docker

        """
        new_upstream_name = 'fedora/ssh'
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        Repository.update({
            'docker-upstream-name': new_upstream_name,
            'id': repo['id'],
            'url': repo['url'],
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['upstream-repository-name'], new_upstream_name)

    @run_only_on('sat')
    def test_update_docker_repo_url(self):
        """@Test: Create a Docker-type repository and update its URL.

        @Assert: A repository is created with a Docker image and that its
        URL can be updated.

        @Feature: Docker

        """
        new_url = gen_url()
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        Repository.update({
            'id': repo['id'],
            'url': new_url,
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['url'], new_url)

    @run_only_on('sat')
    def test_delete_docker_repo(self):
        """@Test: Create and delete a Docker-type repository

        @Assert: A repository is created with a Docker image and then deleted.

        @Feature: Docker

        """
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        Repository.delete({'id': repo['id']})
        with self.assertRaises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})

    @run_only_on('sat')
    def test_delete_random_docker_repo(self):
        """@Test: Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        @Assert: Random repository can be deleted from random product without
        altering the other products.

        @Feature: Docker

        """
        products = [
            make_product({'organization-id': self.org_id})
            for _
            in range(randint(2, 5))
        ]
        repos = []
        for product in products:
            for _ in range(randint(2, 3)):
                repos.append(_make_docker_repo(product['id']))
        # Select random repository and delete it
        repo = choice(repos)
        repos.remove(repo)
        Repository.delete({'id': repo['id']})
        with self.assertRaises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})
        # Verify other repositories were not touched
        for repo in repos:
            result = Repository.info({'id': repo['id']})
            self.assertIn(
                result['product']['id'],
                [product['id'] for product in products],
            )


class DockerContentViewTestCase(CLITestCase):
    """Tests specific to using ``Docker`` repositories with Content Views."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(DockerContentViewTestCase, cls).setUpClass()
        cls.org_id = make_org()['id']

    @run_only_on('sat')
    def _create_and_associate_repo_with_cv(self):
        """Create a Docker-based repository and content view and associate
        them.

        """
        self.repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        self.content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        ContentView.add_repository({
            'id': self.content_view['id'],
            'repository-id': self.repo['id'],
        })
        self.content_view = ContentView.info({
            'id': self.content_view['id']
        })
        self.assertIn(
            self.repo['id'],
            [
                repo_['id']
                for repo_
                in self.content_view['docker-repositories']
            ],
        )

    @run_only_on('sat')
    def test_add_docker_repo_to_content_view(self):
        """@Test: Add one Docker-type repository to a non-composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a non-composite content view

        @Feature: Docker

        """
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertIn(
            repo['id'],
            [repo_['id'] for repo_ in content_view['docker-repositories']],
        )

    @run_only_on('sat')
    def test_add_multiple_docker_repos_to_content_view(self):
        """@Test: Add multiple Docker-type repositories to a
        non-composite content view.

        @Assert: Repositories are created with Docker images and the
        product is added to a non-composite content view.

        @Feature: Docker

        """
        product = make_product({'organization-id': self.org_id})
        repos = [
            _make_docker_repo(product['id'])
            for _
            in range(randint(2, 5))
        ]
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        for repo in repos:
            ContentView.add_repository({
                'id': content_view['id'],
                'repository-id': repo['id'],
            })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertEqual(
            set([repo['id'] for repo in repos]),
            set([repo['id'] for repo in content_view['docker-repositories']]),
        )

    @run_only_on('sat')
    def test_add_synced_docker_repo_to_content_view(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        """
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertGreaterEqual(
            int(repo['content-counts']['docker-images']), 1)
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        content_view = ContentView.info({'id': content_view['id']})
        self.assertIn(
            repo['id'],
            [repo_['id'] for repo_ in content_view['docker-repositories']],
        )

    @run_only_on('sat')
    def test_add_docker_repo_to_composite_content_view(self):
        """@Test: Add one Docker-type repository to a composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a content view which is then added to a composite
        content view.

        @Feature: Docker

        """
        self._create_and_associate_repo_with_cv()
        ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id']})
        self.assertEqual(len(self.content_view['versions']), 1)
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org_id,
        })
        ContentView.update({
            'id': comp_content_view['id'],
            'component-ids': self.content_view['versions'][0]['id'],
        })
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        self.assertIn(
            self.content_view['versions'][0]['id'],
            [component['id'] for component in comp_content_view['components']],
        )

    @run_only_on('sat')
    def test_add_multiple_docker_repos_to_composite_content_view(self):
        """@Test: Add multiple Docker-type repositories to a composite
        content view.

        @Assert: One repository is created with a Docker image and the
        product is added to a random number of content views which are then
        added to a composite content view.

        @Feature: Docker

        """
        cv_versions = []
        product = make_product({'organization-id': self.org_id})
        for _ in range(randint(2, 5)):
            content_view = make_content_view({
                'composite': False,
                'organization-id': self.org_id,
            })
            repo = _make_docker_repo(product['id'])
            ContentView.add_repository({
                'id': content_view['id'],
                'repository-id': repo['id'],
            })
            ContentView.publish({'id': content_view['id']})
            content_view = ContentView.info({'id': content_view['id']})
            self.assertEqual(len(content_view['versions']), 1)
            cv_versions.append(content_view['versions'][0])
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org_id,
        })
        ContentView.update({
            'component-ids': [cv_version['id'] for cv_version in cv_versions],
            'id': comp_content_view['id'],
        })
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        for cv_version in cv_versions:
            self.assertIn(
                cv_version['id'],
                [
                    component['id']
                    for component
                    in comp_content_view['components']
                ],
            )

    @run_only_on('sat')
    def test_publish_once_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish
        it once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once.

        @Feature: Docker

        """
        self._create_and_associate_repo_with_cv()
        self.assertEqual(len(self.content_view['versions']), 0)
        ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id'],
        })
        self.assertEqual(len(self.content_view['versions']), 1)

    @run_only_on('sat')
    def test_publish_once_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite
        content view and publish it once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once and then
        added to a composite content view which is also published only once.

        @Feature: Docker

        """
        self._create_and_associate_repo_with_cv()
        self.assertEqual(len(self.content_view['versions']), 0)
        ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id'],
        })
        self.assertEqual(len(self.content_view['versions']), 1)
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org_id,
        })
        ContentView.update({
            'component-ids': self.content_view['versions'][0]['id'],
            'id': comp_content_view['id'],
        })
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        self.assertIn(
            self.content_view['versions'][0]['id'],
            [
                component['id']
                for component
                in comp_content_view['components']
            ],
        )
        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        self.assertEqual(len(comp_content_view['versions']), 1)

    @run_only_on('sat')
    def test_publish_multiple_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it
        multiple times.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published multiple times.

        @Feature: Docker

        """
        self._create_and_associate_repo_with_cv()
        self.assertEqual(len(self.content_view['versions']), 0)
        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id'],
        })
        self.assertEqual(len(self.content_view['versions']), publish_amount)

    @run_only_on('sat')
    def test_publish_multiple_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it
        multiple times.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then added to a composite content
        view which is then published multiple times.

        @Feature: Docker

        """
        self._create_and_associate_repo_with_cv()
        self.assertEqual(len(self.content_view['versions']), 0)
        ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id']})
        self.assertEqual(len(self.content_view['versions']), 1)
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org_id,
        })
        ContentView.update({
            'component-ids': self.content_view['versions'][0]['id'],
            'id': comp_content_view['id'],
        })
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        self.assertIn(
            self.content_view['versions'][0]['id'],
            [
                component['id']
                for component
                in comp_content_view['components']
            ],
        )
        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        self.assertEqual(len(comp_content_view['versions']), publish_amount)

    @run_only_on('sat')
    def test_promote_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then promote it to the next available lifecycle-environment.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environment.

        @Feature: Docker

        """
        lce = make_lifecycle_environment({'organization-id': self.org_id})
        self._create_and_associate_repo_with_cv()
        ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id']})
        self.assertEqual(len(self.content_view['versions']), 1)
        cvv = ContentView.version_info({
            'id': self.content_view['versions'][0]['id'],
        })
        self.assertEqual(len(cvv['lifecycle-environments']), 1)
        ContentView.version_promote({
            'id': cvv['id'],
            'lifecycle-environment-id': lce['id'],
        })
        cvv = ContentView.version_info({
            'id': self.content_view['versions'][0]['id'],
        })
        self.assertEqual(len(cvv['lifecycle-environments']), 2)

    @run_only_on('sat')
    def test_promote_multiple_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish it.
        Then promote it to multiple available lifecycle-environments.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.

        @Feature: Docker

        """
        self._create_and_associate_repo_with_cv()
        ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id']})
        self.assertEqual(len(self.content_view['versions']), 1)
        cvv = ContentView.version_info({
            'id': self.content_view['versions'][0]['id'],
        })
        self.assertEqual(len(cvv['lifecycle-environments']), 1)
        for i in range(1, randint(3, 6)):
            lce = make_lifecycle_environment({'organization-id': self.org_id})
            ContentView.version_promote({
                'id': cvv['id'],
                'lifecycle-environment-id': lce['id'],
            })
            cvv = ContentView.version_info({
                'id': self.content_view['versions'][0]['id'],
            })
            self.assertEqual(len(cvv['lifecycle-environments']), i+1)

    @run_only_on('sat')
    def test_promote_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite content view and
        publish it. Then promote it to the next available
        lifecycle-environment.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environment.

        @Feature: Docker

        """
        self._create_and_associate_repo_with_cv()
        ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id']})
        self.assertEqual(len(self.content_view['versions']), 1)
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org_id,
        })
        ContentView.update({
            'component-ids': self.content_view['versions'][0]['id'],
            'id': comp_content_view['id'],
        })
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        self.assertIn(
            self.content_view['versions'][0]['id'],
            [
                component['id']
                for component
                in comp_content_view['components']
            ],
        )
        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        cvv = ContentView.version_info({
            'id': comp_content_view['versions'][0]['id'],
        })
        self.assertEqual(len(cvv['lifecycle-environments']), 1)
        lce = make_lifecycle_environment({'organization-id': self.org_id})
        ContentView.version_promote({
            'id': comp_content_view['versions'][0]['id'],
            'lifecycle-environment-id': lce['id'],
        })
        cvv = ContentView.version_info({
            'id': comp_content_view['versions'][0]['id'],
        })
        self.assertEqual(len(cvv['lifecycle-environments']), 2)

    @run_only_on('sat')
    def test_promote_multiple_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite content view and
        publish it. Then promote it to the multiple available
        lifecycle-environments.

        @Assert: Docker-type repository is promoted to content view found in
        the specific lifecycle-environments.

        @Feature: Docker

        """
        self._create_and_associate_repo_with_cv()
        ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id']})
        self.assertEqual(len(self.content_view['versions']), 1)
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org_id,
        })
        ContentView.update({
            'component-ids': self.content_view['versions'][0]['id'],
            'id': comp_content_view['id'],
        })
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        self.assertIn(
            self.content_view['versions'][0]['id'],
            [
                component['id']
                for component
                in comp_content_view['components']
            ],
        )
        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        cvv = ContentView.version_info({
            'id': comp_content_view['versions'][0]['id'],
        })
        self.assertEqual(len(cvv['lifecycle-environments']), 1)
        for i in range(1, randint(3, 6)):
            lce = make_lifecycle_environment({'organization-id': self.org_id})
            ContentView.version_promote({
                'id': comp_content_view['versions'][0]['id'],
                'lifecycle-environment-id': lce['id'],
            })
            cvv = ContentView.version_info({
                'id': comp_content_view['versions'][0]['id'],
            })
            self.assertEqual(len(cvv['lifecycle-environments']), i+1)


class DockerActivationKeyTestCase(CLITestCase):
    """Tests specific to adding ``Docker`` repositories to Activation Keys."""

    @classmethod
    def setUpClass(cls):
        """Create necessary objects which can be re-used in tests."""
        super(DockerActivationKeyTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.lce = make_lifecycle_environment({
            'organization-id': cls.org['id'],
        })
        cls.product = make_product({
            'organization-id': cls.org['id'],
        })
        cls.repo = _make_docker_repo(cls.product['id'])
        cls.content_view = make_content_view({
            'composite': False,
            'organization-id': cls.org['id'],
        })
        ContentView.add_repository({
            'id': cls.content_view['id'],
            'repository-id': cls.repo['id'],
        })
        cls.content_view = ContentView.info({
            'id': cls.content_view['id']
        })
        ContentView.publish({'id': cls.content_view['id']})
        cls.content_view = ContentView.info({
            'id': cls.content_view['id']})
        cls.cvv = ContentView.version_info({
            'id': cls.content_view['versions'][0]['id'],
        })
        ContentView.version_promote({
            'id': cls.content_view['versions'][0]['id'],
            'lifecycle-environment-id': cls.lce['id'],
        })
        cls.cvv = ContentView.version_info({
            'id': cls.content_view['versions'][0]['id'],
        })

    @run_only_on('sat')
    def test_add_docker_repo_to_activation_key(self):
        """@Test: Add Docker-type repository to a non-composite content view
        and publish it. Then create an activation key and associate it with the
        Docker content view.

        @Assert: Docker-based content view can be added to activation key

        @Feature: Docker

        """
        activation_key = make_activation_key({
            'content-view-id': self.content_view['id'],
            'lifecycle-environment-id': self.lce['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(
            activation_key['content-view'], self.content_view['name'])

    @run_only_on('sat')
    def test_remove_docker_repo_to_activation_key(self):
        """@Test: Add Docker-type repository to a non-composite content view
        and publish it. Create an activation key and associate it with the
        Docker content view. Then remove this content view from the activation
        key.

        @Assert: Docker-based content view can be added and then removed
        from the activation key.

        @Feature: Docker

        """
        activation_key = make_activation_key({
            'content-view-id': self.content_view['id'],
            'lifecycle-environment-id': self.lce['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(
            activation_key['content-view'], self.content_view['name'])

        # Create another content view replace with
        another_cv = make_content_view({
            'composite': False,
            'organization-id': self.org['id'],
        })
        ContentView.publish({'id': another_cv['id']})
        another_cv = ContentView.info({
            'id': another_cv['id']})
        ContentView.version_promote({
            'id': another_cv['versions'][0]['id'],
            'lifecycle-environment-id': self.lce['id'],
        })

        ActivationKey.update({
            'id': activation_key['id'],
            'organization-id': self.org['id'],
            'content-view-id': another_cv['id'],
        })
        activation_key = ActivationKey.info({
            'id': activation_key['id'],
        })
        self.assertNotEqual(
            activation_key['content-view'], self.content_view['name'])

    @run_only_on('sat')
    def test_add_docker_repo_composite_view_to_activation_key(self):
        """@Test: Add Docker-type repository to a non-composite content view
        and publish it. Then add this content view to a composite content view
        and publish it. Create an activation key and associate it with the
        composite Docker content view.

        @Assert: Docker-based content view can be added to activation key

        @Feature: Docker

        """
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
        })
        ContentView.update({
            'component-ids': self.content_view['versions'][0]['id'],
            'id': comp_content_view['id'],
        })
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        self.assertIn(
            self.content_view['versions'][0]['id'],
            [
                component['id']
                for component
                in comp_content_view['components']
            ],
        )
        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        comp_cvv = ContentView.version_info({
            'id': comp_content_view['versions'][0]['id'],
        })
        ContentView.version_promote({
            'id': comp_cvv['id'],
            'lifecycle-environment-id': self.lce['id'],
        })
        activation_key = make_activation_key({
            'content-view-id': comp_content_view['id'],
            'lifecycle-environment-id': self.lce['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(
            activation_key['content-view'], comp_content_view['name'])

    @run_only_on('sat')
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
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org['id'],
        })
        ContentView.update({
            'component-ids': self.content_view['versions'][0]['id'],
            'id': comp_content_view['id'],
        })
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        self.assertIn(
            self.content_view['versions'][0]['id'],
            [
                component['id']
                for component
                in comp_content_view['components']
            ],
        )
        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        })
        comp_cvv = ContentView.version_info({
            'id': comp_content_view['versions'][0]['id'],
        })
        ContentView.version_promote({
            'id': comp_cvv['id'],
            'lifecycle-environment-id': self.lce['id'],
        })
        activation_key = make_activation_key({
            'content-view-id': comp_content_view['id'],
            'lifecycle-environment-id': self.lce['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(
            activation_key['content-view'], comp_content_view['name'])

        # Create another content view replace with
        another_cv = make_content_view({
            'composite': False,
            'organization-id': self.org['id'],
        })
        ContentView.publish({'id': another_cv['id']})
        another_cv = ContentView.info({
            'id': another_cv['id']})
        ContentView.version_promote({
            'id': another_cv['versions'][0]['id'],
            'lifecycle-environment-id': self.lce['id'],
        })

        ActivationKey.update({
            'id': activation_key['id'],
            'organization-id': self.org['id'],
            'content-view-id': another_cv['id'],
        })
        activation_key = ActivationKey.info({
            'id': activation_key['id'],
        })
        self.assertNotEqual(
            activation_key['content-view'], comp_content_view['name'])


class DockerClientTestCase(CLITestCase):
    """Tests specific to using ``Docker`` as a client to pull Docker images
    from a Satellite 6 instance."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerClientTestCase, cls).setUpClass()
        cls.org_id = make_org()['id']

    @stubbed()
    @run_only_on('sat')
    def test_docker_client_pull_image(self):
        """@Test: A Docker-enabled client can use ``docker pull`` to pull a
        Docker image off a Satellite 6 instance.

        @Feature: Docker

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

        @Feature: Docker

        @Steps:

        1. Publish and promote content view with Docker content
        2. Register Docker-enabled client against Satellite 6.

        @Assert: Client can create a new image based off an existing Docker
        image from a Satellite 6 instance, add a new package and upload the
        modified image (plus layer) back to the Satellite 6.

        @Status: Manual

        """


class DockerComputeResourceTestCase(CLITestCase):
    """Tests specific to managing Docker-based Compute Resources."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerComputeResourceTestCase, cls).setUpClass()
        cls.org = make_org()

    @run_only_on('sat')
    def test_create_internal_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the Satellite 6
        instance.

        @Assert: Compute Resource can be created and listed.

        @Feature: Docker

        """
        for name in valid_data_list():
            with self.subTest(name):
                compute_resource = make_compute_resource({
                    'name': name,
                    'provider': DOCKER_PROVIDER,
                    'url': settings.docker.get_unix_socket_url(),
                })
                self.assertEqual(compute_resource['name'], name)
                self.assertEqual(compute_resource['provider'], DOCKER_PROVIDER)
                self.assertEqual(
                    compute_resource['url'],
                    settings.docker.get_unix_socket_url()
                )

    @run_only_on('sat')
    def test_update_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the Satellite 6
        instance then edit its attributes.

        @Assert: Compute Resource can be created, listed and its attributes can
        be updated.

        @Feature: Docker

        """
        for url in (settings.docker.external_url,
                    settings.docker.get_unix_socket_url()):
            with self.subTest(url):
                compute_resource = make_compute_resource({
                    'provider': DOCKER_PROVIDER,
                    'url': url,
                })
                self.assertEqual(compute_resource['url'], url)
                new_url = gen_url(subdomain=gen_alpha())
                ComputeResource.update({
                    'id': compute_resource['id'],
                    'url': new_url,
                })
                compute_resource = ComputeResource.info({
                    'id': compute_resource['id'],
                })
                self.assertEqual(compute_resource['url'], new_url)

    @run_only_on('sat')
    def test_list_containers_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the Satellite 6
        instance then list its running containers.

        @Assert: Compute Resource can be created, listed and existing running
        instances can be listed.

        @Feature: Docker

        """
        for url in (settings.docker.external_url,
                    settings.docker.get_unix_socket_url()):
            with self.subTest(url):
                compute_resource = make_compute_resource({
                    'organization-ids': [self.org['id']],
                    'provider': DOCKER_PROVIDER,
                    'url': url,
                })
                self.assertEqual(compute_resource['url'], url)
                result = Docker.container.list({
                    'compute-resource-id': compute_resource['id'],
                })
                self.assertEqual(len(result), 0)
                container = make_container({
                    'compute-resource-id': compute_resource['id'],
                    'organization-ids': [self.org['id']],
                })
                result = Docker.container.list({
                    'compute-resource-id': compute_resource['id'],
                })
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]['name'], container['name'])

    @run_only_on('sat')
    def test_create_external_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource using an external
        Docker-enabled system.

        @Assert: Compute Resource can be created and listed.

        @Feature: Docker

        """
        for name in valid_data_list():
            with self.subTest(name):
                compute_resource = make_compute_resource({
                    'name': name,
                    'provider': DOCKER_PROVIDER,
                    'url': settings.docker.external_url,
                })
                self.assertEqual(compute_resource['name'], name)
                self.assertEqual(compute_resource['provider'], DOCKER_PROVIDER)
                self.assertEqual(
                    compute_resource['url'], settings.docker.external_url)

    @run_only_on('sat')
    def test_delete_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource then delete it.

        @Assert: Compute Resource can be created, listed and deleted.

        @Feature: Docker

        """
        for url in (settings.docker.external_url,
                    settings.docker.get_unix_socket_url()):
            with self.subTest(url):
                compute_resource = make_compute_resource({
                    'provider': DOCKER_PROVIDER,
                    'url': url,
                })
                self.assertEqual(compute_resource['url'], url)
                self.assertEqual(compute_resource['provider'], DOCKER_PROVIDER)
                ComputeResource.delete({'id': compute_resource['id']})
                with self.assertRaises(CLIReturnCodeError):
                    ComputeResource.info({'id': compute_resource['id']})


class DockerContainersTestCase(CLITestCase):
    """Tests specific to using ``Containers`` in local and external Docker
    Compute Resources

    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerContainersTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.cr_internal = make_compute_resource({
            'organization-ids': [cls.org['id']],
            'provider': DOCKER_PROVIDER,
            'url': settings.docker.get_unix_socket_url(),
        })
        cls.cr_external = make_compute_resource({
            'organization-ids': [cls.org['id']],
            'provider': DOCKER_PROVIDER,
            'url': settings.docker.external_url,
        })
        install_katello_ca()

    @classmethod
    def tearDownClass(cls):
        """Remove katello-ca certificate"""
        remove_katello_ca()
        super(DockerContainersTestCase, cls).tearDownClass()

    @run_only_on('sat')
    def test_create_container(self):
        """@Test: Create containers for local and external compute resources

        @Feature: Docker

        @Assert: The docker container is created for each compute resource

        """
        for compute_resource in (self.cr_internal, self.cr_external):
            with self.subTest(compute_resource['url']):
                container = make_container({
                    'compute-resource-id': compute_resource['id'],
                    'organization-ids': [self.org['id']],
                })
                self.assertEqual(
                    container['compute-resource'], compute_resource['name'])

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1282431)
    def test_create_container_content_view(self):
        """@Test: Create docker container using custom content view, lifecycle
        environment and docker repository for local and external compute
        resources

        @Feature: Docker

        @Assert: The docker container is created for each compute resource

        @BZ: 1282431
        """
        lce = make_lifecycle_environment({'organization-id': self.org['id']})
        repo = _make_docker_repo(
            make_product({'organization-id': self.org['id']})['id'],
            upstream_name='centos',
        )
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({'organization-id': self.org['id']})
        ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        ContentView.version_promote({
            'content-view-id': content_view['id'],
            'id': content_view['versions'][0]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        for compute_resource in (self.cr_internal, self.cr_external):
            with self.subTest(compute_resource['url']):
                container = make_container({
                    'compute-resource-id': compute_resource['id'],
                    'organization-ids': [self.org['id']],
                    'repository-name': repo['container-repository-name'],
                    'tag': 'latest',
                    'tty': 'yes',
                })
                self.assertEqual(
                    container['compute-resource'], compute_resource['name'])
                self.assertEqual(
                    container['image-repository'],
                    repo['container-repository-name']
                )
                self.assertEqual(container['tag'], 'latest')

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1230915)
    @skip_if_bug_open('bugzilla', 1269196)
    def test_container_power(self):
        """@Test: Create containers for local and external compute resource,
        then power them on and finally power them off

        @Feature: Docker

        @Assert: The docker container is created for each compute resource
        and the power status is showing properly

        @BZ: 1230915, 1269196

        """
        # testing the text status may fail i18n tests but for now there is
        # nothing else to assert
        not_running_msg = 'Running: no'
        running_msg = 'Running: yes'
        for compute_resource in (self.cr_internal, self.cr_external):
            with self.subTest(compute_resource['url']):
                container = make_container({
                    'compute-resource-id': compute_resource['id'],
                    'organization-ids': [self.org['id']],
                })
                status = Docker.container.status({'id': container['id']})
                self.assertEqual(status[0], running_msg)
                Docker.container.stop({'id': container['id']})
                status = Docker.container.status({'id': container['id']})
                self.assertEqual(status[0], not_running_msg)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1230915)
    @skip_if_bug_open('bugzilla', 1269208)
    def test_container_read_log(self):
        """@Test: Create containers for local and external compute resource and
        read their logs

        @Feature: Docker

        @Assert: The docker container is created for each compute resource and
        its log can be read

        @BZ: 1230915, 1269208

        """
        for compute_resource in (self.cr_internal, self.cr_external):
            with self.subTest(compute_resource['url']):
                container = make_container({
                    'command': 'date',
                    'compute-resource-id': compute_resource['id'],
                    'organization-ids': [self.org['id']],
                })
                logs = Docker.container.logs({'id': container['id']})
                self.assertTrue(logs['logs'])

    @run_only_on('sat')
    @stubbed()
    def test_create_container_external_registry(self):
        """@Test: Create a container pulling an image from a custom external
        registry

        @Feature: Docker

        @Assert: The docker container is created and the image is pulled from
        the external registry

        @Status: Manual

        """

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1230915)
    def test_delete_container(self):
        """@Test: Delete containers in local and external compute resources

        @Feature: Docker

        @Assert: The docker containers are deleted in local and external
        compute resources

        @BZ: 1230915

        """
        for compute_resource in (self.cr_internal, self.cr_external):
            with self.subTest(compute_resource['url']):
                container = make_container({
                    'compute-resource-id': compute_resource['id'],
                    'organization-ids': [self.org['id']],
                })
                Docker.container.delete({'id': container['id']})
                with self.assertRaises(CLIReturnCodeError):
                    Docker.container.info({'id': container['id']})


class DockerRegistriesTestCase(CLITestCase):
    """Tests specific to performing CRUD methods against ``Registries``
    repositories.

    """

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1259498)
    def test_create_registry(self):
        """@Test: Create an external docker registry

        @Feature: Docker

        @Assert: the external registry is created

        @BZ: 1259498

        """
        for name in valid_data_list():
            with self.subTest(name):
                url = gen_url(subdomain=gen_string('alpha'))
                description = gen_string('alphanumeric')
                registry = make_registry({
                    'description': description,
                    'name': name,
                    'url': url,
                })
                self.assertEqual(registry['name'], name)
                self.assertEqual(registry['description'], description)
                self.assertEqual(registry['url'], url)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1259498)
    def test_update_registry_name_by_id(self):
        """@Test: Create an external docker registry and update its name. Use
        registry ID to search by

        @Feature: Docker

        @Assert: the external registry is updated with the new name

        @BZ: 1259498

        """
        registry = make_registry()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                Docker.registry.update({
                    'id': registry['id'],
                    'new-name': new_name,
                })
                registry = Docker.registry.info({'id': registry['id']})
                self.assertEqual(registry['name'], new_name)

    @run_only_on('sat')
    def test_update_registry_name_by_name(self):
        """@Test: Create an external docker registry and update its name. Use
        registry name to search by

        @Feature: Docker

        @Assert: the external registry is updated with the new name

        """
        registry = make_registry()
        for new_name in valid_data_list():
            with self.subTest(new_name):
                Docker.registry.update({
                    'name': registry['name'],
                    'new-name': new_name,
                })
                registry = Docker.registry.info({'name': new_name})
                self.assertEqual(registry['name'], new_name)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1259498)
    def test_update_registry_url_by_id(self):
        """@Test: Create an external docker registry and update its URL. Use
        registry ID to search by

        @Feature: Docker

        @Assert: the external registry is updated with the new URL

        @BZ: 1259498

        """
        registry = make_registry()
        new_url = gen_url(subdomain=gen_string('alpha'))
        Docker.registry.update({
            'id': registry['id'],
            'url': new_url,
        })
        registry = Docker.registry.info({'id': registry['id']})
        self.assertEqual(registry['url'], new_url)

    @run_only_on('sat')
    def test_update_registry_url_by_name(self):
        """@Test: Create an external docker registry and update its URL. Use
        registry name to search by

        @Feature: Docker

        @Assert: the external registry is updated with the new URL

        """
        registry = make_registry()
        new_url = gen_url(subdomain=gen_string('alpha'))
        Docker.registry.update({
            'name': registry['name'],
            'url': new_url,
        })
        registry = Docker.registry.info({'name': registry['name']})
        self.assertEqual(registry['url'], new_url)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1259498)
    def test_update_registry_description_by_id(self):
        """@Test: Create an external docker registry and update its
        description. Use registry ID to search by

        @Feature: Docker

        @Assert: the external registry is updated with the new description

        @BZ: 1259498

        """
        registry = make_registry({'description': gen_string('alpha')})
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                Docker.registry.update({
                    'description': new_desc,
                    'id': registry['id'],
                })
                registry = Docker.registry.info({'id': registry['id']})
                self.assertEqual(registry['description'], new_desc)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1259498)
    def test_update_registry_description_by_name(self):
        """@Test: Create an external docker registry and update its
        description. Use registry name to search by

        @Feature: Docker

        @Assert: the external registry is updated with the new description

        @BZ: 1259498

        """
        registry = make_registry({'description': gen_string('alpha')})
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                Docker.registry.update({
                    'description': new_desc,
                    'name': registry['name'],
                })
                registry = Docker.registry.info({'name': registry['name']})
                self.assertEqual(registry['description'], new_desc)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1259498)
    def test_update_registry_username_by_id(self):
        """@Test: Create an external docker registry and update its username.
        Use registry ID to search by

        @Feature: Docker

        @Assert: the external registry is updated with the new username

        @BZ: 1259498

        """
        registry = make_registry({'username': gen_string('alpha')})
        for new_user in valid_data_list():
            with self.subTest(new_user):
                Docker.registry.update({
                    'id': registry['id'],
                    'username': new_user,
                })
                registry = Docker.registry.info({'id': registry['id']})
                self.assertEqual(registry['username'], new_user)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1259498)
    def test_update_registry_username_by_name(self):
        """@Test: Create an external docker registry and update its username.
        Use registry name to search by

        @Feature: Docker

        @Assert: the external registry is updated with the new username

        @BZ: 1259498

        """
        registry = make_registry({'username': gen_string('alpha')})
        for new_user in valid_data_list():
            with self.subTest(new_user):
                Docker.registry.update({
                    'name': registry['name'],
                    'username': new_user,
                })
                registry = Docker.registry.info({'name': registry['name']})
                self.assertEqual(registry['username'], new_user)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1259498)
    def test_delete_registry_by_id(self):
        """@Test: Create an external docker registry. Use registry ID to search
        by

        @Feature: Docker

        @Assert: the external registry is created

        @BZ: 1259498

        """
        registry = make_registry()
        Docker.registry.delete({'id': registry['id']})
        with self.assertRaises(CLIReturnCodeError):
            Docker.registry.info({'id': registry['id']})

    @run_only_on('sat')
    def test_delete_registry_by_name(self):
        """@Test: Create an external docker registry. Use registry name to
        search by

        @Feature: Docker

        @Assert: the external registry is created

        """
        for name in valid_data_list():
            with self.subTest(name):
                registry = make_registry({'name': name})
                Docker.registry.delete({'name': registry['name']})
                with self.assertRaises(CLIReturnCodeError):
                    Docker.registry.info({'name': registry['name']})
