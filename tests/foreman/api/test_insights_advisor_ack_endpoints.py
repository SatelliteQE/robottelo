"""Robottelo replication of the Advisor ack/hostack API endpoints.

Covers ``ack`` list/create/retrieve/update/destroy, ``hostack``
list/create/retrieve/update/destroy, and the bulk
``rule/{rule_id}/ack_hosts`` mutation. This is a timeboxed replication to
gauge the effort of hand-writing these tests before deciding whether to
replicate further Advisor/Vulnerability endpoints this way.

These are plain Robottelo API tests: calls go through ``nailgun.client``
against Foreman's ``insights_cloud`` Advisor proxy (see
``robottelo.iop.connector``), the same pattern used elsewhere in this repo
for routes without a nailgun entity wrapper. No external/internal test
framework is used or depended on here.

:Method note: the upstream Insights Advisor API documentation for the
ack-collection "create" action lists its HTTP method as ``DELETE``, but its
description text reads "Add an acknowledgement for a rule... a new ack is
created" (a POST/create action). Cross-checked against
``ForemanRhCloud::InsightsApiForwarder``'s own permission map (``POST
/api/insights/v1/ack/`` requires ``edit_advisor``, with no DELETE entry for
the collection route). Treated as a documentation error;
``test_positive_ack_create`` below tests the real POST semantics.

:Note (being worked on): mutating calls through the ``insights_cloud`` proxy
(``InsightsCloud::UIRequestsController``) currently return a CSRF-related 422
for token-authenticated callers, since that controller inherits Rails'
browser-session CSRF protection rather than Foreman's CSRF-exempt API
controller base. A fix is in progress in ``foreman_rh_cloud``. These tests
assert the correct, expected business behavior so they read as valid
regression tests once that fix lands, rather than needing a rewrite.

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:Team: Proton

:CaseImportance: Medium

"""

import http

from nailgun import client
import pytest

from robottelo.iop.connector import advisor_request_kwargs, advisor_url

# Known-valid Advisor rule ID used across this module's lifecycle checks.
RULE_ID = 'network_ipv6_dev_route_crash|NETWORK_IPV6_DEV_ROUTE_CRASH'

# Placeholder inventory/system UUID for hostack/ack_hosts scenarios. Must be
# replaced with a real host inventory UUID registered on the target Foreman
# instance (a host with an Insights upload that triggered RULE_ID above);
# unlike RULE_ID this isn't a stable, environment-independent value.
SYSTEM_UUID = 'REPLACE_WITH_REAL_INVENTORY_UUID'

# Prototype simplification: Default Organization's ID. A non-prototype
# version should create/use a dedicated test organization via target_sat
# fixtures.
DEFAULT_ORGANIZATION_ID = 1


@pytest.fixture
def advisor_kwargs():
    return advisor_request_kwargs()


def _url(*segments):
    return advisor_url(*segments, organization_id=DEFAULT_ORGANIZATION_ID)


def test_positive_ack_list(advisor_kwargs):
    """List account-wide Advisor acks for an org.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c01

    :steps:
        1. GET /api/insights/v1/ack/ through the Foreman proxy.

    :expectedresults: The call succeeds and returns a paginated ack list
        whose declared count matches the number of items returned.
    """
    response = client.get(_url('ack'), **advisor_kwargs)
    assert response.status_code == http.client.OK
    body = response.json()
    assert body['meta']['count'] == len(body['data'])


def test_positive_ack_create(advisor_kwargs):
    """Create an account-wide ack for a rule.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c02

    :steps:
        1. POST /api/insights/v1/ack/ with a rule ID and justification.

    :expectedresults: The ack is created and the response echoes the
        acknowledged rule ID.

    :CaseImportance: Medium
    """
    try:
        response = client.post(
            _url('ack'),
            data={'rule_id': RULE_ID, 'justification': 'Robottelo ack coverage'},
            **advisor_kwargs,
        )
        assert response.status_code == http.client.CREATED
        assert response.json()['rule'] == RULE_ID
    finally:
        client.delete(_url('ack', RULE_ID), **advisor_kwargs)


def test_positive_ack_retrieve(advisor_kwargs):
    """Display a specific account-wide ack for a rule.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c03

    :steps:
        1. Create an ack for a rule.
        2. GET /api/insights/v1/ack/{rule_id}/ for that rule.

    :expectedresults: The retrieved ack matches the rule that was acked.
    """
    client.post(
        _url('ack'),
        data={'rule_id': RULE_ID, 'justification': 'Robottelo ack coverage'},
        **advisor_kwargs,
    )
    try:
        response = client.get(_url('ack', RULE_ID), **advisor_kwargs)
        assert response.status_code == http.client.OK
        assert response.json()['rule'] == RULE_ID
    finally:
        client.delete(_url('ack', RULE_ID), **advisor_kwargs)


def test_positive_ack_update(advisor_kwargs):
    """Update the justification on an existing account-wide ack.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c04

    :steps:
        1. Create an ack for a rule with an initial justification.
        2. PUT /api/insights/v1/ack/{rule_id}/ with a new justification.

    :expectedresults: The ack's justification is updated to the new value.
    """
    client.post(
        _url('ack'),
        data={'rule_id': RULE_ID, 'justification': 'initial justification'},
        **advisor_kwargs,
    )
    try:
        response = client.put(
            _url('ack', RULE_ID),
            data={'justification': 'updated justification'},
            **advisor_kwargs,
        )
        assert response.status_code == http.client.OK
        assert response.json()['justification'] == 'updated justification'
    finally:
        client.delete(_url('ack', RULE_ID), **advisor_kwargs)


def test_positive_ack_destroy(advisor_kwargs):
    """Delete an account-wide ack for a rule.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c05

    :steps:
        1. Create an ack for a rule.
        2. DELETE /api/insights/v1/ack/{rule_id}/ for that rule.
        3. Attempt to retrieve the same rule's ack again.

    :expectedresults: The delete succeeds, and the ack no longer exists.
    """
    client.post(
        _url('ack'),
        data={'rule_id': RULE_ID, 'justification': 'Robottelo ack coverage'},
        **advisor_kwargs,
    )
    delete_response = client.delete(_url('ack', RULE_ID), **advisor_kwargs)
    assert delete_response.status_code == http.client.NO_CONTENT
    retrieve_response = client.get(_url('ack', RULE_ID), **advisor_kwargs)
    assert retrieve_response.status_code == http.client.NOT_FOUND


def test_positive_hostack_list(advisor_kwargs):
    """List host-specific Advisor acks.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c06

    :steps:
        1. GET /api/insights/v1/hostack/ through the Foreman proxy.

    :expectedresults: The call succeeds and returns a paginated hostack list
        whose declared count matches the number of items returned.
    """
    response = client.get(_url('hostack'), **advisor_kwargs)
    assert response.status_code == http.client.OK
    body = response.json()
    assert body['meta']['count'] == len(body['data'])


def test_positive_hostack_create(advisor_kwargs):
    """Create a host-specific ack for a rule.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c07

    :steps:
        1. POST /api/insights/v1/hostack/ with a rule, a system UUID, and a
           justification.

    :expectedresults: The hostack is created and the response echoes the
        acknowledged rule and system.
    """
    host_ack_id = None
    try:
        response = client.post(
            _url('hostack'),
            data={
                'rule': RULE_ID,
                'system_uuid': SYSTEM_UUID,
                'justification': 'Robottelo hostack coverage',
            },
            **advisor_kwargs,
        )
        assert response.status_code == http.client.CREATED
        body = response.json()
        assert body['rule'] == RULE_ID
        assert body['system_uuid'] == SYSTEM_UUID
        host_ack_id = body['id']
    finally:
        if host_ack_id is not None:
            client.delete(_url('hostack', host_ack_id), **advisor_kwargs)


def test_positive_hostack_retrieve(advisor_kwargs):
    """Display a specific host-specific ack.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c08

    :steps:
        1. Create a hostack.
        2. GET /api/insights/v1/hostack/{id}/ for that hostack's ID.

    :expectedresults: The retrieved hostack matches what was created.
    """
    created = client.post(
        _url('hostack'),
        data={
            'rule': RULE_ID,
            'system_uuid': SYSTEM_UUID,
            'justification': 'Robottelo hostack coverage',
        },
        **advisor_kwargs,
    ).json()
    try:
        response = client.get(_url('hostack', created['id']), **advisor_kwargs)
        assert response.status_code == http.client.OK
        body = response.json()
        assert body['id'] == created['id']
        assert body['rule'] == RULE_ID
    finally:
        client.delete(_url('hostack', created['id']), **advisor_kwargs)


def test_positive_hostack_update(advisor_kwargs):
    """Update the justification on an existing hostack.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c09

    :steps:
        1. Create a hostack with an initial justification.
        2. PUT /api/insights/v1/hostack/{id}/ with a new justification.

    :expectedresults: The hostack's justification is updated to the new
        value.
    """
    created = client.post(
        _url('hostack'),
        data={
            'rule': RULE_ID,
            'system_uuid': SYSTEM_UUID,
            'justification': 'initial justification',
        },
        **advisor_kwargs,
    ).json()
    try:
        response = client.put(
            _url('hostack', created['id']),
            data={'id': created['id'], 'justification': 'updated justification'},
            **advisor_kwargs,
        )
        assert response.status_code == http.client.OK
        assert response.json()['justification'] == 'updated justification'
    finally:
        client.delete(_url('hostack', created['id']), **advisor_kwargs)


def test_positive_hostack_destroy(advisor_kwargs):
    """Delete a host-specific ack.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c10

    :steps:
        1. Create a hostack.
        2. DELETE /api/insights/v1/hostack/{id}/ for that hostack's ID.
        3. Attempt to retrieve the same hostack again.

    :expectedresults: The delete succeeds, and the hostack no longer exists.
    """
    created = client.post(
        _url('hostack'),
        data={
            'rule': RULE_ID,
            'system_uuid': SYSTEM_UUID,
            'justification': 'Robottelo hostack coverage',
        },
        **advisor_kwargs,
    ).json()
    delete_response = client.delete(_url('hostack', created['id']), **advisor_kwargs)
    assert delete_response.status_code == http.client.NO_CONTENT
    retrieve_response = client.get(_url('hostack', created['id']), **advisor_kwargs)
    assert retrieve_response.status_code == http.client.NOT_FOUND


def test_positive_rule_ack_hosts_create(advisor_kwargs):
    """Bulk-ack one or more hosts against a single rule.

    :id: 6e1d6f3d-4c5a-4e7e-9f3b-6f7a2b7e1c11

    :steps:
        1. POST /api/insights/v1/rule/{rule_id}/ack_hosts/ with a list of
           system UUIDs and a justification.

    :expectedresults: The hosts are acknowledged for the rule, and the
        response reports the count of created host acks.

    :CaseImportance: Medium
    """
    try:
        response = client.post(
            _url('rule', RULE_ID, 'ack_hosts'),
            data={'systems': [SYSTEM_UUID], 'justification': 'Robottelo bulk ack coverage'},
            **advisor_kwargs,
        )
        assert response.status_code == http.client.OK
        body = response.json()
        assert body['count'] == 1
        assert SYSTEM_UUID in body['host_ids']
    finally:
        # /rule/{rule_id}/unack_hosts/ isn't itself in scope for this batch;
        # used here purely as cleanup for the host ack created above.
        client.post(
            _url('rule', RULE_ID, 'unack_hosts'),
            data={'systems': [SYSTEM_UUID]},
            **advisor_kwargs,
        )
