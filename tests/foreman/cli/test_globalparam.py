"""Test class for Global parameters CLI

:Requirement: Globalparam

:CaseAutomation: Automated

:CaseComponent: Parameters

:Team: Rocket

:CaseImportance: Critical

"""

from functools import partial

from fauxfactory import gen_string
import pytest

pytestmark = [pytest.mark.tier1]


@pytest.mark.upgrade
def test_positive_list_delete_by_name(module_target_sat):
    """Test Global Param List

    :id: 8dd6c4e8-4ec9-4bee-8a04-f5788960973a

    :expectedresults: Global Param is set, listed, and deleted by name
    """
    alphastring = partial(gen_string, 'alpha', 10)

    name = f'opt-{alphastring()}'
    value = f'val-{alphastring()} {alphastring()}'

    # Create
    module_target_sat.cli.GlobalParameter().set({'name': name, 'value': value})

    # List by name
    result = module_target_sat.cli.GlobalParameter().list({'search': name})
    assert len(result) == 1
    assert result[0]['value'] == value

    # Delete
    module_target_sat.cli.GlobalParameter().delete({'name': name})
    assert len(module_target_sat.cli.GlobalParameter().list({'search': name})) == 0
