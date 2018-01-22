# -*- encoding: utf-8 -*-
"""Test class for Statistics UI

:Requirement: Statistic

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from nailgun import entities
from robottelo.decorators import skip_if_bug_open, tier1
from robottelo.test import UITestCase
from robottelo.ui.session import Session


class StatisticTestCase(UITestCase):
    """Implements Statistics tests from UI"""

    @classmethod
    def setUpClass(cls):
        """Prepare some data for charts"""
        super(StatisticTestCase, cls).setUpClass()
        cls.host = entities.Host(organization=cls.session_org).create()
        cls.host_name = cls.host.name.lower()

    @classmethod
    def set_session_org(cls):
        """Creates new organization to be used for current session the
        session_user will login automatically with this org in context
        """
        cls.session_org = entities.Organization().create()

    @tier1
    @skip_if_bug_open('bugzilla', 1510064)
    def test_positive_display_os_chart_title(self):
        """Create new host and check operating system statistic for it

        :id: b80f555a-c3d6-447d-96c9-e6cd00b3335b

        :customerscenario: true

        :expectedresults: Chart is displayed correctly

        :BZ: 1332989, 1510064

        :CaseImportance: Critical
        """
        os = self.host.operatingsystem.read()
        with Session(self):
            os_title = self.statistic.get_chart_title_data('OS Distribution')
            self.assertEqual(os_title['value'], '100%')
            self.assertEqual(os_title['text'], os.name + ' ' + os.major)

    @tier1
    @skip_if_bug_open('bugzilla', 1510064)
    def test_positive_display_arch_chart_title(self):
        """Create new host and check architecture statistic for it

        :id: 597e83ca-c355-484f-afdf-f6c219ac13dd

        :customerscenario: true

        :expectedresults: Chart is displayed correctly

        :BZ: 1332989, 1510064

        :CaseImportance: Critical
        """
        arch = self.host.architecture.read()
        with Session(self):
            arch_title = self.statistic.get_chart_title_data(
                'Architecture Distribution')
            self.assertEqual(arch_title['value'], '100%')
            self.assertEqual(arch_title['text'], arch.name)
