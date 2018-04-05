"""Test class for Sync Plan UI

:Requirement: Syncplan

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime, timedelta

from robottelo.datafactory import gen_string
from robottelo.decorators import tier2


def get_client_datetime(browser):
    """Make Javascript call inside of browser session to get exact current
    date and time. In that way, we will be isolated from any issue that can
    happen due different environments where test automation code is
    executing and where browser session is opened. That should help us to
    have successful run for docker containers or separated virtual machines
    When calling .getMonth() you need to add +1 to display the correct
    month. Javascript count always starts at 0, so calling .getMonth() in
    May will return 4 and not 5.

    :param browser: Webdriver browser object.

    :return: Datetime object that contains data for current date and time
        on a client
    """
    script = ('var currentdate = new Date(); return ({0} + "-" + {1} + '
              '"-" + {2} + " : " + {3} + ":" + {4});').format(
        'currentdate.getFullYear()',
        '(currentdate.getMonth()+1)',
        'currentdate.getDate()',
        'currentdate.getHours()',
        'currentdate.getMinutes()',
    )
    client_datetime = browser.execute_script(script)
    return datetime.strptime(client_datetime, '%Y-%m-%d : %H:%M')


def test_positive_create(session):
    plan_name = gen_string('alpha')
    description = gen_string('alpha')
    with session:
        session.syncplan.create({
            'name': plan_name,
            'description': description,
            'interval': 'daily',
        })
        assert session.syncplan.search(plan_name) == plan_name
        syncplan_values = session.syncplan.read(plan_name)
        assert syncplan_values['Details']['name'] == plan_name
        assert syncplan_values['Details']['description'] == description
        assert syncplan_values['Details']['interval'] == 'daily'


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
                get_client_datetime(session.browser) + timedelta(minutes=10))
        session.syncplan.create({
            'name': plan_name,
            'interval': 'daily',
            'date_time.hours': startdate.strftime('%H'),
            'date_time.minutes': startdate.strftime('%M'),

        })
        assert session.syncplan.search(plan_name) == plan_name
        syncplan_values = session.syncplan.read(plan_name)
        time = str(syncplan_values['Details']['date_time']).rpartition(':')[0]
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
                get_client_datetime(session.browser) + timedelta(days=10))
        session.syncplan.create({
            'name': plan_name,
            'interval': 'daily',
            'date_time.start_date': startdate.strftime("%Y-%m-%d"),
        })
        assert session.syncplan.search(plan_name) == plan_name
        syncplan_values = session.syncplan.read(plan_name)
        date = str(syncplan_values['Details']['date_time']).partition(' ')[0]
        assert date == startdate.strftime("%Y/%m/%d")
