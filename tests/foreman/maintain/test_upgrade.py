"""Test module for satellite-maintain upgrade functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Platform

:CaseImportance: Critical

"""

import pytest

from robottelo.config import settings
from robottelo.constants import INSTALLER_CONFIG_FILE


def last_y_stream_version(release):
    """Returns the version of the last Y stream

    Example: 6.13.0 -> 6.12
    """
    y = release.split('.')[1]
    y_minus = str(int(y) - 1)
    return f"{release.split('.')[0]}.{y_minus}"


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
    skip_message = 'Your system is subscribed using custom activation key'
    result = sat_maintain.cli.Update.check(
        options={
            'assumeyes': True,
            'disable-self-update': True,
            'whitelist': 'check-non-redhat-repository',
        },
        env_var='EXTERNAL_SAT_ORG=Sat6-CI EXTERNAL_SAT_ACTIVATION_KEY=Ext_AK',
    )
    assert 'SKIPPED' in result.stdout
    assert 'FAIL' not in result.stdout
    assert skip_message in result.stdout


@pytest.mark.no_containers
@pytest.mark.parametrize(
    'custom_host',
    [
        {
            'deploy_rhel_version': settings.server.version.rhel_version,
            'deploy_flavor': 'satqe-ssd.disk.xxxl',
        },
        {
            'deploy_rhel_version': settings.server.version.rhel_version,
            'deploy_flavor': 'satqe-ssd.standard.std',
        },
    ],
    ids=['default', 'medium'],
    indirect=True,
)
def test_negative_pre_update_tuning_profile_check(request, custom_host):
    """Negative test that verifies a satellite with less than
    tuning profile hardware requirements fails on pre-update check.

    :id: 240bb97e-7353-4397-8d0e-228c3593c8cc

    :steps:
        1. Check out a RHEL instance with less than tuning requirements
        2. Install Satellite
        3. Run pre-update check

    :expectedresults: Pre-update check fails.
    """
    profile = request.node.callspec.id
    sat_version = ".".join(settings.server.version.release.split('.')[0:2])
    # Register to CDN for RHEL repos, download and enable ohsnap repos,
    # and enable the satellite module and install it on the host
    custom_host.register_to_cdn()
    custom_host.download_repofile(product='satellite', release=sat_version)
    custom_host.install_satellite_or_capsule_package()
    # Install with development tuning profile to get around installer checks
    custom_host.execute(
        'satellite-installer --scenario satellite --tuning development',
        timeout='30m',
    )
    # Change to correct tuning profile (default or medium)
    custom_host.execute(
        f'sed -i "s/tuning: development/tuning: {profile}/g" {INSTALLER_CONFIG_FILE};'
        f'satellite-installer'
    )
    # Check that the update check fails due to system requirements
    result = custom_host.cli.Update.check(
        options={
            'assumeyes': True,
            'disable-self-update': True,
        }
    )
    assert (
        f'ERROR: The installer is configured to use the {profile} tuning '
        'profile and does not meet the requirements.' in result.stdout
    )


@pytest.mark.include_capsule
def test_positive_self_update_maintain_package(sat_maintain):
    """satellite-maintain attempts to update itself when a command is run

    :id: 1c566768-fd73-4fe6-837b-26709a1ebed9

    :parametrized: yes

    :steps:
        1. Run satellite-maintain update check command.
        2. Run satellite-maintain update check command
            with disable-self-upgrade option.

    :expectedresults:
        1. satellite-maintain tries to update rubygem-foreman_maintain to a newer available version
        2. If disable-self-upgrade option is used then it should skip self-upgrade step

    :BZ: 1649329
    """
    result = sat_maintain.cli.Update.check(
        options={'whitelist': 'repositories-validate, non-rh-packages'}
    )
    assert result.status == 0
    assert 'Checking for new version of satellite-maintain...' in result.stdout
    result = sat_maintain.cli.Update.check(
        options={
            'whitelist': 'repositories-validate, non-rh-packages',
            'disable-self-update': True,
        }
    )
    assert result.status == 0
    assert 'Checking for new version of satellite-maintain...' not in result.stdout


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
        1. Run satellite-maintain upgrade check/run command.
        2. Run satellite-maintain upgrade check/run command,
            after removing satellite and satellite-capsule packages.

    :expectedresults:
        1. If those packages are removed, then it should give error, like
            "Error: Important rpm package satellite/satellite-capsule is not installed!
             Install satellite/satellite-capsule rpm to ensure system consistency."

    :BZ: 1886031

    :customerscenario: true

    :CaseAutomation: ManualOnly
    """
