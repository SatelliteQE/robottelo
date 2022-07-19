"""Test class for Content Hosts UI

:Requirement: Content Host

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Hosts-Content

:Assignee: spusater

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re
from datetime import datetime
from datetime import timedelta
from urllib.parse import urlparse

import pytest
from airgun.session import Session
from fauxfactory import gen_integer
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import wait_for_tasks
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_fake_host
from robottelo.cli.factory import make_virt_who_config
from robottelo.config import setting_is_set
from robottelo.config import settings
from robottelo.constants import DEFAULT_SYSPURPOSE_ATTRIBUTES
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import DISTRO_RHEL8
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP_NAME
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_ERRATA_ID
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE_NAME
from robottelo.constants import VDC_SUBSCRIPTION_NAME
from robottelo.constants import VIRT_WHO_HYPERVISOR_TYPES
from robottelo.virtwho_utils import create_fake_hypervisor_content

if not setting_is_set('clients') or not setting_is_set('fake_manifest'):
    pytest.skip('skipping tests due to missing settings', allow_module_level=True)


@pytest.fixture(scope='module')
def module_org():
    org = entities.Organization().create()
    # adding remote_execution_connect_by_ip=Yes at org level
    entities.Parameter(
        name='remote_execution_connect_by_ip',
        value='Yes',
        organization=org.id,
    ).create()
    return org


@pytest.fixture
def vm(module_repos_collection_with_manifest, rhel7_contenthost, target_sat):
    """Virtual machine registered in satellite"""
    module_repos_collection_with_manifest.setup_virtual_machine(rhel7_contenthost)
    rhel7_contenthost.add_rex_key(target_sat)
    yield rhel7_contenthost


@pytest.fixture
def vm_module_streams(module_repos_collection_with_manifest, rhel8_contenthost, target_sat):
    """Virtual machine registered in satellite without katello-agent installed"""
    module_repos_collection_with_manifest.setup_virtual_machine(
        rhel8_contenthost, install_katello_agent=False
    )
    rhel8_contenthost.add_rex_key(satellite=target_sat)
    yield rhel8_contenthost


def set_ignore_facts_for_os(value=False):
    """Helper to set 'ignore_facts_for_operatingsystem' setting"""
    ignore_setting = entities.Setting().search(
        query={'search': 'name="ignore_facts_for_operatingsystem"'}
    )[0]
    ignore_setting.value = str(value)
    ignore_setting.update({'value'})


def run_remote_command_on_content_host(command, vm_module_streams):
    result = vm_module_streams.run(command)
    assert result.status == 0
    return result


@pytest.fixture(scope='module')
def module_host_template(module_org, module_location):
    host_template = entities.Host(organization=module_org, location=module_location)
    host_template.create_missing()
    host_template.name = None
    return host_template


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_end_to_end(session, default_location, module_repos_collection_with_manifest, vm):
    """Create all entities required for content host, set up host, register it
    as a content host, read content host details, install package and errata.

    :id: f43f2826-47c1-4069-9c9d-2410fd1b622c

    :expectedresults: content host details are the same as expected, package
        and errata installation are successful

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: Critical
    """
    result = vm.run(f'yum -y install {FAKE_1_CUSTOM_PACKAGE}')
    assert result.status == 0
    with session:
        session.location.select(default_location.name)
        # Ensure content host is searchable
        assert session.contenthost.search(vm.hostname)[0]['Name'] == vm.hostname
        chost = session.contenthost.read(
            vm.hostname, widget_names=['details', 'provisioning_details', 'subscriptions']
        )
        session.contenthost.update(vm.hostname, {'repository_sets.limit_to_lce': True})
        ch_reposet = session.contenthost.read(vm.hostname, widget_names=['repository_sets'])
        chost.update(ch_reposet)
        # Ensure all content host fields/tabs have appropriate values
        assert chost['details']['name'] == vm.hostname
        assert (
            chost['details']['content_view']
            == module_repos_collection_with_manifest.setup_content_data['content_view']['name']
        )
        lce_name = module_repos_collection_with_manifest.setup_content_data['lce']['name']
        assert chost['details']['lce'][lce_name][lce_name]
        ak_name = module_repos_collection_with_manifest.setup_content_data["activation_key"]["name"]
        assert chost['details']['registered_by'] == f'Activation Key {ak_name}'
        assert chost['provisioning_details']['name'] == vm.hostname
        assert module_repos_collection_with_manifest.custom_product['name'] in {
            repo['Repository Name'] for repo in chost['subscriptions']['resources']['assigned']
        }
        actual_repos = {repo['Repository Name'] for repo in chost['repository_sets']['table']}
        expected_repos = {
            module_repos_collection_with_manifest.repos_data[repo_index].get(
                'repository-set',
                module_repos_collection_with_manifest.repos_info[repo_index]['name'],
            )
            for repo_index in range(len(module_repos_collection_with_manifest.repos_info))
        }
        assert actual_repos == expected_repos
        # Update description
        new_description = gen_string('alpha')
        session.contenthost.update(vm.hostname, {'details.description': new_description})
        chost = session.contenthost.read(vm.hostname, widget_names='details')
        assert chost['details']['description'] == new_description
        # Install package
        result = session.contenthost.execute_package_action(
            vm.hostname, 'Package Install', FAKE_0_CUSTOM_PACKAGE_NAME
        )
        assert result['overview']['job_status'] == 'Success'
        # Ensure package installed
        packages = session.contenthost.search_package(vm.hostname, FAKE_0_CUSTOM_PACKAGE_NAME)
        assert packages[0]['Installed Package'] == FAKE_0_CUSTOM_PACKAGE
        # Install errata
        result = session.contenthost.install_errata(
            vm.hostname, settings.repos.yum_6.errata[2], install_via='rex'
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        # Ensure errata installed
        packages = session.contenthost.search_package(vm.hostname, FAKE_2_CUSTOM_PACKAGE_NAME)
        assert packages[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE
        # Delete content host
        session.contenthost.delete(vm.hostname)

        assert not session.contenthost.search(vm.hostname)


@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_end_to_end_bulk_update(session, default_location, vm, target_sat):
    """Create VM, set up VM as host, register it as a content host,
    read content host details, install a package ( e.g. walrus-0.71) and
    use bulk action (Update All Packages) to update the package by name
    to a later version.

    :id: d460ba30-82c7-11e9-9af5-54ee754f2151

    :customerscenario: true

    :expectedresults: package installation and update to a later version
        are successful.

    :BZ: 1712069, 1838800

    :parametrized: yes

    :CaseLevel: System
    """
    hc_name = gen_string('alpha')
    description = gen_string('alpha')
    result = vm.run(f'yum -y install {FAKE_1_CUSTOM_PACKAGE}')
    assert result.status == 0
    with session:
        session.location.select(default_location.name)
        # Ensure content host is searchable
        assert session.contenthost.search(vm.hostname)[0]['Name'] == vm.hostname
        # Update package using bulk action
        # use the Host Collection view to access Update Packages dialogue
        session.hostcollection.create(
            {
                'name': hc_name,
                'unlimited_hosts': False,
                'max_hosts': 2,
                'description': description,
            }
        )
        session.hostcollection.associate_host(hc_name, vm.hostname)
        # For BZ#1838800, assert the Host Collection Errata Install table has the search URI
        p = urlparse(session.hostcollection.search_applicable_hosts(hc_name, FAKE_1_ERRATA_ID))
        query = f'search=installable_errata%3D{FAKE_1_ERRATA_ID}'
        assert p.hostname == target_sat.hostname
        assert p.path == '/content_hosts'
        assert p.query == query
        # Note time for later wait_for_tasks, and include 4 mins margin of safety.
        timestamp = (datetime.utcnow() - timedelta(minutes=4)).strftime('%Y-%m-%d %H:%M')
        # Update the package by name
        session.hostcollection.manage_packages(
            hc_name,
            content_type='rpm',
            packages=FAKE_1_CUSTOM_PACKAGE_NAME,
            action='update_all',
            action_via='via remote execution',
        )
        # Wait for applicability update event (in case Satellite system slow)
        wait_for_tasks(
            search_query='label = Actions::Katello::Applicability::Hosts::BulkGenerate'
            f' and started_at >= "{timestamp}"'
            f' and state = stopped'
            f' and result = success',
            search_rate=15,
            max_tries=10,
        )
        # Ensure package updated to a later version
        packages = session.contenthost.search_package(vm.hostname, FAKE_2_CUSTOM_PACKAGE_NAME)
        assert packages[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE
        # Delete content host
        session.contenthost.delete(vm.hostname)


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_search_by_subscription_status(session, default_location, vm):
    """Register host into the system and search for it afterwards by
    subscription status

    :id: b4d24ee7-51b9-43e4-b0c9-7866b6340ce1

    :expectedresults: Validate that host can be found for valid
        subscription status and that host is not present in the list for
        invalid status

    :BZ: 1406855, 1498827, 1495271

    :parametrized: yes

    :CaseLevel: System
    """
    with session:
        session.location.select(default_location.name)
        assert session.contenthost.search(vm.hostname)[0]['Name'] == vm.hostname
        result = session.contenthost.search('subscription_status = valid')
        assert vm.hostname in {host['Name'] for host in result}
        result = session.contenthost.search('subscription_status != valid')
        assert vm.hostname not in {host['Name'] for host in result}
        # check dashboard
        session.dashboard.action({'HostSubscription': {'type': 'Invalid'}})
        values = session.contenthost.read_all()
        assert values['searchbox'] == 'subscription_status = invalid'
        assert len(values['table']) == 0
        session.dashboard.action({'HostSubscription': {'type': 'Valid'}})
        values = session.contenthost.read_all()
        assert values['searchbox'] == 'subscription_status = valid'
        assert len(values['table']) == 1
        assert values['table'][0]['Name'] == vm.hostname


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_toggle_subscription_status(session, default_location, vm):
    """Register host into the system, assert subscription status valid,
    toggle status off and on again using CLI and assert status is updated in web UI.

    :id: b9343e6f-9354-46ef-873f-b63851d29043

    :expectedresults: Subscription status changed on the CLI is reflected in the web UI.

    :customerscenario: true

    :BZ: 1836868

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: Medium
    """
    with session:
        session.location.select(default_location.name)
        assert session.contenthost.search(vm.hostname)[0]['Name'] == vm.hostname
        subscriptions = session.contenthost.read(vm.hostname, widget_names='subscriptions')[
            'subscriptions'
        ]
        assert subscriptions['auto_attach'].lower() == 'yes'
        # Toggle auto-attach status to No using CLI
        vm.run('subscription-manager auto-attach --disable && subscription-manager refresh')
        session.browser.refresh()
        subscriptions = session.contenthost.read(vm.hostname, widget_names='subscriptions')[
            'subscriptions'
        ]
        assert subscriptions['auto_attach'].lower() == 'no'
        # Toggle auto-attach status to Yes using CLI
        vm.run('subscription-manager auto-attach --enable && subscription-manager refresh')
        session.browser.refresh()
        subscriptions = session.contenthost.read(vm.hostname, widget_names='subscriptions')[
            'subscriptions'
        ]
        assert subscriptions['auto_attach'].lower() == 'yes'


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_negative_install_package(session, default_location, vm):
    """Attempt to install non-existent package to a host remotely

    :id: d60b70f9-c43f-49c0-ae9f-187ffa45ac97

    :customerscenario: true

    :BZ: 1262940

    :expectedresults: Task finished with warning

    :parametrized: yes

    :CaseLevel: System
    """
    with session:
        session.location.select(default_location.name)
        result = session.contenthost.execute_package_action(
            vm.hostname, 'Package Install', gen_string('alphanumeric')
        )
        assert result['overview']['job_status'] == 'Failed'


@pytest.mark.tier3
@pytest.mark.skipif((not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url')
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_remove_package(session, default_location, vm):
    """Remove a package from a host remotely

    :id: 86d8896b-06d9-4c99-937e-f3aa07b4eb69

    :expectedresults: Package was successfully removed

    :parametrized: yes

    :CaseLevel: System
    """
    vm.download_install_rpm(settings.repos.yum_6.url, FAKE_0_CUSTOM_PACKAGE)
    with session:
        session.location.select(default_location.name)
        result = session.contenthost.execute_package_action(
            vm.hostname, 'Package Remove', FAKE_0_CUSTOM_PACKAGE_NAME
        )
        assert result['overview']['job_status'] == 'Success'
        packages = session.contenthost.search_package(vm.hostname, FAKE_0_CUSTOM_PACKAGE_NAME)
        assert not packages


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_upgrade_package(session, default_location, vm):
    """Upgrade a host package remotely

    :id: 1969db93-e7af-4f5f-973d-23c222224db6

    :expectedresults: Package was successfully upgraded

    :parametrized: yes

    :CaseLevel: System
    """
    vm.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    with session:
        session.location.select(default_location.name)
        result = session.contenthost.execute_package_action(
            vm.hostname, 'Package Update', FAKE_1_CUSTOM_PACKAGE_NAME
        )
        assert result['overview']['job_status'] == 'Success'
        packages = session.contenthost.search_package(vm.hostname, FAKE_2_CUSTOM_PACKAGE)
        assert packages[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_install_package_group(session, default_location, vm):
    """Install a package group to a host remotely

    :id: a43fb21b-5f6a-4f14-8cd6-114ec287540c

    :expectedresults: Package group was successfully installed

    :parametrized: yes

    :CaseLevel: System
    """
    with session:
        session.location.select(default_location.name)
        result = session.contenthost.execute_package_action(
            vm.hostname,
            'Group Install (Deprecated)',
            FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
        )
        assert result['overview']['job_status'] == 'Success'
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            packages = session.contenthost.search_package(vm.hostname, package)
            assert packages[0]['Installed Package'] == package


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_remove_package_group(session, default_location, vm):
    """Remove a package group from a host remotely

    :id: dbeea1f2-adf4-4ad8-a989-efad8ce21b98

    :expectedresults: Package group was successfully removed

    :parametrized: yes

    :CaseLevel: System
    """
    with session:
        session.location.select(default_location.name)
        for action in ('Group Install (Deprecated)', 'Group Remove (Deprecated)'):
            result = session.contenthost.execute_package_action(
                vm.hostname, action, FAKE_0_CUSTOM_PACKAGE_GROUP_NAME
            )
            assert result['overview']['job_status'] == 'Success'
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            assert not session.contenthost.search_package(vm.hostname, package)


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_search_errata_non_admin(
    session, default_location, vm, test_name, default_viewer_role
):
    """Search for host's errata by non-admin user with enough permissions

    :id: 5b8887d2-987f-4bce-86a1-8f65ca7e1195

    :customerscenario: true

    :BZ: 1255515, 1662405, 1652938

    :expectedresults: User can access errata page and proper errata is
        listed

    :parametrized: yes

    :CaseLevel: System
    """
    vm.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    with Session(
        test_name, user=default_viewer_role.login, password=default_viewer_role.password
    ) as session:
        session.location.select(default_location.name)
        chost = session.contenthost.read(vm.hostname, widget_names='errata')
        assert settings.repos.yum_6.errata[2] in {
            errata['Id'] for errata in chost['errata']['table']
        }


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_ensure_errata_applicability_with_host_reregistered(session, default_location, vm):
    """Ensure that errata remain available to install when content host is
    re-registered

    :id: 30b1e512-45e5-481e-845f-5344ed81450d

    :customerscenario: true

    :steps:
        1. Prepare an activation key with content view that contain a
            repository with a package that has errata
        2. Register the host to activation key
        3. Install the package that has errata
        4. Refresh content host subscription running:
            "subscription-manager refresh  && yum repolist"
        5. Ensure errata is available for installation
        6. Refresh content host subscription running:
            "subscription-manager refresh  && yum repolist"

    :expectedresults: errata is available in installable errata list

    :BZ: 1463818

    :parametrized: yes

    :CaseLevel: System
    """
    vm.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    result = vm.run(f'rpm -q {FAKE_1_CUSTOM_PACKAGE}')
    assert result.status == 0
    result = vm.run('subscription-manager refresh  && yum repolist')
    assert result.status == 0
    with session:
        session.location.select(default_location.name)
        chost = session.contenthost.read(vm.hostname, widget_names='errata')
        assert settings.repos.yum_6.errata[2] in {
            errata['Id'] for errata in chost['errata']['table']
        }
        result = vm.run('subscription-manager refresh  && yum repolist')
        assert result.status == 0
        chost = session.contenthost.read(vm.hostname, widget_names='errata')
        assert settings.repos.yum_6.errata[2] in {
            errata['Id'] for errata in chost['errata']['table']
        }


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_host_re_registration_with_host_rename(
    session, default_location, module_org, module_repos_collection_with_manifest, vm
):
    """Ensure that content host should get re-registered after change in the hostname

    :id: c11f4e69-6ef5-45ab-aff5-00cf2d87f209

    :customerscenario: true

    :steps:
        1. Prepare an activation key with content view and repository
        2. Register the host to activation key
        3. Install the package from repository
        4. Unregister the content host
        5. Change the hostname of content host
        6. Re-register the same content host again

    :expectedresults: Re-registration should work as expected even after change in hostname

    :BZ: 1762793

    :parametrized: yes

    :CaseLevel: System
    """
    vm.run(f'yum install -y {FAKE_1_CUSTOM_PACKAGE}')
    result = vm.run(f'rpm -q {FAKE_1_CUSTOM_PACKAGE}')
    assert result.status == 0
    vm.unregister()
    updated_hostname = f'{gen_string("alpha")}.{vm.hostname}'.lower()
    vm.run(f'hostnamectl set-hostname {updated_hostname}')
    assert result.status == 0
    vm.register_contenthost(
        module_org.name,
        activation_key=module_repos_collection_with_manifest.setup_content_data['activation_key'][
            'name'
        ],
    )
    assert result.status == 0
    with session:
        session.location.select(default_location.name)
        assert session.contenthost.search(updated_hostname)[0]['Name'] == updated_hostname


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_positive_check_ignore_facts_os_setting(session, default_location, vm, module_org, request):
    """Verify that 'Ignore facts for operating system' setting works
    properly

    :steps:

        1. Create a new host entry using content host self registration
           procedure
        2. Check that there is a new setting added "Ignore facts for
           operating system", and set it to true.
        3. Upload the facts that were read from initial host, but with a
           change in all the operating system fields to a different OS or
           version.
        4. Verify that the host OS isn't updated.
        5. Set the setting in step 2 to false.
        6. Upload same modified facts from step 3.
        7. Verify that the host OS is updated.
        8. Verify that new OS is created

    :id: 71bed439-105c-4e87-baae-738379d055fb

    :customerscenario: true

    :expectedresults: Host facts impact its own values properly according
        to the setting values

    :BZ: 1155704

    :parametrized: yes

    :CaseLevel: System
    """
    major = str(gen_integer(15, 99))
    minor = str(gen_integer(1, 9))
    expected_os = f'RedHat {major}.{minor}'
    set_ignore_facts_for_os(False)
    host = (
        entities.Host()
        .search(query={'search': f'name={vm.hostname} and organization_id={module_org.id}'})[0]
        .read()
    )
    with session:
        session.location.select(default_location.name)
        # Get host current operating system value
        os = session.contenthost.read(vm.hostname, widget_names='details')['details']['os']
        # Change necessary setting to true
        set_ignore_facts_for_os(True)
        # Add cleanup function to roll back setting to default value
        request.addfinalizer(set_ignore_facts_for_os)
        # Read all facts for corresponding host
        facts = host.get_facts(data={'per_page': 10000})['results'][vm.hostname]
        # Modify OS facts to another values and upload them to the server
        # back
        facts['operatingsystem'] = 'RedHat'
        facts['osfamily'] = 'RedHat'
        facts['operatingsystemmajrelease'] = major
        facts['operatingsystemrelease'] = f'{major}.{minor}'
        host.upload_facts(data={'name': vm.hostname, 'facts': facts})
        session.contenthost.search('')
        updated_os = session.contenthost.read(vm.hostname, widget_names='details')['details']['os']
        # Check that host OS was not changed due setting was set to true
        assert os == updated_os
        # Put it to false and re-run the process
        set_ignore_facts_for_os(False)
        host.upload_facts(data={'name': vm.hostname, 'facts': facts})
        session.contenthost.search('')
        updated_os = session.contenthost.read(vm.hostname, widget_names='details')['details']['os']
        # Check that host OS was changed to new value
        assert os != updated_os
        assert updated_os == expected_os
        # Check that new OS was created
        assert session.operatingsystem.search(expected_os)[0]['Title'] == expected_os


# The content host has been moved to broker, but the test still depends on libvirt compute resource
@pytest.mark.libvirt_discovery
@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_virt_who_hypervisor_subscription_status(
    session, default_location, rhel7_contenthost, target_sat
):
    """Check that virt-who hypervisor shows the right subscription status
    without and with attached subscription.

    :id: 8b2cc5d6-ac85-463f-a973-f4818c55fb37

    :customerscenario: true

    :expectedresults:
        1. With subscription not attached, Subscription status is
           "Unsubscribed hypervisor" and represented by a yellow icon in
           content hosts list.
        2. With attached subscription, Subscription status is
           "Fully entitled" and represented by a green icon in content
           hosts list.

    :BZ: 1336924, 1860928

    :parametrized: yes

    :CaseLevel: System
    """
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    # TODO move this to either hack around virt-who service or use an env-* compute resource
    provisioning_server = settings.libvirt.libvirt_hostname
    # Create a new virt-who config
    virt_who_config = make_virt_who_config(
        {
            'organization-id': org.id,
            'hypervisor-type': VIRT_WHO_HYPERVISOR_TYPES['libvirt'],
            'hypervisor-server': f'qemu+ssh://{provisioning_server}/system',
            'hypervisor-username': 'root',
        }
    )
    # use broker virtual machine to host virt-who service
    # configure virtual machine and setup virt-who service
    # do not supply subscription to attach to virt_who hypervisor
    virt_who_data = rhel7_contenthost.virt_who_hypervisor_config(
        target_sat,
        virt_who_config['general-information']['id'],
        org_id=org.id,
        lce_id=lce.id,
        hypervisor_hostname=provisioning_server,
        configure_ssh=True,
    )
    virt_who_hypervisor_host = virt_who_data['virt_who_hypervisor_host']
    with session:
        session.location.select(default_location.name)
        assert (
            session.contenthost.search(virt_who_hypervisor_host.name)[0]['Subscription Status']
            == 'yellow'
        )
        chost = session.contenthost.read(virt_who_hypervisor_host.name, widget_names='details')
        assert chost['details']['subscription_status'] == 'Unsubscribed hypervisor'
        session.contenthost.add_subscription(virt_who_hypervisor_host.name, VDC_SUBSCRIPTION_NAME)
        assert (
            session.contenthost.search(virt_who_hypervisor_host.name)[0]['Subscription Status']
            == 'green'
        )
        chost = session.contenthost.read(virt_who_hypervisor_host.name, widget_names='details')
        assert chost['details']['subscription_status'] == 'Fully entitled'
        # for BZ#1860928
        checkin_time1 = session.contenthost.search(provisioning_server)[0]['Last Checkin']
        result = rhel7_contenthost.run('service virt-who stop')
        if result.status != 0:
            raise CLIFactoryError(f'Failed to stop the virt-who service:\n{result.stderr[1]}')
        result = rhel7_contenthost.run('virt-who --one-shot')
        if result.status != 0:
            raise CLIFactoryError(f'Failed when executing virt-who --one-shot:\n{result.stderr[1]}')
        result = rhel7_contenthost.run('service virt-who start')
        if result.status != 0:
            raise CLIFactoryError(f'Failed to start the virt-who service:\n{result.stderr[1]}')
        checkin_time2 = session.contenthost.search(provisioning_server)[0]['Last Checkin']
        assert checkin_time2 > checkin_time1


@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_module_stream_actions_on_content_host(session, default_location, vm_module_streams):
    """Check remote execution for module streams actions e.g. install, remove, disable
    works on content host. Verify that correct stream module stream
    get installed/removed.

    :id: 684e467e-b41c-4b95-8450-001abe85abe0

    :expectedresults: Remote execution for module actions should succeed.

    :parametrized: yes

    :CaseLevel: System
    """
    stream_version = '5.21'
    run_remote_command_on_content_host('dnf -y upload-profile', vm_module_streams)
    entities.Parameter(
        name='remote_execution_connect_by_ip',
        value='Yes',
        parameter_type='boolean',
        host=vm_module_streams.hostname,
    )
    with session:
        session.location.select(default_location.name)
        # install Module Stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Install',
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=stream_version,
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version,
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert 'Enabled' and 'Installed' in module_stream[0]['Status']

        # remove Module Stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Remove',
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=stream_version,
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version,
        )
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Enabled',
            stream_version=stream_version,
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Status'] == 'Enabled'

        # disable Module Stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Disable',
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=stream_version,
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Disabled',
            stream_version=stream_version,
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Status'] == 'Disabled'

        # reset Module Stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Reset',
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=stream_version,
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Disabled',
            stream_version=stream_version,
        )
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Unknown',
            stream_version=stream_version,
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Status'] == ''


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_module_streams_customize_action(session, default_location, vm_module_streams):
    """Check remote execution for customized module action is working on content host.

    :id: b139ea1f-380b-40a5-bb57-7530a52de18c

    :expectedresults: Remote execution for module actions should be succeed.

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: Medium
    """
    search_stream_version = '5.21'
    install_stream_version = '0.71'
    run_remote_command_on_content_host('dnf -y upload-profile', vm_module_streams)
    run_remote_command_on_content_host(
        f'dnf module reset {FAKE_2_CUSTOM_PACKAGE_NAME} -y', vm_module_streams
    )
    run_remote_command_on_content_host(
        f'dnf module reset {FAKE_2_CUSTOM_PACKAGE_NAME}', vm_module_streams
    )
    with session:
        session.location.select(default_location.name)
        # installing walrus:0.71 version
        customize_values = {
            'template_content.module_spec': (
                f'{FAKE_2_CUSTOM_PACKAGE_NAME}:{install_stream_version}'
            )
        }
        # run customize action on module streams
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Install',
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=search_stream_version,
            customize=True,
            customize_values=customize_values,
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=install_stream_version,
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == install_stream_version


@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_install_modular_errata(session, default_location, vm_module_streams):
    """Populate, Search and Install Modular Errata generated from module streams.

    :id: 3b745562-7f97-4b58-98ec-844685f5c754

    :expectedresults: Modular Errata should get installed on content host.

    :parametrized: yes

    :CaseLevel: System
    """
    stream_version = '0'
    module_name = 'kangaroo'
    run_remote_command_on_content_host('dnf -y upload-profile', vm_module_streams)
    with session:
        session.location.select(default_location.name)
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Install',
            module_name=module_name,
            stream_version=stream_version,
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'

        # downgrade rpm package to generate errata.
        run_remote_command_on_content_host(f'dnf downgrade {module_name} -y', vm_module_streams)
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            module_name,
            status='Upgrade Available',
            stream_version=stream_version,
        )
        assert module_stream[0]['Name'] == module_name

        # verify the errata
        chost = session.contenthost.read(vm_module_streams.hostname, 'errata')
        assert settings.repos.module_stream_0.errata[2] in {
            errata['Id'] for errata in chost['errata']['table']
        }

        # Install errata
        result = session.contenthost.install_errata(
            vm_module_streams.hostname, settings.repos.module_stream_0.errata[2], install_via='rex'
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'

        # ensure errata installed
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            module_name,
            status='Upgrade Available',
            stream_version=stream_version,
        )

        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            module_name,
            status='Installed',
            stream_version=stream_version,
        )
        assert module_stream[0]['Name'] == module_name


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_module_status_update_from_content_host_to_satellite(
    session, default_location, vm_module_streams, module_org
):
    """Verify dnf upload-profile updates the module stream status to Satellite.

    :id: d05042e3-1996-4293-bb01-a2a0cc5b3b91

    :expectedresults: module stream status should get updated in Satellite

    :parametrized: yes

    :CaseLevel: System
    """
    module_name = 'walrus'
    stream_version = '0.71'
    profile = 'flipper'
    run_remote_command_on_content_host('dnf -y upload-profile', vm_module_streams)

    # reset walrus module streams
    run_remote_command_on_content_host(f'dnf module reset {module_name} -y', vm_module_streams)

    # install walrus module stream with flipper profile
    run_remote_command_on_content_host(
        f'dnf module install {module_name}:{stream_version}/{profile} -y',
        vm_module_streams,
    )
    with session:
        session.location.select(default_location.name)
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version,
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Installed Profile'] == profile

        # remove walrus module stream with flipper profile
        run_remote_command_on_content_host(
            f'dnf module remove {module_name}:{stream_version}/{profile} -y',
            vm_module_streams,
        )
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version,
        )


@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_module_status_update_without_force_upload_package_profile(
    session, default_location, vm_module_streams
):
    """Verify you do not have to run dnf upload-profile or restart rhsmcertd
    to update the module stream status to Satellite and that the web UI will also be updated.

    :id: 16675b57-71c2-4aee-950b-844aa32002d1

    :expectedresults: module stream status should get updated in Satellite

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: Medium
    """
    module_name = 'walrus'
    stream_version = '0.71'
    profile = 'flipper'
    # reset walrus module streams
    run_remote_command_on_content_host(f'dnf module reset {module_name} -y', vm_module_streams)
    # make a note of time for later wait_for_tasks, and include 4 mins margin of safety.
    timestamp = (datetime.utcnow() - timedelta(minutes=4)).strftime('%Y-%m-%d %H:%M')
    # install walrus module stream with flipper profile
    run_remote_command_on_content_host(
        f'dnf module install {module_name}:{stream_version}/{profile} -y',
        vm_module_streams,
    )
    # Wait for applicability update event (in case Satellite system slow)
    wait_for_tasks(
        search_query='label = Actions::Katello::Applicability::Hosts::BulkGenerate'
        f' and started_at >= "{timestamp}"'
        f' and state = stopped'
        f' and result = success',
        search_rate=15,
        max_tries=10,
    )
    with session:
        session.location.select(default_location.name)
        # Ensure content host is searchable
        assert (
            session.contenthost.search(vm_module_streams.hostname)[0]['Name']
            == vm_module_streams.hostname
        )

        # Check web UI for the new module stream version
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version,
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Installed Profile'] == profile

        # remove walrus module stream with flipper profile
        run_remote_command_on_content_host(
            f'dnf module remove {module_name}:{stream_version}/{profile} -y',
            vm_module_streams,
        )
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version,
        )


@pytest.mark.upgrade
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_module_stream_update_from_satellite(session, default_location, vm_module_streams):
    """Verify module stream enable, update actions works and update the module stream

    :id: 8c077d7f-744b-4655-9fa2-e64ce1566d9b

    :expectedresults: module stream should get updated.

    :parametrized: yes

    :CaseLevel: System
    """
    module_name = 'duck'
    stream_version = '0'
    run_remote_command_on_content_host('dnf -y upload-profile', vm_module_streams)
    # reset duck module
    run_remote_command_on_content_host(f'dnf module reset {module_name} -y', vm_module_streams)
    with session:
        session.location.select(default_location.name)
        # enable duck module stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Enable',
            module_name=module_name,
            stream_version=stream_version,
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            module_name,
            status='Enabled',
            stream_version=stream_version,
        )
        assert module_stream[0]['Name'] == module_name
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Status'] == 'Enabled'

        # install module stream and downgrade it to generate the errata
        run_remote_command_on_content_host(
            f'dnf module install {module_name} -y', vm_module_streams
        )
        run_remote_command_on_content_host(f'dnf downgrade {module_name} -y', vm_module_streams)

        # update duck module stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Update',
            module_name=module_name,
            stream_version=stream_version,
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'

        # ensure module stream get updated
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            module_name,
            status='Upgrade Available',
            stream_version=stream_version,
        )


@pytest.mark.skip_if_not_set('clients', 'fake_manifest')
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_syspurpose_attributes_empty(session, default_location, vm_module_streams):
    """
    Test if syspurpose attributes are displayed as empty
    on a freshly provisioned and registered host.

    :id: d8ccf04f-a4eb-4c11-8376-f70857f4ef54

    :expectedresults: Syspurpose attrs are empty, and syspurpose status is set as 'Not specified'

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: High
    """
    with session:
        session.location.select(default_location.name)
        details = session.contenthost.read(vm_module_streams.hostname, widget_names='details')[
            'details'
        ]
        syspurpose_status = details['system_purpose_status']
        assert syspurpose_status.lower() == 'not specified'
        for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
            assert details[spname] == ''


@pytest.mark.skip_if_not_set('clients', 'fake_manifest')
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_set_syspurpose_attributes_cli(session, default_location, vm_module_streams):
    """
    Test that UI shows syspurpose attributes set by the syspurpose tool on a registered host.

    :id: d898a3b0-2941-4fed-a725-2b8e911bba77

    :expectedresults: Syspurpose attributes set for the content host

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: High
    """
    with session:
        session.location.select(default_location.name)
        # Set sypurpose attributes
        for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
            run_remote_command_on_content_host(
                f'syspurpose set-{spdata[0]} "{spdata[1]}"', vm_module_streams
            )

        details = session.contenthost.read(vm_module_streams.hostname, widget_names='details')[
            'details'
        ]
        for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
            assert details[spname] == spdata[1]


@pytest.mark.skip_if_not_set('clients', 'fake_manifest')
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_unset_syspurpose_attributes_cli(session, default_location, vm_module_streams):
    """
    Test that previously set syspurpose attributes are correctly set
    as empty after using 'syspurpose unset-...' on the content host.

    :id: f83ba174-20ab-4ef2-a9e2-d913d20a0b2d

    :expectedresults: Syspurpose attributes are empty

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: High
    """
    # Set sypurpose attributes...
    for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
        run_remote_command_on_content_host(
            f'syspurpose set-{spdata[0]} "{spdata[1]}"', vm_module_streams
        )
    for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
        # ...and unset them.
        run_remote_command_on_content_host(f'syspurpose unset-{spdata[0]}', vm_module_streams)

    with session:
        session.location.select(default_location.name)
        details = session.contenthost.read(vm_module_streams.hostname, widget_names='details')[
            'details'
        ]
        for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
            assert details[spname] == ''


@pytest.mark.skip_if_not_set('clients', 'fake_manifest')
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_syspurpose_matched(session, default_location, vm_module_streams):
    """
    Test that syspurpose status is set as 'Matched' if auto-attach
    is performed on the content host, and correct subscriptions are
    available on the Satellite

    :id: 6b1ca2f9-5bf2-414f-971e-6bb5add69789

    :expectedresults: Syspurpose status is Matched

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: High
    """
    run_remote_command_on_content_host('syspurpose set-sla Premium', vm_module_streams)
    run_remote_command_on_content_host('subscription-manager attach --auto', vm_module_streams)
    with session:
        session.location.select(default_location.name)
        details = session.contenthost.read(vm_module_streams.hostname, widget_names='details')[
            'details'
        ]
        assert details['system_purpose_status'] == 'Matched'


@pytest.mark.skip_if_not_set('clients', 'fake_manifest')
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL7,
            'RHELAnsibleEngineRepository': {'cdn': True},
            'SatelliteToolsRepository': {},
            'YumRepository': [
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        },
    ],
    indirect=True,
)
def test_syspurpose_bulk_action(session, default_location, vm):
    """
    Set system purpose parameters via bulk action

    :id: d084b04a-5fda-418d-ae65-a16f847c8c1d

    :bz: 1905979, 1931527

    :expectedresults: Syspurpose parameters are set and reflected on the host

    :CaseLevel: System

    :CaseImportance: High
    """
    syspurpose_attributes = {
        'service_level': 'Standard',
        'usage_type': 'Production',
        'role': 'Red Hat Enterprise Linux Server',
    }
    with session:
        session.location.select(default_location.name)
        session.contenthost.bulk_set_syspurpose([vm.hostname], syspurpose_attributes)
        details = session.contenthost.read(vm.hostname, widget_names='details')['details']
        for key, val in syspurpose_attributes.items():
            assert details[key] == val
            result = run_remote_command_on_content_host('syspurpose show', vm)
            assert val in result.stdout


@pytest.mark.skip_if_not_set('clients', 'fake_manifest')
@pytest.mark.tier3
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'distro': DISTRO_RHEL8,
            'YumRepository': [
                {'url': settings.repos.rhel8_os.baseos},
                {'url': settings.repos.rhel8_os.appstream},
                {'url': settings.repos.satutils_repo},
                {'url': settings.repos.module_stream_1.url},
            ],
        }
    ],
    indirect=True,
)
def test_syspurpose_mismatched(session, default_location, vm_module_streams):
    """
    Test that syspurpose status is 'Mismatched' if a syspurpose attribute
    is changed to a different value than the one contained in the currently
    attached subscription.

    :id: de71cfd7-eeb8-4a4c-b448-8c5aa5af7f06

    :expectedresults: Syspurpose status is 'Mismatched'

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: High
    """
    run_remote_command_on_content_host('syspurpose set-sla Premium', vm_module_streams)
    run_remote_command_on_content_host('subscription-manager attach --auto', vm_module_streams)
    run_remote_command_on_content_host('syspurpose set-sla Standard', vm_module_streams)
    with session:
        session.location.select(default_location.name)
        details = session.contenthost.read(vm_module_streams.hostname, widget_names='details')[
            'details'
        ]
        assert details['system_purpose_status'] == 'Mismatched'


@pytest.mark.tier3
def test_pagination_multiple_hosts_multiple_pages(session, module_host_template):
    """Create hosts to fill more than one page, sort on OS, check pagination.

    Search for hosts based on operating system and assert that more than one page
    is reported to exist and that more than one page can be accessed. Make some
    additonal aserts to ensure the pagination widget is working as expected.

    To avoid requiring more than 20 fakes hosts to overcome default page setting of 20,
    this test will set a new per_page default (see new_per_page_setting).
    This test is using URL method rather than the "entries_per_page" setting to avoid
    impacting other tests that might be running.

    :id: e63e4872-5fcf-4468-ab66-63ac4f4f5dac

    :customerscenario: true

    :BZ: 1642549
    """
    new_per_page_setting = 2
    host_num = new_per_page_setting + 1
    host_name = None
    start_url = f'/content_hosts?page=1&per_page={new_per_page_setting}'
    # Create more than one page of fake hosts. Need two digits in name to ensure sort order.
    for count in range(host_num):
        host_name = f'test-{count + 1:0>2}'
        make_fake_host(
            {
                'name': host_name,
                'organization-id': module_host_template.organization.id,
                'architecture-id': module_host_template.architecture.id,
                'domain-id': module_host_template.domain.id,
                'location-id': module_host_template.location.id,
                'medium-id': module_host_template.medium.id,
                'operatingsystem-id': module_host_template.operatingsystem.id,
                'partition-table-id': module_host_template.ptable.id,
            }
        )
    with session(url=start_url):
        # Search for all the hosts by os. This uses pagination to get more than one page.
        all_fake_hosts_found = session.contenthost.search(
            f'os = {module_host_template.operatingsystem.name}'
        )
        # Assert dump of fake hosts found includes the higest numbered host created for this test
        match = re.search(fr'test-{host_num:0>2}', str(all_fake_hosts_found))
        assert match, 'Highest numbered host not found.'
        # Get all the pagination values
        pagination_values = session.contenthost.read_all('Pagination')['Pagination']
        # Assert total pages reported is greater than one page of hosts
        total_pages = pagination_values['pages']
        assert int(total_pages) > int(host_num) / int(new_per_page_setting)
        # Assert that total items reported is the number of hosts created for this test
        total_items_found = pagination_values['total_items']
        assert int(total_items_found) >= host_num


@pytest.mark.tier3
def test_search_for_virt_who_hypervisors(session, default_location):
    """
    Search the virt_who hypervisors with hypervisor=True or hypervisor=False.

    :id: 3c759e13-d5ef-4273-8e64-2cc8ed9099af

    :expectedresults: Search with hypervisor=True and hypervisor=False gives the correct result.

    :BZ: 1653386

    :customerscenario: true

    :CaseLevel: System

    :CaseImportance: Medium
    """
    org = entities.Organization().create()
    with session:
        session.organization.select(org.name)
        session.location.select(default_location.name)
        assert not session.contenthost.search('hypervisor = true')
        # create virt-who hypervisor through the fake json conf
        data = create_fake_hypervisor_content(org.label, hypervisors=1, guests=1)
        hypervisor_name = data['hypervisors'][0]['hypervisorId']
        hypervisor_display_name = f'virt-who-{hypervisor_name}-{org.id}'
        # Search with hypervisor=True gives the correct result.
        assert (
            session.contenthost.search('hypervisor = true')[0]['Name']
        ) == hypervisor_display_name
        # Search with hypervisor=false gives the correct result.
        content_hosts = [host['Name'] for host in session.contenthost.search('hypervisor = false')]
        assert hypervisor_display_name not in content_hosts
