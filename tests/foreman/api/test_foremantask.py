"""Tests for the ``foreman_tasks/api/v2/tasks`` path.

:Requirement: Foremantask

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: TasksPlugin

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities
from requests.exceptions import HTTPError


@pytest.mark.tier1
def test_negative_fetch_non_existent_task():
    """Fetch a non-existent task.

    :id: a2a81ca2-63c4-47f5-9314-5852f5e2617f

    :expectedresults: An HTTP 4XX or 5XX message is returned.

    :CaseImportance: Critical
    """
    with pytest.raises(HTTPError):
        entities.ForemanTask(id='abc123').read()


@pytest.mark.tier1
@pytest.mark.upgrade
@pytest.mark.e2e
def test_positive_get_summary():
    """Get a summary of foreman tasks.

    :id: bdcab413-a25d-4fe1-9db4-b50b5c31ebce

    :expectedresults: A list of dicts is returned.

    :CaseImportance: Critical
    """
    summary = entities.ForemanTask().summary()
    assert type(summary) is list
    for item in summary:
        assert type(item) is dict
