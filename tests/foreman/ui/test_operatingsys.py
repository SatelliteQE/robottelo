# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Operating System UI
"""

from ddt import ddt
from robottelo.common.constants import (INSTALL_MEDIUM_URL,
                                        OS_TEMPLATE_DATA_FILE,
                                        PARTITION_SCRIPT_DATA_FILE)
from robottelo.common.decorators import data
from robottelo.common.decorators import skip_if_bz_bug_open
from robottelo.common.helpers import generate_string, get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_org, make_loc, make_os,
                                  make_arch, make_media, make_templates,
                                  make_partitiontable)
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class OperatingSys(UITestCase):
    """
    Implements Operating system tests from UI
    """

    org_name = None
    loc_name = None

    def setUp(self):
        super(OperatingSys, self).setUp()
        #  Make sure to use the Class' org_name instance
        if (OperatingSys.org_name is None and OperatingSys.loc_name is None):
            OperatingSys.org_name = generate_string("alpha", 8)
            OperatingSys.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=OperatingSys.org_name)
                make_loc(session, name=OperatingSys.loc_name)

    def test_create_os(self):
        """
        @Test: Create a new OS
        @Feature: OS - Positive Create
        @Assert: OS is created
        """

        name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.search(name))

    @skip_if_bz_bug_open('1120568')
    @data({u'name': generate_string('alpha', 10),
           u'major_version': generate_string('numeric', 1),
           u'minor_version': generate_string('numeric', 1),
           u'desc': generate_string('alpha', 10),
           u'os_family': "Red Hat"},
          {u'name': generate_string('html', 10),
           u'major_version': generate_string('numeric', 4),
           u'minor_version': generate_string('numeric', 4),
           u'desc': generate_string('html', 10),
           u'os_family': "Gentoo"},
          {u'name': generate_string('utf8', 10),
           u'major_version': generate_string('numeric', 5),
           u'minor_version': generate_string('numeric', 5),
           u'desc': generate_string('utf8', 10),
           u'os_family': "SUSE"},
          {u'name': generate_string('alphanumeric', 255),
           u'major_version': generate_string('numeric', 5),
           u'minor_version': generate_string('numeric', 0),
           u'desc': generate_string('alphanumeric', 255),
           u'os_family': "SUSE"})
    def test_positive_create_os(self, test_data):
        """
        @Test: Create a new OS with different data values
        @Feature: OS - Positive Create
        @Assert: OS is created
        @BZ: 1120568
        """

        arch = "i386"
        with Session(self.browser) as session:
            make_os(session, name=test_data['name'],
                    major_version=test_data['major_version'],
                    minor_version=test_data['minor_version'],
                    description=test_data['desc'],
                    os_family=test_data['os_family'], archs=[arch])
            self.assertIsNotNone(self.operatingsys.search(test_data['name']))

    @skip_if_bz_bug_open(1120181)
    def test_negative_create_os_1(self):
        """
        @Test: OS - Create a new OS with 256 characters in name
        @Feature: Create a new OS - Negative
        @Assert: OS is not created
        @BZ: 1120181
        """

        name = generate_string("alpha", 256)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["alert.error"]))
            self.assertIsNone(self.operatingsys.search(name))

    def test_negative_create_os_2(self):
        """
        @Test: OS - Create a new OS with blank name
        @Feature: Create a new OS - Negative
        @Assert: OS is not created
        """
        name = ""
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["name_haserror"]))
            self.assertIsNone(self.operatingsys.search(name))

    def test_negative_create_os_3(self):
        """
        @Test: OS - Create a new OS with description containing
        256 characters
        @Feature: Create a new OS - Negative
        @Assert: OS is not created
        """
        name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        description = generate_string("alphanumeric", 256)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    description=description,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["alert.error"]))
            self.assertIsNone(self.operatingsys.search(name))

    def test_negative_create_os_4(self):
        """
        @Test: OS - Create a new OS with long major version
        @Feature: Create a new OS - Negative
        @Assert: OS is not created
        """
        name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 6)
        minor_version = generate_string('numeric', 1)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["alert.error"]))
            self.assertIsNone(self.operatingsys.search(name))

    def test_negative_create_os_5(self):
        """
        @Test: OS - Create a new OS with long minor version
        @Feature: Create a new OS - Negative
        @Assert: OS is not created
        """
        name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 17)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["alert.error"]))
            self.assertIsNone(self.operatingsys.search(name))

    def test_negative_create_os_6(self):
        """
        @Test: OS - Create a new OS without major version
        @Feature: Create a new OS - Negative
        @Assert: OS is not created
        """
        name = generate_string("alpha", 6)
        major_version = " "
        minor_version = generate_string('numeric', 6)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["haserror"]))
            self.assertIsNone(self.operatingsys.search(name))

    def test_remove_os(self):
        """
        @Test: Delete an existing OS
        @Feature: OS - Positive Delete
        @Assert: OS is deleted
        """

        name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family)
            self.assertIsNotNone(self.operatingsys.search(name))
            self.operatingsys.delete(name, really=True)
            self.assertIsNotNone(self.user.wait_until_element
                                 (common_locators["notif.success"]))
            self.assertIsNone(self.operatingsys.search(name))

    def test_update_os_1(self):
        """
        @Test: Update OS name, major_version, minor_version, os_family
        and arch
        @Feature: OS - Positive Update
        @Assert: OS is updated
        """

        name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        minor_version = generate_string('numeric', 1)
        os_family = "Red Hat"
        new_name = generate_string("alpha", 4)
        new_major_version = generate_string('numeric', 1)
        new_minor_version = generate_string('numeric', 1)
        new_os_family = "Debian"
        new_arch = generate_string("alpha", 4)
        with Session(self.browser) as session:
            make_arch(session, name=new_arch)
            self.assertIsNotNone(self.architecture.search(new_arch))
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family)
            self.assertIsNotNone(self.operatingsys.search(name))
            self.operatingsys.update(name, new_name, new_major_version,
                                     new_minor_version,
                                     os_family=new_os_family,
                                     new_archs=[new_arch])
            self.assertIsNotNone(self.operatingsys.search(new_name))

    def test_update_os_medium(self):
        """
        @Test: Update OS medium
        @Feature: OS - Positive Update
        @Assert: OS is updated
        """

        name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        medium = generate_string("alpha", 4)
        os_family = "x86_64"
        path = INSTALL_MEDIUM_URL % generate_string("alpha", 6)
        with Session(self.browser) as session:
            make_media(session, name=medium, path=path)
            self.assertIsNotNone(self.medium.search(medium))
            make_os(session, name=name,
                    major_version=major_version,
                    os_family=os_family)
            self.assertIsNotNone(self.operatingsys.search(name))
            self.operatingsys.update(name, new_mediums=[medium])
            result_object = self.operatingsys.get_os_entities(name, "medium")
            self.assertEqual(medium, result_object['medium'])

    def test_update_os_partition_table(self):
        """
        @Test: Update OS partition table
        @Feature: OS - Positive Update
        @Assert: OS is updated
        """

        name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        ptable = generate_string("alpha", 4)
        script_file = get_data_file(PARTITION_SCRIPT_DATA_FILE)
        with open(script_file, 'r') as file_contents:
            layout = file_contents.read()
        with Session(self.browser) as session:
            make_partitiontable(session, name=ptable, layout=layout)
            self.assertIsNotNone(self.partitiontable.search(ptable))
            make_os(session, name=name,
                    major_version=major_version)
            self.assertIsNotNone(self.operatingsys.search(name))
            self.operatingsys.update(name, new_ptables=[ptable])
            result_object = self.operatingsys.get_os_entities(name, "ptable")
            self.assertEqual(ptable, result_object['ptable'])

    def test_update_os_template(self):
        """
        @Test: Update provisioning template
        @Feature: OS - Positive Update
        @Assert: OS is updated
        """

        os_name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        template_name = generate_string("alpha", 4)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        os_list = [os_name]
        with Session(self.browser) as session:
            make_os(session, name=os_name,
                    major_version=major_version)
            self.assertIsNotNone(self.operatingsys.search(os_name))
            make_templates(session, name=template_name,
                           template_path=template_path,
                           custom_really=True, temp_type=temp_type,
                           os_list=os_list)
            self.assertIsNotNone(self.template.search(template_name))
            self.navigator.go_to_operating_systems()
            self.operatingsys.update(os_name, template=template_name)
            result_obj = self.operatingsys.get_os_entities(os_name, "template")
            self.assertEqual(template_name, result_obj['template'])

    def test_set_parameter(self):
        """
        @Test: Set OS parameter
        @Feature: OS - Positive Update
        @Assert: OS is updated
        """
        name = generate_string("alpha", 4)
        major_version = generate_string('numeric', 1)
        param_name = generate_string("alpha", 4)
        param_value = generate_string("alpha", 3)
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version)
            self.assertIsNotNone(self.operatingsys.search(name))
            self.operatingsys.set_os_parameter(name, param_name, param_value)

    def test_remove_parameter(self):
        """
        @Test: Remove selected OS parameter
        @Feature: OS - Positive Update
        @Assert: OS is updated
        """
        name = generate_string("alpha", 6)
        major_version = generate_string('numeric', 1)
        param_name = generate_string("alpha", 4)
        param_value = generate_string("alpha", 3)
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version)
            self.operatingsys.set_os_parameter(name, param_name, param_value)
            self.operatingsys.remove_os_parameter(name, param_name)
