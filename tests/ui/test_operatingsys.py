# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Operating System UI
"""

from robottelo.ui.locators import common_locators
from robottelo.common.constants import OS_TEMPLATE_URL, PARTITION_SCRIPT_URL, \
    INSTALL_MEDIUM_URL
from robottelo.common.helpers import generate_name, generate_string, \
    download_template
from tests.ui.baseui import BaseUI
from urllib2 import urlopen


class OperatingSys(BaseUI):
    """
    Implements Operating system tests from UI
    """

    def create_os(self, name=None, major_version=None,
                  minor_version=None, os_family=None, archs=None):
        """
        Function to create OS with all navigation steps
        """

        name = name or generate_name(6)
        major_version = major_version or generate_string('numeric', 1)
        minor_version = minor_version or generate_string('numeric', 1)
        self.navigator.go_to_operating_systems()  # go to operating system page
        self.operatingsys.create(name, major_version,
                                 minor_version, os_family, archs)
        self.assertIsNotNone(self.operatingsys.search(name))

    def test_create_os(self):
        """
        create new OS
        """

        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Red Hat"
        arch = generate_name(4)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_architectures()  # go to architecture page
        self.architecture.create(arch)
        self.assertIsNotNone(self.architecture.search(arch))
        self.create_os(name, major_version, minor_version, os_family, [arch])

    def test_remove_os(self):
        """
        Delete an existing OS
        """

        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_os(name, major_version, minor_version, os_family)
        self.operatingsys.delete(name, really=True)
        self.assertTrue(self.user.wait_until_element(common_locators
                                                     ["notif.success"]))
        self.assertIsNone(self.operatingsys.search(name))

    def test_update_os(self):
        """
        Update OS name, major_version, minor_version, os_family and arch
        """

        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Red Hat"
        new_name = generate_name(4)
        new_major_version = generate_string('numeric', 1)
        new_minor_version = generate_string('numeric', 1)
        new_os_family = "Debian"
        new_arch = generate_name(4)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_architectures()  # go to architecture page
        self.architecture.create(new_arch)
        self.assertIsNotNone(self.architecture.search(new_arch))
        self.create_os(name, major_version, minor_version, os_family)
        self.operatingsys.update(name, new_name, new_major_version,
                                 new_minor_version, new_os_family,
                                 new_archs=[new_arch])
        self.assertIsNotNone(self.operatingsys.search(new_name))

    def test_update_os_medium(self):
        """
        Update OS medium
        """

        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        medium = generate_name(4)
        path = INSTALL_MEDIUM_URL % generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_installation_media()
        self.medium.create(medium, path)
        self.assertIsNotNone(self.medium.search(medium))
        self.create_os(name, major_version)
        self.operatingsys.update(name, new_mediums=[medium])

    def test_update_os_partition_table(self):
        """
        Update OS partition table
        """

        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        ptable = generate_name(4)
        layout = urlopen(PARTITION_SCRIPT_URL).read()
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.navigator.go_to_partition_tables()
        self.partitiontable.create(ptable, layout)
        self.assertIsNotNone(self.partitiontable.search(ptable))
        self.create_os(name, major_version)
        self.operatingsys.update(name, new_ptables=[ptable])

    def test_update_os_template(self):
        """
        Updates Provisioning template
        """

        os_name = generate_name(6)
        major_version = generate_string('numeric', 1)
        template_name = generate_name(4)
        temp_type = 'provision'
        template_path = download_template(OS_TEMPLATE_URL)
        os_list = [os_name]
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_os(os_name, major_version)
        self.navigator.go_to_provisioning_templates()
        self.template.create(template_name, template_path, True,
                             temp_type, None, os_list)
        self.assertIsNotNone(self.template.search(template_name))
        self.navigator.go_to_operating_systems()
        self.operatingsys.update(os_name, template=template_name)

    def test_set_parameter(self):
        "Set OS parameter"
        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_os(name, major_version)
        self.operatingsys.set_os_parameter(name, param_name, param_value)

    def test_remove_parameter(self):
        "Remove selected OS parameter"
        name = generate_name(6)
        major_version = generate_string('numeric', 1)
        param_name = generate_name(4)
        param_value = generate_name(3)
        self.login.login(self.katello_user, self.katello_passwd)  # login
        self.create_os(name, major_version)
        self.operatingsys.set_os_parameter(name, param_name, param_value)
        self.operatingsys.remove_os_parameter(name, param_name)
