"""Test class for Lifecycle Environment UI

:Requirement: Lifecycleenvironment

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from nailgun import entities


from robottelo.constants import (
    ENVIRONMENT,
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_0_PUPPET_REPO,
    FAKE_0_YUM_REPO,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_2_CUSTOM_PACKAGE,
    REPO_TYPE,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    fixture,
    skip_if_bug_open,
    tier2,
    tier3,
    upgrade,
)


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


def test_positive_edit(session):
    lce_path_name = gen_string('alpha')
    new_name = gen_string('alpha')
    with session:
        session.lifecycleenvironment.create(
            values={'name': lce_path_name}
        )
        session.lifecycleenvironment.update(
            values={'details.name': new_name},
            entity_name=lce_path_name,
        )
        lce_values = session.lifecycleenvironment.read_all()
        assert new_name in lce_values['lce']


@upgrade
@tier2
def test_positive_create_chain(session):
    """Create Content Environment in a chain

    :id: ed3d2c88-ef0a-4a1a-9f11-5bdb2119fc18

    :expectedresults: Environment is created

    :CaseLevel: Integration
    """
    lce_path_name = gen_string('alpha')
    lce_name = gen_string('alpha')
    with session:
        session.lifecycleenvironment.create(
            values={'name': lce_path_name}
        )
        session.lifecycleenvironment.create(
            values={'name': lce_name},
            prior_entity_name=lce_path_name,
        )
        lce_values = session.lifecycleenvironment.read_all()
        assert lce_name in lce_values['lce']
        assert lce_path_name in lce_values['lce'][lce_name]


@tier2
@upgrade
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
        product=product,
        content_type=REPO_TYPE['puppet'],
        url=FAKE_0_PUPPET_REPO
    ).create()
    repo.sync()
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    cv = entities.ContentView(organization=module_org).create()
    with session:
        session.contentview.add_puppet_module(cv.name, puppet_module)
        session.contentview.publish(cv.name)
        result = session.contentview.promote(cv.name, 'Version 1.0', lce.name)
        assert 'Promoted to {}'.format(lce.name) in result['Status']
        lce = session.lifecycleenvironment.read(lce.name)
        assert lce['puppet_modules']['table'][0]['Name'] == puppet_module


@skip_if_bug_open('bugzilla', 1432155)
@tier3
def test_positive_search_lce_content_view_packages_by_full_name(
        session, module_org):
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
        {'name': FAKE_0_CUSTOM_PACKAGE_NAME,
         'full_names': [FAKE_0_CUSTOM_PACKAGE]},
        {'name': FAKE_1_CUSTOM_PACKAGE_NAME,
         'full_names': [FAKE_1_CUSTOM_PACKAGE, FAKE_2_CUSTOM_PACKAGE]},
    ]
    product = entities.Product(organization=module_org).create()
    repository = entities.Repository(
        product=product, url=FAKE_0_YUM_REPO).create()
    repository.sync()
    content_view = entities.ContentView(
        organization=module_org, repository=[repository]).create()
    content_view.publish()
    with session:
        for package in packages:
            for package_full_name in package['full_names']:
                result = session.lifecycleenvironment.search_package(
                    ENVIRONMENT, package_full_name, cv_name=content_view.name)
                assert len(result) == 1
                assert result[0]['Name'] == package['name']


@skip_if_bug_open('bugzilla', 1432155)
@tier3
def test_positive_search_lce_content_view_packages_by_name(
        session, module_org):
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
        {'name': FAKE_0_CUSTOM_PACKAGE_NAME,
         'packages_count': 1},
        {'name': FAKE_1_CUSTOM_PACKAGE_NAME,
         'packages_count': 2},
    ]
    product = entities.Product(organization=module_org).create()
    repository = entities.Repository(
        product=product, url=FAKE_0_YUM_REPO).create()
    repository.sync()
    content_view = entities.ContentView(
        organization=module_org, repository=[repository]).create()
    content_view.publish()
    with session:
        for package in packages:
            result = session.lifecycleenvironment.search_package(
                ENVIRONMENT, package['name'], cv_name=content_view.name)
            assert len(result) == package['packages_count']
            for entry in result:
                assert entry['Name'].startswith(package['name'])
