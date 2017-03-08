"""Test module for System Registration UI

:Requirement: System registration

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
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

        :id: 9427294f-42f7-4f7b-bdcc-88d0fc22b893

        :assert: content is installed on client system

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_list_system_for_org(self):
        """perform a system list for a given org

        :id: 795605d6-01c2-4db1-8ca2-a966545c0db1

        :assert: newly registered system can be found in Systems UI

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_deregister_system(self):
        """delete system via Systems UI

        :id: ce1844c5-a853-49e2-8eaf-dbac24d6afde

        :assert: after deleting, system no longer appears in system UI.

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_compliance_green(self):
        """system with appropriate entitlements for subscriptions

        :id: 42adeb01-765d-4ee8-a326-4b799c1e91ab

        :assert: compliance status is green in UI

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_compliance_red(self):
        """system without appropriate entitlements for subscriptions

        :id: dce486cc-66fc-4959-8cce-e9dbb86eff26

        :assert: compliance status is red in UI

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_compliance_yellow(self):
        """system with some, but not all, appropriate entitlements for
        subscriptions

        :id: 788d0da4-f498-4ad2-9a2c-6897d2e699e4

        :assert: compliance status is yellow in UI

        :caseautomation: notautomated

        :CaseLevel: System
        """
