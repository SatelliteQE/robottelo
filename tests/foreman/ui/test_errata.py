"""UI Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ErrataManagement

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from airgun.session import Session
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import promote
from robottelo.constants import (
    DISTRO_RHEL6,
    DISTRO_RHEL7,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_3_ERRATA_ID,
    FAKE_3_YUM_REPO,
    FAKE_6_YUM_REPO,
    PRDS,
    REAL_0_RH_PACKAGE,
    REAL_4_ERRATA_ID,
    REAL_4_ERRATA_CVES,
)
from robottelo.decorators import (
    fixture,
    run_in_one_thread,
    tier2,
    tier3,
    upgrade
)
from robottelo.manifests import upload_manifest_locked
from robottelo.products import (
    RHELAnsibleEngineRepository,
    YumRepository,
    RepositoryCollection,
    SatelliteToolsRepository,
    VirtualizationAgentsRepository,
)
from robottelo.vm import VirtualMachine

CUSTOM_REPO_URL = FAKE_6_YUM_REPO
CUSTOM_REPO_ERRATA_ID = FAKE_2_ERRATA_ID

RHVA_PACKAGE = REAL_0_RH_PACKAGE
RHVA_ERRATA_ID = REAL_4_ERRATA_ID
RHVA_ERRATA_CVES = REAL_4_ERRATA_CVES

pytestmark = [run_in_one_thread]


def _generate_errata_applicability(host_name):
    """Force host to generate errata applicability"""
    host = entities.Host().search(query={'search': 'name={0}'.format(host_name)})[0].read()
    host.errata_applicability()


def _install_client_package(client, package, errata_applicability=False):
    """Install a package in virtual machine client.

    :param client: The Virtual machine client.
    :param package: the package to install in virtual machine client.
    :param errata_applicability: If True, force host to generate errata applicability.
    :returns: whether package installed successfully
    """
    result = client.run('yum install -y {0}'.format(package))
    if errata_applicability:
        _generate_errata_applicability(client.hostname)
    return not result.return_code


def _set_setting_value(setting_entity, value):
    """Set setting value.

    :param setting_entity: the setting entity instance.
    :param value: The setting value to set.
    """
    setting_entity.value = value
    setting_entity.update(['value'])


@fixture(scope='module')
def module_org():
    org = entities.Organization().create()
    upload_manifest_locked(org.id)
    return org


@fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@fixture(scope='module')
def module_repos_col(module_org, module_lce):
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7,
        repositories=[
            SatelliteToolsRepository(),
            # As Satellite Tools may be added as custom repo and to have a "Fully entitled" host,
            # force the host to consume an RH product with adding a cdn repo.
            RHELAnsibleEngineRepository(cdn=True),
            YumRepository(url=CUSTOM_REPO_URL),
        ]
    )
    repos_collection.setup_content(module_org.id, module_lce.id)
    return repos_collection


@fixture
def vm(module_repos_col):
    """Virtual machine client using module_repos_col for subscription"""
    with VirtualMachine(distro=module_repos_col.distro) as client:
        module_repos_col.setup_virtual_machine(client)
        yield client


@fixture(scope='module')
def module_rhva_repos_col(module_org, module_lce):
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL6,
        repositories=[
            SatelliteToolsRepository(),
            YumRepository(url=CUSTOM_REPO_URL),
            VirtualizationAgentsRepository(cdn=True),
        ]
    )
    repos_collection.setup_content(module_org.id, module_lce.id)
    return repos_collection


@fixture
def rhva_vm(module_rhva_repos_col):
    """Virtual machine client using module_rhva_repos_col for subscription"""
    with VirtualMachine(distro=module_rhva_repos_col.distro) as client:
        module_rhva_repos_col.setup_virtual_machine(client)
        yield client


@fixture
def errata_status_installable():
    """Fixture to allow restoring errata_status_installable setting after usage"""
    errata_status_installable = entities.Setting().search(
        query={'search': 'name="errata_status_installable"'})[0]
    original_value = errata_status_installable.value
    yield errata_status_installable
    _set_setting_value(errata_status_installable, original_value)


@tier3
def test_end_to_end(session, module_repos_col, vm):
    """Create all entities required for errata, set up applicable host,
    read errata details and apply it to host

    :id: a26182fc-f31a-493f-b094-3f5f8d2ece47

    :expectedresults: Errata details are the same as expected, errata
        installation is successful

    :CaseLevel: System
    """
    ERRATA_DETAILS = {
        'advisory': 'RHEA-2012:0055',
        'cves': 'N/A',
        'type': 'Security Advisory',
        'severity': 'N/A',
        'issued': 'Jan 27, 12:00 AM',
        'last_updated_on': 'Jan 27, 12:00 AM',
        'reboot_suggested': 'No',
        'topic': '',
        'description': 'Sea_Erratum',
        'solution': '',
    }
    ERRATA_PACKAGES = {
        'independent_packages': [
            'penguin-0.9.1-1.noarch',
            'shark-0.1-1.noarch',
            'walrus-5.21-1.noarch'
        ],
        'module_stream_packages': [],
    }
    assert _install_client_package(vm, FAKE_1_CUSTOM_PACKAGE)
    with session:
        errata = session.errata.read(CUSTOM_REPO_ERRATA_ID)
        assert errata['details'] == ERRATA_DETAILS
        assert (set(errata['packages']['independent_packages'])
                == set(ERRATA_PACKAGES['independent_packages']))
        assert (errata['packages']['module_stream_packages']
                == ERRATA_PACKAGES['module_stream_packages'])
        assert (
            errata['repositories']['table'][0]['Name'] ==
            module_repos_col.custom_repos_info[-1]['name']
        )
        assert (
            errata['repositories']['table'][0]['Product'] ==
            module_repos_col.custom_product['name']
        )
        result = session.errata.install(CUSTOM_REPO_ERRATA_ID, vm.hostname)
        assert result['result'] == 'success'


@tier2
def test_positive_list(session, module_repos_col, module_lce):
    """View all errata in an Org

    :id: 71c7a054-a644-4c1e-b304-6bc34ea143f4

    :Setup: Errata synced on satellite server.

    :Steps: Create two Orgs each having a product synced which contains errata.

    :expectedresults: Check that the errata belonging to one Org is not showing in the other.

    :BZ: 1659941

    :CaseLevel: Integration
    """
    org = entities.Organization().create()
    org_env = entities.LifecycleEnvironment(organization=org).create()
    org_repos_col = RepositoryCollection(repositories=[YumRepository(FAKE_3_YUM_REPO)])
    org_repos_col.setup_content(org.id, org_env.id)
    with session:
        assert (session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)[0]['Errata ID']
                == CUSTOM_REPO_ERRATA_ID)
        assert not session.errata.search(FAKE_3_ERRATA_ID, applicable=False)
        session.organization.select(org_name=org.name)
        assert (session.errata.search(FAKE_3_ERRATA_ID, applicable=False)[0]['Errata ID']
                == FAKE_3_ERRATA_ID)
        assert not session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)


@tier2
def test_positive_list_permission(test_name, module_org, module_repos_col, module_rhva_repos_col):
    """Show errata only if the User has permissions to view them

    :id: cdb28f6a-23df-47a2-88ab-cd3b492126b2

    :Setup:

        1. Create two products with one repo each. Sync them.
        2. Make sure that they both have errata.
        3. Create a user with view access on one product and not on the other.

    :Steps: Go to Content -> Errata.

    :expectedresults: Check that the new user is able to see errata for one
        product only.

    :CaseLevel: Integration
    """
    role = entities.Role().create()
    entities.Filter(
        organization=[module_org],
        permission=entities.Permission(
            resource_type='Katello::Product').search(),
        role=role,
        search='name = "{0}"'.format(PRDS['rhel']),
    ).create()
    user_password = gen_string('alphanumeric')
    user = entities.User(
        default_organization=module_org,
        organization=[module_org],
        role=[role],
        password=user_password,
    ).create()
    with Session(test_name, user=user.login, password=user_password) as session:
        assert (session.errata.search(RHVA_ERRATA_ID, applicable=False)[0]['Errata ID']
                == RHVA_ERRATA_ID)
        assert not session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)


@tier3
@upgrade
def test_positive_apply_for_all_hosts(session, module_org, module_repos_col):
    """Apply an erratum for all content hosts

    :id: d70a1bee-67f4-4883-a0b9-2ccc08a91738

    :Setup: Errata synced on satellite server.

    :customerscenario: true

    :Steps:

        1. Go to Content -> Errata. Select an erratum -> Content Hosts tab.
        2. Select all Content Hosts and apply the erratum.

    :expectedresults: Check that the erratum is applied in all the content
        hosts.

    :CaseLevel: System
    """
    with VirtualMachine(distro=module_repos_col.distro) as client1, VirtualMachine(
            distro=module_repos_col.distro) as client2:
        clients = [client1, client2]
        for client in clients:
            module_repos_col.setup_virtual_machine(client)
            assert _install_client_package(client, FAKE_1_CUSTOM_PACKAGE)
        with session:
            for client in clients:
                task_values = session.errata.install(CUSTOM_REPO_ERRATA_ID, client.hostname)
                assert task_values['result'] == 'success'
                packages_rows = session.contenthost.search_package(
                    client.hostname, FAKE_2_CUSTOM_PACKAGE)
                assert packages_rows[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE


@tier2
@upgrade
def test_positive_view_cve(session, module_repos_col, module_rhva_repos_col):
    """View CVE number(s) in Errata Details page

    :id: e1c2de13-fed8-448e-b618-c2adb6e82a35

    :Setup: Errata synced on satellite server.

    :Steps: Go to Content -> Errata.  Select an Errata.

    :expectedresults:

        1. Check if the CVE information is shown in Errata Details page.
        2. Check if 'N/A' is displayed if CVE information is not present.

    :CaseLevel: Integration
    """
    with session:
        errata_values = session.errata.read(RHVA_ERRATA_ID)
        assert errata_values['details']['cves']
        assert (set([cve.strip() for cve in errata_values['details']['cves'].split(',')])
                == set(RHVA_ERRATA_CVES))
        errata_values = session.errata.read(CUSTOM_REPO_ERRATA_ID)
        assert errata_values['details']['cves'] == 'N/A'


@tier3
@upgrade
def test_positive_filter_by_environment(session, module_org, module_repos_col):
    """Filter Content hosts by environment

    :id: 578c3a92-c4d8-4933-b122-7ff511c276ec

    :customerscenario: true

    :BZ: 1383729

    :Setup: Errata synced on satellite server.

    :Steps: Go to Content -> Errata.  Select an Errata -> Content Hosts tab
        -> Filter content hosts by Environment.

    :expectedresults: Content hosts can be filtered by Environment.

    :CaseLevel: System
    """
    with VirtualMachine(distro=module_repos_col.distro) as client1, VirtualMachine(
            distro=module_repos_col.distro) as client2:
        for client in client1, client2:
            module_repos_col.setup_virtual_machine(client)
            assert _install_client_package(
                client, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
        # Promote the latest content view version to a new lifecycle environment
        content_view = entities.ContentView(
            id=module_repos_col.setup_content_data['content_view']['id']).read()
        content_view_version = content_view.version[-1].read()
        lce = content_view_version.environment[-1].read()
        new_lce = entities.LifecycleEnvironment(organization=module_org, prior=lce).create()
        promote(content_view_version, new_lce.id)
        host = entities.Host().search(
            query={'search': 'name={0}'.format(client1.hostname)})[0].read()
        host.content_facet_attributes = {
            'content_view_id': content_view.id,
            'lifecycle_environment_id': new_lce.id,
        }
        host.update(['content_facet_attributes'])
        with session:
            # search in new_lce
            values = session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, client1.hostname, environment=new_lce.name)
            assert values[0]['Name'] == client1.hostname
            assert not session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, client2.hostname, environment=new_lce.name)
            # search in lce
            values = session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, client2.hostname, environment=lce.name)
            assert values[0]['Name'] == client2.hostname
            assert not session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, client1.hostname, environment=lce.name)


@tier3
@upgrade
def test_positive_content_host_previous_env(session, module_org, module_repos_col, vm):
    """Check if the applicable errata are available from the content
    host's previous environment

    :id: 78110ba8-3942-46dd-8c14-bffa1dbd5195

    :Setup:

        1. Make sure multiple environments are present.
        2. Content host's previous environments have additional errata.

    :Steps: Go to Content Hosts -> Select content host -> Errata Tab ->
        Select Previous environments.

    :expectedresults: The errata from previous environments are displayed.

    :CaseLevel: System
    """
    host_name = vm.hostname
    assert _install_client_package(vm, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
    # Promote the latest content view version to a new lifecycle environment
    content_view = entities.ContentView(
        id=module_repos_col.setup_content_data['content_view']['id']).read()
    content_view_version = content_view.version[-1].read()
    lce = content_view_version.environment[-1].read()
    new_lce = entities.LifecycleEnvironment(organization=module_org, prior=lce).create()
    promote(content_view_version, new_lce.id)
    host = entities.Host().search(query={'search': 'name={0}'.format(host_name)})[0].read()
    host.content_facet_attributes = {
        'content_view_id': content_view.id,
        'lifecycle_environment_id': new_lce.id,
    }
    host.update(['content_facet_attributes'])
    with session:
        environment = 'Previous Lifecycle Environment ({0}/{1})'.format(
            lce.name, content_view.name)
        content_host_erratum = session.contenthost.search_errata(
            host_name, CUSTOM_REPO_ERRATA_ID, environment=environment)
        assert content_host_erratum[0]['Id'] == CUSTOM_REPO_ERRATA_ID


@tier3
def test_positive_content_host_library(session, module_org, vm):
    """Check if the applicable errata are available from the content
    host's Library

    :id: 4e627410-b7b8-471b-b9b4-a18e77fdd3f8

    :Setup:

        1. Make sure multiple environments are present.
        2. Content host's Library environment has additional errata.

    :Steps: Go to Content Hosts -> Select content host -> Errata Tab -> Select 'Library'.

    :expectedresults: The errata from Library are displayed.

    :CaseLevel: System
    """
    host_name = vm.hostname
    assert _install_client_package(vm, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
    with session:
        content_host_erratum = session.contenthost.search_errata(
            host_name, CUSTOM_REPO_ERRATA_ID, environment='Library Synced Content')
        assert content_host_erratum[0]['Id'] == CUSTOM_REPO_ERRATA_ID


@tier3
def test_positive_show_count_on_content_host_page(session, module_org, rhva_vm):
    """Available errata count displayed in Content hosts page

    :id: 8575e282-d56e-41dc-80dd-f5f6224417cb

    :Setup:

        1. Errata synced on satellite server.
        2. Some content hosts are present.

    :Steps: Go to Hosts -> Content Hosts.

    :expectedresults: The available errata count is displayed.

    :BZ: 1484044

    :CaseLevel: System
    """
    host_name = rhva_vm.hostname
    with session:
        content_host_values = session.contenthost.search(host_name)
        assert content_host_values[0]['Name'] == host_name
        installable_errata = content_host_values[0]['Installable Updates']['errata']
        for errata_type in ('security', 'bug_fix', 'enhancement'):
            assert int(installable_errata[errata_type]) == 0
        assert _install_client_package(rhva_vm, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
        content_host_values = session.contenthost.search(host_name)
        assert content_host_values[0]['Name'] == host_name
        assert int(content_host_values[0]['Installable Updates']['errata']['security']) == 1
        assert _install_client_package(rhva_vm, RHVA_PACKAGE, errata_applicability=True)
        content_host_values = session.contenthost.search(host_name)
        assert content_host_values[0]['Name'] == host_name
        installable_errata = content_host_values[0]['Installable Updates']['errata']
        for errata_type in ('bug_fix', 'enhancement'):
            assert int(installable_errata[errata_type]) == 1


@tier3
def test_positive_show_count_on_content_host_details_page(session, module_org, rhva_vm):
    """Errata count on Content host Details page

    :id: 388229da-2b0b-41aa-a457-9b5ecbf3df4b

    :Setup:

        1. Errata synced on satellite server.
        2. Some content hosts are present.

    :Steps: Go to Hosts -> Content Hosts -> Select Content Host -> Details page.

    :expectedresults: The errata section should be displayed with Security, Bug fix, Enhancement.

    :BZ: 1484044

    :CaseLevel: System
    """
    host_name = rhva_vm.hostname
    with session:
        content_host_values = session.contenthost.read(host_name, 'details')
        for errata_type in ('security', 'bug_fix', 'enhancement'):
            assert int(content_host_values['details'][errata_type]) == 0
        assert _install_client_package(rhva_vm, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
        # navigate to content host main page by making a search, to refresh the details page
        session.contenthost.search(host_name)
        content_host_values = session.contenthost.read(host_name, 'details')
        assert int(content_host_values['details']['security']) == 1
        assert _install_client_package(rhva_vm, RHVA_PACKAGE, errata_applicability=True)
        # navigate to content host main page by making a search, to refresh the details page
        session.contenthost.search(host_name)
        content_host_values = session.contenthost.read(host_name, 'details')
        for errata_type in ('bug_fix', 'enhancement'):
            assert int(content_host_values['details'][errata_type]) == 1


@tier3
@upgrade
def test_positive_filtered_errata_status_installable_param(session, errata_status_installable):
    """Filter errata for specific content view and verify that host that
    was registered using that content view has different states in
    correspondence to filtered errata and `errata status installable`
    settings flag value

    :id: ed94cf34-b8b9-4411-8edc-5e210ea6af4f

    :Steps:

        1. Prepare setup: Create Lifecycle Environment, Content View,
            Activation Key and all necessary repos
        2. Register Content Host using created data
        3. Create necessary Content View Filter and Rule for repository errata
        4. Publish and Promote Content View to a new version.
        5. Go to created Host page and check its properties
        6. Change 'errata status installable' flag in the settings and
            check host properties once more

    :expectedresults: Check that 'errata status installable' flag works as intended

    :BZ: 1368254

    :CaseLevel: System
    """
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7,
        repositories=[
            SatelliteToolsRepository(),
            # As Satellite Tools may be added as custom repo and to have a "Fully entitled" host,
            # force the host to consume an RH product with adding a cdn repo.
            RHELAnsibleEngineRepository(cdn=True),
            YumRepository(url=CUSTOM_REPO_URL),
        ]
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    with VirtualMachine(distro=repos_collection.distro) as client:
        repos_collection.setup_virtual_machine(client)
        assert _install_client_package(client, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
        # Adding content view filter and content view filter rule to exclude errata for the
        # installed package.
        content_view = entities.ContentView(
            id=repos_collection.setup_content_data['content_view']['id']).read()
        cv_filter = entities.ErratumContentViewFilter(
            content_view=content_view, inclusion=False).create()
        errata = entities.Errata(content_view_version=content_view.version[-1]).search(
            query=dict(search='errata_id="{0}"'.format(CUSTOM_REPO_ERRATA_ID)))[0]
        entities.ContentViewFilterRule(content_view_filter=cv_filter, errata=errata).create()
        content_view.publish()
        content_view = content_view.read()
        content_view_version = content_view.version[-1]
        promote(content_view_version, lce.id)
        with session:
            session.organization.select(org_name=org.name)
            _set_setting_value(errata_status_installable, True)
            expected_values = {
                'Status': 'OK',
                'Errata': 'All errata applied',
                'Subscription': 'Fully entitled',
            }
            host_details_values = session.host.get_details(client.hostname)
            actual_values = {
                key: value
                for key, value in host_details_values['properties']['properties_table'].items()
                if key in expected_values
            }
            assert actual_values == expected_values
            _set_setting_value(errata_status_installable, False)
            expected_values = {
                'Status': 'Error',
                'Errata': 'Security errata applicable',
                'Subscription': 'Fully entitled',
            }
            # navigate to host main page by making a search, to refresh the host details page
            session.host.search(client.hostname)
            host_details_values = session.host.get_details(client.hostname)
            actual_values = {
                key: value
                for key, value in host_details_values['properties']['properties_table'].items()
                if key in expected_values
            }
            assert actual_values == expected_values
