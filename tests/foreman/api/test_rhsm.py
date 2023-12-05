"""Tests for the ``rhsm`` paths.

No API doc exists for the subscription manager path(s). However, bugzilla bug
1112802 provides some relevant information.


:Requirement: Rhsm

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: SubscriptionManagement

:team: Phoenix-subscriptions

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import http

from nailgun import client
import pytest

from robottelo.config import get_credentials, get_url


@pytest.mark.tier1
@pytest.mark.pit_server
def test_positive_path():
    """Check whether the path exists.

    :id: a8706cb7-549b-4426-9bd9-4beecc33c797

    :expectedresults: Issuing an HTTP GET produces an HTTP 200 response
        with an ``application/json`` content-type, and the response is a
        list.

    :BZ: 1112802

    :customerscenario: true

    :CaseImportance: Critical
    """
    path = f'{get_url()}/rhsm'
    response = client.get(path, auth=get_credentials(), verify=False)
    assert response.status_code == http.client.OK
    assert 'application/json' in response.headers['content-type']
    assert isinstance(response.json(), list)
