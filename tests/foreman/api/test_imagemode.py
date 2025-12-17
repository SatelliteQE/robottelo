"""API tests for Image Mode Hosts

:Requirement: ImageMode

:CaseAutomation: Automated

:CaseComponent: ImageMode

:Team: Artemis

:CaseImportance: High
"""

import json

import pytest

from robottelo.config import settings
from robottelo.constants import (
    DUMMY_BOOTC_FACTS,
    FAKE_1_CUSTOM_PACKAGE,
    FAKE_7_CUSTOM_PACKAGE,
)
from tests.foreman.api.test_host import _create_transient_packages


@pytest.mark.e2e
@pytest.mark.no_containers
def test_positive_bootc_api_actions(
    target_sat, dummy_bootc_host, function_ak_with_cv, function_org
):
    """Register a bootc host and validate API information

    :id: b94ab231-0dd8-4e47-a96b-972c5ee55f4d

    :expectedresults: Upon registering a Bootc host, the API returns correct information across multiple endpoints

    :Verifies: SAT-27168, SAT-27170, SAT-27173
    """
    bootc_dummy_info = json.loads(DUMMY_BOOTC_FACTS)
    assert (
        dummy_bootc_host.register(function_org, None, function_ak_with_cv.name, target_sat).status
        == 0
    )
    assert dummy_bootc_host.subscribed
    # Testing bootc info from content_facet_attributes
    dummy_bootc_host = target_sat.api.Host().search(
        query={'search': f'name={dummy_bootc_host.hostname}'}
    )[0]
    assert (
        dummy_bootc_host.content_facet_attributes['bootc_booted_image']
        == bootc_dummy_info['bootc.booted.image']
    )
    assert (
        dummy_bootc_host.content_facet_attributes['bootc_booted_digest']
        == bootc_dummy_info['bootc.booted.digest']
    )
    assert (
        dummy_bootc_host.content_facet_attributes['bootc_rollback_image']
        == bootc_dummy_info['bootc.rollback.image']
    )
    assert (
        dummy_bootc_host.content_facet_attributes['bootc_rollback_digest']
        == bootc_dummy_info['bootc.rollback.digest']
    )
    # Testing bootc info from hosts/bootc_images
    bootc_image_info = target_sat.api.Host().get_bootc_images()['results'][0]
    assert bootc_image_info['bootc_booted_image'] == bootc_dummy_info['bootc.booted.image']
    assert (
        bootc_image_info['digests'][0]['bootc_booted_digest']
        == bootc_dummy_info['bootc.booted.digest']
    )
    assert bootc_image_info['digests'][0]['host_count'] > 0

    # Testing bootc image is correctly included in the usage report
    os = dummy_bootc_host.operatingsystem.read_json()
    assert (
        int(target_sat.get_reported_value(f'image_mode_hosts_by_os_count|{os["family"]}')) == 1
    ), "host not included in usage report"


@pytest.mark.parametrize(
    'function_repos_collection_with_manifest',
    [
        {
            'distro': 'rhel10',
            'YumRepository': [
                {'url': settings.repos.yum_3.url},
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('10')
def test_mixed_usr_overlay_transient_templates(
    target_sat, bootc_host, function_repos_collection_with_manifest
):
    """Verify that you can run an Ansible REX playbook after previously installing a package
    with the --transient flag.

    :id: e400d595-c503-492c-a922-d9b652558605

    :steps:
        1. Create and register a bootc host.
        2. Install a package using --transient flag
        3. Install a package via Ansible REX.

    :expectedresults: Both templates install successfully when run in sequence.

    :Verifies: SAT-31226, SAT-31580
    """
    bootc_host.add_rex_key(target_sat)
    function_repos_collection_with_manifest.setup_virtual_machine(bootc_host)
    assert bootc_host.subscribed

    # Enable custom repo
    bootc_host.add_rex_key(target_sat)
    result = bootc_host.execute(r'dnf config-manager --enable \*')
    assert result.status == 0

    # Install a package transiently
    result = bootc_host.execute(r'dnf --transient -y install rabbit')
    assert result.status == 0

    # Install package via Ansible REX
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Package Action - Ansible Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'state': 'latest',
                'name': 'tapir',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = bootc_host.execute('rpm -q tapir')
    assert result.status == 0


@pytest.mark.parametrize(
    'function_repos_collection_with_manifest',
    [
        {
            'distro': 'rhel10',
            'YumRepository': [
                {'url': settings.repos.yum_3.url},
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('10')
def test_bootc_ansible_rex_package_install(
    target_sat, bootc_host, function_repos_collection_with_manifest
):
    """Create a bootc host, and verify that you can install/remove a package via the Ansible REX templates

    :id: 43651f48-40e7-49a5-a686-4ee48947e2f2

    :steps:
        1.Create and register a bootc host.
        2.Install a package via REX Ansible
        3.Remove the package via REX Ansible.

    :expectedresults: All REX Ansible templates actions succeed when run against a bootc host.

    :Verifies: SAT-31580
    """
    bootc_host.add_rex_key(target_sat)
    function_repos_collection_with_manifest.setup_virtual_machine(bootc_host)
    assert bootc_host.subscribed

    # Enable custom repo
    bootc_host.add_rex_key(target_sat)
    result = bootc_host.execute(r'dnf config-manager --enable \*')
    assert result.status == 0

    # Install package via Ansible REX
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Package Action - Ansible Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'state': 'latest',
                'name': 'tapir',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = bootc_host.execute('rpm -q tapir')
    assert result.status == 0

    # Remove package via Ansible REX
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Package Action - Ansible Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'state': 'absent',
                'name': 'tapir',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = bootc_host.execute('rpm -q tapir')
    assert result.status == 1


@pytest.mark.parametrize(
    'function_repos_collection_with_manifest',
    [
        {
            'distro': 'rhel10',
            'YumRepository': [
                {'url': settings.repos.yum_3.url},
                {'url': settings.repos.yum_1.url},
                {'url': settings.repos.yum_6.url},
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('10')
def test_bootc_rex_package_install(target_sat, bootc_host, function_repos_collection_with_manifest):
    """Create a bootc host, and verify that you can install a package via various REX templates

    :id: 72466622-3f9f-445b-9e39-f4d344df44fb

    :steps:
        1.Create and register a bootc host.
        2.Enable a custom package on the host.
        3.Install a package by name search and by id.
        4.Remove the packages installed above
        5.Install a package group

    :expectedresults: All katello package template actions succeed when run against a bootc host.

    :Verifies: SAT-31226
    """
    bootc_host.add_rex_key(target_sat)
    function_repos_collection_with_manifest.setup_virtual_machine(bootc_host)
    assert bootc_host.subscribed

    # Enable custom repo
    bootc_host.add_rex_key(target_sat)
    result = bootc_host.execute(r'dnf config-manager --enable \*')
    assert result.status == 0

    # Install package by search query
    template_id = (
        target_sat.api.JobTemplate()
        .search(
            query={'search': 'name="Install packages by search query - Katello Script Default"'}
        )[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'Package search query': '^(rabbit)',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = bootc_host.execute('rpm -q rabbit')
    assert result.status == 0

    # Remove package by search query
    template_id = (
        target_sat.api.JobTemplate()
        .search(
            query={'search': 'name="Remove Packages by search query - Katello Script Default"'}
        )[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'Packages search query': '^(rabbit)',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = bootc_host.execute('rpm -q rabbit')
    assert result.status == 1

    # Install package by ID
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Install Package - Katello Script Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'package': 'tapir',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    install_result = bootc_host.execute('rpm -q tapir')
    assert 'tapir-8.4.4-1' in install_result.stdout

    # Update package
    downgrade_result = bootc_host.execute('dnf --transient -y downgrade tapir')
    assert 'Downgrading      : tapir-8.4.3-1.noarch' in downgrade_result.stdout
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Update Package - Katello Script Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'package': 'tapir',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    upgrade_result = bootc_host.execute('rpm -q tapir')
    assert 'tapir-8.4.4-1' in upgrade_result.stdout

    # Remove package by ID
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Remove Package - Katello Script Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'package': 'tapir',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = bootc_host.execute('rpm -q tapir')
    assert result.status == 1

    # Install package group
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Install Group - Katello Script Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'package': 'birds',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = bootc_host.execute('dnf grouplist --installed')
    assert 'birds' in result.stdout

    # Remove package group
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Remove Group - Katello Script Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'package': 'birds',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(f'resource_type = JobInvocation and resource_id = {job["id"]}')
    result = bootc_host.execute('dnf grouplist --installed')
    assert 'birds' not in result.stdout


@pytest.mark.parametrize(
    'function_repos_collection_with_manifest',
    [
        {
            'distro': 'rhel10',
            'YumRepository': [
                {'url': settings.repos.yum_3.url},
                {'url': settings.repos.yum_1.url},
            ],
        }
    ],
    indirect=True,
)
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('10')
def test_bootc_rex_errata_install(target_sat, bootc_host, function_repos_collection_with_manifest):
    """Apply an errata through both REX errata templates on a bootc host.

    :id: 2261933f-fb9f-4c32-8f61-c9865de5a1d2

    :steps:
        1.Create and register a bootc host.
        2.Enable a custom package on the host.
        3.Install an errata via name search and ID

    :expectedresults: All errata REX templates actions succeed when run against a bootc host.

    :Verifies: SAT-31226
    """
    errata_ids = [settings.repos.yum_3.errata[25], settings.repos.yum_1.errata[1]]
    bootc_host.add_rex_key(target_sat)
    function_repos_collection_with_manifest.setup_virtual_machine(bootc_host)
    assert bootc_host.subscribed

    # Enable custom repo
    bootc_host.add_rex_key(target_sat)
    result = bootc_host.execute(r'dnf config-manager --enable \*')
    assert result.status == 0

    # Install packages
    bootc_host.run(f'dnf --transient -y install {FAKE_7_CUSTOM_PACKAGE}')
    result = bootc_host.run('rpm -q rabbit')
    assert result.status == 0
    bootc_host.run(f'dnf --transient -y install {FAKE_1_CUSTOM_PACKAGE}')
    result = bootc_host.run('rpm -q walrus')
    assert result.status == 0
    # stripped_errata_id = errata_ids[0].replace("'", ' ')
    # errata_search_query = f'errata_id ^ ({stripped_errata_id})'

    # Install errata by ID
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Install Errata - Katello Script Default"'})[0]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'errata': f'{errata_ids[1]}',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(
        search_query=f'resource_type = JobInvocation and resource_id = {job["id"]}',
        must_succeed=True,
        poll_timeout=100,
    )

    # Install errata by search query
    template_id = (
        target_sat.api.JobTemplate()
        .search(query={'search': 'name="Install errata by search query - Katello Script Default"'})[
            0
        ]
        .id
    )
    job = target_sat.api.JobInvocation().run(
        synchronous=False,
        data={
            'job_template_id': template_id,
            'inputs': {
                'Errata search query': '',
            },
            'targeting_type': 'static_query',
            'search_query': f'name = {bootc_host.hostname}',
        },
    )
    target_sat.wait_for_tasks(
        search_query=f'resource_type = JobInvocation and resource_id = {job["id"]}',
        must_succeed=True,
        poll_timeout=100,
    )


def test_positive_host_packages_persistence_api(target_sat):
    """Verify that package persistence info is exposed via /api/v2/hosts/:id/packages endpoint

    :id: 54e2badc-5f42-4f2c-8d67-4f8107a9eac8

    :steps:
        1. Create a host
        2. Add packages with different persistence values via SQL (transient, persistent, None)
        3. Retrieve packages via /api/v2/hosts/:id/packages API endpoint
        4. Verify persistence info is present and correct for each package

    :expectedresults:
        1. Packages with persistence='transient' are returned with correct value
        2. Packages with persistence='persistent' are returned with correct value
        3. Packages with persistence=None are returned with None/null value
        4. All packages returned via API include the 'persistence' field

    :Verifies: SAT-36788
    """
    # Create a host
    host = target_sat.api.Host().create()

    # Mock packages with different persistence values by directly inserting them via SQL
    package_data = [
        {
            'name': 'transient-pkg',
            'version': '1.0.0',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': 'transient',
        },
        {
            'name': 'persistent-pkg',
            'version': '2.0.0',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': 'persistent',
        },
        {
            'name': 'unknown-pkg',
            'version': '3.0.0',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': None,
        },
    ]

    # Insert packages with persistence info using helper function
    _create_transient_packages(target_sat, host, package_data)

    # Call the /api/v2/hosts/:id/packages API endpoint using NailGun
    packages = host.packages()['results']

    # Verify that all packages are returned
    assert len(packages) == 3, f'Expected 3 packages, got {len(packages)}'

    # Verify each package has correct persistence info
    transient_pkg = next((p for p in packages if p['name'] == 'transient-pkg'), None)
    assert transient_pkg is not None, 'Transient package not found in API response'
    assert 'persistence' in transient_pkg, 'Persistence field missing from transient package'
    assert transient_pkg['persistence'] == 'transient', (
        f"Expected persistence='transient', got '{transient_pkg['persistence']}'"
    )

    persistent_pkg = next((p for p in packages if p['name'] == 'persistent-pkg'), None)
    assert persistent_pkg is not None, 'Persistent package not found in API response'
    assert 'persistence' in persistent_pkg, 'Persistence field missing from persistent package'
    assert persistent_pkg['persistence'] == 'persistent', (
        f"Expected persistence='persistent', got '{persistent_pkg['persistence']}'"
    )

    unknown_pkg = next((p for p in packages if p['name'] == 'unknown-pkg'), None)
    assert unknown_pkg is not None, 'Unknown package not found in API response'
    assert 'persistence' in unknown_pkg, 'Persistence field missing from unknown package'
    assert unknown_pkg['persistence'] is None, (
        f"Expected persistence=None, got '{unknown_pkg['persistence']}'"
    )

    # Verify all packages have the persistence field
    for pkg in packages:
        assert 'persistence' in pkg, f"Package {pkg['name']} missing persistence field"


def test_positive_transient_packages_only(target_sat):
    """Verify API returns only transient packages when all packages are transient

    :id: 279c9340-8101-4127-aa92-a3c70a0e870d

    :steps:
        1. Create a host
        2. Add only transient packages via SQL
        3. Retrieve packages via /api/v2/hosts/:id/packages API endpoint
        4. Verify all returned packages have persistence='transient'

    :expectedresults:
        1. All packages are returned with persistence='transient'
        2. Persistence field is present for all packages

    :Verifies: SAT-36788
    """
    # Create a host
    host = target_sat.api.Host().create()

    # Add only transient packages
    package_data = [
        {
            'name': 'transient-pkg-1',
            'version': '1.0.0',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': 'transient',
        },
        {
            'name': 'transient-pkg-2',
            'version': '2.0.0',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': 'transient',
        },
    ]

    _create_transient_packages(target_sat, host, package_data)

    # Call the API endpoint using NailGun
    packages = host.packages()['results']

    # Verify all packages are transient
    assert len(packages) == 2
    for pkg in packages:
        assert 'persistence' in pkg, f"Package {pkg['name']} missing persistence field"
        assert pkg['persistence'] == 'transient', (
            f"Expected all packages to be transient, but {pkg['name']} has persistence='{pkg['persistence']}'"
        )


def test_positive_persistent_packages_only(target_sat):
    """Verify API returns only persistent packages when all packages are persistent

    :id: 9c0ea941-94c4-4f1b-8a5c-ff3439b090a4

    :steps:
        1. Create a host
        2. Add only persistent packages via SQL
        3. Retrieve packages via /api/v2/hosts/:id/packages API endpoint
        4. Verify all returned packages have persistence='persistent'

    :expectedresults:
        1. All packages are returned with persistence='persistent'
        2. Persistence field is present for all packages

    :Verifies: SAT-36788
    """
    # Create a host
    host = target_sat.api.Host().create()

    # Add only persistent packages
    package_data = [
        {
            'name': 'base-pkg-1',
            'version': '1.0.0',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': 'persistent',
        },
        {
            'name': 'base-pkg-2',
            'version': '2.0.0',
            'release': '1.el10',
            'arch': 'x86_64',
            'persistence': 'persistent',
        },
    ]

    _create_transient_packages(target_sat, host, package_data)

    # Call the API endpoint using NailGun
    packages = host.packages()['results']

    # Verify all packages are persistent
    assert len(packages) == 2
    for pkg in packages:
        assert 'persistence' in pkg, f"Package {pkg['name']} missing persistence field"
        assert pkg['persistence'] == 'persistent', (
            f"Expected all packages to be persistent, but {pkg['name']} has persistence='{pkg['persistence']}'"
        )


def test_positive_host_packages_persistence_api_empty_results(target_sat):
    """Verify that package persistence API returns an empty result set for a host with no packages

    :id: d782367b-598b-49fe-9654-7a66bc3d22be

    :steps:
        1. Create a host
        2. Ensure host has no packages in katello_host_installed_packages
        3. Call /api/v2/hosts/:id/packages API endpoint
        4. Verify response is successful with empty results

    :expectedresults:
        1. Response status is 200
        2. Results field is present and is an empty list
        3. Total and subtotal are 0

    :Verifies: SAT-36788
    """
    # Create a host
    host = target_sat.api.Host().create()

    # Ensure this host has no package persistence rows (it shouldn't by default, but let's be explicit)
    target_sat.query_db(
        f"DELETE FROM katello_host_installed_packages WHERE host_id = {host.id}",
        output_format="raw",
    )

    # Call the packages API for a host with no installed packages using NailGun
    packages = host.packages()

    # results key must be present and an empty list
    assert 'results' in packages
    assert isinstance(packages['results'], list)
    assert len(packages['results']) == 0

    # total/subtotal should correctly represent the empty case
    assert packages.get('total') == 0
    assert packages.get('subtotal') == 0
