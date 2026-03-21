"""Test class for Webhook API

:Requirement: Webhook

:CaseAutomation: Automated

:CaseComponent: HooksandWebhooks

:Team: Endeavour

:CaseImportance: High

"""

import pytest
from requests.exceptions import HTTPError

from robottelo.constants import WEBHOOK_EVENTS, WEBHOOK_METHODS
from robottelo.utils.datafactory import parametrized


class TestWebhook:
    def test_negative_invalid_event(self, target_sat):
        """Test negative webhook creation with an invalid event

        :id: 60cd456a-9943-45cb-a72e-23a83a691499

        :expectedresults: Webhook is not created

        :CaseImportance: High
        """
        with pytest.raises(HTTPError):
            target_sat.api.Webhooks(event='invalid_event').create()

    @pytest.mark.parametrize('event', WEBHOOK_EVENTS)
    def test_positive_valid_event(self, event, target_sat):
        """Test positive webhook creation with a valid event

        :id: 9b505f1b-7ee1-4362-b44c-f3107d043a05

        :expectedresults: Webhook is created with event specified

        :CaseImportance: High
        """
        hook = target_sat.api.Webhooks(event=event).create()
        assert event in hook.event

    def test_negative_invalid_method(self, target_sat):
        """Test negative webhook creation with an invalid HTTP method

        :id: 573be312-7bf3-4d9e-aca1-e5cac810d04b

        :expectedresults: Webhook is not created

        :CaseImportance: High
        """
        with pytest.raises(HTTPError):
            target_sat.api.Webhooks(http_method='NONE').create()

    @pytest.mark.parametrize('method', **parametrized(WEBHOOK_METHODS))
    def test_positive_valid_method(self, method, target_sat):
        """Test positive webhook creation with a valid HTTP method

        :id: cf8f276a-d21e-44d0-92f2-657232240c7e

        :expectedresults: Webhook is created with specified method

        :CaseImportance: High
        """
        hook = target_sat.api.Webhooks(http_method=method).create()
        assert hook.http_method == method

    @pytest.mark.e2e
    def test_positive_end_to_end(self, target_sat):
        """Create a new webhook.

        :id: 7593a04e-cf7e-414c-9e7e-3fe2936cc32a

        :expectedresults: Webhook is created successfully.

        :CaseImportance: Critical
        """
        hook = target_sat.api.Webhooks().create()
        assert hook
        hook.name = "testing"
        hook.http_method = "GET"
        hook.target_url = "http://localhost/updated_url"
        hook.update(['name', 'http_method', 'target_url'])
        assert hook.name == "testing"
        assert hook.http_method == "GET"
        assert hook.target_url == "http://localhost/updated_url"
        hook.delete()
        with pytest.raises(HTTPError):
            hook.read()

    @pytest.mark.e2e
    @pytest.mark.parametrize('setting_update', ['safemode_render=False'], indirect=True)
    def test_positive_event_triggered(self, target_sat, setting_update):
        """Create a webhook and trigger the event
        associated with it.

        :id: 9c0cb060-c171-4f40-8f3a-6645967b5782

        :expectedresults: Event trigger makes a call to
            the specified url.

        :CaseImportance: Critical
        """
        hook = target_sat.api.Webhooks(
            event='user_created',
            http_method='GET',
            target_url=f'https://{target_sat.hostname}',
        ).create()
        target_sat.api.User().create()
        target_sat.wait_for_tasks(f'Deliver webhook {hook.name}')

    @pytest.mark.parametrize('setting_update', ['safemode_render=False'], indirect=True)
    def test_negative_event_task_failed(self, target_sat, setting_update):
        """Create a webhook with unreachable target and assert the associated task
        failed

        :id: d4a49556-9413-46e8-bcb5-7afd0184bdb2

        :expectedresults: Deliver webhook task fails

        :CaseImportance: High
        """
        hook = target_sat.api.Webhooks(
            event='user_created',
            http_method='GET',
            target_url="http://localhost/target",
        ).create()
        target_sat.api.User().create()
        target_sat.wait_for_tasks(f'Deliver webhook {hook.name}', must_succeed=False)
