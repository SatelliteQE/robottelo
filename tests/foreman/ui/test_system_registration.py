"""Test module for System Registration UI"""
from robottelo.decorators import stubbed
from robottelo.test import UITestCase


class SystemRegistrationTestCase(UITestCase):
    """Tests for System Registration UI"""

    @stubbed()
    def test_registered_system_get_pushed_content(self):
        # variations: content types - RH rpms/errata; custom content rpms;
        # puppet modules
        """@test: assure content types can be pushed down to client via UI

        @feature: system registration

        @assert: content is installed on client system

        @status: Manual

        """

    @stubbed()
    def test_registered_system_can_be_listed_ui(self):
        """@test: perform a system list for a given org

        @feature: system registration

        @assert: newly registered system can be found in Systems UI

        @status: Manual

        """

    @stubbed()
    def test_system_deregister_ui(self):
        """@test: delete system via Systems UI

        @feature: system registration

        @assert: after deleting, system no longer appears in system UI.

        @status: Manual

        """

    @stubbed()
    def test_compliance_green(self):
        """@test: system with appropriate entitlements for subscriptions

        @feature: system registration

        @assert: compliance status is green in UI

        @status: Manual

        """

    @stubbed()
    def test_compliance_red(self):
        """@test: system without appropriate entitlements for subscriptions

        @feature: system registration

        @assert: compliance status is red in UI

        @status: Manual

        """

    @stubbed()
    def test_compliance_yellow(self):
        """@test: system with some, but not all, appropriate entitlements for
        subscriptions

        @feature: system registration

        @assert: compliance status is yellow in UI

        @status: Manual

        """
