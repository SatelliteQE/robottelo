# -*- encoding: utf-8 -*-
"""Test class for Operating System UI"""

from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import (
    INSTALL_MEDIUM_URL, PARTITION_SCRIPT_DATA_FILE)
from robottelo.decorators import data, run_only_on, skip_if_bug_open
from robottelo.helpers import (
    get_data_file, invalid_names_list, valid_data_list)
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_os
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class OperatingSys(UITestCase):
    """Implements Operating system tests from UI"""

    @classmethod
    def setUpClass(cls):  # noqa
        cls.organization = entities.Organization().create()
        super(OperatingSys, cls).setUpClass()

    @data(*valid_data_list())
    def test_create_os_with_different_names(self, name):
        """@Test: Create a new OS using different string types as a name

        @Feature: OS - Positive Create

        @Assert: OS is created

        """
        with Session(self.browser) as session:
            make_os(
                session,
                name=name,
                major_version=gen_string('numeric', 1),
                minor_version=gen_string('numeric', 1),
                os_family='Red Hat',
                archs=['x86_64'],
            )
            self.assertIsNotNone(self.operatingsys.search(name))

    @data({u'major_version': gen_string('numeric', 1),
           u'minor_version': gen_string('numeric', 1),
           u'desc': gen_string('alpha', 10),
           u'os_family': 'Red Hat'},
          {u'major_version': gen_string('numeric', 4),
           u'minor_version': gen_string('numeric', 4),
           u'desc': gen_string('html', 10),
           u'os_family': 'Gentoo'},
          {u'major_version': gen_string('numeric', 5),
           u'minor_version': gen_string('numeric', 16),
           u'desc': gen_string('utf8', 10),
           u'os_family': 'SUSE'},
          {u'major_version': gen_string('numeric', 5),
           u'minor_version': gen_string('numeric', 1),
           u'desc': gen_string('alphanumeric', 255),
           u'os_family': 'SUSE'})
    def test_create_os_with_random_params(self, test_data):
        """@Test: Create a new OS with different data values

        @Feature: OS - Positive Create

        @Assert: OS is created

        @BZ: 1120568

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_os(
                session,
                name=name,
                major_version=test_data['major_version'],
                minor_version=test_data['minor_version'],
                description=test_data['desc'],
                os_family=test_data['os_family'],
                archs=['i386'],
            )
            self.assertIsNotNone(self.operatingsys.search
                                 (test_data['desc'], search_key='description'))

    @data(*invalid_names_list())
    def test_negative_create_os_with_long_names(self, name):
        """@Test: OS - Create a new OS with too long string of different types
        as its name value

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        @BZ: 1120181

        """
        with Session(self.browser) as session:
            make_os(
                session,
                name=name,
                major_version=gen_string('numeric', 1),
                minor_version=gen_string('numeric', 1),
                os_family='Red Hat',
                archs=['x86_64']
            )
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators['name_haserror']))
            self.assertIsNone(self.operatingsys.search(name))

    def test_negative_create_os_with_blank_name(self):
        """@Test: OS - Create a new OS with blank name

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        """
        with Session(self.browser) as session:
            make_os(
                session,
                name='',
                major_version=gen_string('numeric', 1),
                minor_version=gen_string('numeric', 1),
                os_family='Red Hat',
                archs=['x86_64']
            )
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators['name_haserror']))

    def test_negative_create_os_with_long_desc(self):
        """@Test: OS - Create a new OS with description containing
        256 characters

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_os(
                session,
                name=gen_string('alpha', 6),
                major_version=gen_string('numeric', 1),
                minor_version=gen_string('numeric', 1),
                description=gen_string('alphanumeric', 256),
                os_family='Red Hat',
                archs=['x86_64']
            )
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.operatingsys.search(name))

    @data(gen_string('numeric', 6), '', '-6')
    def test_negative_create_os_with_wrong_major_version(self, major_version):
        """@Test: OS - Create a new OS with incorrect major version value(More than 5
        characters, empty value, negative number)

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_os(
                session,
                name=name,
                major_version=major_version,
                minor_version=gen_string('numeric', 1),
                os_family='Red Hat',
                archs=['x86_64']
            )
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.operatingsys.search(name))

    @data(gen_string('numeric', 17), '-5')
    def test_negative_create_os_with_wrong_minor_version(self, minor_version):
        """@Test: OS - Create a new OS with incorrect minor version value(More than 16
        characters and negative number)

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_os(
                session,
                name=name,
                major_version=gen_string('numeric', 1),
                minor_version=minor_version,
                os_family='Red Hat',
                archs=['x86_64']
            )
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.operatingsys.search(name))

    @skip_if_bug_open('bugzilla', 1120985)
    def test_negative_create_os_with_same_name_and_version(self):
        """@Test: OS - Create a new OS with same name and version

        @Feature: Create a new OS - Negative

        @Assert: OS is not created

        @BZ: 1120985

        """
        name = gen_string('alpha')
        major_version = gen_string('numeric', 1)
        minor_version = gen_string('numeric', 1)
        with Session(self.browser) as session:
            make_os(
                session,
                name=name,
                major_version=major_version,
                minor_version=minor_version,
                os_family='Red Hat',
                archs=['x86_64']
            )
            self.assertIsNotNone(self.operatingsys.search(name))
            make_os(
                session,
                name=name,
                major_version=major_version,
                minor_version=minor_version,
                os_family='Red Hat',
                archs=['x86_64']
            )
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators['haserror']))

    def test_remove_os(self):
        """@Test: Delete an existing OS

        @Feature: OS - Positive Delete

        @Assert: OS is deleted

        """
        os_name = entities.OperatingSystem().create().name
        with Session(self.browser) as session:
            session.nav.go_to_operating_systems()
            self.operatingsys.delete(os_name)
            self.assertIsNone(self.operatingsys.search(os_name))

    @data(
        {u'new_name': gen_string('alpha', 10),
         u'new_major_version': gen_string('numeric', 1),
         u'new_minor_version': gen_string('numeric', 1),
         u'new_os_family': 'Red Hat'},
        {u'new_name': gen_string('html', 10),
         u'new_major_version': gen_string('numeric', 4),
         u'new_minor_version': gen_string('numeric', 4),
         u'new_os_family': 'Gentoo'},
        {u'new_name': gen_string('utf8', 10),
         u'new_major_version': gen_string('numeric', 5),
         u'new_minor_version': gen_string('numeric', 16),
         u'new_os_family': 'SUSE'},
        {u'new_name': gen_string('alphanumeric', 255),
         u'new_major_version': gen_string('numeric', 5),
         u'new_minor_version': gen_string('numeric', 1),
         u'new_os_family': 'SUSE'}
    )
    def test_update_os_basic_params(self, test_data):
        """@Test: Update OS name, major_version, minor_version, os_family
        and arch

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """
        with Session(self.browser):
            self.operatingsys.update(
                entities.OperatingSystem().create().name,
                test_data['new_name'],
                test_data['new_major_version'],
                test_data['new_minor_version'],
                os_family=test_data['new_os_family'],
                new_archs=[entities.Architecture().create().name]
            )
            self.assertIsNotNone(self.operatingsys.search(
                test_data['new_name']))

    def test_update_os_medium(self):
        """@Test: Update OS medium

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """
        medium_name = gen_string('alpha')
        entities.Media(
            name=medium_name,
            path_=INSTALL_MEDIUM_URL % medium_name,
            organization=[self.organization],
        ).create()
        os_name = entities.OperatingSystem().create().name
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.operatingsys.update(os_name, new_mediums=[medium_name])
            result_obj = self.operatingsys.get_os_entities(os_name, 'medium')
            self.assertEqual(medium_name, result_obj['medium'])

    def test_update_os_partition_table(self):
        """@Test: Update OS partition table

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """

        ptable = gen_string('alpha', 4)
        script_file = get_data_file(PARTITION_SCRIPT_DATA_FILE)
        with open(script_file, 'r') as file_contents:
            layout = file_contents.read()
        entities.PartitionTable(
            name=ptable,
            layout=layout,
        ).create()
        os_name = entities.OperatingSystem().create().name
        with Session(self.browser):
            self.operatingsys.update(os_name, new_ptables=[ptable])
            result_obj = self.operatingsys.get_os_entities(os_name, 'ptable')
            self.assertEqual(ptable, result_obj['ptable'])

    def test_update_os_template(self):
        """@Test: Update provisioning template

        @Feature: OS - Positive Update

        @Assert: OS is updated

        @BZ: 1129612

        """
        os_name = gen_string('alpha')
        template_name = gen_string('alpha')
        entities.ConfigTemplate(
            name=template_name,
            snippet=False,
            operatingsystem=[entities.OperatingSystem(name=os_name).create()],
            organization=[self.organization],
        ).create()
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.operatingsys.update(os_name, template=template_name)
            result_obj = self.operatingsys.get_os_entities(os_name, 'template')
            self.assertEqual(template_name, result_obj['template'])

    def test_positive_set_os_parameter(self):
        """@Test: Set OS parameter

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """
        with Session(self.browser):
            try:
                self.operatingsys.set_os_parameter(
                    entities.OperatingSystem().create().name,
                    gen_string('alpha', 4),
                    gen_string('alpha', 3),
                )
            except UIError as err:
                self.fail(err)

    def test_positive_set_os_parameter_with_blank_value(self):
        """@Test: Set OS parameter with blank value

        @Feature: OS - Positive update

        @Assert: Parameter is created with blank value

        """
        with Session(self.browser):
            try:
                self.operatingsys.set_os_parameter(
                    entities.OperatingSystem().create().name,
                    gen_string('alpha', 4),
                    '',
                )
            except UIError as err:
                self.fail(err)

    def test_remove_os_parameter(self):
        """@Test: Remove selected OS parameter

        @Feature: OS - Positive Update

        @Assert: OS is updated

        """
        param_name = gen_string('alpha', 4)
        os_name = entities.OperatingSystem().create().name
        with Session(self.browser):
            try:
                self.operatingsys.set_os_parameter(
                    os_name, param_name, gen_string('alpha', 3))
                self.operatingsys.remove_os_parameter(os_name, param_name)
            except UIError as err:
                self.fail(err)

    def test_negative_set_os_parameter_same_values(self):
        """@Test: Set same OS parameter again as it was set earlier

        @Feature: OS - Negative Update

        @Assert: Proper error should be raised, Name already taken

        """
        param_name = gen_string('alpha', 4)
        param_value = gen_string('alpha', 3)
        os_name = entities.OperatingSystem().create().name
        with Session(self.browser):
            try:
                for _ in range(2):
                    self.operatingsys.set_os_parameter(
                        os_name, param_name, param_value)
            except UIError as err:
                self.fail(err)
            self.assertIsNotNone(self.operatingsys.wait_until_element(
                common_locators['common_param_error']
            ))

    def test_negative_set_os_parameter_with_blank_value(self):
        """@Test: Set OS parameter with blank name and value

        @Feature: OS - Negative Update

        @Assert: Proper error should be raised, Name can't contain whitespaces

        """
        with Session(self.browser):
            try:
                self.operatingsys.set_os_parameter(
                    entities.OperatingSystem().create().name, '', '')
            except UIError as err:
                self.fail(err)
            self.assertIsNotNone(self.operatingsys.wait_until_element(
                common_locators['common_param_error']
            ))

    @data(*invalid_names_list())
    def test_negative_set_os_parameter_with_long_values(self, param):
        """@Test: Set OS parameter with name and value exceeding 255 characters

        @Feature: OS - Negative Update

        @Assert: Proper error should be raised, Name should contain a value

        """
        with Session(self.browser):
            try:
                self.operatingsys.set_os_parameter(
                    entities.OperatingSystem().create().name, param, param)
            except UIError as err:
                self.fail(err)
            self.assertIsNotNone(self.operatingsys.wait_until_element(
                common_locators['common_param_error']
            ))
