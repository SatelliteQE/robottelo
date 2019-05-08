# -*- encoding: utf-8 -*-
"""Test class for Smart/Puppet Class Parameter

:Requirement: Classparameters

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from fauxfactory import gen_integer, gen_string
from nailgun import entities


from robottelo.api.utils import (
    delete_puppet_class,
    publish_puppet_module,
)
from robottelo.constants import CUSTOM_PUPPET_REPO
from robottelo.datafactory import filtered_datapoint
from robottelo.decorators import (
    run_in_one_thread,
    run_only_on,
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@filtered_datapoint
def invalid_sc_parameters_data():
    """Returns a list of invalid smart class parameter types and values"""
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


@run_in_one_thread
class SmartClassParametersTestCase(UITestCase):
    """Implements Smart Class Parameter tests in UI"""

    @classmethod
    def set_session_org(cls):
        """Creates new organization to be used for current session the
        session_user will login automatically with this org in context
        """
        cls.session_org = entities.Organization().create()

    @classmethod
    def setUpClass(cls):
        """Import some parametrized puppet classes. This is required to make
        sure that we have smart class parameter available.
        Read all available smart class parameters for imported puppet class to
        be able to work with unique entity for each specific test.
        """
        super(SmartClassParametersTestCase, cls).setUpClass()
        cls.pm_name = 'ui_test_classparameters'
        cls.puppet_modules = [
            {'author': 'robottelo', 'name': cls.pm_name},
        ]
        cv = publish_puppet_module(
            cls.puppet_modules, CUSTOM_PUPPET_REPO, cls.session_org)
        cls.env = entities.Environment().search(
            query={'search': u'content_view="{0}"'.format(cv.name)}
        )[0].read()
        cls.puppet_class = entities.PuppetClass().search(query={
            'search': u'name = "{0}" and environment = "{1}"'.format(
                cls.puppet_modules[0]['name'], cls.env.name)
        })[0]
        cls.sc_params_list = entities.SmartClassParameters().search(
            query={
                'search': 'puppetclass="{0}"'.format(cls.puppet_class.name),
                'per_page': 1000
            })

        cls.host = entities.Host(organization=cls.session_org).create()
        cls.host.environment = cls.env
        cls.host.update(['environment'])
        cls.host.add_puppetclass(data={'puppetclass_id': cls.puppet_class.id})
        cls.domain_name = entities.Domain(id=cls.host.domain.id).read().name

    @classmethod
    def tearDownClass(cls):
        """Removes puppet class."""
        super(SmartClassParametersTestCase, cls).tearDownClass()
        delete_puppet_class(cls.puppet_class.name)

    @run_only_on('sat')
    @tier1
    def test_positive_search(self):
        """Search for specific smart class parameter

        :id: 76fcb049-2c3e-4ac1-944b-6dd7b0c69097

        :expectedresults: Specified smart class parameter can be found in the
            system
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.assertIsNotNone(self.sc_parameters.search(
                sc_param.parameter, self.puppet_class.name))

    @run_only_on('sat')
    @tier1
    def test_positive_override_checkbox(self):
        """Override the Default Parameter value.

        :id: e798b1be-b176-48e2-887f-3f3370efef90

        :steps:
            1.  Check the Override checkbox.
            2.  Set the new valid Default Value.
            3.  Submit the changes.

        :expectedresults: Parameter Value overridden with new value.
        """
        new_value = gen_string('alpha')
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=new_value
            )
            default_value = self.sc_parameters.fetch_default_value(
                sc_param.parameter, self.puppet_class.name)
            self.assertEqual(default_value, new_value)

    @run_only_on('sat')
    @tier1
    def test_positive_edit_parameter_dialog(self):
        """Validation, merging and matcher sections are accessible for enabled
        'Override' checkbox.

        :id: a6639110-1a58-4f68-8265-369b515f9c4a

        :steps: Check the Override checkbox.

        :expectedresults: Puppet Default, Hiding, Validation, Merging and
            Matcher section enabled.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True
            )
            self.sc_parameters.click(self.sc_parameters.search(
                sc_param.parameter, self.puppet_class.name))
            self.sc_parameters.click(
                locators['sc_parameters.optional_expander'])
            locators_list = [
                'sc_parameters.omit',
                'sc_parameters.hidden_value',
                'sc_parameters.validator_type',
                'sc_parameters.matcher_priority',
                'sc_parameters.add_matcher',
            ]
            for locator in locators_list:
                self.assertTrue(
                    self.sc_parameters.is_element_enabled(locators[locator]))

    @run_only_on('sat')
    @tier1
    def test_negative_edit_parameter_dialog(self):
        """Validation, merging and matcher sections are not accessible for
        disabled 'Override' checkbox.

        :id: 30da3a17-05a5-4c19-8210-80c3a8dcf32b

        :steps: Don't Check the Override checkbox.

        :expectedresults: Default Value, Puppet Default, Hiding, Validation,
            Merging and Matcher section is disabled.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=False
            )
            self.sc_parameters.click(self.sc_parameters.search(
                sc_param.parameter, self.puppet_class.name))
            self.sc_parameters.click(
                locators['sc_parameters.optional_expander'])
            locators_list = [
                'sc_parameters.default_value',
                'sc_parameters.omit',
                'sc_parameters.hidden_value',
                'sc_parameters.validator_type',
                'sc_parameters.matcher_priority',
                'sc_parameters.add_matcher',
            ]
            for locator in locators_list:
                self.assertFalse(
                    self.sc_parameters.is_element_enabled(locators[locator]))

    @run_only_on('sat')
    @tier1
    def test_negative_update_parameter_type(self):
        """Negative Parameter Update for parameter types - Invalid Value.

        Types - string, boolean, integer, real, array, hash, yaml, json

        :id: 4285b397-0426-4523-8cc2-8e5d79f49aae

        :steps:
            1.  Check the Override checkbox.
            2.  Update the Key Type.
            3.  Enter an 'Invalid' default Value.
            4.  Submit the changes.

        :expectedresults: Parameter is not updated with invalid value for
            specific type.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            initial_value = self.sc_parameters.fetch_default_value(
                sc_param.parameter, self.puppet_class.name)
            for data in invalid_sc_parameters_data():
                with self.subTest(data):
                    self.sc_parameters.update(
                        sc_param.parameter,
                        self.puppet_class.name,
                        override=True,
                        key_type=data['sc_type'],
                        default_value=data['value'],
                    )
                    self.assertIsNotNone(
                        self.sc_parameters.wait_until_element(
                            common_locators['haserror'])
                    )
                    value = self.sc_parameters.fetch_default_value(
                        sc_param.parameter, self.puppet_class.name)
                    self.assertEqual(value, initial_value)

    @run_only_on('sat')
    @tier1
    def test_positive_validate_puppet_default_value(self):
        """Validation doesn't works on puppet default value.

        :id: 8671338d-5547-4259-9119-a8952b4d982d

        :steps:
            1.  Check the Override checkbox.
            2.  Check 'Use Puppet Default' value.
            3.  Validate this value under section 'Optional Input Validator'.

        :expectedresults: Validation shouldn't work with puppet default value.

        :CaseAutomation: automated
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                omit=True,
                validator_type='list',
                validator_rule='45, test, 75',
            )
            self.sc_parameters.click(self.sc_parameters.search(
                sc_param.parameter, self.puppet_class.name))
            self.assertTrue(self.sc_parameters.wait_until_element(
                locators['sc_parameters.omit']).is_selected())
            self.assertFalse(self.sc_parameters.is_element_enabled(
                locators['sc_parameters.default_value']))
            self.sc_parameters.click(
                locators['sc_parameters.optional_expander'])
            value = self.sc_parameters.wait_until_element(
                locators['sc_parameters.validator_rule']
            ).get_attribute('value')
            self.assertEqual(value, u'45, test, 75')

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_validate_default_value_required_checkbox(self):
        """Error raised for blank default Value - Required checkbox.

        :id: b665891a-15c2-4e7b-a118-f239ff45d37a

        :steps:
            1.  Check the Override checkbox.
            2.  Don't provide any default value, keep blank.
            3.  Check Required checkbox in 'Optional Input Validator'.
            4.  Submit the change.

        :expectedresults: Error raised for blank default value by 'Required'
            checkbox.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_validate_matcher_value_required_checkbox(self):
        """Error raised for blank matcher Value - Required checkbox.

        :id: e88b1bc7-529a-4dbd-9e43-4738580e12ab

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher for Parameter for some attribute.
            3.  Dont provide Value for matcher. Keep blank.
            4.  Check Required checkbox in 'Optional Input Validator'.
            5.  Submit the change.

        :expectedresults: Error raised for blank matcher value by 'Required'
            checkbox.

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @run_only_on('sat')
    @tier1
    def test_negative_validate_default_value_with_regex(self):
        """Error raised for default value not matching with regex.

        :id: 1854c189-8a5f-410c-b195-ea2a51e72b30

        :steps:
            1.  Check the Override checkbox.
            2.  Provide default value that doesn't matches the regex of step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for default value not matching with
            regex.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_string('alpha'),
                validator_type='regexp',
                validator_rule='[0-9]',
            )
            self.assertIsNotNone(
                self.sc_parameters.wait_until_element(
                    common_locators['haserror'])
            )

    @run_only_on('sat')
    @tier1
    def test_positive_validate_default_value_with_regex(self):
        """Error not raised for default value matching with regex.

        :id: 81ab3074-dc22-4c60-b638-62fdfabe60fb

        :steps:
            1.  Check the Override checkbox.
            2.  Provide default value that matches the regex of step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for default value matching with
            regex.
        """
        sc_param = self.sc_params_list.pop()
        initial_value = gen_string('numeric')
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=initial_value,
                validator_type='regexp',
                validator_rule='[0-9]',
            )
            self.assertIsNone(
                self.sc_parameters.wait_until_element(
                    common_locators['haserror'], timeout=5)
            )
            value = self.sc_parameters.fetch_default_value(
                sc_param.parameter, self.puppet_class.name)
            self.assertEqual(value, initial_value)

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_value_with_regex(self):
        """Error raised for matcher value not matching with regex.

        :id: 77e56e9b-ddee-41e8-bd9f-e1a43f5053b2

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with value that doesn't matches the regex of
                step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for matcher value not matching with
            regex.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_string('numeric'),
                validator_type='regexp',
                validator_rule='[0-9]',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': gen_string('alpha')
                }]
            )
            self.assertIsNotNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'])
            )

    @run_only_on('sat')
    @tier1
    def test_positive_validate_matcher_value_with_regex(self):
        """Error not raised for matcher value matching with regex.

        :id: e642fcb1-f1dc-4263-adf1-8f881ce06f68

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with value that matches the regex of step 3.
            3.  Validate this value with regex validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for matcher value matching with
            regex.
        """
        sc_param = self.sc_params_list.pop()
        matcher_value = gen_string('numeric')
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_string('numeric'),
                validator_type='regexp',
                validator_rule='[0-9]',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': matcher_value,
                }]
            )
            self.assertIsNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'], timeout=5))
            matchers_list = self.sc_parameters.fetch_matcher_values(
                sc_param.parameter, self.puppet_class.name, 1)
            self.assertEqual(matchers_list[0], matcher_value)

    @run_only_on('sat')
    @tier1
    def test_negative_validate_default_value_with_list(self):
        """Error raised for default value not in list.

        :id: 3d353610-97cd-45a3-8e99-425bc948ee51

        :steps:
            1.  Check the Override checkbox.
            2.  Provide default value that doesn't matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for default value not in list.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_string('alphanumeric'),
                validator_type='list',
                validator_rule='45, test',
            )
            self.assertIsNotNone(
                self.sc_parameters.wait_until_element(
                    common_locators['haserror'])
            )

    @run_only_on('sat')
    @tier1
    def test_positive_validate_default_value_with_list(self):
        """Error not raised for default value in list.

        :id: 62658cde-becd-4083-ba06-1fd4c8904173

        :steps:
            1.  Check the Override checkbox.
            2.  Provide default value that matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for default value in list.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value='475',
                validator_type='list',
                validator_rule='true, 50, 475',
            )
            self.assertIsNone(
                self.sc_parameters.wait_until_element(
                    common_locators['haserror'], timeout=5)
            )
            value = self.sc_parameters.fetch_default_value(
                sc_param.parameter, self.puppet_class.name)
            self.assertEqual(value, '475')

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_value_with_list(self):
        """Error raised for matcher value not in list.

        :id: ab8000e9-0110-473e-9c86-eeb709cbfd08

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with value that doesn't matches the list of
                step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error raised for matcher value not in list.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value='50',
                validator_type='list',
                validator_rule='25, example, 50',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': 'myexample'
                }]
            )
            self.assertIsNone(
                self.sc_parameters.wait_until_element(
                    common_locators['haserror'], timeout=5)
            )
            self.assertIsNotNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'])
            )

    @run_only_on('sat')
    @tier1
    def test_positive_validate_matcher_value_with_list(self):
        """Error not raised for matcher value in list.

        :id: ae5b38e5-f7ea-4325-8a2c-917120470688

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with value that matches the list of step 3.
            3.  Validate this value with list validator type and rule.
            4.  Submit the change.

        :expectedresults: Error not raised for matcher value in list.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value='test',
                validator_type='list',
                validator_rule='test, example, 30',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': '30'
                }]
            )
            self.assertIsNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'], timeout=5))
            matchers_list = self.sc_parameters.fetch_matcher_values(
                sc_param.parameter, self.puppet_class.name, 1)
            self.assertEqual(matchers_list[0], '30')

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_value_with_default_type(self):
        """Error raised for matcher value not of default type.

        :id: 70109667-c72e-4045-92a4-6b8bbbd615eb

        :steps:
            1.  Check the Override checkbox.
            2.  Update parameter default type with valid value.
            3.  Create a matcher with value that doesn't matches the default
                type.
            4.  Submit the change.

        :expectedresults: Error raised for matcher value not of default type.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_integer(),
                key_type='integer',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': gen_string('alpha')
                }]
            )
            self.assertIsNotNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'])
            )

    @run_only_on('sat')
    @tier1
    def test_positive_validate_matcher_value_with_default_type(self):
        """No error for matcher value of default type.

        :id: 57d4d82a-fc5b-4d85-8e8e-9a7ca880c5a2

        :steps:
            1.  Check the Override checkbox.
            2.  Update parameter default type with valid value.
            3.  Create a matcher with value that matches the default type.
            4.  Submit the change.

        :expectedresults: Error not raised for matcher value of default type.
        """
        sc_param = self.sc_params_list.pop()
        matcher_value = gen_integer()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_integer(),
                key_type='integer',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': matcher_value
                }]
            )
            self.assertIsNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'], timeout=5))
            matchers_list = self.sc_parameters.fetch_matcher_values(
                sc_param.parameter, self.puppet_class.name, 1)
            self.assertEqual(int(matchers_list[0]), matcher_value)

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_and_default_value(self):
        """Error for invalid default and matcher value both at a time.

        :id: 141b9e6a-7c4c-4ab0-8e30-7c3ddff0b9c8

        :steps:
            1.  Check the Override checkbox.
            2.  Update parameter default type with Invalid value.
            3.  Create a matcher with value that doesn't matches the default
                type.
            4.  Submit the change.

        :expectedresults: Error raised for invalid default and matcher value
            both.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_string('alpha'),
                key_type='integer',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': gen_string('alpha')
                }]
            )
            self.assertIsNotNone(
                self.sc_parameters.wait_until_element(
                    common_locators['haserror'])
            )
            self.assertIsNotNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'])
            )

    @run_only_on('sat')
    @tier1
    def test_negative_validate_matcher_non_existing_attribute(self):
        """Error while creating matcher for Non Existing Attribute.

        :id: 46fd985d-2e7f-4a8a-8059-0c4d2ffcc8cd

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with non existing attribute in org.
            3.  Attempt to submit the change.

        :expectedresults: Error raised for non existing attribute.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_string('alpha'),
                matcher=[{
                    'matcher_attribute': 'hostgroup={0}'.format(
                        gen_string('alpha')),
                    'matcher_value': gen_string('alpha')
                }]
            )
            self.assertIsNotNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'])
            )

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1402036)
    @tier1
    def test_positive_validate_matcher_with_comma(self):
        """Create matcher for attribute that has comma in its value

        :id: 2116e85b-add5-4bc3-aab7-5c9f0965c4a8

        :steps:
            1.  Check the Override checkbox.
            2.  Create a matcher with attribute that has comma in its value
            3.  Submit the change.

        :BZ: 1402036

        :expectedresults: Matcher is created and its attribute is not modified
            after update is submitted
        """
        sc_param = self.sc_params_list.pop()
        loc_name = '{0}, {1}'.format(gen_string('alpha'), gen_string('alpha'))
        entities.Location(name=loc_name).create()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_string('alpha'),
                matcher_priority='\n'.join(
                    ['fqdn', 'hostgroup', 'os', 'domain', 'location']),
                matcher=[{
                    'matcher_attribute': 'location={0}'.format(loc_name),
                    'matcher_value': gen_string('alpha')
                }]
            )
            self.assertIsNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'], timeout=5))
            self.sc_parameters.click(self.sc_parameters.search(
                sc_param.parameter, self.puppet_class.name))
            attribute_value = self.sc_parameters.wait_until_element(
                locators['sc_parameters.matcher_attribute_value'] % 1
            ).get_attribute('value')
            self.assertEqual(attribute_value, loc_name)

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_create_matcher_puppet_default_value(self):
        """Create matcher for attribute in parameter, where Value is puppet
        default value.

        :id: 656f25cd-4394-414a-bd8e-458f0e51c668

        :steps:
            1.  Check the Override checkbox.
            2.  Set some default Value.
            3.  Click on 'Add Matcher' button to add matcher.
            4.  Choose valid attribute type, name and puppet default value.
            5.  Submit the change.

        :expectedresults: The matcher has been created successfully.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_integer(),
                key_type='integer',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': '',
                    'matcher_omit': True
                }]
            )
            self.assertIsNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'], timeout=5))
            self.sc_parameters.click(self.sc_parameters.search(
                sc_param.parameter, self.puppet_class.name))
            self.assertFalse(self.sc_parameters.is_element_enabled(
                locators['sc_parameters.matcher_value'] % 1))

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_matcher_merge_override_puppet_value(self):
        """Merge the values of all the associated matchers + puppet default value.

        :id: 4eed74ac-0ead-4723-af4d-8638406691f6

        :steps:
            1.  Check the Override checkbox.
            2.  Set some default Value.
            3.  Create first matcher for attribute fqdn with valid details.
            4.  Create second matcher for other attribute with value as puppet
                default.
                Note - The fqdn/host should have this attribute.
            5.  Create more matchers for some more attributes with value as
                puppet default.
                Note - The fqdn/host should have this attributes.
            6.  Select 'Merge overrides' checkbox.
            7.  Select 'Merge default' checkbox.
            8.  Submit the change.
            9.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the value only for fqdn.
            2.  The YAML output doesn't have the puppet default values of
                matchers.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseLevel: Integration

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_matcher_merge_puppet_default(self):
        """Merge the values of all the associated matchers + puppet default value.

        :id: 8e9075c1-adc5-474e-8aa3-4252f507c155

        :steps:
            1.  Check the Override checkbox.
            2.  Set default Value as puppet default value.
            3.  Create first matcher for attribute fqdn with valid details.
            4.  Create second matcher for other attribute with valid details.
                Note - The fqdn/host should have this attribute.
            5.  Create more matchers for some more attributes if any.
                Note - The fqdn/host should have this attributes.
            6.  Select 'Merge overrides' checkbox.
            7.  Select 'Merge default' checkbox.
            8.  Submit the change.
            9.  Go to YAML output of associated host.

        :expectedresults:

            1.  The YAML output has the values merged from all the associated
                matchers.
            2.  The YAML output doesn't have the puppet default value.
            3.  Duplicate values in YAML output if any are displayed.

        :CaseAutomation: notautomated

        :CaseLevel: Integration

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @tier1
    def test_positive_enable_merge_overrides_default_checkboxes(self):
        """Enable Merge Overrides, Merge Default and Avoid Duplicates
        checkboxes for supported types.

        :id: d6323648-4720-4c33-b25f-2b2b569d9df0

        :steps:
            1.  Check the Override checkbox.
            2.  Set parameter type to array/hash.

        :expectedresults: The Merge Overrides, Merge Default and Avoid
            Duplicates checkboxes are enabled to check.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value='[20]',
                key_type='array',
            )
            self.assertIsNone(
                self.sc_parameters.wait_until_element(
                    locators['sc_parameters.matcher_error'], timeout=5))
            self.sc_parameters.click(self.sc_parameters.search(
                sc_param.parameter, self.puppet_class.name))
            self.assertTrue(self.sc_parameters.is_element_enabled(
                locators['sc_parameters.merge_overrides']))
            self.assertFalse(self.sc_parameters.is_element_enabled(
                locators['sc_parameters.merge_default']))
            self.assertFalse(self.sc_parameters.is_element_enabled(
                locators['sc_parameters.avoid_duplicates']))
            self.sc_parameters.click(locators['sc_parameters.merge_overrides'])
            self.assertTrue(self.sc_parameters.is_element_enabled(
                locators['sc_parameters.merge_default']))
            self.assertTrue(self.sc_parameters.is_element_enabled(
                locators['sc_parameters.avoid_duplicates']))

    @run_only_on('sat')
    @tier1
    def test_negative_enable_merge_overrides_default_checkboxes(self):
        """Disable Merge Overrides, Merge Default checkboxes for non supported types.

        :id: 58e42a4d-fabb-4a93-8787-3399cd6d3394

        :steps:
            1.  Check the Override checkbox.
            2.  Set parameter type other than array/hash.

        :expectedresults: The Merge Overrides, Merge Default checkboxes are not
            enabled to check.
        """
        sc_param = self.sc_params_list.pop()
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_string('alpha'),
                key_type='string',
            )
            self.sc_parameters.click(self.sc_parameters.search(
                sc_param.parameter, self.puppet_class.name))
            locators_list = [
                'sc_parameters.merge_overrides',
                'sc_parameters.merge_default',
                'sc_parameters.avoid_duplicates',
            ]
            for locator in locators_list:
                self.assertFalse(
                    self.sc_parameters.is_element_enabled(locators[locator]))

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_create_override_from_attribute(self):
        """Impact on parameter on overriding the parameter value from attribute.

        :id: dcc8a9f5-191d-42d1-bff5-3083cc46cce1

        :steps:
            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with fqdn/hostgroup.
            3.  From host/hostgroup, override the parameter value.
            4.  Submit the changes.

        :expectedresults:
            1.  The host/hostgroup is saved with changes.
            2.  New matcher for fqdn/hostgroup created inside parameter.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_create_override_from_attribute(self):
        """No impact on parameter on overriding the parameter
        with invalid value from attribute.

        :id: 475d71cc-d52c-4a94-adb6-27ea52493176

        :steps:
            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with fqdn/hostgroup.
            3.  From host/hostgroup, Attempt to override the parameter with
                some other key type of value.
        :expectedresults:
            1.  Error thrown for invalid type value.
            2.  No matcher for fqdn/hostgroup is created inside parameter.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_positive_create_override_from_attribute_puppet_default(self):
        """Impact on parameter on overriding the parameter value
        from attribute - puppet default.

        :id: 2a013541-a4f2-4b54-b6ab-52932b17eb4a

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with fqdn/hostgroup.
            3.  From host/hostgroup, override the parameter value as puppet
                default value.
            4.  Submit the changes.

        :expectedresults:

            1.  The host/hostgroup is saved with changes.
            2.  New matcher for fqdn/hostgroup created inside parameter.
            3.  In matcher, 'Use Puppet Default' checkbox is checked.

        :CaseAutomation: notautomated

        :CaseLevel: Integration

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_create_override_from_attribute_required_checked(self):
        """Error for empty value on overriding the parameter value
        from attribute - Required checked.

        :id: c4fadfa6-0747-475f-8fc5-227c147d585a

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Check 'Required' checkbox in parameter.
            3.  Associate parameter with fqdn/hostgroup.
            4.  From host/hostgroup, Attempt to override the parameter with
                empty value.

        :expectedresults:

            1.  Error thrown for empty value as the value is required to pass.
            2.  The info icon changed to warning icon for that parameter.
            3.  No matcher for fqdn/hostgroup created inside parameter.

        :CaseAutomation: notautomated

        :CaseLevel: Integration

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @stubbed()
    @tier2
    def test_negative_update_matcher_from_attribute(self):
        """No Impact on parameter on editing the parameter with
        invalid value from attribute.

        :id: 554de8b7-0ddb-4f2e-b406-882b13eac882

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with fqdn/hostgroup.
            3.  Create a matcher for fqdn/hostgroup with valid details.
            4.  From host/hostgroup, attempt to edit the parameter with invalid
                value.

        :expectedresults:

            1.  Error thrown for invalid value.
            2.  Matcher value in parameter is not updated from fqdn/hostgroup.

        :CaseAutomation: notautomated

        :CaseLevel: Integration

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1295179)
    @stubbed()
    @tier2
    def test_positive_update_parameter_in_nested_hostgroup(self):
        """Update parameter value in nested hostgroup.

        :id: 9aacec96-593c-4089-ad14-d4bbbbd43ef8

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Associate parameter with one hostgroup.
            3.  Create a nested hostgroup from above parent hostgroup.
            4.  And Update the value of parameter from nested hostgroup.
            5.  Submit the changes.

        :expectedresults:

            1.  The parameter value updated in nested hostgroup.
            2.  Changes submitted successfully.

        :CaseAutomation: notautomated

        :CaseLevel: Integration

        :CaseImportance: Critical
        """

    @run_only_on('sat')
    @tier1
    def test_positive_hide_parameter_default_value(self):
        """Hide the default value of parameter.

        :id: 8b3d294e-58e7-454c-b19e-ead1c6a6a342

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Enter some valid default value.
            3.  Check 'Hidden Value' checkbox.

        :expectedresults:

            1.  The default value shown in hidden state.
            2.  Changes submitted successfully.
            3.  Matcher values shown hidden if any.
        """
        sc_param = self.sc_params_list.pop()
        initial_value = gen_string('alpha')
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=initial_value,
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': gen_string('alpha')
                }],
                hidden_value=True,
            )
            value = self.sc_parameters.fetch_default_value(
                sc_param.parameter, self.puppet_class.name, hidden=True)
            self.assertEqual(value, initial_value)
            locator = self.sc_parameters.wait_until_element(
                locators['sc_parameters.default_value'])
            self.assertIn('masked-input', locator.get_attribute('class'))
            matcher_value = self.sc_parameters.wait_until_element(
                locators['sc_parameters.matcher_value'] % 1)
            self.assertIn('masked-input', matcher_value.get_attribute('class'))

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_unhide_parameter_default_value(self):
        """Unhide the default value of parameter.

        :id: fca478b9-eeb9-41ea-8c41-2d9601f4ea4f

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Enter some valid default value.
            3.  Hide the value of parameter.
            4.  After hiding, uncheck the 'Hidden Value' checkbox.

        :expectedresults:

            1.  The default value shown in unhidden state.
            2.  Changes submitted successfully.
            3.  Matcher values shown unhidden if any.
        """
        sc_param = self.sc_params_list.pop()
        initial_value = gen_string('alpha')
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=initial_value,
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': gen_string('alpha')
                }],
                hidden_value=True,
            )
            self.sc_parameters.update(
                sc_param.parameter, self.puppet_class.name, hidden_value=False)
            value = self.sc_parameters.fetch_default_value(
                sc_param.parameter, self.puppet_class.name, hidden=True)
            self.assertEqual(value, initial_value)
            locator = self.sc_parameters.wait_until_element(
                locators['sc_parameters.default_value'])
            self.assertNotIn('masked-input', locator.get_attribute('class'))
            matcher_value = self.sc_parameters.wait_until_element(
                locators['sc_parameters.matcher_value'] % 1)
            self.assertNotIn(
                'masked-input', matcher_value.get_attribute('class'))

    @run_only_on('sat')
    @tier1
    def test_positive_update_hidden_value_in_parameter(self):
        """Update the hidden default value of parameter.

        :id: e7a6e172-d0b9-48e4-81ae-16d866d6f63b

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Enter some valid default value.
            3.  Hide the default Value.
            4.  Again update the default value.
            5.  Submit the changes.

        :expectedresults:

            1.  The parameter default value is updated.
            2.  The parameter default value displayed as hidden.

        :CaseImportance: Critical
        """
        sc_param = self.sc_params_list.pop()
        new_value = gen_string('alpha')
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value=gen_string('alpha'),
                hidden_value=True,
            )
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                default_value=new_value,
            )
            value = self.sc_parameters.fetch_default_value(
                sc_param.parameter, self.puppet_class.name, hidden=True)
            self.assertEqual(value, new_value)
            locator = self.sc_parameters.wait_until_element(
                locators['sc_parameters.default_value'])
            self.assertIn('masked-input', locator.get_attribute('class'))

    @run_only_on('sat')
    @tier1
    def test_positive_hide_empty_default_value(self):
        """Hiding the empty default value.

        :id: 8b02e575-c7bf-45d1-a5eb-4640b65a4d60

        :steps:

            1.  Check the override checkbox for the parameter.
            2.  Don't enter any value, keep blank.
            3.  Check the 'Hidden Value' icon.
            4.  Create a matcher with some value.

        :expectedresults:

            1.  The 'Hidden Value' checkbox is enabled to check.
            2.  The default value shows empty on hide.
            3.  Matcher Value shown as hidden.

        :CaseAutomation: automated
        """
        sc_param = self.sc_params_list.pop()
        matcher_value = gen_string('alpha')
        with Session(self):
            self.sc_parameters.update(
                sc_param.parameter,
                self.puppet_class.name,
                override=True,
                default_value='',
                matcher=[{
                    'matcher_attribute': 'os=rhel6',
                    'matcher_value': matcher_value
                }],
                hidden_value=True,
            )
            value = self.sc_parameters.fetch_default_value(
                sc_param.parameter, self.puppet_class.name, hidden=True)
            self.assertEqual(value, '')
            locator = self.sc_parameters.wait_until_element(
                locators['sc_parameters.default_value'])
            self.assertIn(
                'masked-input', locator.get_attribute('class'))
            value = self.sc_parameters.wait_until_element(
                locators['sc_parameters.matcher_value'] % 1)
            self.assertIn(
                'masked-input', value.get_attribute('class'))
            self.assertEqual(value.get_attribute('value'), matcher_value)
