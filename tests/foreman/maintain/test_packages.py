"""Test class for satellite-maintain packages functionality

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

from robottelo.config import settings
from robottelo.utils.installer import InstallerCommand

pytestmark = pytest.mark.destructive


@pytest.mark.include_capsule
def test_positive_fm_packages_lock_unlock(sat_maintain):
    """Verify whether packages get locked and unlocked for satellite and capsule
    using foreman_maintain

    :id: d387d8be-10ad-4a62-aeff-3bc6a82e6bae

    :parametrized: yes

    :steps:
        1. Run satellite-maintain packages lock
        2. Run satellite-maintain packages status
        3. Run satellite-maintain packages is-locked
        4. Run satellite-maintain packages unlock
        5. Run satellite-maintain packages status
        6. Run satellite-maintain packages is-locked

    :expectedresults: Packages get locked and unlocked using foreman_maintain
    """
    # Packages locking is enabled in installer for satellite, and disabled for capsule by default
    installer = 'disabled' if sat_maintain.__class__.__name__ == 'Capsule' else 'enabled'

    # Test Package lock command
    result = sat_maintain.cli.Packages.lock()
    assert 'FAIL' not in result.stdout
    assert result.status == 0

    result = sat_maintain.cli.Packages.status()
    assert 'Packages are locked.' in result.stdout
    assert f'Automatic locking of package versions is {installer} in installer.' in result.stdout
    assert 'FAIL' not in result.stdout
    assert result.status == 0

    result = sat_maintain.cli.Packages.is_locked()
    assert 'Packages are locked' in result.stdout
    assert result.status == 0

    # Test package unlock command
    result = sat_maintain.cli.Packages.unlock()
    assert 'FAIL' not in result.stdout
    assert result.status == 0

    result = sat_maintain.cli.Packages.status()
    assert 'FAIL' not in result.stdout
    assert 'Packages are not locked.' in result.stdout
    assert f'Automatic locking of package versions is {installer} in installer.' in result.stdout
    assert result.status == 0

    result = sat_maintain.cli.Packages.is_locked()
    assert 'Packages are not locked' in result.stdout
    assert result.status == 1

    # Teardown: lock packages of satellite, for capsule its unlocked by default
    if sat_maintain.__class__.__name__ == 'Satellite':
        result = sat_maintain.cli.Packages.lock()
        assert 'FAIL' not in result.stdout
        assert result.status == 0


@pytest.mark.include_capsule
def test_positive_lock_package_versions_with_installer(sat_maintain):
    """Verify whether packages get locked and unlocked for satellite and capsule
    using satellite-installer

    :id: 9218a718-038c-48bb-b4a4-d4cb74859ddb

    :parametrized: yes

    :steps:
        1. Run satellite-installer --lock-package-versions
        2. Run satellite-maintain packages status
        3. Run satellite-maintain packages is-locked
        4. Run satellite-installer --no-lock-package-versions
        5. Run satellite-maintain packages status
        6. Run satellite-maintain packages is-locked
        7. Teardown (Run satellite-installer --lock-package-versions)

    :expectedresults: Packages get locked and unlocked using satellite-installer
    """
    # Test whether packages are locked or not
    result = sat_maintain.install(InstallerCommand('lock-package-versions'))
    assert result.status == 0
    assert 'Success!' in result.stdout

    result = sat_maintain.cli.Packages.status()
    assert 'Packages are locked.' in result.stdout
    assert 'Automatic locking of package versions is enabled in installer.' in result.stdout
    assert 'FAIL' not in result.stdout
    assert result.status == 0

    result = sat_maintain.cli.Packages.is_locked()
    assert 'Packages are locked' in result.stdout
    assert result.status == 0

    # Test whether packages are unlocked or not
    result = sat_maintain.install(InstallerCommand('no-lock-package-versions'))
    assert result.status == 0
    assert 'Success!' in result.stdout

    result = sat_maintain.cli.Packages.status()
    assert 'FAIL' not in result.stdout
    assert 'Packages are not locked.' in result.stdout
    assert 'Automatic locking of package versions is disabled in installer.' in result.stdout
    assert result.status == 0

    result = sat_maintain.cli.Packages.is_locked()
    assert 'Packages are not locked' in result.stdout
    assert result.status == 1

    # Teardown: lock packages of satellite, for capsule its unlocked by default
    if sat_maintain.__class__.__name__ == 'Satellite':
        result = sat_maintain.install(InstallerCommand('lock-package-versions'))
        assert result.status == 0
        assert 'Success!' in result.stdout


@pytest.mark.include_capsule
def test_positive_fm_packages_install(request, sat_maintain):
    """Verify whether packages install/update work as expected.

    :id: 645a3d84-34cb-469c-8b79-105b889aac78

    :parametrized: yes

    :steps:
        1. Run satellite-installer --lock-package-versions
        2. Run satellite-maintain packages status
        3. Run satellite-maintain packages is-locked
        4. Try to install/update package using satellite-maintain packages install/update command.
        5. Run satellite-installer --no-lock-package-versions
        6. Run satellite-maintain packages status
        7. Run satellite-maintain packages is-locked
        8. Try to install package in unlocked state.
        9. Teardown (Run satellite-installer --lock-package-versions)

    :expectedresults: Packages get install/update when lock/unlocked.
    """
    # Test whether packages are locked or not
    result = sat_maintain.install(InstallerCommand('lock-package-versions'))
    assert result.status == 0
    assert 'Success!' in result.stdout

    result = sat_maintain.cli.Packages.status()
    assert 'Packages are locked.' in result.stdout
    assert 'Automatic locking of package versions is enabled in installer.' in result.stdout
    assert 'FAIL' not in result.stdout
    assert result.status == 0

    result = sat_maintain.cli.Packages.is_locked()
    assert 'Packages are locked' in result.stdout
    assert result.status == 0

    result = sat_maintain.execute('dnf install -y zsh')
    assert result.status == 1
    assert 'Use foreman-maintain packages install/update <package>' in result.stdout

    # Test whether satellite-maintain packages install/update command works as expected.
    result = sat_maintain.cli.Packages.install(packages='zsh', options={'assumeyes': True})
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    assert 'Nothing to do' not in result.stdout
    assert 'Packages are locked.' in result.stdout
    assert 'Automatic locking of package versions is enabled in installer.' in result.stdout

    result = sat_maintain.cli.Packages.update(packages='zsh', options={'assumeyes': True})
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    assert 'Nothing to do' not in result.stdout
    assert 'Packages are locked.' in result.stdout
    assert 'Automatic locking of package versions is enabled in installer.' in result.stdout

    # Test whether packages are unlocked or not
    result = sat_maintain.install(InstallerCommand('no-lock-package-versions'))
    assert result.status == 0
    assert 'Success!' in result.stdout

    result = sat_maintain.cli.Packages.status()
    assert result.status == 0
    assert 'FAIL' not in result.stdout
    assert 'Packages are not locked.' in result.stdout
    assert 'Automatic locking of package versions is disabled in installer.' in result.stdout

    result = sat_maintain.cli.Packages.is_locked()
    assert 'Packages are not locked' in result.stdout
    assert result.status == 1

    result = sat_maintain.execute('dnf remove -y zsh')
    assert result.status == 0

    result = sat_maintain.execute('dnf install -y zsh')
    assert result.status == 0
    assert 'Use foreman-maintain packages install/update <package>' not in result.stdout

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.execute('dnf remove -y zsh').status == 0
        if sat_maintain.__class__.__name__ == 'Satellite':
            result = sat_maintain.install(InstallerCommand('lock-package-versions'))
            assert result.status == 0
            assert 'Success!' in result.stdout


@pytest.mark.include_capsule
def test_positive_fm_packages_update(request, sat_maintain):
    """Verify whether packages check-update and update work as expected.

    :id: 354d9940-10f1-4244-9079-fdbd24be49b3

    :parametrized: yes

    :steps:
        1. Run satellite-maintain packages check-update
        2. Run satellite-maintain packages update to update the walrus package.

    :expectedresults: check-update subcommand should list walrus package for update
        and update subcommand should update the walrus package.

    :BZ: 1803975

    :customerscenario: true
    """
    # Setup custom_repo and packages update
    sat_maintain.create_custom_repos(custom_repo=settings.repos.yum_0.url)
    disableplugin = '--disableplugin=foreman-protector'
    assert sat_maintain.execute(f'dnf -y {disableplugin} install walrus').status == 0
    assert sat_maintain.execute(f'dnf -y {disableplugin} downgrade walrus-0.71-1').status == 0

    # Run satellite-maintain packages check update and verify walrus package is available for update
    result = sat_maintain.cli.Packages.check_update()
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    assert 'walrus' in result.stdout
    # Run satellite-maintain packages update
    result = sat_maintain.cli.Packages.update(packages='walrus', options={'assumeyes': True})
    assert 'FAIL' not in result.stdout
    assert result.status == 0
    # Verify walrus package is updated.
    result = sat_maintain.execute('rpm -qa walrus')
    assert result.status == 0
    assert 'walrus-5.21-1' in result.stdout

    @request.addfinalizer
    def _finalize():
        assert sat_maintain.execute('dnf remove -y walrus').status == 0
        sat_maintain.execute('rm -rf /etc/yum.repos.d/custom_repo.repo')


@pytest.mark.stubbed
def test_positive_fm_packages_sat_installer(sat_maintain):
    """Verify satellite-installer is not executed after install/update
    of satellite-maintain/rubygem-foreman_maintain package

    :id: d73971a1-68b4-4ab2-a87c-76cc5ff80a39

    :steps:
        1. satellite-maintain packages install/update satellite-maintain/rubygem-foreman_maintain

    :BZ: 1825841

    :expectedresults: satellite-installer shouldn't be executed after install/update
        of satellite-maintain/rubygem-foreman_maintain package

    :CaseAutomation: ManualOnly
    """
