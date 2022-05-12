"""Test class for Content View UI

Feature details: https://fedorahosted.org/katello/wiki/ContentViews


:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import datetime
from random import randint

import pytest
from airgun.exceptions import InvalidElementStateException
from airgun.session import Session
from nailgun import entities
from navmazing import NavigationTriesExceeded
from productmd.common import parse_nvra
from widgetastic.exceptions import NoSuchElementException

from robottelo import constants
from robottelo import manifests
from robottelo.api.utils import call_entity_method_with_timeout
from robottelo.api.utils import create_role_permissions
from robottelo.api.utils import create_sync_custom_repo
from robottelo.api.utils import enable_sync_redhat_repo
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.cli.contentview import ContentView
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import CONTAINER_UPSTREAM_NAME
from robottelo.constants import DEFAULT_ARCHITECTURE
from robottelo.constants import DEFAULT_CV
from robottelo.constants import DEFAULT_PTABLE
from robottelo.constants import DISTRO_RHEL6
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import ENVIRONMENT
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_9_YUM_SECURITY_ERRATUM_COUNT
from robottelo.constants import FILTER_CONTENT_TYPE
from robottelo.constants import FILTER_ERRATA_TYPE
from robottelo.constants import FILTER_TYPE
from robottelo.constants import PERMISSIONS
from robottelo.constants import PRDS
from robottelo.constants import REPO_TYPE
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.constants import RHEL_6_MAJOR_VERSION
from robottelo.constants import RHEL_7_MAJOR_VERSION
from robottelo.constants.repos import FEDORA27_OSTREE_REPO
from robottelo.datafactory import gen_string
from robottelo.products import DockerRepository
from robottelo.products import RepositoryCollection
from robottelo.products import SatelliteToolsRepository
from robottelo.products import VirtualizationAgentsRepository
from robottelo.products import YumRepository

VERSION = 'Version 1.0'


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_prod(module_org):
    return entities.Product(organization=module_org).create()


@pytest.mark.tier2
def test_positive_add_custom_content(session):
    """Associate custom content in a view

    :id: 7128fc8b-0e8c-4f00-8541-2ca2399650c8

    :setup: Sync custom content

    :expectedresults: Custom content can be seen in a view

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    org = entities.Organization().create()
    cv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    product = entities.Product(organization=org).create()
    entities.Repository(name=repo_name, product=product).create()
    with session:
        session.organization.select(org_name=org.name)
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        cv = session.contentview.read(cv_name)
        assert cv['repositories']['resources']['assigned'][0]['Name'] == repo_name


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(session, module_org):
    """Create content view with yum repo, publish it and promote it to Library
        +1 env

    :id: 74c1b00d-c582-434f-bf73-588532588d50

    :steps:
        1. Create Product/repo and Sync it
        2. Create CV and add created repo in step1
        3. Publish and promote it to 'Library'
        4. Promote it to next environment

    :expectedresults: content view is created, updated with repo publish and
        promoted to next selected env

    :CaseLevel: Integration

    :CaseImportance: High
    """
    repo_name = gen_string('alpha')
    env_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    # Creates a CV along with product and sync'ed repository
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        # Create Life-cycle environment
        session.lifecycleenvironment.create({'name': env_name})
        # Create content-view
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        # Add repository to selected CV
        session.contentview.add_yum_repo(cv_name, repo_name)
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, env_name)
        assert f'Promoted to {env_name}' in result['Status']


@pytest.mark.tier2
def test_positive_publish_version_changes_in_source_env(session, module_org):
    """When publishing new version to environment, version gets updated

    :id: 576ac8b4-7efe-4267-a672-868a5f3eb28a

    :steps:
        1. publish a view  and then promote it to a new environment
        2. republish a new version of a CV and then promote it once more

    :expectedresults: Content view version is updated in source
        environment.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    cv = entities.ContentView(organization=module_org).create()
    with session:
        result = session.contentview.publish(cv.name)
        assert result['Version'] == 'Version 1.0'
        result = session.contentview.promote(cv.name, 'Version 1.0', lce.name)
        # Check that content view version 1.0 promoted to both environments
        assert ENVIRONMENT in result['Environments']
        assert lce.name in result['Environments']
        # Re-publish content view
        result = session.contentview.publish(cv.name)
        assert result['Version'] == 'Version 2.0'
        # Check that content view version 1.0 is still promoted to last environment,
        # but new published version is promoted to default one
        assert result['Environments'] == ENVIRONMENT
        cv_values = session.contentview.read(cv.name, widget_names='versions')
        env = [
            version['Environments']
            for version in cv_values['versions']['table']
            if version['Version'] == 'Version 1.0'
        ][0]
        assert env == lce.name
        # Promote new version to last environment
        result = session.contentview.promote(cv.name, 'Version 2.0', lce.name)
        # Check that new content view version promoted to both environments and
        # content view version 1.0 has not promoted to any version at all
        assert ENVIRONMENT in result['Environments']
        assert lce.name in result['Environments']
        cv_values = session.contentview.read(cv.name, widget_names='versions')
        assert not [
            version['Environments']
            for version in cv_values['versions']['table']
            if version['Version'] == 'Version 1.0'
        ]


@pytest.mark.tier2
def test_positive_repo_count_for_composite_cv(session, module_org):
    """Create some content views with synchronized repositories and
    promoted to one lce. Add them to composite content view and check repo
    count for it.

    :id: 4b8d5def-a593-4f6c-9856-e5f32fb80164

    :expectedresults: repository count for composite content view should
        be the sum of archived repositories across all content views.

    :BZ: 1431778

    :CaseLevel: Integration

    :CaseImportance: High
    """
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    ccv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    # Create a product and sync'ed repository
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        # Creates a composite CV
        session.contentview.create({'name': ccv_name, 'composite_view': True})
        # Create three content-views and add synced repo to them
        for _ in range(3):
            cv_name = entities.ContentView(organization=module_org).create().name
            assert session.contentview.search(cv_name)[0]['Name'] == cv_name
            # Add repository to selected CV
            session.contentview.add_yum_repo(cv_name, repo_name)
            # Publish content view
            session.contentview.publish(cv_name)
            # Check that repo count for cv is equal to 1
            assert session.contentview.search(cv_name)[0]['Repositories'] == '1'
            # Promote content view
            result = session.contentview.promote(cv_name, VERSION, lce.name)
            assert f'Promoted to {lce.name}' in result['Status']
            # Add content view to composite one
            session.contentview.add_cv(ccv_name, cv_name)
        # Publish composite content view
        session.contentview.publish(ccv_name)
        # Check that composite cv has three repositories in the table as we
        # were using one repository for each content view
        assert session.contentview.search(ccv_name)[0]['Repositories'] == '3'


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_create_composite(session, module_prod, module_org):
    """Create a composite content views

    :id: 550f1970-5cbd-4571-bb7b-17e97639b715

    :setup: sync multiple content source/types (RH, custom, etc.)

    :expectedresults: Composite content views are created

    :CaseLevel: System

    :CaseImportance: High
    """
    cv_name1 = gen_string('alpha')
    cv_name2 = gen_string('alpha')
    composite_name = gen_string('alpha')
    rh_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    docker_repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()

    with manifests.clone() as manifest:
        upload_manifest(module_org.id, manifest.content)
    enable_sync_redhat_repo(rh_repo, module_org.id)
    docker_repo.sync()
    with session:
        session.organization.select(module_org.name)
        # Create content views
        for cv_name in (cv_name1, cv_name2):
            session.contentview.create({'name': cv_name})
            assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_docker_repo(cv_name1, docker_repo.name)
        cv1 = session.contentview.read(cv_name1)
        assert cv1['docker_repositories']['resources']['assigned'][0]['Name'] == docker_repo.name
        session.contentview.publish(cv_name1)
        session.contentview.add_yum_repo(cv_name2, rh_repo['name'])
        session.contentview.publish(cv_name2)
        session.contentview.create({'name': composite_name, 'composite_view': True})
        for cv_name in (cv_name1, cv_name2):
            session.contentview.add_cv(composite_name, cv_name)
        composite_cv = session.contentview.read(composite_name)
        assert {cv_name1, cv_name2} == {
            cv['Name'] for cv in composite_cv['content_views']['resources']['assigned']
        }


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
def test_positive_add_rh_content(session):
    """Add Red Hat content to a content view

    :id: c370fd79-0c0d-4685-99cb-848556c786c1

    :setup: Sync RH content

    :expectedresults: RH Content can be seen in a view

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    cv_name = gen_string('alpha')
    rh_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    # Create new org to import manifest
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    enable_sync_redhat_repo(rh_repo, org.id)
    with session:
        # Create content-view
        session.organization.select(org.name)
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, rh_repo['name'])
        cv = session.contentview.read(cv_name)
        assert cv['repositories']['resources']['assigned'][0]['Name'] == rh_repo['name']


@pytest.mark.tier2
def test_positive_add_docker_repo(session, module_org, module_prod):
    """Add one Docker-type repository to a non-composite content view

    :id: 2868cfd5-d27e-4db9-b4a3-2827e31d1601

    :expectedresults: The repo is added to a non-composite content view

    :CaseLevel: Integration

    :CaseImportance: High
    """
    content_view = entities.ContentView(composite=False, organization=module_org).create()
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    with session:
        session.contentview.add_docker_repo(content_view.name, repo.name)
        cv = session.contentview.read(content_view.name, 'docker_repositories')
        assert cv['docker_repositories']['resources']['assigned'][0]['Name'] == repo.name


@pytest.mark.tier2
def test_positive_add_docker_repos(session, module_org, module_prod):
    """Add multiple Docker-type repositories to a non-composite
    content view.

    :id: 60d0ea23-fe8c-49f3-bed9-cc062ab1118d

    :expectedresults: The repos are added to a non-composite content
        view.

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    content_view = entities.ContentView(composite=False, organization=module_org).create()
    repos = [
        entities.Repository(
            url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
        ).create()
        for _ in range(randint(2, 3))
    ]
    with session:
        for repo in repos:
            session.contentview.add_docker_repo(content_view.name, repo.name)
        cv = session.contentview.read(content_view.name, 'docker_repositories')
        assert {repo.name for repo in repos} == {
            repo['Name'] for repo in cv['docker_repositories']['resources']['assigned']
        }


@pytest.mark.tier2
def test_positive_add_synced_docker_repo(session, module_org, module_prod):
    """Create and sync a docker repository, then add it to content view

    :id: 338a7ed4-9e10-4bc0-8666-5c8cd0ff0504

    :expectedresults: Synchronized docker repository was successfully added
        to content view.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    content_view = entities.ContentView(composite=False, organization=module_org).create()
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    with session:
        result = session.sync_status.synchronize([(module_prod.name, repo.name)])
        assert result[0] == 'Syncing Complete.'
        session.contentview.add_docker_repo(content_view.name, repo.name)
        cv = session.contentview.read(content_view.name, 'docker_repositories')
        assert cv['docker_repositories']['resources']['assigned'][0]['Name'] == repo.name
        assert cv['docker_repositories']['resources']['assigned'][0]['Sync State'] == 'Success'


@pytest.mark.tier2
def test_positive_add_docker_repo_to_ccv(session, module_org, module_prod):
    """Add one docker repository to a composite content view

    :id: 76b68407-b429-4ad7-b8b5-bfde327a0404

    :expectedresults: The repository is added to a content view which
        is then added to a composite content view.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    content_view = entities.ContentView(composite=False, organization=module_org).create()
    composite_cv = entities.ContentView(composite=True, organization=module_org).create()
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    with session:
        session.contentview.add_docker_repo(content_view.name, repo.name)
        result = session.contentview.publish(content_view.name)
        assert result['Version'] == VERSION
        session.contentview.add_cv(composite_cv.name, content_view.name)
        ccv = session.contentview.read(composite_cv.name, 'content_views')
        assert ccv['content_views']['resources']['assigned'][0]['Name'] == content_view.name
        assert '1 Repositories' in ccv['content_views']['resources']['assigned'][0]['Content']


@pytest.mark.tier2
def test_positive_add_docker_repos_to_ccv(session, module_org, module_prod):
    """Add multiple docker repositories to a composite content view.

    :id: 30187102-7106-45de-a68b-e32fbaecedb9

    :expectedresults: The repository is added to a random number of content
        views which are then added to a composite content view.

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    cvs = []
    for _ in range(randint(2, 3)):
        repo = entities.Repository(
            url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
        ).create()
        content_view = entities.ContentView(
            composite=False, organization=module_org, repository=[repo]
        ).create()
        content_view.publish()
        cvs.append(content_view.name)
    composite_cv = entities.ContentView(composite=True, organization=module_org).create()
    with session:
        for cv in cvs:
            session.contentview.add_cv(composite_cv.name, cv)
        ccv = session.contentview.read(composite_cv.name, 'content_views')
        assert set(cvs) == {cv['Name'] for cv in ccv['content_views']['resources']['assigned']}
        assert all(
            '1 Repositories' in cv['Content']
            for cv in ccv['content_views']['resources']['assigned']
        )


@pytest.mark.tier2
def test_positive_publish_with_docker_repo(session, module_org, module_prod):
    """Add docker repository to content view and publish it once.

    :id: 2004b2d4-177b-47de-9e61-bcfb58f05f88

    :expectedresults: The repo is added to a content view which is then
        successfully published.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    content_view = entities.ContentView(composite=False, organization=module_org).create()
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    with session:
        session.contentview.add_docker_repo(content_view.name, repo.name)
        result = session.contentview.publish(content_view.name)
        assert result['Version'] == VERSION
        cv = session.contentview.read(content_view.name, 'versions')
        assert cv['versions']['table'][0]['Version'] == VERSION


@pytest.mark.tier2
def test_positive_publish_with_docker_repo_composite(session, module_org, module_prod):
    """Add docker repository to composite content view and publish it once.

    :id: 7aad525a-a9d3-4100-9611-ca02c6a95a22

    :expectedresults: The docker repository is added to a content view
        which is then published only once and then added to a composite
        content view which is also published only once.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    content_view = entities.ContentView(
        composite=False, organization=module_org, repository=[repo]
    ).create()
    content_view.publish()
    composite_cv = entities.ContentView(composite=True, organization=module_org).create()
    with session:
        session.contentview.add_cv(composite_cv.name, content_view.name)
        result = session.contentview.publish(composite_cv.name)
        assert result['Version'] == VERSION
        ccv = session.contentview.read(composite_cv.name, 'content_views')
        assert '1 Repositories' in ccv['content_views']['resources']['assigned'][0]['Content']


@pytest.mark.tier2
def test_positive_publish_multiple_with_docker_repo(session, module_org, module_prod):
    """Add docker repository to content view and publish it multiple times.

    :id: acc703b7-6e99-48d7-96ce-ea0985409ef9

    :expectedresults: Content view with docker repo is successfully published
        multiple times.

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    content_view = entities.ContentView(
        composite=False, organization=module_org, repository=[repo]
    ).create()
    with session:
        for version in range(randint(2, 5)):
            result = session.contentview.publish(content_view.name)
            assert result['Version'] == f'Version {version + 1}.0'


@pytest.mark.tier2
def test_positive_publish_multiple_with_docker_repo_composite(session, module_org, module_prod):
    """Add docker repository to composite content view and publish it multiple times.

    :id: 07755bff-9071-45e5-b861-77a5c2fed3d9

    :expectedresults: Composite content view with docker repo is successfully
        published multiple times.

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    content_view = entities.ContentView(
        composite=False, organization=module_org, repository=[repo]
    ).create()
    content_view.publish()
    composite_cv = entities.ContentView(composite=True, organization=module_org).create()
    with session:
        session.contentview.add_cv(composite_cv.name, content_view.name)
        for version in range(randint(2, 5)):
            result = session.contentview.publish(composite_cv.name)
            assert result['Version'] == f'Version {version + 1}.0'


@pytest.mark.tier2
def test_positive_promote_with_docker_repo(session, module_org, module_prod):
    """Add docker repository to content view and publish it.
    Then promote it to the next available lifecycle environment.

    :id: c7e8c4a2-9676-429b-a452-f50d7bdd78b3

    :expectedresults: Docker repository is promoted to content view
        found in the specific lifecycle-environment.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    content_view = entities.ContentView(
        composite=False, organization=module_org, repository=[repo]
    ).create()
    content_view.publish()
    with session:
        result = session.contentview.promote(content_view.name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        assert lce.name in result['Environments']


@pytest.mark.tier2
def test_positive_promote_multiple_with_docker_repo(session, module_org, module_prod):
    """Add docker repository to content view and publish it.
    Then promote it to multiple available lifecycle-environments.

    :id: c23d582e-502c-49ac-83f7-dcf0f192cbc6

    :expectedresults: Docker repository is promoted to content view
        found in the specific lifecycle-environments.

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    content_view = entities.ContentView(
        composite=False, organization=module_org, repository=[repo]
    ).create()
    content_view.publish()
    with session:
        for _ in range(randint(2, 3)):
            lce = entities.LifecycleEnvironment(organization=module_org).create()
            result = session.contentview.promote(content_view.name, VERSION, lce.name)
            assert f'Promoted to {lce.name}' in result['Status']
            assert lce.name in result['Environments']


@pytest.mark.tier2
def test_positive_promote_with_docker_repo_composite(session, module_org, module_prod):
    """Add docker repository to composite content view and publish it.
    Then promote it to the next available lifecycle-environment.

    :id: 1c7817c7-60b5-4383-bc6f-2878c2b27fa5

    :expectedresults: Docker repository is promoted to content view
        found in the specific lifecycle-environment.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    content_view = entities.ContentView(
        composite=False, organization=module_org, repository=[repo]
    ).create()
    content_view.publish()
    content_view = content_view.read()
    composite_cv = entities.ContentView(
        component=[content_view.version[-1]], composite=True, organization=module_org
    ).create()
    composite_cv.publish()
    with session:
        result = session.contentview.promote(composite_cv.name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        assert lce.name in result['Environments']


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_promote_multiple_with_docker_repo_composite(session, module_org, module_prod):
    """Add docker repository to composite content view and publish it
    Then promote it to the multiple available lifecycle environments.

    :id: b735b1fa-3d60-4fc0-92d2-4af0ab003097

    :expectedresults: Docker repository is promoted to content view
        found in the specific lifecycle-environments.

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    content_view = entities.ContentView(
        composite=False, organization=module_org, repository=[repo]
    ).create()
    content_view.publish()
    content_view = content_view.read()
    composite_cv = entities.ContentView(
        component=[content_view.version[-1]], composite=True, organization=module_org
    ).create()
    composite_cv.publish()
    with session:
        for _ in range(randint(2, 3)):
            lce = entities.LifecycleEnvironment(organization=module_org).create()
            result = session.contentview.promote(composite_cv.name, VERSION, lce.name)
            assert f'Promoted to {lce.name}' in result['Status']
            assert lce.name in result['Environments']


@pytest.mark.tier2
def test_negative_add_components_to_non_composite(session):
    """Attempt to associate components to a non-composite content view

    :id: fa3e6aea-7ee3-46a6-a5ba-248de3c20a8f

    :expectedresults: User cannot add components to the view

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    cv1_name = gen_string('alpha')
    cv2_name = gen_string('alpha')
    with session:
        session.contentview.create({'name': cv1_name})
        for cv_name in (cv1_name, cv2_name):
            session.contentview.create({'name': cv_name})
            assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        with pytest.raises(AssertionError) as context:
            session.contentview.add_cv(cv1_name, cv2_name)
        assert 'Could not find "Content Views" tab' in str(context.value)


@pytest.mark.tier2
def test_positive_add_unpublished_cv_to_composite(session):
    """Attempt to associate unpublished non-composite content view with
    composite content view.

    :id: dc253606-3425-489d-bc01-266787d36841

    :steps:

        1. Create an empty non-composite content view. Do not publish it.
        2. Create a new composite content view

    :expectedresults: Non-composite content view is added to composite one

    :CaseLevel: Integration

    :CaseImportance: Low

    :BZ: 1367123
    """
    unpublished_cv_name = gen_string('alpha')
    composite_cv_name = gen_string('alpha')
    with session:
        # Create unpublished component CV
        session.contentview.create({'name': unpublished_cv_name})
        assert session.contentview.search(unpublished_cv_name)[0]['Name'] == unpublished_cv_name
        # Create composite CV
        session.contentview.create({'name': composite_cv_name, 'composite_view': True})
        assert session.contentview.search(composite_cv_name)[0]['Name'] == composite_cv_name
        # Add unpublished content view to composite one
        session.contentview.add_cv(composite_cv_name, unpublished_cv_name)


@pytest.mark.tier3
def test_positive_add_non_composite_cv_to_composite(session):
    """Attempt to associate both published and unpublished non-composite
    content views with composite content view.

    :id: 93307c2a-a03f-44fa-972d-43f6e40b9de6

    :steps:

        1. Create an empty non-composite content view. Do not publish it
        2. Create a second non-composite content view. Publish it.
        3. Create a new composite content view.
        4. Add the published non-composite content view to the composite
            content view.
        5. Add the unpublished non-composite content view to the composite
            content view.

    :expectedresults:

        1. Unpublished non-composite content view is successfully added to
            composite content view.
        2. Published non-composite content view is successfully added to
            composite content view.
        3. Composite content view is successfully published

    :CaseLevel: Integration

    :BZ: 1367123

    :CaseImportance: High
    """
    published_cv_name = gen_string('alpha')
    unpublished_cv_name = gen_string('alpha')
    composite_cv_name = gen_string('alpha')
    with session:
        # Create a published component content view
        session.contentview.create({'name': published_cv_name})
        assert session.contentview.search(published_cv_name)[0]['Name'] == published_cv_name
        result = session.contentview.publish(published_cv_name)
        assert result['Version'] == VERSION
        # Create an unpublished component content view
        session.contentview.create({'name': unpublished_cv_name})
        assert session.contentview.search(unpublished_cv_name)[0]['Name'] == unpublished_cv_name
        # Create a composite content view
        session.contentview.create({'name': composite_cv_name, 'composite_view': True})
        assert session.contentview.search(composite_cv_name)[0]['Name'] == composite_cv_name
        # Add the published content view to the composite one
        session.contentview.add_cv(composite_cv_name, published_cv_name)
        # Add the unpublished content view to the composite one
        session.contentview.add_cv(composite_cv_name, unpublished_cv_name)
        # assert that the version of unpublished content view added to
        # composite one is "Latest (Currently no version)"
        composite_cv = session.contentview.read(composite_cv_name)
        assigned_cvs = composite_cv['content_views']['resources']['assigned']
        unpublished_cv = next(cv for cv in assigned_cvs if cv['Name'] == unpublished_cv_name)
        assert unpublished_cv['Version'] == 'Latest (Currently no version)'
        # Publish the composite content view
        result = session.contentview.publish(composite_cv_name)
        assert result['Version'] == VERSION


@pytest.mark.tier3
def test_positive_check_composite_cv_addition_list_versions(session):
    """Create new content view and publish two times. After that remove
    first content view version from the list and try to add that view to
    composite one. Check what content view version is going to be added

    :id: ffd4ac4a-4152-433a-a411-567bab115b05

    :expectedresults: second non-composite content view version should be
        listed as default one to be added to composite view

    :CaseLevel: Integration

    :BZ: 1411074

    :CaseImportance: Low
    """
    non_composite_cv = gen_string('alpha')
    composite_cv = gen_string('alpha')
    with session:
        # Create unpublished component CV
        session.contentview.create({'name': non_composite_cv})
        assert session.contentview.search(non_composite_cv)[0]['Name'] == non_composite_cv
        # Publish content view two times to have two versions
        for _ in range(2):
            session.contentview.publish(non_composite_cv)
        # Delete first version for cv
        session.contentview.remove_version(non_composite_cv, VERSION)
        # Create composite CV
        session.contentview.create({'name': composite_cv, 'composite_view': True})
        assert session.contentview.search(composite_cv)[0]['Name'] == composite_cv
        ccv_values = session.contentview.read(composite_cv, 'content_views')
        cv_values = [
            cv
            for cv in ccv_values['content_views']['resources']['unassigned']
            if cv['Name'] == non_composite_cv
        ]
        assert len(cv_values) == 1
        assert cv_values[0]['Version'] == 'Always Use Latest (Currently 2.0) 2.0'


@pytest.mark.tier2
def test_negative_add_dupe_repos(session, module_org):
    """attempt to associate the same repo multiple times within a
    content view

    :id: 24b98075-fca6-4d80-a778-066193c71e7f

    :expectedresults: User cannot add repos multiple times to the view

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    cv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        with pytest.raises(NoSuchElementException) as context:
            session.contentview.add_yum_repo(cv_name, repo_name)
        error_message = str(context.value)
        assert 'Could not find an element' in error_message
        assert 'checkbox' in error_message


@pytest.mark.tier2
def test_positive_publish_with_custom_content(session, module_org):
    """Attempt to publish a content view containing custom content

    :id: 66b5efc7-2e43-438e-bd80-a754814222f9

    :setup: Multiple environments for an org; custom content synced

    :expectedresults: Content view can be published

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    repo_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        cv = session.contentview.read(cv_name)
        assert cv['versions']['table'][0]['Version'] == VERSION


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
def test_positive_publish_with_rh_content(session):
    """Attempt to publish a content view containing RH content

    :id: bd24dc13-b6c4-4a9b-acb2-cd6df30f436c

    :setup: RH content synced

    :expectedresults: Content view can be published

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    cv_name = gen_string('alpha')
    rh_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    enable_sync_redhat_repo(rh_repo, org.id)
    with session:
        session.organization.select(org.name)
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, rh_repo['name'])
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        cv = session.contentview.read(cv_name)
        assert cv['versions']['table'][0]['Version'] == VERSION


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_publish_composite_with_custom_content(session):
    """Attempt to publish composite content view containing custom content

    :id: 73947204-408e-4e2e-b87f-ba2e52ee50b6

    :setup: Multiple environments for an org; custom content synced

    :expectedresults: Composite content view can be published

    :CaseLevel: Integration

    :CaseImportance: High
    """
    cv1_name = gen_string('alpha')
    cv2_name = gen_string('alpha')
    cv_composite_name = gen_string('alpha')
    custom_repo1_name = gen_string('alpha')
    custom_repo2_name = gen_string('alpha')
    custom_repo1_url = settings.repos.yum_0.url
    custom_repo2_url = settings.repos.yum_1.url
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    rh7_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    # Create docker repos and sync
    docker_repo1 = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=product, content_type=REPO_TYPE['docker']
    ).create()
    docker_repo2 = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=product, content_type=REPO_TYPE['docker']
    ).create()
    docker_repo1.sync()
    docker_repo2.sync()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    # Enable and sync RH repository
    enable_sync_redhat_repo(rh7_repo, org.id)
    # Create custom yum repositories
    for name, url in (
        (custom_repo1_name, custom_repo1_url),
        (custom_repo2_name, custom_repo2_url),
    ):
        create_sync_custom_repo(repo_name=name, repo_url=url, org_id=org.id)
    with session:
        session.organization.select(org.name)
        # create the first content view
        session.contentview.create({'name': cv1_name})
        assert session.contentview.search(cv1_name)[0]['Name'] == cv1_name
        # add repositories to first content view
        for repo_name in (rh7_repo['name'], custom_repo1_name):
            session.contentview.add_yum_repo(cv1_name, repo_name)
        # add the first docker repo to first content view
        session.contentview.add_docker_repo(cv1_name, docker_repo1.name)
        # publish the first content
        result = session.contentview.publish(cv1_name)
        assert result['Version'] == VERSION
        # create the second content view
        session.contentview.create({'name': cv2_name})
        assert session.contentview.search(cv2_name)[0]['Name'] == cv2_name
        # add repositories to the second content view
        session.contentview.add_yum_repo(cv2_name, custom_repo2_name)
        # add the second docker repo to the second content view
        session.contentview.add_docker_repo(cv2_name, docker_repo2.name)
        # publish the second content
        result = session.contentview.publish(cv2_name)
        assert result['Version'] == VERSION
        # create a composite content view
        session.contentview.create({'name': cv_composite_name, 'composite_view': True})
        assert session.contentview.search(cv_composite_name)[0]['Name'] == cv_composite_name
        # add the first and second content views to the composite one
        for cv_name in (cv1_name, cv2_name):
            session.contentview.add_cv(cv_composite_name, cv_name)
        # publish the composite content view
        result = session.contentview.publish(cv_composite_name)
        assert result['Version'] == VERSION
        ccv = session.contentview.read(cv_composite_name)
        assert ccv['versions']['table'][0]['Version'] == VERSION


@pytest.mark.tier2
def test_positive_publish_version_changes_in_target_env(session, module_org):
    # Dev notes:
    # If Dev has version x, then when I promote version y into
    # Dev, version x goes away (ie when I promote version 1 to Dev,
    # version 3 goes away)
    """When publishing new version to environment, version gets updated

    :id: c9fa3def-baa2-497f-b6a6-f3b2d72d1ce9

    :setup: Multiple environments for an org; multiple versions of a content
        view created/published

    :steps:
        1. publish a view to an environment noting the CV version
        2. edit and republish a new version of a CV

    :expectedresults: Content view version is updated in target environment.

    :CaseLevel: Integration

    :CaseImportance: High
    """
    cv_name = gen_string('alpha')
    # will promote environment to 3 versions
    versions_count = 3
    versions = (f'Version {ver + 1}.0' for ver in range(versions_count))
    # create environment lifecycle
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    repo_names = [gen_string('alphanumeric') for _ in range(versions_count)]
    # before each content view publishing add a new repository
    for repo_name in repo_names:
        create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        # create content view
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        # begin publishing content view and promoting environment over all
        # the defined versions
        for repo_name in repo_names:
            version = next(versions)
            # add the repository to the created content view
            session.contentview.add_yum_repo(cv_name, repo_name)
            # publish the content view
            result = session.contentview.publish(cv_name)
            # assert the content view successfully published
            assert result['Version'] == version
            # # assert that Library is in environments of this version
            assert ENVIRONMENT in result['Environments']
            # assert that env_name is not in environments of this version
            assert lce.name not in result['Environments']
            # promote content view environment to this version
            result = session.contentview.promote(cv_name, version, lce.name)
            assert f'Promoted to {lce.name}' in result['Status']
            # assert that Library is still in environments of this version
            assert ENVIRONMENT in result['Environments']
            # assert that env_name is in environments of this version
            assert lce.name in result['Environments']


@pytest.mark.tier2
def test_positive_promote_with_custom_content(session, module_org):
    """Attempt to promote a content view containing custom content,
        check dashboard

    :id: 7c2fd8f0-c83f-4725-8953-9590112fae50

    :setup: Multiple environments for an org; custom content synced

    :expectedresults: Content view can be promoted

    :CaseLevel: Integration

    :BZ: 1361793

    :CaseImportance: Critical
    """
    repo_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        # dashboard
        values = session.dashboard.search(f'lifecycle_environment={lce.name}')
        assert cv_name in values['ContentViews']['content_views'][0]['Content View']
        values = session.dashboard.read('ContentViews')
        assert cv_name in values['content_views'][0]['Content View']
        assert values['content_views'][0]['Task'] == f'Promoted to {lce.name}'
        assert 'Success' in values['content_views'][0]['Status']
        assert cv_name in values['content_views'][1]['Content View']
        assert values['content_views'][1]['Task'] == 'Published new version'
        assert 'Success' in values['content_views'][1]['Status']
        entities.LifecycleEnvironment(id=lce.id).delete()
        values = session.dashboard.search(f'lifecycle_environment={lce.name}')
        assert cv_name in values['ContentViews']['content_views'][0]['Content View']


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
def test_positive_promote_with_rh_content(session):
    """Attempt to promote a content view containing RH content

    :id: 82f71639-3580-49fd-bd5a-8dba568b98d1

    :setup: Multiple environments for an org; RH content synced

    :expectedresults: Content view can be promoted

    :CaseLevel: System

    :CaseImportance: Critical
    """
    cv_name = gen_string('alpha')
    rh_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    enable_sync_redhat_repo(rh_repo, org.id)
    lce = entities.LifecycleEnvironment(organization=org).create()
    with session:
        session.organization.select(org.name)
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, rh_repo['name'])
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_promote_composite_with_custom_content(session):
    """Attempt to promote composite content view containing custom content

    :id: 35efbd83-d32e-4831-9d5b-1adb15289f54

    :setup: Multiple environments for an org; custom content synced

    :steps: create a composite view containing multiple content types

    :expectedresults: Composite content view can be promoted

    :CaseLevel: Integration

    :CaseImportance: High
    """
    cv1_name = gen_string('alpha')
    cv2_name = gen_string('alpha')
    cv_composite_name = gen_string('alpha')
    custom_repo1_name = gen_string('alpha')
    custom_repo2_name = gen_string('alpha')
    custom_repo1_url = settings.repos.yum_0.url
    custom_repo2_url = settings.repos.yum_1.url
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    rh7_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    # create a life cycle environment
    lce = entities.LifecycleEnvironment(organization=org).create()
    # Enable and sync RH repository
    enable_sync_redhat_repo(rh7_repo, org.id)
    # Create custom yum repositories
    for name, url in (
        (custom_repo1_name, custom_repo1_url),
        (custom_repo2_name, custom_repo2_url),
    ):
        create_sync_custom_repo(repo_name=name, repo_url=url, org_id=org.id)
    # Create docker repo and sync
    docker_repo1 = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=product, content_type=REPO_TYPE['docker']
    ).create()
    docker_repo2 = entities.Repository(
        url=CONTAINER_REGISTRY_HUB,
        product=product,
        content_type=REPO_TYPE['docker'],
        docker_upstream_name='quay/busybox',
    ).create()
    docker_repo1.sync()
    docker_repo2.sync()
    with session:
        session.organization.select(org.name)
        # create the first content view
        session.contentview.create({'name': cv1_name})
        assert session.contentview.search(cv1_name)[0]['Name'] == cv1_name
        # add repositories to first content view
        for repo_name in (rh7_repo['name'], custom_repo1_name):
            session.contentview.add_yum_repo(cv1_name, repo_name)
        # add the first docker repo to first content view
        session.contentview.add_docker_repo(cv1_name, docker_repo1.name)
        # publish the first content
        result = session.contentview.publish(cv1_name)
        assert result['Version'] == VERSION
        # create the second content view
        session.contentview.create({'name': cv2_name})
        assert session.contentview.search(cv2_name)[0]['Name'] == cv2_name
        # add repositories to the second content view
        session.contentview.add_yum_repo(cv2_name, custom_repo2_name)
        # add second docker to the second content view
        session.contentview.add_docker_repo(cv1_name, docker_repo2.name)
        # publish the second content
        result = session.contentview.publish(cv2_name)
        assert result['Version'] == VERSION
        # create a composite content view
        session.contentview.create({'name': cv_composite_name, 'composite_view': True})
        assert session.contentview.search(cv_composite_name)[0]['Name'] == cv_composite_name
        # add the first and second content views to the composite one
        for cv_name in (cv1_name, cv2_name):
            session.contentview.add_cv(cv_composite_name, cv_name)
        # publish the composite content view
        result = session.contentview.publish(cv_composite_name)
        assert result['Version'] == VERSION
        # promote the composite content view
        result = session.contentview.promote(cv_composite_name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']


@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_positive_publish_rh_content_with_errata_by_date_filter(session):
    """Publish a CV, containing only RH repo, having errata excluding by
    date filter

    :BZ: 1455990, 1492114

    :id: b4c120b6-129f-4344-8634-df5858c10fef

    :customerscenario: true

    :expectedresults: Errata exclusion by date filter doesn't affect
        packages - errata was successfully filtered out, however packages
        are still present

    :CaseImportance: High
    """
    version = 'Version 2.0'
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL6, repositories=[VirtualizationAgentsRepository()]
    )
    repos_collection.setup_content(
        org.id, lce.id, download_policy='immediate', upload_manifest=True
    )
    cv = entities.ContentView(id=repos_collection.setup_content_data['content_view']['id']).read()
    cvf = entities.ErratumContentViewFilter(
        content_view=cv, inclusion=False, repository=[repos_collection.repos_info[0]['id']]
    ).create()
    entities.ContentViewFilterRule(
        content_view_filter=cvf,
        start_date='2011-01-01',
        types=['security', 'enhancement', 'bugfix'],
    ).create()
    cv.publish()
    with session:
        session.organization.select(org.name)
        version = session.contentview.read_version(cv.name, version)
        assert len(version['rpm_packages']['table'])
        assert not version.get('errata') or not len(version['errata']['table'])


@pytest.mark.tier3
def test_negative_add_same_package_filter_twice(session, module_org):
    """Update version of package inside exclusive cv package filter

    :id: 5a97de5a-679e-4150-adf7-b4a28290b834

    :expectedresults: Same package filter can not be added again

    :CaseLevel: Integration

    :CaseImportance: High
    """
    cv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package_name = 'walrus'
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        session.contentview.create({'name': cv_name})
        for filter_type in FILTER_TYPE['exclude'], FILTER_TYPE['include']:
            filter_name = gen_string('alpha')
            session.contentviewfilter.create(
                cv_name,
                {
                    'name': filter_name,
                    'content_type': FILTER_CONTENT_TYPE['package'],
                    'inclusion_type': filter_type,
                },
            )
            assert session.contentviewfilter.search(cv_name, filter_name)[0]['Name'] == filter_name
            session.contentviewfilter.add_package_rule(
                cv_name, filter_name, package_name, None, ('Equal To', '0.71-1')
            )
            with pytest.raises(AssertionError) as context:
                session.contentviewfilter.add_package_rule(
                    cv_name, filter_name, package_name, None, ('Equal To', '0.71-1')
                )
            assert 'This package filter rule already exists.' in str(context.value)


@pytest.mark.tier2
def test_positive_remove_cv_version_from_default_env(session, module_org):
    """Remove content view version from Library environment

    :id: 43c83c15-c883-45a7-be05-d9b26da99e3c

    :Steps:

        1. Create a content view
        2. Add a yum repo to it
        3. Publish content view
        4. remove the published version from Library environment

    :expectedresults: content view version is removed from Library
        environment

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    cv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        # create a content view
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        cvv = session.contentview.search_version(cv_name, VERSION)[0]
        assert ENVIRONMENT in cvv['Environments']
        # remove the content view version from Library
        session.contentview.remove_version(cv_name, VERSION, False, [ENVIRONMENT])
        cvv = session.contentview.search_version(cv_name, VERSION)[0]
        assert ENVIRONMENT not in cvv['Environments']


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_remove_promoted_cv_version_from_default_env(session, module_org):
    """Remove promoted content view version from Library environment

    :id: a8649444-b063-4fb4-b932-a3fae7d4021d

    :Steps:

        1. Create a content view
        2. Add a yum repos to the content view
        3. Publish the content view
        4. Promote the content view version from Library -> DEV
        5. remove the content view version from Library environment

    :expectedresults:

        1. Content view version exist only in DEV and not in Library
        2. The yum repos exists in content view version

    :CaseLevel: Integration

    :CaseImportance: High
    """
    repo = RepositoryCollection(
        repositories=[
            YumRepository(url=settings.repos.yum_0.url),
        ]
    )
    repo.setup(module_org.id)
    cv, lce = repo.setup_content_view(module_org.id)
    with session:
        cv_values = session.contentview.read(cv['name'])
        assert cv_values['details']['name'] == cv['name']
        cvv = session.contentview.read_version(cv['name'], VERSION)
        assert cvv['yum_repositories']['table'][0]['Name']
        cvv = session.contentview.search_version(cv['name'], VERSION)[0]
        assert ENVIRONMENT in cvv['Environments']
        # remove the content view version from Library
        session.contentview.remove_version(cv['name'], VERSION, False, [ENVIRONMENT])
        cvv = session.contentview.search_version(cv['name'], VERSION)[0]
        assert ENVIRONMENT not in cvv['Environments']
        # ensure that yum repos are still in content view version
        cvv = session.contentview.read_version(cv['name'], VERSION)
        assert cvv['yum_repositories']['table'][0]['Name']


@pytest.mark.tier2
def test_positive_remove_qe_promoted_cv_version_from_default_env(session, module_org):
    """Remove QE promoted content view version from Library environment

    :id: 71ad8b72-68c4-4c98-9387-077f54ef0184

    :Steps:

        1. Create a content view
        2. Add docker repo(s) to it
        3. Publish content view
        4. Promote the content view version to multiple environments
            Library -> DEV -> QE
        5. remove the content view version from Library environment

    :expectedresults: Content view version exist only in DEV, QE and not in
        Library

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    dev_lce = entities.LifecycleEnvironment(organization=module_org).create()
    qe_lce = entities.LifecycleEnvironment(organization=module_org, prior=dev_lce).create()
    repo = RepositoryCollection(
        repositories=[
            DockerRepository(url=CONTAINER_REGISTRY_HUB, upstream_name=CONTAINER_UPSTREAM_NAME)
        ]
    )
    repo.setup(module_org.id)
    repo_name = repo.repos_info[0]['name']
    cv, lce = repo.setup_content_view(module_org.id, dev_lce.id)
    cvv = entities.ContentView(id=cv['id']).read().version[0]
    promote(cvv, qe_lce.id)
    with session:
        cv_values = session.contentview.read(cv['name'])
        assert cv_values['docker_repositories']['resources']['assigned'][0]['Name'] == repo_name
        cvv_content = session.contentview.read_version(cv['name'], VERSION)
        assert cvv_content['docker_repositories']['table'][0]['Name'] == repo_name
        cvv_table = session.contentview.search_version(cv['name'], VERSION)
        assert all(
            item in cvv_table[0]['Environments']
            for item in [ENVIRONMENT, dev_lce.name, qe_lce.name]
        )
        # remove the content view version from Library
        session.contentview.remove_version(cv['name'], VERSION, False, [ENVIRONMENT])
        cvv_content = session.contentview.read_version(cv['name'], VERSION)
        assert cvv_content['docker_repositories']['table'][0]['Name'] == repo_name
        cvv_table = session.contentview.search_version(cv['name'], VERSION)
        assert all(item in cvv_table[0]['Environments'] for item in [dev_lce.name, qe_lce.name])


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_remove_cv_version_from_env(session, module_org):
    """Remove promoted content view version from environment

    :id: d1da23ee-a5db-4990-9572-1a0919a9fe1c

    :Steps:

        1. Create a content view
        2. Add a yum repo and a docker repo to the content view
        3. Publish the content view
        4. Promote the content view version to multiple environments
            Library -> DEV -> QE
        5. remove the content view version from QE environment
        6. Assert: content view version exists only in Library, DEV and not in QE
        7. Promote again from DEV -> QE

    :expectedresults: Content view version exist in Library, DEV, QE

    :CaseLevel: Integration

    :CaseImportance: High
    """
    dev_lce = entities.LifecycleEnvironment(organization=module_org).create()
    qe_lce = entities.LifecycleEnvironment(organization=module_org, prior=dev_lce).create()
    repos = RepositoryCollection(
        repositories=[
            YumRepository(url=settings.repos.yum_0.url),
            DockerRepository(url=CONTAINER_REGISTRY_HUB, upstream_name=CONTAINER_UPSTREAM_NAME),
        ]
    )
    repos.setup(module_org.id)
    yum_repo_name = [repo['name'] for repo in repos.repos_info if repo['content-type'] == 'yum'][0]
    docker_repo_name = [
        repo['name'] for repo in repos.repos_info if repo['content-type'] == 'docker'
    ][0]
    cv, lce = repos.setup_content_view(module_org.id, dev_lce.id)
    cvv = entities.ContentView(id=cv['id']).read().version[0]
    promote(cvv, qe_lce.id)
    with session:
        cvv = session.contentview.read_version(cv['name'], VERSION)
        assert cvv['yum_repositories']['table'][0]['Name']
        assert cvv['docker_repositories']['table'][0]['Name']
        assert yum_repo_name == cvv['yum_repositories']['table'][0]['Name']
        cvv = session.contentview.search_version(cv['name'], VERSION)[0]
        assert all(item in cvv['Environments'] for item in [ENVIRONMENT, dev_lce.name, qe_lce.name])
        # remove the content view version from QE Environment
        session.contentview.remove_version(cv['name'], VERSION, False, [qe_lce.name])
        cvv = session.contentview.search_version(cv['name'], VERSION)[0]
        assert all(item in cvv['Environments'] for item in [ENVIRONMENT, dev_lce.name])
        # promote again to QE
        result = session.contentview.promote(cv['name'], VERSION, qe_lce.name)
        assert f'Promoted to {qe_lce.name}' in result['Status']
        cvv = session.contentview.read_version(cv['name'], VERSION)
        assert docker_repo_name in cvv['docker_repositories']['table'][0]['Name']
        assert yum_repo_name == cvv['yum_repositories']['table'][0]['Name']
        cvv = session.contentview.search_version(cv['name'], VERSION)[0]
        assert all(item in cvv['Environments'] for item in [ENVIRONMENT, dev_lce.name, qe_lce.name])


@pytest.mark.upgrade
@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_delete_cv_promoted_to_multi_env(session, module_org):
    """Delete published content view with version promoted to multiple
     environments

    :id: f16f2db5-7f5b-4ebb-863e-6c18ff745ce4

    :Steps:

        1. Create a content view
        2. Add a yum repo to the content view
        3. Publish the content view
        4. Promote the content view to multiple environment Library -> DEV
        5. Disassociate content view from promoted environment
        6. Delete the content view.

    :expectedresults: The content view doesn't exists.

    :CaseLevel: Integration

    :CaseImportance:High
    """
    repo = RepositoryCollection(repositories=[YumRepository(url=settings.repos.yum_0.url)])
    repo.setup(module_org.id)
    cv, lce = repo.setup_content_view(module_org.id)
    repo_name = repo.repos_info[0]['name']
    with session:
        cvv = session.contentview.read_version(cv['name'], VERSION)
        assert repo_name == cvv['yum_repositories']['table'][0]['Name']
        cvv = session.contentview.search_version(cv['name'], VERSION)[0]
        assert lce['name'] in cvv['Environments']
        lce_values = session.lifecycleenvironment.read(lce['name'])
        assert len(lce_values['content_views']['resources']) == 1
        assert lce_values['content_views']['resources'][0]['Name'] == cv['name']
        session.contentview.remove_version(cv['name'], VERSION, False, [ENVIRONMENT, lce['name']])
        cvv = session.contentview.search_version(cv['name'], VERSION)[0]
        assert lce['name'] not in cvv['Environments']
        session.contentview.delete(cv['name'])
        lce_values = session.lifecycleenvironment.read(lce['name'])
        assert cv not in lce_values['content_views']['resources']


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_composite_version(session, module_org):
    """Delete a composite content-view version associated to 'Library'

    :id: b2d9b21d-1e0d-40f1-9bbc-3c88cddd4f5e

    :expectedresults: Deletion was performed successfully

    :CaseLevel: Integration

    :BZ: 1276479

    :CaseImportance: High
    """
    cv_name = gen_string('alpha')
    ccv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        # create a content view
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        session.contentview.create({'name': ccv_name, 'composite_view': True})
        session.contentview.add_cv(ccv_name, cv_name)
        result = session.contentview.publish(ccv_name)
        assert result['Version'] == VERSION
        cvv = session.contentview.search_version(ccv_name, VERSION)[0]
        assert ENVIRONMENT in cvv['Environments']
        # remove composite content view version from Library
        session.contentview.remove_version(ccv_name, VERSION, False, [ENVIRONMENT])
        cvv = session.contentview.search_version(ccv_name, VERSION)[0]
        assert ENVIRONMENT not in cvv['Environments']


@pytest.mark.tier2
def test_positive_delete_non_default_version(session):
    """Delete a content-view version associated to non-default
    environment

    :id: 1c1beb36-e06b-419f-96db-43b4d85c5e25

    :expectedresults: Deletion was performed successfully

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    repo_name = gen_string('alpha')
    org = entities.Organization().create()
    create_sync_custom_repo(org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(query={'organization_id': org.id})[0]
    cv = entities.ContentView(organization=org, repository=[repo]).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    with session:
        session.organization.select(org.name)
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv.name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv.name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        cvv = session.contentview.search_version(cv.name, VERSION)[0]
        assert lce.name in cvv['Environments']
        # remove the content view version from new custom lifecycle environment
        session.contentview.remove_version(cv.name, VERSION, False, [lce.name])
        cvv = session.contentview.search_version(cv.name, VERSION)[0]
        assert lce.name not in cvv['Environments']


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_delete_version_with_ak(session):
    """Delete a content-view version that had associated activation key to it

    :id: 0da50b26-f82b-4663-9372-4c39270d4323

    :expectedresults: Delete operation was performed successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    org = entities.Organization().create()
    cv = entities.ContentView(organization=org).create()
    cv.publish()
    cvv = cv.read().version[0].read()
    lc_env = entities.LifecycleEnvironment(organization=org).create()
    promote(cvv, lc_env.id)
    ak = entities.ActivationKey(
        name=gen_string('alphanumeric'), environment=lc_env.id, organization=org, content_view=cv
    ).create()
    with session:
        session.organization.select(org.name)
        assert session.contentview.search_version(cv.name, VERSION)
        # It is impossible to remove content view version from content view that
        # has activation key assigned
        with pytest.raises(AssertionError) as context:
            session.contentview.remove_version(cv.name, VERSION)
        assert 'Activation Key is assigned to content view version' in str(context.value)
        # Update activation key with new name
        session.activationkey.update(
            ak.name, {'details.lce': {ENVIRONMENT: True}, 'details.content_view': DEFAULT_CV}
        )
        # remove the content view version
        session.contentview.remove_version(cv.name, VERSION)
        assert session.contentview.search_version(cv.name, VERSION)[0]['Version'] != VERSION


@pytest.mark.tier2
def test_positive_clone_within_same_env(session, module_org):
    """attempt to create new content view based on existing
    view within environment

    :id: 862c385b-d98c-4c29-8345-fd7a5900483a

    :expectedresults: Content view can be cloned

    :BZ: 1461017

    :CaseLevel: Integration

    :CaseImportance: High
    """
    repo_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    copy_cv_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        # Copy the CV
        session.contentview.copy(cv_name, copy_cv_name)
        assert session.contentview.search(copy_cv_name)[0]['Name'] == copy_cv_name
        copy_cv = session.contentview.read(copy_cv_name)
        assert copy_cv['repositories']['resources']['assigned'][0]['Name'] == repo_name


@pytest.mark.tier2
def test_positive_clone_within_diff_env(session, module_org):
    """attempt to create new content view based on existing
    view, inside a different environment

    :id: 09b9307f-91de-4d3d-a6af-31c526ea816f

    :expectedresults: Cloned content view can be published and promoted to different
        environment than initial one

    :BZ: 1461017

    :CaseLevel: Integration

    :CaseImportance: High
    """
    repo_name = gen_string('alpha')
    copy_cv_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    copy_lce = entities.LifecycleEnvironment(organization=module_org).create()
    with session:
        # publish the content view
        result = session.contentview.publish(cv.name)
        assert result['Version'] == VERSION
        # promote the content view
        result = session.contentview.promote(cv.name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        # Copy the CV
        session.contentview.copy(cv.name, copy_cv_name)
        assert session.contentview.search(copy_cv_name)[0]['Name'] == copy_cv_name
        copy_cv = session.contentview.read(copy_cv_name)
        assert copy_cv['repositories']['resources']['assigned'][0]['Name'] == repo_name
        # publish new content view
        result = session.contentview.publish(copy_cv_name)
        assert result['Version'] == VERSION
        # promote cloned content view to different environment
        result = session.contentview.promote(copy_cv_name, VERSION, copy_lce.name)
        assert f'Promoted to {copy_lce.name}' in result['Status']
        assert lce.name not in result['Environments']


@pytest.mark.tier2
def test_positive_remove_filter(session, module_org):
    """Create empty content views filter and remove it

    :id: 6c6deae7-13f1-4638-a960-d3565d93fd64

    :expectedresults: content views filter removed successfully

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    filter_name = gen_string('alpha')
    cv = entities.ContentView(organization=module_org).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['exclude'],
            },
        )
        assert session.contentviewfilter.search(cv.name, filter_name)[0]['Name'] == filter_name
        session.contentviewfilter.delete(cv.name, filter_name)
        assert not session.contentviewfilter.search(cv.name, filter_name)


@pytest.mark.tier2
def test_positive_add_package_filter(session, module_org):
    """Add package to content views filter

    :id: 1cc8d921-92e5-4b51-8050-a7e775095f97

    :expectedresults: content views filter created and selected packages can be
        added for inclusion

    :CaseLevel: Integration

    :CaseImportance: High
    """
    packages = (
        ('cow', 'All Versions'),
        ('bird', ('Equal To', '0.5')),
        ('crow', ('Less Than', '0.5')),
        ('bear', ('Range', '4.1', '4.6')),
    )
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        for package_name, versions in packages:
            session.contentviewfilter.add_package_rule(
                cv.name, filter_name, package_name, None, versions
            )
        cvf = session.contentviewfilter.read(cv.name, filter_name)
        expected_packages = {package_name for package_name, versions in packages}
        actual_packages = {row['RPM Name'] for row in cvf['content_tabs']['rpms']['table']}
        assert expected_packages == actual_packages


@pytest.mark.tier3
def test_positive_add_package_inclusion_filter_and_publish(session, module_org):
    """Add package to inclusion content views filter, publish CV and verify
    package was actually filtered

    :id: 58c32cb5-1392-478e-807a-9c023d5ca0ea

    :expectedresults: Package is included in content view version

    :CaseLevel: Integration

    :CaseImportance: High
    """
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package1_name = 'cow'
    package2_name = 'bear'
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        session.contentviewfilter.add_package_rule(
            cv.name, filter_name, package1_name, None, 'All Versions'
        )
        result = session.contentview.publish(cv.name)
        assert result['Version'] == VERSION
        packages = session.contentview.search_version_package(
            cv.name, VERSION, f'name = "{package1_name}"'
        )
        assert len(packages) == 1
        assert packages[0]['Name'] == package1_name
        packages = session.contentview.search_version_package(
            cv.name, VERSION, f'name = "{package2_name}"'
        )
        assert not packages[0]['Name']


@pytest.mark.tier3
def test_positive_add_package_exclusion_filter_and_publish(session, module_org):
    """Add package to exclusion content views filter, publish CV and verify
    package was actually filtered

    :id: 304dfb76-a222-48ab-b6de-578a2c81210c

    :expectedresults: Package is excluded from content view version

    :CaseLevel: Integration

    :CaseImportance: High
    """
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package1_name = 'cow'
    package2_name = 'bear'
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['exclude'],
            },
        )
        session.contentviewfilter.add_package_rule(
            cv.name, filter_name, package1_name, None, 'All Versions'
        )
        result = session.contentview.publish(cv.name)
        assert result['Version'] == VERSION
        packages = session.contentview.search_version_package(
            cv.name, VERSION, f'name = "{package2_name}"'
        )
        assert len(packages) == 1
        assert packages[0]['Name'] == package2_name
        packages = session.contentview.search_version_package(
            cv.name, VERSION, f'name = "{package1_name}"'
        )
        assert not packages[0]['Name']


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_remove_package_from_exclusion_filter(session, module_org):
    """Remove package from content view exclusion filter

    :id: 2f0adc16-2305-4adf-8582-82e6110fa385

    :expectedresults: Package was successfully removed from content view
        filter and is present in next published content view version

    :CaseLevel: Integration

    :CaseImportance: High
    """
    filter_name = gen_string('alpha')
    package_name = 'cow'
    repo = RepositoryCollection(repositories=[YumRepository(url=settings.repos.yum_1.url)])
    repo.setup(module_org.id)
    cv, lce = repo.setup_content_view(module_org.id)
    with session:
        session.contentviewfilter.create(
            cv['name'],
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['exclude'],
            },
        )
        session.contentviewfilter.add_package_rule(
            cv['name'], filter_name, package_name, None, ('Equal To', '2.2-3')
        )
        result = session.contentview.publish(cv['name'])
        assert result['Version'] == 'Version 2.0'
        packages = session.contentview.search_version_package(
            cv['name'], 'Version 2.0', f'name = "{package_name}"'
        )
        assert not packages[0]['Name']
        session.contentviewfilter.remove_package_rule(cv['name'], filter_name, package_name)
        result = session.contentview.publish(cv['name'])
        assert result['Version'] == 'Version 3.0'
        packages = session.contentview.search_version_package(
            cv['name'], 'Version 3.0', f'name = "{package_name}"'
        )
        assert len(packages) == 1
        assert packages[0]['Name'] == package_name


@pytest.mark.tier3
def test_positive_update_inclusive_filter_package_version(session, module_org):
    """Update version of package inside inclusive cv package filter

    :id: 8d6801de-ab82-49d6-bdeb-0f6e5c95b906

    :expectedresults: Version was updated, next content view version contains
        package with updated version

    :CaseLevel: Integration

    :CaseImportance: High
    """
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package_name = 'walrus'
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        session.contentviewfilter.add_package_rule(
            cv.name, filter_name, package_name, None, ('Equal To', '0.71-1')
        )
        result = session.contentview.publish(cv.name)
        assert result['Version'] == VERSION
        packages = session.contentview.search_version_package(
            cv.name, VERSION, 'name = "{}" and version = "{}"'.format(package_name, '0.71')
        )
        assert len(packages) == 1
        assert packages[0]['Name'] == package_name and packages[0]['Version'] == '0.71'
        packages = session.contentview.search_version_package(
            cv.name, VERSION, 'name = "{}" and version = "{}"'.format(package_name, '5.21')
        )
        assert not packages[0]['Name']
        session.contentviewfilter.update_package_rule(
            cv.name,
            filter_name,
            package_name,
            {'Version': ('Equal To', '5.21-1')},
            version='Version 0.71-1',
        )
        new_version = session.contentview.publish(cv.name)['Version']
        packages = session.contentview.search_version_package(
            cv.name, new_version, 'name = "{}" and version = "{}"'.format(package_name, '0.71')
        )
        assert not packages[0]['Name']
        packages = session.contentview.search_version_package(
            cv.name, new_version, 'name = "{}" and version = "{}"'.format(package_name, '5.21')
        )
        assert len(packages) == 1
        assert packages[0]['Name'] == package_name and packages[0]['Version'] == '5.21'


@pytest.mark.tier3
def test_positive_update_exclusive_filter_package_version(session, module_org):
    """Update version of package inside exclusive cv package filter

    :id: a8aa8864-190a-46c3-aeed-4953c8f3f601

    :expectedresults: Version was updated, next content view version
        contains package with updated version

    :CaseLevel: Integration

    :CaseImportance: High
    """
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package_name = 'walrus'
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['exclude'],
            },
        )
        session.contentviewfilter.add_package_rule(
            cv.name, filter_name, package_name, None, ('Equal To', '0.71-1')
        )
        result = session.contentview.publish(cv.name)
        assert result['Version'] == VERSION
        packages = session.contentview.search_version_package(
            cv.name, VERSION, 'name = "{}" and version = "{}"'.format(package_name, '5.21')
        )
        assert len(packages) == 1
        assert packages[0]['Name'] == package_name and packages[0]['Version'] == '5.21'
        packages = session.contentview.search_version_package(
            cv.name, VERSION, 'name = "{}" and version = "{}"'.format(package_name, '0.71')
        )
        assert not packages[0]['Name']
        session.contentviewfilter.update_package_rule(
            cv.name,
            filter_name,
            package_name,
            {'Version': ('Equal To', '5.21-1')},
            version='Version 0.71-1',
        )
        new_version = session.contentview.publish(cv.name)['Version']
        packages = session.contentview.search_version_package(
            cv.name, new_version, 'name = "{}" and version = "{}"'.format(package_name, '5.21')
        )
        assert not packages[0]['Name']
        packages = session.contentview.search_version_package(
            cv.name, new_version, 'name = "{}" and version = "{}"'.format(package_name, '0.71')
        )
        assert len(packages) == 1
        assert packages[0]['Name'] == package_name and packages[0]['Version'] == '0.71'


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_all_security_errata_by_date_range_filter(session, module_org):
    """Create erratum date range filter to include only security errata and
    publish new content view version

    :id: c8f4453b-e654-4e8d-9156-5443bfb92f23

    :CaseImportance: High

    :expectedresults: all security errata is present in content view
        version
    """
    filter_name = gen_string('alphanumeric')
    start_date = datetime.date(2010, 1, 1)
    end_date = datetime.date.today()
    repo = RepositoryCollection(repositories=[YumRepository(url=settings.repos.yum_9.url)])
    repo.setup(module_org.id)
    cv, lce = repo.setup_content_view(module_org.id)
    with session:
        session.contentviewfilter.create(
            cv['name'],
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['erratum by date and type'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        session.contentviewfilter.update(
            cv['name'],
            filter_name,
            {
                'content_tabs.erratum_date_range.security': True,
                'content_tabs.erratum_date_range.enhancement': False,
                'content_tabs.erratum_date_range.bugfix': False,
                'content_tabs.erratum_date_range.date_type': 'Issued On',
                'content_tabs.erratum_date_range.start_date': start_date.strftime('%m-%d-%Y'),
                'content_tabs.erratum_date_range.end_date': end_date.strftime('%m-%d-%Y'),
            },
        )
        session.contentview.publish(cv['name'])
        cvv = session.contentview.read_version(cv['name'], 'Version 2.0')
        assert len(cvv['errata']['table']) == FAKE_9_YUM_SECURITY_ERRATUM_COUNT
        assert all(
            errata['Type'] == FILTER_ERRATA_TYPE['security'] for errata in cvv['errata']['table']
        )


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.tier3
def test_positive_edit_rh_custom_spin(session):
    """Edit content views for a custom rh spin.  For example, modify a filter.

    :id: 05639074-ef6d-4c6b-8ff6-53033821e686

    :expectedresults: edited content view save is successful and info is
        updated

    :CaseLevel: System

    :CaseImportance: High
    """
    filter_name = gen_string('alpha')
    start_date = datetime.date(2016, 1, 1)
    end_date = datetime.date(2016, 6, 1)
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7, repositories=[SatelliteToolsRepository()]
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    cv = entities.ContentView(id=repos_collection.setup_content_data['content_view']['id']).read()
    with session:
        session.organization.select(org.name)
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['erratum by date and type'],
                'inclusion_type': FILTER_TYPE['exclude'],
            },
        )
        session.contentviewfilter.update(
            cv.name,
            filter_name,
            {
                'content_tabs.erratum_date_range.security': False,
                'content_tabs.erratum_date_range.enhancement': True,
                'content_tabs.erratum_date_range.bugfix': True,
                'content_tabs.erratum_date_range.date_type': 'Issued On',
                'content_tabs.erratum_date_range.start_date': start_date.strftime('%m-%d-%Y'),
                'content_tabs.erratum_date_range.end_date': end_date.strftime('%m-%d-%Y'),
            },
        )
        cvf = session.contentviewfilter.read(cv.name, filter_name)
        assert not cvf['content_tabs']['erratum_date_range']['security']
        assert cvf['content_tabs']['erratum_date_range']['enhancement']
        assert cvf['content_tabs']['erratum_date_range']['bugfix']
        assert cvf['content_tabs']['erratum_date_range']['date_type'] == 'Issued On'
        assert cvf['content_tabs']['erratum_date_range']['start_date'] == start_date.strftime(
            '%Y-%m-%d'
        )
        assert cvf['content_tabs']['erratum_date_range']['end_date'] == end_date.strftime(
            '%Y-%m-%d'
        )


@pytest.mark.run_in_one_thread
@pytest.mark.skip_if_not_set('fake_manifest')
@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_promote_with_rh_custom_spin(session):
    """attempt to promote a content view containing a custom RH
    spin - i.e., contains filters.

    :id: 7d93c81f-2815-4b0e-b72c-23a902fe34b1

    :expectedresults: Content view can be promoted

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    filter_name = gen_string('alpha')
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7, repositories=[SatelliteToolsRepository()]
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    cv = entities.ContentView(id=repos_collection.setup_content_data['content_view']['id']).read()
    with session:
        session.organization.select(org.name)
        # add a package exclude filter
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['exclude'],
            },
        )
        # assert the added filter visible
        assert session.contentviewfilter.search(cv.name, filter_name)[0]['Name'] == filter_name
        # exclude some package in the created filter
        session.contentviewfilter.add_package_rule(
            cv.name, filter_name, 'gofer', None, 'All Versions'
        )
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv.name)
        assert result['Version'] == 'Version 2.0'
        result = session.contentview.promote(cv.name, 'Version 2.0', lce.name)
        assert f'Promoted to {lce.name}' in result['Status']


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_all_security_errata_by_id_filter(session, module_org):
    """Create erratum filter to include only security errata and publish new
    content view version

    :id: bc0be8e8-af53-4db8-937d-93c49c937dcc

    :customerscenario: true

    :BZ: 1275756

    :CaseImportance: High

    :expectedresults: all security errata is present in content view version
    """
    version = 'Version 2.0'
    filter_name = gen_string('alphanumeric')
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product, url=settings.repos.yum_9.url).create()
    repo.sync()
    content_view = entities.ContentView(organization=module_org, repository=[repo]).create()
    content_view.publish()
    with session:
        session.contentviewfilter.create(
            content_view.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['erratum by id'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        session.contentviewfilter.add_errata(
            content_view.name,
            filter_name,
            search_filters={'security': True, 'bugfix': False, 'enhancement': False},
        )
        content_view.publish()
        cvv = session.contentview.read_version(content_view.name, version)
        assert len(cvv['errata']['table']) == FAKE_9_YUM_SECURITY_ERRATUM_COUNT
        assert all(
            errata['Type'] == FILTER_ERRATA_TYPE['security'] for errata in cvv['errata']['table']
        )


@pytest.mark.tier3
def test_positive_add_errata_filter(session, module_org):
    """add errata to content views filter

    :id: bb9eef30-62c4-435c-9573-9f31210b8d7d

    :expectedresults: content views filter created and selected errata-id
        can be added for inclusion/exclusion

    :CaseLevel: Integration

    :CaseImportance: High
    """
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['erratum by id'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        for errata in ['RHEA-2012:0001', 'RHEA-2012:0004']:
            session.contentviewfilter.add_errata(cv.name, filter_name, errata)
        cv.publish()
        cvv = session.contentview.read_version(cv.name, VERSION)
        assert len(cvv['errata']['table']) == 2
        assert {'RHEA-2012:0001', 'RHEA-2012:0004'} == {
            value['Errata ID'] for value in cvv['errata']['table']
        }


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_module_stream_filter(session, module_org):
    """add module stream filter in a content view

    :id: 343c543e-5773-4ea4-aff4-27e0ed6be19e

    :expectedresults: content views filter created and selected module stream
        can be added for inclusion/exclusion

    :CaseLevel: Integration

    :CaseImportance: High
    """
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    create_sync_custom_repo(
        module_org.id, repo_name=repo_name, repo_url=settings.repos.module_stream_1.url
    )
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['modulemd'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        for ms_name, ms_version in [('duck', '0'), ('walrus', '5.21')]:
            session.contentviewfilter.add_module_stream(
                cv.name, filter_name, f'name = {ms_name} and stream = {ms_version}'
            )
        cv.publish()
        cvv = session.contentview.read_version(cv.name, VERSION)
        assert len(cvv['module_streams']['table']) == 2
        assert {('duck', '0'), ('walrus', '5.21')} == {
            (value['Name'], value['Stream']) for value in cvv['module_streams']['table']
        }


@pytest.mark.tier3
def test_positive_add_package_group_filter(session, module_org):
    """add package group to content views filter

    :id: 8c02a432-8b2a-4ba3-9613-7070b2dc2bcb

    :expectedresults: content views filter created and selected package
        groups can be added for inclusion/exclusion

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package_group = 'mammals'
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package group'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        session.contentviewfilter.add_package_group(cv.name, filter_name, package_group)
        cvf = session.contentviewfilter.read(cv.name, filter_name)
        assert cvf['content_tabs']['assigned'][0]['Name'] == package_group


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_update_filter_affected_repos(session, module_org):
    """Update content view package filter affected repos

    :id: 8f095b11-fd63-4a23-9586-a85d6191314f

    :expectedresults: Affected repos were updated, after new content view
        version publishing only updated repos are affected by content view
        filter

    :CaseLevel: Integration

    :CaseImportance: High
    """
    filter_name = gen_string('alpha')
    repo1_name = gen_string('alpha')
    repo2_name = gen_string('alpha')
    repo1_package_name = 'dolphin'
    repo2_package_name = 'dolphin'
    create_sync_custom_repo(module_org.id, repo_name=repo1_name, repo_url=settings.repos.yum_3.url)
    create_sync_custom_repo(module_org.id, repo_name=repo2_name)
    repo1 = entities.Repository(name=repo1_name).search(query={'organization_id': module_org.id})[0]
    repo2 = entities.Repository(name=repo2_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo1, repo2]).create()
    with session:
        # create a filter that affects a subset of repos in the cv
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        session.contentviewfilter.add_package_rule(
            cv.name, filter_name, repo1_package_name, None, ('Equal To', '4.2.8')
        )
        session.contentviewfilter.update_repositories(cv.name, filter_name, [repo1_name])
        cv.publish()
        # Verify filter affected repo1
        packages = session.contentview.search_version_package(
            cv.name, VERSION, 'name = "{}" and version = "{}"'.format(repo1_package_name, '4.2.8')
        )
        assert len(packages) == 1
        assert packages[0]['Name'] == repo1_package_name and packages[0]['Version'] == '4.2.8'
        packages = session.contentview.search_version_package(
            cv.name, VERSION, 'name = "{}" and version = "{}"'.format(repo1_package_name, '4.2.9')
        )
        # checking search showing empty result
        assert not packages[0]['Name']
        # Verify repo2 was not affected and repo2 packages are present
        packages = session.contentview.search_version_package(
            cv.name,
            VERSION,
            'name = "{}" and version = "{}"'.format(repo2_package_name, '3.10.232'),
        )
        assert len(packages) == 1
        assert packages[0]['Name'] == repo2_package_name and packages[0]['Version'] == '3.10.232'


@pytest.mark.tier3
def test_positive_search_composite(session):
    """Search for content view by its composite property criteria

    :id: 214a721b-3993-4251-9b7c-0f6d2446c1d1

    :customerscenario: true

    :expectedresults: Composite content view is successfully found

    :BZ: 1259374

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    composite_name = gen_string('alpha')
    with session:
        session.contentview.create({'name': composite_name, 'composite_view': True})
        assert composite_name in {
            ccv['Name'] for ccv in session.contentview.search('composite = true')
        }


@pytest.mark.tier3
def test_positive_publish_with_repo_with_disabled_http(session, module_org):
    """Attempt to publish content view with repository that set
    'publish via http' to False

    :id: 36ccb083-3433-4b54-911a-856e3dc85f39

    :customerscenario: true

    :steps:
        1.  Create a repo with 'publish via http' set to true, url set to
            some upstream repo
        2.  Sync the repo
        3.  Create a content view
        4.  Set 'publish via http' to false
        5.  Add this repo to the content view
        6.  Publish the content view

    :expectedresults: Content view is published successfully

    :BZ: 1355752

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    repo_name = gen_string('alpha')
    product_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    # Creates a CV along with product and sync'ed repository
    create_sync_custom_repo(
        module_org.id, product_name=product_name, repo_name=repo_name, repo_unprotected=True
    )
    with session:
        # Create content-view
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        # Update repository publishing method
        session.repository.update(product_name, repo_name, {'repo_content.publish_via_http': False})
        session.contentview.add_yum_repo(cv_name, repo_name)
        # Publish content view
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_subscribe_system_with_custom_content(session, rhel7_contenthost, default_sat):
    """Attempt to subscribe a host to content view with custom repository

    :id: 715db997-707b-4868-b7cc-b6977fd6ac04

    :setup: content view with custom yum repo

    :expectedresults: Systems can be subscribed to content view(s)

    :CaseLevel: Integration

    :CaseImportance: High
    """
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7,
        repositories=[SatelliteToolsRepository(), YumRepository(url=settings.repos.yum_0.url)],
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    repos_collection.setup_virtual_machine(rhel7_contenthost, default_sat)
    assert rhel7_contenthost.subscribed
    with session:
        session.organization.select(org.name)
        session.location.select(constants.DEFAULT_LOC)
        # assert the vm exists in content hosts page
        assert (
            session.contenthost.search(rhel7_contenthost.hostname)[0]['Name']
            == rhel7_contenthost.hostname
        )


@pytest.mark.tier3
def test_positive_delete_with_kickstart_repo_and_host_group(session, default_sat):
    """Check that Content View associated with kickstart repository and
    which is used by a host group can be removed from the system

    :id: 7b076f55-72c9-4413-a592-92a47b51cb0a

    :customerscenario: true

    :expectedresults: Deletion was performed successfully

    :BZ: 1417072

    :CaseLevel: Integration

    :CaseImportance: High
    """
    hg_name = gen_string('alpha')
    org = entities.Organization().create()
    # Create a new Lifecycle environment
    lc_env = entities.LifecycleEnvironment(organization=org).create()
    # Create a Product and Kickstart Repository for OS distribution content
    product = entities.Product(organization=org).create()
    repo = entities.Repository(product=product, url=settings.repos.rhel7_os).create()
    # Repo sync procedure
    call_entity_method_with_timeout(repo.sync, timeout=3600)
    # Create, Publish and promote CV
    content_view = entities.ContentView(organization=org).create()
    content_view.repository = [repo]
    content_view = content_view.update(['repository'])
    content_view.publish()
    content_view = content_view.read()
    promote(content_view.version[0], lc_env.id)
    cv_name = content_view.name
    # Get the Partition table ID
    ptable = entities.PartitionTable().search(query={'search': f'name="{DEFAULT_PTABLE}"'})[0]
    # Get the arch ID
    arch = (
        entities.Architecture().search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0].read()
    )
    # Get the OS ID
    os = entities.OperatingSystem().search(
        query={
            'search': 'name="RedHat" AND (major="{}" OR major="{}")'.format(
                RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION
            )
        }
    )[0]
    # Update the OS to associate arch and ptable
    os.architecture = [arch]
    os.ptable = [ptable]
    os = os.update(['architecture', 'ptable'])
    with session:
        session.organization.select(org.name)
        session.hostgroup.create(
            {
                'host_group.name': hg_name,
                'host_group.lce': lc_env.name,
                'host_group.content_view': content_view.name,
                'operating_system.architecture': arch.name,
                'operating_system.operating_system': f'{os.name} {os.major}.{os.minor}',
                'operating_system.ptable': ptable.name,
                'operating_system.media_type': 'Synced Content',
                'operating_system.media_content.synced_content': repo.name,
            }
        )
        assert session.hostgroup.search(hg_name)[0]['Name'] == hg_name
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        with pytest.raises(AssertionError) as context:
            session.contentview.delete(cv_name)
        assert 'Unable to delete content view' in str(context.value)
        # remove the content view version
        session.contentview.remove_version(cv_name, VERSION)
        assert session.contentview.search_version(cv_name, VERSION)[0]['Version'] != VERSION
        session.contentview.delete(cv_name)
        assert session.contentview.search(cv_name)[0]['Name'] != cv_name


@pytest.mark.skip_if_open("BZ:1625783")
@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_custom_ostree_end_to_end(session, module_org):
    """Create content view with custom ostree contents, publish and promote it
    to Library +1 env. Then disassociate repository from that content view

    :id: 869623c8-9547-4432-9e02-4aeece2efd2f

    :steps:
        1. Create ostree content and sync it
        2. Create content view and add created repo to it
        3. Publish that content view
        4. Promote it to next environment
        5. Remove repository from content view

    :expectedresults: Content view works properly with custom OSTree repository and
        has expected output after each step

    :CaseLevel: System

    :CaseImportance: High

    :BZ: 1625783

    :customerscenario: true
    """
    repo_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    create_sync_custom_repo(
        module_org.id,
        repo_url=FEDORA27_OSTREE_REPO,
        repo_type=REPO_TYPE['ostree'],
        repo_name=repo_name,
        repo_unprotected=False,
    )
    with session:
        # Create new content view
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        # Add OSTree repository to content view
        session.contentview.add_ostree_repo(cv_name, repo_name)
        cv = session.contentview.read(cv_name)
        assert cv['ostree_content']['resources']['assigned'][0]['Name'] == repo_name
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        # Remove repository from content view
        session.contentview.remove_ostree_repo(cv_name, repo_name)
        cv = session.contentview.read(cv_name)
        assert len(cv['ostree_content']['resources']['assigned']) == 0
        assert cv['ostree_content']['resources']['unassigned'][0]['Name'] == repo_name


@pytest.mark.skip_if_open("BZ:1625783")
@pytest.mark.tier3
def test_positive_rh_ostree_end_to_end(session):
    """Create content view with RH ostree contents, publish and promote it
    to Library +1 env. Then disassociate repository from that content view

    :id: 5773dde0-1862-420e-a347-b801c9af43d4

    :steps:
        1. Create RH ostree content and sync it
        2. Create content view and add created repo to it
        3. Publish that content view
        4. Promote it to next environment
        5. Remove repository from content view

    :expectedresults: Content view works properly with RH OSTree repository and
        has expected output after each step

    :CaseLevel: System

    :CaseImportance: Low

    :BZ: 1625783
    """
    cv_name = gen_string('alpha')
    rh_repo = {
        'name': REPOS['rhaht']['name'],
        'product': PRDS['rhah'],
        'reposet': REPOSET['rhaht'],
        'basearch': None,
        'releasever': None,
    }
    repo_name = rh_repo['name']
    # Create new org to import manifest
    org = entities.Organization().create()
    manifests.upload_manifest_locked(org.id)
    enable_sync_redhat_repo(rh_repo, org.id)
    lce = entities.LifecycleEnvironment(organization=org).create()
    with session:
        session.organization.select(org.name)
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_ostree_repo(cv_name, repo_name)
        cv = session.contentview.read(cv_name)
        assert cv['ostree_content']['resources']['assigned'][0]['Name'] == repo_name
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        # Remove repository from content view
        session.contentview.remove_ostree_repo(cv_name, repo_name)
        cv = session.contentview.read(cv_name)
        assert len(cv['ostree_content']['resources']['assigned']) == 0
        assert cv['ostree_content']['resources']['unassigned'][0]['Name'] == repo_name


@pytest.mark.skip_if_open("BZ:1625783")
@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_mixed_content_end_to_end(session, module_org):
    """Create a CV with ostree as well as yum and docker contents and
    publish and promote them to next environment. Remove promoted version afterwards

    :id: 6da1a167-cef8-420e-9fdd-bf357f820056

    :expectedresults: CV should be published and promoted with custom
        OSTree and all other contents. Then version is removed successfully

    :CaseLevel: System

    :CaseImportance: High

    :customerscenario: true

    :BZ: 1625783
    """
    cv_name = gen_string('alpha')
    product = entities.Product(organization=module_org).create()
    ostree_repo_name = gen_string('alpha')
    # Creates ostree content
    entities.Repository(
        name=ostree_repo_name,
        url=FEDORA27_OSTREE_REPO,
        content_type=REPO_TYPE['ostree'],
        product=product,
        unprotected=False,
    ).create()
    # Create docker repo
    docker_repo_name = gen_string('alpha')
    entities.Repository(
        name=docker_repo_name,
        url=CONTAINER_REGISTRY_HUB,
        product=product,
        content_type=REPO_TYPE['docker'],
    ).create()
    yum_repo_name = gen_string('alpha')
    # Creates yum repository
    entities.Repository(
        name=yum_repo_name,
        url=settings.repos.yum_1.url,
        content_type=REPO_TYPE['yum'],
        product=product,
    ).create()
    # Sync all repositories in the product
    product.sync()
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    entities.ContentView(name=cv_name, organization=module_org).create()
    with session:
        session.contentview.add_yum_repo(cv_name, yum_repo_name)
        session.contentview.add_docker_repo(cv_name, docker_repo_name)
        session.contentview.add_ostree_repo(cv_name, ostree_repo_name)
        cv = session.contentview.read(cv_name)
        assert cv['repositories']['resources']['assigned'][0]['Name'] == yum_repo_name
        assert cv['docker_repositories']['resources']['assigned'][0]['Name'] == docker_repo_name
        assert cv['ostree_content']['resources']['assigned'][0]['Name'] == ostree_repo_name
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        # remove the content view version
        session.contentview.remove_version(cv_name, VERSION)
        assert session.contentview.search_version(cv_name, VERSION)[0]['Version'] != VERSION


@pytest.mark.upgrade
@pytest.mark.tier3
def test_positive_rh_mixed_content_end_to_end(session, module_prod, module_org):
    """Create a CV with docker repo as well as RH yum contents and publish and promote
    them to next environment. Remove promoted version afterwards

    :id: 752f7b95-26af-4f20-a49d-7b31ae3d7a1a

    :expectedresults: CV should be published and promoted with RH OSTree and all
        other contents. Then version is removed successfully.

    :CaseLevel: System

    :customerscenario: true

    :CaseImportance: High
    """
    cv_name = gen_string('alpha')
    docker_repo = entities.Repository(
        url=CONTAINER_REGISTRY_HUB, product=module_prod, content_type=REPO_TYPE['docker']
    ).create()
    rh_st_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    manifests.upload_manifest_locked(module_org.id)
    enable_sync_redhat_repo(rh_st_repo, module_org.id)
    docker_repo.sync()
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    with session:
        session.organization.select(module_org.name)
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, rh_st_repo['name'])
        session.contentview.add_docker_repo(cv_name, docker_repo.name)
        cv = session.contentview.read(cv_name)
        assert cv['repositories']['resources']['assigned'][0]['Name'] == rh_st_repo['name']
        assert cv['docker_repositories']['resources']['assigned'][0]['Name'] == docker_repo.name
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        # remove the content view version
        session.contentview.remove_version(cv_name, VERSION)
        assert session.contentview.search_version(cv_name, VERSION)[0]['Version'] != VERSION


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_errata_inc_update_list_package(session, default_sat):
    """Publish incremental update with a new errata for a custom repo

    :BZ: 1489778

    :id: fb43791c-60ee-4190-86be-34ccba411396

    :customerscenario: true

    :expectedresults: New errata and corresponding package are present
        in new content view version

    :CaseImportance: High

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    yum_repo_name = gen_string('alpha')
    # Creates custom yum repository
    yum_repo = entities.Repository(
        name=yum_repo_name,
        url=settings.repos.yum_1.url,
        content_type=REPO_TYPE['yum'],
        product=product,
    ).create()
    product.sync()
    # creating cv, cv filter, and publish cv
    cv = entities.ContentView(organization=org, repository=[yum_repo]).create()
    cvf = entities.RPMContentViewFilter(
        content_view=cv, inclusion=True, name=gen_string('alphanumeric')
    ).create()
    entities.ContentViewFilterRule(
        content_view_filter=cvf,
        name='walrus',
        version='0.71',
    ).create()
    cv.publish()
    # Get published content-view version info
    cvvs = entities.ContentView(id=cv.id).read().version
    assert len(cvvs) == 1
    cvv = cvvs[0].read()
    result = ContentView.version_incremental_update(
        {'content-view-version-id': cvv.id, 'errata-ids': settings.repos.yum_1.errata[1]}
    )
    result = [line.strip() for line_dict in result for line in line_dict.values()]
    with session:
        session.organization.select(org.name)
        cvv = entities.ContentView(id=cv.id).read().version[1].read()
        version = session.contentview.read_version(cv.name, f'Version {cvv.version}')
        errata = version['errata']['table']
        assert len(errata) == 1
        assert settings.repos.yum_1.errata[1] in {row['Errata ID'] for row in errata}
        packages = version['rpm_packages']['table']
        assert len(packages) == 4
        packages = {'{}-{}-{}.{}'.format(*row.values()) for row in packages}
        assert set(result[4:]).issubset(packages)


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_composite_child_inc_update(session, rhel7_contenthost, default_sat):
    """Incremental update with a new errata on a child content view should
    trigger incremental update of parent composite content view

    :BZ: 1304891

    :id: 1a870ad6-c79c-49fc-b449-8c7e74dd95ff

    :customerscenario: true

    :Steps:

        1. Create a custom repo with filters that excludes the updated package
        2. Create content view with custom repo publish and
           promote it
        3. Create another content view with Satellite tools in it, publish
           and promote it to the same environment
        4. Create composite content view, add content views from previous
           steps in it (force using the latest versions)
        5. Promote composite content view
        6. Create activation key with subscriptions to both child content
           views
        7. Register a content host with activation key, install certs,
           katello agent, enable repositories
        8. Install outdated package in the content host (walrus-0.71)
        9. On the WebUI, find the errata with the updated package, make sure it's applicable for
            the host
        10. Install the errata to the host, agree with incremental update

    :expectedresults:

        1. Errata installation was successful
        2. Incremental version of composite content view was published
        3. Latest version of composite content view contains the errata and
           updated package

    :CaseImportance: Medium

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    product = entities.Product(organization=org).create()
    yum_repo_name = gen_string('alpha')
    # Creates custom yum repository
    yum_repo = entities.Repository(
        name=yum_repo_name,
        url=settings.repos.yum_1.url,
        content_type=REPO_TYPE['yum'],
        product=product,
    ).create()
    product.sync()
    # creating cv, cv filter, and publish cv
    cv = entities.ContentView(organization=org, repository=[yum_repo]).create()
    cvf = entities.RPMContentViewFilter(
        content_view=cv, inclusion=False, name=gen_string('alphanumeric')
    ).create()
    entities.ContentViewFilterRule(
        content_view_filter=cvf,
        name='walrus',
        version='5.21',
    ).create()
    cv.publish()
    cvv = entities.ContentView(id=cv.id).read().version[0]
    promote(cvv, lce.id)
    # Setup tools repo and add it to ak
    repos_collection = RepositoryCollection(
        distro=constants.DISTRO_RHEL7, repositories=[SatelliteToolsRepository()]
    )
    content_data = repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    # adding custom repo subscription to ak
    ak_id = content_data['activation_key']['id']
    command = (
        f'hammer activation-key add-subscription --id {ak_id} '
        f'--subscription {product.name} --organization-id {org.id}'
    )
    result = default_sat.execute(command)
    assert result.status == 0
    # Create composite cv
    composite_cv = entities.ContentView(composite=True, organization=org).create()
    # Adds all repos to composite cv
    composite_cv.component = [
        entities.ContentView(id=content_data['content_view']['id']).read().version[0],
        cvv,
    ]
    composite_cv = composite_cv.update(['component'])
    # Publish and promote
    composite_cv.publish()
    promote(composite_cv.read().version[0], lce.id)
    # Update AK to use composite cv
    entities.ActivationKey(
        id=content_data['activation_key']['id'], content_view=composite_cv
    ).update(['content_view'])
    repos_collection.setup_virtual_machine(rhel7_contenthost, default_sat)
    result = rhel7_contenthost.run(f'yum -y install {FAKE_1_CUSTOM_PACKAGE}')
    assert result.status == 0
    with session:
        session.organization.select(org.name)
        session.location.select('Default Location')
        result = session.errata.install(settings.repos.yum_1.errata[1], rhel7_contenthost.hostname)
        assert result['result'] == 'success'
        expected_version = 'Version 1.1'
        version = session.contentview.read_version(composite_cv.name, expected_version)
        errata = version['errata']['table']
        assert len(errata) > 1
        assert settings.repos.yum_1.errata[1] in {row['Errata ID'] for row in errata}
        nvra1 = parse_nvra(FAKE_2_CUSTOM_PACKAGE)
        packages = session.contentview.search_version_package(
            composite_cv.name, expected_version, nvra1['name']
        )
        packages_data = {'{}-{}-{}.{}'.format(*row.values()) for row in packages}
        assert FAKE_2_CUSTOM_PACKAGE in packages_data


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_module_stream_end_to_end(session, module_org):
    """Create content view with custom module_stream contents, publish and promote it
    to Library +1 env. Then disassociate repository from that content view

    :id: 66955a89-14ed-414e-a15a-6ed9ede520ea

    :steps:
        1. Create yum repo with module_stream content and sync it
        2. Create content view and add created repo to it
        3. Publish that content view
        4. Promote it to next environment

    :expectedresults: Content view works properly with module_streams and
        count shown should be correct

    :CaseLevel: Integration

    :CaseImportance: Medium
    """
    repo_name = gen_string('alpha')
    env_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    # Creates a CV along with product and sync'ed repository
    create_sync_custom_repo(
        module_org.id, repo_name=repo_name, repo_url=settings.repos.module_stream_1.url
    )
    with session:
        # Create Life-cycle environment
        session.lifecycleenvironment.create({'name': env_name})
        # Create content-view
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        # Add repository to selected CV
        session.contentview.add_yum_repo(cv_name, repo_name)
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, env_name)
        assert f'Promoted to {env_name}' in result['Status']
        assert '7 Module Streams' in result['Content']
        # remove the content view version
        session.contentview.remove_version(cv_name, VERSION)
        assert session.contentview.search_version(cv_name, VERSION)[0]['Version'] != VERSION
        session.contentview.delete(cv_name)
        assert session.contentview.search(cv_name)[0]['Name'] != cv_name


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_search_module_streams_in_content_view(session, module_org):
    """Search module streams in content view version

    :id: 7f5273ff-e80f-459d-adf4-b517b6d60fdc

    :expectedresults: Searching for module streams should work inside content
        view version

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    repo_name = gen_string('alpha')
    module_stream = 'walrus'
    create_sync_custom_repo(
        module_org.id, repo_name=repo_name, repo_url=settings.repos.module_stream_1.url
    )
    repo = entities.Repository(name=repo_name).search(query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        result = session.contentview.publish(cv.name)
        assert result['Version'] == VERSION
        for module_version in ['0.71', '5.21']:
            module_streams = session.contentview.search_version_module_stream(
                cv.name,
                VERSION,
                f'name = "{module_stream}" and stream = "{module_version}"',
            )
            assert len(module_streams) == 1
            assert (
                module_streams[0]['Name'] == module_stream
                and module_streams[0]['Stream'] == module_version
            )


@pytest.mark.tier2
def test_positive_non_admin_user_actions(session, module_org, test_name):
    """Attempt to manage content views

    :id: c4d270fc-a3e6-4ae2-a338-41d864a5622a

    :steps: with global admin account:

        1. create a user with all content views permissions
        2. create lifecycle environment
        3. create 2 content views (one to delete, the other to manage)

    :setup: create a user with all content views permissions

    :expectedresults: Custom user can Read, Modify, Delete, Publish, Promote
        the content views

    :BZ: 1461017

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    # note: the user to be created should not have permissions to access
    # products repositories
    repo_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    cv_new_name = gen_string('alpha')
    cv_copy_name = gen_string('alpha')
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    # create a role with all content views permissions
    role = entities.Role().create()
    create_role_permissions(role, {'Katello::ContentView': PERMISSIONS['Katello::ContentView']})
    create_role_permissions(
        role,
        {
            'Katello::KTEnvironment': [
                'promote_or_remove_content_views_to_environments',
                'view_lifecycle_environments',
            ]
        },
        search=f'name = {ENVIRONMENT} or name = {lce.name}',
    )
    # create a user and assign the above created role
    entities.User(
        default_organization=module_org,
        organization=[module_org],
        role=[role],
        login=user_login,
        password=user_password,
        mail='test@test.com',
    ).create()
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    # create a content view with the main admin account
    with session:
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        # Copy the CV
        session.contentview.copy(cv_name, cv_copy_name)
        assert session.contentview.search(cv_copy_name)[0]['Name'] == cv_copy_name
    # login as the user created above
    with Session(test_name, user=user_login, password=user_password) as session:
        with pytest.raises(NavigationTriesExceeded):
            session.organization.create({'name': gen_string('alpha'), 'label': gen_string('alpha')})
        # assert the user can view all the content views created
        # by admin user
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        assert session.contentview.search(cv_copy_name)[0]['Name'] == cv_copy_name
        # assert that the user can delete a content view
        session.contentview.delete(cv_copy_name)
        assert session.contentview.search(cv_copy_name)[0]['Name'] != cv_copy_name
        session.contentview.update(cv_name, {'details.name': cv_new_name})
        assert session.contentview.search(cv_new_name)[0]['Name'] == cv_new_name
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_new_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_new_name, VERSION, lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        # check that cv tabs are accessible
        cv = session.contentview.read(cv_new_name)
        for tab_name in [
            'details',
            'versions',
            'repositories',
            'filters',
            'docker_repositories',
        ]:
            assert cv.get(tab_name) is not None


@pytest.mark.tier2
def test_positive_readonly_user_actions(module_org, test_name):
    """Attempt to view content views

    :id: ebdc37ed-7887-4f64-944c-f2f92c58a206

    :setup:

        1. create a user with the Content View read-only role
        2. create content view
        3. add a custom repository to content view

    :expectedresults: User with read-only role for content view can view
        the repository in the content view

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    # create a role with content views read only permissions
    role = entities.Role().create()
    create_role_permissions(role, {'Katello::ContentView': ['view_content_views']})
    create_role_permissions(role, {'Katello::Product': ['view_products']})
    # create a user and assign the above created role
    entities.User(
        default_organization=module_org,
        organization=[module_org],
        role=[role],
        login=user_login,
        password=user_password,
    ).create()
    repo_id = create_sync_custom_repo(module_org.id)
    yum_repo = entities.Repository(id=repo_id).read()
    cv = entities.ContentView(organization=module_org, repository=[yum_repo]).create()
    cv.publish()
    # login as the user created above
    with Session(test_name, user=user_login, password=user_password) as session:
        with pytest.raises(NavigationTriesExceeded):
            session.location.create({'name': gen_string('alpha'), 'label': gen_string('alpha')})
        assert session.contentview.search(cv.name)[0]['Name'] == cv.name
        cv_values = session.contentview.read(cv.name)
        assert cv_values['details']['name'] == cv.name
        assert cv_values['versions']['table'][0]['Version'] == VERSION
        assert cv_values['repositories']['resources']['assigned'][0]['Name'] == yum_repo.name


@pytest.mark.tier2
def test_negative_read_only_user_actions(session, module_org, test_name):
    """Attempt to manage content views

    :id: aae6eede-b40e-4e06-a5f7-59d9251aa35d

    :setup:

        1. create a user with the Content View read-only role
        2. create content view
        3. add a custom repository to content view

    :expectedresults: User with read only role for content view cannot
        Modify, Delete, Publish, Promote the content views.  Additionally,
        users cannot create content view, create product, create host collection,
        create activation key, or see repo discovery

    :BZ: 1922134

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    # create a content view read only user with lifecycle environment
    # permissions: view_lifecycle_environments and
    # promote_or_remove_content_views_to_environments
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    # create a role with content views read only permissions
    role = entities.Role().create()
    create_role_permissions(role, {'Katello::ContentView': ['view_content_views']})
    create_role_permissions(
        role,
        {
            'Katello::KTEnvironment': [
                'promote_or_remove_content_views_to_environments',
                'view_lifecycle_environments',
            ]
        },
        search=f'name = {ENVIRONMENT} or name = {lce.name}',
    )
    # create a user and assign the above created role
    entities.User(
        default_organization=module_org,
        organization=[module_org],
        role=[role],
        login=user_login,
        password=user_password,
    ).create()
    repo_id = create_sync_custom_repo(module_org.id)
    yum_repo = entities.Repository(id=repo_id).read()
    repo_name = 'fakerepo01'
    cv = entities.ContentView(organization=module_org, repository=[yum_repo]).create()
    # login as the user created above
    with Session(test_name, user=user_login, password=user_password) as custom_session:
        with pytest.raises(NavigationTriesExceeded):
            custom_session.location.create(
                {'name': gen_string('alpha'), 'label': gen_string('alpha')}
            )
        assert custom_session.contentview.search(cv.name)[0]['Name'] == cv.name
        # Cannot update content view
        with pytest.raises(InvalidElementStateException):
            custom_session.contentview.update(cv.name, {'details.name': gen_string('alpha')})
        # Cannot publish content view
        with pytest.raises(NavigationTriesExceeded) as context:
            custom_session.contentview.publish(cv.name)
        assert 'failed to reach [Publish]' in str(context.value)
    with session:
        result = session.contentview.publish(cv.name)
        assert result['Version'] == VERSION
    with Session(test_name, user=user_login, password=user_password) as session:
        # Cannot create content view
        with pytest.raises(NoSuchElementException) as context:
            session.contentview.create({'name': gen_string('alpha')})
        assert 'Could not find an element' in str(context.value)
        # Cannot create activation key
        with pytest.raises(NavigationTriesExceeded) as context:
            session.activationkey.create({'name': gen_string('alpha')})
        assert 'failed to reach [All]' in str(context.value)
        # Cannot create product
        with pytest.raises(NavigationTriesExceeded) as context:
            session.product.create({'name': gen_string('alpha')})
        assert 'failed to reach [All]' in str(context.value)
        # Cannot create host collection
        with pytest.raises(NavigationTriesExceeded) as context:
            session.hostcollection.create({'name': gen_string('alpha')})
        assert 'failed to reach [All]' in str(context.value)
        # Cannot create discovery repo
        with pytest.raises(NavigationTriesExceeded) as context:
            session.product.discover_repo(
                {
                    'repo_type': 'Yum Repositories',
                    'url': settings.repos.repo_discovery.url,
                    'discovered_repos.repos': repo_name,
                    'create_repo.product_type': 'Existing Product',
                    'create_repo.product_content.product_name': gen_string('alpha'),
                }
            )
        assert 'failed to reach [All]' in str(context.value)
        # Cannot promote content view
        with pytest.raises(NavigationTriesExceeded) as context:
            session.contentview.promote(cv.name, VERSION, lce.name)
        assert 'failed to reach [Promote]' in str(context.value)
        # Cannot delete content view
        with pytest.raises(NavigationTriesExceeded) as context:
            session.contentview.delete(cv.name)
        assert 'failed to reach [Delete]' in str(context.value)


@pytest.mark.tier2
def test_negative_non_readonly_user_actions(module_org, test_name):
    """Attempt to view content views

    :id: 9cbc661a-dbe3-4b88-af27-4cf7b9544074

    :setup: create a user with the Content View without the content views
        read role

    :expectedresults: the user cannot access content views web resources

    :CaseLevel: Integration

    :CaseImportance: High
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    # create a role with all content views permissions except
    # view_content_views
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    cv = entities.ContentView(organization=module_org).create()
    role = entities.Role().create()
    create_role_permissions(
        role,
        {
            'Katello::ContentView': [
                'create_content_views',
                'edit_content_views',
                'destroy_content_views',
                'publish_content_views',
                'promote_or_remove_content_views',
            ]
        },
    )
    create_role_permissions(
        role,
        {
            'Katello::KTEnvironment': [
                'promote_or_remove_content_views_to_environments',
                'view_lifecycle_environments',
            ]
        },
        search=f'name = {ENVIRONMENT} or name = {lce.name}',
    )
    # create a user and assign the above created role
    entities.User(
        default_organization=module_org,
        organization=[module_org],
        role=[role],
        login=user_login,
        password=user_password,
    ).create()
    # login as the user created above
    with Session(test_name, user=user_login, password=user_password) as session:
        with pytest.raises(NavigationTriesExceeded):
            session.user.create(
                {
                    'user.login': gen_string('alpha'),
                    'user.auth': 'INTERNAL',
                    'user.password': gen_string('alpha'),
                    'user.confirm': gen_string('alpha'),
                }
            )
        with pytest.raises(NavigationTriesExceeded) as context:
            session.contentview.search(cv.name)
        assert 'Navigation failed to reach [All]' in str(context.value)


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_conservative_solve_dependencies(session, module_org):
    """Performing solve dependencies on a package that is required by another
    package.  Then performing solve dependencies on a root package with
    its corresponding dependency.

    :id: bffd50f3-77e4-492f-a0ac-09dfb95b1987

    :setup:
        1. Turn dependency solving to conservative.
        2. Create and sync custom repo.
        3. Create cv and add custom repo.
        4. Create exclusion filter and exclude a package that is required
            by another package (cockateel).
        5. Publish CV
        6. Check rpm package list for that version and make sure it's in the
            list.
        7. Create exclusion filter for a root package (duck) along with
            package from above.
        8. Republish and check rpm package list for new version and make
            sure they are NOT in the list.

    :expectedresults: In step 6, 'cockateel' should be in the list.
        In step 8, 'duck' and 'cockateel' should NOT be in the list.

    :CaseImportance: High
    """
    property_name = 'dependency_solving_algorithm'
    param_value = 'conservative'
    cv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package1_name = 'duck'
    package2_name = 'cockateel'
    arch = 'noarch'
    create_sync_custom_repo(module_org.id, repo_name=repo_name, repo_url=settings.repos.yum_0.url)
    with session:
        session.settings.update(f'name = {property_name}', param_value)
        session.contentview.create({'name': cv_name, 'solve_dependencies': True})
        session.contentview.add_yum_repo(cv_name, repo_name)
        filter_name = gen_string('alpha')
        session.contentviewfilter.create(
            cv_name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['exclude'],
            },
        )
        session.contentviewfilter.add_package_rule(
            cv_name, filter_name, package2_name, arch, ('All Versions')
        )
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        package = session.contentview.search_version_package(
            cv_name, VERSION, f'name = "{package2_name}"'
        )
        assert len(package) == 1
        assert package[0]['Name'] == package2_name
        package = session.contentview.search_version_package(
            cv_name, VERSION, f'name = "{package1_name}"'
        )
        assert package[0]['Name'] == package1_name
        session.contentviewfilter.add_package_rule(
            cv_name, filter_name, package1_name, arch, ('All Versions')
        )
        result = session.contentview.publish(cv_name)
        assert result['Version'] == 'Version 2.0'
        for package_names in ['duck', 'cockateel']:
            package = session.contentview.search_version_package(
                cv_name, 'Version 2.0', f'name = "{package_names}"'
            )
            assert not package[0]['Name']


@pytest.mark.tier2
def test_positive_conservative_dep_solving_with_multiversion_packages(session, module_org):
    """Performing solve dependencies on a package with multiple versions that is required
    by another package.

    :id: f1fb2f2e-6d63-4705-b0cd-6697fed2b6e9

    :setup:
        1. Turn dependency solving to conservative.
        2. Create and sync custom repo.
        3. Create cv and add custom repo.
        4. Create exclusion filter and exclude a package (walrus) that has multiple versions that
            is required by another package.
        5. Publish CV
        6. Check rpm package list for that version
        7. Repeat steps 4 - 7 but exclude higher version

    :expectedresults: In step 6, the older version of the package should be filtered out while the
        newest version is still in the list.  In step 7, the new version is filtered out while the
        old version is still in the list.

    :CaseImportance: High
    """
    property_name = 'dependency_solving_algorithm'
    param_value = 'conservative'
    cv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package_name = 'walrus'
    arch = 'noarch'
    create_sync_custom_repo(module_org.id, repo_name=repo_name, repo_url=settings.repos.yum_0.url)
    with session:
        session.settings.update(f'name = {property_name}', param_value)
        session.contentview.create({'name': cv_name, 'solve_dependencies': True})
        session.contentview.add_yum_repo(cv_name, repo_name)
        filter_name = gen_string('alpha')
        session.contentviewfilter.create(
            cv_name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['exclude'],
            },
        )
        session.contentviewfilter.add_package_rule(
            cv_name, filter_name, package_name, arch, ('All Versions')
        )
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        package = session.contentview.search_version_package(
            cv_name, VERSION, f'name = "{package_name}"'
        )
        assert len(package) == 1
        assert package[0]['Name'] == package_name
        assert package[0]['Version'] == '5.21'
        session.contentviewfilter.update_package_rule(
            cv_name, filter_name, package_name, {'Version': ('Equal To', '5.21')}
        )
        session.contentview.publish(cv_name)
        package = session.contentview.search_version_package(
            cv_name, 'Version 2.0', f'name = "{package_name}"'
        )
        assert len(package) == 1
        assert package[0]['Name'] == package_name
        assert package[0]['Version'] == '0.71'


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_depsolve_with_module_errata(session, module_org):
    """Allowing users to filter module streams in content views.  This test case does not test
    against RHEL8 repos because it is known that RHEL8 filtering with depsolving creates
    inconsistent results.  The custom repo used in this test case has consistent results based
    on filtering and thus why it's used.

    :id: 59f9ed09-fe32-4e52-9fb9-6fa2d22eeb26

    :setup:
        1. Create custom repo and sync
        2. Add custom repos to a CV and turn depsolving = true.
        3. Create an inclusion filter for module stream.
        4. Create an exclusion filter for packages for all packages.
        5. Publish CV

    :expectedresults: Content view result should have 4 packages, 1 errata,
        and 1 Module Streams associated with the CV

    :CaseImportance: High
    """
    cv_name = gen_string('alpha')
    repo_name_1 = gen_string('alpha')
    repo_name_2 = gen_string('alpha')
    include_filter_name = gen_string('alpha')
    exclude_filter_name = gen_string('alpha')
    all_packages = '*'
    ms_name = 'walrus'
    ms_version = '0.71'
    rpm_pack = ['shark', 'stork', 'walrus', 'whale']
    mod_stream = 'walrus'
    create_sync_custom_repo(
        module_org.id, repo_name=repo_name_1, repo_url=settings.repos.yum_10.url
    )
    create_sync_custom_repo(
        module_org.id, repo_name=repo_name_2, repo_url=settings.repos.yum_11.url
    )
    content = '4 Packages 1 Errata ( 1 0 0 ) 1 Module Streams'
    with session:
        session.contentview.create({'name': cv_name, 'solve_dependencies': True})
        session.contentview.add_yum_repo(cv_name, repo_name_1)
        session.contentview.add_yum_repo(cv_name, repo_name_2)
        session.contentviewfilter.create(
            cv_name,
            {
                'name': include_filter_name,
                'content_type': FILTER_CONTENT_TYPE['modulemd'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        session.contentviewfilter.add_module_stream(
            cv_name, include_filter_name, f'name = {ms_name} and stream = {ms_version}'
        )
        session.contentviewfilter.create(
            cv_name,
            {
                'name': exclude_filter_name,
                'content_type': FILTER_CONTENT_TYPE['package'],
                'inclusion_type': FILTER_TYPE['exclude'],
            },
        )
        session.contentviewfilter.add_package_rule(
            cv_name, exclude_filter_name, all_packages, '', ('All Versions')
        )
        result = session.contentview.publish(cv_name)
        assert result['Content'] == content
        result = session.contentview.read_version(cv_name, VERSION)
        assert len(result['rpm_packages']['table']) == 4
        assert len(result['module_streams']['table']) == 1
        assert len(result['errata']['table']) == 1
        for items in result['rpm_packages']['table']:
            assert items['Name'] in rpm_pack
        assert result['module_streams']['table'][0]['Name'] == mod_stream
        assert result['errata']['table'][0]['Errata ID'] == settings.repos.yum_10.errata[0]


@pytest.mark.tier2
def test_positive_filter_by_pkg_group_name(session, module_org, default_sat):
    """Publish a filtered version of a Content View, filtering on the package group's name.

    :id: c7021f46-0168-44f7-a863-4aa34533efdb

    :expectedresults: Published Content View's contents is filtered
                based on package group.

    :CaseImportance: Medium
    """

    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package_group = 'birds'
    expected_packages = [('cockateel'), ('duck'), ('penguin'), ('stork')]
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = default_sat.api.Repository(name=repo_name).search(
        query={'organization_id': module_org.id}
    )[0]
    cv = default_sat.api.ContentView(organization=module_org, repository=[repo]).create()
    with session:
        session.contentviewfilter.create(
            cv.name,
            {
                'name': filter_name,
                'content_type': FILTER_CONTENT_TYPE['package group'],
                'inclusion_type': FILTER_TYPE['include'],
            },
        )
        session.contentviewfilter.add_package_group(cv.name, filter_name, package_group)
        cvf = session.contentviewfilter.read(cv.name, filter_name)
        assert cvf['content_tabs']['assigned'][0]['Name'] == package_group
        # Publish CV and check filter worked
        session.contentview.publish(cv.name)
        result = session.contentview.read_version(cv.name, VERSION)
        # Assert only the expected packages are present
        assert expected_packages == [pkg['Name'] for pkg in result['rpm_packages']['table']]


@pytest.mark.tier3
def test_positive_inc_update_should_not_fail(session, module_org):
    """Incremental update after removing a package should not give a 400 error code

    :BZ: 2041497

    :id: 1d78db8f-53cc-4f00-9fea-d871c2f53d03

    :setup:
        1. Create custom repo and sync
        2. Delete some packages from the repo (bear in this case)
        3. Create a cv, add the repo, and publish it
        4. Re-sync the repo to get hte deleted RPMs back
        5. Perform incremental update to add back the repo to the cv

    :customerscenario: true

    :expectedresults: Incremental update is successful

    :CaseImportance: High
    """
    package1_name = 'bear'
    product = entities.Product(organization=module_org).create()
    yum_repo_name = gen_string('alpha')
    # Creates custom yum repository
    yum_repo = entities.Repository(
        name=yum_repo_name,
        url=settings.repos.yum_1.url,
        content_type=REPO_TYPE['yum'],
        product=product,
    ).create()
    yum_repo.sync()
    # remove 'bear' package
    package_id = yum_repo.packages()['results'][0]['id']
    yum_repo.remove_content(data={'ids': [package_id]})
    assert yum_repo.packages()['total'] == 31
    cv = entities.ContentView(organization=module_org, repository=[yum_repo]).create()
    cv.publish()
    cvvs = entities.ContentView(id=cv.id).read().version
    assert len(cvvs) == 1
    yum_repo.sync()
    assert yum_repo.packages()['total'] == 32
    cvv = cvvs[0].read()
    result = ContentView.version_incremental_update(
        {'content-view-version-id': cvv.id, 'errata-ids': settings.repos.yum_1.errata[0]}
    )
    result = [line.strip() for line_dict in result for line in line_dict.values()]
    assert result[2] == FAKE_0_CUSTOM_PACKAGE
    with session:
        cvv = entities.ContentView(id=cv.id).read().version[1].read()
        assert cvv.version == '1.1'
        packages = session.contentview.search_version_package(
            cv.name, 'Version 1.1', f'name= "{package1_name}"'
        )
        assert packages[0]['Name'] == package1_name
