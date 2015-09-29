"""Unit tests for the Docker feature."""
from nailgun import entities
from robottelo.decorators import run_only_on, stubbed
from robottelo.helpers import (
    get_external_docker_url,
    get_internal_docker_url,
)
from robottelo.test import UITestCase
# (too-many-public-methods) pylint:disable=R0904

EXTERNAL_DOCKER_URL = get_external_docker_url()
INTERNAL_DOCKER_URL = get_internal_docker_url()


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
        cls.org_id = entities.Organization().create_json()['id']

    @stubbed()
    @run_only_on('sat')
    def test_create_one_docker_repo(self):
        """@Test: Create one Docker-type repository

        @Assert: A repository is created with a Docker image.

        @Feature: Docker

        @Status: Manual

        """
        # Use robottelo.helpers.valid_data_list for random valid strings

    @stubbed()
    @run_only_on('sat')
    def test_create_multiple_docker_repo(self):
        """@Test: Create multiple Docker-type repositories

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to the same product.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_create_multiple_docker_repo_multiple_products(self):
        """@Test: Create multiple Docker-type repositories on multiple products.

        @Assert: Multiple docker repositories are created with a Docker image
        and they all belong to their respective products.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_sync_docker_repo(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_update_docker_repo_name(self):
        """@Test: Create a Docker-type repository and update its name.

        @Assert: A repository is created with a Docker image and that its
        name can be updated.

        @Feature: Docker

        @Status: Manual

        """
        # Use robottelo.helpers.valid_data_list for random valid strings

    @stubbed()
    @run_only_on('sat')
    def test_update_docker_repo_upstream_name(self):
        """@Test: Create a Docker-type repository and update its upstream name.

        @Assert: A repository is created with a Docker image and that its
        upstream name can be updated.

        @Feature: Docker

        @Status: Manual

        """
        # Use robottelo.helpers.valid_data_list for random valid strings

    @stubbed()
    @run_only_on('sat')
    def test_update_docker_repo_url(self):
        """@Test: Create a Docker-type repository and update its URL.

        @Assert: A repository is created with a Docker image and that its
        URL can be updated.

        @Feature: Docker

        @Status: Manual

        """
        # Use robottelo.helpers.valid_data_list for random valid strings

    @stubbed()
    @run_only_on('sat')
    def test_delete_docker_repo(self):
        """@Test: Create and delete a Docker-type repository

        @Assert: A repository is created with a Docker image and then deleted.

        @Feature: Docker

        @Status: Manual

        """
        # Use robottelo.helpers.valid_data_list for random valid strings

    @stubbed()
    @run_only_on('sat')
    def test_delete_random_docker_repo(self):
        """@Test: Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        @Assert: Random repository can be deleted from random product without
        altering the other products.

        @Feature: Docker

        @Status: Manual

        """


class DockerContentViewTestCase(UITestCase):
    """Tests specific to using ``Docker`` repositories with Content Views."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(DockerContentViewTestCase, cls).setUpClass()
        cls.org_id = entities.Organization().create_json()['id']

    @stubbed()
    @run_only_on('sat')
    def test_add_docker_repo_to_content_view(self):
        """@Test: Add one Docker-type repository to a non-composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a non-composite content view

        @Feature: Docker

        @Status: Manual

        """
        # Use robottelo.helpers.valid_data_list for random valid strings

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

    @stubbed()
    @run_only_on('sat')
    def test_add_synced_docker_repo_to_content_view(self):
        """@Test: Create and sync a Docker-type repository

        @Assert: A repository is created with a Docker repository
        and it is synchronized.

        @Feature: Docker

        @Status: Manual

        """

    @stubbed()
    @run_only_on('sat')
    def test_add_docker_repo_to_composite_content_view(self):
        """@Test: Add one Docker-type repository to a composite content view

        @Assert: A repository is created with a Docker repository and the
        product is added to a content view which is then added to a composite
        content view.

        @Feature: Docker

        @Status: Manual

        """
        # Use robottelo.helpers.valid_data_list for random valid strings

    @stubbed()
    @run_only_on('sat')
    def test_add_multiple_docker_repos_to_composite_content_view(self):
        """@Test: Add multiple Docker-type repositories to a composite
        content view.

        @Assert: One repository is created with a Docker image and the
        product is added to a random number of content views which are then
        added to a composite content view.

        @Feature: Docker

        @Status: Manual

        """

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


class DockerActivationKeyTestCase(UITestCase):
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


class DockerClientTestCase(UITestCase):
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


class DockerComputeResourceTestCase(UITestCase):
    """Tests specific to managing Docker-based Compute Resources."""

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerComputeResourceTestCase, cls).setUpClass()
        cls.org_id = entities.Organization().create_json()['id']

    @stubbed()
    @run_only_on('sat')
    def test_create_internal_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource in the Satellite 6
        instance.

        @Assert: Compute Resource can be created and listed.

        @Feature: Docker

        @Status: Manual

        """
        # Use robottelo.helpers.valid_data_list for random valid strings

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
    def test_create_external_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource using an external
        Docker-enabled system.

        @Assert: Compute Resource can be created and listed.

        @Feature: Docker

        @Status: Manual

        """
        # Use robottelo.helpers.valid_data_list for random valid strings

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
    def test_delete_docker_compute_resource(self):
        """@Test: Create a Docker-based Compute Resource then delete it.

        @Assert: Compute Resource can be created, listed and deleted.

        @Feature: Docker

        @Status: Manual

        """
        # Use (EXTERNAL_DOCKER_URL, INTERNAL_DOCKER_URL) for random
        # URL values.


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
