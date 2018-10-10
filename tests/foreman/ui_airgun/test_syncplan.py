"""Test class for Sync Plan UI

:Requirement: Syncplan

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import timedelta

from robottelo.datafactory import gen_string
from robottelo.decorators import tier2


@tier2
def test_positive_create_with_start_time(session):
    """Create Sync plan with specified start time

    :id: a4709229-325c-4027-b4dc-10a226c4d7bf

    :expectedresults: Sync Plan is created with the specified time.

    :BZ: 1460146

    :CaseLevel: Integration
    """
    plan_name = gen_string('alpha')
    with session:
        startdate = (
                session.browser.get_client_datetime() + timedelta(minutes=10))
        session.syncplan.create({
            'name': plan_name,
            'interval': 'daily',
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),

        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        syncplan_values = session.syncplan.read(plan_name)
        time = str(syncplan_values['details']['date_time']).rpartition(':')[0]
        assert time == startdate.strftime("%Y/%m/%d %H:%M")


@tier2
def test_positive_create_with_start_date(session):
    """Create Sync plan with specified start date

    :id: 020b3aff-7216-4ad6-b95e-8ffaf68cba20

    :expectedresults: Sync Plan is created with the specified date

    :BZ: 1460146

    :CaseLevel: Integration
    """
    plan_name = gen_string('alpha')
    with session:
        startdate = (
                session.browser.get_client_datetime() + timedelta(days=10))
        session.syncplan.create({
            'name': plan_name,
            'interval': 'daily',
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
        })
        assert session.syncplan.search(plan_name)[0]['Name'] == plan_name
        syncplan_values = session.syncplan.read(plan_name)
        date = str(syncplan_values['details']['date_time']).partition(' ')[0]
        assert date == startdate.strftime("%Y/%m/%d")
