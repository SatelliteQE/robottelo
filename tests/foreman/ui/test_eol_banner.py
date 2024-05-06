"""Test module for Dashboard UI

:Requirement: Dashboard

:CaseAutomation: Automated

:CaseComponent: Dashboard

:Team: Endeavour

:CaseImportance: High

"""

from datetime import datetime, timedelta

from airgun.session import Session
from navmazing import NavigationTriesExceeded
import pytest

from robottelo.utils.datafactory import gen_string


def set_eol_date(target_sat, eol_date):
    target_sat.execute(
        rf'''sed -i "/end_of_life/c\    'end_of_life': '{eol_date}'" /usr/share/satellite/lifecycle-metadata.yml'''
    )
    target_sat.restart_services()


@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
@pytest.mark.tier2
def test_positive_eol_banner_e2e(session, target_sat, test_name):
    """Check if the EOL banner is displayed correctly

    :id: 0ce6c11c-d969-4e7e-a934-cd1683de62a3

    :Steps:

        1. Set the EOL date witin 6 months, assert warning banner
        2. Check non-admin users can't see warning banner
        3. Dismiss banner
        4. Move EOL date to the past, assert error banner
        5. Check non-admin users can't see error banner
        6. Dismiss banner

    :expectedresults: Banner shows up when it should
    """
    # non-admin user
    username = gen_string('alpha')
    password = gen_string('alpha')
    target_sat.api.User(login=username, password=password, mail='test@example.com').create()
    # admin user
    admin_username = gen_string('alpha')
    admin_password = gen_string('alpha')
    target_sat.api.User(
        login=admin_username, password=admin_password, admin=True, mail='admin@example.com'
    ).create()

    # eol in 3 months
    eol_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    message_date = (datetime.now() + timedelta(days=90)).strftime("%B %Y")
    set_eol_date(target_sat, eol_date)

    # non-admin can't see banner
    with Session(test_name, username, password) as newsession:
        with pytest.raises(NavigationTriesExceeded) as error:
            newsession.eol_banner.read()
        assert error.typename == 'NavigationTriesExceeded'

    # admin can see warning banner
    with Session(test_name, admin_username, admin_password) as adminsession:
        banner = adminsession.eol_banner.read()
        assert message_date in banner["name"]
        assert adminsession.eol_banner.is_warning()
        adminsession.eol_banner.dismiss()
        with pytest.raises(NavigationTriesExceeded) as error:
            adminsession.eol_banner.read()
        assert error.typename == 'NavigationTriesExceeded'

    # past eol_date
    eol_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    set_eol_date(target_sat, eol_date)

    # non-admin can't see danger banner
    with Session(test_name, username, password) as newsession:
        with pytest.raises(NavigationTriesExceeded) as error:
            newsession.eol_banner.read()
        assert error.typename == 'NavigationTriesExceeded'

    # admin can see danger banner
    with Session(test_name, admin_username, admin_password) as adminsession:
        banner = adminsession.eol_banner.read()
        assert eol_date in banner["name"]
        assert adminsession.eol_banner.is_danger()
        adminsession.eol_banner.dismiss()
        with pytest.raises(NavigationTriesExceeded) as error:
            adminsession.eol_banner.read()
        assert error.typename == 'NavigationTriesExceeded'
