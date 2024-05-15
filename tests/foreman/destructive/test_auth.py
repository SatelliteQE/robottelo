"""Test class for CLI authentication

:Requirement: Auth

:CaseAutomation: Automated

:CaseComponent: Authentication

:Team: Endeavour

:CaseImportance: Critical

"""

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import HAMMER_CONFIG

LOGEDIN_MSG = "Session exists, currently logged in as '{0}'"
password = gen_string('alpha')
pytestmark = pytest.mark.destructive


def test_positive_password_reset(target_sat):
    """Reset admin password using foreman rake and update the hammer config.
    verify the reset password is working.

    :id: 7ab65b6f-cf41-42b9-808c-570fc928e18d

    :expectedresults: verify the 'foreman-rake permissions:reset' command for the admin user

    :CaseImportance: High
    """
    result = target_sat.execute('foreman-rake permissions:reset')
    assert result.status == 0
    reset_password = result.stdout.splitlines()[0].split('password: ')[1]
    result = target_sat.execute(
        f'''sed -i -e '/username/d;/password/d;/use_sessions/d' {HAMMER_CONFIG};\
        echo '  :use_sessions: true' >> {HAMMER_CONFIG}'''
    )
    assert result.status == 0
    target_sat.cli.AuthLogin.basic(
        {'username': settings.server.admin_username, 'password': reset_password}
    )
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(settings.server.admin_username) in result.split("\n")[1]
    assert target_sat.cli.Org.with_user().list()


def test_positive_password_reset_chosen(target_sat):
    """Reset admin password to specified password using foreman rake and update the hammer config. Verify the new password is working.

    :id: e8f13a26-2299-4a6b-a2f7-8cb17389d400

    :expectedresults: New specified password is set.

    :CaseImportance: High
    """
    new_password = gen_string('alpha')
    result = target_sat.execute(f'foreman-rake permissions:reset password={new_password}')
    assert result.status == 0
    reset_password = result.stdout.splitlines()[0].split('password: ')[1]
    assert reset_password == new_password
    result = target_sat.execute(
        f'''sed -i -e '/username/d;/password/d;/use_sessions/d' {HAMMER_CONFIG};\
        echo '  :use_sessions: true' >> {HAMMER_CONFIG}'''
    )
    assert result.status == 0
    target_sat.cli.AuthLogin.basic(
        {'username': settings.server.admin_username, 'password': new_password}
    )
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(settings.server.admin_username) in result.split("\n")[1]
    assert target_sat.cli.Org.with_user().list()
