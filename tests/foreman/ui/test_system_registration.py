"""Test module for System Registration UI"""
from robottelo.decorators import stubbed, tier3
from robottelo.test import UITestCase


class SystemRegistrationTestCase(UITestCase):
    """Tests for System Registration UI"""

    @stubbed()
    @tier3
    def test_positive_get_pushed_content(self):
        # variations: content types - RH rpms/errata; custom content rpms;
        # puppet modules
        """assure content types can be pushed down to client via UI

        @feature: system registration

        @assert: content is installed on client system

        @status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_list_system_for_org(self):
        """perform a system list for a given org

        @feature: system registration

        @assert: newly registered system can be found in Systems UI

        @status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_deregister_system(self):
        """delete system via Systems UI

        @feature: system registration

        @assert: after deleting, system no longer appears in system UI.

        @status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_compliance_green(self):
        """system with appropriate entitlements for subscriptions

        @feature: system registration

        @assert: compliance status is green in UI

        @status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_compliance_red(self):
        """system without appropriate entitlements for subscriptions

        @feature: system registration

        @assert: compliance status is red in UI

        @status: Manual
        """

    @stubbed()
    @tier3
    def test_positive_compliance_yellow(self):
        """system with some, but not all, appropriate entitlements for
        subscriptions

        @feature: system registration

        @assert: compliance status is yellow in UI

        @status: Manual
        """
