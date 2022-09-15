"""UI Tests for the errata management feature

:Requirement: Errata

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ErrataManagement

:Assignee: addubey

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from airgun.session import Session
from broker import Broker
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import promote
from robottelo.config import settings
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import FAKE_10_YUM_BUGFIX_ERRATUM
from robottelo.constants import FAKE_10_YUM_BUGFIX_ERRATUM_COUNT
from robottelo.constants import FAKE_11_YUM_ENHANCEMENT_ERRATUM
from robottelo.constants import FAKE_11_YUM_ENHANCEMENT_ERRATUM_COUNT
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_3_YUM_OUTDATED_PACKAGES
from robottelo.constants import FAKE_4_CUSTOM_PACKAGE
from robottelo.constants import FAKE_5_CUSTOM_PACKAGE
from robottelo.constants import FAKE_9_YUM_OUTDATED_PACKAGES
from robottelo.constants import FAKE_9_YUM_SECURITY_ERRATUM
from robottelo.constants import FAKE_9_YUM_SECURITY_ERRATUM_COUNT
from robottelo.constants import PRDS
from robottelo.constants import REAL_0_RH_PACKAGE
from robottelo.constants import REAL_4_ERRATA_CVES
from robottelo.constants import REAL_4_ERRATA_ID
from robottelo.hosts import ContentHost
from robottelo.manifests import upload_manifest_locked


CUSTOM_REPO_URL = settings.repos.yum_9.url
CUSTOM_REPO_ERRATA_ID = settings.repos.yum_9.errata[0]

RHVA_PACKAGE = REAL_0_RH_PACKAGE
RHVA_ERRATA_ID = REAL_4_ERRATA_ID
RHVA_ERRATA_CVES = REAL_4_ERRATA_CVES

pytestmark = [pytest.mark.run_in_one_thread]


def _generate_errata_applicability(hostname):
    """Force host to generate errata applicability"""
    host = entities.Host().search(query={'search': f'name={hostname}'})[0].read()
    host.errata_applicability(synchronous=False)


def _install_client_package(client, package, errata_applicability=False):
    """Install a package in virtual machine client.

    :param client: The Virtual machine client.
    :param package: the package to install in virtual machine client.
    :param errata_applicability: If True, force host to generate errata applicability.
    :returns: True if package installed successfully, False otherwise.
    """
    result = client.execute(f'yum install -y {package}')
    if errata_applicability:
        _generate_errata_applicability(client.hostname)
    return result.status == 0


def _set_setting_value(setting_entity, value):
    """Set setting value.

    :param setting_entity: the setting entity instance.
    :param value: The setting value to set.
    """
    setting_entity.value = value
    setting_entity.update(['value'])


def _org():
    org = entities.Organization().create()
    # adding remote_execution_connect_by_ip=Yes at org level
    entities.Parameter(
        name='remote_execution_connect_by_ip',
        parameter_type='boolean',
        value='Yes',
        organization=org.id,
    ).create()
    upload_manifest_locked(org.id)
    return org


@pytest.fixture(scope='module')
def module_org():
    return _org()


@pytest.fixture
def org():
    return _org()


@pytest.fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@pytest.fixture
def lce(org):
    return entities.LifecycleEnvironment(organization=org).create()


@pytest.fixture
def erratatype_vm(module_repos_collection_with_setup, target_sat):
    """Virtual machine client using module_repos_collection_with_setup for subscription"""
    with Broker(
        nick=module_repos_collection_with_setup.distro, host_classes={'host': ContentHost}
    ) as client:
        module_repos_collection_with_setup.setup_virtual_machine(client)
        yield client


@pytest.fixture
def errata_status_installable():
    """Fixture to allow restoring errata_status_installable setting after usage"""
    errata_status_installable = entities.Setting().search(
        query={'search': 'name="errata_status_installable"'}
    )[0]
    original_value = errata_status_installable.value
    yield errata_status_installable
    _set_setting_value(errata_status_installable, original_value)


@pytest.fixture(scope='function')
def vm(module_repos_collection_with_setup, rhel7_contenthost, target_sat):
    """Virtual machine registered in satellite"""
    module_repos_collection_with_setup.setup_virtual_machine(rhel7_contenthost)
    rhel7_contenthost.add_rex_key(satellite=target_sat)
    yield rhel7_contenthost


@pytest.mark.tier3
@pytest.mark.parametrize('setting_update', ['remote_execution_by_default'], indirect=True)
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'RHELAnsibleEngineRepository': {},
            'YumRepository': {'url': CUSTOM_REPO_URL},
        }
    ],
    indirect=True,
)
def test_end_to_end(
    session, module_org, module_repos_collection_with_setup, vm, target_sat, setting_update
):
    """Create all entities required for errata, set up applicable host,
    read errata details and apply it to host

    :id: a26182fc-f31a-493f-b094-3f5f8d2ece47

    :expectedresults: Errata details are the same as expected, errata
        installation is successful

    :parametrized: yes

    :BZ: 2029192

    :customerscenario: true

    :CaseLevel: System
    """
    ERRATA_DETAILS = {
        'advisory': 'RHSA-2012:0055',
        'cves': 'N/A',
        'type': 'Security Advisory',
        'severity': 'N/A',
        'reboot_suggested': 'No',
        'topic': '',
        'description': 'Sea_Erratum',
        'solution': '',
    }
    ERRATA_PACKAGES = {
        'independent_packages': [
            'penguin-0.9.1-1.noarch',
            'shark-0.1-1.noarch',
            'walrus-5.21-1.noarch',
        ],
        'module_stream_packages': [],
    }
    assert _install_client_package(vm, FAKE_1_CUSTOM_PACKAGE)
    with session:
        property_value = 'Yes'
        session.settings.update(f'name = {setting_update.name}', property_value)  # BZ 2029192
        # Check selection box function for BZ#1688636
        session.location.select(loc_name=DEFAULT_LOC)
        assert session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=True)[0]['Errata ID']
        assert session.errata.search(CUSTOM_REPO_ERRATA_ID, installable=True)[0]['Errata ID']
        # Check all tabs of Errata Details page
        errata = session.errata.read(CUSTOM_REPO_ERRATA_ID)
        # We ignore issued date and updated date in ERRATA_DETAILS, so we don't perform an
        # equality check here.
        # TODO: Find a way to account for browser time zone, so that the errata dates displayed
        # in the UI can be compared to the UTC values in ERRATA_DETAILS.
        assert (
            not ERRATA_DETAILS.items() - errata['details'].items()
        ), 'Errata details do not match expected values.'
        assert set(errata['packages']['independent_packages']) == set(
            ERRATA_PACKAGES['independent_packages']
        )
        assert (
            errata['packages']['module_stream_packages']
            == ERRATA_PACKAGES['module_stream_packages']
        )
        assert (
            errata['repositories']['table'][-1]['Name']
            == module_repos_collection_with_setup.custom_repos_info[-1]['name']
        )
        assert (
            errata['repositories']['table'][-1]['Product']
            == module_repos_collection_with_setup.custom_product['name']
        )
        status = session.contenthost.install_errata(
            vm.hostname, CUSTOM_REPO_ERRATA_ID, install_via='rex'
        )
        assert status['overview']['job_status'] == 'Success'
        assert status['overview']['job_status_progress'] == '100%'
        _generate_errata_applicability(vm.hostname)
        vm = vm.nailgun_host.read()
        assert vm.content_facet_attributes['errata_counts']['total'] == 0


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_content_host_errata_page_pagination(session, org, lce, target_sat):
    """
    # Test per-page pagination for BZ#1662254
    # Test apply by REX using Select All for BZ#1846670

    :id: 6363eda7-a162-4a4a-b70f-75decbd8202e

    :Steps:
        1. Install more than 20 packages that need errata
        2. View Content Host's Errata page
        3. Assert total_pages > 1
        4. Change per-page setting to 100
        5. Assert table has more than 20 errata
        6. Use the selection box on the left to select all on the page.
            The following is displayed at the top of the table:
            All 20 items on this page are selected. Select all YYY.

        7. Click the "Select all" text and assert more than 20 results are selected.
        8. Click the drop down arrow to the right of "Apply Selected", and select
            "via remote execution"
        9. Click Submit
        10. Assert Errata are applied as expected.

    :expectedresults: More than page of errata can be selected and applied using REX while
        changing per-page settings.

    :customerscenario: true

    :BZ: 1662254, 1846670

    :CaseLevel: System
    """

    pkgs = ' '.join(FAKE_3_YUM_OUTDATED_PACKAGES)
    repos_collection = target_sat.cli_factory.RepositoryCollection(
        distro='rhel7',
        repositories=[
            target_sat.cli_factory.SatelliteToolsRepository(),
            target_sat.cli_factory.YumRepository(url=settings.repos.yum_3.url),
        ],
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    with Broker(nick=repos_collection.distro, host_classes={'host': ContentHost}) as client:
        client.add_rex_key(satellite=target_sat)
        # Add repo and install packages that need errata
        repos_collection.setup_virtual_machine(client)
        assert _install_client_package(client, pkgs)
        with session:
            # Go to content host's Errata tab and read the page's pagination widgets
            session.organization.select(org_name=org.name)
            session.location.select(loc_name=DEFAULT_LOC)
            page_values = session.contenthost.read(
                client.hostname, widget_names=['errata.pagination']
            )
            assert int(page_values['errata']['pagination']['per_page']) == 20
            # assert total_pages > 1 with default page settings
            assert int(page_values['errata']['pagination']['pages']) > 1

            view = session.contenthost.navigate_to(
                session.contenthost, 'Edit', entity_name=client.hostname
            )
            per_page_value = view.errata.pagination.per_page
            # Change per-page setting to 100 and assert there is now only one page
            assert per_page_value.fill('100')
            page_values = session.contenthost.read(
                client.hostname, widget_names=['errata.pagination']
            )
            assert int(page_values['errata']['pagination']['per_page']) == 100
            assert int(page_values['errata']['pagination']['pages']) == 1
            # assert at least the 28 errata from fake repo are present
            assert int(page_values['errata']['pagination']['total_items']) >= 28

            # install all errata using REX
            status = session.contenthost.install_errata(client.hostname, 'All', install_via='rex')
            # Assert errata are listed on job invocation page
            assert status['overview']['job_status'] == 'Success'
            assert status['overview']['job_status_progress'] == '100%'
            # check that there are no applicable errata left on the CHost's errata page
            page_values = session.contenthost.read(
                client.hostname, widget_names=['errata.pagination']
            )
            assert int(page_values['errata']['pagination']['total_items']) == 0


@pytest.mark.tier2
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
def test_positive_list(session, org, lce, target_sat):
    """View all errata in an Org

    :id: 71c7a054-a644-4c1e-b304-6bc34ea143f4

    :Setup: Errata synced on satellite server.

    :Steps: Create two Orgs each having a product synced which contains errata.

    :expectedresults: Check that the errata belonging to one Org is not showing in the other.

    :BZ: 1659941, 1837767

    :customerscenario: true

    :CaseLevel: Integration
    """
    rc = target_sat.cli_factory.RepositoryCollection(
        repositories=[target_sat.cli_factory.YumRepository(settings.repos.yum_3.url)]
    )
    rc.setup_content(org.id, lce.id)
    with session:
        assert (
            session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)[0]['Errata ID']
            == CUSTOM_REPO_ERRATA_ID
        )
        assert not session.errata.search(settings.repos.yum_3.errata[5], applicable=False)
        session.organization.select(org_name=org.name)
        assert (
            session.errata.search(settings.repos.yum_3.errata[5], applicable=False)[0]['Errata ID']
            == settings.repos.yum_3.errata[5]
        )
        assert not session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)


@pytest.mark.tier2
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel6',
            'VirtualizationAgentsRepository': {'cdn': True},
            'YumRepository': {'url': CUSTOM_REPO_URL},
        }
    ],
    indirect=True,
)
def test_positive_list_permission(test_name, module_org, module_repos_collection_with_setup):
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
        permission=entities.Permission().search(
            query={'search': 'resource_type="Katello::Product"'}
        ),
        role=role,
        search='name = "{}"'.format(PRDS['rhel']),
    ).create()
    user_password = gen_string('alphanumeric')
    user = entities.User(
        default_organization=module_org,
        organization=[module_org],
        role=[role],
        password=user_password,
    ).create()
    with Session(test_name, user=user.login, password=user_password) as session:
        assert (
            session.errata.search(RHVA_ERRATA_ID, applicable=False)[0]['Errata ID']
            == RHVA_ERRATA_ID
        )
        assert not session.errata.search(CUSTOM_REPO_ERRATA_ID, applicable=False)


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'RHELAnsibleEngineRepository': {'cdn': True},
            'YumRepository': {'url': CUSTOM_REPO_URL},
        }
    ],
    indirect=True,
)
def test_positive_apply_for_all_hosts(
    session, module_org, module_repos_collection_with_setup, target_sat
):
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
    with Broker(
        nick=module_repos_collection_with_setup.distro, host_classes={'host': ContentHost}, _count=2
    ) as clients:
        for client in clients:
            module_repos_collection_with_setup.setup_virtual_machine(
                client, install_katello_agent=False
            )
            client.add_rex_key(satellite=target_sat)
            assert _install_client_package(client, FAKE_1_CUSTOM_PACKAGE)
        with session:
            session.location.select(loc_name=DEFAULT_LOC)
            for client in clients:
                client.add_rex_key(satellite=target_sat)
                status = session.contenthost.install_errata(
                    client.hostname, CUSTOM_REPO_ERRATA_ID, install_via='rex'
                )
                assert status['overview']['job_status'] == 'Success'
                assert status['overview']['job_status_progress'] == '100%'
                packages_rows = session.contenthost.search_package(
                    client.hostname, FAKE_2_CUSTOM_PACKAGE
                )
                assert packages_rows[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel6',
            'VirtualizationAgentsRepository': {'cdn': True, 'distro': 'rhel6'},
            'YumRepository': {'url': CUSTOM_REPO_URL},
        }
    ],
    indirect=True,
)
def test_positive_view_cve(session, module_repos_collection_with_setup):
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
        assert {cve.strip() for cve in errata_values['details']['cves'].split(',')} == set(
            RHVA_ERRATA_CVES
        )
        errata_values = session.errata.read(CUSTOM_REPO_ERRATA_ID)
        assert errata_values['details']['cves'] == 'N/A'


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'RHELAnsibleEngineRepository': {'cdn': True},
            'YumRepository': {'url': CUSTOM_REPO_URL},
        }
    ],
    indirect=True,
)
def test_positive_filter_by_environment(
    session, module_org, module_repos_collection_with_setup, target_sat
):
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
    with Broker(
        nick=module_repos_collection_with_setup.distro, host_classes={'host': ContentHost}, _count=2
    ) as clients:
        for client in clients:
            module_repos_collection_with_setup.setup_virtual_machine(
                client, install_katello_agent=False
            )
            assert _install_client_package(client, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
        # Promote the latest content view version to a new lifecycle environment
        content_view = entities.ContentView(
            id=module_repos_collection_with_setup.setup_content_data['content_view']['id']
        ).read()
        content_view_version = content_view.version[-1].read()
        lce = content_view_version.environment[-1].read()
        new_lce = entities.LifecycleEnvironment(organization=module_org, prior=lce).create()
        promote(content_view_version, new_lce.id)
        host = entities.Host().search(query={'search': f'name={clients[0].hostname}'})[0].read()
        host.content_facet_attributes = {
            'content_view_id': content_view.id,
            'lifecycle_environment_id': new_lce.id,
        }
        host.update(['content_facet_attributes'])
        with session:
            session.location.select(loc_name=DEFAULT_LOC)
            # search in new_lce
            values = session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, clients[0].hostname, environment=new_lce.name
            )
            assert values[0]['Name'] == clients[0].hostname
            assert not session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, clients[1].hostname, environment=new_lce.name
            )
            # search in lce
            values = session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, clients[1].hostname, environment=lce.name
            )
            assert values[0]['Name'] == clients[1].hostname
            assert not session.errata.search_content_hosts(
                CUSTOM_REPO_ERRATA_ID, clients[0].hostname, environment=lce.name
            )


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'RHELAnsibleEngineRepository': {'cdn': True},
            'YumRepository': {'url': CUSTOM_REPO_URL},
        }
    ],
    indirect=True,
)
def test_positive_content_host_previous_env(
    session, module_org, module_repos_collection_with_setup, vm
):
    """Check if the applicable errata are available from the content
    host's previous environment

    :id: 78110ba8-3942-46dd-8c14-bffa1dbd5195

    :Setup:

        1. Make sure multiple environments are present.
        2. Content host's previous environments have additional errata.

    :Steps: Go to Content Hosts -> Select content host -> Errata Tab ->
        Select Previous environments.

    :expectedresults: The errata from previous environments are displayed.

    :parametrized: yes

    :CaseLevel: System
    """
    hostname = vm.hostname
    assert _install_client_package(vm, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
    # Promote the latest content view version to a new lifecycle environment
    content_view = entities.ContentView(
        id=module_repos_collection_with_setup.setup_content_data['content_view']['id']
    ).read()
    content_view_version = content_view.version[-1].read()
    lce = content_view_version.environment[-1].read()
    new_lce = entities.LifecycleEnvironment(organization=module_org, prior=lce).create()
    promote(content_view_version, new_lce.id)
    host = entities.Host().search(query={'search': f'name={hostname}'})[0].read()
    host.content_facet_attributes = {
        'content_view_id': content_view.id,
        'lifecycle_environment_id': new_lce.id,
    }
    host.update(['content_facet_attributes'])
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        environment = f'Previous Lifecycle Environment ({lce.name}/{content_view.name})'
        content_host_erratum = session.contenthost.search_errata(
            hostname, CUSTOM_REPO_ERRATA_ID, environment=environment
        )
        assert content_host_erratum[0]['Id'] == CUSTOM_REPO_ERRATA_ID


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'RHELAnsibleEngineRepository': {'cdn': True},
            'YumRepository': {'url': CUSTOM_REPO_URL},
        }
    ],
    indirect=True,
)
def test_positive_content_host_library(session, module_org, vm):
    """Check if the applicable errata are available from the content
    host's Library

    :id: 4e627410-b7b8-471b-b9b4-a18e77fdd3f8

    :Setup:

        1. Make sure multiple environments are present.
        2. Content host's Library environment has additional errata.

    :Steps: Go to Content Hosts -> Select content host -> Errata Tab -> Select 'Library'.

    :expectedresults: The errata from Library are displayed.

    :parametrized: yes

    :CaseLevel: System
    """
    hostname = vm.hostname
    assert _install_client_package(vm, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        content_host_erratum = session.contenthost.search_errata(
            hostname, CUSTOM_REPO_ERRATA_ID, environment='Library Synced Content'
        )
        assert content_host_erratum[0]['Id'] == CUSTOM_REPO_ERRATA_ID


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'RHELAnsibleEngineRepository': {'cdn': True},
            'YumRepository': {'url': settings.repos.yum_9.url},
        }
    ],
    indirect=True,
)
def test_positive_content_host_search_type(session, erratatype_vm):
    """Search for errata on a content host's errata tab by type.

    :id: 59e5d6e5-2537-4387-a7d3-637cc4b52d0e

    :Setup: Content Host with applicable errata

    :customerscenario: true

    :Steps: Search for errata on content host by type (e.g. 'type = security')
     Step 1 Search for "type = security", assert expected amount and IDs found
     Step 2 Search for "type = bugfix", assert expected amount and IDs found
     Step 3 Search for "type = enhancement", assert expected amount and IDs found

    :BZ: 1653293

    :CaseLevel: Integration
    """

    pkgs = ' '.join(FAKE_9_YUM_OUTDATED_PACKAGES)
    assert _install_client_package(erratatype_vm, pkgs, errata_applicability=True)

    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        # Search for RHSA security errata
        ch_erratum = session.contenthost.search_errata(
            erratatype_vm.hostname, "type = security", environment='Library Synced Content'
        )

        # Assert length matches known amount of RHSA errata
        assert len(ch_erratum) == FAKE_9_YUM_SECURITY_ERRATUM_COUNT

        # Assert IDs are that of RHSA errata
        errata_ids = sorted(erratum['Id'] for erratum in ch_erratum)
        assert errata_ids == sorted(FAKE_9_YUM_SECURITY_ERRATUM)
        # Search for RHBA buxfix errata
        ch_erratum = session.contenthost.search_errata(
            erratatype_vm.hostname, "type = bugfix", environment='Library Synced Content'
        )

        # Assert length matches known amount of RHBA errata
        assert len(ch_erratum) == FAKE_10_YUM_BUGFIX_ERRATUM_COUNT

        # Assert IDs are that of RHBA errata
        errata_ids = sorted(erratum['Id'] for erratum in ch_erratum)
        assert errata_ids == sorted(FAKE_10_YUM_BUGFIX_ERRATUM)
        # Search for RHEA enhancement errata
        ch_erratum = session.contenthost.search_errata(
            erratatype_vm.hostname, "type = enhancement", environment='Library Synced Content'
        )

        # Assert length matches known amount of RHEA errata
        assert len(ch_erratum) == FAKE_11_YUM_ENHANCEMENT_ERRATUM_COUNT

        # Assert IDs are that of RHEA errata
        errata_ids = sorted(erratum['Id'] for erratum in ch_erratum)
        assert errata_ids == sorted(FAKE_11_YUM_ENHANCEMENT_ERRATUM)


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'RHELAnsibleEngineRepository': {'cdn': True},
            'YumRepository': {'url': settings.repos.yum_9.url},
        }
    ],
    indirect=True,
)
def test_positive_show_count_on_content_host_page(session, module_org, erratatype_vm):
    """Available errata count displayed in Content hosts page

    :id: 8575e282-d56e-41dc-80dd-f5f6224417cb

    :Setup:

        1. Errata synced on satellite server.
        2. Some content hosts are present.

    :Steps: Go to Hosts -> Content Hosts.

    :expectedresults: The available errata count is displayed.

    :BZ: 1484044, 1775427

    :customerscenario: true

    :CaseLevel: System
    """
    vm = erratatype_vm
    hostname = vm.hostname
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        content_host_values = session.contenthost.search(hostname)
        assert content_host_values[0]['Name'] == hostname
        installable_errata = content_host_values[0]['Installable Updates']['errata']

        for errata_type in ('security', 'bug_fix', 'enhancement'):
            assert int(installable_errata[errata_type]) == 0

        pkgs = ' '.join(FAKE_9_YUM_OUTDATED_PACKAGES)
        assert _install_client_package(vm, pkgs, errata_applicability=True)

        content_host_values = session.contenthost.search(hostname)
        assert content_host_values[0]['Name'] == hostname
        installable_errata = content_host_values[0]['Installable Updates']['errata']

        assert int(installable_errata['security']) == FAKE_9_YUM_SECURITY_ERRATUM_COUNT
        for errata_type in ('bug_fix', 'enhancement'):
            assert int(installable_errata[errata_type]) == 1


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'RHELAnsibleEngineRepository': {'cdn': True},
            'YumRepository': {'url': settings.repos.yum_9.url},
        }
    ],
    indirect=True,
)
def test_positive_show_count_on_content_host_details_page(session, module_org, erratatype_vm):
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
    vm = erratatype_vm
    hostname = vm.hostname
    with session:
        session.location.select(loc_name=DEFAULT_LOC)
        content_host_values = session.contenthost.read(hostname, 'details')
        for errata_type in ('security', 'bug_fix', 'enhancement'):
            assert int(content_host_values['details'][errata_type]) == 0

        pkgs = ' '.join(FAKE_9_YUM_OUTDATED_PACKAGES)
        assert _install_client_package(vm, pkgs, errata_applicability=True)

        # navigate to content host main page by making a search, to refresh the details page
        session.contenthost.search(hostname)
        content_host_values = session.contenthost.read(hostname, 'details')
        assert int(content_host_values['details']['security']) == FAKE_9_YUM_SECURITY_ERRATUM_COUNT

        for errata_type in ('bug_fix', 'enhancement'):
            assert int(content_host_values['details'][errata_type]) == 1


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.parametrize('setting_update', ['errata_status_installable'], indirect=True)
def test_positive_filtered_errata_status_installable_param(
    session, errata_status_installable, target_sat, setting_update
):
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

    :BZ: 1368254, 2013093

    :CaseImportance: Medium

    :CaseLevel: System
    """
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    repos_collection = target_sat.cli_factory.RepositoryCollection(
        distro='rhel7',
        repositories=[
            target_sat.cli_factory.SatelliteToolsRepository(),
            # As Satellite Tools may be added as custom repo and to have a "Fully entitled" host,
            # force the host to consume an RH product with adding a cdn repo.
            target_sat.cli_factory.RHELAnsibleEngineRepository(cdn=True),
            target_sat.cli_factory.YumRepository(url=CUSTOM_REPO_URL),
        ],
    )
    repos_collection.setup_content(org.id, lce.id, upload_manifest=True)
    with Broker(nick=repos_collection.distro, host_classes={'host': ContentHost}) as client:
        repos_collection.setup_virtual_machine(client)
        assert _install_client_package(client, FAKE_1_CUSTOM_PACKAGE, errata_applicability=True)
        # Adding content view filter and content view filter rule to exclude errata for the
        # installed package.
        content_view = entities.ContentView(
            id=repos_collection.setup_content_data['content_view']['id']
        ).read()
        cv_filter = entities.ErratumContentViewFilter(
            content_view=content_view, inclusion=False
        ).create()
        errata = entities.Errata(content_view_version=content_view.version[-1]).search(
            query=dict(search=f'errata_id="{CUSTOM_REPO_ERRATA_ID}"')
        )[0]
        entities.ContentViewFilterRule(content_view_filter=cv_filter, errata=errata).create()
        content_view.publish()
        content_view = content_view.read()
        content_view_version = content_view.version[-1]
        promote(content_view_version, lce.id)
        with session:
            session.organization.select(org_name=org.name)
            session.location.select(loc_name=DEFAULT_LOC)
            property_value = 'Yes'
            session.settings.update(f'name = {setting_update.name}', property_value)
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
            for key in actual_values:
                assert expected_values[key] in actual_values[key], 'Expected text not found'
            property_value = 'Yes'
            session.settings.update(f'name = {setting_update.name}', property_value)
            assert _install_client_package(
                client, FAKE_9_YUM_OUTDATED_PACKAGES[1], errata_applicability=True
            )
            expected_values = {
                'Status': 'Error',
                'Errata': 'Security errata installable',
                'Subscription': 'Fully entitled',
            }
            # Refresh the host page to get the new details
            session.browser.refresh()
            host_details_values = session.host.get_details(client.hostname)
            actual_values = {
                key: value
                for key, value in host_details_values['properties']['properties_table'].items()
                if key in expected_values
            }
            for key in actual_values:
                assert expected_values[key] in actual_values[key], 'Expected text not found'


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_setup',
    [
        {
            'distro': 'rhel7',
            'SatelliteToolsRepository': {},
            'RHELAnsibleEngineRepository': {'cdn': True},
            'YumRepository': {'url': CUSTOM_REPO_URL},
        }
    ],
    indirect=True,
)
def test_content_host_errata_search_commands(
    session, module_org, module_repos_collection_with_setup, target_sat
):
    """View a list of affected content hosts for security (RHSA) and bugfix (RHBA) errata,
    filtered with errata status and applicable flags. Applicability is calculated using the
    Library, but Installability is calculated using the attached CV, and is subject to the
    CV's own filtering.

    :id: 45114f8e-0fc8-4c7c-85e0-f9b613530dac

    :Setup: Two Content Hosts, one with RHSA and one with RHBA errata.

    :customerscenario: true

    :Steps:
        1.  host list --search "errata_status = security_needed"
        2.  host list --search "errata_status = errata_needed"
        3.  host list --search "applicable_errata = RHSA-2012:0055"
        4.  host list --search "applicable_errata = RHBA-2012:1030"
        5.  host list --search "applicable_rpms = walrus-5.21-1.noarch"
        6.  host list --search "applicable_rpms = kangaroo-0.2-1.noarch"
        7.  host list --search "installable_errata = RHSA-2012:0055"
        8.  host list --search "installable_errata = RHBA-2012:1030"

    :expectedresults: The hosts are correctly listed for RHSA and RHBA errata.

    :BZ: 1707335
    """
    with Broker(
        nick=module_repos_collection_with_setup.distro, host_classes={'host': ContentHost}, _count=2
    ) as clients:
        for client in clients:
            module_repos_collection_with_setup.setup_virtual_machine(client)
        # Install pkg walrus-0.71-1.noarch to create need for RHSA on client 1
        assert _install_client_package(
            clients[0], FAKE_1_CUSTOM_PACKAGE, errata_applicability=False
        )
        # Install pkg kangaroo-0.1-1.noarch to create need for RHBA on client 2
        assert _install_client_package(
            clients[1], FAKE_4_CUSTOM_PACKAGE, errata_applicability=False
        )
        with session:
            session.location.select(loc_name=DEFAULT_LOC)
            # Search for hosts needing RHSA security errata
            result = session.contenthost.search('errata_status = security_needed')
            result = [item['Name'] for item in result]
            assert clients[0].hostname in result, 'Needs-RHSA host not found'
            # Search for hosts needing RHBA bugfix errata
            result = session.contenthost.search('errata_status = errata_needed')
            result = [item['Name'] for item in result]
            assert clients[1].hostname in result, 'Needs-RHBA host not found'
            # Search for applicable RHSA errata by Errata ID
            result = session.contenthost.search(
                f'applicable_errata = {settings.repos.yum_6.errata[2]}'
            )
            result = [item['Name'] for item in result]
            assert clients[0].hostname in result
            # Search for applicable RHBA errata by Errata ID
            result = session.contenthost.search(
                f'applicable_errata = {settings.repos.yum_6.errata[0]}'
            )
            result = [item['Name'] for item in result]
            assert clients[1].hostname in result
            # Search for RHSA applicable RPMs
            result = session.contenthost.search(f'applicable_rpms = {FAKE_2_CUSTOM_PACKAGE}')
            result = [item['Name'] for item in result]
            assert clients[0].hostname in result
            # Search for RHBA applicable RPMs
            result = session.contenthost.search(f'applicable_rpms = {FAKE_5_CUSTOM_PACKAGE}')
            result = [item['Name'] for item in result]
            assert clients[1].hostname in result
            # Search for installable RHSA errata by Errata ID
            result = session.contenthost.search(
                f'installable_errata = {settings.repos.yum_6.errata[2]}'
            )
            result = [item['Name'] for item in result]
            assert clients[0].hostname in result
            # Search for installable RHBA errata by Errata ID
            result = session.contenthost.search(
                f'installable_errata = {settings.repos.yum_6.errata[0]}'
            )
            result = [item['Name'] for item in result]
            assert clients[1].hostname in result
