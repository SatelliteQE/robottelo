"""Tests for the Docker feature.

:Requirement: Docker

:CaseAutomation: Automated

:CaseLevel: Component

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from random import choice
from random import randint

import pytest
from fauxfactory import gen_string
from fauxfactory import gen_url
from wait_for import wait_for

from robottelo.cli.activationkey import ActivationKey
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.contentview import ContentView
from robottelo.cli.docker import Docker
from robottelo.cli.factory import make_activation_key
from robottelo.cli.factory import make_content_view
from robottelo.cli.factory import make_lifecycle_environment
from robottelo.cli.factory import make_product_wait
from robottelo.cli.factory import make_repository
from robottelo.cli.lifecycleenvironment import LifecycleEnvironment
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CONTAINER_RH_REGISTRY_UPSTREAM_NAME
from robottelo.constants import CONTAINER_UPSTREAM_NAME
from robottelo.constants import REPO_TYPE
from robottelo.logging import logger
from robottelo.utils.datafactory import invalid_docker_upstream_names
from robottelo.utils.datafactory import parametrized
from robottelo.utils.datafactory import valid_docker_repository_names
from robottelo.utils.datafactory import valid_docker_upstream_names


def _repo(product_id, name=None, upstream_name=None, url=None):
    """Creates a Docker-based repository.

    :param product_id: ID of the ``Product``.
    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name of an existing upstream repository.
        If ``None`` then defaults to CONTAINER_UPSTREAM_NAME constant.
    :param str url: URL of repository. If ``None`` then defaults to
        CONTAINER_REGISTRY_HUB constant.
    :return: A ``Repository`` object.
    """
    return make_repository(
        {
            'content-type': REPO_TYPE['docker'],
            'docker-upstream-name': upstream_name or CONTAINER_UPSTREAM_NAME,
            'name': name or gen_string('alpha', 5),
            'product-id': product_id,
            'url': url or CONTAINER_REGISTRY_HUB,
        }
    )


def _content_view(repo_id, org_id):
    """Create a content view and link it to the given repository."""
    content_view = make_content_view({'composite': False, 'organization-id': org_id})
    ContentView.add_repository({'id': content_view['id'], 'repository-id': repo_id})
    return ContentView.info({'id': content_view['id']})


@pytest.fixture
def repo(module_product):
    return _repo(module_product.id)


@pytest.fixture
def content_view(module_org, repo):
    return _content_view(repo['id'], module_org.id)


@pytest.fixture
def content_view_publish(content_view):
    ContentView.publish({'id': content_view['id']})
    content_view = ContentView.info({'id': content_view['id']})
    return ContentView.version_info({'id': content_view['versions'][0]['id']})


@pytest.fixture
def content_view_promote(content_view_publish, module_lce):
    ContentView.version_promote(
        {
            'id': content_view_publish['id'],
            'to-lifecycle-environment-id': module_lce.id,
        }
    )
    return ContentView.version_info({'id': content_view_publish['id']})


class TestDockerManifest:
    """Tests related to docker manifest command

    :CaseComponent: Repositories

    :Assignee: chiggins
    """

    @pytest.mark.tier2
    def test_positive_read_docker_tags(self, repo):
        """docker manifest displays tags information for a docker manifest

        :id: 59b605b5-ac2d-46e3-a85e-a259e78a07a8

        :expectedresults: docker manifest displays tags info for a docker
            manifest

        :CaseImportance: Medium

        :BZ: 1658274
        """
        Repository.synchronize({'id': repo['id']})
        # Grab all available manifests related to repository
        manifests_list = Docker.manifest.list({'repository-id': repo['id']})
        # Some manifests do not have tags associated with it, ignore those
        # because we want to check the tag information
        manifests = [m_iter for m_iter in manifests_list if not m_iter['tags'] == '']
        assert manifests
        tags_list = Docker.tag.list({'repository-id': repo['id']})
        # Extract tag names for the repository out of docker tag list
        repo_tag_names = [tag['tag'] for tag in tags_list]
        for manifest in manifests:
            manifest_info = Docker.manifest.info({'id': manifest['id']})
            # Check that manifest's tag is listed in tags for the repository
            for t_iter in manifest_info['tags']:
                assert t_iter['name'] in repo_tag_names


class TestDockerRepository:
    """Tests specific to performing CRUD methods against ``Docker`` repositories.

    :CaseComponent: Repositories

    :Assignee: chiggins
    """

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_docker_repository_names()))
    def test_positive_create_with_name(self, module_org, module_product, name):
        """Create one Docker-type repository

        :id: e82a36c8-3265-4c10-bafe-c7e07db3be78

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
         repository.

        :CaseImportance: Critical
        """
        repo = _repo(module_product.id, name)
        assert repo['name'] == name
        assert repo['upstream-repository-name'] == CONTAINER_UPSTREAM_NAME
        assert repo['content-type'] == REPO_TYPE['docker']

    @pytest.mark.tier2
    def test_positive_create_repos_using_same_product(self, module_org, module_product):
        """Create multiple Docker-type repositories

        :id: 6dd25cf4-f8b6-4958-976a-c116daf27b44

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to the same product.

        :CaseLevel: Integration
        """
        repo_names = set()
        for _ in range(randint(2, 5)):
            repo = _repo(module_product.id)
            repo_names.add(repo['name'])
        product = Product.info({'id': module_product.id, 'organization-id': module_org.id})
        assert repo_names.issubset({repo_['repo-name'] for repo_ in product['content']})

    @pytest.mark.tier2
    def test_positive_create_repos_using_multiple_products(self, module_org):
        """Create multiple Docker-type repositories on multiple
        products.

        :id: 43f4ab0d-731e-444e-9014-d663ff945f36

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to their respective
            products.

        :CaseLevel: Integration
        """
        for _ in range(randint(2, 5)):
            product = make_product_wait({'organization-id': module_org.id})
            repo_names = set()
            for _ in range(randint(2, 3)):
                repo = _repo(product['id'])
                repo_names.add(repo['name'])
            product = Product.info({'id': product['id'], 'organization-id': module_org.id})
            assert repo_names == {repo_['repo-name'] for repo_ in product['content']}

    @pytest.mark.tier1
    def test_positive_sync(self, repo):
        """Create and sync a Docker-type repository

        :id: bff1d40e-181b-48b2-8141-8c86e0db62a2

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.

        :CaseImportance: Critical
        """
        assert int(repo['content-counts']['container-image-manifests']) == 0
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['container-image-manifests']) > 0

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(valid_docker_repository_names()))
    def test_positive_update_name(self, repo, new_name):
        """Create a Docker-type repository and update its name.

        :id: 8b3a8496-e9bd-44f1-916f-6763a76b9b1b

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
            repository and that its name can be updated.

        :CaseImportance: Critical
        """
        Repository.update({'id': repo['id'], 'new-name': new_name, 'url': repo['url']})
        repo = Repository.info({'id': repo['id']})
        assert repo['name'] == new_name

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_upstream_name', **parametrized(valid_docker_upstream_names()))
    def test_positive_update_upstream_name(self, repo, new_upstream_name):
        """Create a Docker-type repository and update its upstream name.

        :id: 1a6985ed-43ec-4ea6-ba27-e3870457ac56

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can be updated.

        :CaseImportance: Critical
        """
        Repository.update(
            {
                'docker-upstream-name': new_upstream_name,
                'id': repo['id'],
                'url': repo['url'],
            }
        )
        repo = Repository.info({'id': repo['id']})
        assert repo['upstream-repository-name'] == new_upstream_name

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_upstream_name', **parametrized(invalid_docker_upstream_names()))
    def test_negative_update_upstream_name(self, repo, new_upstream_name):
        """Attempt to update upstream name for a Docker-type repository.

        :id: 798651af-28b2-4907-b3a7-7c560bf66c7c

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can not be updated with
            invalid values.

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError, match='Validation failed: Docker upstream name'):
            Repository.update(
                {
                    'docker-upstream-name': new_upstream_name,
                    'id': repo['id'],
                    'url': repo['url'],
                }
            )

    @pytest.mark.skip_if_not_set('docker')
    @pytest.mark.tier1
    def test_positive_create_with_long_upstream_name(self, module_product):
        """Create a docker repository with upstream name longer than 30
        characters

        :id: 4fe47c02-a8bd-4630-9102-189a9d268b83

        :customerscenario: true

        :BZ: 1424689

        :expectedresults: docker repository is successfully created

        :CaseImportance: Critical
        """
        repo = _repo(
            module_product.id,
            upstream_name=CONTAINER_RH_REGISTRY_UPSTREAM_NAME,
            url=settings.docker.external_registry_1,
        )
        assert repo['upstream-repository-name'] == CONTAINER_RH_REGISTRY_UPSTREAM_NAME

    @pytest.mark.skip_if_not_set('docker')
    @pytest.mark.tier1
    def test_positive_update_with_long_upstream_name(self, repo):
        """Create a docker repository and update its upstream name with longer
        than 30 characters value

        :id: 97260cce-9677-4a3e-942b-e95e2714500a

        :BZ: 1424689

        :expectedresults: docker repository is successfully updated

        :CaseImportance: Critical
        """
        Repository.update(
            {
                'docker-upstream-name': CONTAINER_RH_REGISTRY_UPSTREAM_NAME,
                'id': repo['id'],
                'url': settings.docker.external_registry_1,
            }
        )
        repo = Repository.info({'id': repo['id']})
        assert repo['upstream-repository-name'] == CONTAINER_RH_REGISTRY_UPSTREAM_NAME

    @pytest.mark.tier2
    def test_positive_update_url(self, repo):
        """Create a Docker-type repository and update its URL.

        :id: 73caacd4-7f17-42a7-8d93-3dee8b9341fa

        :expectedresults: A repository is created with a Docker upstream
            repository and that its URL can be updated.
        """
        new_url = gen_url()
        Repository.update({'id': repo['id'], 'url': new_url})
        repo = Repository.info({'id': repo['id']})
        assert repo['url'] == new_url

    @pytest.mark.tier1
    def test_positive_delete_by_id(self, repo):
        """Create and delete a Docker-type repository

        :id: ab1e8228-92a8-45dc-a863-7181711f2745

        :expectedresults: A repository with a upstream repository is created
            and then deleted.

        :CaseImportance: Critical
        """
        Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})

    @pytest.mark.tier2
    def test_positive_delete_random_repo_by_id(self, module_org):
        """Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        :id: d4db5eaa-7379-4788-9b72-76f2589d8f20

        :expectedresults: Random repository can be deleted from random product
            without altering the other products.
        """
        products = [
            make_product_wait({'organization-id': module_org.id}) for _ in range(randint(2, 5))
        ]
        repos = []
        for product in products:
            for _ in range(randint(2, 3)):
                repos.append(_repo(product['id']))
        # Select random repository and delete it
        repo = choice(repos)
        repos.remove(repo)
        Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            Repository.info({'id': repo['id']})
        # Verify other repositories were not touched
        product_ids = [product['id'] for product in products]
        for repo in repos:
            result = Repository.info({'id': repo['id']})
            assert result['product']['id'] in product_ids


class TestDockerContentView:
    """Tests specific to using ``Docker`` repositories with Content Views.

    :CaseComponent: ContentViews

    :Assignee: ltran

    :CaseLevel: Integration
    """

    @pytest.mark.tier2
    def test_positive_add_docker_repo_by_id(self, module_org, repo):
        """Add one Docker-type repository to a non-composite content view

        :id: 87d6c7bb-92f8-4a32-8ad2-2a1af896500b

        :expectedresults: A repository is created with a Docker repository and
            the product is added to a non-composite content view
        """
        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert repo['id'] in [repo_['id'] for repo_ in content_view['container-image-repositories']]

    @pytest.mark.tier2
    def test_positive_add_docker_repos_by_id(self, module_org, module_product):
        """Add multiple Docker-type repositories to a non-composite CV.

        :id: 2eb19e28-a633-4c21-9469-75a686c83b34

        :expectedresults: Repositories are created with Docker upstream
            repositories and the product is added to a non-composite content
            view.
        """
        repos = [_repo(module_product.id) for _ in range(randint(2, 5))]
        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        for repo in repos:
            ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        content_view = ContentView.info({'id': content_view['id']})

        assert {repo['id'] for repo in repos} == {
            repo['id'] for repo in content_view['container-image-repositories']
        }

    @pytest.mark.tier2
    def test_positive_add_synced_docker_repo_by_id(self, module_org, repo):
        """Create and sync a Docker-type repository

        :id: 6f51d268-ed23-48ab-9dea-cd3571daa647

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.
        """
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['container-image-manifests']) > 0

        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert repo['id'] in [repo_['id'] for repo_ in content_view['container-image-repositories']]

    @pytest.mark.tier2
    def test_positive_add_docker_repo_by_id_to_ccv(self, module_org, content_view):
        """Add one Docker-type repository to a composite content view

        :id: 8e2ef5ba-3cdf-4ef9-a22a-f1701e20a5d5

        :expectedresults: A repository is created with a Docker repository and
            the product is added to a content view which is then added to a
            composite content view.

        :BZ: 1359665
        """
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1
        comp_content_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.update(
            {
                'id': comp_content_view['id'],
                'component-ids': content_view['versions'][0]['id'],
            }
        )
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert content_view['versions'][0]['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

    @pytest.mark.tier2
    def test_positive_add_docker_repos_by_id_to_ccv(self, module_org, module_product):
        """Add multiple Docker-type repositories to a composite content view.

        :id: b79cbc97-3dba-4059-907d-19316684d569

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a random number of content
            views which are then added to a composite content view.

        :BZ: 1359665
        """
        cv_versions = []
        for _ in range(randint(2, 5)):
            content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
            repo = _repo(module_product.id)
            ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
            ContentView.publish({'id': content_view['id']})
            content_view = ContentView.info({'id': content_view['id']})
            assert len(content_view['versions']) == 1
            cv_versions.append(content_view['versions'][0])
        comp_content_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.update(
            {
                'component-ids': [cv_version['id'] for cv_version in cv_versions],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        comp_ids = [component['id'] for component in comp_content_view['components']]
        for cv_version in cv_versions:
            assert cv_version['id'] in comp_ids

    @pytest.mark.tier2
    def test_positive_publish_with_docker_repo(self, content_view):
        """Add Docker-type repository to content view and publish it once.

        :id: 28480de3-ffb5-4b8e-8174-fffffeef6af4

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published only once.
        """
        assert len(content_view['versions']) == 0
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

    @pytest.mark.tier2
    def test_positive_publish_with_docker_repo_composite(self, content_view, module_org):
        """Add Docker-type repository to composite CV and publish it once.

        :id: 2d75419b-73ed-4f29-ae0d-9af8d9624c87

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published once and added to a composite content view which is also
            published once.

        :BZ: 1359665
        """
        assert len(content_view['versions']) == 0

        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

        comp_content_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.update(
            {
                'component-ids': content_view['versions'][0]['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert content_view['versions'][0]['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert len(comp_content_view['versions']) == 1

    @pytest.mark.tier2
    def test_positive_publish_multiple_with_docker_repo(self, content_view):
        """Add Docker-type repository to content view and publish it multiple
        times.

        :id: 33c1b2ee-ae8a-4a7e-8254-123d97aaaa58

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published multiple times.
        """
        assert len(content_view['versions']) == 0

        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == publish_amount

    @pytest.mark.tier2
    def test_positive_publish_multiple_with_docker_repo_composite(self, module_org, content_view):
        """Add Docker-type repository to content view and publish it multiple
        times.

        :id: 014adf90-d399-4a99-badb-76ee03a2c350

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            added to a composite content view which is then published multiple
            times.

        :BZ: 1359665
        """
        assert len(content_view['versions']) == 0

        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

        comp_content_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.update(
            {
                'component-ids': content_view['versions'][0]['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert content_view['versions'][0]['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert len(comp_content_view['versions']) == publish_amount

    @pytest.mark.tier2
    def test_positive_promote_with_docker_repo(self, module_org, module_lce, content_view):
        """Add Docker-type repository to content view and publish it.
        Then promote it to the next available lifecycle-environment.

        :id: a7df98f4-0ec0-40f6-8941-3dbb776d47b9

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environment.
        """
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

        cvv = ContentView.version_info({'id': content_view['versions'][0]['id']})
        assert len(cvv['lifecycle-environments']) == 1

        ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': module_lce.id})
        cvv = ContentView.version_info({'id': content_view['versions'][0]['id']})
        assert len(cvv['lifecycle-environments']) == 2

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_promote_multiple_with_docker_repo(self, module_org, content_view):
        """Add Docker-type repository to content view and publish it.
        Then promote it to multiple available lifecycle-environments.

        :id: e9432bc4-a709-44d7-8e1d-00ca466aa32d

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environments.
        """
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

        cvv = ContentView.version_info({'id': content_view['versions'][0]['id']})
        assert len(cvv['lifecycle-environments']) == 1

        lces = [
            make_lifecycle_environment({'organization-id': module_org.id})
            for _ in range(1, randint(3, 6))
        ]

        for expected_lces, lce in enumerate(lces, start=2):
            ContentView.version_promote({'id': cvv['id'], 'to-lifecycle-environment-id': lce['id']})
            cvv = ContentView.version_info({'id': cvv['id']})
            assert len(cvv['lifecycle-environments']) == expected_lces

    @pytest.mark.tier2
    def test_positive_promote_with_docker_repo_composite(
        self, module_org, module_lce, content_view
    ):
        """Add Docker-type repository to composite content view and publish it.
        Then promote it to the next available lifecycle-environment.

        :id: fb7d132e-d7fa-4890-a0ec-746dd093513e

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environment.

        :BZ: 1359665
        """
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

        comp_content_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.update(
            {
                'component-ids': content_view['versions'][0]['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert content_view['versions'][0]['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        cvv = ContentView.version_info({'id': comp_content_view['versions'][0]['id']})
        assert len(cvv['lifecycle-environments']) == 1

        ContentView.version_promote(
            {
                'id': comp_content_view['versions'][0]['id'],
                'to-lifecycle-environment-id': module_lce.id,
            }
        )
        cvv = ContentView.version_info({'id': comp_content_view['versions'][0]['id']})
        assert len(cvv['lifecycle-environments']) == 2

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_promote_multiple_with_docker_repo_composite(self, content_view, module_org):
        """Add Docker-type repository to composite content view and publish it.
        Then promote it to the multiple available lifecycle-environments.

        :id: 345288d6-581b-4c07-8062-e58cb6343f1b

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environments.

        :BZ: 1359665
        """
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

        comp_content_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.update(
            {
                'component-ids': content_view['versions'][0]['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert content_view['versions'][0]['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        cvv = ContentView.version_info({'id': comp_content_view['versions'][0]['id']})
        assert len(cvv['lifecycle-environments']) == 1

        lces = [
            make_lifecycle_environment({'organization-id': module_org.id})
            for _ in range(1, randint(3, 6))
        ]

        for expected_lces, lce in enumerate(lces, start=2):
            ContentView.version_promote(
                {
                    'id': cvv['id'],
                    'to-lifecycle-environment-id': lce['id'],
                }
            )
            cvv = ContentView.version_info({'id': cvv['id']})
            assert len(cvv['lifecycle-environments']) == expected_lces

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_name_pattern_change(self, module_org):
        """Promote content view with Docker repository to lifecycle environment.
        Change registry name pattern for that environment. Verify that repository
        name on product changed according to new pattern.

        :id: 63c99ae7-238b-40ed-8cc1-d847eb4e6d65

        :expectedresults: Container repository name is changed
            according to new pattern.
        """
        lce = make_lifecycle_environment({'organization-id': module_org.id})
        pattern_prefix = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = (
            f'{pattern_prefix}-<%= content_view.label %>/<%= repository.docker_upstream_name %>'
        )

        repo = _repo(
            make_product_wait({'organization-id': module_org.id})['id'],
            name=gen_string('alpha', 5),
            upstream_name=docker_upstream_name,
        )
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})

        ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        LifecycleEnvironment.update(
            {
                'registry-name-pattern': new_pattern,
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )
        lce = LifecycleEnvironment.info({'id': lce['id'], 'organization-id': module_org.id})
        assert lce['registry-name-pattern'] == new_pattern

        repo = Repository.list(
            {'name': repo['name'], 'environment-id': lce['id'], 'organization-id': module_org.id}
        )[0]
        expected_name = f'{pattern_prefix}-{content_view["label"]}/{docker_upstream_name}'.lower()
        assert Repository.info({'id': repo['id']})['container-repository-name'] == expected_name

    @pytest.mark.tier2
    def test_positive_product_name_change_after_promotion(self, module_org):
        """Promote content view with Docker repository to lifecycle environment.
        Change product name. Verify that repository name on product changed
        according to new pattern.

        :id: 92279755-717c-415c-88b6-4cc1202072e2

        :expectedresults: Container repository name is changed
            according to new pattern.
        """
        old_prod_name = gen_string('alpha', 5)
        new_prod_name = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = '<%= content_view.label %>/<%= product.name %>'

        lce = make_lifecycle_environment({'organization-id': module_org.id})
        prod = make_product_wait({'organization-id': module_org.id, 'name': old_prod_name})
        repo = _repo(prod['id'], name=gen_string('alpha', 5), upstream_name=docker_upstream_name)
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        LifecycleEnvironment.update(
            {
                'registry-name-pattern': new_pattern,
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )
        lce = LifecycleEnvironment.info({'id': lce['id'], 'organization-id': module_org.id})
        assert lce['registry-name-pattern'] == new_pattern

        ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        Product.update({'name': new_prod_name, 'id': prod['id']})

        repo = Repository.list(
            {'name': repo['name'], 'environment-id': lce['id'], 'organization-id': module_org.id}
        )[0]
        expected_name = f'{content_view["label"]}/{old_prod_name}'.lower()
        assert Repository.info({'id': repo['id']})['container-repository-name'] == expected_name

        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        ContentView.version_promote(
            {
                'id': content_view['versions'][-1]['id'],
                'to-lifecycle-environment-id': lce['id'],
            }
        )

        repo = Repository.list(
            {
                'name': repo['name'],
                'environment-id': lce['id'],
                'organization-id': module_org.id,
            }
        )[0]
        expected_name = f'{content_view["label"]}/{new_prod_name}'.lower()
        assert Repository.info({'id': repo['id']})['container-repository-name'] == expected_name

    @pytest.mark.tier2
    def test_positive_repo_name_change_after_promotion(self, module_org):
        """Promote content view with Docker repository to lifecycle environment.
        Change repository name. Verify that Docker repository name on product
        changed according to new pattern.

        :id: f094baab-e823-47e0-939d-bd0d88eb1538

        :expectedresults: Container repository name is changed
            according to new pattern.
        """
        old_repo_name = gen_string('alpha', 5)
        new_repo_name = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = '<%= content_view.label %>/<%= repository.name %>'

        lce = make_lifecycle_environment({'organization-id': module_org.id})
        prod = make_product_wait({'organization-id': module_org.id})
        repo = _repo(prod['id'], name=old_repo_name, upstream_name=docker_upstream_name)
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        LifecycleEnvironment.update(
            {
                'registry-name-pattern': new_pattern,
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )
        ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        Repository.update({'name': new_repo_name, 'id': repo['id'], 'product-id': prod['id']})

        repo = Repository.list(
            {
                'name': new_repo_name,
                'environment-id': lce['id'],
                'organization-id': module_org.id,
            }
        )[0]
        expected_name = f'{content_view["label"]}/{old_repo_name}'.lower()
        assert Repository.info({'id': repo['id']})['container-repository-name'] == expected_name

        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        ContentView.version_promote(
            {
                'id': content_view['versions'][-1]['id'],
                'to-lifecycle-environment-id': lce['id'],
            }
        )

        repo = Repository.list(
            {
                'name': new_repo_name,
                'environment-id': lce['id'],
                'organization-id': module_org.id,
            }
        )[0]
        expected_name = f'{content_view["label"]}/{new_repo_name}'.lower()
        assert Repository.info({'id': repo['id']})['container-repository-name'] == expected_name

    @pytest.mark.tier2
    def test_negative_set_non_unique_name_pattern_and_promote(self, module_org):
        """Set registry name pattern to one that does not guarantee uniqueness.
        Try to promote content view with multiple Docker repositories to
        lifecycle environment. Verify that content has not been promoted.

        :id: eaf5e7ac-93c9-46c6-b538-4d6bd73ab9fc

        :expectedresults: Content view is not promoted
        """
        docker_upstream_names = ['hello-world', 'alpine']
        new_pattern = '<%= organization.label %>'

        lce = make_lifecycle_environment(
            {'organization-id': module_org.id, 'registry-name-pattern': new_pattern}
        )

        prod = make_product_wait({'organization-id': module_org.id})
        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        for docker_name in docker_upstream_names:
            repo = _repo(prod['id'], upstream_name=docker_name)
            Repository.synchronize({'id': repo['id']})
            ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})

        with pytest.raises(CLIReturnCodeError):
            ContentView.version_promote(
                {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
            )

    @pytest.mark.tier2
    def test_negative_promote_and_set_non_unique_name_pattern(self, module_org, module_product):
        """Promote content view with multiple Docker repositories to
        lifecycle environment. Set registry name pattern to one that
        does not guarantee uniqueness. Verify that pattern has not been
        changed.

        :id: 9f952224-084f-48d1-b2ea-85f3621becea

        :expectedresults: Registry name pattern is not changed
        """
        docker_upstream_names = ['hello-world', 'alpine']
        new_pattern = '<%= organization.label %>'

        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        for docker_name in docker_upstream_names:
            repo = _repo(module_product.id, upstream_name=docker_name)
            Repository.synchronize({'id': repo['id']})
            ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        lce = make_lifecycle_environment({'organization-id': module_org.id})
        ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )

        with pytest.raises(CLIReturnCodeError):
            LifecycleEnvironment.update(
                {
                    'registry-name-pattern': new_pattern,
                    'id': lce['id'],
                    'organization-id': module_org.id,
                }
            )


class TestDockerActivationKey:
    """Tests specific to adding ``Docker`` repositories to Activation Keys.

    :CaseComponent: ActivationKeys

    :Assignee: chiggins

    :CaseLevel: Integration
    """

    @pytest.mark.tier2
    def test_positive_add_docker_repo_cv(self, module_org, module_lce, content_view_promote):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then create an activation key and associate it with the
        Docker content view.

        :id: bb128642-d39f-45c2-aa69-a4776ea536a2

        :expectedresults: Docker-based content view can be added to activation
            key
        """
        activation_key = make_activation_key(
            {
                'content-view-id': content_view_promote['content-view-id'],
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )
        assert activation_key['content-view'] == content_view_promote['content-view-name']

    @pytest.mark.tier2
    def test_positive_remove_docker_repo_cv(self, module_org, module_lce, content_view_promote):
        """Add Docker-type repository to a non-composite content view
        and publish it. Create an activation key and associate it with the
        Docker content view. Then remove this content view from the activation
        key.

        :id: d696e5fe-1818-46ce-9499-924c96e1ef88

        :expectedresults: Docker-based content view can be added and then
            removed from the activation key.
        """
        activation_key = make_activation_key(
            {
                'content-view-id': content_view_promote['content-view-id'],
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )
        assert activation_key['content-view'] == content_view_promote['content-view-name']

        # Create another content view replace with
        another_cv = make_content_view({'composite': False, 'organization-id': module_org.id})
        ContentView.publish({'id': another_cv['id']})
        another_cv = ContentView.info({'id': another_cv['id']})
        ContentView.version_promote(
            {'id': another_cv['versions'][0]['id'], 'to-lifecycle-environment-id': module_lce.id}
        )

        ActivationKey.update(
            {
                'id': activation_key['id'],
                'organization-id': module_org.id,
                'content-view-id': another_cv['id'],
                'lifecycle-environment-id': module_lce.id,
            }
        )
        activation_key = ActivationKey.info({'id': activation_key['id']})
        assert activation_key['content-view'] != content_view_promote['content-view-name']

    @pytest.mark.tier2
    def test_positive_add_docker_repo_ccv(self, module_org, module_lce, content_view_publish):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then add this content view to a composite content view
        and publish it. Create an activation key and associate it with the
        composite Docker content view.

        :id: 1d9b82fd-8dab-4fd9-ad35-656d712d56a2

        :expectedresults: Docker-based content view can be added to activation
            key

        :BZ: 1359665
        """
        comp_content_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.update(
            {
                'component-ids': content_view_publish['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert content_view_publish['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        comp_cvv = ContentView.version_info({'id': comp_content_view['versions'][0]['id']})
        ContentView.version_promote(
            {'id': comp_cvv['id'], 'to-lifecycle-environment-id': module_lce.id}
        )
        activation_key = make_activation_key(
            {
                'content-view-id': comp_content_view['id'],
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )
        assert activation_key['content-view'] == comp_content_view['name']

    @pytest.mark.tier2
    def test_positive_remove_docker_repo_ccv(self, module_org, module_lce, content_view_publish):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then add this content view to a composite content view
        and publish it. Create an activation key and associate it with the
        composite Docker content view. Then, remove the composite content view
        from the activation key.

        :id: b4e63537-d3a8-4afa-8e18-57052b93fb4c

        :expectedresults: Docker-based composite content view can be added and
            then removed from the activation key.

        :BZ: 1359665
        """
        comp_content_view = make_content_view({'composite': True, 'organization-id': module_org.id})
        ContentView.update(
            {
                'component-ids': content_view_publish['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        assert content_view_publish['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = ContentView.info({'id': comp_content_view['id']})
        comp_cvv = ContentView.version_info({'id': comp_content_view['versions'][0]['id']})
        ContentView.version_promote(
            {'id': comp_cvv['id'], 'to-lifecycle-environment-id': module_lce.id}
        )
        activation_key = make_activation_key(
            {
                'content-view-id': comp_content_view['id'],
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )
        assert activation_key['content-view'] == comp_content_view['name']

        # Create another content view replace with
        another_cv = make_content_view({'composite': False, 'organization-id': module_org.id})
        ContentView.publish({'id': another_cv['id']})
        another_cv = ContentView.info({'id': another_cv['id']})
        ContentView.version_promote(
            {'id': another_cv['versions'][0]['id'], 'to-lifecycle-environment-id': module_lce.id}
        )

        ActivationKey.update(
            {
                'id': activation_key['id'],
                'organization-id': module_org.id,
                'content-view-id': another_cv['id'],
                'lifecycle-environment-id': module_lce.id,
            }
        )
        activation_key = ActivationKey.info({'id': activation_key['id']})
        assert activation_key['content-view'] != comp_content_view['name']


class TestDockerClient:
    """Tests specific to using ``Docker`` as a client to pull Docker images
    from a Satellite 6 instance.

    :CaseComponent: ContentManagement

    :Assignee: ltran

    :CaseLevel: System

    :CaseImportance: Medium
    """

    @pytest.mark.tier3
    def test_positive_pull_image(self, module_org, container_contenthost, target_sat):
        """A Docker-enabled client can use ``docker pull`` to pull a
        Docker image off a Satellite 6 instance.

        :id: 023f0538-2aad-4f87-b8a8-6ccced648366

        :Steps:

            1. Publish and promote content view with Docker content
            2. Register Docker-enabled client against Satellite 6.

        :expectedresults: Client can pull Docker images from server and run it.

        :parametrized: yes
        """
        product = make_product_wait({'organization-id': module_org.id})
        repo = _repo(product['id'])
        Repository.synchronize({'id': repo['id']})
        repo = Repository.info({'id': repo['id']})
        try:
            result = container_contenthost.execute(
                f'docker login -u {settings.server.admin_username}'
                f' -p {settings.server.admin_password} {target_sat.hostname}'
            )
            assert result.status == 0

            # publishing takes few seconds sometimes
            result, _ = wait_for(
                lambda: container_contenthost.execute(f'docker pull {repo["published-at"]}'),
                num_sec=60,
                delay=2,
                fail_condition=lambda out: out.status != 0,
                logger=logger,
            )
            assert result.status == 0
            try:
                result = container_contenthost.execute(f'docker run {repo["published-at"]}')
                assert result.status == 0
            finally:
                # Stop and remove the container
                result = container_contenthost.execute(
                    f'docker ps -a | grep {repo["published-at"]}'
                )
                container_id = result.stdout[0].split()[0]
                container_contenthost.execute(f'docker stop {container_id}')
                container_contenthost.execute(f'docker rm {container_id}')
        finally:
            # Remove docker image
            container_contenthost.execute(f'docker rmi {repo["published-at"]}')

    @pytest.mark.skip_if_not_set('docker')
    @pytest.mark.tier3
    @pytest.mark.e2e
    def test_positive_container_admin_end_to_end_search(
        self, module_org, container_contenthost, target_sat
    ):
        """Verify that docker command line can be used against
        Satellite server to search for container images stored
        on Satellite instance.

        :id: cefa74e1-e40d-4f47-853b-1268643cea2f

        :steps:

            1. Publish and promote content view with Docker content
            2. Set 'Unauthenticated Pull' option to false
            3. Try to search for docker images on Satellite
            4. Use Docker client to login to Satellite docker hub
            5. Search for docker images
            6. Use Docker client to log out of Satellite docker hub
            7. Try to search for docker images (ensure last search result
               is caused by change of Satellite option and not login/logout)
            8. Set 'Unauthenticated Pull' option to true
            9. Search for docker images

        :expectedresults: Client can search for docker images stored
            on Satellite instance

        :parametrized: yes
        """
        pattern_prefix = gen_string('alpha', 5)
        registry_name_pattern = (
            f'{pattern_prefix}-<%= content_view.label %>/<%= repository.docker_upstream_name %>'
        )

        # Satellite setup: create product and add Docker repository;
        # create content view and add Docker repository;
        # create lifecycle environment and promote content view to it
        lce = make_lifecycle_environment({'organization-id': module_org.id})
        product = make_product_wait({'organization-id': module_org.id})
        repo = _repo(product['id'], upstream_name=CONTAINER_UPSTREAM_NAME)
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        LifecycleEnvironment.update(
            {
                'registry-name-pattern': registry_name_pattern,
                'registry-unauthenticated-pull': 'false',
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )
        docker_repo_uri = (
            f' {target_sat.hostname}/{pattern_prefix}-{content_view["label"]}/'
            f'{CONTAINER_UPSTREAM_NAME} '
        ).lower()

        # 3. Try to search for docker images on Satellite
        remote_search_command = f'docker search {target_sat.hostname}/{CONTAINER_UPSTREAM_NAME}'
        result = container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri not in result.stdout

        # 4. Use Docker client to login to Satellite docker hub
        result = container_contenthost.execute(
            f'docker login -u {settings.server.admin_username}'
            f' -p {settings.server.admin_password} {target_sat.hostname}'
        )
        assert result.status == 0

        # 5. Search for docker images
        result = container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri in result.stdout

        # 6. Use Docker client to log out of Satellite docker hub
        result = container_contenthost.execute(f'docker logout {target_sat.hostname}')
        assert result.status == 0

        # 7. Try to search for docker images
        result = container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri not in result.stdout

        # 8. Set 'Unauthenticated Pull' option to true
        LifecycleEnvironment.update(
            {
                'registry-unauthenticated-pull': 'true',
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )

        # 9. Search for docker images
        result = container_contenthost.execute(remote_search_command)
        assert result.status == 0
        assert docker_repo_uri in result.stdout

    @pytest.mark.skip_if_not_set('docker')
    @pytest.mark.tier3
    @pytest.mark.e2e
    def test_positive_container_admin_end_to_end_pull(
        self, module_org, container_contenthost, target_sat
    ):
        """Verify that docker command line can be used against
        Satellite server to pull in container images stored
        on Satellite instance.

        :id: 2a331f88-406b-4a5c-ae70-302a9994077f

        :steps:

            1. Publish and promote content view with Docker content
            2. Set 'Unauthenticated Pull' option to false
            3. Try to pull in docker image from Satellite
            4. Use Docker client to login to Satellite container registry
            5. Pull in docker image
            6. Use Docker client to log out of Satellite container registry
            7. Try to pull in docker image (ensure next pull result
               is caused by change of Satellite option and not login/logout)
            8. Set 'Unauthenticated Pull' option to true
            9. Pull in docker image

        :expectedresults: Client can pull in docker images stored
            on Satellite instance

        :parametrized: yes
        """
        pattern_prefix = gen_string('alpha', 5)
        docker_upstream_name = CONTAINER_UPSTREAM_NAME
        registry_name_pattern = (
            f'{pattern_prefix}-<%= content_view.label %>/<%= repository.docker_upstream_name %>'
        )

        # Satellite setup: create product and add Docker repository;
        # create content view and add Docker repository;
        # create lifecycle environment and promote content view to it
        lce = make_lifecycle_environment({'organization-id': module_org.id})
        product = make_product_wait({'organization-id': module_org.id})
        repo = _repo(product['id'], upstream_name=docker_upstream_name)
        Repository.synchronize({'id': repo['id']})
        content_view = make_content_view({'composite': False, 'organization-id': module_org.id})
        ContentView.add_repository({'id': content_view['id'], 'repository-id': repo['id']})
        ContentView.publish({'id': content_view['id']})
        content_view = ContentView.info({'id': content_view['id']})
        ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        LifecycleEnvironment.update(
            {
                'registry-name-pattern': registry_name_pattern,
                'registry-unauthenticated-pull': 'false',
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )
        docker_repo_uri = (
            f'{target_sat.hostname}/{pattern_prefix}-{content_view["label"]}/'
            f'{docker_upstream_name}'
        ).lower()

        # 3. Try to pull in docker image from Satellite
        docker_pull_command = f'docker pull {docker_repo_uri}'
        result = container_contenthost.execute(docker_pull_command)
        assert result.status == 1

        # 4. Use Docker client to login to Satellite docker hub
        result = container_contenthost.execute(
            f'docker login -u {settings.server.admin_username}'
            f' -p {settings.server.admin_password} {target_sat.hostname}'
        )
        assert result.status == 0

        # 5. Pull in docker image
        # publishing takes few seconds sometimes
        result, _ = wait_for(
            lambda: container_contenthost.execute(docker_pull_command),
            num_sec=60,
            delay=2,
            fail_condition=lambda out: out.status != 0,
            logger=logger,
        )
        assert result.status == 0

        # 6. Use Docker client to log out of Satellite docker hub
        result = container_contenthost.execute(f'docker logout {target_sat.hostname}')
        assert result.status == 0

        # 7. Try to pull in docker image
        result = container_contenthost.execute(docker_pull_command)
        assert result.status == 1

        # 8. Set 'Unauthenticated Pull' option to true
        LifecycleEnvironment.update(
            {
                'registry-unauthenticated-pull': 'true',
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )

        # 9. Pull in docker image
        result = container_contenthost.execute(docker_pull_command)
        assert result.status == 0

    @pytest.mark.skip_if_not_set('docker')
    @pytest.mark.tier3
    @pytest.mark.upgrade
    def test_positive_upload_image(self, module_org, target_sat, container_contenthost):
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
            Docker image from a Satellite instance, add a new package and
            upload the modified image (plus layer) back to the Satellite.

        :parametrized: yes
        """
        try:
            """
            These functions were removed, but let's leave them here
            to maintain overall test logic - in case required functionality
            is eventually implemented

            compute_resource = make_compute_resource({
                'organization-ids': [module_org.id],
                'provider': 'Docker',
                'url': f'http://{container_contenthost.ip_addr}:2375',
            })
            container = make_container({
                'compute-resource-id': compute_resource['id'],
                'organization-ids': [module_org.id],
            })
            Docker.container.start({'id': container['id']})
            """
            container = {'uuid': 'stubbed test'}
            repo_name = gen_string('alphanumeric').lower()

            # Commit a new docker image and verify image was created
            image_name = f'{repo_name}/{CONTAINER_UPSTREAM_NAME}'
            result = container_contenthost.execute(
                f'docker commit {container["uuid"]} {image_name}:latest && '
                f'docker images --all | grep {image_name}'
            )
            assert result.status == 0

            # Save the image to a tar archive
            result = container_contenthost.execute(f'docker save -o {repo_name}.tar {image_name}')
            assert result.status == 0

            tar_file = f'{repo_name}.tar'
            container_contenthost.get(remote_path=tar_file)
            target_sat.put(
                local_path=tar_file,
                remote_path=f'/tmp/{tar_file}',
            )

            # Upload tarred repository
            product = make_product_wait({'organization-id': module_org.id})
            repo = _repo(product['id'])
            Repository.upload_content({'id': repo['id'], 'path': f'/tmp/{tar_file}'})

            # Verify repository was uploaded successfully
            repo = Repository.info({'id': repo['id']})
            assert target_sat.hostname == repo['published-at']

            repo_name = '-'.join((module_org.label, product['label'], repo['label'])).lower()
            assert repo_name in repo['published-at']
        finally:
            # Remove the archive
            target_sat.execute(f'rm -f /tmp/{tar_file}')
