"""Test module for satellite-maintain upgrade functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: ForemanMaintain

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest

pytestmark = pytest.mark.destructive


@pytest.mark.include_capsule
def test_positive_satellite_maintain_upgrade_list(sat_maintain):
    """List versions this system is upgradable to

    :id: 12efec41-4f09-4199-a20c-a4525e773b78

    :parametrized: yes

    :steps:
        1. Run satellite-maintain upgrade list-versions

    :expectedresults: Versions system is upgradable to are listed.
    """
    xy_version = '.'.join(sat_maintain.version.split('.')[:2])
    previous_xy_version = '.'.join(
        [xy_version.split('.')[0], str(int(xy_version.split('.')[1]) - 1)]
    )
    if sat_maintain.version.startswith(xy_version):
        versions = [f'{xy_version}.z']
    elif sat_maintain.version.startswith(previous_xy_version):
        versions = [f'{previous_xy_version}.z', xy_version]
    else:
        versions = ['Unsupported Satellite/Capsule version']

    result = sat_maintain.cli.Upgrade.list_versions()
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    for ver in versions:
        assert ver in result.stdout


@pytest.mark.include_capsule
def test_positive_repositories_validate(sat_maintain):
    """Test repositories-validate pre-upgrade check is
     skipped when system is subscribed using custom activationkey.

    :id: 811698c0-09da-4727-8886-077aebb2b5ed

    :parametrized: yes

    :steps:
        1. Run satellite-maintain upgrade check.

    :expectedresults: repositories-validate check should be skipped.

    :BZ: 1632111
    """
    xy_version = '.'.join(sat_maintain.version.split('.')[:2])
    skip_message = 'Your system is subscribed using custom activation key'
    result = sat_maintain.cli.Upgrade.check(
        options={
            'assumeyes': True,
            'target-version': f'{xy_version}.z',
            'whitelist': 'check-non-redhat-repository',
        },
        env_var='EXTERNAL_SAT_ORG=Sat6-CI EXTERNAL_SAT_ACTIVATION_KEY=Ext_AK',
    )
    assert 'SKIPPED' in result.stdout
    assert 'FAIL' not in result.stdout
    assert skip_message in result.stdout


@pytest.mark.stubbed
@pytest.mark.include_capsule
def test_positive_self_update_for_zstream(sat_maintain):
    """Test satellite-maintain self-upgrade to update maintain packages from zstream repo.

    :id: 1c566768-fd73-4fe6-837b-26709a1ebed9

    :parametrized: yes

    :steps:
        1. Run satellite-maintain upgrade check/run command.
        2. Run satellite-maintain upgrade check/run command with disable-self-upgrade option.

    :expectedresults:
        1. Update satellite-maintain package to latest version and gives message to re-run command.
        2. If disable-self-upgrade option is used then it should skip self-upgrade step for zstream

    :BZ: 1649329

    :CaseAutomation: ManualOnly
    """


@pytest.mark.stubbed
@pytest.mark.include_capsule
def test_positive_self_upgrade_for_ystream(sat_maintain):
    """Test satellite-maintain self-upgrade to update maintain packages from ystream repo.

    :id: d31b3a2c-59e9-11ed-ad2d-b723b07b4b09

    :parametrized: yes

    :steps:
        1. Run satellite-maintain self-upgrade command.
        2. Run satellite-maintain self-upgrade command with --maintenance-repo-label flag
        3. Run satellite-maintain self-upgrade command with MAINTENANCE_REPO_LABEL env var

    :expectedresults:
        1. Update satellite-maintain packages to latest versions,
            from next version maintenance repo from CDN
        2. If --maintenance-repo-label flag and MAINTENANCE_REPO_LABEL env var is used,
            then it should use local yum repo

    :BZ: 2026415

    :CaseAutomation: ManualOnly
    """


@pytest.mark.stubbed
@pytest.mark.include_capsule
def test_positive_check_presence_satellite_or_satellite_capsule(sat_maintain):
    """Check for presence of satellite or satellite-capsule packages feature.

    :id: 1011ff01-6dfb-422f-92c5-995d38bc163e

    :parametrized: yes

    :steps:
        1. Run satellite-maintain upgrade list-versions/check/run command.
        2. Run satellite-maintain upgrade list-versions/check/run command,
            after removing satellite and satellite-capsule packages.

    :expectedresults:
        1. If those packages are removed, then it should give error, like
            "Error: Important rpm package satellite/satellite-capsule is not installed!
             Install satellite/satellite-capsule rpm to ensure system consistency."

    :BZ: 1886031

    :customerscenario: true

    :CaseAutomation: ManualOnly
    """
