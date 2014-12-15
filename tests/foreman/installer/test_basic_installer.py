"""Tests for product installer"""
from robottelo.test import InstallerTestCase


class BasicInstallTestCase(InstallerTestCase):
    """Test the basic product installation"""

    def test_hammer_ping(self):
        """Test hammer ping output"""
        result = self.vm.run('hammer -u admin -p changeme ping')
        self.assertEqual(result.return_code, 0)
