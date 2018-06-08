# -*- encoding: utf-8 -*-
"""Test class for Repository UI

:Requirement: Repository

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from airgun.session import Session
from nailgun import entities
from navmazing import NavigationTriesExceeded
from pytest import raises

from robottelo.api.utils import create_role_permissions
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, upgrade
from robottelo.constants import (
    DOCKER_REGISTRY_HUB,
    FAKE_0_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    REPO_DISCOVERY_URL,
    REPO_TYPE,
)


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@tier2
@upgrade
def test_positive_create_in_different_orgs(session, module_org):
    """Create repository in two different orgs with same name

    :id: 019c2242-8802-4bae-82c5-accf8f793dbc

    :expectedresults: Repository is created successfully for both
        organizations

    :CaseLevel: Integration
    """
    repo_name = gen_string('alpha')
    org2 = entities.Organization().create()
    prod1 = entities.Product(organization=module_org).create()
    prod2 = entities.Product(organization=org2).create()
    with session:
        for org, prod in [[module_org, prod1], [org2, prod2]]:
            session.organization.select(org_name=org.name)
            session.repository.create(
                prod.name,
                {
                    'name': repo_name,
                    'label': org.name,
                    'repo_type': REPO_TYPE['yum'],
                    'repo_content.upstream_url': FAKE_1_YUM_REPO,
                }
            )
            assert session.repository.search(
                prod.name, repo_name)[0]['Name'] == repo_name
            values = session.repository.read(prod.name, repo_name)
            assert values['name'] == repo_name
            assert values['label'] == org.name


@tier2
def test_positive_create_as_non_admin_user(module_org, test_name):
    """Create a repository as a non admin user

    :id: 582949c4-b95f-4d64-b7f0-fb80b3d2bd7e

    :expectedresults: Repository successfully created

    :BZ: 1426393

    :CaseLevel: Integration
    """
    user_login = gen_string('alpha')
    user_password = gen_string('alphanumeric')
    repo_name = gen_string('alpha')
    user_permissions = {
        None: ['access_dashboard'],
        'Katello::Product': [
            'view_products',
            'create_products',
            'edit_products',
            'destroy_products',
            'sync_products',
            'export_products',
        ],
    }
    role = entities.Role().create()
    create_role_permissions(role, user_permissions)
    entities.User(
        login=user_login,
        password=user_password,
        role=[role],
        admin=False,
        default_organization=module_org,
        organization=[module_org],
    ).create()
    product = entities.Product(organization=module_org).create()
    with Session(
            test_name, user=user_login, password=user_password) as session:
        session.organization.select(org_name=module_org.name)
        # ensure that the created user is not a global admin user
        # check administer->organizations page
        with raises(NavigationTriesExceeded):
            session.organization.create({
                'name': gen_string('alpha'),
                'label': gen_string('alpha'),
            })
        session.repository.create(
            product.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': FAKE_1_YUM_REPO,
            }
        )
        assert session.repository.search(
            product.name, repo_name)[0]['Name'] == repo_name


@tier2
@upgrade
def test_positive_discover_repo_via_existing_product(session, module_org):
    """Create repository via repo-discovery under existing product

    :id: 9181950c-a756-456f-a46a-059e7a2add3c

    :expectedresults: Repository is discovered and created

    :CaseLevel: Integration
    """
    repo_name = 'fakerepo01'
    product = entities.Product(organization=module_org).create()
    with session:
        session.organization.select(org_name=module_org.name)
        session.product.discover_repo({
            'repo_type': 'Yum Repositories',
            'url': REPO_DISCOVERY_URL,
            'discovered_repos.repos': repo_name,
            'create_repo.product_type': 'Existing Product',
            'create_repo.product_content.product_name': product.name,
        })
        assert repo_name in session.repository.search(
            product.name, repo_name)[0]['Name']


@tier2
def test_positive_discover_repo_via_new_product(session, module_org):
    """Create repository via repo discovery under new product

    :id: dc5281f8-1a8a-4a17-b746-728f344a1504

    :expectedresults: Repository is discovered and created

    :CaseLevel: Integration
    """
    product_name = gen_string('alpha')
    repo_name = 'fakerepo01'
    with session:
        session.organization.select(org_name=module_org.name)
        session.product.discover_repo({
            'repo_type': 'Yum Repositories',
            'url': REPO_DISCOVERY_URL,
            'discovered_repos.repos': repo_name,
            'create_repo.product_type': 'New Product',
            'create_repo.product_content.product_name': product_name,
        })
        assert session.product.search(
            product_name)[0]['Name'] == product_name
        assert repo_name in session.repository.search(
            product_name, repo_name)[0]['Name']


@tier2
@upgrade
def test_positive_sync_custom_repo_yum(session, module_org):
    """Create Custom yum repos and sync it via the repos page.

    :id: afa218f4-e97a-4240-a82a-e69538d837a1

    :expectedresults: Sync procedure for specific yum repository is successful

    :CaseLevel: Integration
    """
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(url=FAKE_1_YUM_REPO, product=product).create()
    with session:
        result = session.repository.synchronize(product.name, repo.name)
        assert result['result'] == 'success'


@tier2
@upgrade
def test_positive_sync_custom_repo_puppet(session, module_org):
    """Create Custom puppet repos and sync it via the repos page.

    :id: 135176cc-7664-41ee-8c41-b77e193f2f22

    :expectedresults: Sync procedure for specific puppet repository is
        successful

    :CaseLevel: Integration
    """
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(
        url=FAKE_0_PUPPET_REPO,
        product=product,
        content_type=REPO_TYPE['puppet'],
    ).create()
    with session:
        result = session.repository.synchronize(product.name, repo.name)
        assert result['result'] == 'success'


@tier2
@upgrade
def test_positive_sync_custom_repo_docker(session, module_org):
    """Create Custom docker repos and sync it via the repos page.

    :id: 942e0b4f-3524-4f00-812d-bdad306f81de

    :expectedresults: Sync procedure for specific docker repository is
        successful

    :CaseLevel: Integration
    """
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(
        url=DOCKER_REGISTRY_HUB,
        product=product,
        content_type=REPO_TYPE['docker'],
    ).create()
    with session:
        result = session.repository.synchronize(product.name, repo.name)
        assert result['result'] == 'success'
