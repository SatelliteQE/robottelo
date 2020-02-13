"""Test class for Content Hosts UI

:Requirement: Content Host

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Hosts-Content

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime
from datetime import timedelta

import pytest
from airgun.session import Session
from fauxfactory import gen_integer
from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import wait_for_tasks
from robottelo.cli.factory import make_virt_who_config
from robottelo.cli.factory import virt_who_hypervisor_config
from robottelo.config import settings
from robottelo.constants import CUSTOM_MODULE_STREAM_REPO_2
from robottelo.constants import DEFAULT_SYSPURPOSE_ATTRIBUTES
from robottelo.constants import DISTRO_RHEL7
from robottelo.constants import DISTRO_RHEL8
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_GROUP_NAME
from robottelo.constants import FAKE_0_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_0_MODULAR_ERRATA_ID
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE
from robottelo.constants import FAKE_1_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_1_YUM_REPO
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE
from robottelo.constants import FAKE_2_CUSTOM_PACKAGE_NAME
from robottelo.constants import FAKE_2_ERRATA_ID
from robottelo.constants import FAKE_6_YUM_REPO
from robottelo.constants import VDC_SUBSCRIPTION_NAME
from robottelo.constants import VIRT_WHO_HYPERVISOR_TYPES
from robottelo.decorators import fixture
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import setting_is_set
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier3
from robottelo.decorators import upgrade
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.products import RepositoryCollection
from robottelo.products import RHELAnsibleEngineRepository
from robottelo.products import SatelliteToolsRepository
from robottelo.products import YumRepository
from robottelo.vm import VirtualMachine


if not setting_is_set('clients') or not setting_is_set('fake_manifest'):
    pytest.skip('skipping tests due to missing settings', allow_module_level=True)


@fixture(scope='module')
def module_org():
    org = entities.Organization().create()
    # adding remote_execution_connect_by_ip=Yes at org level
    entities.Parameter(
        name='remote_execution_connect_by_ip',
        value='Yes',
        organization=org.id
    ).create()
    return org


@fixture(scope='module', autouse=True)
def repos_collection(module_org):
    """Adds required repositories, AK, LCE and CV for content host testing"""
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL7,
        repositories=[
            RHELAnsibleEngineRepository(cdn=True),
            SatelliteToolsRepository(),
            YumRepository(url=FAKE_1_YUM_REPO),
            YumRepository(url=FAKE_6_YUM_REPO)
        ]
    )
    repos_collection.setup_content(module_org.id, lce.id, upload_manifest=True)
    return repos_collection


@fixture(scope='module', autouse=True)
def repos_collection_for_module_streams(module_org):
    """Adds required repositories, AK, LCE and CV for content host testing for
    module streams"""
    lce = entities.LifecycleEnvironment(organization=module_org).create()
    repos_collection = RepositoryCollection(
        distro=DISTRO_RHEL8,
        repositories=[
            YumRepository(url=CUSTOM_MODULE_STREAM_REPO_2)
        ]
    )
    repos_collection.setup_content(module_org.id, lce.id, upload_manifest=True)
    return repos_collection


@fixture
def vm(repos_collection):
    """Virtual machine registered in satellite with katello-agent installed"""
    with VirtualMachine(distro=repos_collection.distro) as vm:
        repos_collection.setup_virtual_machine(vm)
        yield vm


@fixture
def vm_module_streams(repos_collection_for_module_streams):
    """Virtual machine registered in satellite without katello-agent installed"""
    with VirtualMachine(distro=repos_collection_for_module_streams.distro) as vm_module_streams:
        repos_collection_for_module_streams.setup_virtual_machine(vm_module_streams,
                                                                  install_katello_agent=False)
        add_remote_execution_ssh_key(vm_module_streams.ip_addr)
        yield vm_module_streams


def set_ignore_facts_for_os(value=False):
    """Helper to set 'ignore_facts_for_operatingsystem' setting"""
    ignore_setting = entities.Setting().search(
        query={'search': 'name="ignore_facts_for_operatingsystem"'})[0]
    ignore_setting.value = str(value)
    ignore_setting.update({'value'})


def run_remote_command_on_content_host(command, vm_module_streams):
    result = vm_module_streams.run(command)
    assert result.return_code == 0


@tier3
def test_positive_end_to_end(session, repos_collection, vm):
    """Create all entities required for content host, set up host, register it
    as a content host, read content host details, install package and errata.

    :id: f43f2826-47c1-4069-9c9d-2410fd1b622c

    :expectedresults: content host details are the same as expected, package
        and errata installation are successful

    :CaseLevel: System

    :CaseImportance: Critical
    """
    result = vm.run('yum -y install {0}'.format(FAKE_1_CUSTOM_PACKAGE))
    assert result.return_code == 0
    with session:
        # Ensure content host is searchable
        assert session.contenthost.search(vm.hostname)[0]['Name'] == vm.hostname
        chost = session.contenthost.read(vm.hostname,
                                         widget_names=['details',
                                                       'provisioning_details',
                                                       'subscriptions'])
        session.contenthost.update(vm.hostname, {'repository_sets.limit_to_lce': True})
        ch_reposet = session.contenthost.read(vm.hostname, widget_names=['repository_sets'])
        chost.update(ch_reposet)
        # Ensure all content host fields/tabs have appropriate values
        assert chost['details']['name'] == vm.hostname
        assert (
            chost['details']['content_view'] ==
            repos_collection.setup_content_data['content_view']['name']
        )
        lce_name = repos_collection.setup_content_data['lce']['name']
        assert chost['details']['lce'][lce_name][lce_name]
        assert (
            chost['details']['registered_by'] == 'Activation Key {}'
            .format(repos_collection.setup_content_data['activation_key']['name'])
        )
        assert chost['provisioning_details']['name'] == vm.hostname
        assert (
            repos_collection.custom_product['name'] in
            {repo['Repository Name'] for repo in chost['subscriptions']['resources']['assigned']}

        )
        actual_repos = {repo['Repository Name'] for repo in chost['repository_sets']['table']}
        expected_repos = {
            repos_collection.repos_data[repo_index].get(
                'repository-set',
                repos_collection.repos_info[repo_index]['name']
            )
            for repo_index in range(len(repos_collection.repos_info))
        }
        assert actual_repos == expected_repos
        # Update description
        new_description = gen_string('alpha')
        session.contenthost.update(vm.hostname, {'details.description': new_description})
        chost = session.contenthost.read(vm.hostname, widget_names='details')
        assert chost['details']['description'] == new_description
        # Install package
        result = session.contenthost.execute_package_action(
            vm.hostname,
            'Package Install',
            FAKE_0_CUSTOM_PACKAGE_NAME,
        )
        assert result['result'] == 'success'
        # Ensure package installed
        packages = session.contenthost.search_package(vm.hostname, FAKE_0_CUSTOM_PACKAGE_NAME)
        assert packages[0]['Installed Package'] == FAKE_0_CUSTOM_PACKAGE
        # Install errata
        result = session.errata.install(FAKE_2_ERRATA_ID, vm.hostname)
        assert result['result'] == 'success'
        # Ensure errata installed
        packages = session.contenthost.search_package(vm.hostname, FAKE_2_CUSTOM_PACKAGE_NAME)
        assert packages[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE
        # Delete content host
        session.contenthost.delete(vm.hostname)

        assert not session.contenthost.search(vm.hostname)


@upgrade
@tier3
def test_positive_end_to_end_bulk_update(session, vm):
    """Create VM, set up VM as host, register it as a content host,
    read content host details, install a package ( e.g. walrus-0.71) and
    use bulk action (Update All Packages) to update the package by name
    to a later version.

    :id: d460ba30-82c7-11e9-9af5-54ee754f2151

    :expectedresults: package installation and update to a later version
        are successful.

    :BZ: 1712069

    :CaseLevel: System
    """
    hc_name = gen_string('alpha')
    description = gen_string('alpha')
    result = vm.run('yum -y install {0}'.format(FAKE_1_CUSTOM_PACKAGE))
    assert result.return_code == 0
    with session:
        # Ensure content host is searchable
        assert session.contenthost.search(vm.hostname)[0]['Name'] == vm.hostname
        # Update package using bulk action
        # use the Host Collection view to access Update Packages dialogue
        session.hostcollection.create({
            'name': hc_name,
            'unlimited_hosts': False,
            'max_hosts': 2,
            'description': description
        })
        session.hostcollection.associate_host(hc_name, vm.hostname)
        # make a note of time for later CLI wait_for_tasks, and include
        # 5 mins margin of safety.
        timestamp = (datetime.utcnow() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
        # Update the package by name
        session.hostcollection.manage_packages(
            hc_name, content_type='Package',
            packages=FAKE_1_CUSTOM_PACKAGE_NAME,
            action='update_all'
        )
        # Wait for upload profile event (in case Satellite system slow)
        host = entities.Host().search(
            query={'search': 'name={}'.format(vm.hostname)})
        wait_for_tasks(
            search_query='label = Actions::Katello::Host::UploadProfiles'
                         ' and resource_id = {}'
                         ' and started_at >= "{}"'.format(
                             host[0].id, timestamp),
            search_rate=15, max_tries=10,
        )
        # Ensure package updated to a later version
        packages = session.contenthost.search_package(vm.hostname, FAKE_2_CUSTOM_PACKAGE_NAME)
        assert packages[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE
        # Delete content host
        session.contenthost.delete(vm.hostname)


@tier3
def test_positive_search_by_subscription_status(session, vm):
    """Register host into the system and search for it afterwards by
    subscription status

    :id: b4d24ee7-51b9-43e4-b0c9-7866b6340ce1

    :expectedresults: Validate that host can be found for valid
        subscription status and that host is not present in the list for
        invalid status

    :BZ: 1406855, 1498827, 1495271

    :CaseLevel: System
    """
    with session:
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


@tier3
def test_negative_install_package(session, vm):
    """Attempt to install non-existent package to a host remotely

    :id: d60b70f9-c43f-49c0-ae9f-187ffa45ac97

    :customerscenario: true

    :BZ: 1262940

    :expectedresults: Task finished with warning

    :CaseLevel: System
    """
    with session:
        result = session.contenthost.execute_package_action(
            vm.hostname,
            'Package Install',
            gen_string('alphanumeric')
        )
        assert result['result'] == 'warning'


@tier3
def test_positive_remove_package(session, vm):
    """Remove a package from a host remotely

    :id: 86d8896b-06d9-4c99-937e-f3aa07b4eb69

    :expectedresults: Package was successfully removed

    :CaseLevel: System
    """
    vm.download_install_rpm(FAKE_6_YUM_REPO, FAKE_0_CUSTOM_PACKAGE)
    with session:
        result = session.contenthost.execute_package_action(
            vm.hostname,
            'Package Remove',
            FAKE_0_CUSTOM_PACKAGE_NAME,
        )
        assert result['result'] == 'success'
        packages = session.contenthost.search_package(vm.hostname, FAKE_0_CUSTOM_PACKAGE_NAME)
        assert not packages


@tier3
def test_positive_upgrade_package(session, vm):
    """Upgrade a host package remotely

    :id: 1969db93-e7af-4f5f-973d-23c222224db6

    :expectedresults: Package was successfully upgraded

    :CaseLevel: System
    """
    vm.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
    with session:
        result = session.contenthost.execute_package_action(
            vm.hostname,
            'Package Update',
            FAKE_1_CUSTOM_PACKAGE_NAME,
        )
        assert result['result'] == 'success'
        packages = session.contenthost.search_package(vm.hostname, FAKE_2_CUSTOM_PACKAGE)
        assert packages[0]['Installed Package'] == FAKE_2_CUSTOM_PACKAGE


@tier3
@upgrade
def test_positive_install_package_group(session, vm):
    """Install a package group to a host remotely

    :id: a43fb21b-5f6a-4f14-8cd6-114ec287540c

    :expectedresults: Package group was successfully installed

    :CaseLevel: System
    """
    with session:
        result = session.contenthost.execute_package_action(
            vm.hostname,
            'Group Install',
            FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
        )
        assert result['result'] == 'success'
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            packages = session.contenthost.search_package(vm.hostname, package)
            assert packages[0]['Installed Package'] == package


@tier3
def test_positive_remove_package_group(session, vm):
    """Remove a package group from a host remotely

    :id: dbeea1f2-adf4-4ad8-a989-efad8ce21b98

    :expectedresults: Package group was successfully removed

    :CaseLevel: System
    """
    with session:
        for action in ('Group Install', 'Group Remove'):
            result = session.contenthost.execute_package_action(
                vm.hostname,
                action,
                FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            )
            assert result['result'] == 'success'
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            assert not session.contenthost.search_package(vm.hostname, package)


@tier3
def test_positive_search_errata_non_admin(session, vm, module_org, test_name, module_viewer_user):
    """Search for host's errata by non-admin user with enough permissions

    :id: 5b8887d2-987f-4bce-86a1-8f65ca7e1195

    :customerscenario: true

    :BZ: 1255515, 1662405, 1652938

    :expectedresults: User can access errata page and proper errata is
        listed

    :CaseLevel: System
    """
    vm.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
    with Session(
            test_name, user=module_viewer_user.login, password=module_viewer_user.password
    ) as session:
        chost = session.contenthost.read(vm.hostname, widget_names='errata')
        assert FAKE_2_ERRATA_ID in {errata['Id'] for errata in chost['errata']['table']}


@tier3
@upgrade
def test_positive_ensure_errata_applicability_with_host_reregistered(session, vm):
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

    :CaseLevel: System
    """
    vm.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
    result = vm.run('rpm -q {0}'.format(FAKE_1_CUSTOM_PACKAGE))
    assert result.return_code == 0
    result = vm.run('subscription-manager refresh  && yum repolist')
    assert result.return_code == 0
    with session:
        chost = session.contenthost.read(vm.hostname, widget_names='errata')
        assert FAKE_2_ERRATA_ID in {errata['Id'] for errata in chost['errata']['table']}
        result = vm.run('subscription-manager refresh  && yum repolist')
        assert result.return_code == 0
        chost = session.contenthost.read(vm.hostname, widget_names='errata')
        assert FAKE_2_ERRATA_ID in {errata['Id'] for errata in chost['errata']['table']}


@tier3
def test_positive_host_re_registion_with_host_rename(session, module_org, repos_collection, vm):
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

    :CaseLevel: System
    """
    vm.run('yum install -y {0}'.format(FAKE_1_CUSTOM_PACKAGE))
    result = vm.run('rpm -q {0}'.format(FAKE_1_CUSTOM_PACKAGE))
    assert result.return_code == 0
    vm.unregister()
    updated_hostname = '{}.{}'.format(gen_string('alpha'), vm.hostname).lower()
    vm.run('hostnamectl set-hostname {}'.format(updated_hostname))
    assert result.return_code == 0
    vm.register_contenthost(
        module_org.name,
        activation_key=repos_collection.setup_content_data['activation_key']['name']
    )
    assert result.return_code == 0
    with session:
        assert session.contenthost.search(updated_hostname)[0]['Name'] == updated_hostname


@run_in_one_thread
@tier3
@upgrade
def test_positive_check_ignore_facts_os_setting(session, vm, module_org, request):
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

    :CaseLevel: System
    """
    major = str(gen_integer(15, 99))
    minor = str(gen_integer(1, 9))
    expected_os = "RedHat {}.{}".format(major, minor)
    set_ignore_facts_for_os(False)
    host = entities.Host().search(query={
        'search': 'name={0} and organization_id={1}'.format(
            vm.hostname, module_org.id)
    })[0].read()
    with session:
        # Get host current operating system value
        os = session.contenthost.read(vm.hostname, widget_names='details')['details']['os']
        # Change necessary setting to true
        set_ignore_facts_for_os(True)
        # Add cleanup function to roll back setting to default value
        request.addfinalizer(set_ignore_facts_for_os)
        # Read all facts for corresponding host
        facts = host.get_facts(data={u'per_page': 10000})['results'][vm.hostname]
        # Modify OS facts to another values and upload them to the server
        # back
        facts['operatingsystem'] = 'RedHat'
        facts['osfamily'] = 'RedHat'
        facts['operatingsystemmajrelease'] = major
        facts['operatingsystemrelease'] = "{}.{}".format(major, minor)
        host.upload_facts(data={
            u'name': vm.hostname,
            u'facts': facts,
        })
        session.contenthost.search('')
        updated_os = session.contenthost.read(vm.hostname, widget_names='details')['details']['os']
        # Check that host OS was not changed due setting was set to true
        assert os == updated_os
        # Put it to false and re-run the process
        set_ignore_facts_for_os(False)
        host.upload_facts(data={
            u'name': vm.hostname,
            u'facts': facts,
        })
        session.contenthost.search('')
        updated_os = session.contenthost.read(vm.hostname, widget_names='details')['details']['os']
        # Check that host OS was changed to new value
        assert os != updated_os
        assert updated_os == expected_os
        # Check that new OS was created
        assert session.operatingsystem.search(expected_os)[0]['Title'] == expected_os


@skip_if_not_set('clients', 'fake_manifest', 'compute_resources')
@tier3
@upgrade
def test_positive_virt_who_hypervisor_subscription_status(session):
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

    :BZ: 1336924

    :CaseLevel: System
    """
    org = entities.Organization().create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    provisioning_server = settings.compute_resources.libvirt_hostname
    # Create a new virt-who config
    virt_who_config = make_virt_who_config({
        'organization-id': org.id,
        'hypervisor-type': VIRT_WHO_HYPERVISOR_TYPES['libvirt'],
        'hypervisor-server': 'qemu+ssh://{0}/system'.format(provisioning_server),
        'hypervisor-username': 'root',
    })
    # create a virtual machine to host virt-who service
    with VirtualMachine() as virt_who_vm:
        # configure virtual machine and setup virt-who service
        # do not supply subscription to attach to virt_who hypervisor
        virt_who_data = virt_who_hypervisor_config(
            virt_who_config['general-information']['id'],
            virt_who_vm,
            org_id=org.id,
            lce_id=lce.id,
            hypervisor_hostname=provisioning_server,
            configure_ssh=True,
        )
        virt_who_hypervisor_host = virt_who_data[
            'virt_who_hypervisor_host']
        with session:
            session.organization.select(org.name)
            assert session.contenthost.search(
                virt_who_hypervisor_host['name'])[0]['Subscription Status'] == 'yellow'
            chost = session.contenthost.read(
                virt_who_hypervisor_host['name'],
                widget_names='details')
            assert chost['details']['subscription_status'] == 'Unsubscribed hypervisor'
            session.contenthost.add_subscription(
                virt_who_hypervisor_host['name'], VDC_SUBSCRIPTION_NAME)
            assert session.contenthost.search(
                virt_who_hypervisor_host['name'])[0]['Subscription Status'] == 'green'
            chost = session.contenthost.read(
                virt_who_hypervisor_host['name'],
                widget_names='details')
            assert chost['details']['subscription_status'] == 'Fully entitled'


@upgrade
@tier3
def test_module_stream_actions_on_content_host(session, vm_module_streams):
    """Check remote execution for module streams actions e.g. install, remove, disable
    works on content host. Verify that correct stream module stream
    get installed/removed.

    :id: 684e467e-b41c-4b95-8450-001abe85abe0

    :expectedresults: Remote execution for module actions should succeed.

    :CaseLevel: System
    """
    stream_version = "5.21"
    run_remote_command_on_content_host(
        'dnf -y upload-profile',
        vm_module_streams
    )
    with session:
        entities.Parameter(
            name='remote_execution_connect_by_ip',
            value='Yes',
            host=vm_module_streams.hostname
        )
        # install Module Stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type="Install",
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=stream_version
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert 'Enabled' and 'Installed' in module_stream[0]['Status']

        # remove Module Stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type="Remove",
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=stream_version
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version
        )
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Enabled',
            stream_version=stream_version
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Status'] == "Enabled"

        # disable Module Stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Disable',
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=stream_version
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Disabled',
            stream_version=stream_version
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Status'] == "Disabled"

        # reset Module Stream
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Reset',
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=stream_version
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Disabled',
            stream_version=stream_version
        )
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Unknown',
            stream_version=stream_version
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Status'] == ""


@tier3
def test_module_streams_customize_action(session, vm_module_streams):
    """Check remote execution for customized module action is working on content host.

    :id: b139ea1f-380b-40a5-bb57-7530a52de18c

    :expectedresults: Remote execution for module actions should be succeed.

    :CaseLevel: System

    :CaseImportance: Medium
    """
    with session:
        search_stream_version = "5.21"
        install_stream_version = "0.71"
        run_remote_command_on_content_host(
            'dnf -y upload-profile',
            vm_module_streams
        )
        run_remote_command_on_content_host(
            'dnf module reset {} -y'.format(FAKE_2_CUSTOM_PACKAGE_NAME),
            vm_module_streams
        )
        run_remote_command_on_content_host(
            'dnf module reset {}'.format(FAKE_2_CUSTOM_PACKAGE_NAME),
            vm_module_streams
        )

        # installing walrus:0.71 version
        customize_values = {
                'template_content.module_spec': '{}:{}'.format(
                    FAKE_2_CUSTOM_PACKAGE_NAME,
                    install_stream_version
                ),
        }
        # run customize action on module streams
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Install',
            module_name=FAKE_2_CUSTOM_PACKAGE_NAME,
            stream_version=search_stream_version,
            customize=True,
            customize_values=customize_values
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=install_stream_version
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == install_stream_version


@upgrade
@tier3
def test_install_modular_errata(session, vm_module_streams):
    """Populate, Search and Install Modular Errata generated from module streams.

    :id: 3b745562-7f97-4b58-98ec-844685f5c754

    :expectedresults: Modular Errata should get installed on content host.

    :CaseLevel: System
    """
    with session:
        stream_version = "0"
        module_name = "kangaroo"
        run_remote_command_on_content_host(
            'dnf -y upload-profile',
            vm_module_streams
        )
        result = session.contenthost.execute_module_stream_action(
            vm_module_streams.hostname,
            action_type='Install',
            module_name=module_name,
            stream_version=stream_version,
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'

        # downgrade rpm package to generate errata.
        run_remote_command_on_content_host(
            'dnf downgrade {} -y'.format(module_name),
            vm_module_streams
        )
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            module_name,
            status='Upgrade Available',
            stream_version=stream_version
        )
        assert module_stream[0]['Name'] == module_name

        # verify the errata
        chost = session.contenthost.read(vm_module_streams.hostname, 'errata')
        assert FAKE_0_MODULAR_ERRATA_ID in {errata['Id'] for errata in chost['errata']['table']}

        # Install errata
        result = session.contenthost.install_errata(
            vm_module_streams.hostname,
            FAKE_0_MODULAR_ERRATA_ID,
            install_via='rex'
        )
        assert result['overview']['hosts_table'][0]['Status'] == 'success'

        # ensure errata installed
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            module_name,
            status='Upgrade Available',
            stream_version=stream_version
        )


@tier3
def test_module_status_update_from_content_host_to_satellite(session, vm_module_streams):
    """ Verify dnf upload-profile updates the module stream status to Satellite.

    :id: d05042e3-1996-4293-bb01-a2a0cc5b3b91

    :expectedresults: module stream status should get updated in Satellite

    :CaseLevel: System
    """
    with session:
        module_name = "walrus"
        stream_version = "0.71"
        profile = "flipper"
        run_remote_command_on_content_host(
            'dnf -y upload-profile',
            vm_module_streams
        )

        # reset walrus module streams
        run_remote_command_on_content_host(
            'dnf module reset {} -y'.format(module_name),
            vm_module_streams
        )

        # install walrus module stream with flipper profile
        run_remote_command_on_content_host(
            'dnf module install {}:{}/{} -y'.format(
                module_name,
                stream_version,
                profile
            ),
            vm_module_streams
        )

        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Installed Profile'] == profile

        # remove walrus module stream with flipper profile
        run_remote_command_on_content_host(
            'dnf module remove {}:{}/{} -y'.format(
                module_name,
                stream_version,
                profile
            ),
            vm_module_streams
        )
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version
        )


@tier3
def test_module_status_update_without_force_upload_package_profile(session, vm, vm_module_streams):
    """ Verify you do not have to run dnf upload-profile or restart rhsmcertd
    to update the module stream status to Satellite and that the web UI will also be updated.

    :id: 16675b57-71c2-4aee-950b-844aa32002d1

    :expectedresults: module stream status should get updated in Satellite

    :CaseLevel: System

    :CaseImportance: Medium
    """
    with session:
        # Ensure content host is searchable
        assert session.contenthost.search(vm.hostname)[0]['Name'] == vm.hostname
        module_name = "walrus"
        stream_version = "0.71"
        profile = "flipper"
        # reset walrus module streams
        run_remote_command_on_content_host(
            'dnf module reset {} -y'.format(module_name),
            vm_module_streams
        )
        # make a note of time for later CLI wait_for_tasks, and include
        # 5 mins margin of safety.
        timestamp = (datetime.utcnow() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
        # install walrus module stream with flipper profile
        run_remote_command_on_content_host(
            'dnf module install {}:{}/{} -y'.format(
                module_name,
                stream_version,
                profile
            ),
            vm_module_streams
        )
        # Wait for upload profile event (in case Satellite system slow)
        host = entities.Host().search(
            query={'search': 'name={}'.format(vm.hostname)})
        wait_for_tasks(
            search_query='label = Actions::Katello::Host::UploadProfiles'
                         ' and resource_id = {}'
                         ' and started_at >= "{}"'.format(
                             host[0].id, timestamp),
            search_rate=15, max_tries=10,
        )
        # Check web UI for the new module stream version
        module_stream = session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version
        )
        assert module_stream[0]['Name'] == FAKE_2_CUSTOM_PACKAGE_NAME
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Installed Profile'] == profile

        # remove walrus module stream with flipper profile
        run_remote_command_on_content_host(
            'dnf module remove {}:{}/{} -y'.format(
                module_name,
                stream_version,
                profile
            ),
            vm_module_streams
        )
        assert not session.contenthost.search_module_stream(
            vm_module_streams.hostname,
            FAKE_2_CUSTOM_PACKAGE_NAME,
            status='Installed',
            stream_version=stream_version
        )


@upgrade
@tier3
def test_module_stream_update_from_satellite(session, vm_module_streams):
    """ Verify module stream enable, update actions works and update the module stream

    :id: 8c077d7f-744b-4655-9fa2-e64ce1566d9b

    :expectedresults: module stream should get updated.

    :CaseLevel: System
    """
    with session:
        module_name = "duck"
        stream_version = "0"
        run_remote_command_on_content_host(
            'dnf -y upload-profile',
            vm_module_streams
        )
        # reset duck module
        run_remote_command_on_content_host(
            'dnf module reset {} -y'.format(module_name),
            vm_module_streams
        )

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
            stream_version=stream_version
        )
        assert module_stream[0]['Name'] == module_name
        assert module_stream[0]['Stream'] == stream_version
        assert module_stream[0]['Status'] == "Enabled"

        # install module stream and downgrade it to generate the errata
        run_remote_command_on_content_host(
            'dnf module install {} -y'.format(module_name),
            vm_module_streams
        )
        run_remote_command_on_content_host(
            'dnf downgrade {} -y'.format(module_name),
            vm_module_streams
        )

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
            stream_version=stream_version
        )


@skip_if_not_set('clients', 'fake_manifest')
@tier3
def test_syspurpose_attributes_empty(session, vm_module_streams):
    """
    Test if syspurpose attributes are displayed as empty
    on a freshly provisioned and registered host.

    :id: d8ccf04f-a4eb-4c11-8376-f70857f4ef54

    :expectedresults: Syspurpose attrs are empty, and syspurpose status is set as 'Not specified'

    :CaseLevel: System

    :CaseImportance: High
    """
    with session:
        details = session.contenthost.read(
            vm_module_streams.hostname,
            widget_names='details')['details']
        syspurpose_status = details['system_purpose_status']
        assert syspurpose_status.lower() == "not specified"
        for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
            assert details[spname] == ''


@skip_if_not_set('clients', 'fake_manifest')
@tier3
def test_set_syspurpose_attributes_cli(session, vm_module_streams):
    """
    Test that UI shows syspurpose attributes set by the syspurpose tool on a registered host.

    :id: d898a3b0-2941-4fed-a725-2b8e911bba77

    :expectedresults: Syspurpose attributes set for the content host

    :CaseLevel: System

    :CaseImportance: High
    """
    with session:
        # Set sypurpose attributes
        for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
            run_remote_command_on_content_host(
                'syspurpose set-{0} "{1}"'.format(*spdata), vm_module_streams)

        details = session.contenthost.read(
            vm_module_streams.hostname, widget_names='details')['details']
        for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
            assert details[spname] == spdata[1]


@skip_if_not_set('clients', 'fake_manifest')
@tier3
def test_unset_syspurpose_attributes_cli(session, vm_module_streams):
    """
    Test that previously set syspurpose attributes are correctly set
    as empty after using 'syspurpose unset-...' on the content host.

    :id: f83ba174-20ab-4ef2-a9e2-d913d20a0b2d

    :expectedresults: Syspurpose attributes are empty

    :CaseLevel: System

    :CaseImportance: High
    """
    # Set sypurpose attributes...
    for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
        run_remote_command_on_content_host(
            'syspurpose set-{0} "{1}"'.format(*spdata), vm_module_streams)
    for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
        # ...and unset them.
        run_remote_command_on_content_host(
            'syspurpose unset-{0}'.format(*spdata), vm_module_streams)

    with session:
        details = session.contenthost.read(
            vm_module_streams.hostname, widget_names='details')['details']
        for spname, spdata in DEFAULT_SYSPURPOSE_ATTRIBUTES.items():
            assert details[spname] == ''


@skip_if_not_set('clients', 'fake_manifest')
@tier3
def test_syspurpose_matched(session, vm_module_streams):
    """
    Test that syspurpose status is set as 'Matched' if auto-attach
    is performed on the content host, and correct subscriptions are
    available on the Satellite

    :id: 6b1ca2f9-5bf2-414f-971e-6bb5add69789

    :expectedresults: Syspurpose status is Matched

    :CaseLevel: System

    :CaseImportance: High
    """
    run_remote_command_on_content_host(
        'syspurpose set-sla Premium', vm_module_streams)
    run_remote_command_on_content_host(
        "subscription-manager attach --auto", vm_module_streams)
    with session:
        details = session.contenthost.read(
            vm_module_streams.hostname, widget_names='details')['details']
        assert details['system_purpose_status'] == "Matched"


@skip_if_not_set('clients', 'fake_manifest')
@tier3
def test_syspurpose_mismatched(session, vm_module_streams):
    """
    Test that syspurpose status is 'Mismatched' if a syspurpose attribute
    is changed to a different value than the one contained in the currently
    attached subscription.

    :id: de71cfd7-eeb8-4a4c-b448-8c5aa5af7f06

    :expectedresults: Syspurpose status is 'Mismatched'

    :CaseLevel: System

    :CaseImportance: High
    """
    run_remote_command_on_content_host(
        'syspurpose set-sla Premium', vm_module_streams)
    run_remote_command_on_content_host(
        'subscription-manager attach --auto', vm_module_streams)
    run_remote_command_on_content_host(
        'syspurpose set-sla Standard', vm_module_streams)
    with session:
        details = session.contenthost.read(
            vm_module_streams.hostname, widget_names='details')['details']
        assert details['system_purpose_status'] == "Mismatched"
