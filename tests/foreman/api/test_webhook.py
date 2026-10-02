"""Test class for Webhook API

:Requirement: Webhook

:CaseAutomation: Automated

:CaseComponent: HooksandWebhooks

:Team: Endeavour

:CaseImportance: High

"""

import pytest


class TestWebhook:
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
