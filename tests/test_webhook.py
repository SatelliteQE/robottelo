"""Test class for Activation key CLI

:Requirement: Webhook

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Webhook

:Assignee: rdrazny

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_alphanumeric

from robottelo.cli.base import CLIError
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.webhook import Webhook

# import robottelo.constants


class TestWebhook:
    @pytest.mark.tier2
    def test_negative_invalid_event(self):
        """Test negative webhook creation with an invalid event

        :id: 60cd456a-9943-45cb-a72e-23a83a691499

        :expectedresults: Webhook is not created

        :CaseImportance: High
        """
        with pytest.raises(CLIError) as exc_info:
            Webhook.create(
                {
                    'name': 'invalid-event-webhook',
                    'event': 'non-existent-even',
                    'target-url': 'http://localhost/bla',
                }
            )

    @pytest.mark.tier2
    def test_negative_invalid_method(self):
        """Test negative webhook creation with an invalid HTTP method

        :id: 573be312-7bf3-4d9e-aca1-e5cac810d04b

        :expectedresults: Webhook is not created

        :CaseImportance: High
        """
        with pytest.raises(CLIError) as exc_info:
            Webhook.create(
                {
                    'name': 'invalid-method-webhook',
                    'event': 'host_created',
                    'http-method': 'NONE',
                    'target-url': 'http://localhost/bla',
                }
            )

    @pytest.mark.tier3
    def test_positive_webhook_crud(self):
        """Test creation, list, update and removal of webhook

        :id: d893d176-cbe9-421b-8631-7c7a1a462ea5

        :CaseImportance: Critical
        """
        webhook_postfix = gen_alphanumeric()
        webhook_options = {
            'name': f'test-webhook-crud-{webhook_postfix}',
            'event': 'host_created',
            'http-method': 'GET',
            'target-url': 'http://localhost/some-path',
        }

        webhook_item = Webhook.create(webhook_options)
        for option in webhook_options.items():
            if option[0] != 'event':
                assert webhook_item[option[0]] == option[1]
        # Event is defined in a webhook item as {event_name}.event.foreman so we need to remove that postfix
        assert webhook_options['event'] == webhook_item['event'].rsplit('.', 2)[0]

        # Find webhook by name
        webhook_search = Webhook.info({'name': webhook_options['name']})
        # A non empty dict has been returned
        assert webhook_search

        # Returned webhook has same params as the original one
        for original_option in webhook_options.items():
            if original_option[0] != 'event':
                assert original_option[1] == webhook_search[original_option[0]]
            # Event is defined in a webhook item as {event_name}.event.foreman so we need to remove that postfix
            assert webhook_options['event'] == webhook_search['event'].rsplit('.', 2)[0]

        # Test that webhook gets updated
        different_url = 'http://localhost/different-path'
        Webhook.update({'name': webhook_options['name'], 'target-url': different_url})
        webhook_search_after_update = Webhook.info({'name': webhook_options['name']})
        assert webhook_search_after_update['target-url'] == different_url

        # Test that webhook is deleted
        Webhook.delete({'name': webhook_options['name']})
        webhook_deleted_search = Webhook.list({'search': webhook_options['name']})
        assert len(webhook_deleted_search) == 0

    def test_webhook_disabled_enabled(self):
        """
        Test disable/enable the webhook

        :id: 4fef4320-0655-440d-90e7-150ffcdcd043

        :CaseImportance: High
        """
        webhook_postfix = gen_alphanumeric()
        webhook_options = {
            'name': f'test-webhook-crud-{webhook_postfix}',
            'event': 'host_created',
            'http-method': 'GET',
            'target-url': 'http://localhost/some-path',
        }
        webhook_item = Webhook.create(webhook_options)

        # The new webhook is enabled by default on creation
        assert Webhook.info({'name': webhook_options['name']})['enabled'] == 'yes'

        Webhook.update({'name': webhook_options['name'], 'enabled': 'no'})
        # The webhook should be disabled now
        assert Webhook.info({'name': webhook_options['name']})['enabled'] == 'no'

        Webhook.update({'name': webhook_options['name'], 'enabled': 'yes'})
        # The webhook should be enabled again
        assert Webhook.info({'name': webhook_options['name']})['enabled'] == 'yes'

        # Cleanup
        Webhook.delete({'name': webhook_options['name']})

    def test_negative_update(self):
        """Test webhook negative update - invalid target URL fails

        :id: d893d176-cbe9-421b-8631-7c7a1a462ea5

        :expectedresults: Webhook is not updated

        :CaseImportance: High
        """
        webhook_postfix = gen_alphanumeric()
        webhook_options = {
            'name': f'test-webhook-invalid-update-{webhook_postfix}',
            'event': 'host_created',
            'http-method': 'GET',
            'target-url': 'http://localhost/some-path',
        }
        webhook_item = Webhook.create(webhook_options)

        invalid_url = '$%^##@***'
        with pytest.raises(CLIReturnCodeError):
            Webhook.update({'name': webhook_options['name'], 'target-url': invalid_url})

        # cleanup
        Webhook.delete({'name': webhook_options['name']})

    @pytest.mark.stubbed
    def test_webhook_triggered(self):
        """
        :id: 0f96d8cb-bdbe-404b-bf05-a2133322770a

        :expectedresults: A standard webhook is triggered by an event

        :CaseImportance: High
        """

    @pytest.mark.stubbed
    def test_ssl_webhook_triggered(self):
        """
        :id: aea4d330-e0eb-4664-85d1-dcfce190c9a7

        :expectedresults: An SSL webhook is triggered by an event
        """
