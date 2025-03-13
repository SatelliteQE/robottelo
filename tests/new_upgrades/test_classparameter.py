"""Test Puppet Class Parameter related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: Puppet

:Team: Rocket

:CaseImportance: High

"""

import json
import os
from time import sleep

from box import Box
import pytest

from robottelo.utils.shared_resource import SharedResource


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


@pytest.fixture(params=[1, 2, 3, 4, 5, 6, 7, 8, 9])
def puppet_class_parameter_data_and_type_setup(
    puppet_upgrade_shared_satellite, upgrade_action, request
):
    """Puppet Class parameters with different data type are created

    :steps:

        1. In Preupgrade Satellite, Import a puppet module having
        parameters
        2. Update existing class parameters with different value and type

    :expectedresults: The parameters are updated with different data types
    """
    target_sat = puppet_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_data = Box(
            {
                'target_sat': target_sat,
                'count': None,
            }
        )
        repo = 'api_test_classparameters'
        # Hitting the import_puppetclasses API endpoint multiple times at once causes frequent
        # 500 ISE errors, so stagger execution of the `create_custom_environment` method. The
        # Xdist worker number is used as the basis for the splay because a random splay could
        # still cause collisions. Since the first worker number is 0, we need to add 1 to the
        # Xdist worker number before multiplying by the length of the splay.
        xdist_worker_splay = (int(os.environ.get("PYTEST_XDIST_WORKER")[-1]) + 1) * 20
        sleep(xdist_worker_splay)
        env_name = target_sat.create_custom_environment(repo=repo)
        puppet_class = target_sat.api.PuppetClass().search(
            query={'search': f'name = "{repo}" and environment = "{env_name}"'}
        )[0]
        data = _valid_sc_parameters_data()[request.param - 1]
        sc_param = target_sat.api.SmartClassParameters().search(
            query={'search': f'parameter="api_classparameters_scp_00{request.param}"'}
        )[0]
        sc_param.override = True
        sc_param.parameter_type = data['sc_type']
        sc_param.default_value = data['value']
        sc_param.update(['override', 'parameter_type', 'default_value'])
        sc_param = sc_param.read()
        assert sc_param.parameter_type == data['sc_type']
        _validate_value(data, sc_param)
        test_data.puppet_class = puppet_class.name
        test_data.count = request.param
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.puppet_upgrades
def test_post_puppet_class_parameter_data_and_type(
    puppet_class_parameter_data_and_type_setup,
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
    target_sat = puppet_class_parameter_data_and_type_setup.target_sat
    count = puppet_class_parameter_data_and_type_setup.count
    data = _valid_sc_parameters_data()[count - 1]
    sc_param = target_sat.api.SmartClassParameters().search(
        query={'search': f'parameter="api_classparameters_scp_00{count}"'}
    )[0]
    assert sc_param.parameter_type == data['sc_type']
    _validate_value(data, sc_param)
