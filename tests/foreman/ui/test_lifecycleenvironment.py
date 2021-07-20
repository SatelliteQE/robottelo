"""Test class for Lifecycle Environment UI

:Requirement: Lifecycleenvironment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: LifecycleEnvironments

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from airgun.session import Session
from nailgun import entities
from navmazing import NavigationTriesExceeded

from robottelo.api.utils import create_role_permissions
from robottelo.config import settings
from robottelo.constants import ENVIRONMENT
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_3_CUSTOM_PACKAGE_NAME
from robottelo.constants import REPO_TYPE
from robottelo.datafactory import gen_string


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_end_to_end(session):
    """Perform end to end testing for lifecycle environment component

    :id: b2293de9-7a71-462e-b988-321b07c01642

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    lce_name = gen_string('alpha')
    new_lce_name = gen_string('alpha')
    label = gen_string('alpha')
    description = gen_string('alpha')
    with session:
        # Create new lce
        session.lifecycleenvironment.create(
            {'name': lce_name, 'label': label, 'description': description}
        )
        lce_values = session.lifecycleenvironment.read(lce_name)
        assert lce_values['details']['name'] == lce_name
        assert lce_values['details']['label'] == label
        assert lce_values['details']['description'] == description
        assert lce_values['details']['unauthenticated_pull'] == 'No'
        # Update lce with new name
        session.lifecycleenvironment.update(lce_name, {'details.name': new_lce_name})
        lce_values = session.lifecycleenvironment.read_all()
        assert new_lce_name in lce_values['lce']
        assert lce_name not in lce_values['lce']
        # Delete lce
        session.lifecycleenvironment.delete(new_lce_name)
        lce_values = session.lifecycleenvironment.read_all()
        assert new_lce_name not in lce_values['lce']


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_create_chain(session):
    """Create Content Environment in a chain

    :id: ed3d2c88-ef0a-4a1a-9f11-5bdb2119fc18

    :expectedresults: Environment is created

    :CaseLevel: Integration
    """
    lce_path_name = gen_string('alpha')
    lce_name = gen_string('alpha')
    with session:
        session.lifecycleenvironment.create(values={'name': lce_path_name})
        session.lifecycleenvironment.create(
            values={'name': lce_name}, prior_entity_name=lce_path_name
        )
        lce_values = session.lifecycleenvironment.read_all()
        assert lce_name in lce_values['lce']
        assert lce_path_name in lce_values['lce'][lce_name]


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_add_puppet_module(session, module_org):
    """Promote content view with puppet module to a new environment

    :id: 12bed99d-8f96-48ca-843a-b77e123e8e2e

    :steps:
        1. Create Product/puppet repo and sync it
        2. Create CV and add puppet module from created repo
        3. Publish and promote CV to new environment

    :expectedresults: Puppet modules can be listed successfully from lifecycle
        environment interface

    :BZ: 1408264

    :CaseLevel: Integration
    """
    puppet_module = 'httpd'
    product = entities.Product(organization=module_org).create()
    repo = entities.Repository(
        product=product, content_type=REPO_TYPE['puppet'], url=settings.repos.puppet_0.url
    ).create()
    repo.sync()
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    cv = entities.ContentView(organization=module_org).create()
    with session:
        session.contentview.add_puppet_module(cv.name, puppet_module)
        session.contentview.publish(cv.name)
        result = session.contentview.promote(cv.name, 'Version 1.0', lce.name)
        assert f'Promoted to {lce.name}' in result['Status']
        lce = session.lifecycleenvironment.search_puppet_module(
            lce.name, puppet_module, cv_name=cv.name
        )
        assert lce[0]['Name'] == puppet_module


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_search_lce_content_view_packages_by_full_name(session, module_org):
    """Search Lifecycle Environment content view packages by full name

    Note: if package full name looks like "bear-4.1-1.noarch",
        eg. name-version-release-arch, the package name is "bear"

    :id: fad05fe9-b673-4384-b65a-926d4a0d2598

    :customerscenario: true

    :steps:
        1. Create a product with a repository synchronized
            - The repository must contain at least two package names P1 and
              P2
            - P1 has only one package
            - P2 has two packages
        2. Create a content view with the repository and publish it
        3. Go to Lifecycle Environment > Library > Packages
        4. Select the content view
        5. Search by packages using full names

    :expectedresults: only the searched packages where found

    :BZ: 1432155

    :CaseLevel: System
    """
    packages = [
        {'name': FAKE_0_CUSTOM_PACKAGE_NAME, 'full_names': [FAKE_0_CUSTOM_PACKAGE]},
        {
            'name': FAKE_1_CUSTOM_PACKAGE_NAME,
            'full_names': [FAKE_1_CUSTOM_PACKAGE, FAKE_2_CUSTOM_PACKAGE],
        },
    ]
    product = entities.Product(organization=module_org).create()
    repository = entities.Repository(product=product, url=settings.repos.yum_0.url).create()
    repository.sync()
    content_view = entities.ContentView(organization=module_org, repository=[repository]).create()
    content_view.publish()
    with session:
        for package in packages:
            for package_full_name in package['full_names']:
                result = session.lifecycleenvironment.search_package(
                    ENVIRONMENT, package_full_name, cv_name=content_view.name
                )
                assert len(result) == 1
                assert result[0]['Name'] == package['name']


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_search_lce_content_view_packages_by_name(session, module_org):
    """Search Lifecycle Environment content view packages by name

    Note: if package full name looks like "bear-4.1-1.noarch",
        eg. name-version-release-arch, the package name is "bear"

    :id: f8dec2a8-8971-44ad-a4d5-1eb5d2eb62f6

    :customerscenario: true

    :steps:
        1. Create a product with a repository synchronized
            - The repository must contain at least two package names P1 and
              P2
            - P1 has only one package
            - P2 has two packages
        2. Create a content view with the repository and publish it
        3. Go to Lifecycle Environment > Library > Packages
        4. Select the content view
        5. Search by package names

    :expectedresults: only the searched packages where found

    :BZ: 1432155

    :CaseLevel: System
    """
    packages = [
        {'name': FAKE_0_CUSTOM_PACKAGE_NAME, 'packages_count': 1},
        {'name': FAKE_1_CUSTOM_PACKAGE_NAME, 'packages_count': 2},
    ]
    product = entities.Product(organization=module_org).create()
    repository = entities.Repository(product=product, url=settings.repos.yum_0.url).create()
    repository.sync()
    content_view = entities.ContentView(organization=module_org, repository=[repository]).create()
    content_view.publish()
    with session:
        for package in packages:
            result = session.lifecycleenvironment.search_package(
                ENVIRONMENT, package['name'], cv_name=content_view.name
            )
            assert len(result) == package['packages_count']
            for entry in result:
                assert entry['Name'].startswith(package['name'])


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_search_lce_content_view_module_streams_by_name(session, module_org):
    """Search Lifecycle Environment content view module streams by name

    :id: e67893b2-a56e-4eac-87e6-63be897ba912

    :customerscenario: true

    :steps:
        1. Create a product with a repository synchronized
            - The repository must contain at least two module stream names P1 and
              P2
            - P1 has two module streams
            - P2 has three module streams
        2. Create a content view with the repository and publish it
        3. Go to Lifecycle Environment > Library > ModuleStreams
        4. Select the content view
        5. Search by module stream names

    :expectedresults: only the searched module streams where found

    :CaseLevel: System
    """
    module_streams = [
        {'name': FAKE_1_CUSTOM_PACKAGE_NAME, 'streams_count': 2},
        {'name': FAKE_3_CUSTOM_PACKAGE_NAME, 'streams_count': 3},
    ]
    product = entities.Product(organization=module_org).create()
    repository = entities.Repository(
        product=product, url=settings.repos.module_stream_1.url
    ).create()
    repository.sync()
    content_view = entities.ContentView(organization=module_org, repository=[repository]).create()
    content_view.publish()
    with session:
        for module in module_streams:
            result = session.lifecycleenvironment.search_module_stream(
                ENVIRONMENT, module['name'], cv_name=content_view.name
            )
            assert len(result) == module['streams_count']
            for entry in result:
                assert entry['Name'].startswith(module['name'])


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_custom_user_view_lce(session, test_name):
    """As a custom user attempt to view a lifecycle environment created
    by admin user

    :id: 768b647b-c530-4eca-9caa-38cf8622f36d

    :BZ: 1420511

    :Steps:

        As an admin user:

        1. Create an additional lifecycle environments other than Library
        2. Create a user without administrator privileges
        3. Create a role with the the following permissions:

            * (Miscellaneous): access_dashboard
            * Lifecycle Environment:

            * edit_lifecycle_environments
            * promote_or_remove_content_views_to_environment
            * view_lifecycle_environments

            * Location: view_locations
            * Organization: view_organizations

        4. Assign the created role to the custom user

        As a custom user:

        1. Log in
        2. Navigate to Content -> Lifecycle Environments

    :expectedresults: The additional lifecycle environment is viewable and
        accessible by the custom user.

    :CaseLevel: Integration
    """
    role_name = gen_string('alpha')
    lce_name = gen_string('alpha')
    user_login = gen_string('alpha')
    user_password = gen_string('alpha')
    org = entities.Organization().create()
    role = entities.Role(name=role_name).create()
    permissions_types_names = {
        None: ['access_dashboard'],
        'Organization': ['view_organizations'],
        'Location': ['view_locations'],
        'Katello::KTEnvironment': [
            'view_lifecycle_environments',
            'edit_lifecycle_environments',
            'promote_or_remove_content_views_to_environments',
        ],
    }
    create_role_permissions(role, permissions_types_names)
    entities.User(
        default_organization=org,
        organization=[org],
        role=[role],
        login=user_login,
        password=user_password,
    ).create()
    # create a life cycle environment as admin user and ensure it's visible
    with session:
        session.organization.select(org.name)
        session.lifecycleenvironment.create(values={'name': lce_name})
        lce_values = session.lifecycleenvironment.read_all()
        assert lce_name in lce_values['lce']
    # ensure the created user also can find the created lifecycle environment link
    with Session(test_name, user_login, user_password) as non_admin_session:
        # to ensure that the created user has only the assigned
        # permissions, check that hosts menu tab does not exist
        with pytest.raises(NavigationTriesExceeded):
            assert not non_admin_session.host.read_all()
        # assert that the user can view the lvce created by admin user
        lce_values = non_admin_session.lifecycleenvironment.read_all()
        assert lce_name in lce_values['lce']
