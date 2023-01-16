"""Test class for CLI authentication

:Requirement: Auth

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Authentication

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.config import settings
from robottelo.constants import HAMMER_CONFIG

LOGEDIN_MSG = "Session exists, currently logged in as '{0}'"
LOGEDOFF_MSG = "Using sessions, you are currently not logged in"
NOTCONF_MSG = "Credentials are not configured."
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
    reset_password = result.stdout.strip().split('password: ')[1]
    result = target_sat.execute(
        f'''sed -i -e '/username/d;/password/d;/use_sessions/d' {HAMMER_CONFIG};\
        echo '  :use_sessions: true' >> {HAMMER_CONFIG}'''
    )
    assert result.status == 0
    target_sat.cli.AuthLogin.basic(
        {'username': settings.server.admin_username, 'password': reset_password}
    )
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(settings.server.admin_username) in result[0]['message']
    assert target_sat.cli.Org.with_user().list()
