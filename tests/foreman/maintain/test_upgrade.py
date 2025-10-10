"""Test module for satellite-maintain upgrade functionality

:Requirement: foreman-maintain

:CaseAutomation: Automated

:CaseComponent: SatelliteMaintain

:Team: Rocket

:CaseImportance: Critical

"""

import pytest

from robottelo.config import settings
from robottelo.constants import SATELLITE_INSTALLER_CONFIG
from robottelo.utils.ohsnap import dogfood_repository


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
            'deploy_network_type': settings.server.network_type,
        },
        {
            'deploy_rhel_version': settings.server.version.rhel_version,
            'deploy_flavor': 'satqe-ssd.standard.std',
            'deploy_network_type': settings.server.network_type,
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
    custom_host.enable_ipv6_dnf_and_rhsm_proxy()
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
        f'sed -i "s/tuning: development/tuning: {profile}/g" {SATELLITE_INSTALLER_CONFIG};'
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
    assert (
        'Checking for new version of satellite-maintain, rubygem-foreman_maintain...'
        in result.stdout
    )
    result = sat_maintain.cli.Update.check(
        options={
            'whitelist': 'repositories-validate, non-rh-packages',
            'disable-self-update': True,
        }
    )
    assert result.status == 0
    assert (
        'Checking for new version of satellite-maintain, rubygem-foreman_maintain...'
        not in result.stdout
    )


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


@pytest.mark.upgrade
def test_positive_upgrade_check_capsule_hammer(module_capsule_configured):
    """Test satellite-maintain upgrade check for capsule with hammer installed.

    :id: 903a4140-74f3-428a-8768-ecb610fef2fa

    :steps:
        1. Sync utils repo on Capsule
        2. install hammer on Capsule
        3. Add satellite-capsule repo on Capsule
        4. Add maintenance repo on Capsule
        5. run satellite-maintain upgrade check
        6. run satellite-maintain upgrade run
        7. verify that the capsule is upgraded
        8. verify that the hammer is installed on Capsule

    :expectedresults:
        1. The utils repo should be installed on Capsule
        2. The hammer should be installed on Capsule
        3. The satellite-capsule repo should be installed on Capsule
        4. The capsule should be upgraded
        5. The hammer should be installed on Capsule

    :Verifies: SAT-37909
    """
    repo_config = f"[utils]\nname=Utils Repository\nbaseurl={settings.repos.satutils_repo}\nenabled=1\ngpgcheck=0\n"
    result = module_capsule_configured.execute(
        f'cat > /etc/yum.repos.d/utils.repo << EOF\n{repo_config}\nEOF'
    )
    assert result.status == 0
    result = module_capsule_configured.execute('yum clean all && yum makecache')
    assert "Utils Repository" in result.stdout
    assert result.status == 0
    result = module_capsule_configured.execute('yum install rubygem-hammer_cli_katello -y')
    assert result.status == 0
    result = module_capsule_configured.execute('rpm -qa | grep -i "hammer"')
    assert "hammer_cli_katello" in result.stdout
    assert result.status == 0

    capsule = dogfood_repository(
        ohsnap=settings.ohsnap,
        repo='capsule',
        product='capsule',
        release='stream',
        os_release=9,
        snap='',
        arch='x86_64',
    )
    maintenance = dogfood_repository(
        ohsnap=settings.ohsnap,
        repo='maintenance',
        product='capsule',
        release='stream',
        os_release=9,
        snap='',
        arch='x86_64',
    )
    capsul_config = (
        f"[capsule]\nname=Capsuls Repository\nbaseurl={capsule.baseurl}\nenabled=1\ngpgcheck=0\n"
    )
    maintainance_config = f"[maintenance]\nname=Capsuls Repository\nbaseurl={maintenance.baseurl}\nenabled=1\ngpgcheck=0\n"

    result = module_capsule_configured.execute(
        f'cat > /etc/yum.repos.d/satellite-capsule.repo << EOF\n{capsul_config}\nEOF'
    )
    assert result.status == 0
    result = module_capsule_configured.execute(
        f'cat >> /etc/yum.repos.d/satellite-capsule.repo << EOF\n{maintainance_config}\nEOF'
    )
    assert result.status == 0

    result = module_capsule_configured.cli.Upgrade.check(
        options={'whitelist': 'repositories-validate, non-rh-packages', 'assumeyes': True}
    )
    assert result.status == 75
    assert "Successfully updated satellite-maintain" in result.stdout
    result = module_capsule_configured.cli.Upgrade.run(
        options={
            'whitelist': 'repositories-validate, non-rh-packages, repositories-setup, pulpcore-rpm-datarepair',
            'assumeyes': True,
        }
    )
    assert result.status == 0
    assert "Upgrade finished." in result.stdout
    result = module_capsule_configured.execute('rpm -qa | grep -i "capsule"')
    assert result.status == 0
    assert "satellite-capsule-6.19" in result.stdout
    result = module_capsule_configured.execute('rpm -qa | grep -i "hammer"')
    assert "hammer_cli_katello" in result.stdout
    assert result.status == 0
