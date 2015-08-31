"""Unit tests for the Docker feature."""
from ddt import ddt
from fauxfactory import gen_choice, gen_string, gen_url
from nailgun import entities
from random import choice, randint
from robottelo.cli.docker import Docker
from robottelo.cli.factory import (
    CLIFactoryError,
    make_content_view,
    make_org,
    make_product,
    make_repository,
)
from robottelo.cli.contentview import ContentView
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
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
)
from robottelo.test import CLITestCase
# (too-many-public-methods) pylint:disable=R0904

EXTERNAL_DOCKER_URL = get_external_docker_url()
INTERNAL_DOCKER_URL = get_internal_docker_url()
STRING_TYPES = ['alpha', 'alphanumeric', 'cjk', 'utf8', 'latin1']

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


@ddt
class DockerImageTestCase(CLITestCase):
    """Tests related to docker image command"""

    @skip_if_bug_open('bugzilla', 1221729)
    def test_bugzilla_1190122(self):
        """@Test: docker image displays tags information for a docker image

        @Feature: Docker

        @Assert: docker image displays tags information for a docker image

        @BZ: 1221729

        """
        try:
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
        except CLIFactoryError as err:
            self.fail(err)

        result = Repository.synchronize({'id': repository['id']})
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Grab all available images related to repository
        result = Docker.image.list({
            u'repository-id': repository['id'],
        })
        self.assertEqual(result.return_code, 0)
        self.assertEqual(len(result.stderr), 0)

        # Some images do not have tags associated with it, ignore those because
        # we want to check the tag information
        images = [
            image for image in result.stdout if int(image['tag-count']) > 0
        ]
        for image in images:
            result = Docker.image.info({'id': image['id']})
            self.assertEqual(result.return_code, 0)
            self.assertEqual(len(result.stderr), 0)

            # Extract the list of repository ids of the available image's tags
            tag_repository_ids = []
            for tag in result.stdout['tags']:
                tag_repository_ids.append(tag['repository-id'])
                self.assertGreater(len(tag['tag']), 0)
            self.assertIn(repository['id'], tag_repository_ids)


@run_only_on('sat')
@ddt
class DockerRepositoryTestCase(CLITestCase):
    """Tests specific to performing CRUD methods against ``Docker``
    repositories.

    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
        cls.org_id = entities.Organization().create_json()['id']

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
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'],
            name,
        )
        self.assertEqual(repo['name'], name)
        self.assertEqual(repo['upstream-repository-name'], REPO_UPSTREAM_NAME)
        self.assertEqual(repo['content-type'], REPO_CONTENT_TYPE)

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
        }).stdout
        self.assertEqual(
            repo_names,
            set([repo_['repo-name'] for repo_ in product['content']]),
        )

    def test_create_multiple_docker_repo_multiple_products(self):
        """@Test: Create multiple Docker-type repositories on multiple products.

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
            }).stdout
            self.assertEqual(
                repo_names,
                set([repo_['repo-name'] for repo_ in product['content']]),
            )

    def test_sync_docker_repo(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        """
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        self.assertEqual(int(repo['content-counts']['docker-images']), 0)
        result = Repository.synchronize({'id': repo['id']})
        self.assertEqual(result.return_code, 0)
        repo = Repository.info({'id': repo['id']}).stdout
        self.assertGreaterEqual(
            int(repo['content-counts']['docker-images']), 1)

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
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        self.assertNotEqual(repo['name'], new_name)
        result = Repository.update({
            'id': repo['id'],
            'new-name': new_name,
            'url': repo['url'],
        })
        self.assertEqual(result.return_code, 0)
        repo = Repository.info({'id': repo['id']}).stdout
        self.assertEqual(repo['name'], new_name)

    def test_update_docker_repo_upstream_name(self):
        """@Test: Create a Docker-type repository and update its upstream name.

        @Assert: A repository is created with a Docker image and that its
        upstream name can be updated.

        @Feature: Docker

        """
        new_upstream_name = 'fedora/ssh'
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        result = Repository.update({
            'docker-upstream-name': new_upstream_name,
            'id': repo['id'],
            'url': repo['url'],
        })
        self.assertEqual(result.return_code, 0)
        repo = Repository.info({'id': repo['id']}).stdout
        self.assertEqual(repo['upstream-repository-name'], new_upstream_name)

    def test_update_docker_repo_url(self):
        """@Test: Create a Docker-type repository and update its URL.

        @Assert: A repository is created with a Docker image and that its
        URL can be updated.

        @Feature: Docker

        """
        new_url = gen_url()
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        result = Repository.update({
            'id': repo['id'],
            'url': new_url,
        })
        self.assertEqual(result.return_code, 0)
        repo = Repository.info({'id': repo['id']}).stdout
        self.assertEqual(repo['url'], new_url)

    def test_delete_docker_repo(self):
        """@Test: Create and delete a Docker-type repository

        @Assert: A repository is created with a Docker image and then deleted.

        @Feature: Docker

        """
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        result = Repository.delete({'id': repo['id']})
        self.assertEqual(result.return_code, 0)
        result = Repository.info({'id': repo['id']})
        self.assertNotEqual(result.return_code, 0)

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
        result = Repository.delete({'id': repo['id']})
        self.assertEqual(result.return_code, 0)
        result = Repository.info({'id': repo['id']})
        self.assertNotEqual(result.return_code, 0)
        # Verify other repositories were not touched
        for repo in repos:
            result = Repository.info({'id': repo['id']})
            self.assertEqual(result.return_code, 0)
            self.assertIn(
                result.stdout['product']['id'],
                [product['id'] for product in products],
            )


@run_only_on('sat')
@ddt
class DockerContentViewTestCase(CLITestCase):
    """Tests specific to using ``Docker`` repositories with Content Views."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(DockerContentViewTestCase, cls).setUpClass()
        cls.org_id = entities.Organization().create_json()['id']

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
        result = ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        content_view = ContentView.info({'id': content_view['id']}).stdout
        self.assertIn(
            repo['id'],
            [repo_['id'] for repo_ in content_view['docker-repositories']],
        )

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
            result = ContentView.add_repository({
                'id': content_view['id'],
                'repository-id': repo['id'],
            })
            self.assertEqual(result.return_code, 0)
        content_view = ContentView.info({'id': content_view['id']}).stdout
        self.assertEqual(
            set([repo['id'] for repo in repos]),
            set([repo['id'] for repo in content_view['docker-repositories']]),
        )

    def test_add_synced_docker_repo_to_content_view(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        """
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        result = Repository.synchronize({'id': repo['id']})
        self.assertEqual(result.return_code, 0)
        repo = Repository.info({'id': repo['id']}).stdout
        self.assertGreaterEqual(
            int(repo['content-counts']['docker-images']), 1)
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        result = ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        content_view = ContentView.info({'id': content_view['id']}).stdout
        self.assertIn(
            repo['id'],
            [repo_['id'] for repo_ in content_view['docker-repositories']],
        )

    def test_add_docker_repo_to_composite_content_view(self):
        """@Test: Add one Docker-type repository to a composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a content view which is then added to a composite
        content view.

        @Feature: Docker

        """
        repo = _make_docker_repo(
            make_product({'organization-id': self.org_id})['id'])
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        result = ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        self.assertEqual(result.return_code, 0)
        content_view = ContentView.info({'id': content_view['id']}).stdout
        self.assertIn(
            repo['id'],
            [repo_['id'] for repo_ in content_view['docker-repositories']],
        )
        result = ContentView.publish({'id': content_view['id']})
        self.assertEqual(result.return_code, 0)
        content_view = ContentView.info({'id': content_view['id']}).stdout
        self.assertEqual(len(content_view['versions']), 1)
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org_id,
        })
        result = ContentView.update({
            'id': comp_content_view['id'],
            'component-ids': content_view['versions'][0]['id'],
        })
        self.assertEqual(result.return_code, 0)
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        }).stdout
        self.assertIn(
            content_view['versions'][0]['id'],
            [component['id'] for component in comp_content_view['components']],
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
        product = make_product({'organization-id': self.org_id})
        for _ in range(randint(2, 5)):
            content_view = make_content_view({
                'composite': False,
                'organization-id': self.org_id,
            })
            repo = _make_docker_repo(product['id'])
            result = ContentView.add_repository({
                'id': content_view['id'],
                'repository-id': repo['id'],
            })
            self.assertEqual(result.return_code, 0)
            result = ContentView.publish({'id': content_view['id']})
            self.assertEqual(result.return_code, 0)
            content_view = ContentView.info({'id': content_view['id']}).stdout
            self.assertEqual(len(content_view['versions']), 1)
            cv_versions.append(content_view['versions'][0])
        comp_content_view = make_content_view({
            'composite': True,
            'organization-id': self.org_id,
        })
        cv_versions_ids = ','.join(
            cv_version['id'] for cv_version in cv_versions)
        result = ContentView.update({
            'component-ids': cv_versions_ids,
            'id': comp_content_view['id'],
        })
        self.assertEqual(result.return_code, 0)
        comp_content_view = ContentView.info({
            'id': comp_content_view['id'],
        }).stdout
        for cv_version in cv_versions:
            self.assertIn(
                cv_version['id'],
                [
                    component['id']
                    for component
                    in comp_content_view['components']
                ],
            )

    @stubbed()
    @run_only_on('sat')
    def test_publish_once_docker_repo_content_view(self):
        """@Test: Add Docker-type repository to content view and publish
        it once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_publish_once_docker_repo_composite_content_view(self):
        """@Test: Add Docker-type repository to composite
        content view and publish it once.

        @Assert: One repository is created with a Docker image and the product
        is added to a content view which is then published only once and then
        added to a composite content view which is also published only once.

        @Feature: Docker

        @Status: Manual

        """

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
class DockerActivationKeyTestCase(CLITestCase):
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
class DockerClientTestCase(CLITestCase):
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
class DockerComputeResourceTestCase(CLITestCase):
    """Tests specific to managing Docker-based Compute Resources."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerComputeResourceTestCase, cls).setUpClass()
        cls.org_id = entities.Organization().create_json()['id']

    @stubbed()
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

        @Status: Manual

        """

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

    @stubbed()
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

        @Status: Manual

        """

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

    @stubbed()
    @run_only_on('sat')
    @data(
        EXTERNAL_DOCKER_URL,
        INTERNAL_DOCKER_URL,
    )
    def test_delete_docker_compute_resource(self, url):
        """@Test: Create a Docker-based Compute Resource then delete it.

        @Assert: Compute Resource can be created, listed and deleted.

        @Feature: Docker

        @Status: Manual

        """


class DockerContainersTestCase(CLITestCase):
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
class DockerRegistriesTestCase(CLITestCase):
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
