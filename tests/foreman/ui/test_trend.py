"""Test class for Trend UI

:Requirement: Trend

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Trends

:TestType: Functional

:CaseImportance: Low

:Upstream: No
"""
from fauxfactory import gen_string

from robottelo.constants import TREND_TYPES
from robottelo.decorators import tier2
from robottelo.decorators import upgrade


@tier2
@upgrade
def test_positive_end_to_end(session):
    """Perform end to end testing for trend component

    :id: 82040ebe-34e7-45af-b928-120188498562

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    name = gen_string('alpha')
    new_name = gen_string('alpha')
    fact_name = 'cpu'
    with session:
        # Create new trend
        session.trend.create(
            {'trendable_type': TREND_TYPES['facts'], 'trendable_id': fact_name, 'name': name}
        )
        assert session.trend.search(name)
        # Update trend
        session.trend.update(name, fact_name, new_name)
        assert session.trend.search(new_name)
        # Delete trend
        session.trend.delete(new_name)
        assert not session.trend.search(new_name)
