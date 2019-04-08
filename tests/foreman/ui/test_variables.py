# -*- encoding: utf-8 -*-
"""Test class for Puppet Smart Variables

:Requirement: Variables

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

import yaml
from random import choice, uniform

from fauxfactory import gen_string
from nailgun import entities

from robottelo.api.utils import publish_puppet_module
from robottelo.constants import CUSTOM_PUPPET_REPO, ENVIRONMENT
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_names_list,
    valid_data_list,
)
from robottelo.decorators import (
    run_in_one_thread_if_bug_open,
    run_only_on,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_smart_variable
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_sc_variable_data():
    """Returns a list of valid smart class variable types and values"""
    return [
        {
            u'sc_type': 'string',
            u'value': choice(generate_strings_list()),
        },
        {
            u'sc_type': 'boolean',
            u'value': choice(['true', 'false']),
        },
        {
            u'sc_type': 'integer',
            u'value': gen_string('numeric', 5).lstrip('0'),
        },
        {
            u'sc_type': 'real',
            u'value': str(uniform(-1000, 1000)),
        },
        {
            u'sc_type': 'array',
            u'value': u'["{0}","{1}","{2}"]'.format(
                gen_string('alpha'),
                gen_string('numeric').lstrip('0'),
                gen_string('html'),
            ),
        },
        {
            u'sc_type': 'hash',
            u'value': '{0}: {1}'.format(
                gen_string('alpha'), gen_string('alpha')),
        },
        {
            u'sc_type': 'yaml',
            u'value': '--- {0}=>{1}'.format(
                gen_string('alpha'), gen_string('alpha')),
        },
        {
            u'sc_type': 'json',
            u'value': u'{{"{0}":"{1}","{2}":"{3}"}}'.format(
                gen_string('alpha'),
                gen_string('numeric').lstrip('0'),
                gen_string('alpha'),
                gen_string('alphanumeric')
            ),
        },
    ]


@filtered_datapoint
def invalid_sc_variable_data():
    """Returns a list of invalid smart class variable type and values"""
    return [
        {
            u'sc_type': 'boolean',
            u'value': gen_string('alphanumeric'),
        },
        {
            u'sc_type': 'integer',
            u'value': gen_string('utf8'),
        },
        {
            u'sc_type': 'real',
            u'value': gen_string('alphanumeric'),
        },
        {
            u'sc_type': 'array',
            u'value': gen_string('alpha'),
        },
        {
            u'sc_type': 'hash',
            u'value': gen_string('alpha'),
        },
        {
            u'sc_type': 'yaml',
            u'value': '{{{0}:{1}}}'.format(
                gen_string('alpha'), gen_string('alpha')),
        },
        {
            u'sc_type': 'json',
            u'value': u'{{{0}:{1},{2}:{3}}}'.format(
                gen_string('alpha'),
                gen_string('numeric').lstrip('0'),
                gen_string('alpha'),
                gen_string('alphanumeric')
            ),
        }
    ]


class SmartVariablesTestCase(UITestCase):
    """Implements Smart Variables tests in UI"""

    @classmethod
    def set_session_org(cls):
        """Creates new organization to be used for current session the
        session_user will login automatically with this org in context
        """
        cls.session_org = entities.Organization().create()

    @classmethod
    def setUpClass(cls):
        """Import some parametrized puppet classes. This is required to make
        sure that we have data to be able to perform interactions with smart
        class variables.
        """
        super(SmartVariablesTestCase, cls).setUpClass()
        cls.puppet_modules = [
            {'author': 'robottelo', 'name': 'ui_test_variables'},
        ]
        cv = publish_puppet_module(
           cls.puppet_modules, CUSTOM_PUPPET_REPO, cls.session_org)
        cls.env = entities.Environment().search(
           query={'search': u'content_view="{0}"'.format(cv.name)}
        )[0]
        # Find imported puppet class
        cls.puppet_class = entities.PuppetClass().search(query={
           'search': u'name = "{0}" and environment = "{1}"'.format(
               cls.puppet_modules[0]['name'], cls.env.name)
        })[0]
        # And all its subclasses
        cls.puppet_subclasses = entities.PuppetClass().search(query={
            'search': u'name ~ "{0}::" and environment = "{1}"'.format(
                cls.puppet_modules[0]['name'], cls.env.name)
        })

        lce = entities.LifecycleEnvironment().search(
            query={
                'search': 'organization_id="{0}" and name="{1}"'
                .format(cls.session_org.id, ENVIRONMENT)
            }
        )[0]
        cls.host = entities.Host(
            organization=cls.session_org,
            content_facet_attributes={
                'content_view_id': cv.id,
                'lifecycle_environment_id': lce.id,
            }
        ).create()
        cls.host.environment = cls.env
        cls.host.update(['environment'])
        cls.host.add_puppetclass(data={'puppetclass_id': cls.puppet_class.id})
        cls.domain_name = entities.Domain(id=cls.host.domain.id).read().name

    # TearDown brakes parallel tests run as every test depends on the same
    # puppet class that will be removed during TearDown.
    # Uncomment for developing or debugging and do not forget to import
    # `robottelo.api.utils.delete_puppet_class`.
    #
    # @classmethod
    # def tearDownClass(cls):
    #     """Removes puppet class."""
    #     super(SmartVariablesTestCase, cls).tearDownClass()
    #     delete_puppet_class(cls.puppet_class.name)

    @tier1
    def test_positive_create(self):
        """Creates a Smart Variable using different names.

        :id: a729c1b4-7a85-45d3-858d-614234d82f92

        :steps: Creates a smart variable with valid name

        :expectedresults: The smart variable is created successfully.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_smart_variable(
                        session,
                        name=name,
                        puppet_class=self.puppet_class.name,
                    )
                    self.assertIsNotNone(self.smart_variable.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create(self):
        """Smart Variable is not created with invalid data.

        :id: 09a67cb6-5de0-41b3-90f4-593323936c6c

        :steps: Creates a smart variable with invalid name and valid default
            value.

        :expectedresults:

            1. Error is displayed for invalid variable name.
            2. The smart Variable is not created.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_names_list():
                with self.subTest(name):
                    make_smart_variable(
                        session,
                        name=name,
                        puppet_class=self.puppet_class.name,
                        default_value=gen_string('alpha')
                    )
                    self.assertIsNotNone(
                        self.smart_variable.wait_until_element(
                            common_locators['haserror'])
                    )
                    self.assertIsNone(self.smart_variable.search(name))

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_delete(self):
        """Deletes a Smart Variable from Smart Variables Menu.

        :id: 19fedbdf-48a1-46a7-b184-615a0efd7b4e

        :steps: Deletes a smart Variable from Configure - Smart Variables menu.

        :expectedresults:

            1. The smart Variable is deleted successfully.
            2. In YAML output of associated Host, the variable should be
               removed.
            3. In Host-> variables tab, the smart variable should be removed.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        value = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value=value,
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            self.smart_variable.delete(name)
            # Verify that corresponding entry is not present in YAML output
            output = yaml.load(self.hosts.get_yaml_output(self.host.name))
            self.assertNotIn(name, output['parameters'])
            # Verify that smart variable is not present on Host page
            sv_value = self.hosts.get_smart_variable_value(
                self.host.name, name)
            self.assertIsNone(sv_value)

    @run_only_on('sat')
    @run_in_one_thread_if_bug_open('bugzilla', 1440878)
    @tier1
    def test_positive_update_name(self):
        """Update Smart Variable name.

        :id: 2083cfb7-eed6-4086-8f6a-86d6cd08bd06

        :steps:

            1. In Puppet Class, create a smart variable with valid name
            2. After successful creation, update the name of variable.

        :expectedresults: The variable is updated with new name.

        :CaseImportance: Critical
        """
        old_name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=old_name,
                puppet_class=self.puppet_class.name,
            )
            self.assertIsNotNone(self.smart_variable.search(old_name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.smart_variable.update(old_name, new_name=new_name)
                    self.assertIsNotNone(self.smart_variable.search(new_name))
                    old_name = new_name  # for next iteration

    @run_only_on('sat')
    @run_in_one_thread_if_bug_open('bugzilla', 1440878)
    @tier1
    def test_positive_update_variable_puppet_class(self):
        """Update Smart Variable puppet class.

        :id: 6c3e2da9-420c-4e39-8b71-e5be6b605bd7

        :steps:

            1. In Puppet Class, creates a smart variable with valid name and
               default value.
            2. After successful creation, update the puppet class of variable.

        :expectedresults: The variable is updated with new puppet class.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            new_puppet_class = choice(self.puppet_subclasses).name
            self.smart_variable.update(name, puppet_class=new_puppet_class)
            self.assertTrue(self.smart_variable.validate_smart_variable(
                name, 'puppet_class', new_puppet_class))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Attempt to create Smart Variable with same name as already existent
        entity

        :id: 7f37194d-4a12-437b-a284-3350cf048eea

        :steps:

            1. In Puppet Class, create a smart Variable with valid name and
               default value.
            2. After successful creation, attempt to create a variable with
               same name from same/other class.

        :expectedresults:

            1. An error is displayed in front of Variable Key field as 'has
               already been taken'.
            2. The variable with same name are not allowed to create from any
               class

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            for _ in range(2):
                make_smart_variable(
                    session,
                    name=name,
                    puppet_class=self.puppet_class.name,
                )
            self.assertIsNotNone(
                self.smart_variable.wait_until_element(
                    common_locators['haserror'])
            )

    @run_only_on('sat')
    @run_in_one_thread_if_bug_open('bugzilla', 1440878)
    @tier1
    @upgrade
    def test_positive_update_type(self):
        """Update Smart Variable with valid default value for all variable
        types

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: d89cdd32-dd2b-46fe-bcc2-8c66d92cc6f8

        :steps:

            1.  Update the Key Type.
            2.  Enter a 'valid' default Value.
            3.  Submit the changes.

        :expectedresults: Variable is updated with a new type and value
            successfully.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                default_value=gen_string('alpha'),
                puppet_class=self.puppet_class.name,
            )
            for data in valid_sc_variable_data():
                with self.subTest(data):
                    self.smart_variable.update(
                        name,
                        key_type=data['sc_type'],
                        default_value=data['value'],
                    )
                    self.smart_variable.click(self.smart_variable.search(name))
                    value = self.smart_variable.wait_until_element(
                        locators['smart_variable.default_value']).text
                    # Application is adding some data for yaml type once
                    # variable is created
                    if data['sc_type'] == 'yaml':
                        data['value'] += '\n...'
                    self.assertEqual(value, data['value'])

    @run_only_on('sat')
    @run_in_one_thread_if_bug_open('bugzilla', 1440878)
    @tier1
    def test_negative_update_type(self):
        """Attempt to update Smart Variable with invalid default value for all
        variable types

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: d64d1b6d-028a-4782-a6d4-e3029d7118b6

        :steps:

            1.  Update the Key Type.
            2.  Enter an 'Invalid' default Value.
            3.  Submit the changes.

        :expectedresults: Variable is not updated with new type and invalid
            default value.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        initial_value = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                default_value=initial_value,
                puppet_class=self.puppet_class.name,
            )
            for data in invalid_sc_variable_data():
                with self.subTest(data):
                    self.smart_variable.update(
                        name,
                        key_type=data['sc_type'],
                        default_value=data['value'],
                    )
                    self.assertIsNotNone(
                        self.smart_variable.wait_until_element(
                            common_locators['haserror'])
                    )
                    self.smart_variable.click(self.smart_variable.search(name))
                    value = self.smart_variable.wait_until_element(
                        locators['smart_variable.default_value']).text
                    self.assertEqual(value, initial_value)

    @run_only_on('sat')
    @tier1
    def test_negative_validate_default_value_with_regex(self):
        """Attempt to create Smart Variable that has default value that doesn't
        match regexp from validator rule

        :id: 5285b784-e02c-4f3b-a053-93b36bf9fbfc

        :steps:

            1.  Provide regexp to validator rule
            2.  Provide default value that doesn't match the regex from
                validator rule
            3.  Submit the change.

        :expectedresults: Error is raised for default value not matching with
            regex.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_smart_variable(
                session,
                puppet_class=self.puppet_class.name,
                default_value=gen_string('alpha'),
                validator_type='regexp',
                validator_rule='[0-9]',
            )
            self.assertIsNotNone(
                self.smart_variable.wait_until_element(
                    common_locators['haserror'])
            )

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_validate_default_value_with_regex(self):
        """Create Smart Variable that has default value that match regexp from
        validator rule

        :id: 7a329b05-7efd-42d2-b472-1a36d0ee6464

        :steps:

            1.  Provide regexp to validator rule
            2.  Provide default value that matches the regexp from validator
                rule
            3.  Submit the change.

        :expectedresults: Smart Variable is created successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value=gen_string('numeric'),
                validator_type='regexp',
                validator_rule='[0-9]',
            )
            self.assertIsNotNone(self.smart_variable.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_value_with_regex(self):
        """Attempt to create Smart Variable that has matcher value that doesn't
        match regexp from validator rule

        :id: b8e039b3-2491-4dba-a91b-a4aa3fc7f544

        :steps:

            1.  Provide regexp to validator rule
            2.  Create a matcher with value that doesn't match the regexp from
                validator rule
            3.  Submit the change.

        :expectedresults: Error is raised for matcher value not matching with
            regex.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_smart_variable(
                session,
                name=gen_string('alpha'),
                puppet_class=self.puppet_class.name,
                default_value=gen_string('numeric'),
                validator_type='regexp',
                validator_rule='[0-9]',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': gen_string('alpha')
                }]
            )
            self.assertIsNotNone(
                self.smart_variable.wait_until_element(
                    locators['smart_variable.matcher_error'])
            )

    @run_only_on('sat')
    @tier1
    def test_positive_validate_matcher_value_with_regex(self):
        """Create Smart Variable that has matcher value that match regexp from
        validator rule

        :id: 04a8f849-6323-4e54-9f07-fb750b911a4c

        :steps:

            1.  Provide regexp to validator rule
            2.  Create a matcher with value that matches the regex from
                validator rule
            3.  Submit the change.

        :expectedresults: Smart Variable is created successfully and error is
            not raised for matcher value matching with regex.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value=gen_string('numeric'),
                validator_type='regexp',
                validator_rule='[0-9]',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': gen_string('numeric')
                }]
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            self.assertIsNone(
                self.smart_variable.wait_until_element(
                    locators['smart_variable.matcher_error'], timeout=8)
            )

    @run_only_on('sat')
    @tier1
    def test_negative_validate_default_value_with_list(self):
        """Attempt to create Smart Variable that has default value that is not
        in list from validator rule

        :id: d1aa9149-9025-4492-95d0-e72aec8eadc3

        :steps:

            1.  Provide list of values to validator rule
            2.  Provide default value that doesn't match list from validator
                rule
            3.  Submit the change.

        :expectedresults: Error is raised for default value which is not in the
            list from validator rule.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_smart_variable(
                session,
                puppet_class=self.puppet_class.name,
                default_value=gen_string('alphanumeric'),
                validator_type='list',
                validator_rule='45, test',
            )
            self.assertIsNotNone(
                self.smart_variable.wait_until_element(
                    common_locators['haserror'])
            )

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_validate_default_value_with_list(self):
        """Creates Smart Variable that has default value that is in the list
        from validator rule

        :id: 5ea443f2-ec91-4986-b97c-1c28fb862e1c

        :steps:

            1.  Provide list of values to validator rule
            2.  Provide default value that matches list from validator rule
            3.  Submit the change.

        :expectedresults: Smart Variable is created successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value='test1',
                validator_type='list',
                validator_rule='true, 50, test1',
            )
            self.assertIsNotNone(self.smart_variable.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_value_with_list(self):
        """Attempt to create Smart Variable that has matcher value that is not
        in list from validator rule

        :id: 87d128b9-c7f7-4396-b162-60021b0ef682

        :steps:

            1.  Provide list of values to validator rule
            2.  Create a matcher with value that is not in the list from
                validator rule
            3.  Submit the change.

        :expectedresults: Error is raised for matcher value that is not in list
            from validator rule.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_smart_variable(
                session,
                name=gen_string('alpha'),
                puppet_class=self.puppet_class.name,
                default_value='50',
                validator_type='list',
                validator_rule='25, example, 50',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': 'myexample'
                }]
            )
            self.assertIsNotNone(
                self.smart_variable.wait_until_element(
                    locators['smart_variable.matcher_error'])
            )

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_validate_matcher_value_with_list(self):
        """Create Smart Variable that has matcher value that is in the list
        from validator rule

        :id: ac91eaf5-2a15-4d54-b078-a37b60074287

        :steps:

            1.  Provide list of values to validator rule
            2.  Create a matcher with value that present in the list from
                validator rule
            3.  Submit the change.

        :expectedresults: Smart Variable is created successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value='example',
                validator_type='list',
                validator_rule='test, example, 30',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': '30'
                }]
            )
            self.assertIsNotNone(self.smart_variable.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_value_with_default_type(self):
        """Attempt to create Smart Variable that has matcher value of another
        type than key type

        :id: 466197ea-44f0-46d0-b111-686b72183fe5

        :steps:

            1.  Update smart variable with default type and value.
            2.  Create a matcher with value that doesn't match the default
                type.
            3.  Submit the change.

        :expectedresults: Error is raised for matcher value which is not of
            default type

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_smart_variable(
                session,
                name=gen_string('alpha'),
                puppet_class=self.puppet_class.name,
                default_value='true',
                key_type='boolean',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': gen_string('alpha')
                }]
            )
            self.assertIsNotNone(
                self.smart_variable.wait_until_element(
                    locators['smart_variable.matcher_error'])
            )

    @run_only_on('sat')
    @tier1
    def test_positive_validate_matcher_value_with_default_type(self):
        """Create Smart Variable that has matcher value of the same type than
        key type

        :id: 033bf7d8-a488-49c1-b900-9e7169e945e0

        :steps:

            1.  Update smart variable with default type and value.
            2.  Create a matcher with value that matches the default type.
            3.  Submit the change.

        :expectedresults: Smart Variable is created successfully

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value='true',
                key_type='boolean',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': 'false'
                }]
            )
            self.assertIsNotNone(self.smart_variable.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_and_default_value(self):
        """Attempt to create Smart Variable that has default value and matcher
        value of another type than key type

        :id: 9f5987d1-ac40-4031-bcfe-979dc95866d3

        :steps:

            1.  Update smart variable with default type and invalid default
                value.
            2.  Create a matcher with value that doesn't match the default
                type.
            3.  Submit the change.

        :expectedresults: Error is raised for invalid default and matcher value
            both.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_smart_variable(
                session,
                name=gen_string('alpha'),
                puppet_class=self.puppet_class.name,
                default_value=gen_string('alpha'),
                key_type='integer',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': gen_string('alpha')
                }]
            )
            self.assertIsNotNone(
                self.smart_variable.wait_until_element(
                    locators['smart_variable.matcher_error'])
            )
            self.assertIsNotNone(
                self.smart_variable.wait_until_element(
                    common_locators['haserror'])
            )

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Attempt to create Smart Variable with a matcher that has value for
        non existing attribute.

        :id: 27ef1ef0-1c89-47eb-89e0-3da161154513

        :steps:

            1.  Create a matcher with non existing attribute in org.
            2.  Attempt to submit the change.

        :expectedresults: Error is raised for non existing attribute.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_smart_variable(
                session,
                name=gen_string('alpha'),
                puppet_class=self.puppet_class.name,
                default_value=gen_string('alpha'),
                matcher=[{
                    'matcher_attribute': 'hostgroup={0}'.format(
                        gen_string('alpha')),
                    'matcher_value': gen_string('alpha')
                }]
            )
            self.assertIsNotNone(
                self.smart_variable.wait_until_element(
                    locators['smart_variable.matcher_error'])
            )

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_create_with_long_priority_list(self):
        """Smart variable priority order list can contain more than 255
        character inside of it

        :id: 440923cb-9d81-40c8-9d81-7bf22f503cf5

        :customerscenario: true

        :steps:
            1.  Create variable with some default value.
            2.  Set long priority order list

        :expectedresults: Smart variable is created successfully and has proper
            priority list

        :BZ: 1458817

        :CaseImportance: Medium
        """
        name = gen_string('alpha')
        order_value = '\n'.join(
            [gen_string('alpha').lower() for _ in range(60)])
        self.assertGreater(len(order_value), 255)
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value=gen_string('alpha'),
                matcher_priority=order_value,
            )
            self.smart_variable.search_and_click(name)
            priority_list_value = self.sc_parameters.wait_until_element(
                locators['smart_variable.matcher_priority']).text
            self.assertEqual(order_value, priority_list_value)

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_create_matcher_merge_override(self):
        """Merge the values of all the associated matchers.

        :id: b9c9b1c7-ff9a-4080-aeee-3b61b5414332

        :steps:

            1.  Create variable with some default value.
            2.  Create first matcher for attribute fqdn with valid details.
            3.  Create second matcher for other attribute with valid details.
                Note - The fqdn/host should have this attribute.
            4.  Create more matchers for some more attributes if any.
                Note - The fqdn/host should have this attributes.
            5.  Select 'Merge overrides' checkbox.
            6.  Submit the change.
            7.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the default value of variable.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        override_value = '[80, 90]'
        override_value2 = '[90, 100]'
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value='[20]',
                key_type='array',
                matcher_merge_overrides=True,
                matcher=[
                    {
                        'matcher_attribute': 'fqdn={0}'.format(self.host.name),
                        'matcher_value': override_value
                    },
                    {
                        'matcher_attribute': 'domain={0}'.format(
                            self.domain_name),
                        'matcher_value': override_value2
                    }

                ]
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            output = yaml.load(self.hosts.get_yaml_output(self.host.name))
            self.assertEqual(output['parameters'][name], [80, 90, 90, 100])

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_negative_create_matcher_merge_override(self):
        """Attempt to merge the values from non associated matchers.

        :id: 3cc2a7b3-7b46-4c8c-b719-79c004ae04c6

        :steps:

            1.  Create variable with some default value.
            2.  Create first matcher for attribute fqdn with valid details.
            3.  Create second matcher for other attribute with valid details.
                Note - The fqdn/host should not have this attribute.
            4.  Create more matchers for some more attributes if any.
                Note - The fqdn/host should not have this attributes.
            5.  Select 'Merge overrides' checkbox.
            6.  Submit the change.
            7.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values only for fqdn.
            2.  The YAML output doesn't have the values for attribute which are
                not associated to host.
            3.  The YAML output doesn't have the default value of variable.
            4.  Duplicate values in YAML output if any are displayed.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        override_value = '[80, 90]'
        override_value2 = '[90, 100]'
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value='[20]',
                key_type='array',
                matcher_merge_overrides=True,
                matcher=[
                    {
                        'matcher_attribute': 'fqdn={0}'.format(self.host.name),
                        'matcher_value': override_value
                    },
                    {
                        'matcher_attribute': 'os=rhel2',
                        'matcher_value': override_value2
                    }

                ]
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            output = yaml.load(self.hosts.get_yaml_output(self.host.name))
            self.assertEqual(output['parameters'][name], [80, 90])

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_create_matcher_merge_default(self):
        """Merge the values of all the associated matchers + default value.

        :id: 21d8fde8-0844-4384-b86a-30547c82b221

        :steps:

            1.  Create variable with some default value.
            2.  Create first matcher for attribute fqdn with valid details.
            3.  Create second matcher for other attribute with valid details.
                Note - The fqdn/host should have this attribute.
            4.  Create more matchers for some more attributes if any.
                Note - The fqdn/host should have this attributes.
            5.  Select 'Merge overrides' checkbox.
            6.  Select 'Merge default' checkbox.
            7.  Submit the change.
            8.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output has the default value of variable.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        override_value = '[80, 90]'
        override_value2 = '[90, 100]'
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value='[test]',
                key_type='array',
                matcher_merge_overrides=True,
                matcher_merge_default=True,
                matcher=[
                    {
                        'matcher_attribute': 'fqdn={0}'.format(self.host.name),
                        'matcher_value': override_value
                    },
                    {
                        'matcher_attribute': 'domain={0}'.format(
                            self.domain_name),
                        'matcher_value': override_value2
                    }

                ]
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            output = yaml.load(self.hosts.get_yaml_output(self.host.name))
            self.assertEqual(
                output['parameters'][name], ['test', 80, 90, 90, 100])

    @run_only_on('sat')
    @tier2
    def test_negative_create_matcher_merge_default(self):
        """Empty default value is not shown in merged values.

        :id: 98f8fe63-d125-4d27-a15a-2550c9e5f0ff

        :steps:

            1.  Create variable with empty default value.
            2.  Create first matcher for attribute fqdn with valid details.
            3.  Create second matcher for other attribute with valid details.
                Note - The fqdn/host should have this attribute.
            4.  Create more matchers for some more attributes if any.
                Note - The fqdn/host should have this attributes.
            5.  Select 'Merge overrides' checkbox.
            6.  Select 'Merge default' checkbox.
            7.  Submit the change.
            8.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the empty default value of
                variable.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        override_value = '[80, 90]'
        override_value2 = '[90, 100]'
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value='[]',
                key_type='array',
                matcher_merge_overrides=True,
                matcher_merge_default=True,
                matcher=[
                    {
                        'matcher_attribute': 'fqdn={0}'.format(self.host.name),
                        'matcher_value': override_value
                    },
                    {
                        'matcher_attribute': 'domain={0}'.format(
                            self.domain_name),
                        'matcher_value': override_value2
                    }

                ]
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            output = yaml.load(self.hosts.get_yaml_output(self.host.name))
            self.assertEqual(output['parameters'][name], [80, 90, 90, 100])

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_create_matcher_avoid_duplicate(self):
        """Merge the values of all the associated matchers, remove duplicates.

        :id: 75fc514f-70dd-4cc1-8069-221e9edda89a

        :steps:

            1.  Create variable with type array and value.
            2.  Create first matcher for attribute fqdn with some value.
            3.  Create second matcher for other attribute with same value as
                fqdn matcher.
                Note - The fqdn/host should have this attribute.
            4.  Select 'Merge overrides' checkbox.
            5.  Select 'Merge default' checkbox.
            6.  Select 'Avoid Duplicates' checkbox.
            7.  Submit the change.
            8.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output has the default value of variable.
            3.  Duplicate values in YAML output are removed / not displayed.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        override_value = '[80, 90]'
        override_value2 = '[90, 100]'
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value='[20]',
                key_type='array',
                matcher_merge_overrides=True,
                matcher_merge_avoid=True,
                matcher=[
                    {
                        'matcher_attribute': 'fqdn={0}'.format(self.host.name),
                        'matcher_value': override_value
                    },
                    {
                        'matcher_attribute': 'domain={0}'.format(
                            self.domain_name),
                        'matcher_value': override_value2
                    }

                ]
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            output = yaml.load(self.hosts.get_yaml_output(self.host.name))
            self.assertEqual(output['parameters'][name], [80, 90, 100])

    @run_only_on('sat')
    @tier2
    def test_negative_create_matcher_avoid_duplicate(self):
        """Duplicates not removed as they were not really present.

        :id: 050c7cef-eed6-4a61-b567-371f398647a2

        :steps:

            1.  Create variable with type array and value.
            2.  Create first matcher for attribute fqdn with some value.
            3.  Create second matcher for other attribute with other value than
                fqdn matcher and default value.
                Note - The fqdn/host should have this attribute.
            4.  Select 'Merge overrides' checkbox.
            5.  Select 'Merge default' checkbox.
            6.  Select 'Avoid Duplicates' checkbox.
            7.  Submit the change.
            8.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all matchers.
            2.  The YAML output has the default value of variable.
            3.  No value removed as duplicate value.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        override_value = '[70, 80]'
        override_value2 = '[90, 100]'
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value='[20]',
                key_type='array',
                matcher_merge_overrides=True,
                matcher_merge_avoid=True,
                matcher=[
                    {
                        'matcher_attribute': 'fqdn={0}'.format(self.host.name),
                        'matcher_value': override_value
                    },
                    {
                        'matcher_attribute': 'domain={0}'.format(
                            self.domain_name),
                        'matcher_value': override_value2
                    }

                ]
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            output = yaml.load(self.hosts.get_yaml_output(self.host.name))
            self.assertEqual(output['parameters'][name], [70, 80, 90, 100])

    @run_only_on('sat')
    @tier1
    def test_negative_enable_merge_overrides_default_checkboxes(self):
        """Verify that Merge Overrides and Merge Default checkboxes are
        disabled for non supported types

        :id: 834af938-e056-4a40-8831-91f6400aedd3

        :steps: Set variable type other than array/hash.

        :expectedresults: The Merge Overrides, Merge Default checkboxes are
            disabled for editing

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                default_value=gen_string('numeric'),
                key_type='integer',
                puppet_class=self.puppet_class.name,
            )
            self.assertFalse(
                self.smart_variable.validate_checkbox(name, 'Merge Overrides'))
            self.assertFalse(
                self.smart_variable.validate_checkbox(name, 'Merge Default'))

    @run_only_on('sat')
    @tier1
    def test_negative_enable_avoid_duplicates_checkbox(self):
        """Verify that Merge Overrides and Avoid Duplicates checkboxes are
        disabled for non supported types

        :id: 8dc28e77-584a-46f9-aed7-dcc3345a2d9b

        :steps: Set variable type other than array.

        :expectedresults: The Merge Overrides, Avoid Duplicates checkboxes are
            disabled for editing

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                default_value='true',
                key_type='boolean',
                puppet_class=self.puppet_class.name,
            )
            self.assertFalse(
                self.smart_variable.validate_checkbox(name, 'Merge Overrides'))
            self.assertFalse(
                self.smart_variable.validate_checkbox(name, 'Avoid Duplicates')
            )

    @run_only_on('sat')
    @tier2
    def test_positive_impact_delete_attribute(self):
        """Impact on variable after deleting associated attribute.

        :id: 26ce3c25-0deb-415d-a2f5-0eacaf354f92

        :steps:

            1.  Create a variable with matcher for some attribute.
            2.  Delete the attribute.
            3.  Recreate the attribute with same name as earlier.

        :expectedresults:

            1.  The matcher for deleted attribute removed from variable.
            2.  On recreating attribute, the matcher should not reappear in
                variable.

        :CaseLevel: Integration
        """
        sv_name = gen_string('alpha')
        hg_name = gen_string('alpha')
        hostgroup = entities.HostGroup(
            name=hg_name, environment=self.env).create()
        hostgroup.add_puppetclass(
            data={'puppetclass_id': self.puppet_class.id})
        with Session(self) as session:
            make_smart_variable(
                session,
                name=sv_name,
                puppet_class=self.puppet_class.name,
                matcher=[{
                        'matcher_attribute': 'hostgroup={0}'.format(
                            hostgroup.name),
                        'matcher_value': gen_string('alpha')
                    },
                ]
            )
            self.assertTrue(self.smart_variable.validate_smart_variable(
                sv_name, 'overrides_number', '1'))
            hostgroup.delete()
            self.assertTrue(self.smart_variable.validate_smart_variable(
                sv_name, 'overrides_number', '0'))
            hostgroup = entities.HostGroup(
                name=hg_name, environment=self.env).create()
            hostgroup.add_puppetclass(
                data={'puppetclass_id': self.puppet_class.id})
            self.assertTrue(self.smart_variable.validate_smart_variable(
                sv_name, 'overrides_number', '0'))

    @run_only_on('sat')
    @tier2
    def test_positive_override_from_attribute(self):
        """Impact on variable on overriding the variable value from attribute.

        :id: 0d4a6b5f-09d8-4d64-ae4b-efa152815ea8

        :steps:

            1.  Create a variable.
            2.  From host/hostgroup, override the variable value.
            3.  Submit the changes.

        :expectedresults:

            1.  The host/hostgroup is saved with changes.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
            )
            self.assertTrue(self.smart_variable.validate_smart_variable(
                name, 'overrides_number', '0'))
            self.hosts.set_smart_variable_value(
                self.host.name, name, gen_string('alpha'))
            self.assertTrue(self.smart_variable.validate_smart_variable(
                name, 'overrides_number', '1'))

    @run_only_on('sat')
    @tier2
    def test_positive_override_default_value_from_attribute(self):
        """Override smart variable that has default value with a new value from
        attribute(host) page

        :id: a76dcb34-b005-4998-99e9-418b2e821a00

        :steps:

            1.  Create a variable with array type and default value
            2.  From host/hostgroup, override the variable value.
            3.  Submit the changes.

        :expectedresults:

            1.  The host/hostgroup is saved with changes and variable value has
                been changed
            2.  Smart variable should be treated as overridden

        :BZ: 1405118

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        new_value = '[90,100,120]'
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                key_type='array',
                default_value='[20,30]',
            )
            self.assertTrue(self.smart_variable.validate_smart_variable(
                name, 'overrides_number', '0'))
            self.hosts.set_smart_variable_value(
                self.host.name, name, new_value)
            self.assertTrue(self.smart_variable.validate_smart_variable(
                name, 'overrides_number', '1'))
            sv_value = self.hosts.get_smart_variable_value(
                self.host.name, name)
            self.assertEqual(sv_value.get_attribute('value'), new_value)

    @run_only_on('sat')
    @tier2
    def test_negative_create_override_from_attribute(self):
        """No impact on variable on overriding the variable with invalid value
        from attribute.

        :id: 18071443-a511-49c4-9ca9-04c7594b831d

        :steps:

            1.  Create a variable.
            2.  Associate variable with fqdn/hostgroup.
            3.  From host/hostgroup, attempt to override the variable with some
                other key type of value.

        :expectedresults:

            1.  Error thrown for invalid type value.
            2.  No matcher for fqdn/hostgroup is created inside variable.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        default_value = gen_string('numeric').lstrip('0')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                key_type='integer',
                default_value=default_value,
                puppet_class=self.puppet_class.name,
            )
            self.assertTrue(self.smart_variable.validate_smart_variable(
                name, 'overrides_number', '0'))
            self.hosts.set_smart_variable_value(
                self.host.name, name, gen_string('alpha'))
            self.assertIsNotNone(
                self.hosts.wait_until_element(
                    locators['host.override_error'] % default_value))
            self.assertTrue(self.smart_variable.validate_smart_variable(
                name, 'overrides_number', '0'))

    @run_only_on('sat')
    @tier2
    def test_positive_update_matcher_from_attribute(self):
        """Impact on variable on editing the variable value from attribute.

        :id: e98a8404-5e32-4d2e-af81-4339d214658a

        :steps:

            1.  Create a variable.
            2.  Associate variable with fqdn/hostgroup.
            3.  Create a matcher for fqdn/hostgroup with valid details.
            4.  From host/hostgroup, edit the variable value.
            5.  Submit the changes.

        :expectedresults:

            1.  The host/hostgroup is saved with changes.
            2.  Matcher value in variable is updated from fqdn/hostgroup.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        host_override_value = gen_string('numeric').lstrip('0')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value=gen_string('numeric'),
                key_type='integer',
                matcher=[
                    {
                        'matcher_attribute': 'fqdn={0}'.format(self.host.name),
                        'matcher_value': gen_string('numeric')
                    },
                ]
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            # Change matcher value for smart variable from Host page
            self.hosts.set_smart_variable_value(
                self.host.name, name, host_override_value, override=False)
            # Check that matcher value was changed from smart variable
            # interface
            self.smart_variable.click(self.smart_variable.search(name))
            sv_matcher_value = self.smart_variable.wait_until_element(
                locators['smart_variable.matcher_value'] % 1)
            self.assertEqual(sv_matcher_value.text, host_override_value)

    @run_only_on('sat')
    @tier2
    def test_negative_update_matcher_from_attribute(self):
        """No impact on variable on editing the variable with invalid value
        from attribute.

        :id: bd4a2535-57dd-49a8-b8b5-c5e8de652aa7

        :steps:

            1.  Create a variable.
            2.  Associate variable with fqdn/hostgroup.
            3.  Create a matcher for fqdn/hostgroup with valid details.
            4.  From host/hostgroup, attempt to edit the variable with invalid
                value.

        :expectedresults:

            1.  Error thrown for invalid value.
            2.  Matcher value in variable is not updated from fqdn/hostgroup.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        override_value = gen_string('numeric').lstrip('0')
        host_override_value = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value=gen_string('numeric'),
                key_type='integer',
                matcher=[
                    {
                        'matcher_attribute': 'fqdn={0}'.format(self.host.name),
                        'matcher_value': override_value
                    },
                ]
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            # Attempt to change matcher value from Host page using invalid
            # value
            self.hosts.set_smart_variable_value(
                self.host.name, name, host_override_value, override=False)
            self.assertIsNotNone(self.hosts.wait_until_element(
                    locators['host.override_error'] % override_value))
            # Verify that matcher value was not changed
            self.smart_variable.click(self.smart_variable.search(name))
            sv_matcher_value = self.smart_variable.wait_until_element(
                locators['smart_variable.matcher_value'] % 1)
            self.assertEqual(sv_matcher_value.text, override_value)
            self.assertNotEqual(sv_matcher_value.text, host_override_value)

    @run_only_on('sat')
    @tier1
    def test_positive_hide_default_value(self):
        """Hide the default value of variable.

        :id: cd2ec5a5-4bf1-4239-9b3a-8fbca02d7070

        :steps:

            1.  Create a variable.
            2.  Enter some valid default value.
            3.  Check 'Hidden Value' checkbox.

        :expectedresults: Created Smart Variable has hidden default value

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        value = gen_string('alphanumeric')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                default_value=value,
                puppet_class=self.puppet_class.name,
                hidden_value=True,
            )
            self.smart_variable.click(self.smart_variable.search(name))
            default_value = self.smart_variable.wait_until_element(
                locators['smart_variable.default_value'])
            self.assertEqual(default_value.get_attribute('value'), value)
            self.assertIn('masked-input', default_value.get_attribute('class'))

    @run_only_on('sat')
    @tier1
    def test_positive_unhide_default_value(self):
        """Unhide the default value of variable.

        :id: 708fbd15-5177-4eb5-800a-4266e2476439

        :steps:

            1.  Create a variable.
            2.  Enter some valid default value.
            3.  Hide the value of variable.
            4.  After hiding, uncheck the 'Hidden Value' checkbox.

        :expectedresults: The default value shown in unhidden state.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        value = gen_string('alphanumeric')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                default_value=value,
                puppet_class=self.puppet_class.name,
                hidden_value=True,
            )
            self.smart_variable.search_and_click(name)
            default_value = self.smart_variable.wait_until_element(
                locators['smart_variable.default_value'])
            self.assertIn('masked-input', default_value.get_attribute('class'))
            self.smart_variable.update(name, hidden_value=False)
            self.smart_variable.click(self.smart_variable.search(name))
            default_value = self.smart_variable.wait_until_element(
                locators['smart_variable.default_value'])
            self.assertNotIn(
                'masked-input', default_value.get_attribute('class'))
            self.assertEqual(default_value.get_attribute('value'), value)

    @run_only_on('sat')
    @tier2
    def test_positive_hide_default_value_in_attribute(self):
        """Hide the default value of variable in attribute.

        :id: 3b9661f9-f7f7-4dbe-8b08-1a712db6a83d

        :steps:

            1.  Create a variable.
            2.  Enter some valid default value.
            3.  Hide the default Value.
            4.  Submit the changes.
            5.  Associate variable on host/hostgroup.

        :expectedresults:

            1.  In host/hostgroup, the variable value shown in hidden state.
            2.  The button for unhiding the value is displayed and accessible.
            3.  The button for overriding the value is displayed and
                accessible.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        default_value = gen_string('numeric').lstrip('0')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value=default_value,
                hidden_value=True,
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            self.hosts.search_and_click(self.host.name)
            self.hosts.click(locators['host.edit'])
            self.hosts.click(tab_locators['host.tab_params'])
            sv_value = self.hosts.get_smart_variable_value(
                self.host.name, name)
            self.assertEqual(sv_value.get_attribute('value'), default_value)
            self.assertIn('masked-input', sv_value.get_attribute('class'))
            self.assertIn(
                '***', sv_value.get_attribute('data-hidden-value'))
            self.assertTrue(self.smart_variable.is_element_enabled(
                locators['host.smart_variable_override'] % name))
            self.assertTrue(self.smart_variable.is_element_enabled(
                locators['host.smart_variable_unhide'] % name))

    @run_only_on('sat')
    @tier2
    def test_positive_unhide_default_value_in_attribute(self):
        """Unhide the default value of variable in attribute.

        :id: 5d7c1eb2-3f98-4dfd-aac0-ff740b7f82ec

        :steps:

            1.  Create a variable.
            2.  Enter some valid default value.
            3.  Hide the default Value.
            4.  Submit the changes.
            5.  Associate variable on host/hostgroup.
            6.  In host/hostgroup, Click Unhide button icon.

        :expectedresults:

            1.  In host/hostgroup, the variable value shown in unhidden state.
            2.  The button for hiding the value is displayed and accessible.
            3.  The button for overriding the value is displayed and
                accessible.
            4.  In variable, the default value is still hidden.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        default_value = gen_string('numeric').lstrip('0')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value=default_value,
                hidden_value=True,
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            sv_value = self.hosts.get_smart_variable_value(
                self.host.name, name)
            self.assertIn('masked-input', sv_value.get_attribute('class'))
            self.hosts.click(locators['host.smart_variable_unhide'] % name)
            self.assertTrue(self.smart_variable.is_element_enabled(
                locators['host.smart_variable_override'] % name))
            self.assertTrue(self.smart_variable.is_element_enabled(
                locators['host.smart_variable_hide'] % name))
            self.hosts.click(common_locators['submit'])
            self.smart_variable.click(self.smart_variable.search(name))
            default_value = self.smart_variable.wait_until_element(
                locators['smart_variable.default_value'])
            self.assertIn('masked-input', default_value.get_attribute('class'))

    @run_only_on('sat')
    @run_in_one_thread_if_bug_open('bugzilla', 1440878)
    @tier1
    def test_positive_update_hidden_value(self):
        """Update the hidden default value of variable.

        :id: b56e2b84-ba31-4fd2-b65a-ac9f3eb1c1e1

        :steps:

            1.  Create a variable.
            2.  Enter some valid default value.
            3.  Hide the default Value.
            4.  Again update the default value.
            5.  Submit the changes.

        :expectedresults:

            1.  The variable default value is updated.
            2.  The variable default value displayed as hidden.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        value = gen_string('alphanumeric')
        new_value = gen_string('alphanumeric')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                default_value=value,
                puppet_class=self.puppet_class.name,
                hidden_value=True,
            )
            self.smart_variable.click(self.smart_variable.search(name))
            default_value = self.smart_variable.wait_until_element(
                locators['smart_variable.default_value'])
            self.assertIn('masked-input', default_value.get_attribute('class'))
            self.assertEqual(default_value.get_attribute('value'), value)
            self.smart_variable.assign_value(
                locators['smart_variable.default_value'], new_value)
            self.smart_variable.click(common_locators['submit'])
            self.smart_variable.click(self.smart_variable.search(name))
            default_value = self.smart_variable.wait_until_element(
                locators['smart_variable.default_value'])
            self.assertIn('masked-input', default_value.get_attribute('class'))
            self.assertEqual(default_value.get_attribute('value'), new_value)

    @run_only_on('sat')
    @tier2
    def test_positive_update_hidden_value_in_attribute(self):
        """Update the hidden default value of variable in attribute.

        :id: 2f506d47-aed5-45ad-a6fb-133ece18eb14

        :steps:

            1.  Create a variable.
            2.  Enter some valid default value.
            3.  Hide the default Value.
            4.  Submit the changes.
            5.  Associate variable on host/hostgroup.
            6.  In host/hostgroup, update the variable value.

        :expectedresults:

            1.  In host/hostgroup, the variable value is updated.
            2.  The variable Value displayed as hidden.
            3.  In variable, new matcher created for fqdn/hostgroup.
            4.  And the value shown hidden.

        :CaseLevel: Integration
        """
        name = gen_string('alpha')
        default_value = gen_string('numeric').lstrip('0')
        host_override_value = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                puppet_class=self.puppet_class.name,
                default_value=default_value,
                hidden_value=True,
            )
            self.assertIsNotNone(self.smart_variable.search(name))
            sv_value = self.hosts.get_smart_variable_value(
                self.host.name, name)
            self.assertIn('masked-input', sv_value.get_attribute('class'))
            self.assertEqual(sv_value.get_attribute('value'), default_value)
            self.hosts.set_smart_variable_value(
                self.host.name, name, host_override_value)
            sv_value = self.hosts.get_smart_variable_value(
                self.host.name, name)
            self.assertIn('masked-input', sv_value.get_attribute('class'))
            self.assertEqual(
                sv_value.get_attribute('value'), host_override_value)
            self.smart_variable.search_and_click(name)
            default_value_element = self.smart_variable.wait_until_element(
                locators['smart_variable.default_value'])
            self.assertEqual(
                default_value_element.get_attribute('value'), default_value)
            self.assertIn(
                'masked-input', default_value_element.get_attribute('class'))
            matcher_element = self.smart_variable.wait_until_element(
                locators['smart_variable.matcher_value'] % 1)
            self.assertEqual(
                matcher_element.get_attribute('value'), host_override_value)
            self.assertIn(
                'masked-input', matcher_element.get_attribute('class'))

    @run_only_on('sat')
    @tier1
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        :id: ee96bc8c-5294-4580-8316-e62e72e9e3ea

        :steps:

            1.  Create a variable.
            2.  Don't enter any value, keep blank.
            3.  Check the 'Hidden Value' icon.
            4.  Create a matcher with some value.

        :expectedresults:

            1.  The 'Hidden Value' checkbox is enabled to check.
            2.  The default value shows empty on hide.
            3.  Matcher Value shown as hidden.

        :CaseImportance: Critical

        :CaseAutomation: automated
        """
        name = gen_string('alpha')
        override_value = gen_string('alpha')
        with Session(self) as session:
            make_smart_variable(
                session,
                name=name,
                default_value='',
                puppet_class=self.puppet_class.name,
                hidden_value=True,
                matcher=[
                    {
                        'matcher_attribute': 'fqdn={0}'.format(self.host.name),
                        'matcher_value': override_value
                    },
                ]
            )
            self.smart_variable.click(self.smart_variable.search(name))
            default_value = self.smart_variable.wait_until_element(
                locators['smart_variable.default_value'])
            self.assertIn('masked-input', default_value.get_attribute('class'))
            self.assertEqual(default_value.get_attribute('value'), '')
            # Check matcher state and value
            matcher_element = self.smart_variable.wait_until_element(
                locators['smart_variable.matcher_value'] % 1)
            self.assertEqual(
                matcher_element.get_attribute('value'), override_value)
            self.assertIn('masked-input', default_value.get_attribute('class'))
