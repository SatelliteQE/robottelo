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
from nailgun import entities

from robottelo.api.utils import create_sync_custom_repo
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade


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
        assert session.contentview.search(cv_name) == cv_name
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
        assert session.contentview.search(cv_name) == cv_name
        session.contentview.add_yum_repo(cv_name, repo_name)
        cv_values = session.contentview.read(cv_name)
        assert cv_values['yumrepo']['repos']['assigned'][0] == repo_name


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
        assert session.contentview.search(cv_name) == cv_name
        # Add repository to selected CV
        session.contentview.add_yum_repo(cv_name, repo_name)
        # Publish and promote CV to next environment
        result = session.contentview.publish(cv_name)
        assert result['Version'] == version
        result = session.contentview.promote(cv_name, version, env_name)
        assert 'Promoted to {}'.format(env_name) in result['Status']
