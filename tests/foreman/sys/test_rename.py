# -*- encoding: utf-8 -*-
"""Test class for ``katello-change-hostname``

:Requirement: katello-change-hostname

:CaseAutomation: notautomated

:CaseLevel: System

:CaseComponent: katello-change-hostname

:TestType: Functional

:CaseImportance: High

:Upstream: No

"""
from fauxfactory import gen_string
from robottelo.config import settings
from robottelo.decorators import (
        destructive,
        stubbed,
)
from robottelo.ssh import get_connection
from robottelo.test import TestCase

BCK_MSG = "Hostname change complete!"


@destructive
class RenameHostTestCase(TestCase):
    """Implements ``katello-change-hostname`` tests"""

    @stubbed()
    def test_positive_rename_satellite(self):
        """run katello-change-hostname on Satellite server

        :id: 9944bfb1-1440-4820-ada8-2e219f09c0be

        :setup: Satellite server with synchronized rh and custom
            repos and with a registered host

        :steps:
            1. Rename Satellite using katello-change-hostname
            2. Do basic checks for hostname change (hostnamctl)
            3. Run some existence tests, as in backup testing
            4. Verify certificates were properly recreated, check
                for instances of old hostname
                in etc/foreman-installer/scenarios.d/
            5. Check for updated repo urls, installation media paths,
                updated internal capsule
            6. Check usability of entities created before rename: refresh
                manifest, resync repos, republish CVs and re-register hosts
            7. Create new entities (run end-to-end test from robottelo)

        :bz: 1469466

        :expectedresults: Satellite hostname is successfully updated
            and the server functions correctly
        """
        # Save original hostname, get credentials, eventually will
        # end up in setUpClass
        # original_name = settings.server.hostname
        username = settings.server.admin_username
        password = settings.server.admin_password
        # the rename part of the test, not necessary to run from robotello
        with get_connection() as connection:
            hostname = gen_string('alpha')
            result = connection.run(
                # use -y once implemented BZ#1469466
                'yes | katello-change-hostname -u {0} -p {1}\
                        --disable-system-checks\
                        --scenario satellite {2}'.format(
                    username, password, hostname),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG, result.stdout)
        # reconnecting to a new hostname for additional asserts
        # with get_connection(hostname=hostname) as connection:
        # ...

    @stubbed()
    def test_positive_rename_capsule(self):
        """run katello-change-hostname on Capsule

        :id: 4aa9fd86-bba9-49e4-a67a-8685e1ab5a74

        :setup: Capsule server registered to Satellite, with common features
            enabled, with synchronized content and a host registered to it

        :steps:
            1. Rename Satellite using katello-change-hostname
            2. Do basic checks for hostname change (hostnamctl)
            3. Verify certificates were properly recreated, check
                for instances of old hostname
                in etc/foreman-installer/scenarios.d/
            4. Re-register Capsule to Satellite, resync content
            5. Re-register old host, register new one to Satellite,
            6. Check hosts can consume content, run basic REX command,
                import Puppet environments from hosts

        :BZ: 1469466, 1473614

        :expectedresults: Capsule hostname is successfully updated
            and the capsule fuctions correctly
        """
        # Save original hostname, get credentials, eventually will
        # end up in setUpClass
        # original_name = settings.server.hostname
        username = settings.server.admin_username
        password = settings.server.admin_password
        # the rename part of the test, not necessary to run from robotello
        with get_connection() as connection:
            hostname = gen_string('alpha')
            result = connection.run(
                # use -y once implemented BZ#1469466
                'yes | katello-change-hostname -u {0} -p {1}\
                        --disable-system-checks\
                        --scenario capsule {2}'.format(
                    username, password, hostname),
                output_format='plain'
            )
            self.assertEqual(result.return_code, 0)
            self.assertIn(BCK_MSG, result.stdout)
