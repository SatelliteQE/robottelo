"""Test for Foreman-maintain related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: ForemanMaintain

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from unittest2.case import TestCase
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade

from robottelo import ssh


class TestScenarioForemanMaintain(TestCase):
    """The test class contains pre-upgrade and post-upgrade scenarios to test
    foreman-maintain utility

    Test Steps:

    1. Before Satellite upgrade, Perform test for
       foreman-maintain upgrade list-versions.
    2. Upgrade satellite/capsule.
    3. Perform tests for foreman-maintain upgrade list-versions, after upgrade.
    4. Check if tests passed.

    """

    @staticmethod
    def satellite_upgradable_version_list():
        """
        This function is used to collect the details of satellite version  and upgradable
        version list.

        :return: satellite_version, upgradeable_version, major_version_change
        """

        cmd = "rpm -q satellite > /dev/null && rpm -q satellite --queryformat=%{VERSION}"
        satellite_version = ssh.command(cmd)
        if satellite_version.return_code == 0:
            satellite_version = satellite_version.stdout
        else:
            return [], [], None, None
        forman_maintain_version = ssh.command(
            "foreman-maintain upgrade list-versions --disable-self-upgrade"
        )
        upgradeable_version = [
            version for version in forman_maintain_version.stdout if version != ''
        ]
        version_change = 0
        for version in upgradeable_version:
            version_change += int(version.split('.')[0])
        if version_change % 2 == 0:
            major_version_change = False
            y_version = ''
        else:
            major_version_change = True
            y_version = list(set(forman_maintain_version) - set(satellite_version))[0].split('.')[
                -1
            ]

        return satellite_version, upgradeable_version, major_version_change, y_version

    @staticmethod
    def version_details(
        satellite_version, major_version_change, y_version, upgrade_stage="pre-upgrade"
    ):
        """
        This function is used to update the details of zstream upgrade and
        next version upgrade
        :param str satellite_version: satellite version would be like 6.5.0, 6.6.0, 6,7.0
        :param bool major_version_change: For major version upgrade like 6.8 to 7.0, 7.0
        to 8.0 etc, then major_version_change would be True.
        :param str y_version: y_version change depends on major_version_change
        :param str upgrade_stage: upgrade stage would be pre or post.
        :return: zstream_version, next_version
        """

        major_version = satellite_version.split('.')[0:1]
        if major_version_change:
            major_version = [int(major_version[0]) + 1].append(y_version)
        else:
            y_version = int(satellite_version.split('.')[0:2][-1])
        zstream_version = ''
        if upgrade_stage == "pre-upgrade":
            major_version.append(str(y_version + 1))
            zstream_version = ".".join(satellite_version.split('.')[0:2]) + ".z"
        else:
            major_version.append(str(y_version))
            major_version.append("z")
        next_version = ".".join(major_version)
        return zstream_version, next_version

    @pre_upgrade
    def test_pre_foreman_maintain_upgrade_list_versions(self):
        """Pre-upgrade sceanrio that tests list of satellite version
        which satellite can be upgraded.

        :id: preupgrade-fc2c54b2-2663-11ea-b47c-48f17f1fc2e1

        :steps:
            1. Run foreman-maintain upgrade list-versions

        :expectedresults: Versions should be current z-stream.

        """
        (
            satellite_version,
            upgradable_version,
            major_version_change,
            y_version,
        ) = self.satellite_upgradable_version_list()
        if satellite_version:
            # In future If foreman-maintain packages update add before
            # pre-upgrade test case execution then next version kind of
            # stuff check we can add it here.
            zstream_version, next_version = self.version_details(
                satellite_version[0], major_version_change, y_version
            )
        else:
            zstream_version = -1
        self.assertIn(zstream_version, upgradable_version)

    @post_upgrade
    def test_post_foreman_maintain_upgrade_list_versions(self):
        """Post-upgrade sceanrio that tests list of satellite version
        which satellite can be upgraded.

        :id: postupgrade-0bce689c-2664-11ea-b47c-48f17f1fc2e1

        :steps:
            1. Run foreman-maintain upgrade list-versions.

        :expectedresults: Versions should be next z-stream.

        """
        (
            satellite_version,
            upgradable_version,
            major_version_change,
            y_version,
        ) = self.satellite_upgradable_version_list()
        if satellite_version:
            zstream_version, next_version = self.version_details(
                satellite_version[0], major_version_change, y_version, upgrade_stage="post-upgrade"
            )
        else:
            next_version = -1
        self.assertIn(next_version, upgradable_version)
