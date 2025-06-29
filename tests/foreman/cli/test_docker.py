"""Tests for the Docker feature.

:Requirement: Docker

:CaseAutomation: Automated

:CaseImportance: High

"""

from random import choice, randint

from fauxfactory import gen_string, gen_url
import pytest

from robottelo.config import settings
from robottelo.constants import (
    EXPIRED_MANIFEST,
    REPO_TYPE,
    DataFile,
)
from robottelo.exceptions import CLIReturnCodeError
from robottelo.utils.datafactory import (
    invalid_docker_upstream_names,
    parametrized,
    valid_docker_repository_names,
    valid_docker_upstream_names,
)


def _repo(sat, product_id, name=None, upstream_name=None, url=None):
    """Creates a Docker-based repository.

    :param product_id: ID of the ``Product``.
    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name of an existing upstream repository.
        If ``None`` then defaults to settings.container.upstream_name constant.
    :param str url: URL of repository. If ``None`` then defaults to
        settings.container.registry_hub constant.
    :return: A ``Repository`` object.
    """
    return sat.cli_factory.make_repository(
        {
            'content-type': REPO_TYPE['docker'],
            'docker-upstream-name': upstream_name or settings.container.upstream_name,
            'name': name or gen_string('alpha', 5),
            'product-id': product_id,
            'url': url or settings.container.registry_hub,
        }
    )


def _content_view(sat, repo_id, org_id):
    """Create a content view and link it to the given repository."""
    content_view = sat.cli_factory.make_content_view(
        {'composite': False, 'organization-id': org_id}
    )
    sat.cli.ContentView.add_repository({'id': content_view['id'], 'repository-id': repo_id})
    return sat.cli.ContentView.info({'id': content_view['id']})


@pytest.fixture
def repo(module_product, target_sat):
    return _repo(target_sat, module_product.id)


@pytest.fixture
def content_view(module_org, target_sat, repo):
    return _content_view(target_sat, repo['id'], module_org.id)


@pytest.fixture
def content_view_publish(content_view, target_sat):
    target_sat.cli.ContentView.publish({'id': content_view['id']})
    content_view = target_sat.cli.ContentView.info({'id': content_view['id']})
    return target_sat.cli.ContentView.version_info({'id': content_view['versions'][0]['id']})


@pytest.fixture
def content_view_promote(content_view_publish, module_lce, target_sat):
    target_sat.cli.ContentView.version_promote(
        {
            'id': content_view_publish['id'],
            'to-lifecycle-environment-id': module_lce.id,
        }
    )
    return target_sat.cli.ContentView.version_info({'id': content_view_publish['id']})


class TestDockerManifest:
    """Tests related to docker manifest command

    :CaseComponent: Repositories

    :team: Phoenix-content
    """

    def test_positive_read_docker_tags(self, repo, module_target_sat):
        """docker manifest displays tags information for a docker manifest

        :id: 59b605b5-ac2d-46e3-a85e-a259e78a07a8

        :expectedresults: docker manifest displays tags info for a docker
            manifest

        :CaseImportance: Medium

        :BZ: 1658274
        """
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        # Grab all available manifests related to repository
        manifests_list = module_target_sat.cli.Docker.manifest.list({'repository-id': repo['id']})
        # Some manifests do not have tags associated with it, ignore those
        # because we want to check the tag information
        manifests = [m_iter for m_iter in manifests_list if m_iter['tags'] != '']
        assert manifests
        tags_list = module_target_sat.cli.Docker.tag.list({'repository-id': repo['id']})
        # Extract tag names for the repository out of docker tag list
        repo_tag_names = [tag['tag'] for tag in tags_list]
        for manifest in manifests:
            manifest_info = module_target_sat.cli.Docker.manifest.info({'id': manifest['id']})
            # Check that manifest's tag is listed in tags for the repository
            for t_iter in manifest_info['tags']:
                assert t_iter['name'] in repo_tag_names


class TestDockerRepository:
    """Tests specific to performing CRUD methods against ``Docker`` repositories.

    :CaseComponent: Repositories

    :team: Phoenix-content
    """

    @pytest.mark.parametrize('name', **parametrized(valid_docker_repository_names()))
    def test_positive_create_with_name(self, module_product, name, module_target_sat):
        """Create one Docker-type repository

        :id: e82a36c8-3265-4c10-bafe-c7e07db3be78

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
         repository.

        :CaseImportance: Critical
        """
        repo = _repo(module_target_sat, module_product.id, name)
        assert repo['name'] == name
        assert repo['upstream-repository-name'] == settings.container.upstream_name
        assert repo['content-type'] == REPO_TYPE['docker']

    def test_positive_create_repos_using_same_product(
        self, module_org, module_product, module_target_sat
    ):
        """Create multiple Docker-type repositories

        :id: 6dd25cf4-f8b6-4958-976a-c116daf27b44

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to the same product.

        """
        repo_names = set()
        for _ in range(randint(2, 5)):
            repo = _repo(module_target_sat, module_product.id)
            repo_names.add(repo['name'])
        product = module_target_sat.cli.Product.info(
            {'id': module_product.id, 'organization-id': module_org.id}
        )
        assert repo_names.issubset({repo_['repo-name'] for repo_ in product['content']})

    def test_positive_create_repos_using_multiple_products(self, module_org, module_target_sat):
        """Create multiple Docker-type repositories on multiple
        products.

        :id: 43f4ab0d-731e-444e-9014-d663ff945f36

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to their respective
            products.

        """
        for _ in range(randint(2, 5)):
            product = module_target_sat.cli_factory.make_product_wait(
                {'organization-id': module_org.id}
            )
            repo_names = set()
            for _ in range(randint(2, 3)):
                repo = _repo(module_target_sat, product['id'])
                repo_names.add(repo['name'])
            product = module_target_sat.cli.Product.info(
                {'id': product['id'], 'organization-id': module_org.id}
            )
            assert repo_names == {repo_['repo-name'] for repo_ in product['content']}

    def test_positive_sync(self, repo, module_target_sat):
        """Create and sync a Docker-type repository

        :id: bff1d40e-181b-48b2-8141-8c86e0db62a2

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.

        :CaseImportance: Critical
        """
        assert int(repo['content-counts']['container-manifests']) == 0
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['container-manifests']) > 0

    @pytest.mark.parametrize('new_name', **parametrized(valid_docker_repository_names()))
    def test_positive_update_name(self, repo, new_name, module_target_sat):
        """Create a Docker-type repository and update its name.

        :id: 8b3a8496-e9bd-44f1-916f-6763a76b9b1b

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
            repository and that its name can be updated.

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.update(
            {'id': repo['id'], 'new-name': new_name, 'url': repo['url']}
        )
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['name'] == new_name

    @pytest.mark.parametrize('new_upstream_name', **parametrized(valid_docker_upstream_names()))
    def test_positive_update_upstream_name(self, repo, new_upstream_name, module_target_sat):
        """Create a Docker-type repository and update its upstream name.

        :id: 1a6985ed-43ec-4ea6-ba27-e3870457ac56

        :Verifies: SAT-32427

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can be updated.

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.update(
            {
                'docker-upstream-name': new_upstream_name,
                'id': repo['id'],
                'url': repo['url'],
            }
        )
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['upstream-repository-name'] == new_upstream_name
        repo_from_list = module_target_sat.cli.Repository.list(
            {'search': f"label = {repo['label']}", 'fields': 'Upstream repository name'}
        )[0]
        assert repo_from_list['upstream-repository-name'] == new_upstream_name

    @pytest.mark.parametrize('new_upstream_name', **parametrized(invalid_docker_upstream_names()))
    def test_negative_update_upstream_name(self, repo, new_upstream_name, module_target_sat):
        """Attempt to update upstream name for a Docker-type repository.

        :id: 798651af-28b2-4907-b3a7-7c560bf66c7c

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can not be updated with
            invalid values.

        :CaseImportance: Critical
        """
        with pytest.raises(CLIReturnCodeError, match='Validation failed: Docker upstream name'):
            module_target_sat.cli.Repository.update(
                {
                    'docker-upstream-name': new_upstream_name,
                    'id': repo['id'],
                    'url': repo['url'],
                }
            )

    @pytest.mark.skip_if_not_set('docker')
    def test_positive_create_with_long_upstream_name(self, module_product, module_target_sat):
        """Create a docker repository with upstream name longer than 30
        characters

        :id: 4fe47c02-a8bd-4630-9102-189a9d268b83

        :customerscenario: true

        :BZ: 1424689

        :expectedresults: docker repository is successfully created

        :CaseImportance: Critical
        """
        repo = _repo(
            module_target_sat,
            module_product.id,
            upstream_name=settings.container.rh.upstream_name,
            url=settings.docker.external_registry_1,
        )
        assert repo['upstream-repository-name'] == settings.container.rh.upstream_name

    @pytest.mark.skip_if_not_set('docker')
    def test_positive_update_with_long_upstream_name(self, repo, module_target_sat):
        """Create a docker repository and update its upstream name with longer
        than 30 characters value

        :id: 97260cce-9677-4a3e-942b-e95e2714500a

        :BZ: 1424689

        :expectedresults: docker repository is successfully updated

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.update(
            {
                'docker-upstream-name': settings.container.rh.upstream_name,
                'id': repo['id'],
                'url': settings.docker.external_registry_1,
            }
        )
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['upstream-repository-name'] == settings.container.rh.upstream_name

    def test_positive_update_url(self, repo, module_target_sat):
        """Create a Docker-type repository and update its URL.

        :id: 73caacd4-7f17-42a7-8d93-3dee8b9341fa

        :expectedresults: A repository is created with a Docker upstream
            repository and that its URL can be updated.
        """
        new_url = gen_url()
        module_target_sat.cli.Repository.update({'id': repo['id'], 'url': new_url})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert repo['url'] == new_url

    def test_positive_delete_by_id(self, repo, module_target_sat):
        """Create and delete a Docker-type repository

        :id: ab1e8228-92a8-45dc-a863-7181711f2745

        :expectedresults: A repository with a upstream repository is created
            and then deleted.

        :CaseImportance: Critical
        """
        module_target_sat.cli.Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Repository.info({'id': repo['id']})

    def test_positive_delete_random_repo_by_id(self, module_org, module_target_sat):
        """Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        :id: d4db5eaa-7379-4788-9b72-76f2589d8f20

        :expectedresults: Random repository can be deleted from random product
            without altering the other products.
        """
        products = [
            module_target_sat.cli_factory.make_product_wait({'organization-id': module_org.id})
            for _ in range(randint(2, 5))
        ]
        repos = []
        for product in products:
            for _ in range(randint(2, 3)):
                repos.append(_repo(module_target_sat, product['id']))
        # Select random repository and delete it
        repo = choice(repos)
        repos.remove(repo)
        module_target_sat.cli.Repository.delete({'id': repo['id']})
        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.Repository.info({'id': repo['id']})
        # Verify other repositories were not touched
        product_ids = [product['id'] for product in products]
        for repo in repos:
            result = module_target_sat.cli.Repository.info({'id': repo['id']})
            assert result['product']['id'] in product_ids

    def test_negative_docker_upload_content(self, repo, module_org, module_target_sat):
        """Create and sync a Docker-type repository, and attempt to run upload-content

        :id: 031563fb-7265-44e3-9693-43e622b7756f

        :Verifies: SAT-21359

        :customerscenario: true

        :expectedresults: upload-content cannot be run with a docker type repository

        :CaseImportance: Critical
        """
        assert int(repo['content-counts']['container-manifests']) == 0
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        repo = module_target_sat.cli.Repository.info({'id': repo['id']})
        assert int(repo['content-counts']['container-manifests']) > 0
        remote_path = f'/tmp/{EXPIRED_MANIFEST}'
        module_target_sat.put(DataFile.EXPIRED_MANIFEST_FILE, remote_path)
        with pytest.raises(CLIReturnCodeError) as error:
            module_target_sat.cli.Repository.upload_content(
                {
                    'name': repo['name'],
                    'organization-id': module_org.id,
                    'path': remote_path,
                    'product-id': repo['product']['id'],
                }
            )
        assert (
            "Could not upload the content:\n  Cannot upload container content via Hammer/API. Use podman push instead.\n"
            in error.value.stderr
        )


class TestDockerContentView:
    """Tests specific to using ``Docker`` repositories with Content Views.

    :CaseComponent: ContentViews

    :team: Phoenix-content
    """

    def test_positive_add_docker_repos_by_id(self, module_org, module_product, module_target_sat):
        """Add multiple Docker-type repositories to a non-composite CV.

        :id: 2eb19e28-a633-4c21-9469-75a686c83b34

        :expectedresults: Repositories are created with Docker upstream
            repositories and the product is added to a non-composite content
            view.
        """
        repos = [_repo(module_target_sat, module_product.id) for _ in range(randint(2, 5))]
        content_view = module_target_sat.cli_factory.make_content_view(
            {'composite': False, 'organization-id': module_org.id}
        )
        for repo in repos:
            module_target_sat.cli.ContentView.add_repository(
                {'id': content_view['id'], 'repository-id': repo['id']}
            )
        content_view = module_target_sat.cli.ContentView.info({'id': content_view['id']})

        assert {repo['id'] for repo in repos} == {
            repo['id'] for repo in content_view['container-image-repositories']
        }

    def test_positive_publish_with_docker_repo_composite(
        self, content_view, module_org, module_target_sat
    ):
        """Add Docker-type repository to composite CV and publish it once.

        :id: 2d75419b-73ed-4f29-ae0d-9af8d9624c87

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published once and added to a composite content view which is also
            published once.

        :BZ: 1359665
        """
        assert len(content_view['versions']) == 0

        module_target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = module_target_sat.cli.ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

        comp_content_view = module_target_sat.cli_factory.make_content_view(
            {'composite': True, 'organization-id': module_org.id}
        )
        module_target_sat.cli.ContentView.update(
            {
                'component-ids': content_view['versions'][0]['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = module_target_sat.cli.ContentView.info({'id': comp_content_view['id']})
        assert content_view['versions'][0]['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        module_target_sat.cli.ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = module_target_sat.cli.ContentView.info({'id': comp_content_view['id']})
        assert len(comp_content_view['versions']) == 1

    @pytest.mark.upgrade
    def test_positive_promote_multiple_with_docker_repo_composite(
        self, content_view, module_org, module_target_sat
    ):
        """Add Docker-type repository to composite content view and publish it.
        Then promote it to the multiple available lifecycle-environments.

        :id: 345288d6-581b-4c07-8062-e58cb6343f1b

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environments.

        :BZ: 1359665
        """
        module_target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = module_target_sat.cli.ContentView.info({'id': content_view['id']})
        assert len(content_view['versions']) == 1

        comp_content_view = module_target_sat.cli_factory.make_content_view(
            {'composite': True, 'organization-id': module_org.id}
        )
        module_target_sat.cli.ContentView.update(
            {
                'component-ids': content_view['versions'][0]['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = module_target_sat.cli.ContentView.info({'id': comp_content_view['id']})
        assert content_view['versions'][0]['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        module_target_sat.cli.ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = module_target_sat.cli.ContentView.info({'id': comp_content_view['id']})
        cvv = module_target_sat.cli.ContentView.version_info(
            {'id': comp_content_view['versions'][0]['id']}
        )
        assert len(cvv['lifecycle-environments']) == 1

        lces = [
            module_target_sat.cli_factory.make_lifecycle_environment(
                {'organization-id': module_org.id}
            )
            for _ in range(1, randint(3, 6))
        ]

        for expected_lces, lce in enumerate(lces, start=2):
            module_target_sat.cli.ContentView.version_promote(
                {
                    'id': cvv['id'],
                    'to-lifecycle-environment-id': lce['id'],
                }
            )
            cvv = module_target_sat.cli.ContentView.version_info({'id': cvv['id']})
            assert len(cvv['lifecycle-environments']) == expected_lces

    def test_positive_product_name_change_after_promotion(self, module_org, module_target_sat):
        """Promote content view with Docker repository to lifecycle environment.
        Change product name. Verify that repository name on product changed
        according to new pattern.

        :id: 92279755-717c-415c-88b6-4cc1202072e2

        :expectedresults: Container repository name is changed
            according to new pattern.
        """
        old_prod_name = gen_string('alpha', 5)
        new_prod_name = gen_string('alpha', 5)
        docker_upstream_name = settings.container.alternative_upstream_names[0]
        new_pattern = '<%= content_view.label %>/<%= product.name %>'

        lce = module_target_sat.cli_factory.make_lifecycle_environment(
            {'organization-id': module_org.id}
        )
        prod = module_target_sat.cli_factory.make_product_wait(
            {'organization-id': module_org.id, 'name': old_prod_name}
        )
        repo = _repo(
            module_target_sat,
            prod['id'],
            name=gen_string('alpha', 5),
            upstream_name=docker_upstream_name,
        )
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        content_view = module_target_sat.cli_factory.make_content_view(
            {'composite': False, 'organization-id': module_org.id}
        )
        module_target_sat.cli.ContentView.add_repository(
            {'id': content_view['id'], 'repository-id': repo['id']}
        )
        module_target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = module_target_sat.cli.ContentView.info({'id': content_view['id']})
        module_target_sat.cli.LifecycleEnvironment.update(
            {
                'registry-name-pattern': new_pattern,
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )
        lce = module_target_sat.cli.LifecycleEnvironment.info(
            {'id': lce['id'], 'organization-id': module_org.id}
        )
        assert lce['registry-name-pattern'] == new_pattern

        module_target_sat.cli.ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        module_target_sat.cli.Product.update({'name': new_prod_name, 'id': prod['id']})

        repo = module_target_sat.cli.Repository.list(
            {'name': repo['name'], 'environment-id': lce['id'], 'organization-id': module_org.id}
        )[0]
        expected_name = f'{content_view["label"]}/{old_prod_name}'.lower()
        assert (
            module_target_sat.cli.Repository.info({'id': repo['id']})['container-repository-name']
            == expected_name
        )

        module_target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = module_target_sat.cli.ContentView.info({'id': content_view['id']})
        module_target_sat.cli.ContentView.version_promote(
            {
                'id': sorted(cvv['id'] for cvv in content_view['versions'])[-1],
                'to-lifecycle-environment-id': lce['id'],
            }
        )

        repo = module_target_sat.cli.Repository.list(
            {
                'name': repo['name'],
                'environment-id': lce['id'],
                'organization-id': module_org.id,
            }
        )[0]
        expected_name = f'{content_view["label"]}/{new_prod_name}'.lower()
        assert (
            module_target_sat.cli.Repository.info({'id': repo['id']})['container-repository-name']
            == expected_name
        )

    def test_positive_repo_name_change_after_promotion(self, module_org, module_target_sat):
        """Promote content view with Docker repository to lifecycle environment.
        Change repository name. Verify that Docker repository name on product
        changed according to new pattern.

        :id: f094baab-e823-47e0-939d-bd0d88eb1538

        :expectedresults: Container repository name is changed
            according to new pattern.
        """
        old_repo_name = gen_string('alpha', 5)
        new_repo_name = gen_string('alpha', 5)
        docker_upstream_name = settings.container.alternative_upstream_names[0]
        new_pattern = '<%= content_view.label %>/<%= repository.name %>'

        lce = module_target_sat.cli_factory.make_lifecycle_environment(
            {'organization-id': module_org.id}
        )
        prod = module_target_sat.cli_factory.make_product_wait({'organization-id': module_org.id})
        repo = _repo(
            module_target_sat, prod['id'], name=old_repo_name, upstream_name=docker_upstream_name
        )
        module_target_sat.cli.Repository.synchronize({'id': repo['id']})
        content_view = module_target_sat.cli_factory.make_content_view(
            {'composite': False, 'organization-id': module_org.id}
        )
        module_target_sat.cli.ContentView.add_repository(
            {'id': content_view['id'], 'repository-id': repo['id']}
        )
        module_target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = module_target_sat.cli.ContentView.info({'id': content_view['id']})
        module_target_sat.cli.LifecycleEnvironment.update(
            {
                'registry-name-pattern': new_pattern,
                'id': lce['id'],
                'organization-id': module_org.id,
            }
        )
        module_target_sat.cli.ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )
        module_target_sat.cli.Repository.update(
            {'name': new_repo_name, 'id': repo['id'], 'product-id': prod['id']}
        )

        repo = module_target_sat.cli.Repository.list(
            {
                'name': new_repo_name,
                'environment-id': lce['id'],
                'organization-id': module_org.id,
            }
        )[0]
        expected_name = f'{content_view["label"]}/{old_repo_name}'.lower()
        assert (
            module_target_sat.cli.Repository.info({'id': repo['id']})['container-repository-name']
            == expected_name
        )

        module_target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = module_target_sat.cli.ContentView.info({'id': content_view['id']})
        module_target_sat.cli.ContentView.version_promote(
            {
                'id': sorted(cvv['id'] for cvv in content_view['versions'])[-1],
                'to-lifecycle-environment-id': lce['id'],
            }
        )

        repo = module_target_sat.cli.Repository.list(
            {
                'name': new_repo_name,
                'environment-id': lce['id'],
                'organization-id': module_org.id,
            }
        )[0]
        expected_name = f'{content_view["label"]}/{new_repo_name}'.lower()
        assert (
            module_target_sat.cli.Repository.info({'id': repo['id']})['container-repository-name']
            == expected_name
        )

    def test_negative_set_non_unique_name_pattern_and_promote(self, module_org, module_target_sat):
        """Set registry name pattern to one that does not guarantee uniqueness.
        Try to promote content view with multiple Docker repositories to
        lifecycle environment. Verify that content has not been promoted.

        :id: eaf5e7ac-93c9-46c6-b538-4d6bd73ab9fc

        :expectedresults: Content view is not promoted
        """
        docker_upstream_names = settings.container.alternative_upstream_names
        new_pattern = '<%= organization.label %>'

        lce = module_target_sat.cli_factory.make_lifecycle_environment(
            {'organization-id': module_org.id, 'registry-name-pattern': new_pattern}
        )

        prod = module_target_sat.cli_factory.make_product_wait({'organization-id': module_org.id})
        content_view = module_target_sat.cli_factory.make_content_view(
            {'composite': False, 'organization-id': module_org.id}
        )
        for docker_name in docker_upstream_names:
            repo = _repo(module_target_sat, prod['id'], upstream_name=docker_name)
            module_target_sat.cli.Repository.synchronize({'id': repo['id']})
            module_target_sat.cli.ContentView.add_repository(
                {'id': content_view['id'], 'repository-id': repo['id']}
            )
        module_target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = module_target_sat.cli.ContentView.info({'id': content_view['id']})

        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.ContentView.version_promote(
                {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
            )

    def test_negative_promote_and_set_non_unique_name_pattern(
        self, module_org, module_product, module_target_sat
    ):
        """Promote content view with multiple Docker repositories to
        lifecycle environment. Set registry name pattern to one that
        does not guarantee uniqueness. Verify that pattern has not been
        changed.

        :id: 9f952224-084f-48d1-b2ea-85f3621becea

        :expectedresults: Registry name pattern is not changed
        """
        docker_upstream_names = settings.container.alternative_upstream_names
        new_pattern = '<%= organization.label %>'

        content_view = module_target_sat.cli_factory.make_content_view(
            {'composite': False, 'organization-id': module_org.id}
        )
        for docker_name in docker_upstream_names:
            repo = _repo(module_target_sat, module_product.id, upstream_name=docker_name)
            module_target_sat.cli.Repository.synchronize({'id': repo['id']})
            module_target_sat.cli.ContentView.add_repository(
                {'id': content_view['id'], 'repository-id': repo['id']}
            )
        module_target_sat.cli.ContentView.publish({'id': content_view['id']})
        content_view = module_target_sat.cli.ContentView.info({'id': content_view['id']})
        lce = module_target_sat.cli_factory.make_lifecycle_environment(
            {'organization-id': module_org.id}
        )
        module_target_sat.cli.ContentView.version_promote(
            {'id': content_view['versions'][0]['id'], 'to-lifecycle-environment-id': lce['id']}
        )

        with pytest.raises(CLIReturnCodeError):
            module_target_sat.cli.LifecycleEnvironment.update(
                {
                    'registry-name-pattern': new_pattern,
                    'id': lce['id'],
                    'organization-id': module_org.id,
                }
            )


class TestDockerActivationKey:
    """Tests specific to adding ``Docker`` repositories to Activation Keys.

    :CaseComponent: ActivationKeys

    :team: Phoenix-subscriptions
    """

    def test_positive_add_docker_repo_cv(
        self, module_org, module_lce, content_view_promote, module_target_sat
    ):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then create an activation key and associate it with the
        Docker content view.

        :id: bb128642-d39f-45c2-aa69-a4776ea536a2

        :expectedresults: Docker-based content view can be added to activation
            key
        """
        activation_key = module_target_sat.cli_factory.make_activation_key(
            {
                'content-view-id': content_view_promote['content-view-id'],
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )
        assert (
            activation_key['content-view-environments'][0]['label']
            == f'{module_lce.name}/{content_view_promote["content-view-name"]}'
        )

    def test_positive_remove_docker_repo_cv(
        self, module_org, module_lce, content_view_promote, module_target_sat
    ):
        """Add Docker-type repository to a non-composite content view
        and publish it. Create an activation key and associate it with the
        Docker content view. Then remove this content view from the activation
        key.

        :id: d696e5fe-1818-46ce-9499-924c96e1ef88

        :expectedresults: Docker-based content view can be added and then
            removed from the activation key.
        """
        activation_key = module_target_sat.cli_factory.make_activation_key(
            {
                'content-view-id': content_view_promote['content-view-id'],
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )
        assert (
            activation_key['content-view-environments'][0]['label']
            == f'{module_lce.name}/{content_view_promote["content-view-name"]}'
        )

        # Create another content view replace with
        another_cv = module_target_sat.cli_factory.make_content_view(
            {'composite': False, 'organization-id': module_org.id}
        )
        module_target_sat.cli.ContentView.publish({'id': another_cv['id']})
        another_cv = module_target_sat.cli.ContentView.info({'id': another_cv['id']})
        module_target_sat.cli.ContentView.version_promote(
            {'id': another_cv['versions'][0]['id'], 'to-lifecycle-environment-id': module_lce.id}
        )

        module_target_sat.cli.ActivationKey.update(
            {
                'id': activation_key['id'],
                'organization-id': module_org.id,
                'content-view-id': another_cv['id'],
                'lifecycle-environment-id': module_lce.id,
            }
        )
        activation_key = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
        assert (
            activation_key['content-view-environments'][0]['label']
            != f'{module_lce.name}/{content_view_promote["content-view-name"]}'
        )

    def test_positive_add_docker_repo_ccv(
        self, module_org, module_lce, content_view_publish, module_target_sat
    ):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then add this content view to a composite content view
        and publish it. Create an activation key and associate it with the
        composite Docker content view.

        :id: 1d9b82fd-8dab-4fd9-ad35-656d712d56a2

        :expectedresults: Docker-based content view can be added to activation
            key

        :BZ: 1359665
        """
        comp_content_view = module_target_sat.cli_factory.make_content_view(
            {'composite': True, 'organization-id': module_org.id}
        )
        module_target_sat.cli.ContentView.update(
            {
                'component-ids': content_view_publish['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = module_target_sat.cli.ContentView.info({'id': comp_content_view['id']})
        assert content_view_publish['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        module_target_sat.cli.ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = module_target_sat.cli.ContentView.info({'id': comp_content_view['id']})
        comp_cvv = module_target_sat.cli.ContentView.version_info(
            {'id': comp_content_view['versions'][0]['id']}
        )
        module_target_sat.cli.ContentView.version_promote(
            {'id': comp_cvv['id'], 'to-lifecycle-environment-id': module_lce.id}
        )
        activation_key = module_target_sat.cli_factory.make_activation_key(
            {
                'content-view-id': comp_content_view['id'],
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )
        assert (
            activation_key['content-view-environments'][0]['label']
            == f'{module_lce.name}/{comp_content_view["name"]}'
        )

    def test_positive_remove_docker_repo_ccv(
        self, module_org, module_lce, content_view_publish, module_target_sat
    ):
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
        comp_content_view = module_target_sat.cli_factory.make_content_view(
            {'composite': True, 'organization-id': module_org.id}
        )
        module_target_sat.cli.ContentView.update(
            {
                'component-ids': content_view_publish['id'],
                'id': comp_content_view['id'],
            }
        )
        comp_content_view = module_target_sat.cli.ContentView.info({'id': comp_content_view['id']})
        assert content_view_publish['id'] in [
            component['id'] for component in comp_content_view['components']
        ]

        module_target_sat.cli.ContentView.publish({'id': comp_content_view['id']})
        comp_content_view = module_target_sat.cli.ContentView.info({'id': comp_content_view['id']})
        comp_cvv = module_target_sat.cli.ContentView.version_info(
            {'id': comp_content_view['versions'][0]['id']}
        )
        module_target_sat.cli.ContentView.version_promote(
            {'id': comp_cvv['id'], 'to-lifecycle-environment-id': module_lce.id}
        )
        activation_key = module_target_sat.cli_factory.make_activation_key(
            {
                'content-view-id': comp_content_view['id'],
                'lifecycle-environment-id': module_lce.id,
                'organization-id': module_org.id,
            }
        )
        assert (
            activation_key['content-view-environments'][0]['label']
            == f'{module_lce.name}/{comp_content_view["name"]}'
        )

        # Create another content view replace with
        another_cv = module_target_sat.cli_factory.make_content_view(
            {'composite': False, 'organization-id': module_org.id}
        )
        module_target_sat.cli.ContentView.publish({'id': another_cv['id']})
        another_cv = module_target_sat.cli.ContentView.info({'id': another_cv['id']})
        module_target_sat.cli.ContentView.version_promote(
            {'id': another_cv['versions'][0]['id'], 'to-lifecycle-environment-id': module_lce.id}
        )

        module_target_sat.cli.ActivationKey.update(
            {
                'id': activation_key['id'],
                'organization-id': module_org.id,
                'content-view-id': another_cv['id'],
                'lifecycle-environment-id': module_lce.id,
            }
        )
        activation_key = module_target_sat.cli.ActivationKey.info({'id': activation_key['id']})
        assert (
            activation_key['content-view-environments'][0]['label']
            != f'{module_lce.name}/{comp_content_view["name"]}'
        )
