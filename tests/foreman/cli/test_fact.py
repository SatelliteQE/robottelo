"""Test class for Fact  CLI

:Requirement: Fact

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Fact

:Assignee: rmynar

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.cli.fact import Fact


pytestmark = [pytest.mark.tier1]


@pytest.mark.upgrade
@pytest.mark.parametrize(
    'fact', ['uptime', 'os::family', 'uptime_seconds', 'memorysize', 'ipaddress']
)
def test_positive_list_by_name(fact):
    """Test Fact List

    :id: 83794d97-d21b-4482-9522-9b41053e595f

    :expectedresults: Fact List is displayed

    :parametrized: yes
    """
    facts = Fact().list(options={'search': f'fact={fact}'})
    assert facts[0]['fact'] == fact


@pytest.mark.parametrize('fact', ['uptime_days', 'memoryfree'])
def test_negative_list_ignored_by_name(fact):
    """Test Fact List

    :id: b6375f39-b8c3-4807-b04b-b0e43644441f

    :expectedresults: Ignored fact is not listed

    :parametrized: yes
    """
    assert Fact().list(options={'search': f'fact={fact}'}) == []


def test_negative_list_by_name():
    """Test Fact List failure

    :id: bd56d27e-59c0-4f35-bd53-2999af7c6946

    :expectedresults: Fact List is not displayed
    """
    assert Fact().list(options={'search': f'fact={gen_string("alpha")}'}) == []
