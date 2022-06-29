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
import pytest
from nailgun import entities

class TestWebhook:
    @pytest.mark.tier1
    def test_positive_create_hook(self, module_org, module_location):
        """Create a new webhook.

        :id: 7593a04e-cf7e-414c-9e7e-3fe2936cc32a

        :expectedresults: Webhook is created successfully.

        :CaseImportance: High
        """
        hook = entities.Webhooks(organization=[module_org], location=[module_location]).create()
        assert hook
