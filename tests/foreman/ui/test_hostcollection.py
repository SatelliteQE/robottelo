"""Test class for Host Collection UI

:Requirement: Hostcollection

:CaseAutomation: Automated

:CaseComponent: HostCollections

:team: Phoenix-subscriptions

:CaseImportance: High

"""

import time

from broker import Broker
from manifester import Manifester
import pytest

from robottelo import constants
from robottelo.config import settings
from robottelo.hosts import ContentHost
from robottelo.utils.datafactory import gen_string


@pytest.fixture(scope='module')
def module_manifest():
    with Manifester(manifest_category=settings.manifest.golden_ticket) as manifest:
        yield manifest


@pytest.fixture(scope='module')
def module_org_with_parameter(module_target_sat, module_manifest):
    # adding remote_execution_connect_by_ip=Yes at org level
    org = module_target_sat.api.Organization().create()
    module_target_sat.api.Parameter(
        name='remote_execution_connect_by_ip',
        parameter_type='boolean',
        value='Yes',
        organization=org.id,
    ).create()
    module_target_sat.upload_manifest(org.id, module_manifest.content)
    return org


@pytest.fixture(scope='module')
def module_lce(module_target_sat, module_org_with_parameter):
    return module_target_sat.api.LifecycleEnvironment(
        organization=module_org_with_parameter
    ).create()


@pytest.fixture(scope='module')
def module_repos_collection(module_org_with_parameter, module_lce, module_target_sat):
    repos_collection = module_target_sat.cli_factory.RepositoryCollection(
        distro=constants.DISTRO_DEFAULT,
        repositories=[
            module_target_sat.cli_factory.SatelliteToolsRepository(),
            module_target_sat.cli_factory.YumRepository(url=settings.repos.yum_1.url),
            module_target_sat.cli_factory.YumRepository(url=settings.repos.yum_6.url),
        ],
    )
    repos_collection.setup_content(module_org_with_parameter.id, module_lce.id, override=True)
    return repos_collection


@pytest.fixture
def vm_content_hosts(smart_proxy_location, module_repos_collection, module_target_sat):
    distro = module_repos_collection.distro
    with Broker(nick=distro, host_class=ContentHost, _count=2) as clients:
        for client in clients:
            module_repos_collection.setup_virtual_machine(client)
            client.add_rex_key(satellite=module_target_sat)
            module_target_sat.api_factory.update_vm_host_location(client, smart_proxy_location.id)
        yield clients


@pytest.fixture
def vm_content_hosts_module_stream(
    smart_proxy_location, module_repos_collection_with_manifest, module_target_sat
):
    with Broker(nick='rhel8', host_class=ContentHost, _count=2) as clients:
        for client in clients:
            module_repos_collection_with_manifest.setup_virtual_machine(client)
            client.add_rex_key(satellite=module_target_sat)
            module_target_sat.api_factory.update_vm_host_location(client, smart_proxy_location.id)
        yield clients


@pytest.fixture
def vm_host_collection(module_target_sat, module_org_with_parameter, vm_content_hosts):
    host_ids = [
        module_target_sat.api.Host().search(query={'search': f'name={host.hostname}'})[0].id
        for host in vm_content_hosts
    ]
    return module_target_sat.api.HostCollection(
        host=host_ids, organization=module_org_with_parameter
    ).create()


@pytest.fixture
def vm_host_collection_module_stream(
    module_target_sat, module_org_with_parameter, vm_content_hosts_module_stream
):
    host_ids = [
        module_target_sat.api.Host().search(query={'search': f'name={host.hostname}'})[0].id
        for host in vm_content_hosts_module_stream
    ]
    return module_target_sat.api.HostCollection(
        host=host_ids, organization=module_org_with_parameter
    ).create()


def _run_remote_command_on_content_hosts(command, vm_clients):
    """run remote command on content hosts"""
    for vm_client in vm_clients:
        result = vm_client.run(command)
        assert result.status == 0


def _is_package_installed(
    vm_clients, package_name, expect_installed=True, retries=10, iteration_sleep=15
):
    """Check whether package name was installed on the list of Virtual Machines
    clients.
    """
    assert len(vm_clients) > 0
    installed = 0
    if not expect_installed:
        installed = len(vm_clients)
    for vm_client in vm_clients:
        for ind in range(retries):
            result = vm_client.run(f'rpm -q {package_name}')
            if result.status == 0 and expect_installed:
                installed += 1
                break
            if result.status != 0 and not expect_installed:
                installed -= 1
                break
            if ind < retries - 1:
                time.sleep(iteration_sleep)
        else:
            break

    if expect_installed:
        return installed == len(vm_clients)
    return bool(installed)


def _install_package_with_assertion(vm_clients, package_name):
    """Install package in Virtual machine clients and assert installed"""
    for client in vm_clients:
        result = client.run(f'yum install -y {package_name}')
        assert result.status == 0
    assert _is_package_installed(vm_clients, package_name)


def _get_content_repository_urls(repos_collection, lce, content_view, module_target_sat):
    """Returns a list of the content repository urls"""
    repos_urls = [
        '/'.join(
            [
                module_target_sat.url,
                'pulp',
                'content',
                repos_collection.organization["label"],
                lce.name,
                content_view.name,
                'custom',
                repos_collection.custom_product["label"],
                repository["name"],
            ]
        )
        for repository in repos_collection.custom_repos_info
    ]
    # add sat-tool rh repo
    # Note: if sat-tools is not cdn it must be already in repos_urls
    for repo in repos_collection:
        if isinstance(repo, module_target_sat.cli_factory.SatelliteToolsRepository) and repo.cdn:
            repos_urls.append(
                '/'.join(
                    [
                        module_target_sat.url,
                        'pulp',
                        'content',
                        repos_collection.organization["label"],
                        lce.name,
                        content_view.name,
                        'content',
                        'dist',
                        'rhel',
                        'server',
                        str(repo.distro_major_version),
                        f'{repo.distro_major_version}Server',
                        '$basearch',
                        'sat-tools',
                        repo.repo_data["version"],
                        'os',
                    ]
                )
            )
    return repos_urls


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_end_to_end(module_target_sat, module_org_with_parameter, smart_proxy_location):
    """Perform end to end testing for host collection component

    :id: 1d40bc74-8e05-42fa-b6e3-2999dc3b730d

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: High
    """
    hc_name = gen_string('alpha')
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    host = module_target_sat.api.Host(
        organization=module_org_with_parameter, location=smart_proxy_location
    ).create()
    with module_target_sat.ui_session() as session:
        session.organization.select(module_org_with_parameter.name)
        session.location.select(smart_proxy_location.name)
        # Create new host collection
        session.hostcollection.create(
            {'name': hc_name, 'unlimited_hosts': False, 'max_hosts': 2, 'description': description}
        )
        assert session.hostcollection.search(hc_name)[0]['Name'] == hc_name
        session.hostcollection.associate_host(hc_name, host.name)
        hc_values = session.hostcollection.read(hc_name, widget_names=['details', 'hosts'])
        assert hc_values['details']['name'] == hc_name
        assert hc_values['details']['description'] == description
        assert hc_values['details']['content_hosts'] == '1'
        assert hc_values['details']['content_host_limit'] == '2'
        assert hc_values['hosts']['resources']['assigned'][0]['Name'] == host.name

        # View host collection on dashboard
        values = session.dashboard.read('HostCollections')
        assert [hc_name, '1'] in [
            [coll['Name'], coll['Content Hosts']] for coll in values['collections']
        ]

        # Update host collection with new name
        session.hostcollection.update(hc_name, {'details.name': new_name})
        assert session.hostcollection.search(new_name)[0]['Name'] == new_name
        # Delete host collection
        session.hostcollection.delete(new_name)
        assert not session.hostcollection.search(new_name)


@pytest.mark.tier2
def test_negative_install_via_remote_execution(
    session, module_target_sat, module_org_with_parameter, smart_proxy_location
):
    """Test basic functionality of the Hosts collection UI install package via
    remote execution.

    :id: c5fe46fb-0b34-4ea3-bc53-e86c18adaf94

    :setup: Create a host collection with two fake hosts assigned.

    :expectedresults: The package is not installed, and the job invocation
        status contains some expected values: hosts information, jos status.
    """
    hosts = []
    for _ in range(2):
        hosts.append(
            module_target_sat.api.Host(
                organization=module_org_with_parameter, location=smart_proxy_location
            ).create()
        )
    host_collection = module_target_sat.api.HostCollection(
        host=[host.id for host in hosts], organization=module_org_with_parameter
    ).create()
    with session:
        session.location.select(smart_proxy_location.name)
        job_values = session.hostcollection.manage_packages(
            host_collection.name,
            packages=constants.FAKE_0_CUSTOM_PACKAGE_NAME,
            action='install',
            action_via='via remote execution',
        )
        assert job_values['job_status'] == 'Failed'
        assert job_values['job_status_progress'] == '100%'
        assert int(job_values['total_hosts']) == len(hosts)
        assert {host.name for host in hosts} == {host['Host'] for host in job_values['hosts_table']}


@pytest.mark.tier2
def test_negative_install_via_custom_remote_execution(
    session, module_target_sat, module_org_with_parameter, smart_proxy_location
):
    """Test basic functionality of the Hosts collection UI install package via
    remote execution - customize first.

    :id: 5aa7f084-bab7-4e62-9bf3-a37fd4aa71fa

    :setup: Create a host collection with two fake hosts assigned.

    :expectedresults: The package is not installed, and the job invocation
        status contains some expected values: hosts information, jos status.
    """
    hosts = []
    for _ in range(2):
        hosts.append(
            module_target_sat.api.Host(
                organization=module_org_with_parameter, location=smart_proxy_location
            ).create()
        )
    host_collection = module_target_sat.api.HostCollection(
        host=[host.id for host in hosts], organization=module_org_with_parameter
    ).create()
    with session:
        session.location.select(smart_proxy_location.name)
        job_values = session.hostcollection.manage_packages(
            host_collection.name,
            packages=constants.FAKE_0_CUSTOM_PACKAGE_NAME,
            action='install',
            action_via='via remote execution - customize first',
        )
        assert job_values['job_status'] == 'Failed'
        assert job_values['job_status_progress'] == '100%'
        assert int(job_values['total_hosts']) == len(hosts)
        assert {host.name for host in hosts} == {host['Host'] for host in job_values['hosts_table']}


@pytest.mark.upgrade
@pytest.mark.tier3
def test_positive_add_host(session, module_target_sat):
    """Check if host can be added to Host Collection

    :id: 80824c9f-15a1-4f76-b7ac-7d9ca9f6ed9e

    :expectedresults: Host is added to Host Collection successfully
    """
    hc_name = gen_string('alpha')
    org = module_target_sat.api.Organization().create()
    loc = module_target_sat.api.Location().create()
    cv = module_target_sat.api.ContentView(organization=org).create()
    lce = module_target_sat.api.LifecycleEnvironment(organization=org).create()
    cv.publish()
    cv.read().version[0].promote(data={'environment_ids': lce.id})
    host = module_target_sat.api.Host(
        organization=org,
        location=loc,
        content_facet_attributes={'content_view_id': cv.id, 'lifecycle_environment_id': lce.id},
    ).create()
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        session.hostcollection.create({'name': hc_name})
        assert session.hostcollection.search(hc_name)[0]['Name'] == hc_name
        session.hostcollection.associate_host(hc_name, host.name)
        hc_values = session.hostcollection.read(hc_name, widget_names='hosts')
        assert hc_values['hosts']['resources']['assigned'][0]['Name'] == host.name


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_install_package(
    session, module_org_with_parameter, smart_proxy_location, vm_content_hosts, vm_host_collection
):
    """Install a package to hosts inside host collection remotely

    :id: eead8392-0ffc-4062-b045-5d0252670775

    :expectedresults: Package was successfully installed on all the hosts
        in host collection
    """
    with session:
        session.organization.select(org_name=module_org_with_parameter.name)
        session.location.select(smart_proxy_location.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            packages=constants.FAKE_0_CUSTOM_PACKAGE_NAME,
            action='install',
            action_via='via remote execution',
        )
        assert _is_package_installed(vm_content_hosts, constants.FAKE_0_CUSTOM_PACKAGE_NAME)


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_remove_package(
    session, module_org_with_parameter, smart_proxy_location, vm_content_hosts, vm_host_collection
):
    """Remove a package from hosts inside host collection remotely

    :id: 488fa88d-d0ef-4108-a050-96fb621383df

    :expectedresults: Package was successfully removed from all the hosts
        in host collection
    """
    _install_package_with_assertion(vm_content_hosts, constants.FAKE_0_CUSTOM_PACKAGE)
    with session:
        session.organization.select(org_name=module_org_with_parameter.name)
        session.location.select(smart_proxy_location.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            packages=constants.FAKE_0_CUSTOM_PACKAGE_NAME,
            action='remove',
            action_via='via remote execution',
        )
        assert not _is_package_installed(
            vm_content_hosts, constants.FAKE_0_CUSTOM_PACKAGE_NAME, expect_installed=False
        )


@pytest.mark.tier3
def test_positive_upgrade_package(
    session, module_org_with_parameter, smart_proxy_location, vm_content_hosts, vm_host_collection
):
    """Upgrade a package on hosts inside host collection remotely

    :id: 5a6fff0a-686f-419b-a773-4d03713e47e9

    :expectedresults: Package was successfully upgraded on all the hosts in
        host collection
    """
    _install_package_with_assertion(vm_content_hosts, constants.FAKE_1_CUSTOM_PACKAGE)
    with session:
        session.organization.select(org_name=module_org_with_parameter.name)
        session.location.select(smart_proxy_location.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            packages=constants.FAKE_1_CUSTOM_PACKAGE_NAME,
            action='update',
            action_via='via remote execution',
        )
        assert _is_package_installed(vm_content_hosts, constants.FAKE_2_CUSTOM_PACKAGE)


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_install_package_group(
    session, module_org_with_parameter, smart_proxy_location, vm_content_hosts, vm_host_collection
):
    """Install a package group to hosts inside host collection remotely

    :id: 2bf47798-d30d-451a-8de5-bc03bd8b9a48

    :expectedresults: Package group was successfully installed on all the
        hosts in host collection
    """
    with session:
        session.organization.select(org_name=module_org_with_parameter.name)
        session.location.select(smart_proxy_location.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            content_type='Package Group',
            packages=constants.FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            action='install',
            action_via='via remote execution',
        )
        for package in constants.FAKE_0_CUSTOM_PACKAGE_GROUP:
            assert _is_package_installed(vm_content_hosts, package)


@pytest.mark.tier3
def test_positive_remove_package_group(
    session, module_org_with_parameter, smart_proxy_location, vm_content_hosts, vm_host_collection
):
    """Remove a package group from hosts inside host collection remotely

    :id: 458897dc-9836-481a-b777-b147d64836f2

    :expectedresults: Package group was successfully removed  on all the
        hosts in host collection
    """
    for client in vm_content_hosts:
        result = client.run(f'yum groups install -y {constants.FAKE_0_CUSTOM_PACKAGE_GROUP_NAME}')
        assert result.status == 0
    for package in constants.FAKE_0_CUSTOM_PACKAGE_GROUP:
        assert _is_package_installed(vm_content_hosts, package)
    with session:
        session.organization.select(org_name=module_org_with_parameter.name)
        session.location.select(smart_proxy_location.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            content_type='Package Group',
            packages=constants.FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            action='remove',
            action_via='via remote execution',
        )
        for package in constants.FAKE_0_CUSTOM_PACKAGE_GROUP:
            assert not _is_package_installed(vm_content_hosts, package, expect_installed=False)


@pytest.mark.tier3
@pytest.mark.upgrade
def test_positive_install_errata(
    session, module_org_with_parameter, smart_proxy_location, vm_content_hosts, vm_host_collection
):
    """Install an errata to the hosts inside host collection remotely

    :id: 69c83000-0b46-4735-8c03-e9e0b48af0fb

    :expectedresults: Errata was successfully installed in all the hosts in
        host collection
    """
    _install_package_with_assertion(vm_content_hosts, constants.FAKE_1_CUSTOM_PACKAGE)
    with session:
        session.organization.select(org_name=module_org_with_parameter.name)
        session.location.select(smart_proxy_location.name)
        result = session.hostcollection.install_errata(
            vm_host_collection.name,
            settings.repos.yum_6.errata[2],
            install_via='via remote execution',
        )
        assert result['job_status'] == 'Success'
        assert result['job_status_progress'] == '100%'
        assert int(result['total_hosts']) == 2
        assert _is_package_installed(vm_content_hosts, constants.FAKE_2_CUSTOM_PACKAGE)


@pytest.mark.skip_if_open("BZ:2094815")
@pytest.mark.tier3
def test_positive_change_assigned_content(
    session,
    module_org_with_parameter,
    smart_proxy_location,
    module_lce,
    vm_content_hosts,
    vm_host_collection,
    module_repos_collection,
    module_target_sat,
):
    """Change Assigned Life cycle environment and content view of host
    collection

    :id: e426064a-db3d-4a94-822a-fc303defe1f9

    :customerscenario: true

    :steps:
        1. Setup activation key with content view that contain product
           repositories
        2. Prepare hosts (minimum 2) and subscribe them to activation key
        3. Create a host collection and add the hosts to it
        4. Run "subscription-manager repos" command on each host to notice
           the repos urls current values
        5. Create a new life cycle environment
        6. Create a copy of content view and publish & promote it to the new
           life cycle environment
        7. Go to  Hosts => Hosts Collections and select the host collection
        8. under host collection details tab notice the Actions Area and
           click on the link
           "Change assigned Lifecycle Environment or Content View"
        9. When a dialog box is open, select the new life cycle environment
           and the new content view
        10. Click on "Assign" button and click "Yes" button on confirmation
            dialog when it appears
        11. After last step the host collection change task page will
            appear
        12. Run "subscription-manager refresh" command on each host
        13. Run "subscription-manager repos" command on each host

    :expectedresults:
        1. The host collection change task successfully finished
        2. The "subscription-manager refresh" command successfully executed
           and "All local data refreshed" message is displayed
        3. The urls listed by last command "subscription-manager repos" was
           updated to the new Life cycle environment and content view
           names

    :BZ: 1315280
    """
    new_lce_name = gen_string('alpha')
    new_cv_name = gen_string('alpha')
    new_lce = module_target_sat.api.LifecycleEnvironment(
        name=new_lce_name, organization=module_org_with_parameter
    ).create()
    content_view = module_target_sat.api.ContentView(
        id=module_repos_collection.setup_content_data['content_view']['id']
    ).read()
    new_content_view = module_target_sat.api.ContentView(
        id=content_view.copy(data={'name': new_cv_name})['id']
    )
    new_content_view.publish()
    new_content_view = new_content_view.read()
    new_content_view_version = new_content_view.version[0]
    new_content_view_version.promote(data={'environment_ids': new_lce.id})
    # repository urls listed by command "subscription-manager repos" looks
    # like:
    # Repo URL:  https://{host}/pulp/content/{org}/{lce}/{cv}/custom
    # /{product_name}/{repo_name}
    repo_line_start_with = 'Repo URL:  '
    expected_repo_urls = _get_content_repository_urls(
        module_repos_collection, module_lce, content_view, module_target_sat
    )
    for client in vm_content_hosts:
        result = client.run("subscription-manager repos")
        assert result.status == 0
        client_repo_urls = [
            line.split(' ')[-1]
            for line in result.stdout.splitlines()
            if line.startswith(repo_line_start_with)
        ]
        assert len(client_repo_urls)
        assert set(expected_repo_urls) == set(client_repo_urls)
    with session:
        session.organization.select(org_name=module_org_with_parameter.name)
        session.location.select(smart_proxy_location.name)
        task_values = session.hostcollection.change_assigned_content(
            vm_host_collection.name, new_lce.name, new_content_view.name
        )
        assert task_values['result'] == 'success'
        expected_repo_urls = _get_content_repository_urls(
            module_repos_collection, new_lce, new_content_view, module_target_sat
        )
        for client in vm_content_hosts:
            result = client.run("subscription-manager refresh")
            assert result.status == 0
            assert 'All local data refreshed' in result.stdout
            result = client.run("subscription-manager repos")
            assert result.status == 0
            client_repo_urls = [
                line.split(' ')[-1]
                for line in result.stdout.splitlines()
                if line.startswith(repo_line_start_with)
            ]
            assert len(client_repo_urls)
            assert set(expected_repo_urls) == set(client_repo_urls)


@pytest.mark.tier3
def test_negative_hosts_limit(
    session, module_target_sat, module_org_with_parameter, smart_proxy_location
):
    """Check that Host limit actually limits usage

    :id: 57b70977-2110-47d9-be3b-461ad15c70c7

    :steps:
        1. Create Host Collection entity that can contain only one Host
            (using Host Limit field)
        2. Create Host and add it to Host Collection. Check that it was
            added successfully
        3. Create one more Host and try to add it to Host Collection
        4. Check that expected error is shown

    :expectedresults: Second host is not added to Host Collection and
        appropriate error is shown
    """
    hc_name = gen_string('alpha')
    org = module_target_sat.api.Organization().create()
    cv = module_target_sat.api.ContentView(organization=org).create()
    lce = module_target_sat.api.LifecycleEnvironment(organization=org).create()
    cv.publish()
    cv.read().version[0].promote(data={'environment_ids': lce.id})
    hosts = []
    for _ in range(2):
        hosts.append(
            module_target_sat.api.Host(
                organization=module_org_with_parameter,
                location=smart_proxy_location,
                content_facet_attributes={
                    'content_view_id': cv.id,
                    'lifecycle_environment_id': lce.id,
                },
            ).create()
        )
    assert len(hosts) == 2
    with session:
        session.location.select(smart_proxy_location.name)
        session.hostcollection.create({'name': hc_name, 'unlimited_hosts': False, 'max_hosts': 1})
        assert session.hostcollection.search(hc_name)[0]['Name'] == hc_name
        session.hostcollection.associate_host(hc_name, hosts[0].name)
        with pytest.raises(AssertionError) as context:
            session.hostcollection.associate_host(hc_name, hosts[1].name)
        assert (
            f"cannot have more than 1 host(s) associated with host collection '{hc_name}'"
            in str(context.value)
        )


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'YumRepository': {
                'url': settings.repos.module_stream_1.url,
                'distro': 'rhel8',
            }
        }
    ],
    indirect=True,
)
def test_positive_install_module_stream(
    session, smart_proxy_location, vm_content_hosts_module_stream, vm_host_collection_module_stream
):
    """Install a module-stream to hosts inside host collection remotely

    :id: e5d882e0-3520-4cb6-8629-ef4c18692868

    :steps:
        1. Run dnf upload profile to sync module streams from hosts to Satellite
        2. Navigate to host_collection
        3. Install the module stream duck
        4. Verify that remote job get passed
        5. Verify that package get installed

    :expectedresults: Module-Stream should get installed on all the hosts
        in host collection
    """
    _run_remote_command_on_content_hosts('dnf -y upload-profile', vm_content_hosts_module_stream)
    with session:
        session.location.select(smart_proxy_location.name)
        result = session.hostcollection.manage_module_streams(
            vm_host_collection_module_stream.name,
            action_type="Install",
            module_name=constants.FAKE_3_CUSTOM_PACKAGE_NAME,
            stream_version="0",
        )
        assert result['overview']['job_status'] == 'Success'
        assert result['overview']['job_status_progress'] == '100%'
        assert int(result['overview']['total_hosts']) == 2
        assert _is_package_installed(
            vm_content_hosts_module_stream, constants.FAKE_3_CUSTOM_PACKAGE
        )


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize(
    'module_repos_collection_with_manifest',
    [
        {
            'YumRepository': {
                'url': settings.repos.module_stream_1.url,
                'distro': 'rhel8',
            }
        }
    ],
    indirect=True,
)
def test_positive_install_modular_errata(
    session, smart_proxy_location, vm_content_hosts_module_stream, vm_host_collection_module_stream
):
    """Install Modular Errata generated from module streams.

    :id: 8d6fb447-af86-4084-a147-7910f0cecdef

    :steps:
        1. Generate modular errata by installing older version of module stream
        2. Run dnf upload-profile
        3. Install the modular errata by 'remote execution'
        4. Verify that latest package got installed

    :expectedresults: Modular Errata should get installed on all hosts in host
        collection.
    """
    stream = "0"
    version = "20180704111719"
    _module_install_command = (
        f'dnf -y module install {constants.FAKE_4_CUSTOM_PACKAGE_NAME}:{stream}:{version}'
    )
    _run_remote_command_on_content_hosts(_module_install_command, vm_content_hosts_module_stream)
    _run_remote_command_on_content_hosts('dnf -y upload-profile', vm_content_hosts_module_stream)
    with session:
        session.location.select(smart_proxy_location.name)
        _run_remote_command_on_content_hosts(
            f'dnf -y module install {constants.FAKE_4_CUSTOM_PACKAGE_NAME}:0:20180704111719',
            vm_content_hosts_module_stream,
        )
        _run_remote_command_on_content_hosts(
            'dnf -y upload-profile', vm_content_hosts_module_stream
        )
        result = session.hostcollection.install_errata(
            vm_host_collection_module_stream.name,
            settings.repos.module_stream_0.errata[2],
            install_via='via remote execution',
        )
        assert result['job_status'] == 'Success'
        assert result['job_status_progress'] == '100%'
        assert int(result['total_hosts']) == 2
        assert _is_package_installed(
            vm_content_hosts_module_stream, constants.FAKE_6_CUSTOM_PACKAGE
        )
