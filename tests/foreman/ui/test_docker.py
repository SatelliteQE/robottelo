"""WebUI tests for the Docker feature.

:Requirement: Docker

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import randint

from fauxfactory import gen_string, gen_url
from nailgun import entities

from robottelo.config import settings
from robottelo.constants import (
    DOCKER_REGISTRY_HUB,
    FOREMAN_PROVIDERS,
    REPO_TYPE,
)
from robottelo.datafactory import (
    invalid_docker_upstream_names,
    valid_data_list,
    valid_docker_repository_names,
    valid_docker_upstream_names,
)
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_registry,
    make_repository,
    make_resource,
    set_context,
)
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.products import Products
from robottelo.ui.session import Session


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
    Products(session.browser).search_and_click(product)
    make_repository(
        session,
        name=name,
        repo_type=REPO_TYPE['docker'],
        url=DOCKER_REGISTRY_HUB,
        upstream_repo_name=upstream_name,
    )


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

        :id: 233f39b5-ec75-4035-a45f-0f37a40bbdfe

        :expectedresults: A repository is created with a Docker upstream
            repository.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_docker_repository_names():
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

        :id: f6e7d9fe-7dec-42ef-8cbd-071871e4b8ac

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to the same product.

        :CaseImportance: Critical
        """
        product = entities.Product(organization=self.organization).create()
        with Session(self) as session:
            for _ in range(randint(2, 5)):
                name = gen_string('utf8')
                _create_repository(
                    session,
                    org=self.organization.name,
                    name=name,
                    product=product.name,
                )
                self.products.search_and_click(product.name)
                self.assertIsNotNone(self.repository.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create_repos_using_multiple_products(self):
        """Create multiple Docker-type repositories on multiple products.

        :id: da76f1e8-236e-455d-b300-676e00e3df8e

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to their respective
            products.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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
                    self.products.search_and_click(pr.name)
                    self.assertIsNotNone(self.repository.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Create a Docker-type repository and update its name.

        :id: 64878d14-39ed-44fd-9a71-5923edaa6e3d

        :expectedresults: A repository is created with a Docker upstream
            repository and that its name can be updated.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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
            for new_name in valid_docker_repository_names():
                with self.subTest(new_name):
                    self.repository.update(name, new_name=new_name)
                    self.products.search_and_click(product.name)
                    self.assertIsNotNone(self.repository.search(new_name))
                    name = new_name

    @run_only_on('sat')
    @tier1
    def test_positive_update_upstream_name(self):
        """Create a Docker-type repository and update its upstream name.

        :id: b7e17891-e248-4044-ac88-8f8a9d0e95f2

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can be updated.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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
            for new_upstream_name in valid_docker_upstream_names():
                with self.subTest(new_upstream_name):
                    self.products.search_and_click(product.name)
                    self.repository.update(
                        repo_name, new_upstream_name=new_upstream_name)
                    self.products.search_and_click(product.name)
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'upstream', new_upstream_name))

    @run_only_on('sat')
    @tier1
    def test_negative_update_upstream_name(self):
        """Attempt to update upstream name for a Docker-type repository.

        :id: 4722cfa1-33d0-41c4-8ed2-46da9b6d0cd1

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can not be updated with
            invalid values.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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
            for new_upstream_name in invalid_docker_upstream_names():
                with self.subTest(new_upstream_name):
                    self.products.search_and_click(product.name)
                    self.repository.update(
                        repo_name, new_upstream_name=new_upstream_name)
                    self.assertIsNotNone(self.products.wait_until_element(
                        common_locators['alert.error']))
                    self.repository.click(common_locators['alert.close'])
                    self.products.search_and_click(product.name)
                    self.assertTrue(self.repository.validate_field(
                        repo_name, 'upstream', 'busybox'))

    @run_only_on('sat')
    @tier1
    def test_positive_update_url(self):
        """Create a Docker-type repository and update its URL.

        :id: d85892a2-a887-413d-81c6-97a2a518f365

        :expectedresults: A repository is created with a Docker upstream
            repository and that its URL can be updated.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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
            self.products.search_and_click(product.name)
            self.repository.update(name, new_url=new_url)
            self.products.search_and_click(product.name)
            self.assertTrue(self.repository.validate_field(
                name, 'url', new_url))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create and delete a Docker-type repository

        :id: 725a0f6b-67c5-4a59-a7b9-2308333a42bd

        :expectedresults: A repository is created with a Docker upstream
            repository and then deleted.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_docker_repository_names():
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
    @tier1
    def test_positive_create_with_disabled_sync_plan(self):
        """Create sync plan, disable it, add to product and create docker repo
        for mentioned product.

        :id: 8a926e5a-2602-4007-ab4d-e0881a2538aa

        :expectedresults: Docker repository is successfully created

        :CaseImportance: Critical

        :BZ: 1426410
        """
        sync_plan = entities.SyncPlan(
            enabled=True,
            organization=self.organization,
        ).create()
        sync_plan.enabled = False
        sync_plan = sync_plan.update(['enabled'])
        self.assertEqual(sync_plan.enabled, False)
        product = entities.Product(
            organization=self.organization,
            sync_plan=sync_plan,
        ).create()
        self.assertEqual(product.sync_plan.id, sync_plan.id)
        repo_name = gen_string('alphanumeric')
        with Session(self) as session:
            _create_repository(
                session,
                org=self.organization.name,
                name=repo_name,
                product=product.name,
            )
            self.assertIsNotNone(self.repository.search(repo_name))


class DockerActivationKeyTestCase(UITestCase):
    """Tests specific to adding ``Docker`` repositories to Activation Keys."""

    @stubbed()
    # Return to that case once BZ 1269829 is fixed
    @run_only_on('sat')
    @tier2
    def test_positive_remove_docker_repo_cv(self):
        """Add Docker-type repository to a non-composite content view and
        publish it. Create an activation key and associate it with the Docker
        content view. Then remove this content view from the activation key.

        :id: 4336093e-141b-47e0-9a39-3952cfaaf377

        :expectedresults: Docker-based content view can be added and then
            removed from the activation key.

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

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

        :id: 0bf0360f-555a-4d79-9a14-71360f56633f

        :expectedresults: Docker-based composite content view can be added and
            then removed from the activation key.

        :caseautomation: notautomated

        :CaseLevel: Integration
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

        :id: 78a65ed3-0dbf-413f-91cf-3a02f7ee12d1

        :expectedresults: Compute Resource can be created and listed.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: 6a22e770-6a9a-48ab-94b6-e991e484812d

        :expectedresults: Compute Resource can be created, listed and its
            attributes can be updated.

        :CaseImportance: Critical
        """
        comp_name = gen_string('alphanumeric')
        with Session(self) as session:
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

    @run_only_on('sat')
    @tier1
    def test_positive_create_external(self):
        """Create a Docker-based Compute Resource using an external
        Docker-enabled system.

        :id: 73ca3ee1-4353-4399-90ba-56560407246e

        :expectedresults: Compute Resource can be created and listed.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: 13d6c7ee-0c90-46cd-8661-73fa1a3c4ef3

        :expectedresults: Compute Resource can be created, listed and its
            attributes can be updated.

        :CaseImportance: Critical
        """
        comp_name = gen_string('alphanumeric')
        with Session(self) as session:
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

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create a Docker-based Compute Resource then delete it.

        :id: 151d5c08-4f66-461d-9535-f904cd26ce49

        :expectedresults: Compute Resource can be created, listed and deleted.

        :CaseImportance: Critical
        """
        comp_name = gen_string('alphanumeric')
        with Session(self) as session:
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
                    self.compute_resource.delete(
                        comp_name, dropdown_present=True)


@run_in_one_thread
class DockerRegistryTestCase(UITestCase):
    """Tests specific to performing CRUD methods against ``Registries``
    repositories.
    """

    @classmethod
    @skip_if_not_set('docker')
    def setUpClass(cls):
        """Skip the tests if docker section is not set in properties file and
        set external docker registry url which can be re-used in tests.
        """
        super(DockerRegistryTestCase, cls).setUpClass()
        cls.url = settings.docker.external_registry_1

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create an external docker registry

        :id: 7d2a2271-801e-454b-af0e-fedf1d96a7d5

        :expectedresults: the external registry is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_registry(
                        session,
                        name=name,
                        url=self.url,
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

        :id: 2b59f929-4a47-4216-b8b3-7f923d8e7de9

        :expectedresults: the external registry is updated with the new name

        :CaseImportance: Critical
        """
        with Session(self) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=self.url,
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

        :id: cf477436-085d-4517-ad86-23e3d254ad70

        :expectedresults: the external registry is updated with the new URL

        :CaseImportance: Critical
        """
        with Session(self) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=self.url,
            )
            try:
                registry_entity = entities.Registry(name=name).search()[0]
                self.assertIsNotNone(self.registry.search(name))
                new_url = settings.docker.external_registry_2
                self.registry.update(name, new_url=new_url)
                self.registry.search_and_click(name)
                self.assertEqual(self.registry.get_element_value(
                    locators['registry.url']), new_url)
            finally:
                registry_entity.delete()

    @run_only_on('sat')
    @tier1
    def test_positive_update_description(self):
        """Create an external docker registry and update its description

        :id: 0ca5e992-b28e-452e-a2be-fca57b4b5195

        :expectedresults: the external registry is updated with the new
            description

        :CaseImportance: Critical
        """
        with Session(self) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=self.url,
                description=gen_string('alphanumeric'),
            )
            try:
                registry_entity = entities.Registry(name=name).search()[0]
                self.assertIsNotNone(self.registry.search(name))
                new_description = gen_string('utf8')
                self.registry.update(name, new_desc=new_description)
                self.registry.search_and_click(name)
                self.assertIsNotNone(self.registry.wait_until_element(
                    locators['registry.description']).text, new_description)
            finally:
                registry_entity.delete()

    @run_only_on('sat')
    @tier1
    def test_positive_update_username(self):
        """Create an external docker registry and update its username

        :id: 9cb24a5a-e383-446e-9b1a-3bf02e0ef439

        :expectedresults: the external registry is updated with the new
            username

        :CaseImportance: Critical
        """
        with Session(self) as session:
            name = gen_string('utf8')
            make_registry(
                session,
                name=name,
                url=self.url,
                username=gen_string('alphanumeric'),
            )
            try:
                registry_entity = entities.Registry(name=name).search()[0]
                self.assertIsNotNone(self.registry.search(name))
                new_username = gen_string('utf8')
                self.registry.update(name, new_username=new_username)
                self.registry.search_and_click(name)
                self.assertIsNotNone(self.registry.wait_until_element(
                    locators['registry.username']).text, new_username)
            finally:
                registry_entity.delete()

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Create an external docker registry and then delete it

        :id: a85d82f5-88b1-4235-8763-1d2f05c8913a

        :expectedresults: The external registry is deleted successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_registry(
                        session,
                        name=name,
                        url=self.url,
                        description=gen_string('utf8'),
                    )
                    self.registry.delete(name)
