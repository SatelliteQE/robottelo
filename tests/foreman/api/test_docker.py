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
from random import shuffle

import pytest
from fauxfactory import gen_string
from fauxfactory import gen_url
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.api.utils import promote
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CONTAINER_UPSTREAM_NAME
from robottelo.datafactory import generate_strings_list
from robottelo.datafactory import invalid_docker_upstream_names
from robottelo.datafactory import parametrized
from robottelo.datafactory import valid_docker_repository_names
from robottelo.datafactory import valid_docker_upstream_names

DOCKER_PROVIDER = 'Docker'


def _create_repository(product, name=None, upstream_name=None):
    """Create a Docker-based repository.

    :param product: A ``Product`` object.
    :param str name: Name for the repository. If ``None`` then a random
        value will be generated.
    :param str upstream_name: A valid name of an existing upstream repository.
        If ``None`` then defaults to CONTAINER_UPSTREAM_NAME.
    :return: A ``Repository`` object.
    """
    if name is None:
        name = choice(generate_strings_list(15, ['numeric', 'html']))
    if upstream_name is None:
        upstream_name = CONTAINER_UPSTREAM_NAME
    return entities.Repository(
        content_type='docker',
        docker_upstream_name=upstream_name,
        name=name,
        product=product,
        url=CONTAINER_REGISTRY_HUB,
    ).create()


@pytest.fixture
def repo(module_product):
    """Create a single repository."""
    return _create_repository(module_product)


@pytest.fixture
def repos(module_product):
    """Create and return a list of repositories."""
    return [_create_repository(module_product) for _ in range(randint(2, 5))]


@pytest.fixture
def content_view(module_org):
    """Create a content view."""
    return entities.ContentView(composite=False, organization=module_org).create()


@pytest.fixture
def content_view_with_repo(content_view, repo):
    """Assign a docker-based repository to a content view."""
    content_view.repository = [repo]
    return content_view.update(['repository'])


@pytest.fixture
def content_view_publish_promote(content_view_with_repo, module_lce):
    """Publish and promote a new content view version into the lifecycle environment."""
    cv = content_view_with_repo
    cv.publish()

    cvv = cv.read().version[0].read()
    promote(cvv, module_lce.id)

    return cv.read()


@pytest.fixture
def content_view_version(content_view_publish_promote):
    return content_view_publish_promote.version[0].read()


class TestDockerRepository:
    """Tests specific to performing CRUD methods against ``Docker``
    repositories.

    :CaseComponent: Repositories

    :Assignee: tpapaioa
    """

    @pytest.mark.tier1
    @pytest.mark.parametrize('name', **parametrized(valid_docker_repository_names()))
    def test_positive_create_with_name(self, module_product, name):
        """Create one Docker-type repository

        :id: 3360aab2-74f3-4f6e-a083-46498ceacad2

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
            repository.

        :CaseImportance: Critical
        """
        repo = _create_repository(module_product, name)
        assert repo.name == name
        assert repo.docker_upstream_name == CONTAINER_UPSTREAM_NAME
        assert repo.content_type == 'docker'

    @pytest.mark.tier1
    @pytest.mark.parametrize('upstream_name', **parametrized(valid_docker_upstream_names()))
    def test_positive_create_with_upstream_name(self, module_product, upstream_name):
        """Create a Docker-type repository with a valid docker upstream
        name

        :id: 742a2118-0ab2-4e63-b978-88fe9f52c034

        :parametrized: yes

        :expectedresults: A repository is created with the specified upstream
            name.

        :CaseImportance: Critical
        """
        repo = _create_repository(module_product, upstream_name=upstream_name)
        assert repo.docker_upstream_name == upstream_name
        assert repo.content_type == 'docker'

    @pytest.mark.tier1
    @pytest.mark.parametrize('upstream_name', **parametrized(invalid_docker_upstream_names()))
    def test_negative_create_with_invalid_upstream_name(self, module_product, upstream_name):
        """Create a Docker-type repository with a invalid docker
        upstream name.

        :id: 2c5abb4a-e50b-427a-81d2-57eaf8f57a0f

        :parametrized: yes

        :expectedresults: A repository is not created and a proper error is
            raised.

        :CaseImportance: Critical
        """
        with pytest.raises(HTTPError):
            _create_repository(module_product, upstream_name=upstream_name)

    @pytest.mark.tier2
    def test_positive_create_repos_using_same_product(self, module_product):
        """Create multiple Docker-type repositories

        :id: 4a6929fc-5111-43ff-940c-07a754828630

        :expectedresults: Multiple docker repositories are created with a
            Docker usptream repository and they all belong to the same product.

        :CaseLevel: Integration
        """
        for _ in range(randint(2, 5)):
            repo = _create_repository(module_product)
            assert repo.id in [repo_.id for repo_ in module_product.read().repository]

    @pytest.mark.tier2
    def test_positive_create_repos_using_multiple_products(self, module_org):
        """Create multiple Docker-type repositories on multiple products

        :id: 5a65d20b-d3b5-4bd7-9c8f-19c8af190558

        :expectedresults: Multiple docker repositories are created with a
            Docker upstream repository and they all belong to their respective
            products.

        :CaseLevel: Integration
        """
        for _ in range(randint(2, 5)):
            product = entities.Product(organization=module_org).create()
            for _ in range(randint(2, 3)):
                repo = _create_repository(product)
                product = product.read()
                assert repo.id in [repo_.id for repo_ in product.repository]

    @pytest.mark.tier1
    def test_positive_sync(self, module_product):
        """Create and sync a Docker-type repository

        :id: 80fbcd84-1c6f-444f-a44e-7d2738a0cba2

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.

        :CaseImportance: Critical
        """
        repo = _create_repository(module_product)
        repo.sync(timeout=600)
        repo = repo.read()
        assert repo.content_counts['docker_manifest'] >= 1

    @pytest.mark.tier1
    @pytest.mark.parametrize('new_name', **parametrized(valid_docker_repository_names()))
    def test_positive_update_name(self, module_product, repo, new_name):
        """Create a Docker-type repository and update its name.

        :id: 7967e6b5-c206-4ad0-bcf5-64a7ce85233b

        :parametrized: yes

        :expectedresults: A repository is created with a Docker upstream
            repository and that its name can be updated.

        :CaseImportance: Critical
        """
        repo.name = new_name
        repo = repo.update()
        assert repo.name == new_name

    @pytest.mark.tier1
    def test_positive_update_upstream_name(self, repo):
        """Create a Docker-type repository and update its upstream name.

        :id: 4e2fb78d-0b6a-4455-8869-8eaf9d4a61b0

        :expectedresults: A repository is created with a Docker upstream
            repository and that its upstream name can be updated.

        :CaseImportance: Critical
        """
        assert repo.docker_upstream_name == CONTAINER_UPSTREAM_NAME

        # Update the repository upstream name
        new_upstream_name = 'fedora/ssh'
        repo.docker_upstream_name = new_upstream_name
        repo = repo.update()
        assert repo.docker_upstream_name == new_upstream_name

    @pytest.mark.tier2
    def test_positive_update_url(self, module_product, repo):
        """Create a Docker-type repository and update its URL.

        :id: 6a588e65-bf1d-4ca9-82ce-591f9070215f

        :expectedresults: A repository is created with a Docker upstream
            repository and that its URL can be updated.

        :BZ: 1489322
        """
        assert repo.url == CONTAINER_REGISTRY_HUB

        # Update the repository URL
        new_url = gen_url()
        repo.url = new_url
        repo = repo.update()
        assert repo.url == new_url
        assert repo.url != CONTAINER_REGISTRY_HUB

    @pytest.mark.tier1
    def test_positive_delete(self, repo):
        """Create and delete a Docker-type repository

        :id: 92df93cb-9de2-40fa-8451-b8c1ba8f45be

        :expectedresults: A repository is created with a Docker upstream
            repository and then deleted.

        :CaseImportance: Critical
        """
        # Delete it
        repo.delete()
        with pytest.raises(HTTPError):
            repo.read()

    @pytest.mark.tier2
    def test_positive_delete_random_repo(self, module_org):
        """Create Docker-type repositories on multiple products and
        delete a random repository from a random product.

        :id: cbc2792d-cf81-41f7-8889-001a27e4dd66

        :expectedresults: Random repository can be deleted from random product
            without altering the other products.
        """
        repos = []
        products = [
            entities.Product(organization=module_org).create() for _ in range(randint(2, 5))
        ]
        for product in products:
            repo = _create_repository(product)
            assert repo.content_type == 'docker'
            repos.append(repo)

        # Delete a random repository
        shuffle(repos)
        repo = repos.pop()
        repo.delete()
        with pytest.raises(HTTPError):
            repo.read()

        # Check if others repositories are not touched
        for repo in repos:
            repo = repo.read()
            assert repo.product.id in [prod.id for prod in products]


class TestDockerContentView:
    """Tests specific to using ``Docker`` repositories with Content Views.

    :CaseComponent: ContentViews

    :Assignee: ltran

    :CaseLevel: Integration
    """

    @pytest.mark.tier2
    def test_positive_add_docker_repo(self, repo, content_view):
        """Add one Docker-type repository to a non-composite content view

        :id: a065822f-bb41-4fc9-bf5c-65814ca11b2d

        :expectedresults: A repository is created with a Docker repository and
            the product is added to a non-composite content view
        """
        # Associate docker repo with the content view
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert repo.id in [repo_.id for repo_ in content_view.repository]

    @pytest.mark.tier2
    def test_positive_add_docker_repos(self, module_org, module_product, content_view):
        """Add multiple Docker-type repositories to a
        non-composite content view.

        :id: 08eed081-2003-4475-95ac-553a56b83997

        :expectedresults: Repositories are created with Docker upstream repos
            and the product is added to a non-composite content view.
        """
        repos = [
            _create_repository(module_product, name=gen_string('alpha'))
            for _ in range(randint(2, 5))
        ]
        repo_ids = {r.id for r in repos}
        assert repo_ids.issubset({r.id for r in module_product.read().repository})

        content_view.repository = repos
        content_view = content_view.update(['repository'])

        assert len(repos) == len(content_view.repository)

        for repo in content_view.repository:
            r = repo.read()
            assert r.id in repo_ids
            assert r.content_type == 'docker'
            assert r.docker_upstream_name == CONTAINER_UPSTREAM_NAME

    @pytest.mark.tier2
    def test_positive_add_synced_docker_repo(self, module_org, module_product):
        """Create and sync a Docker-type repository

        :id: 3c7d6f17-266e-43d3-99f8-13bf0251eca6

        :expectedresults: A repository is created with a Docker repository and
            it is synchronized.
        """
        repo = _create_repository(module_product)
        repo.sync(timeout=600)
        repo = repo.read()
        assert repo.content_counts['docker_manifest'] > 0

        # Create content view and associate docker repo
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert repo.id in [repo_.id for repo_ in content_view.repository]

    @pytest.mark.tier2
    def test_positive_add_docker_repo_to_ccv(self, module_org):
        """Add one Docker-type repository to a composite content view

        :id: fe278275-2bb2-4d68-8624-f0cfd63ecb57

        :expectedresults: A repository is created with a Docker repository and
            the product is added to a content view which is then added to a
            composite content view.
        """
        repo = _create_repository(entities.Product(organization=module_org).create())

        # Create content view and associate docker repo
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert repo.id in [repo_.id for repo_ in content_view.repository]

        # Publish it and grab its version ID (there should only be one version)
        content_view.publish()
        content_view = content_view.read()
        assert len(content_view.version) == 1

        # Create composite content view and associate content view to it
        comp_content_view = entities.ContentView(composite=True, organization=module_org).create()
        comp_content_view.component = content_view.version
        comp_content_view = comp_content_view.update(['component'])
        assert content_view.version[0].id in [
            component.id for component in comp_content_view.component
        ]

    @pytest.mark.tier2
    def test_positive_add_docker_repos_to_ccv(self, module_org):
        """Add multiple Docker-type repositories to a composite
        content view.

        :id: 3824ccae-fb59-4f63-a1ab-a4f2419fcadd

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a random number of content
            views which are then added to a composite content view.
        """
        cv_versions = []
        product = entities.Product(organization=module_org).create()
        for _ in range(randint(2, 5)):
            # Create content view and associate docker repo
            content_view = entities.ContentView(composite=False, organization=module_org).create()
            repo = _create_repository(product)
            content_view.repository = [repo]
            content_view = content_view.update(['repository'])
            assert repo.id in [repo_.id for repo_ in content_view.repository]

            # Publish it and grab its version ID (there should be one version)
            content_view.publish()
            content_view = content_view.read()
            cv_versions.append(content_view.version[0])

        # Create composite content view and associate content view to it
        comp_content_view = entities.ContentView(composite=True, organization=module_org).create()
        for cv_version in cv_versions:
            comp_content_view.component.append(cv_version)
            comp_content_view = comp_content_view.update(['component'])
            assert cv_version.id in [component.id for component in comp_content_view.component]

    @pytest.mark.tier2
    def test_positive_publish_with_docker_repo(self, module_org):
        """Add Docker-type repository to content view and publish it once.

        :id: 86a73e96-ead6-41fb-8095-154a0b83e344

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published only once.
        """
        repo = _create_repository(entities.Product(organization=module_org).create())

        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert repo.id in [repo_.id for repo_ in content_view.repository]

        # Not published yet?
        content_view = content_view.read()
        assert content_view.last_published is None
        assert float(content_view.next_version) == 1.0

        # Publish it and check that it was indeed published.
        content_view.publish()
        content_view = content_view.read()
        assert content_view.last_published is not None
        assert float(content_view.next_version) > 1.0

    @pytest.mark.tier2
    def test_positive_publish_with_docker_repo_composite(self, module_org):
        """Add Docker-type repository to composite content view and
        publish it once.

        :id: 103ebee0-1978-4fc5-a11e-4dcdbf704185

        :expectedresults: One repository is created with an upstream repository
            and the product is added to a content view which is then published
            only once and then added to a composite content view which is also
            published only once.

        :BZ: 1217635
        """
        repo = _create_repository(entities.Product(organization=module_org).create())
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert repo.id in [repo_.id for repo_ in content_view.repository]

        # Not published yet?
        content_view = content_view.read()
        assert content_view.last_published is None
        assert float(content_view.next_version) == 1.0

        # Publish it and check that it was indeed published.
        content_view.publish()
        content_view = content_view.read()
        assert content_view.last_published is not None
        assert float(content_view.next_version) > 1.0

        # Create composite content view…
        comp_content_view = entities.ContentView(composite=True, organization=module_org).create()
        comp_content_view.component = [content_view.version[0]]
        comp_content_view = comp_content_view.update(['component'])
        assert content_view.version[0].id in [
            component.id for component in comp_content_view.component
        ]
        # … publish it…
        comp_content_view.publish()
        # … and check that it was indeed published
        comp_content_view = comp_content_view.read()
        assert comp_content_view.last_published is not None
        assert float(comp_content_view.next_version) > 1.0

    @pytest.mark.tier2
    def test_positive_publish_multiple_with_docker_repo(self, module_org):
        """Add Docker-type repository to content view and publish it
        multiple times.

        :id: e2caad64-e9f4-422d-a1ab-f64c286d82ff

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            published multiple times.
        """
        repo = _create_repository(entities.Product(organization=module_org).create())
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert [repo.id] == [repo_.id for repo_ in content_view.repository]
        assert content_view.read().last_published is None

        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            content_view.publish()
        content_view = content_view.read()
        assert content_view.last_published is not None
        assert len(content_view.version) == publish_amount

    @pytest.mark.tier2
    def test_positive_publish_multiple_with_docker_repo_composite(self, module_org):
        """Add Docker-type repository to content view and publish it
        multiple times.

        :id: 77a5957a-7415-41c3-be68-fa706fee7c98

        :expectedresults: One repository is created with a Docker upstream
            repository and the product is added to a content view which is then
            added to a composite content view which is then published multiple
            times.
        """
        repo = _create_repository(entities.Product(organization=module_org).create())
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert [repo.id] == [repo_.id for repo_ in content_view.repository]
        assert content_view.read().last_published is None

        content_view.publish()
        content_view = content_view.read()
        assert content_view.last_published is not None

        comp_content_view = entities.ContentView(composite=True, organization=module_org).create()
        comp_content_view.component = [content_view.version[0]]
        comp_content_view = comp_content_view.update(['component'])
        assert [content_view.version[0].id] == [comp.id for comp in comp_content_view.component]
        assert comp_content_view.last_published is None

        publish_amount = randint(2, 5)
        for _ in range(publish_amount):
            comp_content_view.publish()
        comp_content_view = comp_content_view.read()
        assert comp_content_view.last_published is not None
        assert len(comp_content_view.version) == publish_amount

    @pytest.mark.tier2
    def test_positive_promote_with_docker_repo(self, module_org):
        """Add Docker-type repository to content view and publish it.
        Then promote it to the next available lifecycle-environment.

        :id: 5ab7d7f1-fb13-4b83-b228-a6293be36195

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environment.
        """
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        repo = _create_repository(entities.Product(organization=module_org).create())

        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert [repo.id] == [repo_.id for repo_ in content_view.repository]

        content_view.publish()
        content_view = content_view.read()
        cvv = content_view.version[0].read()
        assert len(cvv.environment) == 1

        promote(cvv, lce.id)
        assert len(cvv.read().environment) == 2

    @pytest.mark.tier2
    def test_positive_promote_multiple_with_docker_repo(self, module_org):
        """Add Docker-type repository to content view and publish it.
        Then promote it to multiple available lifecycle-environments.

        :id: 7b0cbc95-5f63-47f3-9048-e6917078be73

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environments.
        """
        repo = _create_repository(entities.Product(organization=module_org).create())

        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert [repo.id] == [repo_.id for repo_ in content_view.repository]

        content_view.publish()
        cvv = content_view.read().version[0]
        assert len(cvv.read().environment) == 1

        for i in range(1, randint(3, 6)):
            lce = entities.LifecycleEnvironment(organization=module_org).create()
            promote(cvv, lce.id)
            assert len(cvv.read().environment) == i + 1

    @pytest.mark.tier2
    def test_positive_promote_with_docker_repo_composite(self, module_org):
        """Add Docker-type repository to content view and publish it.
        Then add that content view to composite one. Publish and promote that
        composite content view to the next available lifecycle-environment.

        :id: e903c7b2-7722-4a9e-bb69-99bbd3c23946

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environment.
        """
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        repo = _create_repository(entities.Product(organization=module_org).create())
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert [repo.id] == [repo_.id for repo_ in content_view.repository]

        content_view.publish()
        cvv = content_view.read().version[0].read()

        comp_content_view = entities.ContentView(composite=True, organization=module_org).create()
        comp_content_view.component = [cvv]
        comp_content_view = comp_content_view.update(['component'])
        assert cvv.id == comp_content_view.component[0].id

        comp_content_view.publish()
        comp_cvv = comp_content_view.read().version[0]
        assert len(comp_cvv.read().environment) == 1

        promote(comp_cvv, lce.id)
        assert len(comp_cvv.read().environment) == 2

    @pytest.mark.upgrade
    @pytest.mark.tier2
    def test_positive_promote_multiple_with_docker_repo_composite(self, module_org):
        """Add Docker-type repository to content view and publish it.
        Then add that content view to composite one. Publish and promote that
        composite content view to the multiple available lifecycle-environments

        :id: 91ac0f4a-8974-47e2-a1d6-7d734aa4ad46

        :expectedresults: Docker-type repository is promoted to content view
            found in the specific lifecycle-environments.
        """
        repo = _create_repository(entities.Product(organization=module_org).create())
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        assert [repo.id] == [repo_.id for repo_ in content_view.repository]

        content_view.publish()
        cvv = content_view.read().version[0].read()

        comp_content_view = entities.ContentView(composite=True, organization=module_org).create()
        comp_content_view.component = [cvv]
        comp_content_view = comp_content_view.update(['component'])
        assert cvv.id == comp_content_view.component[0].id

        comp_content_view.publish()
        comp_cvv = comp_content_view.read().version[0]
        assert len(comp_cvv.read().environment) == 1

        for i in range(1, randint(3, 6)):
            lce = entities.LifecycleEnvironment(organization=module_org).create()
            promote(comp_cvv, lce.id)
            assert len(comp_cvv.read().environment) == i + 1

    @pytest.mark.tier2
    @pytest.mark.upgrade
    def test_positive_name_pattern_change(self, module_org):
        """Promote content view with Docker repository to lifecycle environment.
        Change registry name pattern for that environment. Verify that repository
        name on product changed according to new pattern.

        :id: cc78d82d-027b-4cb7-92c5-dcccf9b592ea

        :expectedresults: Container repository name is changed
            according to new pattern.
        """
        pattern_prefix = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = (
            f'{pattern_prefix}-<%= organization.label %>/<%= repository.docker_upstream_name %>'
        )

        repo = _create_repository(
            entities.Product(organization=module_org).create(), upstream_name=docker_upstream_name
        )
        repo.sync(timeout=600)
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        promote(cvv, lce.id)
        lce.registry_name_pattern = new_pattern
        lce = lce.update(['registry_name_pattern'])
        repos = entities.Repository(organization=module_org).search(
            query={'environment_id': lce.id}
        )

        expected_pattern = f'{pattern_prefix}-{module_org.label}/{docker_upstream_name}'.lower()
        assert lce.registry_name_pattern == new_pattern
        assert repos[0].container_repository_name == expected_pattern

    @pytest.mark.tier2
    def test_positive_product_name_change_after_promotion(self, module_org):
        """Promote content view with Docker repository to lifecycle environment.
        Change product name. Verify that repository name on product changed
        according to new pattern.

        :id: 4ff21344-9ee6-4e17-9a88-0230e7cdd586

        :expectedresults: Container repository name is changed
            according to new pattern.
        """
        old_prod_name = gen_string('alpha', 5)
        new_prod_name = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = "<%= organization.label %>/<%= product.name %>"

        prod = entities.Product(organization=module_org, name=old_prod_name).create()
        repo = _create_repository(prod, upstream_name=docker_upstream_name)
        repo.sync(timeout=600)
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        lce.registry_name_pattern = new_pattern
        lce = lce.update(['registry_name_pattern'])
        promote(cvv, lce.id)
        prod.name = new_prod_name
        prod.update(['name'])
        repos = entities.Repository(organization=module_org).search(
            query={'environment_id': lce.id}
        )

        expected_pattern = f"{module_org.label}/{old_prod_name}".lower()
        assert repos[0].container_repository_name == expected_pattern

        content_view.publish()
        cvv = content_view.read().version[-1]
        promote(cvv, lce.id)
        repos = entities.Repository(organization=module_org).search(
            query={'environment_id': lce.id}
        )

        expected_pattern = f"{module_org.label}/{new_prod_name}".lower()
        assert repos[0].container_repository_name == expected_pattern

    @pytest.mark.tier2
    def test_positive_repo_name_change_after_promotion(self, module_org):
        """Promote content view with Docker repository to lifecycle environment.
        Change repository name. Verify that Docker repository name on product
        changed according to new pattern.

        :id: 304ae909-dc67-4a7e-80e1-96b45354e5a6

        :expectedresults: Container repository name is changed
            according to new pattern.
        """
        old_repo_name = gen_string('alpha', 5)
        new_repo_name = gen_string('alpha', 5)
        docker_upstream_name = 'hello-world'
        new_pattern = "<%= organization.label %>/<%= repository.name %>"

        repo = _create_repository(
            entities.Product(organization=module_org).create(),
            name=old_repo_name,
            upstream_name=docker_upstream_name,
        )
        repo.sync(timeout=600)
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = [repo]
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        lce.registry_name_pattern = new_pattern
        lce = lce.update(['registry_name_pattern'])
        promote(cvv, lce.id)
        repo.name = new_repo_name
        repo.update(['name'])
        repos = entities.Repository(organization=module_org).search(
            query={'environment_id': lce.id}
        )

        expected_pattern = f"{module_org.label}/{old_repo_name}".lower()
        assert repos[0].container_repository_name == expected_pattern

        content_view.publish()
        cvv = content_view.read().version[-1]
        promote(cvv, lce.id)
        repos = entities.Repository(organization=module_org).search(
            query={'environment_id': lce.id}
        )

        expected_pattern = f"{module_org.label}/{new_repo_name}".lower()
        assert repos[0].container_repository_name == expected_pattern

    @pytest.mark.tier2
    def test_negative_set_non_unique_name_pattern_and_promote(self, module_org, module_lce):
        """Set registry name pattern to one that does not guarantee uniqueness.
        Try to promote content view with multiple Docker repositories to
        lifecycle environment. Verify that content has not been promoted.

        :id: baae1ec2-35e8-4122-8fac-135c987139d3

        :expectedresults: Content view is not promoted
        """
        docker_upstream_names = ['hello-world', 'alpine']
        new_pattern = "<%= organization.label %>"

        lce = entities.LifecycleEnvironment(organization=module_org).create()
        lce.registry_name_pattern = new_pattern
        lce = lce.update(['registry_name_pattern'])
        prod = entities.Product(organization=module_org).create()
        repos = []
        for docker_name in docker_upstream_names:
            repo = _create_repository(prod, upstream_name=docker_name)
            repo.sync(timeout=600)
            repos.append(repo)
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = repos
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        with pytest.raises(HTTPError):
            promote(cvv, lce.id)

    @pytest.mark.tier2
    def test_negative_promote_and_set_non_unique_name_pattern(self, module_org):
        """Promote content view with multiple Docker repositories to
        lifecycle environment. Set registry name pattern to one that
        does not guarantee uniqueness. Verify that pattern has not been
        changed.

        :id: 945b3301-c523-4026-9753-df3577888319

        :expectedresults: Registry name pattern is not changed
        """
        docker_upstream_names = ['hello-world', 'alpine']
        new_pattern = "<%= organization.label %>"

        prod = entities.Product(organization=module_org).create()
        repos = []
        for docker_name in docker_upstream_names:
            repo = _create_repository(prod, upstream_name=docker_name)
            repo.sync(timeout=600)
            repos.append(repo)
        content_view = entities.ContentView(composite=False, organization=module_org).create()
        content_view.repository = repos
        content_view = content_view.update(['repository'])
        content_view.publish()
        cvv = content_view.read().version[0]
        lce = entities.LifecycleEnvironment(organization=module_org).create()
        promote(cvv, lce.id)
        with pytest.raises(HTTPError):
            lce.registry_name_pattern = new_pattern
            lce.update(['registry_name_pattern'])


class TestDockerActivationKey:
    """Tests specific to adding ``Docker`` repositories to Activation Keys.

    :CaseComponent: ActivationKeys

    :Assignee: chiggins

    :CaseLevel: Integration
    """

    @pytest.mark.tier2
    def test_positive_add_docker_repo_cv(
        self, module_lce, module_org, repo, content_view_publish_promote
    ):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then create an activation key and associate it with the
        Docker content view.

        :id: ce4ae928-49c7-4782-a032-08885050dd83

        :expectedresults: Docker-based content view can be added to activation
            key
        """
        content_view = content_view_publish_promote
        ak = entities.ActivationKey(
            content_view=content_view, environment=module_lce, organization=module_org
        ).create()
        assert ak.content_view.id == content_view.id
        assert ak.content_view.read().repository[0].id == repo.id

    @pytest.mark.tier2
    def test_positive_remove_docker_repo_cv(
        self, module_org, module_lce, content_view_publish_promote
    ):
        """Create an activation key and associate it with the Docker content view. Then remove
        this content view from the activation key.

        :id: 6a887a67-6700-47ac-9230-deaa0e382f22

        :expectedresults: Docker-based content view can be added and then
            removed from the activation key.

        :CaseLevel: Integration
        """
        content_view = content_view_publish_promote
        ak = entities.ActivationKey(
            content_view=content_view, environment=module_lce, organization=module_org
        ).create()
        assert ak.content_view.id == content_view.id
        ak.content_view = None
        assert ak.update(['content_view']).content_view is None

    @pytest.mark.tier2
    def test_positive_add_docker_repo_ccv(self, content_view_version, module_lce, module_org):
        """Add Docker-type repository to a non-composite content view and
        publish it. Then add this content view to a composite content view and
        publish it. Create an activation key and associate it with the
        composite Docker content view.

        :id: 2fc8a462-9d91-48bc-8e32-7ff8f769b9e4

        :expectedresults: Docker-based content view can be added to activation
            key
        """
        cvv = content_view_version
        comp_content_view = entities.ContentView(composite=True, organization=module_org).create()
        comp_content_view.component = [cvv]
        comp_content_view = comp_content_view.update(['component'])
        assert cvv.id == comp_content_view.component[0].id

        comp_content_view.publish()
        comp_cvv = comp_content_view.read().version[0].read()
        promote(comp_cvv, module_lce.id)

        ak = entities.ActivationKey(
            content_view=comp_content_view, environment=module_lce, organization=module_org
        ).create()
        assert ak.content_view.id == comp_content_view.id

    @pytest.mark.tier2
    def test_positive_remove_docker_repo_ccv(self, module_lce, module_org, content_view_version):
        """Add Docker-type repository to a non-composite content view
        and publish it. Then add this content view to a composite content view
        and publish it. Create an activation key and associate it with the
        composite Docker content view. Then, remove the composite content view
        from the activation key.

        :id: f3542272-13db-4a49-bc27-d1137172df41

        :expectedresults: Docker-based composite content view can be added and
            then removed from the activation key.
        """
        cvv = content_view_version
        comp_content_view = entities.ContentView(composite=True, organization=module_org).create()
        comp_content_view.component = [cvv]
        comp_content_view = comp_content_view.update(['component'])
        assert cvv.id == comp_content_view.component[0].id

        comp_content_view.publish()
        comp_cvv = comp_content_view.read().version[0].read()
        promote(comp_cvv, module_lce.id)

        ak = entities.ActivationKey(
            content_view=comp_content_view, environment=module_lce, organization=module_org
        ).create()
        assert ak.content_view.id == comp_content_view.id
        ak.content_view = None
        assert ak.update(['content_view']).content_view is None
