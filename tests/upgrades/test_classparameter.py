"""Test Puppet Class Parameter related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Parameters

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import json

from nailgun import entities
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import get_entity_data

from robottelo.api.utils import delete_puppet_class
from robottelo.api.utils import publish_puppet_module
from robottelo.constants.repos import CUSTOM_PUPPET_REPO
from robottelo.test import APITestCase


def _valid_sc_parameters_data():
    """Returns a list of valid smart class parameter types and values"""
    return [
        {'sc_type': 'string', 'value': '\u6120\U000201fc\u3a07\U0002b2cf\u45b9\u7d3c\U00026dea'},
        {'sc_type': 'boolean', 'value': '1'},
        {'sc_type': 'boolean', 'value': '0'},
        {'sc_type': 'integer', 'value': 4541321256269544184},
        {'sc_type': 'real', 'value': -123.0},
        {'sc_type': 'array', 'value': "['JkKAxzCvIw', '343532124', 'False']"},
        {'sc_type': 'hash', 'value': '{"SAEasshgd": "ASDFDdsss"}'},
        {'sc_type': 'yaml', 'value': 'name=>XYZ'},
        {'sc_type': 'json', 'value': '{"name": "XYZ"}'},
    ]


class TestScenarioPositivePuppetParameterAndDatatypeIntact(APITestCase):
    """Puppet Class Parameters value and type is intact post upgrade

    :id: 08012f39-240b-40df-b893-2ee767129737

    :steps:

        1. In Preupgrade Satellite, Import a puppet module having parameters
        2. Update existing class parameters with different value and type
        3. Upgrade the satellite to next/latest version
        4. Postupgrade, Verify the data and type of updated parameters

    :expectedresults: The puppet class parameters data and type should be
        intact post upgrade
    """

    def setupScenario(self):
        """Import some parametrized puppet classes. This is required to make
        sure that we have smart class variable available.
        Read all available smart class parameters for imported puppet class to
        be able to work with unique entity for each specific test.
        """
        self.puppet_modules = [{'author': 'robottelo', 'name': 'api_test_classparameters'}]
        self.org = entities.Organization().create()
        cv = publish_puppet_module(self.puppet_modules, CUSTOM_PUPPET_REPO, self.org)
        self.env = (
            entities.Environment().search(query={'search': f'content_view="{cv.name}"'})[0].read()
        )
        self.puppet_class = entities.PuppetClass().search(
            query={
                'search': 'name = "{}" and environment = "{}"'.format(
                    self.puppet_modules[0]['name'], self.env.name
                )
            }
        )[0]
        self.sc_params_list = entities.SmartClassParameters().search(
            query={'search': f'puppetclass="{self.puppet_class.name}"', 'per_page': 1000}
        )
        scenario_ents = {self.__class__.__name__: {'puppet_class': self.puppet_class.name}}
        create_dict(scenario_ents)

    def _validate_value(self, data, sc_param):
        """The helper function to validate the parameter actual and expected
        value

        :param data: The Expected Value of parameter
        :param sc_param: The Actual Value of parameter
        """
        if data['sc_type'] == 'boolean':
            self.assertEqual(sc_param.default_value, True if data['value'] == '1' else False)
        elif data['sc_type'] == 'array':
            string_list = [str(element) for element in sc_param.default_value]
            self.assertEqual(str(string_list), data['value'])
        elif data['sc_type'] in ('json', 'hash'):
            self.assertEqual(
                sc_param.default_value,
                # convert string to dict
                json.loads(data['value']),
            )
        else:
            self.assertEqual(sc_param.default_value, data['value'])

    @pre_upgrade
    def test_pre_puppet_class_parameter_data_and_type(self):
        """Puppet Class parameters with different data type are created

        :steps:

            1. In Preupgrade Satellite, Import a puppet module having
            parameters
            2. Update existing class parameters with different value and type

        :expectedresults: The parameters are updated with different data types
        """
        self.setupScenario()
        for count in range(1, 10):
            with self.subTest(count):
                data = _valid_sc_parameters_data()[count - 1]
                sc_param = entities.SmartClassParameters().search(
                    query={'search': f'parameter="api_classparameters_scp_00{count}"'}
                )[0]
                sc_param.override = True
                sc_param.parameter_type = data['sc_type']
                sc_param.default_value = data['value']
                sc_param.update(['override', 'parameter_type', 'default_value'])
                sc_param = sc_param.read()
                self.assertEqual(sc_param.parameter_type, data['sc_type'])
                self._validate_value(data, sc_param)

    @post_upgrade(depend_on=test_pre_puppet_class_parameter_data_and_type)
    def test_post_puppet_class_parameter_data_and_type(self):
        """Puppet Class Parameters value and type is intact post upgrade

        :steps: Postupgrade, Verify the value and type of updated parameters

        :expectedresults: The puppet class parameters data and type should be
            intact post upgrade
        """
        for count in range(1, 10):
            with self.subTest(count):
                data = _valid_sc_parameters_data()[count - 1]
                sc_param = entities.SmartClassParameters().search(
                    query={'search': f'parameter="api_classparameters_scp_00{count}"'}
                )[0]
                self.assertEqual(sc_param.parameter_type, data['sc_type'])
                self._validate_value(data, sc_param)
        puppet_class = get_entity_data(self.__class__.__name__)['puppet_class']
        delete_puppet_class(puppet_class)
