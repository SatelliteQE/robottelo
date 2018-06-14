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
    FAKE_1_PUPPET_REPO,
    FAKE_1_YUM_REPO,
    FAKE_2_YUM_REPO,
    FAKE_8_PUPPET_REPO,
    INVALID_URL,
    REPO_DISCOVERY_URL,
    REPO_TYPE,
)


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_prod(module_org):
    return entities.Product(organization=module_org).create()


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
def test_positive_create_puppet_repo_same_url_different_orgs(
        session, module_prod):
    """Create two repos with the same URL in two different organizations.

    :id: f4cb00ed-6faf-4c79-9f66-76cd333299cb

    :expectedresults: Repositories are created and puppet modules are visible
        from different organizations.

    :CaseLevel: Integration
    """
    # Create first repository
    repo = entities.Repository(
        url=FAKE_8_PUPPET_REPO,
        product=module_prod,
        content_type=REPO_TYPE['puppet'],
    ).create()
    repo.sync()
    # Create second repository
    org = entities.Organization().create()
    product = entities.Product(organization=org).create()
    new_repo = entities.Repository(
        url=FAKE_8_PUPPET_REPO,
        product=product,
        content_type=REPO_TYPE['puppet'],
    ).create()
    new_repo.sync()
    with session:
        # Check packages number in first repository
        assert session.repository.search(
            module_prod.name, repo.name)[0]['Name'] == repo.name
        repo = session.repository.read(module_prod.name, repo.name)
        assert repo['content_counts']['Puppet Modules'] == '1'
        # Check packages number in first repository
        session.organization.select(org.name)
        assert session.repository.search(
            product.name, new_repo.name)[0]['Name'] == new_repo.name
        new_repo = session.repository.read(product.name, new_repo.name)
        assert new_repo['content_counts']['Puppet Modules'] == '1'


@tier2
@upgrade
def test_positive_create_as_non_admin_user_with_cv_published(
        module_org, module_prod, test_name):
    """Create a repository as a non admin user in a product that already
    contain a repository that is used in a published content view.

    :id: 407864eb-50b8-4bc8-bbc7-0e6f8136d89f

    :expectedresults: New repository successfully created by non admin user

    :BZ: 1447829

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
    repo = entities.Repository(
        product=module_prod, url=FAKE_2_YUM_REPO).create()
    repo.sync()
    content_view = entities.ContentView(organization=module_org).create()
    content_view.repository = [repo]
    content_view = content_view.update(['repository'])
    content_view.publish()
    with Session(test_name, user_login, user_password) as session:
        # ensure that the created user is not a global admin user
        # check administer->users page
        with raises(NavigationTriesExceeded):
            pswd = gen_string('alphanumeric')
            session.user.create({
                'user.login': gen_string('alphanumeric'),
                'user.auth': 'INTERNAL',
                'user.password': pswd,
                'user.confirm': pswd,
            })
        # ensure that the created user has only the assigned permissions
        # check that host collections menu tab does not exist
        with raises(NavigationTriesExceeded):
            session.hostcollection.create({'name': gen_string('alphanumeric')})
        session.repository.create(
            module_prod.name,
            {
                'name': repo_name,
                'repo_type': REPO_TYPE['yum'],
                'repo_content.upstream_url': FAKE_1_YUM_REPO,
            }
        )
        assert session.repository.search(
            module_prod.name, repo.name)[0]['Name'] == repo.name


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


@tier2
def test_positive_resync_custom_repo_after_invalid_update(session, module_org):
    """Create Custom yum repo and sync it via the repos page. Then try to
    change repo url to invalid one and re-sync that repository

    :id: 089b1e41-2017-429a-9c3f-b0291007a78f

    :customerscenario: true

    :expectedresults: Repository URL is not changed to invalid value and resync
        procedure for specific yum repository is successful

    :BZ: 1487173, 1262313

    :CaseLevel: Integration
    """
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(
        url=FAKE_1_YUM_REPO,
        product=product,
    ).create()
    with session:
        result = session.repository.synchronize(product.name, repo.name)
        assert result['result'] == 'success'
        with raises(AssertionError) as context:
            session.repository.update(
                product.name, repo.name,
                {'repo_content.upstream_url': INVALID_URL}
            )
        assert 'bad URI(is not URI?)' in str(context.value)
        assert session.repository.search(
            product.name, repo.name)[0]['Name'] == repo.name
        repo_values = session.repository.read(product.name, repo.name)
        assert repo_values['repo_content']['upstream_url'] == FAKE_1_YUM_REPO
        result = session.repository.synchronize(product.name, repo.name)
        assert result['result'] == 'success'


@tier2
def test_positive_resynchronize_rpm_repo(session, module_prod):
    """Check that repository content is resynced after packages were removed
    from repository

    :id: dc415563-c9b8-4e3c-9d2a-f4ac251c7d35

    :expectedresults: Repository has updated non-zero package count

    :CaseLevel: Integration

    :BZ: 1318004
    """
    repo = entities.Repository(
        url=FAKE_1_YUM_REPO,
        content_type=REPO_TYPE['yum'],
        product=module_prod,
    ).create()
    with session:
        result = session.repository.synchronize(module_prod.name, repo.name)
        assert result['result'] == 'success'
        # Check packages count
        repo_values = session.repository.read(module_prod.name, repo.name)
        assert int(repo_values['content_counts']['Packages']) >= 1
        # Remove packages
        session.repository.remove_packages(module_prod.name, repo.name)
        repo_values = session.repository.read(module_prod.name, repo.name)
        assert repo_values['content_counts']['Packages'] == '0'
        # Sync it again
        result = session.repository.synchronize(module_prod.name, repo.name)
        assert result['result'] == 'success'
        # Check packages number
        repo_values = session.repository.read(module_prod.name, repo.name)
        assert int(repo_values['content_counts']['Packages']) >= 1


@tier2
def test_positive_resynchronize_puppet_repo(session, module_prod):
    """Check that repository content is resynced after packages were removed
    from repository

    :id: c82dfe9d-aa1c-4922-ab3f-5d66ba8375c5

    :expectedresults: Repository has updated non-zero package count

    :CaseLevel: Integration

    :BZ: 1318004
    """
    repo = entities.Repository(
        url=FAKE_1_PUPPET_REPO,
        content_type=REPO_TYPE['puppet'],
        product=module_prod,
    ).create()
    with session:
        result = session.repository.synchronize(module_prod.name, repo.name)
        assert result['result'] == 'success'
        # Check puppet modules count
        repo_values = session.repository.read(module_prod.name, repo.name)
        assert int(repo_values['content_counts']['Puppet Modules']) >= 1
        # Remove puppet modules
        session.repository.remove_puppet_modules(module_prod.name, repo.name)
        repo_values = session.repository.read(module_prod.name, repo.name)
        assert repo_values['content_counts']['Puppet Modules'] == '0'
        # Sync it again
        result = session.repository.synchronize(module_prod.name, repo.name)
        assert result['result'] == 'success'
        # Check puppet modules number
        repo_values = session.repository.read(module_prod.name, repo.name)
        assert int(repo_values['content_counts']['Puppet Modules']) >= 1
