"""Test for Content Access (Golden Ticket) CLI

:Requirement: Content Access

:CaseLevel: Acceptance

:CaseComponent: Hosts-Content

:CaseAutomation: Automated

:Assignee: shwsingh

:TestType: Functional

:Upstream: No
"""
import time

import pytest
from nailgun import entities

from robottelo import manifests
from robottelo.api.utils import promote
from robottelo.cli.host import Host
from robottelo.cli.package import Package
from robottelo.config import settings
from robottelo.constants import REAL_0_ERRATA_ID
from robottelo.constants import REAL_RHEL7_0_2_PACKAGE_FILENAME
from robottelo.constants import REAL_RHEL7_0_2_PACKAGE_NAME
from robottelo.constants import REPOS

pytestmark = [
    pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    ),
    pytest.mark.run_in_one_thread,
]


@pytest.fixture(scope='module')
def module_lce(module_gt_manifest_org):
    return entities.LifecycleEnvironment(organization=module_gt_manifest_org).create()


@pytest.fixture(scope="module")
def rh_repo_cv(module_gt_manifest_org, rh_repo_gt_manifest, module_lce):
    rh_repo_cv = entities.ContentView(organization=module_gt_manifest_org).create()
    # Add CV to AK
    rh_repo_cv.repository = [rh_repo_gt_manifest]
    rh_repo_cv.update(['repository'])
    rh_repo_cv.publish()
    rh_repo_cv = rh_repo_cv.read()
    # promote the last version published into the module lce
    promote(rh_repo_cv.version[-1], environment_id=module_lce.id)
    return rh_repo_cv


@pytest.fixture(scope="module")
def module_ak(rh_repo_cv, module_gt_manifest_org, module_lce):
    module_ak = entities.ActivationKey(
        content_view=rh_repo_cv,
        environment=module_lce,
        organization=module_gt_manifest_org,
    ).create()
    # Ensure tools repo is enabled in the activation key
    module_ak.content_override(
        data={'content_overrides': [{'content_label': REPOS['rhst7']['id'], 'value': '1'}]}
    )
    return module_ak


@pytest.fixture(scope="module")
def vm(
    rh_repo_gt_manifest,
    module_gt_manifest_org,
    module_ak,
    rhel7_contenthost_module,
    module_target_sat,
):
    # python-psutil obsoleted by python2-psutil, install older python2-psutil for errata test.
    rhel7_contenthost_module.run(
        'rpm -Uvh https://download.fedoraproject.org/pub/epel/7/x86_64/Packages/p/'
        'python2-psutil-5.6.7-1.el7.x86_64.rpm'
    )
    rhel7_contenthost_module.install_katello_ca(module_target_sat)
    rhel7_contenthost_module.register_contenthost(module_gt_manifest_org.label, module_ak.name)
    host = entities.Host().search(query={'search': f'name={rhel7_contenthost_module.hostname}'})
    host_id = host[0].id
    host_content = entities.Host(id=host_id).read_json()
    assert host_content["subscription_status"] == 5
    rhel7_contenthost_module.install_katello_host_tools()
    return rhel7_contenthost_module


@pytest.mark.tier2
@pytest.mark.pit_client
@pytest.mark.pit_server
def test_positive_list_installable_updates(vm):
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
        applicable_packages = Package.list(
            {
                'host': vm.hostname,
                'packages-restrict-applicable': 'true',
                'search': f'name={REAL_RHEL7_0_2_PACKAGE_NAME}',
            }
        )
        if applicable_packages:
            break
        time.sleep(10)
    assert len(applicable_packages) > 0
    assert REAL_RHEL7_0_2_PACKAGE_FILENAME in [
        package['filename'] for package in applicable_packages
    ]


@pytest.mark.tier2
@pytest.mark.upgrade
@pytest.mark.pit_client
@pytest.mark.pit_server
def test_positive_erratum_installable(vm):
    """Ensure erratum applicability is showing properly, without attaching
    any subscription.

    :id: e8dc52b9-884b-40d7-9244-680b5a736cf7

    :steps:
        1. register a host to unrestricted org with Library
        2. install a package, that will need errata to be applied
        3. list the host applicable errata with searching the required
            errata id

    :expectedresults: errata listed successfuly and is installable

    :BZ: 1344049, 1498158

    :parametrized: yes

    :CaseImportance: Critical
    """
    # check that package errata is applicable
    for _ in range(30):
        erratum = Host.errata_list({'host': vm.hostname, 'search': f'id = {REAL_0_ERRATA_ID}'})
        if erratum:
            break
        time.sleep(10)
    assert len(erratum) == 1
    assert erratum[0]['installable'] == 'true'


@pytest.mark.tier2
def test_negative_rct_not_shows_golden_ticket_enabled(target_sat):
    """Assert restricted manifest has no Golden Ticket enabled .

    :id: 754c1be7-468e-4795-bcf9-258a38f3418b

    :steps:

        1. Run `rct cat-manifest /tmp/restricted_manifest.zip`.


    :expectedresults:
        1. Assert `Content Access Mode: Simple Content Access` is not present.

    :CaseImportance: High
    """
    # need a clean org for a new manifest
    org = entities.Organization().create()
    # upload organization manifest with org environment access disabled
    manifest = manifests.clone()
    manifests.upload_manifest_locked(org.id, manifest, interface=manifests.INTERFACE_CLI)
    result = target_sat.execute(f'rct cat-manifest {manifest.filename}')
    assert result.status == 0
    assert 'Content Access Mode: Simple Content Access' not in result.stdout


@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_rct_shows_golden_ticket_enabled(module_gt_manifest_org, target_sat):
    """Assert unrestricted manifest has Golden Ticket enabled .

    :id: 0c6e2f88-1a86-4417-9248-d7bd20584197

    :steps:

        1. Run `rct cat-manifest /tmp/unrestricted_manifest.zip`.

    :expectedresults:
        1. Assert `Content Access Mode: Simple Content Access` is present.

    :CaseImportance: Medium
    """
    result = target_sat.execute(f'rct cat-manifest {module_gt_manifest_org.manifest_filename}')
    assert result.status == 0
    assert 'Content Access Mode: Simple Content Access' in result.stdout


@pytest.mark.tier3
def test_negative_unregister_and_pull_content(vm):
    """Attempt to retrieve content after host has been unregistered from Satellite

    :id: de0d0d91-b1e1-4f0e-8a41-c27df4d6b6fd

    :expectedresults: Host can no longer retrieve content from satellite

    :CaseLevel: System

    :parametrized: yes

    :CaseImportance: Critical
    """
    result = vm.run('subscription-manager unregister')
    assert result.status == 0
    # Try installing any package from available repos on vm
    result = vm.run('yum install -y katello-agent')
    assert result.status != 0
