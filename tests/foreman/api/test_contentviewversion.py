"""Unit tests for the ``content_view_versions`` paths.

:Requirement: Contentviewversion

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ContentViews

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import CONTAINER_REGISTRY_HUB
from robottelo.constants import DEFAULT_CV
from robottelo.constants import ENVIRONMENT
from robottelo.constants import DataFile


@pytest.fixture(scope='module')
def module_lce_cv(module_org):
    """Create some entities for all tests."""
    lce1 = entities.LifecycleEnvironment(organization=module_org).create()
    lce2 = entities.LifecycleEnvironment(organization=module_org, prior=lce1).create()
    default_cv = entities.ContentView(organization=module_org, name=DEFAULT_CV).search()
    default_cvv = default_cv[0].version[0]
    return lce1, lce2, default_cvv


# Tests for content view version creation.


@pytest.mark.tier2
def test_positive_create(module_cv):
    """Create a content view version.

    :id: 627c84b3-e3f1-416c-a09b-5d2200d6429f

    :expectedresults: Content View Version is created.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    # Fetch content view for latest information
    cv = module_cv.read()
    # No versions should be available yet
    assert len(cv.version) == 0

    # Publish existing content view
    cv.publish()
    # Fetch it again
    cv = cv.read()
    assert len(cv.version) > 0


@pytest.mark.tier2
def test_negative_create(module_org):
    """Attempt to create content view version using the 'Default Content View'.

    :id: 0afd49c6-f3a4-403e-9929-849f51ffa922

    :expectedresults: Content View Version is not created

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    # The default content view cannot be published
    cv = entities.ContentView(organization=module_org.id, name=DEFAULT_CV).search()
    # There should be only 1 record returned
    assert len(cv) == 1
    with pytest.raises(HTTPError):
        cv[0].publish()


# Tests for content view version promotion.


@pytest.mark.tier2
def test_positive_promote_valid_environment(module_lce_cv, module_org):
    """Promote a content view version to 'next in sequence lifecycle environment.

    :id: f205ca06-8ab5-4546-83bd-deac4363d487

    :expectedresults: Promotion succeeds.

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    # Create a new content view...
    cv = entities.ContentView(organization=module_org).create()
    # ... and promote it.
    cv.publish()
    # Refresh the entity
    cv = cv.read()
    # Check that we have a new version
    assert len(cv.version) == 1
    version = cv.version[0].read()
    # Assert that content view version is found in 1 lifecycle
    # environments (i.e. 'Library')
    assert len(version.environment) == 1
    # Promote it to the next 'in sequence' lifecycle environment
    promote(version, module_lce_cv[0].id)
    # Assert that content view version is found in 2 lifecycle
    # environments.
    version = version.read()
    assert len(version.environment) == 2


@pytest.mark.tier2
def test_positive_promote_out_of_sequence_environment(module_org, module_lce_cv):
    """Promote a content view version to a lifecycle environment
    that is 'out of sequence'.

    :id: e88405de-843d-4279-9d81-cedaab7c23cf

    :expectedresults: The promotion succeeds.

    :CaseLevel: Integration
    """
    # Create a new content view...
    cv = entities.ContentView(organization=module_org).create()
    # ... and publish it.
    cv.publish()
    # Refresh the entity
    cv = cv.read()
    # Check that we have a new version
    assert len(cv.version) == 1
    version = cv.version[0].read()
    # The immediate lifecycle is lce1, not lce2
    promote(version, module_lce_cv[1].id, force=True)
    # Assert that content view version is found in 2 lifecycle
    # environments.
    version = version.read()
    assert len(version.environment) == 2


@pytest.mark.tier2
def test_negative_promote_valid_environment(module_lce_cv):
    """Attempt to promote the default content view version.

    :id: cd4f3c3d-93c5-425f-bc3b-d1ac17696a4a

    :expectedresults: The promotion fails.

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    lce1, _, default_cvv = module_lce_cv
    with pytest.raises(HTTPError):
        promote(default_cvv, lce1.id)


@pytest.mark.tier2
def test_negative_promote_out_of_sequence_environment(module_lce_cv, module_org):
    """Attempt to promote a content view version to a Lifecycle environment
    that is 'out of sequence'.

    :id: 621d1bb6-92c6-4209-8369-6ea14a4c8a01

    :expectedresults: The promotion fails.

    :CaseLevel: Integration
    """
    # Create a new content view...
    cv = entities.ContentView(organization=module_org).create()
    # ... and publish it.
    cv.publish()
    # Refresh the entity
    cv = cv.read()
    # Check that we have a new version
    assert len(cv.version) == 1
    version = cv.version[0].read()
    # The immediate lifecycle is lce1, not lce2
    with pytest.raises(HTTPError):
        promote(version, module_lce_cv[1].id)


# Tests for content view version promotion.


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_delete(module_org, module_product):
    """Create content view and publish it. After that try to
    disassociate content view from 'Library' environment through
    'delete_from_environment' command and delete content view version from
    that content view. Add repository and gpg key to initial content view
    for better coverage

    :id: 066dec47-c942-4c01-8956-359c8b23a6d4

    :expectedresults: Content version deleted successfully

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    key_content = DataFile.ZOO_CUSTOM_GPG_KEY.read_bytes()
    gpgkey = entities.GPGKey(content=key_content, organization=module_org).create()
    # Creates new repository with GPGKey
    repo = entities.Repository(
        gpg_key=gpgkey, product=module_product, url=settings.repos.yum_1.url
    ).create()
    # sync repository
    repo.sync()
    # Create content view
    content_view = entities.ContentView(organization=module_org).create()
    # Associate repository to new content view
    content_view.repository = [repo]
    content_view = content_view.update(['repository'])
    # Publish content view
    content_view.publish()
    content_view = content_view.read()
    # Get published content-view version id
    assert len(content_view.version) == 1
    cvv = content_view.version[0].read()
    assert len(cvv.environment) == 1
    # Delete the content-view version from selected env
    content_view.delete_from_environment(cvv.environment[0].id)
    # Delete the version
    content_view.version[0].delete()
    # Make sure that content view version is really removed
    assert len(content_view.read().version) == 0


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_delete_non_default(module_org):
    """Create content view and publish and promote it to new
    environment. After that try to disassociate content view from 'Library'
    and one more non-default environment through 'delete_from_environment'
    command and delete content view version from that content view.

    :id: 95bb973c-ebec-4a72-a1b6-ad28b66bd11b

    :expectedresults: Content view version deleted successfully

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    content_view = entities.ContentView(organization=module_org).create()
    # Publish content view
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    assert len(content_view.version[0].read().environment) == 1
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    promote(content_view.version[0], lce.id)
    cvv = content_view.version[0].read()
    assert len(cvv.environment) == 2
    # Delete the content-view version from selected environments
    for env in reversed(cvv.environment):
        content_view.delete_from_environment(env.id)
    content_view.version[0].delete()
    # Make sure that content view version is really removed
    assert len(content_view.read().version) == 0


@pytest.mark.upgrade
@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_delete_composite_version(module_org):
    """Create composite content view and publish it. After that try to
    disassociate content view from 'Library' environment through
    'delete_from_environment' command and delete content view version from
    that content view. Add repository to initial content view
    for better coverage.

    :id: b5bb547e-0174-464c-b974-0254d372cdd6

    :expectedresults: Content version deleted successfully

    :CaseLevel: Integration

    :BZ: 1276479
    """
    # Create product with repository and publish it
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(product=product, url=settings.repos.yum_1.url).create()
    repo.sync()
    # Create and publish content views
    content_view = entities.ContentView(organization=module_org, repository=[repo]).create()
    content_view.publish()
    # Create and publish composite content view
    composite_cv = entities.ContentView(
        organization=module_org, composite=True, component=[content_view.read().version[0]]
    ).create()
    composite_cv.publish()
    composite_cv = composite_cv.read()
    # Get published content-view version id
    assert len(composite_cv.version) == 1
    cvv = composite_cv.version[0].read()
    assert len(cvv.environment) == 1
    # Delete the content-view version from selected env
    composite_cv.delete_from_environment(cvv.environment[0].id)
    # Delete the version
    composite_cv.version[0].delete()
    # Make sure that content view version is really removed
    assert len(composite_cv.read().version) == 0


@pytest.mark.tier2
def test_negative_delete(module_org):
    """Create content view and publish it. Try to delete content
    view version while content view is still associated with lifecycle
    environment

    :id: 21c35aae-2f9c-4679-b3ba-7cd9182bd880

    :expectedresults: Content view version is not deleted

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    content_view = entities.ContentView(organization=module_org).create()
    # Publish content view
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    with pytest.raises(HTTPError):
        content_view.version[0].delete()
    # Make sure that content view version is still present
    assert len(content_view.read().version) == 1


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_remove_renamed_cv_version_from_default_env(module_org):
    """Remove version of renamed content view from Library environment

    :id: 7d5961d0-6a9a-4610-979e-cbc4ddbc50ca

    :Steps:

        1. Create a content view
        2. Add a yum repo to the content view
        3. Publish the content view
        4. Rename the content view
        5. remove the published version from Library environment

    :expectedresults: content view version is removed from Library
        environment

    :CaseLevel: Integration
    """
    new_name = gen_string('alpha')
    # create yum product and repo
    product = entities.Product(organization=module_org).create()
    yum_repo = entities.Repository(url=settings.repos.yum_1.url, product=product).create()
    yum_repo.sync()
    # create a content view and add the yum repo to it
    content_view = entities.ContentView(organization=module_org).create()
    content_view.repository = [yum_repo]
    content_view = content_view.update(['repository'])
    # publish the content view
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    content_view_version = content_view.version[0].read()
    assert len(content_view_version.environment) == 1
    lce_library = entities.LifecycleEnvironment(id=content_view_version.environment[0].id).read()
    # ensure that the content view version is promoted to the Library
    # lifecycle environment
    assert lce_library.name == ENVIRONMENT
    # rename the content view
    content_view.name = new_name
    content_view.update(['name'])
    assert content_view.name == new_name
    # delete the content view version from Library environment
    content_view.delete_from_environment(lce_library.id)
    # assert that the content view version does not exist in Library
    # environment
    assert len(content_view_version.read().environment) == 0


@pytest.mark.tier2
def test_positive_remove_qe_promoted_cv_version_from_default_env(module_org):
    """Remove QE promoted content view version from Library environment

    :id: c7795762-93bd-419c-ac49-d10dc26b842b

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
    """
    lce_dev = entities.LifecycleEnvironment(organization=module_org).create()
    lce_qe = entities.LifecycleEnvironment(organization=module_org, prior=lce_dev).create()
    product = entities.Product(organization=module_org).create()
    docker_repo = entities.Repository(
        content_type='docker',
        docker_upstream_name='busybox',
        product=product,
        url=CONTAINER_REGISTRY_HUB,
    ).create()
    docker_repo.sync()
    # create a content view and add to it the docker repo
    content_view = entities.ContentView(organization=module_org).create()
    content_view.repository = [docker_repo]
    content_view = content_view.update(['repository'])
    # publish the content view
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    content_view_version = content_view.version[0].read()
    assert len(content_view_version.environment) == 1
    lce_library = entities.LifecycleEnvironment(id=content_view_version.environment[0].id).read()
    assert lce_library.name == ENVIRONMENT
    # promote content view version to DEV and QE lifecycle environments
    for lce in [lce_dev, lce_qe]:
        promote(content_view_version, lce.id)
    assert {lce_library.id, lce_dev.id, lce_qe.id} == {
        lce.id for lce in content_view_version.read().environment
    }
    # remove the content view version from Library environment
    content_view.delete_from_environment(lce_library.id)
    # assert that the content view version does not exist in Library
    # environment
    assert {lce_dev.id, lce_qe.id} == {lce.id for lce in content_view_version.read().environment}


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_remove_prod_promoted_cv_version_from_default_env(module_org):
    """Remove PROD promoted content view version from Library environment

    :id: 24911876-7c2a-4a12-a3aa-98051dfda29d

    :Steps:

        1. Create a content view
        2. Add yum repositories and docker repositories to CV
        3. Publish content view
        4. Promote the content view version to multiple environments
            Library -> DEV -> QE -> PROD
        5. remove the content view version from Library environment

    :expectedresults: Content view version exist only in DEV, QE, PROD and
        not in Library

    :CaseLevel: Integration
    """
    lce_dev = entities.LifecycleEnvironment(organization=module_org).create()
    lce_qe = entities.LifecycleEnvironment(organization=module_org, prior=lce_dev).create()
    lce_prod = entities.LifecycleEnvironment(organization=module_org, prior=lce_qe).create()
    product = entities.Product(organization=module_org).create()
    yum_repo = entities.Repository(url=settings.repos.yum_1.url, product=product).create()
    yum_repo.sync()
    docker_repo = entities.Repository(
        content_type='docker',
        docker_upstream_name='busybox',
        product=product,
        url=CONTAINER_REGISTRY_HUB,
    ).create()
    docker_repo.sync()
    # create a content view and add to it the yum and docker repos
    content_view = entities.ContentView(organization=module_org).create()
    content_view.repository = [yum_repo, docker_repo]
    content_view = content_view.update(['repository'])
    # publish the content view
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    content_view_version = content_view.version[0].read()
    assert len(content_view_version.environment) == 1
    lce_library = entities.LifecycleEnvironment(id=content_view_version.environment[0].id).read()
    assert lce_library.name == ENVIRONMENT
    # promote content view version to DEV QE PROD lifecycle environments
    for lce in [lce_dev, lce_qe, lce_prod]:
        promote(content_view_version, lce.id)
    assert {lce_library.id, lce_dev.id, lce_qe.id, lce_prod.id} == {
        lce.id for lce in content_view_version.read().environment
    }
    # remove the content view version from Library environment
    content_view.delete_from_environment(lce_library.id)
    # assert that the content view version exists only in DEV QE PROD and
    # not in Library environment
    assert {lce_dev.id, lce_qe.id, lce_prod.id} == {
        lce.id for lce in content_view_version.read().environment
    }


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_remove_cv_version_from_env(module_org):
    """Remove promoted content view version from environment

    :id: 17cf18bf-09d5-4641-b0e0-c50e628fa6c8

    :Steps:

        1. Create a content view
        2. Add a yum repo and a docker repo to the content view
        3. Publish the content view
        4. Promote the content view version to multiple environments
           Library -> DEV -> QE -> STAGE -> PROD
        5. remove the content view version from PROD environment
        6. Assert: content view version exists only in Library, DEV, QE,
           STAGE and not in PROD
        7. Promote again from STAGE -> PROD

    :expectedresults: Content view version exist in Library, DEV, QE,
        STAGE, PROD

    :CaseLevel: Integration
    """
    lce_dev = entities.LifecycleEnvironment(organization=module_org).create()
    lce_qe = entities.LifecycleEnvironment(organization=module_org, prior=lce_dev).create()
    lce_stage = entities.LifecycleEnvironment(organization=module_org, prior=lce_qe).create()
    lce_prod = entities.LifecycleEnvironment(organization=module_org, prior=lce_stage).create()
    product = entities.Product(organization=module_org).create()
    yum_repo = entities.Repository(url=settings.repos.yum_1.url, product=product).create()
    yum_repo.sync()
    # docker repo
    docker_repo = entities.Repository(
        content_type='docker',
        docker_upstream_name='busybox',
        product=product,
        url=CONTAINER_REGISTRY_HUB,
    ).create()
    docker_repo.sync()
    # create a content view and add the yum and docker repo to it
    content_view = entities.ContentView(organization=module_org).create()
    content_view.repository = [yum_repo, docker_repo]
    content_view = content_view.update(['repository'])
    # publish the content view
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    content_view_version = content_view.version[0].read()
    assert len(content_view_version.environment) == 1
    lce_library = entities.LifecycleEnvironment(id=content_view_version.environment[0].id).read()
    assert lce_library.name == ENVIRONMENT
    # promote content view version to DEV QE STAGE PROD lifecycle
    # environments
    for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
        promote(content_view_version, lce.id)
    assert {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id, lce_prod.id} == {
        lce.id for lce in content_view_version.read().environment
    }
    # remove the content view version from Library environment
    content_view.delete_from_environment(lce_prod.id)
    # assert that the content view version exists only in Library DEV QE
    # STAGE and not in PROD environment
    assert {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id} == {
        lce.id for lce in content_view_version.read().environment
    }
    # promote content view version to PROD environment again
    promote(content_view_version, lce_prod.id)
    assert {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id, lce_prod.id} == {
        lce.id for lce in content_view_version.read().environment
    }


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_remove_cv_version_from_multi_env(module_org):
    """Remove promoted content view version from multiple environments

    :id: 18b86a68-8e6a-43ea-b95e-188fba125a26

    :Steps:

        1. Create a content view
        2. Add a yum repo and a docker repo to the content view
        3. Publish the content view
        4. Promote the content view version to multiple environments
           Library -> DEV -> QE -> STAGE -> PROD
        5. Remove content view version from QE, STAGE and PROD

    :expectedresults: Content view version exists only in Library, DEV

    :CaseLevel: Integration

    :CaseImportance: Low
    """
    lce_dev = entities.LifecycleEnvironment(organization=module_org).create()
    lce_qe = entities.LifecycleEnvironment(organization=module_org, prior=lce_dev).create()
    lce_stage = entities.LifecycleEnvironment(organization=module_org, prior=lce_qe).create()
    lce_prod = entities.LifecycleEnvironment(organization=module_org, prior=lce_stage).create()
    product = entities.Product(organization=module_org).create()
    yum_repo = entities.Repository(url=settings.repos.yum_1.url, product=product).create()
    yum_repo.sync()
    docker_repo = entities.Repository(
        content_type='docker',
        docker_upstream_name='busybox',
        product=product,
        url=CONTAINER_REGISTRY_HUB,
    ).create()
    docker_repo.sync()
    # create a content view and add the yum repo to it
    content_view = entities.ContentView(organization=module_org).create()
    content_view.repository = [yum_repo, docker_repo]
    content_view = content_view.update(['repository'])
    # publish the content view
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    content_view_version = content_view.version[0].read()
    assert len(content_view_version.environment) == 1
    lce_library = entities.LifecycleEnvironment(id=content_view_version.environment[0].id).read()
    assert lce_library.name == ENVIRONMENT
    # promote content view version to DEV QE STAGE PROD lifecycle
    # environments
    for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
        promote(content_view_version, lce.id)
    assert {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id, lce_prod.id} == {
        lce.id for lce in content_view_version.read().environment
    }
    # remove the content view version from QE STAGE and PROD environments
    for lce in [lce_qe, lce_stage, lce_prod]:
        content_view.delete_from_environment(lce.id)
    # assert that the content view version exists only in Library and DEV
    # environments
    assert {lce_library.id, lce_dev.id} == {
        lce.id for lce in content_view_version.read().environment
    }


@pytest.mark.upgrade
@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_delete_cv_promoted_to_multi_env(module_org):
    """Delete published content view with version promoted to multiple
     environments

    :id: c164bd97-e710-4a5a-9c9f-657e6bed804b

    :Steps:

        1. Create a content view
        2. Add a yum repo and a docker repo to the content view
        3. Publish the content view
        4. Promote the content view to multiple environment
           Library -> DEV -> QE -> STAGE -> PROD
        5. Delete the content view, this should delete the content with all
           it's published/promoted versions from all environments

    :expectedresults: The content view doesn't exists

    :CaseLevel: Integration

    :CaseImportance: Critical
    """
    lce_dev = entities.LifecycleEnvironment(organization=module_org).create()
    lce_qe = entities.LifecycleEnvironment(organization=module_org, prior=lce_dev).create()
    lce_stage = entities.LifecycleEnvironment(organization=module_org, prior=lce_qe).create()
    lce_prod = entities.LifecycleEnvironment(organization=module_org, prior=lce_stage).create()
    product = entities.Product(organization=module_org).create()
    yum_repo = entities.Repository(url=settings.repos.yum_1.url, product=product).create()
    yum_repo.sync()
    docker_repo = entities.Repository(
        content_type='docker',
        docker_upstream_name='busybox',
        product=product,
        url=CONTAINER_REGISTRY_HUB,
    ).create()
    docker_repo.sync()
    # create a content view and add the yum repo to it
    content_view = entities.ContentView(organization=module_org).create()
    content_view.repository = [yum_repo, docker_repo]
    content_view = content_view.update(['repository'])
    # publish the content view
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    content_view_version = content_view.version[0].read()
    assert len(content_view_version.environment) == 1
    lce_library = entities.LifecycleEnvironment(id=content_view_version.environment[0].id).read()
    assert lce_library.name == ENVIRONMENT
    # promote content view version to DEV QE STAGE PROD lifecycle
    # environments
    for lce in [lce_dev, lce_qe, lce_stage, lce_prod]:
        promote(content_view_version, lce.id)
    content_view_version = content_view_version.read()
    assert {lce_library.id, lce_dev.id, lce_qe.id, lce_stage.id, lce_prod.id} == {
        lce.id for lce in content_view_version.environment
    }
    # remove content view version from all lifecycle environments
    for lce in content_view_version.environment:
        content_view.delete_from_environment(lce.id)
    # delete the content view
    content_view.delete()
    with pytest.raises(HTTPError):
        content_view.read()


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_remove_cv_version_from_env_with_host_registered():
    """Remove promoted content view version from environment that is used
    in association of an Activation key and content-host registration.

    :id: a5b9ba8b-80e6-4435-bc0a-041b3fda227c

    :Steps:

        1. Create a content view cv1
        2. Add a yum repo to the content view
        3. Publish the content view
        4. Promote the content view to multiple environment Library -> DEV
           -> QE
        5. Create an Activation key with the QE environment
        6. Register a content-host using the Activation key
        7. Remove the content view cv1 version from QE environment.  Note:
           prior to removing, replace the current QE environment of cv1 by DEV
           and content view cv1 for Content-host and for Activation key.
        8. Refresh content-host subscription

    :expectedresults:

        1. Activation key exists
        2. Content-host exists
        3. QE environment of cv1 was replaced by DEV environment of cv1 in
           activation key
        4. QE environment of cv1 was replaced by DEV environment of cv1 in
           content-host
        5. At content-host some package from cv1 is installable

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


@pytest.mark.upgrade
@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_delete_cv_multi_env_promoted_with_host_registered():
    """Delete published content view with version promoted to multiple
     environments, with one of the environments used in association of an
     Activation key and content-host registration.

    :id: 10699af9-617e-4930-9c80-2827a0ba52eb

    :Steps:

        1. Create two content views, cv1 and cv2
        2. Add a yum repo to both content views
        3. Publish the content views
        4. Promote the content views to multiple environment Library -> DEV
           -> QE
        5. Create an Activation key with the QE environment and cv1
        6. Register a content-host using the Activation key
        7. Delete the content view cv1.
           Note: prior to deleting, replace the current QE environment of cv1
           by DEV and content view cv2 for Content-host and for Activation
           key.
        8. Refresh content-host subscription

    :expectedresults:

        1. The content view cv1 doesn't exist
        2. Activation key exists
        3. Content-host exists
        4. QE environment of cv1 was replaced by DEV environment of cv2 in
           activation key
        5. QE environment of cv1 was replaced by DEV environment of cv2 in
           content-host
        6. At content-host some package from cv2 is installable

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_remove_cv_version_from_multi_env_capsule_scenario():
    """Remove promoted content view version from multiple environments,
    with satellite module_lce_cv to use capsule

    :id: 1e8a8e64-eec8-49e0-b121-919c53f416d2

    :Steps:

        1. Create a content view
        2. module_lce_cv satellite to use a capsule and to sync all lifecycle
           environments
        3. Add a yum repo and a docker repo to the content
           view
        4. Publish the content view
        5. Promote the content view to multiple environment Library -> DEV
           -> QE -> PROD
        6. Make sure the capsule is updated (content synchronization can be
           applied)
        7. Disconnect the capsule
        8. Remove the content view version from Library and DEV
           environments and assert successful completion
        9. Bring the capsule back online and assert that the task is
           completed in capsule
        10. Make sure the capsule is updated (content synchronization can
            be applied)

    :expectedresults: content view version in capsule is removed from
        Library and DEV and exists only in QE and PROD

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
