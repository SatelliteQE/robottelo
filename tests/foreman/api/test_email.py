"""API Tests for the email notification feature"""

from robottelo.decorators import stubbed
from robottelo.test import APITestCase


class EmailTestCase(APITestCase):
    """API Tests for the email notification feature"""

    @stubbed()
    def test_email_1(self):
        """@Test: Manage user email notification preferences.

        @Feature: Email Notification

        @Steps:

        1. Enable and disable email notifications using /api/mail_notifications

        @Assert: Enabling and disabling email notification preferences saved
        accordingly.

        @Status: Manual

        """
