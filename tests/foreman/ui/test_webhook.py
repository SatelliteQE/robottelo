"""Test class for Webhook UI

:Requirement: Webhooks

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Webhooks

:Assignee: gsulliva

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from fauxfactory import gen_url


@pytest.mark.tier1
def test_positive_end_to_end(session):
    """Perform end to end testing for webhooks.

    :id: 9d2072e7-c6b6-4ecb-ac84-e73f4cf76fe4

    :expectedresults: All expected CRUD actions finished successfully

    :CaseImportance: Critical
    """
    hook_name = gen_string('alpha')
    subscribe_to = 'Host Created'
    target_url = gen_url(subdomain=gen_string('alpha'), scheme='http')
    template = 'Katello Publish'
    http_method = 'GET'
    new_hook_name = gen_string('alpha')
    new_subscribe_to = 'Host Destroyed'
    new_target_url = gen_url(subdomain=gen_string('alpha'), scheme='http')
    new_template = 'Katello Promote'
    new_http_method = 'PUT'
    with session:
        session.webhook.create(
            {
                'general.subscribe_to': subscribe_to,
                'general.name': hook_name,
                'general.target_url': target_url,
                'general.template': template,
                'general.http_method': http_method,
                'general.enabled': False,
            }
        )
        values = session.webhook.read(hook_name)
        assert values['general']['name'] == hook_name
        assert values['general']['subscribe_to'] == subscribe_to
        assert values['general']['target_url'] == target_url
        assert values['general']['template'] == template
        assert values['general']['http_method'] == http_method
        assert values['general']['enabled'] is False
        session.webhook.update(
            hook_name,
            {
                'general.subscribe_to': new_subscribe_to,
                'general.name': new_hook_name,
                'general.target_url': new_target_url,
                'general.template': new_template,
                'general.http_method': new_http_method,
                'general.enabled': True,
            },
        )
        values = session.webhook.read(new_hook_name)
        assert values['general']['name'] == new_hook_name
        assert values['general']['subscribe_to'] == new_subscribe_to
        assert values['general']['target_url'] == new_target_url
        assert values['general']['template'] == new_template
        assert values['general']['http_method'] == new_http_method
        assert values['general']['enabled'] is True
        session.webhook.delete(new_hook_name)
        assert not session.webhook.search(new_hook_name)
