"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: LDAP

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from time import sleep

import pytest

from robottelo.cli.base import CLIReturnCodeError
from robottelo.config import settings
from robottelo.constants import HAMMER_CONFIG
from robottelo.rhsso_utils import get_oidc_authorization_endpoint
from robottelo.rhsso_utils import get_oidc_client_id
from robottelo.rhsso_utils import get_oidc_token_endpoint
from robottelo.rhsso_utils import get_two_factor_token_rh_sso_url
from robottelo.rhsso_utils import open_pxssh_session
from robottelo.rhsso_utils import run_command
from robottelo.rhsso_utils import update_client_configuration

pytestmark = [pytest.mark.destructive]


def configure_hammer_session(enable=True):
    """take backup of the hammer config file and enable use_sessions"""
    run_command(f'cp {HAMMER_CONFIG} {HAMMER_CONFIG}.backup')
    run_command(f"sed -i '/:use_sessions.*/d' {HAMMER_CONFIG}")
    run_command(f"echo '  :use_sessions: {'true' if enable else 'false'}' >> {HAMMER_CONFIG}")


@pytest.fixture()
def rh_sso_hammer_auth_setup(target_sat, request):
    """rh_sso hammer setup before running the auth login tests"""
    configure_hammer_session()
    client_config = {'publicClient': 'true'}
    update_client_configuration(client_config)

    def rh_sso_hammer_auth_cleanup():
        """restore the hammer config backup file and rhsso client settings"""
        run_command(f'mv {HAMMER_CONFIG}.backup {HAMMER_CONFIG}')
        client_config = {'publicClient': 'false'}
        update_client_configuration(client_config)

    request.addfinalizer(rh_sso_hammer_auth_cleanup)


def test_rhsso_login_using_hammer(
    target_sat,
    enable_external_auth_rhsso,
    rhsso_setting_setup,
    rh_sso_hammer_auth_setup,
):
    """verify the hammer auth login using RHSSO auth source

    :id: 56c09a1a-d0e5-11ea-9024-d46d6dd3b5b2

    :expectedresults: hammer auth login should be suceessful for a rhsso user

    :CaseImportance: High
    """
    result = target_sat.cli.AuthLogin.oauth(
        {
            'oidc-token-endpoint': get_oidc_token_endpoint(),
            'oidc-client-id': get_oidc_client_id(),
            'username': settings.rhsso.rhsso_user,
            'password': settings.rhsso.rhsso_password,
        }
    )
    assert f"Successfully logged in as '{settings.rhsso.rhsso_user}'." == result[0]['message']
    result = target_sat.cli.Auth.with_user(
        username=settings.rhsso.rhsso_user, password=settings.rhsso.rhsso_password
    ).status()
    assert (
        f"Session exists, currently logged in as '{settings.rhsso.rhsso_user}'."
        == result[0]['message']
    )
    task_list = target_sat.cli.Task.with_user(
        username=settings.rhsso.rhsso_user, password=settings.rhsso.rhsso_password
    ).list()
    assert len(task_list) >= 0
    with pytest.raises(CLIReturnCodeError) as error:
        target_sat.cli.Role.with_user(
            username=settings.rhsso.rhsso_user, password=settings.rhsso.rhsso_password
        ).list()
    assert 'Missing one of the required permissions' in error.value.message


def test_rhsso_timeout_using_hammer(
    enable_external_auth_rhsso,
    rhsso_setting_setup_with_timeout,
    rh_sso_hammer_auth_setup,
    module_target_sat,
):
    """verify the hammer auth timeout using RHSSO auth source

    :id: d014cc98-d198-11ea-b526-d46d6dd3b5b2

    :expectedresults: hammer auth login timeout should be suceessful for a rhsso user

    :CaseImportance: Medium
    """
    result = module_target_sat.cli.AuthLogin.oauth(
        {
            'oidc-token-endpoint': get_oidc_token_endpoint(),
            'oidc-client-id': get_oidc_client_id(),
            'username': settings.rhsso.rhsso_user,
            'password': settings.rhsso.rhsso_password,
        }
    )
    assert f"Successfully logged in as '{settings.rhsso.rhsso_user}'." == result[0]['message']
    sleep(70)
    with pytest.raises(CLIReturnCodeError) as error:
        module_target_sat.cli.Task.with_user(
            username=settings.rhsso.rhsso_user, password=settings.rhsso.rhsso_password
        ).list()
    assert 'Unable to authenticate user sat_admin' in error.value.message


def test_rhsso_two_factor_login_using_hammer(
    module_target_sat, rhsso_setting_setup, rh_sso_hammer_auth_setup
):
    """verify the hammer auth login using RHSSO auth source

    :id: 4018c646-cb64-4eae-a422-7d5257ed2756

    :expectedresults: hammer auth login should be suceessful for a rhsso user

    :CaseImportance: Medium
    """
    with module_target_sat.ui_session(login=False) as rhsso_session:
        two_factor_code = rhsso_session.rhsso_login.get_two_factor_login_code(
            {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.rhsso_password},
            get_two_factor_token_rh_sso_url(),
        )
        with open_pxssh_session() as ssh_session:
            ssh_session.sendline(
                f"echo '{two_factor_code['code']}' | hammer auth login oauth "
                f'--oidc-token-endpoint {get_oidc_token_endpoint()} '
                f'--oidc-authorization-endpoint {get_oidc_authorization_endpoint()} '
                f'--oidc-client-id {get_oidc_client_id()} '
                f"--oidc-redirect-uri 'urn:ietf:wg:oauth:2.0:oob' "
                f'--two-factor '
            )
            ssh_session.prompt()  # match the prompt
            result = ssh_session.before.decode()
            assert f"Successfully logged in as '{settings.rhsso.rhsso_user}'." in result
