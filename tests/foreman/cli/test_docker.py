# pylint: attribute-defined-outside-init
"""Unit tests for the Docker feature.

:Requirement: Docker

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice, randint
from time import sleep

from fauxfactory import gen_alpha, gen_string, gen_url

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.docker import Docker
from robottelo.cli.factory import (
    make_activation_key,
    make_compute_resource,
    make_container,
    make_content_view,
    make_lifecycle_environment,
    make_org,
    make_product_wait,  # workaround for BZ 1332650
    make_registry,
    make_repository,
)
from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.computeresource import ComputeResource
from robottelo.cli.contentview import ContentView
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.config import settings
from robottelo.constants import (
    DOCKER_REGISTRY_HUB,
    DOCKER_RH_REGISTRY_UPSTREAM_NAME,
)
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
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade,
)
from robottelo.test import CLITestCase
from robottelo.vm import VirtualMachine

DOCKER_PROVIDER = 'Docker'
REPO_CONTENT_TYPE = 'docker'
REPO_UPSTREAM_NAME = 'busybox'


def _make_docker_repo(product_id, name=None, upstream_name=None, url=None):
    """Creates a Docker-based repository.

    :param product_id: ID of the ``Product``.
    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name of an existing upstream repository.
        If ``None`` then defaults to ``busybox``.
    :param str url: URL of repository. If ``None`` then defaults to
        DOCKER_REGISTRY_HUB constant.
    :return: A ``Repository`` object.
    """
    return make_repository({
        'content-type': REPO_CONTENT_TYPE,
        'docker-upstream-name': upstream_name or REPO_UPSTREAM_NAME,
        'name': name or choice(generate_strings_list(15, ['numeric', 'html'])),
        'product-id': product_id,
        'url': url or DOCKER_REGISTRY_HUB,
    })


class DockerManifestTestCase(CLITestCase):
    """Tests related to docker manifest command"""

    @tier2
    @skip_if_bug_open('bugzilla', 1658274)
    def test_positive_read_docker_tags(self):
        """docker manifest displays tags information for a docker manifest

        :id: 59b605b5-ac2d-46e3-a85e-a259e78a07a8

        :expectedresults: docker manifest displays tags info for a docker
            manifest

        :CaseLevel: Integration
        """
        organization = make_org()
        product = make_product_wait({
            u'organization-id': organization['id'],
        })
        repository = make_repository({
            u'content-type': REPO_CONTENT_TYPE,
            u'docker-upstream-name': REPO_UPSTREAM_NAME,
            u'product-id': product['id'],
            u'url': DOCKER_REGISTRY_HUB,
        })
        Repository.synchronize({'id': repository['id']})
        # Grab all available manifests related to repository
        manifests_list = Docker.manifest.list({
            u'repository-id': repository['id'],
        })
        # Some manifests do not have tags associated with it, ignore those
        # because we want to check the tag information
        manifests = [
            m_iter for m_iter in manifests_list if not m_iter['tag-name'] == ''
        ]
        self.assertTrue(manifests)
        tags_list = Docker.tag.list({
            u'repository-id': repository['id'],
        })
        # Extract tag names for the repository out of docker tag list
        repo_tag_names = [tag['tag'] for tag in tags_list]
        for manifest in manifests:
            manifest_info = Docker.manifest.info({'id': manifest['id']})
            # Check that manifest's tag is listed in tags for the repository
            self.assertIn(manifest_info['tag-name'], repo_tag_names)


class DockerRepositoryTestCase(CLITestCase):
    """Tests specific to performing CRUD methods against ``Docker``
    repositories.
    """

    @classmethod
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerRepositoryTestCase, cls).setUpClass()
        cls.org_id = make_org()['id']

    @tier1
    @run_only_on('sat')
    def test_positive_create_with_name(self):
        """Create one Docker-type repository

        :id: e82a36c8-3265-4c10-bafe-c7e07db3be78

        :expectedresults: A repository is created with a Docker upstream
         repository.

        :CaseImportance: Critical
        """
        for name in valid_docker_repository_names():
            with self.subTest(name):
                repo = _make_docker_repo(
                    make_product_wait({'organization-id': self.org_id})['id'],
                    name,
                )
                self.assertEqual(repo['name'], name)
                self.assertEqual(
                    repo['upstream-repository-name'], REPO_UPSTREAM_NAME)
                self.assertEqual(repo['content-type'], REPO_CONTENT_TYPE)

    @tier1
    @run_only_on('sat')
    def test_positive_create_repos_using_same_product(self):
        """Create multiple Docker-type repositories

        :id: 6dd25cf4-f8b6-4958-976a-c116daf27b44

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to the same product.

        :CaseImportance: Critical
        """
        product = make_product_wait({'organization-id': self.org_id})
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

    @tier1
    @run_only_on('sat')
    def test_positive_create_repos_using_multiple_products(self):
        """Create multiple Docker-type repositories on multiple
        products.

        :id: 43f4ab0d-731e-444e-9014-d663ff945f36

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to their respective
            products.

        :CaseImportance: Critical
        """
        for _ in range(randint(2, 5)):
            product = make_product_wait({'organization-id': self.org_id})
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

    @tier1
    @run_only_on('sat')
    def test_positive_sync(self):
        """Create and sync a Docker-type repository

        :id: bff1d40e-181b-48b2-8141-8c86e0db62a2

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.

        :CaseImportance: Critical
        """
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])
        self.assertEqual(
            int(repo['content-counts']['container-image-manifests']), 0)
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertGreaterEqual(
            int(repo['content-counts']['container-image-manifests']), 1)

    @tier1
    @run_only_on('sat')
    def test_positive_update_name(self):
        """Create a Docker-type repository and update its name.

        :id: 8b3a8496-e9bd-44f1-916f-6763a76b9b1b

        :expectedresults: A repository is created with a Docker upstream
            repository and that its name can be updated.

        :CaseImportance: Critical
        """
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])
        for new_name in valid_docker_repository_names():
            with self.subTest(new_name):
                Repository.update({
                    'id': repo['id'],
                    'new-name': new_name,
                    'url': repo['url'],
                })
                repo = Repository.info({'id': repo['id']})
                self.assertEqual(repo['name'], new_name)

    @tier1
    @run_only_on('sat')
    def test_positive_update_upstream_name(self):
        """Create a Docker-type repository and update its upstream name.

        :id: 1a6985ed-43ec-4ea6-ba27-e3870457ac56

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can be updated.

        :CaseImportance: Critical
        """
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])

        for new_upstream_name in valid_docker_upstream_names():
            with self.subTest(new_upstream_name):
                Repository.update({
                    'docker-upstream-name': new_upstream_name,
                    'id': repo['id'],
                    'url': repo['url'],
                })
                repo = Repository.info({'id': repo['id']})
                self.assertEqual(
                    repo['upstream-repository-name'],
                    new_upstream_name)

    @tier1
    @run_only_on('sat')
    def test_negative_update_upstream_name(self):
        """Attempt to update upstream name for a Docker-type repository.

        :id: 798651af-28b2-4907-b3a7-7c560bf66c7c

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can not be updated with
            invalid values.

        :CaseImportance: Critical
        """
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])

        for new_upstream_name in invalid_docker_upstream_names():
            with self.subTest(new_upstream_name):
                with self.assertRaises(CLIReturnCodeError) as context:
                    Repository.update({
                        'docker-upstream-name': new_upstream_name,
                        'id': repo['id'],
                        'url': repo['url'],
                    })
                self.assertIn(
                    'Validation failed: Docker upstream name',
                    str(context.exception)
                )

    @skip_if_not_set('docker')
    @tier1
    def test_positive_create_with_long_upstream_name(self):
        """Create a docker repository with upstream name longer than 30
        characters

        :id: 4fe47c02-a8bd-4630-9102-189a9d268b83

        :customerscenario: true

        :BZ: 1424689

        :expectedresults: docker repository is successfully created

        :CaseImportance: Critical
        """
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'],
            upstream_name=DOCKER_RH_REGISTRY_UPSTREAM_NAME,
            url=settings.docker.external_registry_1,
        )
        self.assertEqual(
            repo['upstream-repository-name'], DOCKER_RH_REGISTRY_UPSTREAM_NAME)

    @skip_if_not_set('docker')
    @tier1
    def test_positive_update_with_long_upstream_name(self):
        """Create a docker repository and update its upstream name with longer
        than 30 characters value

        :id: 97260cce-9677-4a3e-942b-e95e2714500a

        :BZ: 1424689

        :expectedresults: docker repository is successfully updated

        :CaseImportance: Critical
        """
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])
        Repository.update({
            'docker-upstream-name': DOCKER_RH_REGISTRY_UPSTREAM_NAME,
            'id': repo['id'],
            'url': settings.docker.external_registry_1,
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(
            repo['upstream-repository-name'], DOCKER_RH_REGISTRY_UPSTREAM_NAME)

    @tier1
    @run_only_on('sat')
    def test_positive_update_url(self):
        """Create a Docker-type repository and update its URL.

        :id: 73caacd4-7f17-42a7-8d93-3dee8b9341fa

        :expectedresults: A repository is created with a Docker upstream
            repository and that its URL can be updated.

        :CaseImportance: Critical
        """
        new_url = gen_url()
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])
        Repository.update({
            'id': repo['id'],
            'url': new_url,
        })
        repo = Repository.info({'id': repo['id']})
        self.assertEqual(repo['url'], new_url)

    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_id(self):
        """Create and delete a Docker-type repository

        :id: ab1e8228-92a8-45dc-a863-7181711f2745

        :expectedresults: A repository with a upstream repository is created
            and then deleted.

        :CaseImportance: Critical
        """
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])
        Repository.delete({'id': repo['id']})
        with self.assertRaises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_delete_random_repo_by_id(self):
        """Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        :id: d4db5eaa-7379-4788-9b72-76f2589d8f20

        :expectedresults: Random repository can be deleted from random product
            without altering the other products.

        :CaseImportance: Critical
        """
        products = [
            make_product_wait({'organization-id': self.org_id})
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

    def _create_and_associate_repo_with_cv(self):
        """Create a Docker-based repository and content view and associate
        them.
        """
        self.repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])
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
                in self.content_view['container-image-repositories']
            ],
        )

    @tier1
    @run_only_on('sat')
    def test_positive_add_docker_repo_by_id(self):
        """Add one Docker-type repository to a non-composite content view

        :id: 87d6c7bb-92f8-4a32-8ad2-2a1af896500b

        :expectedresults: A repository is created with a Docker repository and
            the product is added to a non-composite content view

        :CaseImportance: Critical
        """
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])
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
            [repo_['id'] for repo_ in
                content_view['container-image-repositories']],
        )

    @tier1
    @run_only_on('sat')
    def test_positive_add_docker_repos_by_id(self):
        """Add multiple Docker-type repositories to a non-composite CV.

        :id: 2eb19e28-a633-4c21-9469-75a686c83b34

        :expectedresults: Repositories are created with Docker upstream
            repositories and the product is added to a non-composite content
            view.

        :CaseImportance: Critical
        """
        product = make_product_wait({'organization-id': self.org_id})
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
            set([repo['id'] for repo in
                content_view['container-image-repositories']]),
        )

    @tier2
    @run_only_on('sat')
    def test_positive_add_synced_docker_repo_by_id(self):
        """Create and sync a Docker-type repository

        :id: 6f51d268-ed23-48ab-9dea-cd3571daa647

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.

        :CaseLevel: Integration
        """
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org_id})['id'])
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        self.assertGreaterEqual(
            int(repo['content-counts']['container-image-manifests']), 1)
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
            [repo_['id'] for repo_ in
                content_view['container-image-repositories']],
        )

    @tier1
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    def test_positive_add_docker_repo_by_id_to_ccv(self):
        """Add one Docker-type repository to a composite content view

        :id: 8e2ef5ba-3cdf-4ef9-a22a-f1701e20a5d5

        :expectedresults: A repository is created with a Docker repository and
            the product is added to a content view which is then added to a
            composite content view.

        :BZ: 1359665

        :CaseImportance: Critical
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

    @tier1
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    def test_positive_add_docker_repos_by_id_to_ccv(self):
        """Add multiple Docker-type repositories to a composite content view.

        :id: b79cbc97-3dba-4059-907d-19316684d569

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a random number of content
            views which are then added to a composite content view.

        :BZ: 1359665

        :CaseImportance: Critical
        """
        cv_versions = []
        product = make_product_wait({'organization-id': self.org_id})
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

    @tier2
    @run_only_on('sat')
    def test_positive_publish_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it once.

        :id: 28480de3-ffb5-4b8e-8174-fffffeef6af4

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published only once.

        :CaseLevel: Integration
        """
        self._create_and_associate_repo_with_cv()
        self.assertEqual(len(self.content_view['versions']), 0)
        ContentView.publish({'id': self.content_view['id']})
        self.content_view = ContentView.info({
            'id': self.content_view['id'],
        })
        self.assertEqual(len(self.content_view['versions']), 1)

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    def test_positive_publish_with_docker_repo_composite(self):
        """Add Docker-type repository to composite CV and publish it once.

        :id: 2d75419b-73ed-4f29-ae0d-9af8d9624c87

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published once and added to a composite content view which is also
            published once.

        :CaseLevel: Integration

        :BZ: 1359665
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

    @tier2
    @run_only_on('sat')
    def test_positive_publish_multiple_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it multiple
        times.

        :id: 33c1b2ee-ae8a-4a7e-8254-123d97aaaa58

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published multiple times.

        :CaseLevel: Integration
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

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    def test_positive_publish_multiple_with_docker_repo_composite(self):
        """Add Docker-type repository to content view and publish it multiple
        times.

        :id: 014adf90-d399-4a99-badb-76ee03a2c350

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            added to a composite content view which is then published multiple
            times.

        :CaseLevel: Integration

        :BZ: 1359665
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

    @tier2
    @run_only_on('sat')
    def test_positive_promote_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it.
        Then promote it to the next available lifecycle-environment.

        :id: a7df98f4-0ec0-40f6-8941-3dbb776d47b9

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environment.

        :CaseLevel: Integration
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
            'to-lifecycle-environment-id': lce['id'],
        })
        cvv = ContentView.version_info({
            'id': self.content_view['versions'][0]['id'],
        })
        self.assertEqual(len(cvv['lifecycle-environments']), 2)

    @tier2
    @run_only_on('sat')
    @upgrade
    def test_positive_promote_multiple_with_docker_repo(self):
        """Add Docker-type repository to content view and publish it.
        Then promote it to multiple available lifecycle-environments.

        :id: e9432bc4-a709-44d7-8e1d-00ca466aa32d

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environments.

        :CaseLevel: Integration
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
                'to-lifecycle-environment-id': lce['id'],
            })
            cvv = ContentView.version_info({
                'id': self.content_view['versions'][0]['id'],
            })
            self.assertEqual(len(cvv['lifecycle-environments']), i+1)

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    def test_positive_promote_with_docker_repo_composite(self):
        """Add Docker-type repository to composite content view and publish it.
        Then promote it to the next available lifecycle-environment.

        :id: fb7d132e-d7fa-4890-a0ec-746dd093513e

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environment.

        :CaseLevel: Integration

        :BZ: 1359665
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
            'to-lifecycle-environment-id': lce['id'],
        })
        cvv = ContentView.version_info({
            'id': comp_content_view['versions'][0]['id'],
        })
        self.assertEqual(len(cvv['lifecycle-environments']), 2)

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    @upgrade
    def test_positive_promote_multiple_with_docker_repo_composite(self):
        """Add Docker-type repository to composite content view and publish it.
        Then promote it to the multiple available lifecycle-environments.

        :id: 345288d6-581b-4c07-8062-e58cb6343f1b

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environments.

        :CaseLevel: Integration

        :BZ: 1359665
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
                'to-lifecycle-environment-id': lce['id'],
            })
            cvv = ContentView.version_info({
                'id': comp_content_view['versions'][0]['id'],
            })
            self.assertEqual(len(cvv['lifecycle-environments']), i+1)

    @tier2
    @upgrade
    @run_only_on('sat')
    def test_positive_name_pattern_change(self):
        """Promote content view with Docker repository to lifecycle environment.
        Change registry name pattern for that environment. Verify that repository
        name on product changed according to new pattern.

        :id: 63c99ae7-238b-40ed-8cc1-d847eb4e6d65

        :expectedresults: Container repository name is changed
            according to new pattern.

        :CaseLevel: Integration
        """
        pattern_prefix = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = ("{}-<%= content_view.label %>"
                       + "/<%= repository.docker_upstream_name %>").format(
                pattern_prefix)

        repo = _make_docker_repo(
                make_product_wait({'organization-id': self.org_id})['id'],
                upstream_name=docker_upstream_name)
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({
            'id': content_view['id'],
        })
        lce = make_lifecycle_environment({'organization-id': self.org_id})
        ContentView.version_promote({
            'id': content_view['versions'][0]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        LifecycleEnvironment.update({
            'registry-name-pattern': new_pattern,
            'id': lce['id'],
            'organization-id': self.org_id,
        })
        lce = LifecycleEnvironment.info({
            'id': lce['id'],
            'organization-id': self.org_id,
        })
        repos = Repository.list({
            'environment-id': lce['id'],
            'organization-id': self.org_id,
        })

        expected_pattern = "{}-{}/{}".format(pattern_prefix,
                                             content_view['label'],
                                             docker_upstream_name).lower()
        self.assertEqual(lce['registry-name-pattern'], new_pattern)
        self.assertEqual(
                Repository.info({'id': repos[0]['id']})['container-repository-name'],
                expected_pattern)

    @tier2
    @run_only_on('sat')
    def test_positive_product_name_change_after_promotion(self):
        """Promote content view with Docker repository to lifecycle environment.
        Change product name. Verify that repository name on product changed
        according to new pattern.

        :id: 92279755-717c-415c-88b6-4cc1202072e2

        :expectedresults: Container repository name is changed
            according to new pattern.

        :CaseLevel: Integration
        """
        old_prod_name = gen_string('alpha', 5)
        new_prod_name = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = "<%= content_view.label %>/<%= product.name %>"

        prod = make_product_wait({
            'organization-id': self.org_id,
            'name': old_prod_name
        })
        repo = _make_docker_repo(prod['id'],
                                 upstream_name=docker_upstream_name)
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({
            'id': content_view['id'],
        })
        lce = make_lifecycle_environment({'organization-id': self.org_id})
        LifecycleEnvironment.update({
            'registry-name-pattern': new_pattern,
            'id': lce['id'],
            'organization-id': self.org_id,
        })
        lce = LifecycleEnvironment.info({
            'id': lce['id'],
            'organization-id': self.org_id,
        })
        ContentView.version_promote({
            'id': content_view['versions'][0]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        Product.update({
            'name': new_prod_name,
            'id': prod['id'],
        })
        repos = Repository.list({
            'environment-id': lce['id'],
            'organization-id': self.org_id,
        })

        expected_pattern = "{}/{}".format(content_view['label'],
                                          old_prod_name).lower()
        self.assertEqual(lce['registry-name-pattern'], new_pattern)
        self.assertEqual(
                Repository.info({'id': repos[0]['id']})['container-repository-name'],
                expected_pattern)

        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({
            'id': content_view['id'],
        })
        ContentView.version_promote({
            'id': content_view['versions'][-1]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        repos = Repository.list({
            'environment-id': lce['id'],
            'organization-id': self.org_id,
        })

        expected_pattern = "{}/{}".format(content_view['label'],
                                          new_prod_name).lower()
        self.assertEqual(
                Repository.info({'id': repos[0]['id']})['container-repository-name'],
                expected_pattern)

    @tier2
    @run_only_on('sat')
    def test_positive_repo_name_change_after_promotion(self):
        """Promote content view with Docker repository to lifecycle environment.
        Change repository name. Verify that Docker repository name on product
        changed according to new pattern.

        :id: f094baab-e823-47e0-939d-bd0d88eb1538

        :expectedresults: Container repository name is changed
            according to new pattern.

        :CaseLevel: Integration
        """
        old_repo_name = gen_string('alpha', 5)
        new_repo_name = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = "<%= content_view.label %>/<%= repository.name %>"

        prod = make_product_wait({'organization-id': self.org_id})
        repo = _make_docker_repo(prod['id'],
                                 name=old_repo_name,
                                 upstream_name=docker_upstream_name)
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({
            'id': content_view['id'],
        })
        lce = make_lifecycle_environment({'organization-id': self.org_id})
        LifecycleEnvironment.update({
            'registry-name-pattern': new_pattern,
            'id': lce['id'],
            'organization-id': self.org_id,
        })
        lce = LifecycleEnvironment.info({
            'id': lce['id'],
            'organization-id': self.org_id,
        })
        ContentView.version_promote({
            'id': content_view['versions'][0]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        Repository.update({
            'name': new_repo_name,
            'id': repo['id'],
            'product-id': prod['id'],
        })
        repos = Repository.list({
            'environment-id': lce['id'],
            'organization-id': self.org_id,
        })

        expected_pattern = "{}/{}".format(content_view['label'],
                                          old_repo_name).lower()
        self.assertEqual(
                Repository.info({'id': repos[0]['id']})['container-repository-name'],
                expected_pattern)

        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({
            'id': content_view['id'],
        })
        ContentView.version_promote({
            'id': content_view['versions'][-1]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        repos = Repository.list({
            'environment-id': lce['id'],
            'organization-id': self.org_id,
        })

        expected_pattern = "{}/{}".format(content_view['label'],
                                          new_repo_name).lower()
        self.assertEqual(
                Repository.info({'id': repos[0]['id']})['container-repository-name'],
                expected_pattern)

    @tier2
    @run_only_on('sat')
    def test_negative_set_non_unique_name_pattern_and_promote(self):
        """Set registry name pattern to one that does not guarantee uniqueness.
        Try to promote content view with multiple Docker repositories to
        lifecycle environment. Verify that content has not been promoted.

        :id: eaf5e7ac-93c9-46c6-b538-4d6bd73ab9fc

        :expectedresults: Content view is not promoted

        :CaseLevel: Integration
        """
        docker_upstream_names = ['hello-world', 'alpine']
        new_pattern = "<%= organization.label %>"

        lce = make_lifecycle_environment({
            'organization-id': self.org_id,
            'registry-name-pattern': new_pattern,
        })

        prod = make_product_wait({'organization-id': self.org_id})
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        for docker_name in docker_upstream_names:
            repo = _make_docker_repo(prod['id'],
                                     upstream_name=docker_name)
            Repository.synchronize({'id': repo['id']})
            ContentView.add_repository({
                'id': content_view['id'],
                'repository-id': repo['id'],
            })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({
            'id': content_view['id'],
        })
        with self.assertRaises(CLIReturnCodeError):
            ContentView.version_promote({
                'id': content_view['versions'][0]['id'],
                'to-lifecycle-environment-id': lce['id'],
            })

    @tier2
    @run_only_on('sat')
    def test_negative_promote_and_set_non_unique_name_pattern(self):
        """Promote content view with multiple Docker repositories to
        lifecycle environment. Set registry name pattern to one that
        does not guarantee uniqueness. Verify that pattern has not been
        changed.

        :id: 9f952224-084f-48d1-b2ea-85f3621becea

        :expectedresults: Registry name pattern is not changed

        :CaseLevel: Integration
        """
        docker_upstream_names = ['hello-world', 'alpine']
        new_pattern = "<%= organization.label %>"

        prod = make_product_wait({'organization-id': self.org_id})
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org_id,
        })
        for docker_name in docker_upstream_names:
            repo = _make_docker_repo(prod['id'],
                                     upstream_name=docker_name)
            Repository.synchronize({'id': repo['id']})
            ContentView.add_repository({
                'id': content_view['id'],
                'repository-id': repo['id'],
            })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({
            'id': content_view['id'],
        })
        lce = make_lifecycle_environment({'organization-id': self.org_id})
        ContentView.version_promote({
            'id': content_view['versions'][0]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })

        with self.assertRaises(CLIReturnCodeError):
            LifecycleEnvironment.update({
                'registry-name-pattern': new_pattern,
                'id': lce['id'],
                'organization-id': self.org_id,
            })


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
        cls.product = make_product_wait({
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
            'to-lifecycle-environment-id': cls.lce['id'],
        })
        cls.cvv = ContentView.version_info({
            'id': cls.content_view['versions'][0]['id'],
        })

    @tier2
    @run_only_on('sat')
    def test_positive_add_docker_repo_cv(self):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then create an activation key and associate it with the
        Docker content view.

        :id: bb128642-d39f-45c2-aa69-a4776ea536a2

        :expectedresults: Docker-based content view can be added to activation
            key

        :CaseLevel: Integration
        """
        activation_key = make_activation_key({
            'content-view-id': self.content_view['id'],
            'lifecycle-environment-id': self.lce['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(
            activation_key['content-view'], self.content_view['name'])

    @tier2
    @run_only_on('sat')
    def test_positive_remove_docker_repo_cv(self):
        """Add Docker-type repository to a non-composite content view
        and publish it. Create an activation key and associate it with the
        Docker content view. Then remove this content view from the activation
        key.

        :id: d696e5fe-1818-46ce-9499-924c96e1ef88

        :expectedresults: Docker-based content view can be added and then
            removed from the activation key.

        :CaseLevel: Integration
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
            'to-lifecycle-environment-id': self.lce['id'],
        })

        ActivationKey.update({
            'id': activation_key['id'],
            'organization-id': self.org['id'],
            'content-view-id': another_cv['id'],
            'lifecycle-environment-id': self.lce['id'],
        })
        activation_key = ActivationKey.info({
            'id': activation_key['id'],
        })
        self.assertNotEqual(
            activation_key['content-view'], self.content_view['name'])

    @tier2
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    def test_positive_add_docker_repo_ccv(self):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then add this content view to a composite content view
        and publish it. Create an activation key and associate it with the
        composite Docker content view.

        :id: 1d9b82fd-8dab-4fd9-ad35-656d712d56a2

        :expectedresults: Docker-based content view can be added to activation
            key

        :CaseLevel: Integration

        :BZ: 1359665
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
            'to-lifecycle-environment-id': self.lce['id'],
        })
        activation_key = make_activation_key({
            'content-view-id': comp_content_view['id'],
            'lifecycle-environment-id': self.lce['id'],
            'organization-id': self.org['id'],
        })
        self.assertEqual(
            activation_key['content-view'], comp_content_view['name'])

    @tier1
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1359665)
    def test_positive_remove_docker_repo_ccv(self):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then add this content view to a composite content view
        and publish it. Create an activation key and associate it with the
        composite Docker content view. Then, remove the composite content view
        from the activation key.

        :id: b4e63537-d3a8-4afa-8e18-57052b93fb4c

        :expectedresults: Docker-based composite content view can be added and
            then removed from the activation key.

        :BZ: 1359665

        :CaseImportance: Critical
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
            'to-lifecycle-environment-id': self.lce['id'],
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
            'to-lifecycle-environment-id': self.lce['id'],
        })

        ActivationKey.update({
            'id': activation_key['id'],
            'organization-id': self.org['id'],
            'content-view-id': another_cv['id'],
            'lifecycle-environment-id': self.lce['id'],
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
        cls.org = make_org()
        """Instantiate and setup a docker host VM"""
        cls.logger.info(u'Creating an external docker host')
        docker_image = settings.docker.docker_image
        cls.docker_host = VirtualMachine(
            source_image=docker_image,
            tag=u'docker'
        )
        cls.docker_host.create()
        cls.logger.info(u'Installing katello-ca on the external docker host')
        cls.docker_host.install_katello_ca()

    @classmethod
    def tearDownClass(cls):
        """Destroy the docker host VM"""
        cls.docker_host.destroy()

    @run_only_on('sat')
    @tier3
    def test_positive_pull_image(self):
        """A Docker-enabled client can use ``docker pull`` to pull a
        Docker image off a Satellite 6 instance.

        :id: 023f0538-2aad-4f87-b8a8-6ccced648366

        :Steps:

            1. Publish and promote content view with Docker content
            2. Register Docker-enabled client against Satellite 6.

        :expectedresults: Client can pull Docker images from server and run it.

        :CaseLevel: System
        """

        product = make_product_wait({'organization-id': self.org['id']})
        repo = _make_docker_repo(product['id'])
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        try:
            # publishing takes few seconds sometimes
            retries = 10 if bz_bug_is_open(1452149) else 1
            for i in range(retries):
                result = ssh.command(
                    'docker pull {0}'.format(repo['published-at']),
                    hostname=self.docker_host.ip_addr
                )
                if result.return_code == 0:
                    break
                sleep(2)
            self.assertEqual(result.return_code, 0)
            try:
                result = ssh.command(
                    'docker run {0}'.format(repo['published-at']),
                    hostname=self.docker_host.ip_addr
                )
                self.assertEqual(result.return_code, 0)
            finally:
                # Stop and remove the container
                result = ssh.command(
                    'docker ps -a | grep {0}'.format(repo['published-at']),
                    hostname=self.docker_host.ip_addr
                )
                container_id = result.stdout[0].split()[0]
                ssh.command(
                    'docker stop {0}'.format(container_id),
                    hostname=self.docker_host.ip_addr
                )
                ssh.command(
                    'docker rm {0}'.format(container_id),
                    hostname=self.docker_host.ip_addr
                )
        finally:
            # Remove docker image
            ssh.command(
                'docker rmi {0}'.format(repo['published-at']),
                hostname=self.docker_host.ip_addr
            )

    @run_only_on('sat')
    @skip_if_not_set('docker')
    @tier3
    def test_positive_container_admin_end_to_end_search(self):
        """Verify that docker command line can be used against
        Satellite server to search for container images stored
        on Satellite instance.

        :id: cefa74e1-e40d-4f47-853b-1268643cea2f

        :steps:

            1. Publish and promote content view with Docker content
            2. Set "Unauthenticated Pull" option to false
            3. Try to search for docker images on Satellite
            4. Use Docker client to login to Satellite docker hub
            5. Search for docker images
            6. Use Docker client to log out of Satellite docker hub
            7. Try to search for docker images (ensure last search result
               is caused by change of Satellite option and not login/logout)
            8. Set "Unauthenticated Pull" option to true
            9. Search for docker images

        :expectedresults: Client can search for docker images stored
            on Satellite instance

        :CaseLevel: System
        """
        pattern_prefix = gen_string('alpha', 5)
        docker_upstream_name = 'alpine'
        registry_name_pattern = (
            "{}-<%= content_view.label %>/<%= repository.docker_upstream_name %>"
        ).format(pattern_prefix)

        # Satellite setup: create product and add Docker repository;
        # create content view and add Docker repository;
        # create lifecycle environment and promote content view to it
        product = make_product_wait({'organization-id': self.org['id']})
        repo = _make_docker_repo(
                product['id'], upstream_name=docker_upstream_name)
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org['id'],
        })
        ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({
            'id': content_view['id'],
        })
        lce = make_lifecycle_environment({'organization-id': self.org['id']})
        ContentView.version_promote({
            'id': content_view['versions'][0]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        LifecycleEnvironment.update({
            'registry-name-pattern': registry_name_pattern,
            'registry-unauthenticated-pull': 'false',
            'id': lce['id'],
            'organization-id': self.org['id'],
        })
        docker_repo_uri = " {}/{}-{}/{} ".format(
                settings.server.hostname,
                pattern_prefix,
                content_view['label'],
                docker_upstream_name
        ).lower()

        # 3. Try to search for docker images on Satellite
        remote_search_command = 'docker search {0}/{1}'.format(
                settings.server.hostname,
                docker_upstream_name
        )
        result = ssh.command(
                remote_search_command,
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 0)
        self.assertNotIn(
                docker_repo_uri,
                "\n".join(result.stdout)
        )

        # 4. Use Docker client to login to Satellite docker hub
        result = ssh.command(
                'docker login -u {} -p {} {}'.format(
                        settings.server.admin_username,
                        settings.server.admin_password,
                        settings.server.hostname
                ),
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 0)

        # 5. Search for docker images
        result = ssh.command(
                remote_search_command,
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 0)
        self.assertIn(
                docker_repo_uri,
                "\n".join(result.stdout)
        )

        # 6. Use Docker client to log out of Satellite docker hub
        result = ssh.command(
                'docker logout {}'.format(settings.server.hostname),
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 0)

        # 7. Try to search for docker images
        result = ssh.command(
                remote_search_command,
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 0)
        self.assertNotIn(
                docker_repo_uri,
                "\n".join(result.stdout)
        )

        # 8. Set "Unauthenticated Pull" option to true
        LifecycleEnvironment.update({
            'registry-unauthenticated-pull': 'true',
            'id': lce['id'],
            'organization-id': self.org['id'],
        })

        # 9. Search for docker images
        result = ssh.command(
                remote_search_command,
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 0)
        self.assertIn(
                docker_repo_uri,
                "\n".join(result.stdout)
        )

    @run_only_on('sat')
    @skip_if_not_set('docker')
    @tier3
    def test_positive_container_admin_end_to_end_pull(self):
        """Verify that docker command line can be used against
        Satellite server to pull in container images stored
        on Satellite instance.

        :id: 2a331f88-406b-4a5c-ae70-302a9994077f

        :steps:

            1. Publish and promote content view with Docker content
            2. Set "Unauthenticated Pull" option to false
            3. Try to pull in docker image from Satellite
            4. Use Docker client to login to Satellite container registry
            5. Pull in docker image
            6. Use Docker client to log out of Satellite container registry
            7. Try to pull in docker image (ensure next pull result
               is caused by change of Satellite option and not login/logout)
            8. Set "Unauthenticated Pull" option to true
            9. Pull in docker image

        :expectedresults: Client can pull in docker images stored
            on Satellite instance

        :CaseLevel: System
        """
        pattern_prefix = gen_string('alpha', 5)
        docker_upstream_name = 'alpine'
        registry_name_pattern = (
            "{}-<%= content_view.label %>/<%= repository.docker_upstream_name %>"
        ).format(pattern_prefix)

        # Satellite setup: create product and add Docker repository;
        # create content view and add Docker repository;
        # create lifecycle environment and promote content view to it
        product = make_product_wait({'organization-id': self.org['id']})
        repo = _make_docker_repo(
                product['id'], upstream_name=docker_upstream_name)
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({
            'composite': False,
            'organization-id': self.org['id'],
        })
        ContentView.add_repository({
            'id': content_view['id'],
            'repository-id': repo['id'],
        })
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({
            'id': content_view['id'],
        })
        lce = make_lifecycle_environment({'organization-id': self.org['id']})
        ContentView.version_promote({
            'id': content_view['versions'][0]['id'],
            'to-lifecycle-environment-id': lce['id'],
        })
        LifecycleEnvironment.update({
            'registry-name-pattern': registry_name_pattern,
            'registry-unauthenticated-pull': 'false',
            'id': lce['id'],
            'organization-id': self.org['id'],
        })
        docker_repo_uri = "{}/{}-{}/{}".format(
                settings.server.hostname,
                pattern_prefix,
                content_view['label'],
                docker_upstream_name
        ).lower()

        # 3. Try to pull in docker image from Satellite
        docker_pull_command = 'docker pull {0}'.format(docker_repo_uri)
        result = ssh.command(
                docker_pull_command,
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 1)

        # 4. Use Docker client to login to Satellite docker hub
        result = ssh.command(
                'docker login -u {} -p {} {}'.format(
                        settings.server.admin_username,
                        settings.server.admin_password,
                        settings.server.hostname
                ),
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 0)

        # 5. Pull in docker image
        # publishing takes few seconds sometimes
        retries = 20 if bz_bug_is_open(1452149) else 1
        for i in range(retries):
            result = ssh.command(
                    docker_pull_command,
                    hostname=self.docker_host.ip_addr
            )
            if result.return_code == 0:
                break
            sleep(2)
        self.assertEqual(result.return_code, 0)

        # 6. Use Docker client to log out of Satellite docker hub
        result = ssh.command(
                'docker logout {}'.format(settings.server.hostname),
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 0)

        # 7. Try to pull in docker image
        result = ssh.command(
                docker_pull_command,
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 1)

        # 8. Set "Unauthenticated Pull" option to true
        LifecycleEnvironment.update({
            'registry-unauthenticated-pull': 'true',
            'id': lce['id'],
            'organization-id': self.org['id'],
        })

        # 9. Pull in docker image
        result = ssh.command(
                docker_pull_command,
                hostname=self.docker_host.ip_addr
        )
        self.assertEqual(result.return_code, 0)

    @stubbed()
    @run_only_on('sat')
    @skip_if_not_set('docker')
    @tier3
    @upgrade
    def test_positive_upload_image(self):
        """A Docker-enabled client can create a new ``Dockerfile``
        pointing to an existing Docker image from a Satellite 6 and modify it.
        Then, using ``docker build`` generate a new image which can then be
        uploaded back onto the Satellite 6 as a new repository.

        :id: 2c47559c-b27f-436e-9b1e-df5c3633b007

        :Steps:

            1. Create a local docker compute resource
            2. Create a container and start it
            3. [on docker host] Commit a new image from the container
            4. [on docker host] Export the image to tar
            5. scp the image to satellite box
            6. create a new docker repo
            7. upload the image to the new repo

        :expectedresults: Client can create a new image based off an existing
            Docker image from a Satellite 6 instance, add a new package and
            upload the modified image (plus layer) back to the Satellite 6.

        :CaseLevel: System
        """
        compute_resource = make_compute_resource({
            'organization-ids': [self.org['id']],
            'provider': DOCKER_PROVIDER,
            'url': u'http://{0}:2375'.format(self.docker_host.ip_addr),
        })
        try:
            container = make_container({
                'compute-resource-id': compute_resource['id'],
                'organization-ids': [self.org['id']],
            })
            Docker.container.start({'id': container['id']})
            repo_name = gen_string('alphanumeric').lower()
            # Commit a new docker image and verify image was created
            result = ssh.command(
                'docker commit {0} {1}/{2}:latest && '
                'docker images --all | grep {1}/{2}'.format(
                    container['uuid'],
                    repo_name,
                    REPO_UPSTREAM_NAME,
                ),
                self.docker_host.ip_addr
            )
            self.assertEqual(result.return_code, 0)
            # Save the image to a tar archive
            result = ssh.command(
                'docker save -o {0}.tar {0}/{1}'.format(
                    repo_name,
                    REPO_UPSTREAM_NAME,
                ),
                self.docker_host.ip_addr
            )
            self.assertEqual(result.return_code, 0)
            tar_file = '{0}.tar'.format(repo_name)
            ssh.download_file(
                tar_file,
                hostname=self.docker_host.ip_addr
            )

            ssh.upload_file(
                local_file=tar_file,
                remote_file='/tmp/{0}'.format(tar_file),
                hostname=settings.server.hostname
            )
            # Upload tarred repository
            product = make_product_wait({'organization-id': self.org['id']})
            repo = _make_docker_repo(product['id'])
            Repository.upload_content({
                'id': repo['id'],
                'path': '/tmp/{0}.tar'.format(repo_name),
            })
            # Verify repository was uploaded successfully
            repo = Repository.info({'id': repo['id']})
            self.assertIn(settings.server.hostname, repo['published-at'])
            self.assertIn(
                '{0}-{1}-{2}'.format(
                    self.org['label'].lower(),
                    product['label'].lower(),
                    repo['label'].lower(),
                ),
                repo['published-at'],
            )
        finally:
            # Remove the archive
            ssh.command('rm -f /tmp/{0}.tar'.format(repo_name))


class DockerComputeResourceTestCase(CLITestCase):
    """Tests specific to managing Docker-based Compute Resources."""

    @classmethod
    @skip_if_not_set('docker')
    def setUpClass(cls):
        """Create an organization and product which can be re-used in tests."""
        super(DockerComputeResourceTestCase, cls).setUpClass()
        cls.org = make_org()

    @tier3
    @run_only_on('sat')
    def test_positive_create_internal(self):
        """Create a Docker-based Compute Resource in the Satellite 6
        instance.

        :id: 8c8e6185-9aad-42d4-bab2-e067d9a98ffb

        :expectedresults: Compute Resource can be created and listed.

        :CaseLevel: System
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

    @tier3
    @run_only_on('sat')
    def test_positive_update_internal(self):
        """Create a Docker-based Compute Resource in the Satellite 6
        instance then edit its attributes.

        :id: 0b6411a9-2e9d-4ea6-9b9d-e026b1ff3c1c

        :expectedresults: Compute Resource can be created, listed and its
            attributes can be updated.

        :CaseLevel: System
        """
        url = settings.docker.get_unix_socket_url()
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

    @tier3
    @skip_if_bug_open('bugzilla', 1466240)
    @skip_if_bug_open('bugzilla', 1478966)
    @run_only_on('sat')
    @upgrade
    def test_positive_list_containers(self):
        """Create a Docker-based Compute Resource in the Satellite 6
        instance then list its running containers.

        :id: 52606017-bbf8-4630-9516-9ae069eaf09d

        :expectedresults: Compute Resource can be created, listed and existing
            running instances can be listed.

        :CaseLevel: System
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

    @tier3
    @run_only_on('sat')
    def test_positive_create_external(self):
        """Create a Docker-based Compute Resource using an external
        Docker-enabled system.

        :id: d7c9fbc9-3b6b-4cff-8a48-9b93d63075a8

        :expectedresults: Compute Resource can be created and listed.

        :CaseLevel: System
        """
        docker_image = settings.docker.docker_image
        with VirtualMachine(source_image=docker_image) as docker_host:
            docker_host.create()
            for name in valid_data_list():
                with self.subTest(name):
                    compute_resource = make_compute_resource({
                        'name': name,
                        'provider': DOCKER_PROVIDER,
                        'url': 'http://{0}:2375'.format(docker_host.ip_addr),
                    })
                    self.assertEqual(compute_resource['name'], name)
                    self.assertEqual(
                        compute_resource['provider'],
                        DOCKER_PROVIDER
                    )
                    self.assertEqual(
                        compute_resource['url'],
                        'http://{0}:2375'.format(docker_host.ip_addr)
                    )

    @tier3
    @run_only_on('sat')
    def test_positive_delete_by_id(self):
        """Create a Docker-based Compute Resource then delete it.

        :id: df96331a-6a4c-4db9-9188-5ff510ef4356

        :expectedresults: Compute Resource can be created, listed and deleted.

        :CaseLevel: System
        """
        docker_image = settings.docker.docker_image
        with VirtualMachine(source_image=docker_image) as docker_host:
            docker_host.create()
            url = 'http://{0}:2375'.format(docker_host.ip_addr)
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
    """Tests specific to using ``Containers`` with external Docker Compute
    Resource
    """

    @classmethod
    @skip_if_not_set('docker')
    @skip_if_bug_open('bugzilla', 1478966)
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(DockerContainersTestCase, cls).setUpClass()
        cls.org = make_org()

    def setUp(self):
        """Instantiate and setup a docker host VM + compute resource"""
        self.logger.info(u'Creating an external docker host')
        docker_image = settings.docker.docker_image
        self.docker_host = VirtualMachine(
            source_image=docker_image,
            tag=u'docker'
        )
        self.docker_host.create()
        self.logger.info(u'Installing katello-ca on the external docker host')
        self.docker_host.install_katello_ca()
        self.logger.info(u'Adding the external docker host as a docker CR')
        self.comp_resource = make_compute_resource({
            'organization-ids': [self.org['id']],
            'provider': DOCKER_PROVIDER,
            'url': 'http://{0}:2375'.format(self.docker_host.ip_addr),
        })

    def tearDown(self):
        self.docker_host.destroy()

    @tier3
    @run_only_on('sat')
    def test_positive_create_with_compresource(self):
        """Create containers on a docker compute resource

        :id: aa1d5216-deaf-403e-9d4c-60157a251762

        :expectedresults: The docker container is created

        :CaseLevel: System
        """
        container = make_container({
            'compute-resource-id': self.comp_resource['id'],
            'organization-ids': [self.org['id']],
        })
        self.assertEqual(
            container['compute-resource'], self.comp_resource['name'])

    @tier3
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1282431)
    @skip_if_bug_open('bugzilla', 1347658)
    @upgrade
    def test_positive_create_using_cv(self):
        """Create docker container using custom content view, lifecycle
        environment and docker repository

        :id: 5569186f-667b-4866-a88e-fd6cf6e821da

        :expectedresults: The docker container is created

        :BZ: 1282431

        :CaseLevel: System
        """
        lce = make_lifecycle_environment({'organization-id': self.org['id']})
        repo = _make_docker_repo(
            make_product_wait({'organization-id': self.org['id']})['id'],
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

        container = make_container({
            'compute-resource-id': self.comp_resource['id'],
            'organization-ids': [self.org['id']],
            'repository-name': repo['container-repository-name'],
            'tag': 'latest',
            'tty': 'yes',
        })
        self.assertEqual(
            container['compute-resource'], self.comp_resource['name'])
        self.assertEqual(
            container['image-repository'],
            repo['container-repository-name']
        )
        self.assertEqual(container['tag'], 'latest')

    @tier3
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1230915)
    @skip_if_bug_open('bugzilla', 1269196)
    def test_positive_power_on_off(self):
        """Create containers on external compute resource, then
        power them on and finally power them off

        :id: c7150e63-f81c-4a55-808d-a2bed1a4eaf2

        :expectedresults: The docker container is created and the power status
            is showing properly

        :BZ: 1230915, 1269196

        :CaseLevel: System
        """
        # testing the text status may fail i18n tests but for now there is
        # nothing else to assert
        not_running_msg = 'Running: no'
        running_msg = 'Running: yes'
        container = make_container({
            'compute-resource-id': self.comp_resource['id'],
            'organization-ids': [self.org['id']],
        })
        self.logger.info(u'Verifying docker container is running on host')
        docker_ps = ssh.command(
            'docker ps -f id={0}'.format(container['name']),
            self.docker_host.ip_addr
        )
        self.assertEqual(docker_ps.return_code, 0)
        status = Docker.container.status({'id': container['id']})
        self.assertEqual(status[0], running_msg)
        Docker.container.stop({'id': container['id']})
        docker_ps = ssh.command(
            'docker ps -f id={0}'.format(container['id']),
            self.docker_host.ip_addr
        )
        self.assertEqual(docker_ps.return_code, 0)
        status = Docker.container.status({'id': container['id']})
        self.assertEqual(status[0], not_running_msg)

    @tier3
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1230915)
    @skip_if_bug_open('bugzilla', 1479291)
    def test_positive_read_container_log(self):
        """Create containers for local and external compute resource and read
        their logs

        :id: 7c818e53-9833-4a4c-b9bf-a62895dad37f

        :expectedresults: The docker container is created for each compute
            resource and its log can be read

        :BZ: 1230915, 1479291

        :CaseLevel: System
        """
        container = make_container({
            'command': 'date',
            'compute-resource-id': self.comp_resource['id'],
            'organization-ids': [self.org['id']],
        })
        logs = Docker.container.logs({'id': container['id']})
        self.assertTrue(logs['logs'])

    @run_in_one_thread
    @run_only_on('sat')
    @tier2
    def test_positive_create_with_external_registry(self):
        """Create a container pulling an image from a custom external registry

        :id: 006ff4c2-8ff8-41fc-8096-dda24267a223

        :expectedresults: The docker container is created and the image is
            pulled from the external registry

        :CaseLevel: Integration
        """
        repo_name = 'rhel'
        registry = make_registry({'url': settings.docker.external_registry_1})
        try:
            container = make_container({
                'compute-resource-id': self.comp_resource['id'],
                'organization-ids': [self.org['id']],
                'registry-id': registry['id'],
                'repository-name': repo_name,
            })
            self.assertEqual(container['registry'], registry['name'])
            self.assertEqual(container['image-repository'], repo_name)
        finally:
            Docker.registry.delete({'id': registry['id']})

    @tier3
    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1230915)
    def test_positive_delete_by_id(self):
        """Delete containers in local and external compute resources

        :id: 7280efa4-2569-4034-bce4-12dc08838e36

        :expectedresults: The docker containers are deleted in local and
            external compute resources

        :BZ: 1230915

        :CaseLevel: System
        """
        container = make_container({
            'compute-resource-id': self.comp_resource['id'],
            'organization-ids': [self.org['id']],
        })
        Docker.container.delete({'id': container['id']})
        with self.assertRaises(CLIReturnCodeError):
            Docker.container.info({'id': container['id']})


@skip_if_bug_open('bugzilla', 1414821)
class DockerUnixSocketContainerTestCase(CLITestCase):
    """Tests specific to using ``Containers`` with internal unix-socket
      Docker Compute Resource
    """

    @classmethod
    @skip_if_not_set('docker')
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(DockerUnixSocketContainerTestCase, cls).setUpClass()
        cls.org = make_org()
        cls.cr_internal = make_compute_resource({
            'organization-ids': [cls.org['id']],
            'provider': DOCKER_PROVIDER,
            'url': settings.docker.get_unix_socket_url(),
        })

    @tier3
    @run_only_on('sat')
    @upgrade
    def test_positive_create_with_compresource(self):
        """Create containers on a docker compute resource

        :id: 5ad180d5-ee36-440e-a0a0-130c7ebc8c8d

        :expectedresults: The docker container is created

        :CaseLevel: System
        """
        container = make_container({
            'compute-resource-id': self.cr_internal['id'],
            'organization-ids': [self.org['id']],
        })
        self.assertEqual(
            container['compute-resource'], self.cr_internal['name'])


@run_in_one_thread
class DockerRegistryTestCase(CLITestCase):
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

        :id: c2380323-56d6-4465-ad79-06868b97be16

        :expectedresults: the external registry is created

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                description = gen_string('alphanumeric')
                registry = make_registry({
                    'description': description,
                    'name': name,
                    'url': self.url,
                })
                try:
                    self.assertEqual(registry['name'], name)
                    self.assertEqual(registry['description'], description)
                    self.assertEqual(registry['url'], self.url)
                finally:
                    Docker.registry.delete({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_name_by_id(self):
        """Create an external docker registry and update its name. Use registry
        ID to search by

        :id: b702a33c-1c23-4b55-9ea1-f0b3bfc9cca2

        :expectedresults: the external registry is updated with the new name

        :CaseImportance: Critical
        """
        registry = make_registry()
        try:
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    Docker.registry.update({
                        'id': registry['id'],
                        'new-name': new_name,
                    })
                    registry = Docker.registry.info({'id': registry['id']})
                    self.assertEqual(registry['name'], new_name)
        finally:
            Docker.registry.delete({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_name_by_name(self):
        """Create an external docker registry and update its name. Use registry
        name to search by

        :id: d74e5795-5336-414c-844f-04bf1171d337

        :expectedresults: the external registry is updated with the new name

        :CaseImportance: Critical
        """
        registry = make_registry()
        try:
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    Docker.registry.update({
                        'name': registry['name'],
                        'new-name': new_name,
                    })
                    registry = Docker.registry.info({'name': new_name})
                    self.assertEqual(registry['name'], new_name)
        finally:
            Docker.registry.delete({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_url_by_id(self):
        """Create an external docker registry and update its URL. Use registry
        ID to search by

        :id: 71e8c75a-ce5d-4e8a-9564-2c6d9084f8fc

        :expectedresults: the external registry is updated with the new URL

        :BZ: 1489322

        :CaseImportance: Critical
        """
        registry = make_registry()
        try:
            new_url = settings.docker.external_registry_2
            Docker.registry.update({
                'id': registry['id'],
                'url': new_url,
            })
            registry = Docker.registry.info({'id': registry['id']})
            self.assertEqual(registry['url'], new_url)
        finally:
            Docker.registry.delete({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_url_by_name(self):
        """Create an external docker registry and update its URL. Use registry
        name to search by

        :id: 7d4fcdb3-c66f-4d0b-9df0-7a105ab29cb2

        :expectedresults: the external registry is updated with the new URL

        :BZ: 1489322

        :CaseImportance: Critical
        """
        registry = make_registry()
        try:
            new_url = settings.docker.external_registry_2
            Docker.registry.update({
                'name': registry['name'],
                'url': new_url,
            })
            registry = Docker.registry.info({'name': registry['name']})
            self.assertEqual(registry['url'], new_url)
        finally:
            Docker.registry.delete({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_description_by_id(self):
        """Create an external docker registry and update its description. Use
        registry ID to search by

        :id: 84efd73c-517e-411a-8a4a-5cf2718ca03c

        :expectedresults: the external registry is updated with the new
            description

        :CaseImportance: Critical
        """
        registry = make_registry({'description': gen_string('alpha')})
        try:
            for new_desc in valid_data_list():
                with self.subTest(new_desc):
                    Docker.registry.update({
                        'description': new_desc,
                        'id': registry['id'],
                    })
                    registry = Docker.registry.info({'id': registry['id']})
                    self.assertEqual(registry['description'], new_desc)
        finally:
            Docker.registry.delete({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_description_by_name(self):
        """Create an external docker registry and update its description. Use
        registry name to search by

        :id: 0c452868-096f-46ae-b884-a6553611b1f3

        :expectedresults: the external registry is updated with the new
            description

        :CaseImportance: Critical
        """
        registry = make_registry({'description': gen_string('alpha')})
        try:
            for new_desc in valid_data_list():
                with self.subTest(new_desc):
                    Docker.registry.update({
                        'description': new_desc,
                        'name': registry['name'],
                    })
                    registry = Docker.registry.info({'name': registry['name']})
                    self.assertEqual(registry['description'], new_desc)
        finally:
            Docker.registry.delete({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_username_by_id(self):
        """Create an external docker registry and update its username. Use
        registry ID to search by

        :id: 58e119e9-5681-49f3-bb33-41bb7d024930

        :expectedresults: the external registry is updated with the new
            username

        :CaseImportance: Critical
        """
        registry = make_registry({'username': gen_string('alpha')})
        try:
            for new_user in valid_data_list():
                with self.subTest(new_user):
                    Docker.registry.update({
                        'id': registry['id'],
                        'username': new_user,
                    })
                    registry = Docker.registry.info({'id': registry['id']})
                    self.assertEqual(registry['username'], new_user)
        finally:
            Docker.registry.delete({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_update_username_by_name(self):
        """Create an external docker registry and update its username. Use
        registry name to search by

        :id: d139f89f-ce84-449c-9938-945c6dc980b6

        :expectedresults: the external registry is updated with the new
            username

        :CaseImportance: Critical
        """
        registry = make_registry({'username': gen_string('alpha')})
        try:
            for new_user in valid_data_list():
                with self.subTest(new_user):
                    Docker.registry.update({
                        'name': registry['name'],
                        'username': new_user,
                    })
                    registry = Docker.registry.info({'name': registry['name']})
                    self.assertEqual(registry['username'], new_user)
        finally:
            Docker.registry.delete({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_id(self):
        """Create an external docker registry. Use registry ID to search by

        :id: c518011c-8665-4a7f-8b0e-af00232f876a

        :expectedresults: the external registry is created

        :CaseImportance: Critical
        """
        registry = make_registry()
        Docker.registry.delete({'id': registry['id']})
        with self.assertRaises(CLIReturnCodeError):
            Docker.registry.info({'id': registry['id']})

    @tier1
    @run_only_on('sat')
    def test_positive_delete_by_name(self):
        """Create an external docker registry. Use registry name to search by

        :id: a0c52cef-1757-4b91-a144-7dc0405cd33d

        :expectedresults: the external registry is created

        :CaseImportance: Critical
        """
        for name in valid_data_list():
            with self.subTest(name):
                registry = make_registry({'name': name})
                Docker.registry.delete({'name': registry['name']})
                with self.assertRaises(CLIReturnCodeError):
                    Docker.registry.info({'name': registry['name']})
