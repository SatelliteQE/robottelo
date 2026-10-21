"""Test module for Dashboard UI

:Requirement: Dashboard

:CaseAutomation: Automated

:CaseComponent: Dashboard

:Team: Dragonfly

:CaseImportance: High

"""

from datetime import datetime, timedelta
from pathlib import Path

from airgun.session import Session
from navmazing import NavigationTriesExceeded
import pytest
import requests

from robottelo.constants import LIFECYCLE_METADATA_FILE
from robottelo.utils.datafactory import gen_string


def set_eol_date(target_sat, eol_date):
    target_sat.execute(
        rf'''sed -i "/end_of_life/c\    'end_of_life': '{eol_date}'" "{LIFECYCLE_METADATA_FILE}"'''
    )
    target_sat.restart_services()


def check_links(session):
    for link in [session.eol_banner.lifecycle_link(), session.eol_banner.helper_link()]:
        assert requests.get(link, verify=False).status_code == 200, f'Failed to reach {link}'


@pytest.fixture
def target_eol_sat(target_sat):
    """Yield target_sat with LIFECYCLE_METADATA_FILE bind-mounted from the Satellite host."""

    lifecycle_metadata_dir = Path(f"{LIFECYCLE_METADATA_FILE}").parent
    unit_file = target_sat.execute(
        'systemctl show foreman.service -p SourcePath --value'
    ).stdout.strip()
    target_sat.execute(f"sed -i '\\|^Volume={lifecycle_metadata_dir}:|d' {unit_file}")
    target_sat.execute(f"mkdir -p {lifecycle_metadata_dir}")
    target_sat.execute(f'podman cp foreman:{LIFECYCLE_METADATA_FILE} {LIFECYCLE_METADATA_FILE}')
    target_sat.execute(
        f"sed -i '/^\\[Container\\]/a Volume={lifecycle_metadata_dir}:{lifecycle_metadata_dir}:z' {unit_file}"
    )
    target_sat.execute('systemctl daemon-reload')
    target_sat.restart_services()

    yield target_sat

    target_sat.execute(f"sed -i '\\|^Volume={lifecycle_metadata_dir}:|d' {unit_file}")
    target_sat.execute('systemctl daemon-reload')
    target_sat.restart_services()


@pytest.mark.upgrade
@pytest.mark.run_in_one_thread
def test_positive_eol_banner_e2e(session, target_eol_sat, test_name):
    """Check if the EOL banner is displayed correctly

    :id: 0ce6c11c-d969-4e7e-a934-cd1683de62a3

    :Steps:

        1. Set the EOL date within 6 months, assert warning banner
        2. Check non-admin users can't see warning banner
        3. Dismiss banner
        4. Move EOL date to the past, assert error banner
        5. Check non-admin users can't see error banner
        6. Dismiss banner

    :Verifies: SAT-29427

    :expectedresults: Banner shows up when it should
    """
    # non-admin user
    username = gen_string('alpha')
    password = gen_string('alpha')
    target_eol_sat.api.User(login=username, password=password, mail='test@example.com').create()
    # admin user
    admin_username = gen_string('alpha')
    admin_password = gen_string('alpha')
    target_eol_sat.api.User(
        login=admin_username, password=admin_password, admin=True, mail='admin@example.com'
    ).create()

    # eol in 3 months
    eol_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    message_date = (datetime.now() + timedelta(days=90)).strftime("%B %Y")
    set_eol_date(target_eol_sat, eol_date)

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
        check_links(adminsession)
        adminsession.eol_banner.dismiss()
        with pytest.raises(NavigationTriesExceeded) as error:
            adminsession.eol_banner.read()
        assert error.typename == 'NavigationTriesExceeded'

    # past eol_date
    eol_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    set_eol_date(target_eol_sat, eol_date)

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
        check_links(adminsession)
        adminsession.eol_banner.dismiss()
        with pytest.raises(NavigationTriesExceeded) as error:
            adminsession.eol_banner.read()
        assert error.typename == 'NavigationTriesExceeded'
