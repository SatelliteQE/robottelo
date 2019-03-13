"""API Tests for the email notification feature

:Requirement: Email

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import stubbed, tier1
from robottelo.test import APITestCase


class EmailTestCase(APITestCase):
    """API Tests for the email notification feature"""

    @stubbed()
    @tier1
    def test_positive_enable_and_disable_notification(self):
        """Manage user email notification preferences.

        :id: 60928133-7bdc-4934-9804-f52b10d9ac95

        :Steps: Enable and disable email notifications using
            /api/mail_notifications

        :expectedresults: Enabling and disabling email notification preferences
            saved accordingly.

        :CaseAutomation: notautomated

        :CaseImportance: Critical
        """
