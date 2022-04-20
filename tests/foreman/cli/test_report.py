"""Test class for Reports CLI.

:Requirement: Report

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: SCAPPlugin

:Assignee: jpathan

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.report import ConfigReport


@pytest.fixture(scope='module', autouse=True)
def run_puppet_agent(default_sat):
    """Retrieves the client configuration from the puppet master and
    applies it to the local host. This is required to make sure
    that we have reports available.
    """
    default_sat.execute('puppet agent -t')


@pytest.mark.tier1
def test_positive_info():
    """Test Info for Puppet report

    :id: 32646d4b-7101-421a-85e0-777d3c6b71ec

    :expectedresults: Puppet Report Info is displayed

    :CaseImportance: Critical
    """
    result = ConfigReport.list()
    assert len(result) > 0
    # Grab a random report
    report = random.choice(result)
    result = ConfigReport.info({'id': report['id']})
    assert report['id'] == result['id']


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete_by_id():
    """Check if Puppet Report can be deleted by its ID

    :id: bf918ec9-e2d4-45d0-b913-ab939b5d5e6a

    :expectedresults: Puppet Report is deleted

    :CaseImportance: Critical
    """
    result = ConfigReport.list()
    assert len(result) > 0
    # Grab a random report
    report = random.choice(result)
    ConfigReport.delete({'id': report['id']})
    with pytest.raises(CLIReturnCodeError):
        ConfigReport.info({'id': report['id']})
