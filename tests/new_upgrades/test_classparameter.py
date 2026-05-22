"""Test Puppet Class Parameter related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Puppet

:Team: Endeavour

:CaseImportance: High

"""

import json

import pytest

from robottelo.config import settings
from robottelo.utils.shared_resource import SharedResource

VALID_SC_PARAMS_DATA = [
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


def _validate_value(data, sc_param):
    """The helper function to validate the parameter actual and expected
    value

    :param data: The Expected Value of parameter
    :param sc_param: The Actual Value of parameter
    """
    if data['sc_type'] == 'boolean':
        assert sc_param.default_value == (data['value'] == '1')
    elif data['sc_type'] == 'array':
        string_list = [str(element) for element in sc_param.default_value]
        assert str(string_list) == data['value']
    elif data['sc_type'] in ('json', 'hash'):
        # convert string to dict
        assert sc_param.default_value == json.loads(data['value'])
    else:
        assert sc_param.default_value == data['value']


@pytest.fixture(scope='module')
def module_puppet_class_parameter_data_and_type_setup(
    module_puppet_upgrade_shared_satellite,
    upgrade_action,
):
    """Puppet Class parameters with different data type are created

    :steps:

        1. In Preupgrade Satellite, Import a puppet module having
        parameters
        2. Update existing class parameters with different value and type

    :expectedresults: The parameters are updated with different data types
    """
    target_sat = module_puppet_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        target_sat.create_custom_environment(repo='api_test_classparameters')

        for index, data in enumerate(VALID_SC_PARAMS_DATA):
            sc_param = target_sat.api.SmartClassParameters().search(
                query={'search': f'parameter="api_classparameters_scp_00{index + 1}"'}
            )[0]

            sc_param.override = True
            sc_param.parameter_type = data['sc_type']
            sc_param.default_value = data['value']
            sc_param.update(['override', 'parameter_type', 'default_value'])
            sc_param = sc_param.read()

            assert sc_param.parameter_type == data['sc_type']
            _validate_value(data, sc_param)

        sat_upgrade.ready()
        target_sat._swap_nailgun(settings.upgrade.to_version)
        target_sat._session = None
        yield target_sat


@pytest.mark.puppet_upgrades
@pytest.mark.parametrize(
    'sc_data',
    [p for p in enumerate(VALID_SC_PARAMS_DATA)],
    ids=range(1, len(VALID_SC_PARAMS_DATA) + 1),
)
def test_post_puppet_class_parameter_data_and_type(
    module_puppet_class_parameter_data_and_type_setup, sc_data
):
    """Puppet Class Parameters value and type is intact post upgrade

    :id: postupgrade-08012f39-240b-40df-b893-2ee767129737

    :parametrized: yes

    :steps:

        1. In Preupgrade Satellite, Import a puppet module having parameters
        2. Update existing class parameters with different value and type
        3. Upgrade the satellite to next/latest version
        4. Postupgrade, Verify the data and type of updated parameters

    :expectedresults: The puppet class parameters data and type should be
        intact post upgrade
    """
    target_sat = module_puppet_class_parameter_data_and_type_setup
    index, my_param = sc_data
    sc_param = target_sat.api.SmartClassParameters().search(
        query={'search': f'parameter="api_classparameters_scp_00{index + 1}"'}
    )[0]
    assert sc_param.parameter_type == my_param['sc_type']
    _validate_value(my_param, sc_param)
