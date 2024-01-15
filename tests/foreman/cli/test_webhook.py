"""Test class for Webhook CLI

:Requirement: Webhook

:CaseAutomation: Automated

:CaseComponent: HooksandWebhooks

:Team: Endeavour

:CaseImportance: High

"""
from functools import partial
from random import choice

from box import Box
from fauxfactory import gen_alphanumeric
import pytest

from robottelo.constants import WEBHOOK_EVENTS, WEBHOOK_METHODS
from robottelo.exceptions import CLIReturnCodeError


@pytest.fixture
def webhook_factory(request, class_org, class_location, class_target_sat):
    def _create_webhook(org, loc, options=None):
        """Function for creating a new Webhook

        Returns a Box representation of a Webhook
        """
        options = options or {}
        if not any(options.get(key) for key in ['organizations', 'organization-ids']):
            options['organization-id'] = org.id
        if not any(options.get(key) for key in ['locations', 'locations-ids']):
            options['location-id'] = loc.id
        if options.get('name') is None:
            options['name'] = gen_alphanumeric()
        if options.get('event') is None:
            options['event'] = choice(WEBHOOK_EVENTS)
        if options.get('http-method') is None:
            options['http-method'] = choice(WEBHOOK_METHODS)
        if options.get('target-url') is None:
            options['target-url'] = 'http://localhost/some-path'

        return Box(class_target_sat.cli.Webhook.create(options))

    return partial(_create_webhook, org=class_org, loc=class_location)


def assert_created(options, hook):
    for option in options.items():
        if option[0] not in ['event', 'organization-id', 'location-id']:
            assert hook[option[0]] == option[1]


class TestWebhook:
    @pytest.mark.tier3
    @pytest.mark.e2e
    def test_positive_end_to_end(self, webhook_factory, class_target_sat):
        """Test creation, list, update and removal of webhook

        :id: d893d176-cbe9-421b-8631-7c7a1a462ea5

        :CaseImportance: Critical
        """
        webhook_options = {
            'event': 'host_created',
            'http-method': WEBHOOK_METHODS[1],
        }
        webhook_item = webhook_factory(options=webhook_options)
        assert_created(webhook_options, webhook_item)
        # Event is defined in a webhook item as {event_name}.event.foreman
        # so we need to remove that postfix
        assert webhook_options['event'] == webhook_item['event'].rsplit('.', 2)[0]

        # Find webhook by name
        webhook_search = class_target_sat.cli.Webhook.info({'name': webhook_options['name']})
        # A non empty dict has been returned
        assert webhook_search

        # Test that webhook gets updated
        different_url = 'http://localhost/different-path'
        class_target_sat.cli.Webhook.update(
            {'name': webhook_options['name'], 'target-url': different_url}
        )
        webhook_search_after_update = class_target_sat.cli.Webhook.info(
            {'name': webhook_options['name']}
        )
        assert webhook_search_after_update['target-url'] == different_url

        # Test that webhook is deleted
        class_target_sat.cli.Webhook.delete({'name': webhook_options['name']})
        webhook_deleted_search = class_target_sat.cli.Webhook.list(
            {'search': webhook_options['name']}
        )
        assert len(webhook_deleted_search) == 0

    def test_webhook_disabled_enabled(self, webhook_factory, class_target_sat):
        """Test disable/enable the webhook

        :id: 4fef4320-0655-440d-90e7-150ffcdcd043

        :CaseImportance: High
        """
        hook = webhook_factory()

        # The new webhook is enabled by default on creation
        assert class_target_sat.cli.Webhook.info({'name': hook.name})['enabled'] == 'yes'

        class_target_sat.cli.Webhook.update({'name': hook.name, 'enabled': 'no'})
        # The webhook should be disabled now
        assert class_target_sat.cli.Webhook.info({'name': hook.name})['enabled'] == 'no'

        class_target_sat.cli.Webhook.update({'name': hook.name, 'enabled': 'yes'})
        # The webhook should be enabled again
        assert class_target_sat.cli.Webhook.info({'name': hook.name})['enabled'] == 'yes'

    def test_negative_update_invalid_url(self, webhook_factory, class_target_sat):
        """Test webhook negative update - invalid target URL fails

        :id: 7a6c87f5-0e6c-4a55-b495-b1bfb24607bd

        :expectedresults: Webhook is not updated

        :CaseImportance: High
        """
        hook = webhook_factory()

        invalid_url = '$%^##@***'
        with pytest.raises(CLIReturnCodeError):
            class_target_sat.cli.Webhook.update({'name': hook.name, 'target-url': invalid_url})
