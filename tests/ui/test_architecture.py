# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Architecture UI
"""

from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_string
from tests.ui.baseui import BaseUI


class Architecture(BaseUI):
    """
    Implements Architecture tests from UI
    """

    def create_arch(self, arch_name, os_name=None):
        """
        Function navigates and creates new architecture from UI
        """
        arch_name = arch_name or generate_name(4)
        os_name = os_name or generate_name(6)
        self.navigator.go_to_architectures()  # go to architecture page
        self.architecture.create(arch_name, os_name)
        self.assertIsNotNone(self.architecture.search(arch_name))

    def test_create_arch(self):
        """
        Create new Arch
        """

        name = generate_name(4)
        os_name = generate_name(6)
        major_version = generate_string('numeric', 1)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_operating_systems()  # go to operating system page
        self.operatingsys.create(os_name, major_version)
        self.assertIsNotNone(self.operatingsys.search(os_name))
        self.create_arch(name, os_name)

    def test_remove_arch(self):
        """
        Delete an existing Arch
        """

        name = generate_name(4)
        os_name = generate_name(6)
        major_version = generate_string('numeric', 1)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_operating_systems()  # go to operating system page
        self.operatingsys.create(os_name, major_version)
        self.assertIsNotNone(self.operatingsys.search(os_name))
        self.create_arch(name, os_name)
        self.architecture.delete(name, True)
        self.assertIsNone(self.architecture.search(name))

    def test_update_arch(self):
        """
        Update arch with new arch-name and new OS
        """

        old_name = generate_name(6)
        new_name = generate_name(4)
        os_name = generate_name(6)
        major_version = generate_string('numeric', 1)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_operating_systems()  # go to operating system page
        self.operatingsys.create(os_name, major_version)
        self.assertIsNotNone(self.operatingsys.search(os_name))
        self.create_arch(old_name)
        self.architecture.update(old_name, new_name, os_name)
        self.assertIsNotNone(self.architecture.search(new_name))
