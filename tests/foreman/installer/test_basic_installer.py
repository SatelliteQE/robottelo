"""Tests for product installer"""
from robottelo.test import InstallerTestCase


class BasicInstallTestCase(InstallerTestCase):
    """Test the basic product installation"""

    def test_hammer_ping(self):
        """@Test: Test hammer ping command.

        @Feature: Installer Test

        @Assert: Return code is zero

        """
        result = self.vm.run('hammer -u admin -p changeme ping')
        self.assertEqual(result.return_code, 0)
