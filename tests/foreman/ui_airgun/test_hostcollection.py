"""Test class for Host Collection UI

:Requirement: Hostcollection

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import time

from nailgun import entities
from pytest import raises

from robottelo.api.utils import promote, update_vm_host_location
from robottelo.config import settings
from robottelo.constants import (
    DISTRO_DEFAULT,
    FAKE_0_CUSTOM_PACKAGE,
    FAKE_0_CUSTOM_PACKAGE_NAME,
    FAKE_0_CUSTOM_PACKAGE_GROUP,
    FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_1_CUSTOM_PACKAGE_NAME,
    FAKE_1_YUM_REPO,
    FAKE_2_CUSTOM_PACKAGE,
    FAKE_2_ERRATA_ID,
    FAKE_6_YUM_REPO,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import fixture, tier2, tier3, upgrade
from robottelo.products import (
    YumRepository,
    RepositoryCollection,
    SatelliteToolsRepository,
)
from robottelo.vm import VirtualMachine


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_loc():
    return entities.Location().create()


@fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@fixture(scope='module')
def module_repos_collection(module_org, module_lce):
    repos_collection = RepositoryCollection(
        distro=DISTRO_DEFAULT,
        repositories=[
            SatelliteToolsRepository(),
            YumRepository(url=FAKE_1_YUM_REPO),
            YumRepository(url=FAKE_6_YUM_REPO),
        ]
    )
    repos_collection.setup_content(
        module_org.id, module_lce.id, upload_manifest=True)
    return repos_collection


@fixture
def vm_content_hosts(request, module_loc, module_repos_collection):
    clients = []
    for _ in range(2):
        client = VirtualMachine(distro=module_repos_collection.distro)
        clients.append(client)
        request.addfinalizer(client.destroy)
        client.create()
        module_repos_collection.setup_virtual_machine(client)
        update_vm_host_location(client, module_loc.id)
    return clients


@fixture
def vm_host_collection(module_org, vm_content_hosts):
    host_ids = [
        entities.Host().search(query={
            'search': 'name={0}'.format(host.hostname)})[0].id
        for host in vm_content_hosts
    ]
    host_collection = entities.HostCollection(
        host=host_ids,
        organization=module_org,
    ).create()
    return host_collection


def _is_package_installed(
        vm_clients, package_name, expect_installed=True, retries=10,
        iteration_sleep=15):
    """Check whether package name was installed on the list of Virtual Machines
    clients.
    """
    assert len(vm_clients) > 0
    installed = 0
    if not expect_installed:
        installed = len(vm_clients)
    for vm_client in vm_clients:
        for ind in range(retries):
            result = vm_client.run(
                'rpm -q {0}'.format(package_name))
            if result.return_code == 0 and expect_installed:
                installed += 1
                break
            elif result.return_code != 0 and not expect_installed:
                installed -= 1
                break
            if ind < retries - 1:
                time.sleep(iteration_sleep)
        else:
            break

    if expect_installed:
        return installed == len(vm_clients)
    else:
        return bool(installed)


def _install_package_with_assertion(vm_clients, package_name):
    """Install package in Virtual machine clients and assert installed"""
    for client in vm_clients:
        result = client.run(
            'yum install -y {0}'.format(package_name))
        assert result.return_code == 0
    assert _is_package_installed(vm_clients, package_name)


def _get_content_repository_urls(repos_collection, lce, content_view):
    """Returns a list of the content repository urls"""
    custom_url_template = (
        'https://{hostname}/pulp/repos/{org_label}/{lce.name}'
        '/{content_view.name}/custom/{product_label}/{repository_name}'
    )
    rh_sat_tools_url_template = (
        'https://{hostname}/pulp/repos/{org_label}/{lce.name}'
        '/{content_view.name}/content/dist/rhel/server/{major_version}'
        '/{major_version}Server/$basearch/sat-tools/{product_version}/os'
    )
    repos_urls = [
        custom_url_template.format(
            hostname=settings.server.hostname,
            org_label=repos_collection.organization['label'],
            lce=lce,
            content_view=content_view,
            product_label=repos_collection.custom_product['label'],
            repository_name=repository['name'],
        )
        for repository in repos_collection.custom_repos_info
    ]
    # add sat-tool rh repo
    # Note: if sat-tools is not cdn it must be already in repos_urls
    for repo in repos_collection:
        if isinstance(repo, SatelliteToolsRepository) and repo.cdn:
            repos_urls.append(rh_sat_tools_url_template.format(
                hostname=settings.server.hostname,
                org_label=repos_collection.organization['label'],
                lce=lce,
                content_view=content_view,
                major_version=repo.distro_major_version,
                product_version=repo.repo_data['version'],
            ))
    return repos_urls


@tier2
@upgrade
def test_positive_end_to_end(session, module_org, module_loc):
    """Perform end to end testing for host collection component

    :id: 1d40bc74-8e05-42fa-b6e3-2999dc3b730d

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    hc_name = gen_string('alpha')
    new_name = gen_string('alpha')
    description = gen_string('alpha')
    host = entities.Host(
        organization=module_org, location=module_loc).create()
    with session:
        # Create new host collection
        session.hostcollection.create({
            'name': hc_name,
            'unlimited_hosts': False,
            'max_hosts': 2,
            'description': description
        })
        assert session.hostcollection.search(hc_name)[0]['Name'] == hc_name
        session.hostcollection.associate_host(hc_name, host.name)
        hc_values = session.hostcollection.read(hc_name)
        assert hc_values['details']['name'] == hc_name
        assert hc_values['details']['description'] == description
        assert hc_values['details']['content_hosts'] == '1'
        assert hc_values['details']['content_host_limit'] == '2'
        assert hc_values['hosts']['resources']['assigned'][0]['Name'] == host.name
        # Update host collection with new name
        session.hostcollection.update(hc_name, {'details.name': new_name})
        assert session.hostcollection.search(new_name)[0]['Name'] == new_name
        # Delete host collection
        session.hostcollection.delete(new_name)
        assert not session.hostcollection.search(new_name)


@tier2
def test_negative_install_via_remote_execution(session, module_org, module_loc):
    """Test basic functionality of the Hosts collection UI install package via
    remote execution.

    :id: c5fe46fb-0b34-4ea3-bc53-e86c18adaf94

    :setup: Create a host collection with two fake hosts assigned.

    :expectedresults: The package is not installed, and the job invocation
        status contains some expected values: hosts information, jos status.

    :CaseLevel: Integration
    """
    hosts = []
    for _ in range(2):
        hosts.append(entities.Host(
            organization=module_org, location=module_loc).create())
    host_collection = entities.HostCollection(
        host=[host.id for host in hosts],
        organization=module_org,
    ).create()
    with session:
        job_values = session.hostcollection.manage_packages(
            host_collection.name,
            packages=FAKE_0_CUSTOM_PACKAGE_NAME,
            action='install',
            action_via='via remote execution'
        )
        assert job_values['job_status'] == 'Failed'
        assert job_values['job_status_progress'] == '100%'
        assert int(job_values['total_hosts']) == len(hosts)
        assert ({host.name for host in hosts}
                == {host['Host'] for host in job_values['hosts_table']})


@tier2
def test_negative_install_via_custom_remote_execution(session, module_org, module_loc):
    """Test basic functionality of the Hosts collection UI install package via
    remote execution - customize first.

    :id: 5aa7f084-bab7-4e62-9bf3-a37fd4aa71fa

    :setup: Create a host collection with two fake hosts assigned.

    :expectedresults: The package is not installed, and the job invocation
        status contains some expected values: hosts information, jos status.

    :CaseLevel: Integration
    """
    hosts = []
    for _ in range(2):
        hosts.append(entities.Host(
            organization=module_org, location=module_loc).create())
    host_collection = entities.HostCollection(
        host=[host.id for host in hosts],
        organization=module_org,
    ).create()
    with session:
        job_values = session.hostcollection.manage_packages(
            host_collection.name,
            packages=FAKE_0_CUSTOM_PACKAGE_NAME,
            action='install',
            action_via='via remote execution - customize first',
        )
        assert job_values['job_status'] == 'Failed'
        assert job_values['job_status_progress'] == '100%'
        assert int(job_values['total_hosts']) == len(hosts)
        assert ({host.name for host in hosts}
                == {host['Host'] for host in job_values['hosts_table']})


@upgrade
@tier3
def test_positive_add_host(session):
    """Check if host can be added to Host Collection

    :id: 80824c9f-15a1-4f76-b7ac-7d9ca9f6ed9e

    :expectedresults: Host is added to Host Collection successfully

    :CaseLevel: System
    """
    hc_name = gen_string('alpha')
    org = entities.Organization().create()
    loc = entities.Location().create()
    cv = entities.ContentView(organization=org).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    cv.publish()
    promote(cv.read().version[0], lce.id)
    host = entities.Host(
        organization=org,
        location=loc,
        content_facet_attributes={
            'content_view_id': cv.id,
            'lifecycle_environment_id': lce.id,
        },
    ).create()
    with session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        session.hostcollection.create({'name': hc_name})
        assert session.hostcollection.search(hc_name)[0]['Name'] == hc_name
        session.hostcollection.associate_host(hc_name, host.name)
        hc_values = session.hostcollection.read(hc_name)
        assert (
            hc_values['hosts']['resources']['assigned'][0]['Name'] == host.name
        )


@tier3
@upgrade
def test_positive_install_package(
        session, module_org, vm_content_hosts, vm_host_collection):
    """Install a package to hosts inside host collection remotely

    :id: eead8392-0ffc-4062-b045-5d0252670775

    :expectedresults: Package was successfully installed on all the hosts
        in host collection

    :CaseLevel: System
    """
    with session:
        session.organization.select(org_name=module_org.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            packages=FAKE_0_CUSTOM_PACKAGE_NAME,
            action='install'
        )
        assert _is_package_installed(
            vm_content_hosts, FAKE_0_CUSTOM_PACKAGE_NAME)


@tier3
@upgrade
def test_positive_remove_package(
        session, module_org, vm_content_hosts, vm_host_collection):
    """Remove a package from hosts inside host collection remotely

    :id: 488fa88d-d0ef-4108-a050-96fb621383df

    :expectedresults: Package was successfully removed from all the hosts
        in host collection

    :CaseLevel: System
    """
    _install_package_with_assertion(vm_content_hosts, FAKE_0_CUSTOM_PACKAGE)
    with session:
        session.organization.select(org_name=module_org.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            packages=FAKE_0_CUSTOM_PACKAGE_NAME,
            action='remove'
        )
        assert not _is_package_installed(
            vm_content_hosts,
            FAKE_0_CUSTOM_PACKAGE_NAME,
            expect_installed=False
        )


@tier3
def test_positive_upgrade_package(
        session, module_org, vm_content_hosts, vm_host_collection):
    """Upgrade a package on hosts inside host collection remotely

    :id: 5a6fff0a-686f-419b-a773-4d03713e47e9

    :expectedresults: Package was successfully upgraded on all the hosts in
        host collection

    :CaseLevel: System
    """
    _install_package_with_assertion(vm_content_hosts, FAKE_1_CUSTOM_PACKAGE)
    with session:
        session.organization.select(org_name=module_org.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            packages=FAKE_1_CUSTOM_PACKAGE_NAME,
            action='update'
        )
        assert _is_package_installed(vm_content_hosts, FAKE_2_CUSTOM_PACKAGE)


@tier3
@upgrade
def test_positive_install_package_group(
        session, module_org, vm_content_hosts, vm_host_collection):
    """Install a package group to hosts inside host collection remotely

    :id: 2bf47798-d30d-451a-8de5-bc03bd8b9a48

    :expectedresults: Package group was successfully installed on all the
        hosts in host collection

    :CaseLevel: System
    """
    with session:
        session.organization.select(org_name=module_org.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            content_type='Package Group',
            packages=FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            action='install',
        )
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            assert _is_package_installed(vm_content_hosts, package)


@tier3
def test_positive_remove_package_group(
        session, module_org, vm_content_hosts, vm_host_collection):
    """Remove a package group from hosts inside host collection remotely

    :id: 458897dc-9836-481a-b777-b147d64836f2

    :expectedresults: Package group was successfully removed  on all the
        hosts in host collection

    :CaseLevel: System
    """
    for client in vm_content_hosts:
        result = client.run('yum groups install -y {0}'.format(
            FAKE_0_CUSTOM_PACKAGE_GROUP_NAME))
        assert result.return_code == 0
    for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
        assert _is_package_installed(vm_content_hosts, package)
    with session:
        session.organization.select(org_name=module_org.name)
        session.hostcollection.manage_packages(
            vm_host_collection.name,
            content_type='Package Group',
            packages=FAKE_0_CUSTOM_PACKAGE_GROUP_NAME,
            action='remove',
        )
        for package in FAKE_0_CUSTOM_PACKAGE_GROUP:
            assert not _is_package_installed(
                vm_content_hosts,
                package,
                expect_installed=False
            )


@tier3
@upgrade
def test_positive_install_errata(
        session, module_org, vm_content_hosts, vm_host_collection):
    """Install an errata to the hosts inside host collection remotely

    :id: 69c83000-0b46-4735-8c03-e9e0b48af0fb

    :expectedresults: Errata was successfully installed in all the hosts in
        host collection

    :CaseLevel: System
    """
    _install_package_with_assertion(vm_content_hosts, FAKE_1_CUSTOM_PACKAGE)
    with session:
        session.organization.select(org_name=module_org.name)
        task_values = session.hostcollection.install_errata(
            vm_host_collection.name, FAKE_2_ERRATA_ID)
        assert task_values['result'] == 'success'
        assert _is_package_installed(vm_content_hosts, FAKE_2_CUSTOM_PACKAGE)


@tier3
def test_positive_change_assigned_content(
        session, module_org, module_lce, vm_content_hosts, vm_host_collection,
        module_repos_collection):
    """Change Assigned Life cycle environment and content view of host
    collection

    :id: e426064a-db3d-4a94-822a-fc303defe1f9

    :customerscenario: true

    :steps:
        1. Setup activation key with content view that contain product
           repositories
        2. Prepare hosts (minimum 2) and subscribe them to activation key,
           katello agent must be also installed and running on each host
        3. Create a host collection and add the hosts to it
        4. Run "subscription-manager repos" command on each host to notice
           the repos urls current values
        5. Create a new life cycle environment
        6. Create a copy of content view and publish/promote it to the new
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

    :CaseLevel: System
    """
    new_lce_name = gen_string('alpha')
    new_cv_name = gen_string('alpha')
    new_lce = entities.LifecycleEnvironment(
        name=new_lce_name, organization=module_org).create()
    content_view = entities.ContentView(
        id=module_repos_collection.setup_content_data['content_view']['id']
    ).read()
    new_content_view = entities.ContentView(
        id=content_view.copy(data={u'name': new_cv_name})['id']
    )
    new_content_view.publish()
    new_content_view = new_content_view.read()
    new_content_view_version = new_content_view.version[0]
    new_content_view_version.promote(data={'environment_id': new_lce.id})
    # repository urls listed by command "subscription-manager repos" looks
    # like:
    # Repo URL  : https://{host}/pulp/repos/{org}/{lce}/{cv}/custom
    # /{product_name}/{repo_name}
    repo_line_start_with = 'Repo URL:  '
    expected_repo_urls = _get_content_repository_urls(
        module_repos_collection, module_lce, content_view)
    for client in vm_content_hosts:
        result = client.run("subscription-manager repos")
        assert result.return_code == 0
        client_repo_urls = [
            line.split(' ')[-1]
            for line in result.stdout
            if line.startswith(repo_line_start_with)
        ]
        assert len(client_repo_urls) > 0
        assert set(expected_repo_urls) == set(client_repo_urls)
    with session:
        session.organization.select(org_name=module_org.name)
        task_values = session.hostcollection.change_assigned_content(
            vm_host_collection.name,
            new_lce.name,
            new_content_view.name
        )
        assert task_values['result'] == 'success'
        expected_repo_urls = _get_content_repository_urls(
            module_repos_collection, new_lce, new_content_view)
        for client in vm_content_hosts:
            result = client.run("subscription-manager refresh")
            assert result.return_code == 0
            assert 'All local data refreshed' in result.stdout
            result = client.run("subscription-manager repos")
            assert result.return_code == 0
            client_repo_urls = [
                line.split(' ')[-1]
                for line in result.stdout
                if line.startswith(repo_line_start_with)
            ]
            assert len(client_repo_urls) > 0
            assert set(expected_repo_urls) == set(client_repo_urls)


@tier3
def test_negative_hosts_limit(session, module_org, module_loc):
    """Check that Host limit actually limits usage

    :id: 57b70977-2110-47d9-be3b-461ad15c70c7

    :Steps:
        1. Create Host Collection entity that can contain only one Host
            (using Host Limit field)
        2. Create Host and add it to Host Collection. Check that it was
            added successfully
        3. Create one more Host and try to add it to Host Collection
        4. Check that expected error is shown

    :expectedresults: Second host is not added to Host Collection and
        appropriate error is shown

    :CaseLevel: System
    """
    hc_name = gen_string('alpha')
    org = entities.Organization().create()
    cv = entities.ContentView(organization=org).create()
    lce = entities.LifecycleEnvironment(organization=org).create()
    cv.publish()
    promote(cv.read().version[0], lce.id)
    hosts = []
    for _ in range(2):
        hosts.append(entities.Host(
            organization=module_org,
            location=module_loc,
            content_facet_attributes={
                'content_view_id': cv.id,
                'lifecycle_environment_id': lce.id,
            },
        ).create())
    assert len(hosts) == 2
    with session:
        session.hostcollection.create({
            'name': hc_name, 'unlimited_hosts': False, 'max_hosts': 1})
        assert session.hostcollection.search(hc_name)[0]['Name'] == hc_name
        session.hostcollection.associate_host(hc_name, hosts[0].name)
        with raises(AssertionError) as context:
            session.hostcollection.associate_host(hc_name, hosts[1].name)
        assert "cannot have more than 1 host(s) associated with host collection '{}'".format(
            hc_name
        ) in str(context.value)
