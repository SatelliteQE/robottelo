"""Test class for Global parameters CLI

:Requirement: Globalparam

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Parameters

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
from functools import partial

import pytest
from fauxfactory import gen_string

from robottelo.cli.globalparam import GlobalParameter


pytestmark = [pytest.mark.tier1]


@pytest.mark.upgrade
def test_positive_list_delete_by_name():
    """Test Global Param List

    :id: 8dd6c4e8-4ec9-4bee-8a04-f5788960973a

    :expectedresults: Global Param is set, listed, and deleted by name
    """
    alphastring = partial(gen_string, 'alpha', 10)

    name = f'opt-{alphastring()}'
    value = f'val-{alphastring()} {alphastring()}'

    # Create
    GlobalParameter().set({'name': name, 'value': value})

    # List by name
    result = GlobalParameter().list({'search': name})
    assert len(result) == 1
    assert result[0]['value'] == value

    # Delete
    GlobalParameter().delete({'name': name})
    assert len(GlobalParameter().list({'search': name})) == 0
