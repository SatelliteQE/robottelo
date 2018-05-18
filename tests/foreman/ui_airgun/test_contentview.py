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

from robottelo import manifests
from robottelo.api.utils import (
    create_sync_custom_repo,
    enable_sync_redhat_repo,
    upload_manifest,
)
from robottelo.constants import (
    FAKE_0_PUPPET_REPO,
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
    version = 'Version 1.0'
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
        assert result['Version'] == version
        result = session.contentview.promote(cv_name, version, env_name)
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
            result = session.contentview.promote(
                cv_name, 'Version 1.0', lce.name)
            assert 'Promoted to {}'.format(lce.name) in result['Status']
            # Add content view to composite one
            # fixme: drop next line after airgun#63 is solved
            session.contentview.search(ccv_name)
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
        # fixme: drop next line after airgun#63 is solved
        session.contentview.search(cv_name2)
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
