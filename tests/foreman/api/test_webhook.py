"""Test class for Webhook API

:Requirement: Webhook

:CaseAutomation: Automated

:CaseComponent: HooksandWebhooks

:Team: Endeavour

:CaseImportance: High

"""

import re

import pytest
from requests.exceptions import HTTPError
from wait_for import TimedOutError, wait_for

from robottelo.config import settings
from robottelo.constants import WEBHOOK_EVENTS, WEBHOOK_METHODS
from robottelo.logging import logger
from robottelo.utils.datafactory import parametrized


def _read_log(ch, pattern):
    """Read the first line from the given channel buffer and return the matching line"""
    # read lines until the buffer is empty
    for log_line in ch.stdout().splitlines():
        logger.debug(f'foreman-tail: {log_line}')
        if re.search(pattern, log_line):
            return log_line
    else:
        return None


def _wait_for_log(channel, pattern, timeout=2, delay=0.2):
    """_read_log method enclosed in wait_for method"""
    matching_log = wait_for(
        _read_log,
        func_args=(
            channel,
            pattern,
        ),
        fail_condition=None,
        timeout=timeout,
        delay=delay,
        logger=logger,
    )
    return matching_log.out


def assert_event_triggered(channel, event):
    """Reads foreman logs until event trigger message is found"""
    pattern = f'ForemanWebhooks::EventSubscriber: {event} event received'
    try:
        log = _wait_for_log(channel, pattern)
        assert pattern in log
    except TimedOutError as err:
        raise AssertionError(f'Timed out waiting for {pattern} from VM') from err


class TestWebhook:
    @pytest.mark.tier2
    def test_negative_invalid_event(self, target_sat):
        """Test negative webhook creation with an invalid event

        :id: 60cd456a-9943-45cb-a72e-23a83a691499

        :expectedresults: Webhook is not created

        :CaseImportance: High
        """
        with pytest.raises(HTTPError):
            target_sat.api.Webhooks(event='invalid_event').create()

    @pytest.mark.tier2
    @pytest.mark.parametrize('event', WEBHOOK_EVENTS)
    def test_positive_valid_event(self, event, target_sat):
        """Test positive webhook creation with a valid event

        :id: 9b505f1b-7ee1-4362-b44c-f3107d043a05

        :expectedresults: Webhook is created with event specified

        :CaseImportance: High
        """
        hook = target_sat.api.Webhooks(event=event).create()
        assert event in hook.event

    @pytest.mark.tier2
    def test_negative_invalid_method(self, target_sat):
        """Test negative webhook creation with an invalid HTTP method

        :id: 573be312-7bf3-4d9e-aca1-e5cac810d04b

        :expectedresults: Webhook is not created

        :CaseImportance: High
        """
        with pytest.raises(HTTPError):
            target_sat.api.Webhooks(http_method='NONE').create()

    @pytest.mark.tier2
    @pytest.mark.parametrize('method', **parametrized(WEBHOOK_METHODS))
    def test_positive_valid_method(self, method, target_sat):
        """Test positive webhook creation with a valid HTTP method

        :id: cf8f276a-d21e-44d0-92f2-657232240c7e

        :expectedresults: Webhook is created with specified method

        :CaseImportance: High
        """
        hook = target_sat.api.Webhooks(http_method=method).create()
        assert hook.http_method == method

    @pytest.mark.tier1
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

    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    @pytest.mark.tier2
    @pytest.mark.e2e
    @pytest.mark.parametrize('setting_update', ['safemode_render=False'], indirect=True)
    def test_positive_event_triggered(self, module_org, target_sat, setting_update):
        """Create a webhook and trigger the event
        associated with it.

        :id: 9c0cb060-c171-4f40-8f3a-6645967b5782

        :expectedresults: Event trigger makes a call to
            the specified url.

        :CaseImportance: Critical
        """
        hook = target_sat.api.Webhooks(
            event='actions.katello.repository.sync_succeeded',
            http_method='GET',
            target_url=settings.repos.yum_0.url,
        ).create()
        repo = target_sat.api.Repository(
            organization=module_org, content_type='yum', url=settings.repos.yum_0.url
        ).create()
        with target_sat.session.shell() as shell:
            shell.send('foreman-tail')
            repo.sync()
            assert_event_triggered(shell, hook.event)
        target_sat.wait_for_tasks(f'Deliver webhook {hook.name}')

    @pytest.mark.parametrize('setting_update', ['safemode_render=False'], indirect=True)
    def test_negative_event_task_failed(self, module_org, target_sat, setting_update):
        """Create a webhook with unreachable target and assert the associated task
        failed

        :id: d4a49556-9413-46e8-bcb5-7afd0184bdb2

        :expectedresults: Deliver webhook task fails

        :CaseImportance: High
        """
        hook = target_sat.api.Webhooks(
            event='actions.katello.repository.sync_succeeded',
            http_method='GET',
            target_url="http://localhost/target",
        ).create()
        repo = target_sat.api.Repository(
            organization=module_org, content_type='yum', url=settings.repos.yum_0.url
        ).create()
        with target_sat.session.shell() as shell:
            shell.send('foreman-tail')
            repo.sync()
            assert_event_triggered(shell, hook.event)
        target_sat.wait_for_tasks(f'Deliver webhook {hook.name}', must_succeed=False)
