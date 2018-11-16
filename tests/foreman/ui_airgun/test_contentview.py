"""Test class for Content View UI

Feature details: https://fedorahosted.org/katello/wiki/ContentViews


:Requirement: Contentview

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import datetime
from pytest import raises

from navmazing import NavigationTriesExceeded
from nailgun import entities
from widgetastic.exceptions import NoSuchElementException

from robottelo import manifests
from robottelo.api.utils import (
    call_entity_method_with_timeout,
    create_sync_custom_repo,
    enable_sync_redhat_repo,
    promote,
    upload_manifest,
)
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_PTABLE,
    DISTRO_RHEL6,
    DISTRO_RHEL7,
    ENVIRONMENT,
    FAKE_0_PUPPET_REPO,
    FAKE_0_YUM_REPO,
    FAKE_1_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    FAKE_3_YUM_REPO,
    FAKE_9_YUM_REPO,
    FAKE_9_YUM_SECURITY_ERRATUM_COUNT,
    FEDORA27_OSTREE_REPO,
    FILTER_CONTENT_TYPE,
    FILTER_ERRATA_TYPE,
    FILTER_TYPE,
    PRDS,
    PUPPET_MODULE_CUSTOM_FILE_NAME,
    PUPPET_MODULE_CUSTOM_NAME,
    REPO_TYPE,
    REPOS,
    REPOSET,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    fixture,
    skip_if_not_set,
    run_in_one_thread,
    tier2,
    tier3,
    upgrade,
)
from robottelo.decorators.host import skip_if_os
from robottelo.helpers import get_data_file
from robottelo.products import (
    RepositoryCollection,
    SatelliteToolsRepository,
    VirtualizationAgentsRepository,
)


VERSION = 'Version 1.0'


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@tier2
def test_positive_add_custom_content(session):
    """Associate custom content in a view

    :id: 7128fc8b-0e8c-4f00-8541-2ca2399650c8

    :setup: Sync custom content

    :expectedresults: Custom content can be seen in a view

    :CaseLevel: Integration
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
        assert (
            cv['repositories']['resources']['assigned'][0]['Name'] == repo_name
        )


@tier2
@upgrade
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
        assert 'Promoted to {}'.format(env_name) in result['Status']


@tier2
def test_positive_repo_count_for_composite_cv(session, module_org):
    """Create some content views with synchronized repositories and
    promoted to one lce. Add them to composite content view and check repo
    count for it.

    :id: 4b8d5def-a593-4f6c-9856-e5f32fb80164

    :expectedresults: repository count for composite content view should
        be the sum of archived repositories across all content views.

    :BZ: 1431778

    :CaseLevel: Integration
    """
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    ccv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    # Create a product and sync'ed repository
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        # Creates a composite CV
        session.contentview.create({
            'name': ccv_name,
            'composite_view': True,
        })
        # Create three content-views and add synced repo to them
        for _ in range(3):
            cv_name = entities.ContentView(
                organization=module_org).create().name
            assert session.contentview.search(cv_name)[0]['Name'] == cv_name
            # Add repository to selected CV
            session.contentview.add_yum_repo(cv_name, repo_name)
            # Publish content view
            session.contentview.publish(cv_name)
            # Check that repo count for cv is equal to 1
            assert session.contentview.search(
                cv_name)[0]['Repositories'] == '1'
            # Promote content view
            result = session.contentview.promote(cv_name, VERSION, lce.name)
            assert 'Promoted to {}'.format(lce.name) in result['Status']
            # Add content view to composite one
            session.contentview.add_cv(ccv_name, cv_name)
        # Publish composite content view
        session.contentview.publish(ccv_name)
        # Check that composite cv has three repositories in the table as we
        # were using one repository for each content view
        assert session.contentview.search(ccv_name)[0]['Repositories'] == '3'


@tier2
def test_positive_add_puppet_module(session, module_org):
    """create content view with puppet repository

    :id: c772d55b-6762-4c25-bbaf-83e7c200fe8a

    :customerscenario: true

    :steps:
        1. Create Product/puppet repo and Sync it
        2. Create CV and add puppet modules from created repo

    :expectedresults: content view is created, updated with puppet module

    :CaseLevel: Integration
    """
    repo_url = FAKE_0_PUPPET_REPO
    cv_name = gen_string('alpha')
    puppet_module = 'httpd'
    create_sync_custom_repo(
        module_org.id, repo_url=repo_url, repo_type=REPO_TYPE['puppet'])
    with session:
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_puppet_module(cv_name, puppet_module)
        cv = session.contentview.read(cv_name)
        assert cv['puppet_modules']['table'][0]['Name'] == puppet_module


@run_in_one_thread
@skip_if_not_set('fake_manifest')
@tier3
def test_positive_create_composite(session):
    # Note: puppet repos cannot/should not be used in this test
    # It shouldn't work - and that is tested in a different case.
    # Individual modules from a puppet repo, however, are a valid
    # variation.
    """Create a composite content views

    :id: 550f1970-5cbd-4571-bb7b-17e97639b715

    :setup: sync multiple content source/types (RH, custom, etc.)

    :expectedresults: Composite content views are created

    :CaseLevel: System
    """
    puppet_module = 'httpd'
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
    # Create new org to import manifest
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    enable_sync_redhat_repo(rh_repo, org.id)
    create_sync_custom_repo(
        org.id, repo_url=FAKE_0_PUPPET_REPO, repo_type=REPO_TYPE['puppet'])
    with session:
        session.organization.select(org.name)
        # Create content views
        for cv_name in (cv_name1, cv_name2):
            session.contentview.create({'name': cv_name})
            assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_puppet_module(cv_name1, puppet_module)
        cv1 = session.contentview.read(cv_name1)
        assert cv1['puppet_modules']['table'][0]['Name'] == puppet_module
        session.contentview.publish(cv_name1)
        session.contentview.add_yum_repo(cv_name2, rh_repo['name'])
        session.contentview.publish(cv_name2)
        session.contentview.create({
            'name': composite_name,
            'composite_view': True,
        })
        for cv_name in (cv_name1, cv_name2):
            session.contentview.add_cv(composite_name, cv_name)
        composite_cv = session.contentview.read(composite_name)
        assert {cv_name1, cv_name2} == set([
            cv['Name']
            for cv
            in composite_cv['content_views']['resources']['assigned']
        ])


@run_in_one_thread
@skip_if_not_set('fake_manifest')
@tier2
def test_positive_add_rh_content(session):
    """Add Red Hat content to a content view

    :id: c370fd79-0c0d-4685-99cb-848556c786c1

    :setup: Sync RH content

    :expectedresults: RH Content can be seen in a view

    :CaseLevel: Integration
    """
    cv_name = gen_string('alpha')
    rh_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None
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
        assert (
            cv['repositories']['resources']['assigned'][0]['Name'] ==
            rh_repo['name']
        )


@tier2
def test_negative_add_puppet_repo_to_composite(session):
    """Attempt to associate puppet repos within a composite content view

    :id: 283fa7da-ca40-4ce2-b3c5-da58ae01b8e7

    :expectedresults: User cannot create a composite content view that contains
        direct puppet repos.

    :CaseLevel: Integration
    """
    composite_name = gen_string('alpha')
    with session:
        session.contentview.create({
            'name': composite_name,
            'composite_view': True,
        })
        assert session.contentview.search(
            composite_name)[0]['Name'] == composite_name
        with raises(NavigationTriesExceeded) as context:
            session.contentview.add_puppet_module(composite_name, 'httpd')
        assert 'failed to reach [AddPuppetModule]' in str(context.value)


@tier2
def test_negative_add_components_to_non_composite(session):
    """Attempt to associate components to a non-composite content view

    :id: fa3e6aea-7ee3-46a6-a5ba-248de3c20a8f

    :expectedresults: User cannot add components to the view

    :CaseLevel: Integration
    """
    cv1_name = gen_string('alpha')
    cv2_name = gen_string('alpha')
    with session:
        session.contentview.create({'name': cv1_name})
        for cv_name in (cv1_name, cv2_name):
            session.contentview.create({'name': cv_name})
            assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        with raises(AssertionError) as context:
            session.contentview.add_cv(cv1_name, cv2_name)
        assert 'Could not find "Content Views" tab' in str(context.value)


@tier2
def test_positive_add_unpublished_cv_to_composite(session):
    """Attempt to associate unpublished non-composite content view with
    composite content view.

    :id: dc253606-3425-489d-bc01-266787d36841

    :steps:

        1. Create an empty non-composite content view. Do not publish it.
        2. Create a new composite content view

    :expectedresults: Non-composite content view is added to composite one

    :CaseLevel: Integration

    :BZ: 1367123
    """
    unpublished_cv_name = gen_string('alpha')
    composite_cv_name = gen_string('alpha')
    with session:
        # Create unpublished component CV
        session.contentview.create({'name': unpublished_cv_name})
        assert session.contentview.search(
            unpublished_cv_name)[0]['Name'] == unpublished_cv_name
        # Create composite CV
        session.contentview.create({
            'name': composite_cv_name,
            'composite_view': True,
        })
        assert session.contentview.search(
            composite_cv_name)[0]['Name'] == composite_cv_name
        # Add unpublished content view to composite one
        session.contentview.add_cv(composite_cv_name, unpublished_cv_name)


@tier2
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
    """
    published_cv_name = gen_string('alpha')
    unpublished_cv_name = gen_string('alpha')
    composite_cv_name = gen_string('alpha')
    with session:
        # Create a published component content view
        session.contentview.create({'name': published_cv_name})
        assert session.contentview.search(
            published_cv_name)[0]['Name'] == published_cv_name
        result = session.contentview.publish(published_cv_name)
        assert result['Version'] == VERSION
        # Create an unpublished component content view
        session.contentview.create({'name': unpublished_cv_name})
        assert session.contentview.search(
            unpublished_cv_name)[0]['Name'] == unpublished_cv_name
        # Create a composite content view
        session.contentview.create({
            'name': composite_cv_name,
            'composite_view': True,
        })
        assert session.contentview.search(
            composite_cv_name)[0]['Name'] == composite_cv_name
        # Add the published content view to the composite one
        session.contentview.add_cv(composite_cv_name, published_cv_name)
        # Add the unpublished content view to the composite one
        session.contentview.add_cv(composite_cv_name, unpublished_cv_name)
        # assert that the version of unpublished content view added to
        # composite one is "Latest (Currently no version)"
        composite_cv = session.contentview.read(composite_cv_name)
        assigned_cvs = composite_cv['content_views']['resources']['assigned']
        unpublished_cv = next(
            cv for cv in assigned_cvs if cv['Name'] == unpublished_cv_name)
        assert unpublished_cv['Version'] == 'Latest (Currently no version)'
        # Publish the composite content view
        result = session.contentview.publish(composite_cv_name)
        assert result['Version'] == VERSION


@tier2
def test_negative_add_dupe_repos(session, module_org):
    """attempt to associate the same repo multiple times within a
    content view

    :id: 24b98075-fca6-4d80-a778-066193c71e7f

    :expectedresults: User cannot add repos multiple times to the view

    :CaseLevel: Integration
    """
    cv_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    with session:
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        with raises(NoSuchElementException) as context:
            session.contentview.add_yum_repo(cv_name, repo_name)
        assert 'Could not find element' and repo_name in str(context.value)


@tier2
def test_negative_add_dupe_modules(session, module_org):
    """Attempt to associate duplicate puppet module(s) within a content view

    :id: ee33a306-9f91-439d-ac7c-d30f7e1a14cc

    :expectedresults: User cannot add modules multiple times to the view

    :CaseLevel: Integration
    """
    cv_name = gen_string('alpha')
    module_name = 'samba'
    product = entities.Product(organization=module_org).create()
    puppet_repository = entities.Repository(
        url=FAKE_0_PUPPET_REPO,
        content_type='puppet',
        product=product
    ).create()
    puppet_repository.sync()
    with session:
        # Create content-view
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_puppet_module(cv_name, module_name)
        # ensure that the puppet module is added to content view
        cv = session.contentview.read(cv_name)
        assert cv['puppet_modules']['table'][0]['Name'] == module_name
        # ensure that cannot add the same module a second time.
        with raises(NavigationTriesExceeded) as context:
            session.contentview.add_puppet_module(cv_name, module_name)
        assert (
            'Navigation failed to reach [SelectPuppetModuleVersion]'
            in str(context.value)
        )


@tier2
def test_positive_publish_with_custom_content(session, module_org):
    """Attempt to publish a content view containing custom content

    :id: 66b5efc7-2e43-438e-bd80-a754814222f9

    :setup: Multiple environments for an org; custom content synced

    :expectedresults: Content view can be published

    :CaseLevel: Integration
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


@run_in_one_thread
@skip_if_not_set('fake_manifest')
@tier2
def test_positive_publish_with_rh_content(session):
    """Attempt to publish a content view containing RH content

    :id: bd24dc13-b6c4-4a9b-acb2-cd6df30f436c

    :setup: RH content synced

    :expectedresults: Content view can be published

    :CaseLevel: System
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


@run_in_one_thread
@skip_if_not_set('fake_manifest')
@tier2
def test_positive_publish_composite_with_custom_content(session):
    """Attempt to publish composite content view containing custom content

    :id: 73947204-408e-4e2e-b87f-ba2e52ee50b6

    :setup: Multiple environments for an org; custom content synced

    :expectedresults: Composite content view can be published

    :CaseLevel: Integration
    """
    cv1_name = gen_string('alpha')
    cv2_name = gen_string('alpha')
    cv_composite_name = gen_string('alpha')
    custom_repo1_name = gen_string('alpha')
    custom_repo2_name = gen_string('alpha')
    custom_repo1_url = FAKE_0_YUM_REPO
    custom_repo2_url = FAKE_1_YUM_REPO
    puppet_repo1_url = FAKE_0_PUPPET_REPO
    puppet_repo2_url = FAKE_1_PUPPET_REPO
    puppet_module1 = 'httpd'
    puppet_module2 = 'ntp'
    rh7_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    # Enable and sync RH repository
    enable_sync_redhat_repo(rh7_repo, org.id)
    # Create custom yum repositories
    for name, url in (
            (custom_repo1_name, custom_repo1_url),
            (custom_repo2_name, custom_repo2_url)):
        create_sync_custom_repo(repo_name=name, repo_url=url, org_id=org.id)
    # Create custom puppet repositories
    for url in (puppet_repo1_url, puppet_repo2_url):
        create_sync_custom_repo(
            repo_url=url, repo_type=REPO_TYPE['puppet'], org_id=org.id)
    with session:
        session.organization.select(org.name)
        # create the first content view
        session.contentview.create({'name': cv1_name})
        assert session.contentview.search(cv1_name)[0]['Name'] == cv1_name
        # add repositories to first content view
        for repo_name in (rh7_repo['name'], custom_repo1_name):
            session.contentview.add_yum_repo(cv1_name, repo_name)
        # add the first puppet module to first content view
        session.contentview.add_puppet_module(cv1_name, puppet_module1)
        # publish the first content
        result = session.contentview.publish(cv1_name)
        assert result['Version'] == VERSION
        # create the second content view
        session.contentview.create({'name': cv2_name})
        assert session.contentview.search(cv2_name)[0]['Name'] == cv2_name
        # add repositories to the second content view
        session.contentview.add_yum_repo(cv2_name, custom_repo2_name)
        # add the second puppet module to the second content view
        session.contentview.add_puppet_module(cv2_name, puppet_module2)
        # publish the second content
        result = session.contentview.publish(cv2_name)
        assert result['Version'] == VERSION
        # create a composite content view
        session.contentview.create({
            'name': cv_composite_name,
            'composite_view': True,
        })
        assert session.contentview.search(
            cv_composite_name)[0]['Name'] == cv_composite_name
        # add the first and second content views to the composite one
        for cv_name in (cv1_name, cv2_name):
            session.contentview.add_cv(cv_composite_name, cv_name)
        # publish the composite content view
        result = session.contentview.publish(cv_composite_name)
        assert result['Version'] == VERSION
        ccv = session.contentview.read(cv_composite_name)
        assert ccv['versions']['table'][0]['Version'] == VERSION


@tier2
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
    """
    cv_name = gen_string('alpha')
    # will promote environment to 3 versions
    versions_count = 3
    versions = ('Version {}.0'.format(ver+1) for ver in range(versions_count))
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
            assert 'Promoted to {}'.format(lce.name) in result['Status']
            # assert that Library is still in environments of this version
            assert ENVIRONMENT in result['Environments']
            # assert that env_name is in environments of this version
            assert lce.name in result['Environments']


@tier2
def test_positive_promote_with_custom_content(session, module_org):
    """Attempt to promote a content view containing custom content

    :id: 7c2fd8f0-c83f-4725-8953-9590112fae50

    :setup: Multiple environments for an org; custom content synced

    :expectedresults: Content view can be promoted

    :CaseLevel: Integration
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
        assert 'Promoted to {}'.format(lce.name) in result['Status']


@run_in_one_thread
@skip_if_not_set('fake_manifest')
@tier2
def test_positive_promote_with_rh_content(session):
    """Attempt to promote a content view containing RH content

    :id: 82f71639-3580-49fd-bd5a-8dba568b98d1

    :setup: Multiple environments for an org; RH content synced

    :expectedresults: Content view can be promoted

    :CaseLevel: System
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
        assert 'Promoted to {}'.format(lce.name) in result['Status']


@run_in_one_thread
@skip_if_not_set('fake_manifest')
@tier2
def test_positive_promote_composite_with_custom_content(session):
    """Attempt to promote composite content view containing custom content

    :id: 35efbd83-d32e-4831-9d5b-1adb15289f54

    :setup: Multiple environments for an org; custom content synced

    :steps: create a composite view containing multiple content types

    :expectedresults: Composite content view can be promoted

    :CaseLevel: Integration
    """
    cv1_name = gen_string('alpha')
    cv2_name = gen_string('alpha')
    cv_composite_name = gen_string('alpha')
    custom_repo1_name = gen_string('alpha')
    custom_repo2_name = gen_string('alpha')
    custom_repo1_url = FAKE_0_YUM_REPO
    custom_repo2_url = FAKE_1_YUM_REPO
    puppet_repo1_url = FAKE_0_PUPPET_REPO
    puppet_repo2_url = FAKE_1_PUPPET_REPO
    puppet_module1 = 'httpd'
    puppet_module2 = 'ntp'
    rh7_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    org = entities.Organization().create()
    with manifests.clone() as manifest:
        upload_manifest(org.id, manifest.content)
    # create a life cycle environment
    lce = entities.LifecycleEnvironment(organization=org).create()
    # Enable and sync RH repository
    enable_sync_redhat_repo(rh7_repo, org.id)
    # Create custom yum repositories
    for name, url in (
            (custom_repo1_name, custom_repo1_url),
            (custom_repo2_name, custom_repo2_url)):
        create_sync_custom_repo(repo_name=name, repo_url=url, org_id=org.id)
    # Create custom puppet repositories
    for url in (puppet_repo1_url, puppet_repo2_url):
        create_sync_custom_repo(
            repo_url=url, repo_type=REPO_TYPE['puppet'], org_id=org.id)
    with session:
        session.organization.select(org.name)
        # create the first content view
        session.contentview.create({'name': cv1_name})
        assert session.contentview.search(cv1_name)[0]['Name'] == cv1_name
        # add repositories to first content view
        for repo_name in (rh7_repo['name'], custom_repo1_name):
            session.contentview.add_yum_repo(cv1_name, repo_name)
        # add the first puppet module to first content view
        session.contentview.add_puppet_module(cv1_name, puppet_module1)
        # publish the first content
        result = session.contentview.publish(cv1_name)
        assert result['Version'] == VERSION
        # create the second content view
        session.contentview.create({'name': cv2_name})
        assert session.contentview.search(cv2_name)[0]['Name'] == cv2_name
        # add repositories to the second content view
        session.contentview.add_yum_repo(cv2_name, custom_repo2_name)
        # add the second puppet module to the second content view
        session.contentview.add_puppet_module(cv2_name, puppet_module2)
        # publish the second content
        result = session.contentview.publish(cv2_name)
        assert result['Version'] == VERSION
        # create a composite content view
        session.contentview.create({
            'name': cv_composite_name,
            'composite_view': True,
        })
        assert session.contentview.search(
            cv_composite_name)[0]['Name'] == cv_composite_name
        # add the first and second content views to the composite one
        for cv_name in (cv1_name, cv2_name):
            session.contentview.add_cv(cv_composite_name, cv_name)
        # publish the composite content view
        result = session.contentview.publish(cv_composite_name)
        assert result['Version'] == VERSION
        # promote the composite content view
        result = session.contentview.promote(
            cv_composite_name, VERSION, lce.name)
        assert 'Promoted to {}'.format(lce.name) in result['Status']


@run_in_one_thread
@tier2
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
        distro=DISTRO_RHEL6,
        repositories=[VirtualizationAgentsRepository()]
    )
    repos_collection.setup_content(
        org.id, lce.id,
        download_policy='immediate',
        upload_manifest=True,
    )
    cv = entities.ContentView(
        id=repos_collection.setup_content_data['content_view']['id']).read()
    cvf = entities.ErratumContentViewFilter(
        content_view=cv,
        inclusion=False,
        repository=[repos_collection.repos_info[0]['id']],
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


@tier2
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
        session.contentview.remove_version(
            cv_name, VERSION, False, [ENVIRONMENT])
        cvv = session.contentview.search_version(cv_name, VERSION)[0]
        assert ENVIRONMENT not in cvv['Environments']


@tier2
def test_positive_clone_within_same_env(session, module_org):
    """attempt to create new content view based on existing
    view within environment

    :id: 862c385b-d98c-4c29-8345-fd7a5900483a

    :expectedresults: Content view can be cloned

    :BZ: 1461017

    :CaseLevel: Integration
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
        assert session.contentview.search(
            copy_cv_name)[0]['Name'] == copy_cv_name
        copy_cv = session.contentview.read(copy_cv_name)
        assert copy_cv[
            'repositories']['resources']['assigned'][0]['Name'] == repo_name


@tier2
def test_positive_remove_filter(session, module_org):
    """Create empty content views filter and remove it

    :id: 6c6deae7-13f1-4638-a960-d3565d93fd64

    :expectedresults: content views filter removed successfully

    :CaseLevel: Integration
    """
    filter_name = gen_string('alpha')
    cv = entities.ContentView(organization=module_org).create()
    with session:
        session.contentviewfilter.create(cv.name, {
            'name': filter_name,
            'content_type': FILTER_CONTENT_TYPE['package'],
            'inclusion_type': FILTER_TYPE['exclude'],
        })
        assert session.contentviewfilter.search(
            cv.name, filter_name)[0]['Name'] == filter_name
        session.contentviewfilter.delete(cv.name, filter_name)
        assert not session.contentviewfilter.search(cv.name, filter_name)


@tier2
def test_positive_add_package_filter(session, module_org):
    """Add package to content views filter

    :id: 1cc8d921-92e5-4b51-8050-a7e775095f97

    :expectedresults: content views filter created and selected packages can be
        added for inclusion/exclusion

    :CaseLevel: Integration
    """
    packages = (
                ('cow', 'All Versions'),
                ('bird', ('Equal To', '0.5')),
                ('crow', ('Less Than', '0.5')),
                ('bear', ('Range', '4.1', '4.6')))
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(
        query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(
        organization=module_org,
        repository=[repo]
    ).create()
    with session:
        session.contentviewfilter.create(cv.name, {
            'name': filter_name,
            'content_type': FILTER_CONTENT_TYPE['package'],
            'inclusion_type': FILTER_TYPE['include'],
        })
        for package_name, versions in packages:
            session.contentviewfilter.add_package_rule(
                cv.name, filter_name, package_name, None, versions)
        cvf = session.contentviewfilter.read(cv.name, filter_name)
        expected_packages = {
            package_name for package_name, versions in packages}
        actual_packages = {
            row['RPM Name'] for row in cvf['content_tabs']['rpms']['table']}
        assert expected_packages == actual_packages


@tier2
def test_positive_update_inclusive_filter_package_version(session, module_org):
    """Update version of package inside inclusive cv package filter

    :id: 8d6801de-ab82-49d6-bdeb-0f6e5c95b906

    :expectedresults: Version was updated, next content view version contains
        package with updated version

    :CaseLevel: Integration
    """
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package_name = 'walrus'
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(
        query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(
        organization=module_org,
        repository=[repo]
    ).create()
    with session:
        session.contentviewfilter.create(cv.name, {
            'name': filter_name,
            'content_type': FILTER_CONTENT_TYPE['package'],
            'inclusion_type': FILTER_TYPE['include'],
        })
        session.contentviewfilter.add_package_rule(
            cv.name, filter_name, package_name, None, ('Equal To', '0.71-1'))
        result = session.contentview.publish(cv.name)
        assert result['Version'] == VERSION
        packages = session.contentview.search_version_package(
            cv.name, VERSION,
            'name = "{}" and version = "{}"'.format(package_name, '0.71')
        )
        assert len(packages) == 1
        assert (
            packages[0]['Name'] == package_name
            and packages[0]['Version'] == '0.71'
        )
        packages = session.contentview.search_version_package(
            cv.name, VERSION,
            'name = "{}" and version = "{}"'.format(package_name, '5.21')
        )
        assert not packages
        session.contentviewfilter.update_package_rule(
            cv.name, filter_name, package_name,
            {'Version': ('Equal To', '5.21-1')},
            version='Version 0.71-1',
        )
        new_version = session.contentview.publish(cv.name)['Version']
        packages = session.contentview.search_version_package(
            cv.name, new_version,
            'name = "{}" and version = "{}"'.format(package_name, '0.71')
        )
        assert not packages
        packages = session.contentview.search_version_package(
            cv.name, new_version,
            'name = "{}" and version = "{}"'.format(package_name, '5.21')
        )
        assert len(packages) == 1
        assert (
            packages[0]['Name'] == package_name
            and packages[0]['Version'] == '5.21'
        )


@run_in_one_thread
@skip_if_not_set('fake_manifest')
@tier3
def test_positive_edit_rh_custom_spin(session):
    """Edit content views for a custom rh spin.  For example, modify a filter

    :id: 05639074-ef6d-4c6b-8ff6-53033821e686

    :expectedresults: edited content view save is successful and info is
        updated

    :CaseLevel: System
    """
    filter_name = gen_string('alpha')
    start_date = datetime.date(2016, 1, 1)
    end_date = datetime.date(2016, 6, 1)
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7,
        repositories=[SatelliteToolsRepository()]
    )
    repos_collection.setup_content(
        org.id, lce.id,
        upload_manifest=True,
    )
    cv = entities.ContentView(
        id=repos_collection.setup_content_data['content_view']['id']).read()
    with session:
        session.organization.select(org.name)
        session.contentviewfilter.create(cv.name, {
            'name': filter_name,
            'content_type': FILTER_CONTENT_TYPE['erratum by date and type'],
            'inclusion_type': FILTER_TYPE['exclude'],
        })
        session.contentviewfilter.update(cv.name, filter_name, {
            'content_tabs.erratum_date_range.security': False,
            'content_tabs.erratum_date_range.enhancement': True,
            'content_tabs.erratum_date_range.bugfix': True,
            'content_tabs.erratum_date_range.date_type': 'Issued On',
            'content_tabs.erratum_date_range.start_date': start_date.strftime(
                '%m-%d-%Y'),
            'content_tabs.erratum_date_range.end_date': end_date.strftime(
                '%m-%d-%Y'),
        })
        cvf = session.contentviewfilter.read(cv.name, filter_name)
        assert not cvf['content_tabs']['erratum_date_range']['security']
        assert cvf['content_tabs']['erratum_date_range']['enhancement']
        assert cvf['content_tabs']['erratum_date_range']['bugfix']
        assert cvf['content_tabs']['erratum_date_range'][
                   'date_type'] == 'Issued On'
        assert cvf['content_tabs']['erratum_date_range'][
                   'start_date'] == start_date.strftime('%Y-%m-%d')
        assert cvf['content_tabs']['erratum_date_range'][
                   'end_date'] == end_date.strftime('%Y-%m-%d')


@tier2
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
    repo = entities.Repository(
        product=product,
        url=FAKE_9_YUM_REPO,
    ).create()
    repo.sync()
    content_view = entities.ContentView(
        organization=module_org,
        repository=[repo],
    ).create()
    content_view.publish()
    with session:
        session.contentviewfilter.create(content_view.name, {
            'name': filter_name,
            'content_type': FILTER_CONTENT_TYPE['erratum by id'],
            'inclusion_type': FILTER_TYPE['include'],
        })
        session.contentviewfilter.add_errata(
            content_view.name, filter_name,
            search_filters={
                'security': True,
                'bugfix': False,
                'enhancement': False,
            }
        )
        content_view.publish()
        cvv = session.contentview.read_version(content_view.name, version)
        assert len(cvv['errata']['table']) == FAKE_9_YUM_SECURITY_ERRATUM_COUNT
        assert all(
            errata['Type'] == FILTER_ERRATA_TYPE['security']
            for errata in cvv['errata']['table']
        )


@tier2
def test_positive_add_package_group_filter(session, module_org):
    """add package group to content views filter

    :id: 8c02a432-8b2a-4ba3-9613-7070b2dc2bcb

    :expectedresults: content views filter created and selected package
        groups can be added for inclusion/exclusion

    :CaseLevel: Integration
    """
    filter_name = gen_string('alpha')
    repo_name = gen_string('alpha')
    package_group = 'mammals'
    create_sync_custom_repo(module_org.id, repo_name=repo_name)
    repo = entities.Repository(name=repo_name).search(
        query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(
        organization=module_org,
        repository=[repo]
    ).create()
    with session:
        session.contentviewfilter.create(cv.name, {
            'name': filter_name,
            'content_type': FILTER_CONTENT_TYPE['package group'],
            'inclusion_type': FILTER_TYPE['include'],
        })
        session.contentviewfilter.add_package_group(
            cv.name, filter_name, package_group)
        cvf = session.contentviewfilter.read(cv.name, filter_name)
        assert cvf['content_tabs']['assigned'][0]['Name'] == package_group


@tier2
def test_positive_update_filter_affected_repos(session, module_org):
    """Update content view package filter affected repos

    :id: 8f095b11-fd63-4a23-9586-a85d6191314f

    :expectedresults: Affected repos were updated, after new content view
        version publishing only updated repos are affected by content view
        filter

    :CaseLevel: Integration
    """
    filter_name = gen_string('alpha')
    repo1_name = gen_string('alpha')
    repo2_name = gen_string('alpha')
    repo1_package_name = 'walrus'
    repo2_package_name = 'Walrus'
    create_sync_custom_repo(module_org.id, repo_name=repo1_name)
    create_sync_custom_repo(
        module_org.id, repo_name=repo2_name, repo_url=FAKE_3_YUM_REPO)
    repo1 = entities.Repository(name=repo1_name).search(
        query={'organization_id': module_org.id})[0]
    repo2 = entities.Repository(name=repo2_name).search(
        query={'organization_id': module_org.id})[0]
    cv = entities.ContentView(
        organization=module_org,
        repository=[repo1, repo2]
    ).create()
    with session:
        session.contentviewfilter.create(cv.name, {
            'name': filter_name,
            'content_type': FILTER_CONTENT_TYPE['package'],
            'inclusion_type': FILTER_TYPE['include'],
        })
        session.contentviewfilter.add_package_rule(
            cv.name, filter_name, repo1_package_name, None,
            ('Equal To', '0.71-1')
        )
        session.contentviewfilter.update_repositories(
            cv.name, filter_name, [repo1_name])
        cv.publish()
        # Verify filter affected repo1
        packages = session.contentview.search_version_package(
            cv.name, VERSION,
            'name = "{}" and version = "{}"'.format(repo1_package_name, '0.71')
        )
        assert packages
        assert (
                packages[0]['Name'] == repo1_package_name
                and packages[0]['Version'] == '0.71'
        )
        packages = session.contentview.search_version_package(
            cv.name, VERSION,
            'name = "{}" and version = "{}"'.format(repo1_package_name, '5.21')
        )
        assert not packages
        # Verify repo2 was not affected and repo2 packages are present
        packages = session.contentview.search_version_package(
            cv.name, VERSION,
            'name = "{}" and version = "{}"'
            .format(repo2_package_name, '5.6.6')
        )
        assert packages
        assert (
                packages[0]['Name'] == repo2_package_name
                and packages[0]['Version'] == '5.6.6'
        )


@tier2
def test_positive_search_composite(session):
    """Search for content view by its composite property criteria

    :id: 214a721b-3993-4251-9b7c-0f6d2446c1d1

    :customerscenario: true

    :expectedresults: Composite content view is successfully found

    :BZ: 1259374

    :CaseLevel: Integration

    :CaseImportance: High
    """
    composite_name = gen_string('alpha')
    with session:
        session.contentview.create({
            'name': composite_name, 'composite_view': True})
        assert (
            composite_name in
            {ccv['Name'] for ccv in session.contentview.search('composite = true')}
        )


@tier2
def test_positive_publish_with_force_puppet_env(session, module_org):
    """Check that puppet environment will be created automatically once
    content view that contains puppet module is published, no matter
    whether 'Force Puppet' option is enabled or disabled for that content
    view
    Check that puppet environment will be created automatically once content
    view without puppet module is published, only if 'Force Puppet' option is
    enabled

    :id: af553367-e621-41e8-86cb-091ba7ba6c0a

    :customerscenario: true

    :expectedresults: puppet environment is created only in expected cases

    :BZ: 1437110

    :CaseLevel: Integration
    """
    puppet_module = 'httpd'
    create_sync_custom_repo(
        module_org.id, repo_url=FAKE_0_PUPPET_REPO, repo_type=REPO_TYPE['puppet'])
    with session:
        for add_puppet in [True, False]:
            for force_value in [True, False]:
                cv_name = gen_string('alpha')
                session.contentview.create({'name': cv_name})
                session.contentview.update(
                    cv_name, {'details.force_puppet': force_value})
                if add_puppet:
                    session.contentview.add_puppet_module(cv_name, puppet_module)
                result = session.contentview.publish(cv_name)
                assert result['Version'] == VERSION
                env_name = 'KT_{0}_{1}_{2}_{3}'.format(
                    module_org.name,
                    ENVIRONMENT,
                    cv_name,
                    str(
                        entities.ContentView(
                            name=cv_name,
                            organization=module_org,
                        ).search()[0].id
                    ),
                )
                if not add_puppet and not force_value:
                    assert not session.puppetenvironment.search(env_name)
                else:
                    assert session.puppetenvironment.search(env_name)[0]['Name'] == env_name


@tier2
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
    """
    repo_name = gen_string('alpha')
    product_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    # Creates a CV along with product and sync'ed repository
    create_sync_custom_repo(
        module_org.id,
        product_name=product_name,
        repo_name=repo_name,
        repo_unprotected=True
    )
    with session:
        # Create content-view
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        # Update repository publishing method
        session.repository.update(
            product_name, repo_name,
            {'repo_content.publish_via_http': False}
        )
        session.contentview.add_yum_repo(cv_name, repo_name)
        # Publish content view
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION


@tier3
def test_positive_publish_promote_with_custom_puppet_module(session, module_org):
    """Ensure that a custom puppet module file can be added to an existent
     puppet repo and it's module added to content view

    :id: 9562c548-5b65-4b79-acc7-382f8a21249d

    :customerscenario: true

    :steps:
        1. Create a product with a puppet repository
        2. Add a custom puppet module file
        3. Create a content view and add The puppet module
        4. Publish and promote the content view

    :expectedresults:
        1. Custom puppet module file successfully uploaded
        2. Puppet module successfully added to content view
        3. Content view successfully published and promoted

    :BZ: 1335833

    :CaseLevel: System
    """
    cv_name = gen_string('alpha')
    env = entities.LifecycleEnvironment(organization=module_org).create()
    # Creates new custom product via API's
    product = entities.Product(organization=module_org).create()
    # Creates new custom repository via API's
    repo = entities.Repository(
        url=FAKE_0_PUPPET_REPO,
        content_type=REPO_TYPE['puppet'],
        product=product,
    ).create()
    # Sync repo
    call_entity_method_with_timeout(
        entities.Repository(id=repo.id).sync, timeout=1500)
    with session:
        repo_values = session.repository.read(product.name, repo.name)
        initial_modules_count = int(repo_values['content_counts']['Puppet Modules'])
        session.repository.upload_content(
            product.name, repo.name, get_data_file(PUPPET_MODULE_CUSTOM_FILE_NAME))
        repo_values = session.repository.read(product.name, repo.name)
        assert (
            int(repo_values['content_counts']['Puppet Modules'])
            == initial_modules_count + 1
        )
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_puppet_module(cv_name, PUPPET_MODULE_CUSTOM_NAME)
        cv = session.contentview.read(cv_name)
        assert cv['puppet_modules']['table'][0]['Name'] == PUPPET_MODULE_CUSTOM_NAME
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, env.name)
        assert 'Promoted to {}'.format(env.name) in result['Status']


@tier3
def test_positive_delete_with_kickstart_repo_and_host_group(session):
    """Check that Content View associated with kickstart repository and
    which is used by a host group can be removed from the system

    :id: 7b076f55-72c9-4413-a592-92a47b51cb0a

    :customerscenario: true

    :expectedresults: Deletion was performed successfully

    :BZ: 1417072

    :CaseLevel: Integration
    """
    hg_name = gen_string('alpha')
    sat_hostname = settings.server.hostname
    org = entities.Organization().create()
    # Create a new Lifecycle environment
    lc_env = entities.LifecycleEnvironment(organization=org).create()
    # Create a Product and Kickstart Repository for OS distribution content
    product = entities.Product(organization=org).create()
    repo = entities.Repository(product=product, url=settings.rhel6_os).create()
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
    ptable = entities.PartitionTable().search(
        query={u'search': u'name="{0}"'.format(DEFAULT_PTABLE)})[0]
    # Get the arch ID
    arch = entities.Architecture().search(
        query={u'search': u'name="{0}"'.format(DEFAULT_ARCHITECTURE)}
    )[0].read()
    # Get the OS ID
    os = entities.OperatingSystem().search(query={
        u'search': u'name="RedHat" AND (major="{0}" OR major="{1}")'
                   .format(RHEL_6_MAJOR_VERSION, RHEL_7_MAJOR_VERSION)
    })[0]
    # Update the OS to associate arch and ptable
    os.architecture = [arch]
    os.ptable = [ptable]
    os = os.update(['architecture', 'ptable'])
    with session:
        session.organization.select(org.name)
        session.hostgroup.create({
            'host_group.name': hg_name,
            'host_group.lce': lc_env.name,
            'host_group.content_view': content_view.name,
            'host_group.content_source': sat_hostname,
            'host_group.puppet_ca': sat_hostname,
            'host_group.puppet_master': sat_hostname,
            'operating_system.architecture': arch.name,
            'operating_system.operating_system': '{} {}.{}'.format(
                os.name, os.major, os.minor),
            'operating_system.ptable': ptable.name,
            'operating_system.media_type': 'Synced Content',
            'operating_system.media_content.synced_content': repo.name,
        })
        assert session.hostgroup.search(hg_name)[0]['Name'] == hg_name
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        with raises(AssertionError) as context:
            session.contentview.delete(cv_name)
        assert 'Unable to delete content view' in str(context.value)
        # remove the content view version
        session.contentview.remove_version(cv_name, VERSION)
        assert not session.contentview.search_version(cv_name, VERSION)
        session.contentview.delete(cv_name)
        assert not session.contentview.search(cv_name)


@skip_if_os('RHEL6')
@tier3
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
    """
    repo_name = gen_string('alpha')
    cv_name = gen_string('alpha')
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    create_sync_custom_repo(
        module_org.id,
        repo_url=FEDORA27_OSTREE_REPO,
        repo_type=REPO_TYPE['ostree'],
        repo_name=repo_name,
        repo_unprotected=False
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
        assert 'Promoted to {}'.format(lce.name) in result['Status']
        # Remove repository from content view
        session.contentview.remove_ostree_repo(cv_name, repo_name)
        cv = session.contentview.read(cv_name)
        assert len(cv['ostree_content']['resources']['assigned']) == 0
        assert cv['ostree_content']['resources']['unassigned'][0]['Name'] == repo_name


@skip_if_os('RHEL6')
@tier3
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
        assert 'Promoted to {}'.format(lce.name) in result['Status']
        # Remove repository from content view
        session.contentview.remove_ostree_repo(cv_name, repo_name)
        cv = session.contentview.read(cv_name)
        assert len(cv['ostree_content']['resources']['assigned']) == 0
        assert cv['ostree_content']['resources']['unassigned'][0]['Name'] == repo_name


@skip_if_os('RHEL6')
@upgrade
@tier3
def test_positive_mixed_content_end_to_end(session, module_org):
    """Create a CV with ostree as well as yum and puppet type contents and
    publish and promote them to next environment. Remove promoted version afterwards

    :id: 6da1a167-cef8-420e-9fdd-bf357f820056

    :expectedresults: CV should be published and promoted with custom
        OSTree and all other contents. Then version is removed successfully

    :CaseLevel: System
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
    # Creates puppet module
    puppet_module = 'httpd'
    entities.Repository(
        url=FAKE_0_PUPPET_REPO,
        content_type=REPO_TYPE['puppet'],
        product=product,
    ).create()
    yum_repo_name = gen_string('alpha')
    # Creates yum repository
    entities.Repository(
        name=yum_repo_name,
        url=FAKE_1_YUM_REPO,
        content_type=REPO_TYPE['yum'],
        product=product,
    ).create()
    # Sync all repositories in the product
    product.sync()
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    entities.ContentView(name=cv_name, organization=module_org).create()
    with session:
        session.contentview.add_yum_repo(cv_name, yum_repo_name)
        session.contentview.add_puppet_module(cv_name, puppet_module)
        session.contentview.add_ostree_repo(cv_name, ostree_repo_name)
        cv = session.contentview.read(cv_name)
        assert (
            cv['repositories']['resources']['assigned'][0]['Name']
            == yum_repo_name
        )
        assert cv['puppet_modules']['table'][0]['Name'] == puppet_module
        assert (
            cv['ostree_content']['resources']['assigned'][0]['Name']
            == ostree_repo_name
        )
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, lce.name)
        assert 'Promoted to {}'.format(lce.name) in result['Status']
        # remove the content view version
        session.contentview.remove_version(cv_name, VERSION)
        assert not session.contentview.search_version(cv_name, VERSION)


@skip_if_os('RHEL6')
@upgrade
@tier3
def test_positive_rh_mixed_content_end_to_end(session):
    """Create a CV with RH ostree as well as RH yum contents and publish and promote
    them to next environment. Remove promoted version afterwards

    :id: 752f7b95-26af-4f20-a49d-7b31ae3d7a1a

    :expectedresults: CV should be published and promoted with RH OSTree and all
        other contents. Then version is removed successfully.

    :CaseLevel: System
    """
    cv_name = gen_string('alpha')
    rh_ah_repo = {
        'name': REPOS['rhaht']['name'],
        'product': PRDS['rhah'],
        'reposet': REPOSET['rhaht'],
        'basearch': None,
        'releasever': None,
    }
    rh_st_repo = {
        'name': REPOS['rhst7']['name'],
        'product': PRDS['rhel'],
        'reposet': REPOSET['rhst7'],
        'basearch': 'x86_64',
        'releasever': None,
    }
    org = entities.Organization().create()
    manifests.upload_manifest_locked(org.id)
    for rh_repo in [rh_ah_repo, rh_st_repo]:
        enable_sync_redhat_repo(rh_repo, org.id)
    lce = entities.LifecycleEnvironment(organization=org).create()
    with session:
        session.organization.select(org.name)
        session.contentview.create({'name': cv_name})
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        session.contentview.add_yum_repo(cv_name, rh_st_repo['name'])
        session.contentview.add_ostree_repo(cv_name, rh_ah_repo['name'])
        cv = session.contentview.read(cv_name)
        assert (
            cv['repositories']['resources']['assigned'][0]['Name']
            == rh_st_repo['name']
        )
        assert (
            cv['ostree_content']['resources']['assigned'][0]['Name']
            == rh_ah_repo['name']
        )
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == VERSION
        result = session.contentview.promote(cv_name, VERSION, lce.name)
        assert 'Promoted to {}'.format(lce.name) in result['Status']
        # remove the content view version
        session.contentview.remove_version(cv_name, VERSION)
        assert not session.contentview.search_version(cv_name, VERSION)
