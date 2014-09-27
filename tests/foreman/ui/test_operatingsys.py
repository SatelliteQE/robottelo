# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Operating System UI"""

from ddt import ddt
from fauxfactory import FauxFactory
from robottelo import entities
from robottelo.common.constants import (
    INSTALL_MEDIUM_URL, PARTITION_SCRIPT_DATA_FILE)
from robottelo.common.decorators import data
from robottelo.common.decorators import run_only_on, skip_if_bug_open
from robottelo.common.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_os
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class OperatingSys(UITestCase):
    """Implements Operating system tests from UI"""

    org_name = None
    loc_name = None
    org_id = None
    loc_id = None

    def setUp(self):
        super(OperatingSys, self).setUp()
        #  Make sure to use the Class' org_name instance
        if OperatingSys.org_name is None and OperatingSys.loc_name is None:
            org_name = FauxFactory.generate_string("alpha", 8)
            loc_name = FauxFactory.generate_string("alpha", 8)
            org_attrs = entities.Organization(name=org_name).create()
            loc_attrs = entities.Location(name=loc_name).create()
            OperatingSys.org_name = org_attrs['name']
            OperatingSys.org_id = org_attrs['id']
            OperatingSys.loc_name = loc_attrs['name']
            OperatingSys.loc_id = loc_attrs['id']

    def test_create_os(self):
        """@Test: Create a new OS

        @Feature: OS - Positive Create

        @Assert: OS is created

        """

        name = FauxFactory.generate_string("alpha", 6)
        major_version = FauxFactory.generate_string('numeric', 1)
        minor_version = FauxFactory.generate_string('numeric', 1)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.search(name))

    @data({u'name': FauxFactory.generate_string('alpha', 10),
           u'major_version': FauxFactory.generate_string('numeric', 1),
           u'minor_version': FauxFactory.generate_string('numeric', 1),
           u'desc': FauxFactory.generate_string('alpha', 10),
           u'os_family': "Red Hat"},
          {u'name': FauxFactory.generate_string('html', 10),
           u'major_version': FauxFactory.generate_string('numeric', 4),
           u'minor_version': FauxFactory.generate_string('numeric', 4),
           u'desc': FauxFactory.generate_string('html', 10),
           u'os_family': "Gentoo"},
          {u'name': FauxFactory.generate_string('utf8', 10),
           u'major_version': FauxFactory.generate_string('numeric', 5),
           u'minor_version': FauxFactory.generate_string('numeric', 16),
           u'desc': FauxFactory.generate_string('utf8', 10),
           u'os_family': "SUSE"},
          {u'name': FauxFactory.generate_string('alphanumeric', 255),
           u'major_version': FauxFactory.generate_string('numeric', 5),
           u'minor_version': FauxFactory.generate_string('numeric', 1),
           u'desc': FauxFactory.generate_string('alphanumeric', 255),
           u'os_family': "SUSE"})
    def test_positive_create_os(self, test_data):
        """@Test: Create a new OS with different data values

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
            self.assertIsNotNone(self.operatingsys.search
                                 (test_data['desc'], search_key="description"))

    def test_negative_create_os_1(self):
        """@Test: OS - Create a new OS with 256 characters in name

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        @BZ: 1120181

        """

        name = FauxFactory.generate_string("alpha", 256)
        major_version = FauxFactory.generate_string('numeric', 1)
        minor_version = FauxFactory.generate_string('numeric', 1)
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

    def test_negative_create_os_2(self):
        """@Test: OS - Create a new OS with blank name

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        """
        name = ""
        major_version = FauxFactory.generate_string('numeric', 1)
        minor_version = FauxFactory.generate_string('numeric', 1)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["name_haserror"]))

    def test_negative_create_os_3(self):
        """@Test: OS - Create a new OS with description containing
        256 characters

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        """
        name = FauxFactory.generate_string("alpha", 6)
        major_version = FauxFactory.generate_string('numeric', 1)
        minor_version = FauxFactory.generate_string('numeric', 1)
        description = FauxFactory.generate_string("alphanumeric", 256)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    description=description,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["haserror"]))
            self.assertIsNone(self.operatingsys.search(name))

    def test_negative_create_os_4(self):
        """@Test: OS - Create a new OS with long major version (More than 5
        characters in major version)

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        """
        name = FauxFactory.generate_string("alpha", 6)
        major_version = FauxFactory.generate_string('numeric', 6)
        minor_version = FauxFactory.generate_string('numeric', 1)
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

    def test_negative_create_os_5(self):
        """@Test: OS - Create a new OS with long minor version (More than 16
        characters in minor version)

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        """
        name = FauxFactory.generate_string("alpha", 6)
        major_version = FauxFactory.generate_string('numeric', 1)
        minor_version = FauxFactory.generate_string('numeric', 17)
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

    def test_negative_create_os_6(self):
        """@Test: OS - Create a new OS without major version

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        """
        name = FauxFactory.generate_string("alpha", 6)
        major_version = " "
        minor_version = FauxFactory.generate_string('numeric', 6)
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

    def test_negative_create_os_7(self):
        """@Test: OS - Create a new OS with -ve value of major version

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        @BZ: 1120199

        """
        name = FauxFactory.generate_string("alpha", 6)
        major_version = "-6"
        minor_version = "-5"
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

    @skip_if_bug_open('bugzilla', 1120985)
    def test_negative_create_os_8(self):
        """@Test: OS - Create a new OS with same name and version

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        @BZ: 1120985

        """
        name = FauxFactory.generate_string("alpha", 6)
        major_version = FauxFactory.generate_string('numeric', 1)
        minor_version = FauxFactory.generate_string('numeric', 1)
        os_family = "Red Hat"
        arch = "x86_64"
        with Session(self.browser) as session:
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.search(name))
            make_os(session, name=name,
                    major_version=major_version,
                    minor_version=minor_version,
                    os_family=os_family, archs=[arch])
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["haserror"]))
            self.assertIsNone(self.operatingsys.search(name))

    def test_remove_os(self):
        """@Test: Delete an existing OS

        @Feature: OS - Positive Delete

        @Assert: OS is deleted

        """
        os_name = entities.OperatingSystem().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            self.operatingsys.delete(os_name, really=True)
            self.assertIsNotNone(self.user.wait_until_element
                                 (common_locators["notif.success"]))
            self.assertIsNone(self.operatingsys.search(os_name))

    @data(
        {u'new_name': FauxFactory.generate_string('alpha', 10),
         u'new_major_version': FauxFactory.generate_string('numeric', 1),
         u'new_minor_version': FauxFactory.generate_string('numeric', 1),
         u'new_os_family': "Red Hat"},
        {u'new_name': FauxFactory.generate_string('html', 10),
         u'new_major_version': FauxFactory.generate_string('numeric', 4),
         u'new_minor_version': FauxFactory.generate_string('numeric', 4),
         u'new_os_family': "Gentoo"},
        {u'new_name': FauxFactory.generate_string('utf8', 10),
         u'new_major_version': FauxFactory.generate_string('numeric', 5),
         u'new_minor_version': FauxFactory.generate_string('numeric', 16),
         u'new_os_family': "SUSE"},
        {u'new_name': FauxFactory.generate_string('alphanumeric', 255),
         u'new_major_version': FauxFactory.generate_string('numeric', 5),
         u'new_minor_version': FauxFactory.generate_string('numeric', 1),
         u'new_os_family': "SUSE"}
    )
    def test_update_os_1(self, test_data):
        """@Test: Update OS name, major_version, minor_version, os_family
        and arch

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """

        os_name = entities.OperatingSystem().create()['name']
        arch_name = entities.Architecture().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            self.operatingsys.update(os_name, test_data['new_name'],
                                     test_data['new_major_version'],
                                     test_data['new_minor_version'],
                                     os_family=test_data['new_os_family'],
                                     new_archs=[arch_name])
            self.assertIsNotNone(self.operatingsys.search(
                test_data['new_name']))

    def test_update_os_medium(self):
        """@Test: Update OS medium

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """

        medium_name = FauxFactory.generate_string("alpha", 4)
        path = INSTALL_MEDIUM_URL % medium_name
        entities.Media(
            name=medium_name,
            media_path=path,
        ).create()
        os_name = entities.OperatingSystem().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            self.operatingsys.update(os_name, new_mediums=[medium_name])
            result_obj = self.operatingsys.get_os_entities(os_name, "medium")
            self.assertEqual(medium_name, result_obj['medium'])

    def test_update_os_partition_table(self):
        """@Test: Update OS partition table

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """

        ptable = FauxFactory.generate_string("alpha", 4)
        script_file = get_data_file(PARTITION_SCRIPT_DATA_FILE)
        with open(script_file, 'r') as file_contents:
            layout = file_contents.read()
        entities.PartitionTable(
            name=ptable,
            layout=layout,
        ).create()
        os_name = entities.OperatingSystem().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            self.operatingsys.update(os_name, new_ptables=[ptable])
            result_obj = self.operatingsys.get_os_entities(os_name, "ptable")
            self.assertEqual(ptable, result_obj['ptable'])

    def test_update_os_template(self):
        """@Test: Update provisioning template

        @Feature: OS - Positive Update

        @Assert: OS is updated

        @BZ: 1129612

        """
        os_name = FauxFactory.generate_string("alpha", 4)
        template_name = FauxFactory.generate_string("alpha", 4)
        os_attrs = entities.OperatingSystem(name=os_name).create()
        entities.ConfigTemplate(
            name=template_name,
            operatingsystem=[os_attrs['id']]
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            self.operatingsys.update(os_name, template=template_name)
            result_obj = self.operatingsys.get_os_entities(os_name, "template")
            self.assertEqual(template_name, result_obj['template'])

    def test_positive_set_os_parameter_1(self):
        """@Test: Set OS parameter

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """

        param_name = FauxFactory.generate_string("alpha", 4)
        param_value = FauxFactory.generate_string("alpha", 3)
        os_name = entities.OperatingSystem().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            try:
                self.operatingsys.set_os_parameter(os_name, param_name,
                                                   param_value)
            except Exception as e:
                self.fail(e)

    def test_positive_set_os_parameter_2(self):
        """@Test: Set OS parameter with blank value

        @Feature: OS - Positive update

        @Assert: Parameter is created with blank value

        """

        param_name = FauxFactory.generate_string("alpha", 4)
        param_value = ""
        os_name = entities.OperatingSystem().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            try:
                self.operatingsys.set_os_parameter(os_name, param_name,
                                                   param_value)
            except Exception as e:
                self.fail(e)

    def test_remove_os_parameter(self):
        """@Test: Remove selected OS parameter

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """

        param_name = FauxFactory.generate_string("alpha", 4)
        param_value = FauxFactory.generate_string("alpha", 3)
        os_name = entities.OperatingSystem().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            try:
                self.operatingsys.set_os_parameter(os_name, param_name,
                                                   param_value)
                self.operatingsys.remove_os_parameter(os_name, param_name)
            except Exception as e:
                self.fail(e)

    def test_negative_set_os_parameter_1(self):
        """@Test: Set same OS parameter again as it was set earlier

        @Feature: OS - Negative Update

        @Assert: Proper error should be raised, Name already taken

        @BZ: 1120663

        """

        param_name = FauxFactory.generate_string("alpha", 4)
        param_value = FauxFactory.generate_string("alpha", 3)
        os_name = entities.OperatingSystem().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            try:
                self.operatingsys.set_os_parameter(os_name, param_name,
                                                   param_value)
                self.operatingsys.set_os_parameter(os_name, param_name,
                                                   param_value)
            except Exception as e:
                self.fail(e)
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["common_param_error"]))

    def test_negative_set_os_parameter_2(self):
        """@Test: Set OS parameter with blank name and value

        @Feature: OS - Negative Update

        @Assert: Proper error should be raised, Name can't contain whitespaces

        @BZ: 1120663

        """

        param_name = " "
        param_value = " "
        os_name = entities.OperatingSystem().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            try:
                self.operatingsys.set_os_parameter(os_name, param_name,
                                                   param_value)
            except Exception as e:
                self.fail(e)
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["common_param_error"]))

    def test_negative_set_os_parameter_3(self):
        """@Test: Set OS parameter with name and value exceeding 255 characters

        @Feature: OS - Negative Update

        @Assert: Proper error should be raised, Name should contain a value

        """

        param_name = FauxFactory.generate_string("alpha", 256)
        param_value = FauxFactory.generate_string("alpha", 256)
        os_name = entities.OperatingSystem().create()['name']
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            try:
                self.operatingsys.set_os_parameter(os_name, param_name,
                                                   param_value)
            except Exception as e:
                self.fail(e)
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators["common_param_error"]))
