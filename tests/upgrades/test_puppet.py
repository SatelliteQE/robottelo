"""Test for Remote Execution related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
import pytest

from robottelo.config import settings
from robottelo.hosts import Capsule


@pytest.fixture(scope='module', params=[True, False], ids=["satellite", "capsule"])
def upgrade_server(request, module_target_sat):
    if request.param:
        return module_target_sat
    else:
        return Capsule(settings.upgrade.capsule_hostname)


class TestPuppet:
    """
    Test puppet availability on the upgraded setup.
    """

    @pytest.mark.post_upgrade
    def test_post_puppet_active(self, upgrade_server):
        """Test that puppet remains active after the upgrade on both,
        Satellite and Capsule.

        :id: postupgrade-6360e928-ba0f-41a7-9aaa-bea87cb6342d

        :steps:
            1. Check for capsule features.
            2. Check for puppetserver status.

        :expectedresults:
            1. Puppet and Puppetca features are enabled.
            2. Puppetserver is installed and runnning.

        :parametrized: yes

        """
        result = upgrade_server.get_features()
        assert 'puppet' in result
        assert 'puppetca' in result

        result = upgrade_server.execute('rpm -q puppetserver')
        assert result.status == 0

        result = upgrade_server.execute('systemctl status puppetserver')
        assert 'active (running)' in result.stdout

    @pytest.mark.post_upgrade
    def test_post_puppet_reporting(self, target_sat):
        """Test that puppet is reporting to Satellite after the upgrade.

        :id:   postupgrade-cdc4f6cc-23d8-4b4a-bd94-5c86b3072828

        :steps:
            1. Run puppet agent on the registered Capsule.
            2. On Satellite, read puppet-originated Config reports for the Capsule host.

        :expectedresults:
            1. Puppet agent run succeeds.
            2. At least one Config report exists (was created) for the Capsule.

        """
        default_caps = Capsule(settings.upgrade.capsule_hostname)

        result = default_caps.execute('puppet agent -t')
        assert result.status == 0

        result = target_sat.cli.ConfigReport.list(
            {'search': f'host={default_caps.hostname},origin=Puppet'}
        )
        assert len(result)
