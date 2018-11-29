# -*- encoding: utf-8 -*-
"""Unit tests for the Docker feature.

:Requirement: Docker

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice, randint, shuffle
from time import sleep

from fauxfactory import gen_string, gen_url
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.api.utils import promote
from robottelo.cleanup import vm_cleanup
from robottelo.config import settings
from robottelo.constants import DOCKER_REGISTRY_HUB
from robottelo.datafactory import (
    generate_strings_list,
    invalid_docker_upstream_names,
    valid_data_list,
    valid_docker_repository_names,
    valid_docker_upstream_names,
)
from robottelo.decorators import (
    bz_bug_is_open,
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import APITestCase
from robottelo.vm import VirtualMachine


DOCKER_PROVIDER = 'Docker'


def _create_repository(product, name=None, upstream_name=None):
    """Creates a Docker-based repository.

    :param product: A ``Product`` object.
    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name of an existing upstream repository.
        If ``None`` then defaults to ``busybox``.
    :return: A ``Repository`` object.
    """
    if name is None:
        name = choice(generate_strings_list(15, ['numeric', 'html']))
    if upstream_name is None:
        upstream_name = u'busybox'
    return entities.Repository(
        content_type=u'docker',
        docker_upstream_name=upstream_name,
        name=name,
        product=product,
        url=DOCKER_REGISTRY_HUB,
    ).create()


class DockerRepositoryTestCase(APITestCase):
    """Tests specific to performing CRUD methods against ``Docker``
    repositories.
    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create one Docker-type repository

        :id: 3360aab2-74f3-4f6e-a083-46498ceacad2

        :expectedresults: A repository is created with a Docker upstream
            repository.

        :CaseImportance: Critical
        """
        for name in valid_docker_repository_names():
            with self.subTest(name):
                repo = _create_repository(
                    entities.Product(organization=self.org).create(),
                    name,
                )
                self.assertEqual(repo.name, name)
                self.assertEqual(repo.docker_upstream_name, 'busybox')
                self.assertEqual(repo.content_type, 'docker')

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_upstream_name(self):
        """Create a Docker-type repository with a valid docker upstream
        name

        :id: 742a2118-0ab2-4e63-b978-88fe9f52c034

        :expectedresults: A repository is created with the specified upstream
            name.

        :CaseImportance: Critical
        """
        for upstream_name in valid_docker_upstream_names():
            with self.subTest(upstream_name):
                repo = _create_repository(
                    entities.Product(organization=self.org).create(),
                    upstream_name=upstream_name,
                )
                self.assertEqual(repo.docker_upstream_name, upstream_name)
                self.assertEqual(repo.content_type, u'docker')

    @tier1
    @run_only_on('sat')
    def test_negative_create_with_invalid_upstream_name(self):
        """Create a Docker-type repository with a invalid docker
        upstream name.

        :id: 2c5abb4a-e50b-427a-81d2-57eaf8f57a0f

        :expectedresults: A repository is not created and a proper error is
            raised.

        :CaseImportance: Critical
        """
        product = entities.Product(organization=self.org).create()
        for upstream_name in invalid_docker_upstream_names():
            with self.subTest(upstream_name):
                with self.assertRaises(HTTPError):
                    _create_repository(product, upstream_name=upstream_name)

    @tier2
    @run_only_on('sat')
    def test_positive_create_repos_using_same_product(self):
        """Create multiple Docker-type repositories

        :id: 4a6929fc-5111-43ff-940c-07a754828630

        :expectedresults: Multiple docker repositories are created with a
            Docker usptream repository and they all belong to the same product.

        :CaseLevel: Integration
        """
        product = entities.Product(organization=self.org).create()
        for _ in range(randint(2, 5)):
            repo = _create_repository(product)
            product = product.read()
            self.assertIn(repo.id, [repo_.id for repo_ in product.repository])

    @tier2
    @run_only_on('sat')
    def test_positive_create_repos_using_multiple_products(self):
        """Create multiple Docker-type repositories on multiple products

        :id: 5a65d20b-d3b5-4bd7-9c8f-19c8af190558

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to their respective
            products.

        :CaseLevel: Integration
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

    @tier2
    @run_only_on('sat')
    def test_positive_sync(self):
        """Create and sync a Docker-type repository

        :id: 80fbcd84-1c6f-444f-a44e-7d2738a0cba2

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.

        :CaseLevel: Integration
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create()
        )
        repo.sync()
        repo = repo.read()
        self.assertGreaterEqual(repo.content_counts['docker_manifest'], 1)

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Create a Docker-type repository and update its name.

        :id: 7967e6b5-c206-4ad0-bcf5-64a7ce85233b

        :expectedresults: A repository is created with a Docker upstream
            repository and that its name can be updated.

        :CaseImportance: Critical
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())

        # Update the repository name to random value
        for new_name in valid_docker_repository_names():
            with self.subTest(new_name):
                repo.name = new_name
                repo = repo.update()
                self.assertEqual(repo.name, new_name)

    @tier1
    @run_only_on('sat')
    def test_positive_update_upstream_name(self):
        """Create a Docker-type repository and update its upstream name.

        :id: 4e2fb78d-0b6a-4455-8869-8eaf9d4a61b0

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can be updated.

        :CaseImportance: Critical
        """
        new_upstream_name = u'fedora/ssh'
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        self.assertNotEqual(repo.docker_upstream_name, new_upstream_name)

        # Update the repository upstream name
        repo.docker_upstream_name = new_upstream_name
        repo = repo.update()
        self.assertEqual(repo.docker_upstream_name, new_upstream_name)

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1489322)
    def test_positive_update_url(self):
        """Create a Docker-type repository and update its URL.

        :id: 6a588e65-bf1d-4ca9-82ce-591f9070215f

        :expectedresults: A repository is created with a Docker upstream
            repository and that its URL can be updated.

        :BZ: 1489322

        :CaseLevel: Integration
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

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Create and delete a Docker-type repository

        :id: 92df93cb-9de2-40fa-8451-b8c1ba8f45be

        :expectedresults: A repository is created with a Docker upstream
            repository and then deleted.

        :CaseImportance: Critical
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        # Delete it
        repo.delete()
        with self.assertRaises(HTTPError):
            repo.read()

    @tier2
    @run_only_on('sat')
    def test_positive_delete_random_repo(self):
        """Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        :id: cbc2792d-cf81-41f7-8889-001a27e4dd66

        :expectedresults: Random repository can be deleted from random product
            without altering the other products.

        :CaseLevel: Integration
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


class DockerContentViewTestCase(APITestCase):
    """Tests specific to using ``Docker`` repositories with Content Views."""

    @classmethod
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(DockerContentViewTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier2
    @run_only_on('sat')
    def test_positive_add_docker_repo(self):
        """Add one Docker-type repository to a non-composite content view

        :id: a065822f-bb41-4fc9-bf5c-65814ca11b2d

        :expectedresults: A repository is created with a Docker repository and
            the product is added to a non-composite content view

        :CaseLevel: Integration
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

    @tier2
    @run_only_on('sat')
    def test_positive_add_docker_repos(self):
        """Add multiple Docker-type repositories to a
        non-composite content view.

        :id: 08eed081-2003-4475-95ac-553a56b83997

        :expectedresults: Repositories are created with Docker upstream repos
            and the product is added to a non-composite content view.

        :CaseLevel: Integration
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

    @tier2
    @run_only_on('sat')
    def test_positive_add_synced_docker_repo(self):
        """Create and sync a Docker-type repository

        :id: 3c7d6f17-266e-43d3-99f8-13bf0251eca6

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.

        :CaseLevel: Integration
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        repo.sync()
        repo = repo.read()
        self.assertGreaterEqual(repo.content_counts['docker_manifest'], 1)

        # Create content view and associate docker repo
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertIn(repo.id, [repo_.id for repo_ in content_view.repository])

    @tier2
    @run_only_on('sat')
    def test_positive_add_docker_repo_to_ccv(self):
        """Add one Docker-type repository to a composite content view

        :id: fe278275-2bb2-4d68-8624-f0cfd63ecb57

        :expectedresults: A repository is created with a Docker repository and
            the product is added to a content view which is then added to a
            composite content view.

        :CaseLevel: Integration
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

    @tier2
    @run_only_on('sat')
    def test_positive_add_docker_repos_to_ccv(self):
        """Add multiple Docker-type repositories to a composite
        content view.

        :id: 3824ccae-fb59-4f63-a1ab-a4f2419fcadd

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a random number of content
            views which are then added to a composite content view.

        :CaseLevel: Integration
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

    @tier2
    @run_only_on('sat')
    def test_positive_publish_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it once.

        :id: 86a73e96-ead6-41fb-8095-154a0b83e344

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published only once.

        :CaseLevel: Integration
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())

        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertIn(repo.id, [repo_.id for repo_ in content_view.repository])

        # Not published yet?
        content_view = content_view.read()
        self.assertIsNone(content_view.last_published)
        self.assertEqual(float(content_view.next_version), 1.0)

        # Publish it and check that it was indeed published.
        content_view.publish()
        content_view = content_view.read()
        self.assertIsNotNone(content_view.last_published)
        self.assertGreater(float(content_view.next_version), 1.0)

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1217635)
    def test_positive_publish_with_docker_repo_composite(self):
        """Add Docker-type repository to composite content view and
        publish it once.

        :id: 103ebee0-1978-4fc5-a11e-4dcdbf704185

        :expectedresults: One repository is created with an upstream repository
            and the product is added to a content view which is then published
            only once and then added to a composite content view which is also
            published only once.

        :CaseLevel: Integration
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertIn(repo.id, [repo_.id for repo_ in content_view.repository])

        # Not published yet?
        content_view = content_view.read()
        self.assertIsNone(content_view.last_published)
        self.assertEqual(float(content_view.next_version), 1.0)

        # Publish it and check that it was indeed published.
        content_view.publish()
        content_view = content_view.read()
        self.assertIsNotNone(content_view.last_published)
        self.assertGreater(float(content_view.next_version), 1.0)

        # Create composite content view…
        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        comp_content_view.component = [content_view.version[0]]
        comp_content_view = comp_content_view.update(['component'])
        self.assertIn(
            content_view.version[0].id,  # pylint:disable=no-member
            [component.id for component in comp_content_view.component]
        )
        # … publish it…
        comp_content_view.publish()
        # … and check that it was indeed published
        comp_content_view = comp_content_view.read()
        self.assertIsNotNone(comp_content_view.last_published)
        self.assertGreater(float(comp_content_view.next_version), 1.0)

    @tier2
    @run_only_on('sat')
    def test_positive_publish_multiple_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it
        multiple times.

        :id: e2caad64-e9f4-422d-a1ab-f64c286d82ff

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published multiple times.

        :CaseLevel: Integration
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(
            [repo.id], [repo_.id for repo_ in content_view.repository])
        self.assertIsNone(content_view.read().last_published)

        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            content_view.publish()
        content_view = content_view.read()
        self.assertIsNotNone(content_view.last_published)
        self.assertEqual(len(content_view.version), publish_amount)

    @tier2
    @run_only_on('sat')
    def test_positive_publish_multiple_with_docker_repo_composite(self):
        """Add Docker-type repository to content view and publish it
        multiple times.

        :id: 77a5957a-7415-41c3-be68-fa706fee7c98

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            added to a composite content view which is then published multiple
            times.

        :CaseLevel: Integration
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
        content_view = entities.ContentView(
            composite=False,
            organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        self.assertEqual(
            [repo.id], [repo_.id for repo_ in content_view.repository])
        self.assertIsNone(content_view.read().last_published)

        content_view.publish()
        content_view = content_view.read()
        self.assertIsNotNone(content_view.last_published)

        comp_content_view = entities.ContentView(
            composite=True,
            organization=self.org,
        ).create()
        comp_content_view.component = [content_view.version[0]]
        comp_content_view = comp_content_view.update(['component'])
        self.assertEqual(
            [content_view.version[0].id],
            [comp.id for comp in comp_content_view.component],
        )
        self.assertIsNone(comp_content_view.last_published)

        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            comp_content_view.publish()
        comp_content_view = comp_content_view.read()
        self.assertIsNotNone(comp_content_view.last_published)
        self.assertEqual(len(comp_content_view.version), publish_amount)

    @tier2
    @run_only_on('sat')
    def test_positive_promote_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it.
        Then promote it to the next available lifecycle-environment.

        :id: 5ab7d7f1-fb13-4b83-b228-a6293be36195

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environment.

        :CaseLevel: Integration
        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        repo = _create_repository(
            entities.Product(organization=self.org).create())

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

    @tier2
    @run_only_on('sat')
    def test_positive_promote_multiple_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it.
        Then promote it to multiple available lifecycle-environments.

        :id: 7b0cbc95-5f63-47f3-9048-e6917078be73

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environments.

        :CaseLevel: Integration
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())

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

    @tier2
    @run_only_on('sat')
    def test_positive_promote_with_docker_repo_composite(self):
        """Add Docker-type repository to content view and publish it.
        Then add that content view to composite one. Publish and promote that
        composite content view to the next available lifecycle-environment.

        :id: e903c7b2-7722-4a9e-bb69-99bbd3c23946

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environment.

        :CaseLevel: Integration
        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        repo = _create_repository(
            entities.Product(organization=self.org).create())
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

    @upgrade
    @tier2
    @run_only_on('sat')
    def test_positive_promote_multiple_with_docker_repo_composite(self):
        """Add Docker-type repository to content view and publish it.
        Then add that content view to composite one. Publish and promote that
        composite content view to the multiple available lifecycle-environments

        :id: 91ac0f4a-8974-47e2-a1d6-7d734aa4ad46

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environments.

        :CaseLevel: Integration
        """
        repo = _create_repository(
            entities.Product(organization=self.org).create())
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
            self.assertEqual(len(comp_cvv.read().environment), i + 1)

    @tier2
    @upgrade
    @run_only_on('sat')
    def test_positive_name_pattern_change(self):
        """Promote content view with Docker repository to lifecycle environment.
        Change registry name pattern for that environment. Verify that repository
        name on product changed according to new pattern.

        :id: cc78d82d-027b-4cb7-92c5-dcccf9b592ea

        :expectedresults: Container repository name is changed
            according to new pattern.

        :CaseLevel: Integration
        """
        pattern_prefix = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = ("{}-<%= organization.label %>"
                       "/<%= repository.docker_upstream_name %>").format(
                pattern_prefix)

        repo = _create_repository(
                entities.Product(organization=self.org).create(),
                upstream_name=docker_upstream_name)
        repo.sync()
        content_view = entities.ContentView(
                composite=False,
                organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(cvv, lce.id)
        lce.registry_name_pattern = new_pattern
        lce = lce.update(['registry_name_pattern'])
        repos = entities.Repository(organization=self.org).search(
                query={'environment_id': lce.id})

        expected_pattern = "{}-{}/{}".format(pattern_prefix, self.org.label,
                                             docker_upstream_name).lower()
        self.assertEqual(lce.registry_name_pattern, new_pattern)
        self.assertEqual(repos[0].container_repository_name, expected_pattern)

    @tier2
    @run_only_on('sat')
    def test_positive_product_name_change_after_promotion(self):
        """Promote content view with Docker repository to lifecycle environment.
        Change product name. Verify that repository name on product changed
        according to new pattern.

        :id: 4ff21344-9ee6-4e17-9a88-0230e7cdd586

        :expectedresults: Container repository name is changed
            according to new pattern.

        :CaseLevel: Integration
        """
        old_prod_name = gen_string('alpha', 5)
        new_prod_name = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = "<%= organization.label %>/<%= product.name %>"

        prod = entities.Product(organization=self.org, name=old_prod_name).create()
        repo = _create_repository(prod, upstream_name=docker_upstream_name)
        repo.sync()
        content_view = entities.ContentView(
                composite=False,
                organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        lce.registry_name_pattern = new_pattern
        lce = lce.update(['registry_name_pattern'])
        promote(cvv, lce.id)
        prod.name = new_prod_name
        prod.update(['name'])
        repos = entities.Repository(organization=self.org).search(
                query={'environment_id': lce.id})

        expected_pattern = "{}/{}".format(self.org.label, old_prod_name).lower()
        self.assertEqual(repos[0].container_repository_name, expected_pattern)

        content_view.publish()
        cvv = content_view.read().version[-1]
        promote(cvv, lce.id)
        repos = entities.Repository(organization=self.org).search(
                query={'environment_id': lce.id})

        expected_pattern = "{}/{}".format(self.org.label, new_prod_name).lower()
        self.assertEqual(repos[0].container_repository_name, expected_pattern)

    @tier2
    @run_only_on('sat')
    def test_positive_repo_name_change_after_promotion(self):
        """Promote content view with Docker repository to lifecycle environment.
        Change repository name. Verify that Docker repository name on product
        changed according to new pattern.

        :id: 304ae909-dc67-4a7e-80e1-96b45354e5a6

        :expectedresults: Container repository name is changed
            according to new pattern.

        :CaseLevel: Integration
        """
        old_repo_name = gen_string('alpha', 5)
        new_repo_name = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = "<%= organization.label %>/<%= repository.name %>"

        repo = _create_repository(
                entities.Product(organization=self.org).create(),
                name=old_repo_name, upstream_name=docker_upstream_name)
        repo.sync()
        content_view = entities.ContentView(
                composite=False,
                organization=self.org,
        ).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        lce.registry_name_pattern = new_pattern
        lce = lce.update(['registry_name_pattern'])
        promote(cvv, lce.id)
        repo.name = new_repo_name
        repo.update(['name'])
        repos = entities.Repository(organization=self.org).search(
                query={'environment_id': lce.id})

        expected_pattern = "{}/{}".format(self.org.label, old_repo_name).lower()
        self.assertEqual(repos[0].container_repository_name, expected_pattern)

        content_view.publish()
        cvv = content_view.read().version[-1]
        promote(cvv, lce.id)
        repos = entities.Repository(organization=self.org).search(
                query={'environment_id': lce.id})

        expected_pattern = "{}/{}".format(self.org.label, new_repo_name).lower()
        self.assertEqual(repos[0].container_repository_name, expected_pattern)

    @tier2
    @run_only_on('sat')
    def test_negative_set_non_unique_name_pattern_and_promote(self):
        """Set registry name pattern to one that does not guarantee uniqueness.
        Try to promote content view with multiple Docker repositories to
        lifecycle environment. Verify that content has not been promoted.

        :id: baae1ec2-35e8-4122-8fac-135c987139d3

        :expectedresults: Content view is not promoted

        :CaseLevel: Integration
        """
        docker_upstream_names = ['hello-world', 'alpine']
        new_pattern = "<%= organization.label %>"

        lce = entities.LifecycleEnvironment(organization=self.org).create()
        lce.registry_name_pattern = new_pattern
        lce = lce.update(['registry_name_pattern'])
        prod = entities.Product(organization=self.org).create()
        repos = []
        for docker_name in docker_upstream_names:
            repo = _create_repository(
                prod, upstream_name=docker_name)
            repo.sync()
            repos.append(repo)
        content_view = entities.ContentView(
                composite=False,
                organization=self.org,
        ).create()
        content_view.repository = repos
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        with self.assertRaises(HTTPError):
            promote(cvv, lce.id)

    @tier2
    @run_only_on('sat')
    def test_negative_promote_and_set_non_unique_name_pattern(self):
        """Promote content view with multiple Docker repositories to
        lifecycle environment. Set registry name pattern to one that
        does not guarantee uniqueness. Verify that pattern has not been
        changed.

        :id: 945b3301-c523-4026-9753-df3577888319

        :expectedresults: Registry name pattern is not changed

        :CaseLevel: Integration
        """
        docker_upstream_names = ['hello-world', 'alpine']
        new_pattern = "<%= organization.label %>"

        prod = entities.Product(organization=self.org).create()
        repos = []
        for docker_name in docker_upstream_names:
            repo = _create_repository(
                    prod, upstream_name=docker_name)
            repo.sync()
            repos.append(repo)
        content_view = entities.ContentView(
                composite=False,
                organization=self.org,
        ).create()
        content_view.repository = repos
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        promote(cvv, lce.id)
        with self.assertRaises(HTTPError):
            lce.registry_name_pattern = new_pattern
            lce.update(['registry_name_pattern'])


class DockerActivationKeyTestCase(APITestCase):
    """Tests specific to adding ``Docker`` repositories to Activation Keys."""

    @classmethod
    def setUpClass(cls):
        """Create necessary objects which can be re-used in tests."""
        super(DockerActivationKeyTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.lce = entities.LifecycleEnvironment(organization=cls.org).create()
        cls.repo = _create_repository(
            entities.Product(organization=cls.org).create())
        content_view = entities.ContentView(
            composite=False,
            organization=cls.org,
        ).create()
        content_view.repository = [cls.repo]
        cls.content_view = content_view.update(['repository'])
        cls.content_view.publish()
        cls.cvv = content_view.read().version[0].read()
        promote(cls.cvv, cls.lce.id)

    @tier2
    @run_only_on('sat')
    def test_positive_add_docker_repo_cv(self):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then create an activation key and associate it with the
        Docker content view.

        :id: ce4ae928-49c7-4782-a032-08885050dd83

        :expectedresults: Docker-based content view can be added to activation
            key

        :CaseLevel: Integration
        """
        ak = entities.ActivationKey(
            content_view=self.content_view,
            environment=self.lce,
            organization=self.org,
        ).create()
        self.assertEqual(ak.content_view.id, self.content_view.id)
        self.assertEqual(ak.content_view.read().repository[0].id, self.repo.id)

    @tier2
    @run_only_on('sat')
    def test_positive_remove_docker_repo_cv(self):
        """Add Docker-type repository to a non-composite content view
        and publish it. Create an activation key and associate it with the
        Docker content view. Then remove this content view from the activation
        key.

        :id: 6a887a67-6700-47ac-9230-deaa0e382f22

        :expectedresults: Docker-based content view can be added and then
            removed from the activation key.

        :CaseLevel: Integration
        """
        ak = entities.ActivationKey(
            content_view=self.content_view,
            environment=self.lce,
            organization=self.org,
        ).create()
        self.assertEqual(ak.content_view.id, self.content_view.id)
        ak.content_view = None
        self.assertIsNone(ak.update(['content_view']).content_view)

    @tier2
    @run_only_on('sat')
    def test_positive_add_docker_repo_ccv(self):
        """Add Docker-type repository to a non-composite content view and
        publish it. Then add this content view to a composite content view and
        publish it. Create an activation key and associate it with the
        composite Docker content view.

        :id: 2fc8a462-9d91-48bc-8e32-7ff8f769b9e4

        :expectedresults: Docker-based content view can be added to activation
            key

        :CaseLevel: Integration
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
            organization=self.org,
        ).create()
        self.assertEqual(ak.content_view.id, comp_content_view.id)

    @tier2
    @run_only_on('sat')
    def test_positive_remove_docker_repo_ccv(self):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then add this content view to a composite content view
        and publish it. Create an activation key and associate it with the
        composite Docker content view. Then, remove the composite content view
        from the activation key.

        :id: f3542272-13db-4a49-bc27-d1137172df41

        :expectedresults: Docker-based composite content view can be added and
            then removed from the activation key.

        :CaseLevel: Integration
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
            organization=self.org,
        ).create()
        self.assertEqual(ak.content_view.id, comp_content_view.id)
        ak.content_view = None
        self.assertIsNone(ak.update(['content_view']).content_view)


class DockerComputeResourceTestCase(APITestCase):
    """Tests specific to managing Docker-based Compute Resources."""

    @classmethod
    @skip_if_not_set('docker')
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerComputeResourceTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    @tier2
    @run_only_on('sat')
    def test_positive_create_internal(self):
        """Create a Docker-based Compute Resource in the Satellite 6
        instance.

        :id: 146dd836-83c7-4f9c-937e-791162ea106e

        :expectedresults: Compute Resource can be created and listed.

        :CaseLevel: Integration
        """
        for name in valid_data_list():
            with self.subTest(name):
                compute_resource = entities.DockerComputeResource(
                    name=name,
                    url=settings.docker.get_unix_socket_url(),
                ).create()
                self.assertEqual(compute_resource.name, name)
                self.assertEqual(compute_resource.provider, DOCKER_PROVIDER)
                self.assertEqual(
                    compute_resource.url,
                    settings.docker.get_unix_socket_url()
                )

    @tier2
    @run_only_on('sat')
    def test_positive_update_internal(self):
        """Create a Docker-based Compute Resource in the Satellite 6
        instance then edit its attributes.

        :id: 5590621f-063c-4e32-80cb-ebe634dbadaa

        :expectedresults: Compute Resource can be created, listed and its
            attributes can be updated.

        :CaseLevel: Integration
        """
        for url in (settings.docker.external_url,
                    settings.docker.get_unix_socket_url()):
            with self.subTest(url):
                compute_resource = entities.DockerComputeResource(
                    organization=[self.org],
                    url=url,
                ).create()
                self.assertEqual(compute_resource.url, url)
                compute_resource.url = gen_url()
                self.assertEqual(
                    compute_resource.url,
                    compute_resource.update(['url']).url,
                )

    @skip_if_bug_open('bugzilla', 1466240)
    @skip_if_bug_open('bugzilla', 1478966)
    @tier2
    @run_only_on('sat')
    def test_positive_list_containers(self):
        """Create a Docker-based Compute Resource in the Satellite 6
        instance then list its running containers.

        :id: 96bfba71-03e5-4d80-bd27-fc5db8e00b50

        :expectedresults: Compute Resource can be created and existing
            instances can be listed.

        :CaseLevel: Integration
        """
        # Instantiate and setup a docker host VM + compute resource
        docker_image = settings.docker.docker_image
        with VirtualMachine(
            source_image=docker_image,
            tag=u'docker'
        ) as docker_host:
            docker_host.create()
            docker_host.install_katello_ca()
            url = 'http://{0}:2375'.format(docker_host.ip_addr)
            compute_resource = entities.DockerComputeResource(
                organization=[self.org],
                url=url,
            ).create()
            self.assertEqual(compute_resource.url, url)
            self.assertEqual(len(entities.AbstractDockerContainer(
                compute_resource=compute_resource).search()), 0)
            container = entities.DockerHubContainer(
                command='top',
                compute_resource=compute_resource,
                organization=[self.org],
            ).create()
            result = entities.AbstractDockerContainer(
                compute_resource=compute_resource).search()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].name, container.name)

    @tier2
    @run_only_on('sat')
    def test_positive_create_external(self):
        """Create a Docker-based Compute Resource using an external
        Docker-enabled system.

        :id: 91ae6374-82de-424e-aa4c-e19209acd5b5

        :expectedresults: Compute Resource can be created and listed.

        :CaseLevel: Integration
        """
        for name in valid_data_list():
            with self.subTest(name):
                compute_resource = entities.DockerComputeResource(
                    name=name,
                    url=settings.docker.external_url,
                ).create()
                self.assertEqual(compute_resource.name, name)
                self.assertEqual(compute_resource.provider, DOCKER_PROVIDER)
                self.assertEqual(
                    compute_resource.url, settings.docker.external_url)

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Create a Docker-based Compute Resource then delete it.

        :id: f1f23c1e-6481-46b5-9485-787ae18d9ed5

        :expectedresults: Compute Resource can be created, listed and deleted.

        :CaseImportance: Critical
        """
        for url in (settings.docker.external_url,
                    settings.docker.get_unix_socket_url()):
            with self.subTest(url):
                resource = entities.DockerComputeResource(url=url).create()
                self.assertEqual(resource.url, url)
                self.assertEqual(resource.provider, DOCKER_PROVIDER)
                resource.delete()
                with self.assertRaises(HTTPError):
                    resource.read()


class DockerContainerTestCase(APITestCase):
    """Tests specific to using ``Containers`` in an external Docker
    Compute Resource
    """

    @classmethod
    @skip_if_not_set('docker')
    @skip_if_bug_open('bugzilla', 1478966)
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerContainerTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()

    def setUp(self):
        """Instantiate and setup a docker host VM + compute resource"""
        docker_image = settings.docker.docker_image
        self.docker_host = VirtualMachine(
            source_image=docker_image,
            tag=u'docker'
        )
        self.addCleanup(vm_cleanup, self.docker_host)
        self.docker_host.create()
        self.docker_host.install_katello_ca()
        self.compute_resource = entities.DockerComputeResource(
            name=gen_string('alpha'),
            organization=[self.org],
            url='http://{0}:2375'.format(self.docker_host.ip_addr),
        ).create()

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_compresource(self):
        """Create containers for docker compute resources

        :id: c57c261c-39cf-4a71-93a4-e01e3ec368a7

        :expectedresults: The docker container is created

        :CaseLevel: Integration
        """
        container = entities.DockerHubContainer(
            command='top',
            compute_resource=self.compute_resource,
            organization=[self.org],
        ).create()
        self.assertEqual(
            container.compute_resource.read().name,
            self.compute_resource.name,
        )

    @upgrade
    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1282431)
    @skip_if_bug_open('bugzilla', 1347658)
    def test_positive_create_using_cv(self):
        """Create docker container using custom content view, lifecycle
        environment and docker repository for docker compute resource

        :id: 69f29cc8-45e0-4b3a-b001-2842c45617e0

        :expectedresults: The docker container is created

        :CaseLevel: Integration
        """
        lce = entities.LifecycleEnvironment(organization=self.org).create()
        repo = _create_repository(
            entities.Product(organization=self.org).create(),
            upstream_name='centos',
        )
        repo.sync()
        content_view = entities.ContentView(organization=self.org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        cvv = content_view.read().version[0].read()
        promote(cvv, lce.id)

        # publishing takes few seconds sometimes
        retries = 10 if bz_bug_is_open(1452149) else 1
        for i in range(retries):
            try:
                container = entities.DockerHubContainer(
                    command='top',
                    compute_resource=self.compute_resource,
                    organization=[self.org],
                    repository_name=repo.container_repository_name,
                    tag='latest',
                    tty='yes',
                ).create()
            except HTTPError:
                if i == retries - 1:
                    raise
                else:
                    sleep(2)
                    pass
        self.assertEqual(
            container.compute_resource.read().name,
            self.compute_resource.name
        )
        self.assertEqual(
            container.repository_name,
            repo.container_repository_name
        )
        self.assertEqual(container.tag, 'latest')

    @tier2
    @run_only_on('sat')
    def test_positive_power_on_off(self):
        """Create containers for docker compute resource,
        then power them on and finally power them off

        :id: 6271afcf-698b-47e2-af80-1ce38c111742

        :expectedresults: The docker container is created and the power status
            is showing properly

        :CaseLevel: Integration
        """
        container = entities.DockerHubContainer(
            command='top',
            compute_resource=self.compute_resource,
            organization=[self.org],
        ).create()
        self.assertEqual(
            container.compute_resource.read().url,
            self.compute_resource.url,
        )
        self.assertTrue(container.power(
            data={u'power_action': 'status'})['running'])
        container.power(data={u'power_action': 'stop'})
        self.assertFalse(container.power(
            data={u'power_action': 'status'})['running'])

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1479291)
    def test_positive_read_container_log(self):
        """Create containers for docker compute resource and read their logs

        :id: ffeb3c57-c7dc-4cee-a087-b52daedd4485

        :expectedresults: The docker container is created and its log can be
            read

        :CaseLevel: Integration
        """
        container = entities.DockerHubContainer(
            command='date',
            compute_resource=self.compute_resource,
            organization=[self.org],
        ).create()
        self.assertTrue(container.logs()['logs'])

    @upgrade
    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_create_with_external_registry(self):
        """Create a container pulling an image from a custom external
        registry

        :id: 04506604-637f-473b-a764-825c61067b1b

        :expectedresults: The docker container is created and the image is
            pulled from the external registry

        :CaseLevel: Integration
        """
        repo_name = 'rhel'
        registry = entities.Registry(
            url=settings.docker.external_registry_1).create()
        try:
            container = entities.DockerRegistryContainer(
                compute_resource=self.compute_resource,
                organization=[self.org],
                registry=registry,
                repository_name=repo_name,
            ).create()
            self.assertEqual(container.registry.id, registry.id)
            self.assertEqual(container.repository_name, repo_name)
        finally:
            registry.delete()

    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Delete containers using docker compute resource

        :id: 12efdf50-9494-48c3-a181-01c495b48c19

        :expectedresults: The docker containers are deleted

        :CaseImportance: Critical
        """
        container = entities.DockerHubContainer(
            command='top',
            compute_resource=self.compute_resource,
            organization=[self.org],
        ).create()
        container.delete()
        with self.assertRaises(HTTPError):
            container.read()


@skip_if_bug_open('bugzilla', 1414821)
class DockerUnixSocketContainerTestCase(APITestCase):
    """Tests specific to using ``Containers`` in local unix-socket
    Docker Compute Resource
    """

    @classmethod
    @skip_if_not_set('docker')
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerUnixSocketContainerTestCase, cls).setUpClass()
        cls.org = entities.Organization().create()
        cls.compute_resource = entities.DockerComputeResource(
            name=gen_string('alpha'),
            organization=[cls.org],
            url=settings.docker.get_unix_socket_url(),
        ).create()

    @tier2
    @run_only_on('sat')
    def test_positive_create_with_compresource(self):
        """Create containers for docker compute resources

        :id: 91a8a159-0f00-44b6-8ab7-dc8b1a5f1f37

        :expectedresults: The docker container is created

        :CaseLevel: Integration
        """
        container = entities.DockerHubContainer(
            command='top',
            compute_resource=self.compute_resource,
            organization=[self.org],
        ).create()
        self.assertEqual(
            container.compute_resource.read().name,
            self.compute_resource.name,
        )


@run_in_one_thread
class DockerRegistryTestCase(APITestCase):
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

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create an external docker registry

        :id: 8212ab15-8298-4a46-88ba-eaf71069e068

        :expectedresults: External registry is created successfully

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                description = gen_string('alphanumeric')
                registry = entities.Registry(
                    description=description,
                    name=name,
                    url=self.url,
                ).create()
                try:
                    self.assertEqual(registry.name, name)
                    self.assertEqual(registry.url, self.url)
                    self.assertEqual(registry.description, description)
                finally:
                    registry.delete()

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Create an external docker registry and update its name

        :id: fdd9c76b-43a7-4ece-8975-3b08241134c8

        :expectedresults: the external registry is updated with the new name

        :CaseImportance: Critical
        """
        registry = entities.Registry(
            name=gen_string('alpha'), url=self.url).create()
        try:
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    registry.name = new_name
                    registry = registry.update()
                    self.assertEqual(registry.name, new_name)
        finally:
            registry.delete()

    @tier2
    @run_only_on('sat')
    def test_positive_update_url(self):
        """Create an external docker registry and update its URL

        :id: a3701f92-0846-4d1b-b691-48cdc85c1341

        :expectedresults: the external registry is updated with the new URL

        :CaseLevel: Integration
        """
        new_url = settings.docker.external_registry_2
        registry = entities.Registry(url=self.url).create()
        try:
            self.assertEqual(registry.url, self.url)
            registry.url = new_url
            registry = registry.update()
            self.assertEqual(registry.url, new_url)
        finally:
            registry.delete()

    @tier2
    @run_only_on('sat')
    def test_positive_update_description(self):
        """Create an external docker registry and update its description

        :id: 7eb08208-8b45-444f-b365-2d6f6e417533

        :expectedresults: the external registry is updated with the new
            description

        :CaseLevel: Integration
        """
        registry = entities.Registry(url=self.url).create()
        try:
            for new_desc in valid_data_list():
                with self.subTest(new_desc):
                    registry.description = new_desc
                    registry = registry.update()
                    self.assertEqual(registry.description, new_desc)
        finally:
            registry.delete()

    @tier2
    @run_only_on('sat')
    def test_positive_update_username(self):
        """Create an external docker registry and update its username

        :id: 7da17c30-4582-4e27-a080-e446e6eec176

        :expectedresults: the external registry is updated with the new
            username

        :CaseLevel: Integration
        """
        username = gen_string('alpha')
        new_username = gen_string('alpha')
        registry = entities.Registry(
            username=username,
            password=gen_string('alpha'),
            url=self.url,
        ).create()
        try:
            self.assertEqual(registry.username, username)
            registry.username = new_username
            registry = registry.update()
            self.assertEqual(registry.username, new_username)
        finally:
            registry.delete()

    @upgrade
    @tier1
    @run_only_on('sat')
    def test_positive_delete(self):
        """Create an external docker registry and then delete it

        :id: 1a215237-91b5-4fcc-8c18-a9944068ac88

        :expectedresults: The external registry is deleted successfully

        :CaseImportance: Critical
        """
        registry = entities.Registry(url=self.url).create()
        registry.delete()
        with self.assertRaises(HTTPError):
            registry.read()
