"""Test for Content Access (Golden Ticket) CLI

:Requirement: Content Access

:CaseComponent: Hosts-Content

:CaseAutomation: Automated

:team: Phoenix-subscriptions

"""

import time

import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    PRDS,
    REAL_RHEL9_ERRATA_ID,
    REAL_RHEL9_OUTDATED_PACKAGE_FILENAME,
    REAL_RHEL9_PACKAGE,
    REPOS,
    REPOSET,
)

pytestmark = [
    pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    ),
    pytest.mark.run_in_one_thread,
]


@pytest.fixture(scope='module')
def rh_repo_setup_ak(module_sca_manifest_org, module_target_sat):
    """Use module sca manifest org, creates rhsclient9 repo & syncs it,
    also create CV, LCE & AK and return AK"""
    rh_repo_id = module_target_sat.api_factory.enable_rhrepo_and_fetchid(
        basearch=DEFAULT_ARCHITECTURE,
        org_id=module_sca_manifest_org.id,
        product=PRDS['rhel9'],
        repo=REPOS['rhsclient9']['name'],
        reposet=REPOSET['rhsclient9'],
        releasever=None,
    )
    # Sync step because repo is not synced by default
    rh_repo = module_target_sat.api.Repository(id=rh_repo_id).read()
    rh_repo.sync()

    # Create CV, LCE and AK
    cv = module_target_sat.api.ContentView(organization=module_sca_manifest_org).create()
    lce = module_target_sat.api.LifecycleEnvironment(organization=module_sca_manifest_org).create()
    # Add CV to AK
    cv.repository = [rh_repo]
    cv.update(['repository'])
    cv.publish()
    cv = cv.read()
    # promote the last version published into the module lce
    cv.version[-1].promote(data={'environment_ids': lce.id, 'force': False})

    ak = module_target_sat.api.ActivationKey(
        content_view=cv,
        environment=lce,
        organization=module_sca_manifest_org,
    ).create()
    # Ensure tools repo is enabled in the activation key
    ak.content_override(
        data={'content_overrides': [{'content_label': REPOS['rhsclient9']['id'], 'value': '1'}]}
    )
    return ak


@pytest.fixture(scope="module")
def vm(
    rh_repo_setup_ak,
    module_sca_manifest_org,
    module_rhel_contenthost,
    module_target_sat,
):
    module_rhel_contenthost.register(
        module_sca_manifest_org, None, rh_repo_setup_ak.name, module_target_sat
    )
    # Install older 'python3-gofer' for errata test
    module_rhel_contenthost.run(f'yum install -y {REAL_RHEL9_OUTDATED_PACKAGE_FILENAME}')
    host = module_target_sat.api.Host().search(
        query={'search': f'name={module_rhel_contenthost.hostname}'}
    )
    host_id = host[0].id
    host_content = module_target_sat.api.Host(id=host_id).read_json()
    assert host_content['subscription_facet_attributes']['uuid']
    module_rhel_contenthost.install_katello_host_tools()
    return module_rhel_contenthost


@pytest.mark.pit_client
@pytest.mark.pit_server
@pytest.mark.rhel_ver_match('9')
def test_positive_list_installable_updates(vm, module_target_sat):
    """Ensure packages applicability is functioning properly.

    :id: 4feb692c-165b-4f96-bb97-c8447bd2cf6e

    :steps:

        1. Setup a content host with registration to unrestricted org
        2. Install a package that has updates
        3. Run `hammer package list` specifying option
            packages-restrict-applicable="true".


    :expectedresults:
        1. Update package is available independent of subscription because
            Golden Ticket is enabled.

    :BZ: 1344049, 1498158

    :parametrized: yes

    :CaseImportance: Critical
    """
    for _ in range(30):
        applicable_packages = module_target_sat.cli.Package.list(
            {
                'host': vm.hostname,
                'packages-restrict-applicable': 'true',
                'search': f'name={REAL_RHEL9_PACKAGE}',
            }
        )
        if applicable_packages:
            break
        time.sleep(10)
    assert len(applicable_packages) > 0
    assert REAL_RHEL9_PACKAGE in applicable_packages[0]['filename']


@pytest.mark.upgrade
@pytest.mark.pit_client
@pytest.mark.pit_server
@pytest.mark.rhel_ver_match('9')
def test_positive_erratum_installable(vm, module_target_sat):
    """Ensure erratum applicability is showing properly, without attaching
    any subscription.

    :id: e8dc52b9-884b-40d7-9244-680b5a736cf7

    :steps:
        1. register a host to unrestricted org with Library
        2. install a package, that will need errata to be applied
        3. list the host applicable errata with searching the required
            errata id

    :expectedresults: errata listed successfully and is installable

    :BZ: 1344049, 1498158

    :parametrized: yes

    :CaseImportance: Critical
    """
    # check that package errata is applicable
    for _ in range(30):
        erratum = module_target_sat.cli.Host.errata_list(
            {'host': vm.hostname, 'search': f'id = {REAL_RHEL9_ERRATA_ID}'}
        )
        if erratum:
            break
        time.sleep(10)
    assert len(erratum) == 1
    assert erratum[0]['installable'] == 'true'


@pytest.mark.upgrade
def test_positive_rct_shows_sca_enabled(module_sca_manifest, module_target_sat):
    """Assert unrestricted (SCA) manifest shows SCA enabled.

    :id: 0c6e2f88-1a86-4417-9248-d7bd20584197

    :steps:
        1. Run `rct cat-manifest /tmp/unrestricted_manifest.zip`.

    :expectedresults:
        1. Assert `Content Access Mode: Simple Content Access` is present.

    :CaseImportance: Medium
    """
    with module_sca_manifest as manifest:
        module_target_sat.put(f'{manifest.path}', f'{manifest.name}')
    result = module_target_sat.execute(f'rct cat-manifest {module_sca_manifest.name}')
    assert result.status == 0
    assert 'Content Access Mode: Simple Content Access' in result.stdout


@pytest.mark.rhel_ver_match('9')
def test_negative_unregister_and_pull_content(vm):
    """Attempt to retrieve content after host has been unregistered from Satellite

    :id: de0d0d91-b1e1-4f0e-8a41-c27df4d6b6fd

    :expectedresults: Host can no longer retrieve content from satellite

    :parametrized: yes

    :CaseImportance: Critical
    """
    result = vm.run('subscription-manager unregister')
    assert result.status == 0
    # Try installing any package from available repos on vm
    result = vm.run('yum install -y katello-agent')
    assert result.status != 0
