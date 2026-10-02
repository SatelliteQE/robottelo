"""Test class for Webhook API

:Requirement: Webhook

:CaseAutomation: Automated

:CaseComponent: HooksandWebhooks

:Team: Endeavour

:CaseImportance: High

"""

from http.client import parse_headers
from io import BytesIO
import json
import uuid

import pytest
from wait_for import wait_for

from robottelo.logging import logger

WEBHOOK_LISTENER_PORT = 9999


@pytest.fixture
def webhook_listener(target_sat):
    """Start a netcat listener on the Satellite host to capture webhook requests."""
    output_file = f'/tmp/webhook-test-{uuid.uuid4()}'
    target_sat.execute(f'nohup nc -l {WEBHOOK_LISTENER_PORT} > {output_file} 2>&1 &')

    def listener_ready():
        result = target_sat.execute(f'ss -ltn "sport = :{WEBHOOK_LISTENER_PORT}"')
        return str(WEBHOOK_LISTENER_PORT) in result.stdout

    wait_for(listener_ready, timeout=10, delay=0.5)

    yield output_file

    target_sat.execute(f'fuser -k {WEBHOOK_LISTENER_PORT}/tcp 2>/dev/null || true')
    target_sat.execute(f'rm -f {output_file}')


@pytest.fixture
def webhook(target_sat):
    """Create a webhook and ensure it's deleted after the test."""
    hooks = []

    def _create(**kwargs):
        hook = target_sat.api.Webhooks(**kwargs).create()
        hooks.append(hook)
        return hook

    yield _create

    for hook in hooks:
        hook.delete()


class TestWebhook:
    @pytest.mark.e2e
    @pytest.mark.parametrize('setting_update', ['safemode_render=False'], indirect=True)
    def test_positive_event_triggered(self, target_sat, setting_update, webhook, webhook_listener):
        """Create a webhook and trigger the event associated with it.

        :id: 9c0cb060-c171-4f40-8f3a-6645967b5782

        :expectedresults: Event trigger makes a call to the specified url, and the
            request payload received by the listener matches the triggered event.

        :CaseImportance: Critical
        """
        hook = webhook(
            event='user_created.event.foreman',
            http_method='POST',
            target_url=f'http://host.containers.internal:{WEBHOOK_LISTENER_PORT}',
        )
        target_sat.api.User().create()

        def captured_payload():
            content = target_sat.execute(f'cat {webhook_listener}').stdout
            request = BytesIO(content.encode())
            request.readline()  # Skip the HTTP request line.
            parse_headers(request)
            try:
                return json.load(request)
            except json.JSONDecodeError:
                # The listener may have written only headers or part of the JSON body.
                return False

        payload = wait_for(
            captured_payload,
            timeout=30,
            delay=1,
            logger=logger,
        ).out

        assert payload.get('webhook_id') == hook.id, (
            f'Payload does not reference webhook {hook.id}: {payload}'
        )
        assert payload.get('event_name') == 'user_created.event.foreman', (
            f'Payload does not reference the triggered event: {payload}'
        )

        # must_succeed=False: nc dumps the raw request to a file but never sends an HTTP response, so Foreman always records the delivery task as a 'warning'
        target_sat.wait_for_tasks(f'Deliver webhook {hook.name}', must_succeed=False)

    @pytest.mark.parametrize('setting_update', ['safemode_render=False'], indirect=True)
    def test_negative_event_task_failed(self, target_sat, setting_update, webhook):
        """Create a webhook with unreachable target and assert the associated task
        failed

        :id: d4a49556-9413-46e8-bcb5-7afd0184bdb2

        :expectedresults: Deliver webhook task fails

        :CaseImportance: High
        """
        hook = webhook(
            event='user_created.event.foreman',
            http_method='GET',
            target_url="http://localhost/target",
        )
        target_sat.api.User().create()
        target_sat.wait_for_tasks(f'Deliver webhook {hook.name}', must_succeed=False)
