"""Test class for Webhook API

:Requirement: Webhook

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Webhooks

:Assignee: gsulliva

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import re

import pytest
from nailgun import entities
from requests.exceptions import HTTPError
from wait_for import TimedOutError
from wait_for import wait_for

from robottelo.config import settings
from robottelo.constants import WEBHOOK_EVENTS
from robottelo.constants import WEBHOOK_METHODS
from robottelo.datafactory import parametrized
from robottelo.logging import logger


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
    except TimedOutError:
        raise AssertionError(f'Timed out waiting for {pattern} from VM')


class TestWebhook:
    @pytest.mark.tier2
    def test_negative_invalid_event(self):
        """Test negative webhook creation with an invalid event

        :id: 60cd456a-9943-45cb-a72e-23a83a691499

        :expectedresults: Webhook is not created

        :CaseImportance: High
        """
        with pytest.raises(HTTPError):
            entities.Webhooks(event='invalid_event').create()

    @pytest.mark.tier2
    @pytest.mark.parametrize('event', **parametrized(WEBHOOK_EVENTS))
    def test_positive_valid_event(self, event):
        """Test positive webhook creation with a valid event

        :id: 9b505f1b-7ee1-4362-b44c-f3107d043a05

        :expectedresults: Webhook is created with event specified

        :CaseImportance: High
        """
        hook = entities.Webhooks(event=event).create()
        assert event in hook.event

    @pytest.mark.tier2
    def test_negative_invalid_method(self):
        """Test negative webhook creation with an invalid HTTP method

        :id: 573be312-7bf3-4d9e-aca1-e5cac810d04b

        :expectedresults: Webhook is not created

        :CaseImportance: High
        """
        with pytest.raises(HTTPError):
            entities.Webhooks(http_method='NONE').create()

    @pytest.mark.tier2
    @pytest.mark.parametrize('method', **parametrized(WEBHOOK_METHODS))
    def test_positive_valid_method(self, method):
        """Test positive webhook creation with a valid HTTP method

        :id: cf8f276a-d21e-44d0-92f2-657232240c7e

        :expectedresults: Webhook is created with specified method

        :CaseImportance: High
        """
        hook = entities.Webhooks(http_method=method).create()
        assert hook.http_method == method

    @pytest.mark.tier1
    def test_positive_end_to_end(self):
        """Create a new webhook.

        :id: 7593a04e-cf7e-414c-9e7e-3fe2936cc32a

        :expectedresults: Webhook is created successfully.

        :CaseImportance: Critical
        """
        hook = entities.Webhooks().create()
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
    def test_positive_event_triggered(self, module_org, target_sat):
        """Create a webhook and trigger the event
        associated with it.

        :id: 9c0cb060-c171-4f40-8f3a-6645967b5782

        :expectedresults: Event trigger makes a call to
            the specified url.

        :CaseImportance: Critical
        """
        hook = entities.Webhooks(
            event='actions.katello.repository.sync_succeeded', http_method='GET'
        ).create()
        repo = entities.Repository(
            organization=module_org, content_type='yum', url=settings.repos.yum_0.url
        ).create()
        with target_sat.session.shell() as shell:
            shell.send('foreman-tail')
            repo.sync()
            assert_event_triggered(shell, hook.event)
