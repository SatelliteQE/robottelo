"""Unit tests for the ``content_view_versions`` paths.

:Requirement: Contentviewversion

:CaseAutomation: Automated

:CaseComponent: ContentViews

:team: Phoenix-content

:CaseImportance: High

"""

import pytest
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_CV,
    DataFile,
)


@pytest.fixture(scope='module')
def module_lce_cv(module_org, module_target_sat):
    """Create some entities for all tests."""
    lce1 = module_target_sat.api.LifecycleEnvironment(organization=module_org).create()
    lce2 = module_target_sat.api.LifecycleEnvironment(organization=module_org, prior=lce1).create()
    default_cv = module_target_sat.api.ContentView(
        organization=module_org, name=DEFAULT_CV
    ).search()
    default_cvv = default_cv[0].version[0]
    return lce1, lce2, default_cvv


@pytest.mark.tier2
def test_positive_promote_out_of_sequence_environment(module_org, module_lce_cv, module_target_sat):
    """Promote a content view version to a lifecycle environment
    that is 'out of sequence'.

    :id: e88405de-843d-4279-9d81-cedaab7c23cf

    :expectedresults: The promotion succeeds.
    """
    # Create a new content view...
    cv = module_target_sat.api.ContentView(organization=module_org).create()
    # ... and publish it.
    cv.publish()
    # Refresh the entity
    cv = cv.read()
    # Check that we have a new version
    assert len(cv.version) == 1
    version = cv.version[0].read()
    # The immediate lifecycle is lce1, not lce2
    version.promote(data={'environment_ids': module_lce_cv[1].id, 'force': True})
    # Assert that content view version is found in 2 lifecycle
    # environments.
    version = version.read()
    assert len(version.environment) == 2


@pytest.mark.tier2
def test_negative_promote_valid_environment(module_lce_cv):
    """Attempt to promote the default content view version.

    :id: cd4f3c3d-93c5-425f-bc3b-d1ac17696a4a

    :expectedresults: The promotion fails.

    :CaseImportance: Low
    """
    lce1, _, default_cvv = module_lce_cv
    with pytest.raises(HTTPError):
        default_cvv.promote(data={'environment_ids': lce1.id, 'force': False})


@pytest.mark.tier2
def test_negative_promote_out_of_sequence_environment(module_lce_cv, module_org, module_target_sat):
    """Attempt to promote a content view version to a Lifecycle environment
    that is 'out of sequence'.

    :id: 621d1bb6-92c6-4209-8369-6ea14a4c8a01

    :expectedresults: The promotion fails.
    """
    # Create a new content view...
    cv = module_target_sat.api.ContentView(organization=module_org).create()
    # ... and publish it.
    cv.publish()
    # Refresh the entity
    cv = cv.read()
    # Check that we have a new version
    assert len(cv.version) == 1
    version = cv.version[0].read()
    # The immediate lifecycle is lce1, not lce2
    with pytest.raises(HTTPError):
        version.promote(data={'environment_ids': module_lce_cv[1].id, 'force': False})


# Tests for content view version promotion.


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_delete(module_org, module_product, module_target_sat):
    """Create content view and publish it. After that try to
    disassociate content view from 'Library' environment through
    'delete_from_environment' command and delete content view version from
    that content view. Add repository and gpg key to initial content view
    for better coverage

    :id: 066dec47-c942-4c01-8956-359c8b23a6d4

    :expectedresults: Content version deleted successfully

    :CaseImportance: Critical
    """
    key_content = DataFile.ZOO_CUSTOM_GPG_KEY.read_text()
    gpgkey = module_target_sat.api.GPGKey(content=key_content, organization=module_org).create()
    # Creates new repository with GPGKey
    repo = module_target_sat.api.Repository(
        gpg_key=gpgkey, product=module_product, url=settings.repos.yum_1.url
    ).create()
    # sync repository
    repo.sync()
    # Create content view
    content_view = module_target_sat.api.ContentView(organization=module_org).create()
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
def test_positive_delete_non_default(module_org, module_target_sat):
    """Create content view and publish and promote it to new
    environment. After that try to disassociate content view from 'Library'
    and one more non-default environment through 'delete_from_environment'
    command and delete content view version from that content view.

    :id: 95bb973c-ebec-4a72-a1b6-ad28b66bd11b

    :expectedresults: Content view version deleted successfully

    :CaseImportance: Critical
    """
    content_view = module_target_sat.api.ContentView(organization=module_org).create()
    # Publish content view
    content_view.publish()
    content_view = content_view.read()
    assert len(content_view.version) == 1
    assert len(content_view.version[0].read().environment) == 1
    lce = module_target_sat.api.LifecycleEnvironment(organization=module_org).create()
    content_view.version[0].promote(data={'environment_ids': lce.id, 'force': False})
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
def test_positive_delete_composite_version(module_org, module_target_sat):
    """Create composite content view and publish it. After that try to
    disassociate content view from 'Library' environment through
    'delete_from_environment' command and delete content view version from
    that content view. Add repository to initial content view
    for better coverage.

    :id: b5bb547e-0174-464c-b974-0254d372cdd6

    :expectedresults: Content version deleted successfully

    :BZ: 1276479
    """
    # Create product with repository and publish it
    product = module_target_sat.api.Product(organization=module_org).create()
    repo = module_target_sat.api.Repository(product=product, url=settings.repos.yum_1.url).create()
    repo.sync()
    # Create and publish content views
    content_view = module_target_sat.api.ContentView(
        organization=module_org, repository=[repo]
    ).create()
    content_view.publish()
    # Create and publish composite content view
    composite_cv = module_target_sat.api.ContentView(
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


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_remove_cv_version_from_env_with_host_registered():
    """Remove promoted content view version from environment that is used
    in association of an Activation key and content-host registration.

    :id: a5b9ba8b-80e6-4435-bc0a-041b3fda227c

    :steps:

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
    """


@pytest.mark.upgrade
@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_delete_cv_multi_env_promoted_with_host_registered():
    """Delete published content view with version promoted to multiple
     environments, with one of the environments used in association of an
     Activation key and content-host registration.

    :id: 10699af9-617e-4930-9c80-2827a0ba52eb

    :steps:

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
    """


@pytest.mark.stubbed
@pytest.mark.tier3
def test_positive_remove_cv_version_from_multi_env_capsule_scenario():
    """Remove promoted content view version from multiple environments,
    with satellite module_lce_cv to use capsule

    :id: 1e8a8e64-eec8-49e0-b121-919c53f416d2

    :steps:

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
    """
