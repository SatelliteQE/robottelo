# -*- encoding: utf-8 -*-
"""Test class for Task UI

:Requirement: Task

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_integer
from robottelo.decorators import skip_if_bug_open, tier1
from robottelo.test import UITestCase
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class TaskTest(UITestCase):
    """Implements Task tests in UI."""

    @skip_if_bug_open('bugzilla', 1440157)
    @tier1
    def test_negative_search(self):
        """Attempt to find task using long integer number

        :id: 4e4f92ca-0a9d-45f6-a602-641c5932362c

        :expectedresults: 'No entries found' message should be returned

        :BZ: 1440157

        :CaseImportance: Critical
        """

        with Session(self):
            self.assertIsNotNone(self.task.search(
                str(gen_integer(min_value=1489607391328)),
                expecting_results=False)
            )
            self.assertIsNotNone(self.task.search(
                '',
                _raw_query=str(gen_integer(min_value=1489607391328)),
                expecting_results=False)
            )
            self.assertIsNone(self.task.wait_until_element(
                common_locators['alert.error'], timeout=5))
