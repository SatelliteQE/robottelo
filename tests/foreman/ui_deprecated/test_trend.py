# -*- encoding: utf-8 -*-
"""Test class for Trend UI

:Requirement: Trend

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from robottelo.constants import TREND_TYPES
from robottelo.decorators import tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.factory import make_trend
from robottelo.ui.session import Session


class TrendTest(UITestCase):
    """Implements Trend tests in UI.

    Please note that we have static amount of Trend types and trendables, so it
    is not possible to generate values for them. In case you want to interact
    with them through automation, it is must have condition to provide unique
    elements from corresponding lists.
    In most cases it will not be possible to re-run tests due condition of
    uniqueness described above.
    """

    @tier1
    def test_positive_create(self):
        """Create new trend

        :id: d0c040cf-8132-43cd-9569-26148b80a44b

        :expectedresults: Trend is created successfully

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_trend(session, trend_type=TREND_TYPES['model'])
            search = self.trend.search(TREND_TYPES['model'])
            self.assertIsNotNone(search)

    @tier1
    @upgrade
    def test_positive_update(self):
        """Update trend entity value

        :id: 329af7a7-e7c1-4c09-9849-d9ec12ddcee9

        :expectedresults: Trend entity is updated successfully

        :CaseImportance: Critical
        """
        name = gen_string('alphanumeric')
        new_name = gen_string('alphanumeric')
        with Session(self) as session:
            make_trend(
                session,
                trend_type=TREND_TYPES['facts'],
                trendable='clientcert',
                name=name,
            )
            search = self.trend.search(name)
            self.assertIsNotNone(search)

            self.trend.update(name, 'clientcert', new_name)
            search = self.trend.search(new_name)
            self.assertIsNotNone(search)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete existing trend

        :id: 0b5376f0-c8ae-434a-a5da-10b16ac3b932

        :expectedresults: Trend is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            make_trend(session, trend_type=TREND_TYPES['environment'])
            self.trend.delete(
                TREND_TYPES['environment'], dropdown_present=True)
