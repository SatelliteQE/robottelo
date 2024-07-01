"""Test class for CLI authentication

:Requirement: Auth

:CaseAutomation: Automated

:CaseComponent: Authentication

:Team: Endeavour

:CaseImportance: Critical

"""

from time import sleep

from fauxfactory import gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import HAMMER_CONFIG
from robottelo.exceptions import CLIReturnCodeError

LOGEDIN_MSG = "Session exists, currently logged in as '{0}'"
NOTCONF_MSG = "Credentials are not configured."
password = gen_string('alpha')


def configure_sessions(satellite, enable=True, add_default_creds=False):
    """Enables the `use_sessions` option in hammer config"""
    result = satellite.execute(
        '''sed -i -e '/username/d;/password/d;/use_sessions/d' {0};\
        echo '  :use_sessions: {1}' >> {0}'''.format(HAMMER_CONFIG, 'true' if enable else 'false')
    )
    if result.status == 0 and add_default_creds:
        result = satellite.execute(
            f'''{{ echo '  :username: "{settings.server.admin_username}"';\
            echo '  :password: "{settings.server.admin_password}"'; }} >> {HAMMER_CONFIG}'''
        )
    return result.status


@pytest.fixture(scope='module')
def admin_user(module_target_sat):
    """create the admin role user for tests"""
    uname_admin = gen_string('alpha')
    return module_target_sat.cli_factory.user(
        {'login': uname_admin, 'password': password, 'admin': '1'}
    )


@pytest.fixture(scope='module')
def non_admin_user(module_target_sat):
    """create the non-admin role user for tests"""
    uname_viewer = gen_string('alpha')
    user = module_target_sat.cli_factory.user({'login': uname_viewer, 'password': password})
    module_target_sat.cli.User.add_role({'login': uname_viewer, 'role': 'Viewer'})
    return user


@pytest.mark.tier1
def test_positive_create_session(admin_user, target_sat):
    """Check if user stays authenticated with session enabled

    :id: fcee7f5f-1040-41a9-bf17-6d0c24a93e22

    :steps:

        1. Set use_sessions, set short expiration time
        2. Authenticate, assert credentials are not demanded
           on next command run
        3. Wait until session expires, assert credentials
           are required

    :expectedresults: The session is successfully created and
        expires after specified time
    """
    try:
        idle_timeout = target_sat.cli.Settings.list({'search': 'name=idle_timeout'})[0]['value']
        target_sat.cli.Settings.set({'name': 'idle_timeout', 'value': 1})
        result = configure_sessions(target_sat)
        assert result == 0, 'Failed to configure hammer sessions'
        target_sat.cli.AuthLogin.basic({'username': admin_user['login'], 'password': password})
        result = target_sat.cli.Auth.with_user().status()
        assert LOGEDIN_MSG.format(admin_user['login']) in result[0]['message']
        # list organizations without supplying credentials
        assert target_sat.cli.Org.with_user().list()
        # wait until session expires
        sleep(70)
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.Org.with_user().list()
        result = target_sat.cli.Auth.with_user().status()
        assert NOTCONF_MSG in result[0]['message']
    finally:
        # reset timeout to default
        target_sat.cli.Settings.set({'name': 'idle_timeout', 'value': f'{idle_timeout}'})


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_disable_session(admin_user, target_sat):
    """Check if user logs out when session is disabled

    :id: 38ee0d85-c2fe-4cac-a992-c5dbcec11031

    :steps:

        1. Set use_sessions
        2. Authenticate, assert credentials are not demanded
           on next command run
        3. Disable use_sessions

    :expectedresults: The session is terminated
    """
    result = configure_sessions(target_sat)
    assert result == 0, 'Failed to configure hammer sessions'
    target_sat.cli.AuthLogin.basic({'username': admin_user['login'], 'password': password})
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(admin_user['login']) in result[0]['message']
    # list organizations without supplying credentials
    assert target_sat.cli.Org.with_user().list()
    # disabling sessions
    result = configure_sessions(satellite=target_sat, enable=False)
    assert result == 0, 'Failed to configure hammer sessions'
    result = target_sat.cli.Auth.with_user().status()
    assert NOTCONF_MSG in result[0]['message']
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Org.with_user().list()


@pytest.mark.tier1
def test_positive_log_out_from_session(admin_user, target_sat):
    """Check if session is terminated when user logs out

    :id: 0ba05f2d-7b83-4b0c-a04c-80e62b7c4cf2

    :steps:

        1. Set use_sessions
        2. Authenticate, assert credentials are not demanded
           on next command run
        3. Run `hammer auth logout`

    :expectedresults: The session is terminated
    """
    result = configure_sessions(target_sat)
    assert result == 0, 'Failed to configure hammer sessions'
    target_sat.cli.AuthLogin.basic({'username': admin_user['login'], 'password': password})
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(admin_user['login']) in result[0]['message']
    # list organizations without supplying credentials
    assert target_sat.cli.Org.with_user().list()
    target_sat.cli.Auth.logout()
    result = target_sat.cli.Auth.with_user().status()
    assert NOTCONF_MSG in result[0]['message']
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Org.with_user().list()


@pytest.mark.tier1
def test_positive_change_session(admin_user, non_admin_user, target_sat):
    """Change from existing session to a different session

    :id: b6ea6f3c-fcbd-4e7b-97bd-f3e0e6b9da8f

    :steps:

        1. Set use_sessions
        2. Authenticate, assert credentials are not demanded
           on next command run
        3. Login as a different user

    :CaseImportance: High

    :expectedresults: The session is altered
    """
    result = configure_sessions(target_sat)
    assert result == 0, 'Failed to configure hammer sessions'
    target_sat.cli.AuthLogin.basic({'username': admin_user['login'], 'password': password})
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(admin_user['login']) in result[0]['message']
    # list organizations without supplying credentials
    assert target_sat.cli.User.with_user().list()
    target_sat.cli.AuthLogin.basic({'username': non_admin_user['login'], 'password': password})
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(non_admin_user['login']) in result[0]['message']
    assert target_sat.cli.User.with_user().list()


@pytest.mark.tier1
def test_positive_session_survives_unauthenticated_call(admin_user, target_sat):
    """Check if session stays up after unauthenticated call

    :id: 8bc304a0-70ea-489c-9c3f-ea8343c5284c

    :steps:

        1. Set use_sessions
        2. Authenticate
        3. Run an authenticated call, assert credentials are not demanded
        4. Run `hammer ping`, an unauthenticated call
        5. Run an authenticated call, assert credentials are not demanded

    :CaseImportance: Medium

    :expectedresults: The session is unchanged
    """
    result = configure_sessions(target_sat)
    assert result == 0, 'Failed to configure hammer sessions'
    target_sat.cli.AuthLogin.basic({'username': admin_user['login'], 'password': password})
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(admin_user['login']) in result[0]['message']
    # list organizations without supplying credentials
    target_sat.cli.Org.with_user().list()
    result = target_sat.execute('hammer ping')
    assert result.status == 0, 'Failed to run hammer ping'
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(admin_user['login']) in result[0]['message']
    target_sat.cli.Org.with_user().list()


@pytest.mark.tier1
def test_positive_session_survives_failed_login(admin_user, non_admin_user, target_sat):
    """Check if session stays up after failed login attempt

    :id: 6c4d5c4c-eff0-411b-829f-0c2f2ec26132

    :BZ: 1465552

    :steps:

        1. Set use_sessions
        2. Authenticate
        3. Run an authenticated command, assert credentials are not demanded
        4. Run login with invalid credentials
        5. Run an authenticated command, assert credentials are not demanded

    :expectedresults: The session is unchanged

    :CaseImportance: High
    """
    result = configure_sessions(target_sat)
    assert result == 0, 'Failed to configure hammer sessions'
    target_sat.cli.AuthLogin.basic({'username': admin_user['login'], 'password': password})
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(admin_user['login']) in result[0]['message']
    target_sat.cli.Org.with_user().list()
    # using invalid password
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.AuthLogin.basic(
            {'username': non_admin_user['login'], 'password': gen_string('alpha')}
        )
    # checking the session status again
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(admin_user['login']) in result[0]['message']
    target_sat.cli.Org.with_user().list()


@pytest.mark.e2e
@pytest.mark.tier1
def test_positive_session_preceeds_saved_credentials(admin_user, target_sat):
    """Check if enabled session is mutually exclusive with
    saved credentials in hammer config

    :id: e4277298-1c24-494b-84a6-22f45f96e144

    :BZ: 1471099, 1903693

    :CaseImportance: High

    :steps:

        1. Set use_sessions, set username and password,
           set short expiration time
        2. Authenticate, assert credentials are not demanded
           on next command run
        3. Wait until session expires

    :expectedresults: Session expires after specified time
        and saved credentials are not applied
    """
    try:
        idle_timeout = target_sat.cli.Settings.list({'search': 'name=idle_timeout'})[0]['value']
        target_sat.cli.Settings.set({'name': 'idle_timeout', 'value': 1})
        result = configure_sessions(satellite=target_sat, add_default_creds=True)
        assert result == 0, 'Failed to configure hammer sessions'
        target_sat.cli.AuthLogin.basic({'username': admin_user['login'], 'password': password})
        result = target_sat.cli.Auth.with_user().status()
        assert LOGEDIN_MSG.format(admin_user['login']) in result[0]['message']
        # list organizations without supplying credentials
        sleep(70)
        with pytest.raises(CLIReturnCodeError):
            target_sat.cli.Org.with_user().list()
    finally:
        # reset timeout to default
        target_sat.cli.Settings.set({'name': 'idle_timeout', 'value': f'{idle_timeout}'})


@pytest.mark.tier1
def test_negative_no_credentials(target_sat):
    """Attempt to execute command without authentication

    :id: 8a3b5c68-1027-450f-997c-c5630218f49f

    :expectedresults: Command is not executed

    :CaseImportance: High
    """
    result = configure_sessions(satellite=target_sat, enable=False)
    assert result == 0, 'Failed to configure hammer sessions'
    result = target_sat.cli.Auth.with_user().status()
    assert NOTCONF_MSG in result[0]['message']
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Org.with_user().list()


@pytest.mark.tier1
def test_negative_no_permissions(admin_user, non_admin_user, target_sat):
    """Attempt to execute command out of user's permissions

    :id: 756f666f-270a-4b02-b587-a2ab09b7d46c

    :expectedresults: Command is not executed

    :CaseImportance: High
    """
    result = configure_sessions(target_sat)
    assert result == 0, 'Failed to configure hammer sessions'
    target_sat.cli.AuthLogin.basic({'username': non_admin_user['login'], 'password': password})
    result = target_sat.cli.Auth.with_user().status()
    assert LOGEDIN_MSG.format(non_admin_user['login']) in result[0]['message']
    # try to update user from viewer's session
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.User.with_user().update(
            {'login': admin_user['login'], 'new-login': gen_string('alpha')}
        )
