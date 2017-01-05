# -*- encoding: utf-8 -*-
"""Test class for Operating System UI

@Requirement: Operatingsystem

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.constants import (
    INSTALL_MEDIUM_URL, PARTITION_SCRIPT_DATA_FILE)
from robottelo.datafactory import (
    filtered_datapoint,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import run_only_on, tier1, tier2
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_os
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_os_parameters():
    """Returns a list of valid os parameters"""
    return [
        {u'name': gen_string('alpha', 10),
         u'major_version': gen_string('numeric', 1),
         u'minor_version': gen_string('numeric', 1),
         u'desc': gen_string('alpha', 10),
         u'os_family': 'Red Hat'},
        {u'name': gen_string('html', 10),
         u'major_version': gen_string('numeric', 4),
         u'minor_version': gen_string('numeric', 4),
         u'desc': gen_string('html', 10),
         u'os_family': 'Gentoo'},
        {u'name': gen_string('utf8', 10),
         u'major_version': gen_string('numeric', 5),
         u'minor_version': gen_string('numeric', 16),
         u'desc': gen_string('utf8', 10),
         u'os_family': 'SUSE'},
        {u'name': gen_string('alphanumeric', 255),
         u'major_version': gen_string('numeric', 5),
         u'minor_version': gen_string('numeric', 1),
         u'desc': gen_string('alphanumeric', 255),
         u'os_family': 'SUSE'}
    ]


class OperatingSystemTestCase(UITestCase):
    """Implements Operating system tests from UI"""

    @classmethod
    def setUpClass(cls):
        super(OperatingSystemTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create a new OS using different string types as a name

        @id: 08cb212e-586f-4630-af1b-ad3e749e82e7

        @Assert: OS is created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_os(
                        session,
                        name=name,
                        major_version=gen_string('numeric', 1),
                        minor_version=gen_string('numeric', 1),
                        os_family='Red Hat',
                        archs=['x86_64'],
                    )
                    self.assertIsNotNone(self.operatingsys.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_create(self):
        """Create a new OS with different data values

        @id: fcb41aff-c963-403b-a80f-5f9c467d0632

        @Assert: OS is created
        """
        with Session(self.browser) as session:
            for test_data in valid_os_parameters():
                with self.subTest(test_data):
                    make_os(
                        session,
                        name=test_data['name'],
                        major_version=test_data['major_version'],
                        minor_version=test_data['minor_version'],
                        description=test_data['desc'],
                        os_family=test_data['os_family'],
                        archs=['i386'],
                    )
                    self.operatingsys.search_key = 'description'
                    self.assertIsNotNone(self.operatingsys.search(
                        test_data['desc']))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """OS - Create a new OS with invalid name

        @id: aa035ef6-a503-48c4-b95a-021a03a145c0

        @Assert: OS is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_os(
                        session,
                        name=name,
                        major_version=gen_string('numeric', 1),
                        minor_version=gen_string('numeric', 1),
                        os_family='Red Hat',
                        archs=['x86_64'],
                    )
                    self.assertIsNotNone(self.operatingsys.wait_until_element(
                        common_locators['name_haserror']))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_too_long_description(self):
        """OS - Create a new OS with description containing
        256 characters

        @id: 7f395b9a-2d48-468a-937b-bba4e6576ba9

        @Assert: OS is not created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_os(
                session,
                name=gen_string('alpha'),
                major_version=gen_string('numeric', 1),
                minor_version=gen_string('numeric', 1),
                description=gen_string('alphanumeric', 256),
                os_family='Red Hat',
                archs=['x86_64']
            )
            self.assertIsNotNone(self.operatingsys.wait_until_element
                                 (common_locators['haserror']))
            self.assertIsNone(self.operatingsys.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_major_version(self):
        """OS - Create a new OS with incorrect major version value
        (More than 5 characters, empty value, negative number)

        @id: 89d061a8-cb4c-4460-a7fb-7cea73c323af

        @Assert: OS is not created
        """
        with Session(self.browser) as session:
            for major_version in gen_string('numeric', 6), '', '-6':
                with self.subTest(major_version):
                    name = gen_string('alpha')
                    make_os(
                        session,
                        name=name,
                        major_version=major_version,
                        minor_version=gen_string('numeric', 1),
                        os_family='Red Hat',
                        archs=['x86_64'],
                    )
                    self.assertIsNotNone(self.operatingsys.wait_until_element(
                        common_locators['haserror']))
                    self.assertIsNone(self.operatingsys.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_minor_version(self):
        """OS - Create a new OS with incorrect minor version value
        (More than 16 characters and negative number)

        @id: 2828cd68-d57a-4e3e-bced-90937290251e

        @Assert: OS is not created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            for minor_version in gen_string('numeric', 17), '-5':
                with self.subTest(minor_version):
                    make_os(
                        session,
                        name=name,
                        major_version=gen_string('numeric', 1),
                        minor_version=minor_version,
                        os_family='Red Hat',
                        archs=['x86_64'],
                    )
                    self.assertIsNotNone(self.operatingsys.wait_until_element(
                        common_locators['haserror']))
                    self.assertIsNone(self.operatingsys.search(name))

    @run_only_on('sat')
    @tier2
    def test_negative_create_with_same_name_and_version(self):
        """OS - Create a new OS with same name and version

        @id: f1865efe-bdc0-4065-90b8-b48c9fad80bb

        @Assert: OS is not created

        @CaseLevel: Integration
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
            self.assertIsNotNone(self.operatingsys.wait_until_element(
                common_locators['haserror']))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete an existing OS

        @id: 252f1512-78a6-415d-a4fd-5f6d268cbb82

        @Assert: OS is deleted successfully
        """
        os_name = entities.OperatingSystem().create().name
        with Session(self.browser):
            self.operatingsys.delete(os_name)

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Update OS name, major_version, minor_version, os_family
        and arch

        @id: d86aeac2-c2b6-4766-96a8-c2e427a9c8be

        @Assert: OS is updated
        """
        os_name = entities.OperatingSystem().create().name
        with Session(self.browser):
            for test_data in valid_os_parameters():
                with self.subTest(test_data):
                    self.operatingsys.update(
                        os_name,
                        test_data['name'],
                        test_data['major_version'],
                        test_data['minor_version'],
                        os_family=test_data['os_family'],
                        new_archs=[entities.Architecture().create().name],
                    )
                    self.assertIsNotNone(self.operatingsys.search(
                        test_data['name']))
                    os_name = test_data['name']

    @run_only_on('sat')
    @tier1
    def test_positive_update_medium(self):
        """Update OS medium

        @id: 4fbcd341-5aff-465c-b251-7ecd97471e01

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

    @run_only_on('sat')
    @tier1
    def test_positive_update_ptable(self):
        """Update OS partition table

        @id: 08ddbc40-dcc1-4695-b209-ba72a6a458df

        @Assert: OS is updated
        """
        ptable = gen_string('alpha', 4)
        script_file = get_data_file(PARTITION_SCRIPT_DATA_FILE)
        with open(script_file, 'r') as file_contents:
            layout = file_contents.read()
        entities.PartitionTable(
            name=ptable,
            layout=layout,
            organization=[self.organization],
        ).create()
        os_name = entities.OperatingSystem().create().name
        with Session(self.browser) as session:
            session.nav.go_to_select_org(self.organization.name)
            self.operatingsys.update(os_name, new_ptables=[ptable])
            result_obj = self.operatingsys.get_os_entities(os_name, 'ptable')
            self.assertEqual(ptable, result_obj['ptable'])

    @run_only_on('sat')
    @tier1
    def test_positive_update_template(self):
        """Update provisioning template

        @id: df21419a-1fdd-414c-86fc-64cde10d3e05

        @Assert: OS is updated
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

    @run_only_on('sat')
    @tier2
    def test_positive_set_parameter(self):
        """Set Operating System parameter

        @id: 05b504d8-2518-4359-a53a-f577339f1ebe

        @Assert: OS is updated with new parameter

        @CaseLevel: Integration
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

    @run_only_on('sat')
    @tier2
    def test_positive_set_parameter_with_blank_value(self):
        """Set OS parameter with blank value

        @id: 38ef9293-0f83-4c9d-8314-0c72fdf7e2a6

        @Assert: Parameter is created with blank value

        @CaseLevel: Integration
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

    @run_only_on('sat')
    @tier2
    def test_positive_remove_parameter(self):
        """Remove selected OS parameter

        @id: 14aa3459-9941-43ba-8c17-d7f32e9db43b

        @Assert: Expected OS parameter is removed

        @CaseLevel: Integration
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

    @run_only_on('sat')
    @tier2
    def test_negative_set_parameter_same_values(self):
        """Set same OS parameter again as it was set earlier

        @id: 4211c9c6-d61f-4254-ac45-6791f7577142

        @Assert: Proper error should be raised - Name is already taken

        @CaseLevel: Integration
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

    @run_only_on('sat')
    @tier2
    def test_negative_set_parameter_with_blank_name_and_value(self):
        """Set OS parameter with blank name and value

        @id: 635c354f-3360-403c-9bcb-78f2da9ed893

        @Assert: Proper error should be raised - Name can't contain whitespaces

        @CaseLevel: Integration
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

    @run_only_on('sat')
    @tier2
    def test_negative_set_parameter_with_too_long_values(self):
        """Set OS parameter with name and value exceeding 255 characters

        @id: e961ce00-f86b-476e-afad-468491cb2a12

        @Assert: Proper error should be raised, Name should contain a value

        @CaseLevel: Integration
        """
        os_name = entities.OperatingSystem().create().name
        with Session(self.browser):
            for param in invalid_values_list(interface='ui'):
                with self.subTest(param):
                    try:
                        self.operatingsys.set_os_parameter(
                            os_name, param, param)
                    except UIError as err:
                        self.fail(err)
                    self.assertIsNotNone(self.operatingsys.wait_until_element(
                        common_locators['common_param_error']))
