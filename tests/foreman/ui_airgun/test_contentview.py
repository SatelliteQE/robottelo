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
from pytest import raises

from navmazing import NavigationTriesExceeded
from nailgun import entities
from widgetastic.exceptions import NoSuchElementException

from robottelo import manifests
from robottelo.api.utils import (
    create_sync_custom_repo,
    enable_sync_redhat_repo,
    upload_manifest,
)
from robottelo.constants import (
    DISTRO_RHEL6,
    ENVIRONMENT,
    FAKE_0_PUPPET_REPO,
    FAKE_0_YUM_REPO,
    FAKE_1_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    PRDS,
    REPO_TYPE,
    REPOS,
    REPOSET,
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
from robottelo.products import (
    RepositoryCollection,
    VirtualizationAgentsRepository,
)


VERSION = 'Version 1.0'


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


def test_positive_create(session):
    cv_name = gen_string('alpha')
    label = gen_string('alpha')
    description = gen_string('alpha')
    with session:
        session.contentview.create({
            'name': cv_name,
            'label': label,
            'description': description,
        })
        assert session.contentview.search(cv_name)[0]['Name'] == cv_name
        cv_values = session.contentview.read(cv_name)
        assert cv_values['details']['name'] == cv_name
        assert cv_values['details']['label'] == label
        assert cv_values['details']['description'] == description
        assert cv_values['details']['composite'] == 'No'


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
