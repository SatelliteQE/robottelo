"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseComponent: Authentication

:Team: Endeavour

:CaseImportance: High

"""

from time import sleep

import pytest

from robottelo.config import settings
from robottelo.constants import HAMMER_CONFIG
from robottelo.exceptions import CLIReturnCodeError
from robottelo.hosts import RHBKHost

pytestmark = [pytest.mark.destructive]


def configure_hammer_session(sat, enable=True):
    """take backup of the hammer config file and enable use_sessions"""
    sat.execute(f'cp {HAMMER_CONFIG} {HAMMER_CONFIG}.backup')
    sat.execute(f"sed -i '/:use_sessions.*/d' {HAMMER_CONFIG}")
    sat.execute(f"echo '  :use_sessions: {'true' if enable else 'false'}' >> {HAMMER_CONFIG}")


@pytest.fixture
def rh_sso_hammer_auth_setup(module_target_sat, default_sso_host, request):
    """rh_sso hammer setup before running the auth login tests"""
    configure_hammer_session(module_target_sat)
    client_config = {'publicClient': 'true'}
    default_sso_host.update_client_configuration(client_config)
    yield
    module_target_sat.execute(f'mv {HAMMER_CONFIG}.backup {HAMMER_CONFIG}')
    client_config = {'publicClient': 'false'}
    default_sso_host.update_client_configuration(client_config)


@pytest.mark.pit_server
@pytest.mark.parametrize(
    ('default_sso_host', 'rhsso_setting_setup', 'enroll_configure_rhsso_external_auth'),
    [(True, True, True), (False, False, False)],
    ids=['RHBK', 'RHSSO'],
    indirect=True,
)
def test_rhsso_login_using_hammer(
    module_target_sat,
    enable_external_auth_rhsso,
    rhsso_setting_setup,
    rh_sso_hammer_auth_setup,
    default_sso_host,
):
    """verify the hammer auth login using RHSSO auth source

    :id: 56c09a1a-d0e5-11ea-9024-d46d6dd3b5b2

    :expectedresults: hammer auth login should be successful for a rhsso user

    :CaseImportance: High
    """
    if type(default_sso_host) is RHBKHost:
        user = settings.rhbk.rhbk_user
        password = settings.rhbk.rhbk_password
    else:
        user = settings.rhsso.rhsso_user
        password = settings.rhsso.rhsso_password

    result = module_target_sat.cli.AuthLogin.oauth(
        {
            'oidc-token-endpoint': default_sso_host.oidc_token_endpoint,
            'oidc-client-id': default_sso_host.get_oidc_client_id(),
            'username': user,
            'password': password,
        }
    )
    assert f"Successfully logged in as '{user}'." == result[0]['message']
    result = module_target_sat.cli.Auth.with_user(username=user, password=password).status()
    assert f"Session exists, currently logged in as '{user}'." in result[0]['message']
    task_list = module_target_sat.cli.Task.with_user(username=user, password=password).list()
    assert len(task_list) >= 0
    with pytest.raises(CLIReturnCodeError) as error:
        module_target_sat.cli.Role.with_user(username=user, password=password).list()
    assert 'Missing one of the required permissions' in error.value.message


def test_rhsso_timeout_using_hammer(
    enable_external_auth_rhsso,
    rhsso_setting_setup_with_timeout,
    rh_sso_hammer_auth_setup,
    module_target_sat,
    default_sso_host,
):
    """verify the hammer auth timeout using RHSSO auth source

    :id: d014cc98-d198-11ea-b526-d46d6dd3b5b2

    :expectedresults: hammer auth login timeout should be successful for a rhsso user

    :CaseImportance: Medium
    """
    result = module_target_sat.cli.AuthLogin.oauth(
        {
            'oidc-token-endpoint': default_sso_host.oidc_token_endpoint,
            'oidc-client-id': default_sso_host.get_oidc_client_id(),
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
    enable_external_auth_rhsso,
    module_target_sat,
    rhsso_setting_setup,
    rh_sso_hammer_auth_setup,
    default_sso_host,
):
    """verify the hammer auth login using RHSSO auth source

    :id: 4018c646-cb64-4eae-a422-7d5257ed2756

    :expectedresults: hammer auth login should be successful for a rhsso user

    :CaseImportance: Medium
    """
    with module_target_sat.ui_session(login=False) as rhsso_session:
        two_factor_code = rhsso_session.rhsso_login.get_two_factor_login_code(
            {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.rhsso_password},
            default_sso_host.get_two_factor_token_rh_sso_url(),
        )
    # to workaround SAT-25654, fake tty using 'ssh -tt'
    result = module_target_sat.execute(
        f"KEYPATH=/root/$RANDOM; ssh-keygen -f $KEYPATH -N ''; cat $KEYPATH.pub >> /root/.ssh/authorized_keys; ssh -tt -i $KEYPATH -o StrictHostKeyChecking=accept-new root@localhost 'echo '{two_factor_code['code']}' | hammer auth login oauth --oidc-token-endpoint {default_sso_host.oidc_token_endpoint} --oidc-authorization-endpoint {default_sso_host.oidc_authorization_endpoint} --oidc-client-id {default_sso_host.get_oidc_client_id()} --oidc-redirect-uri 'urn:ietf:wg:oauth:2.0:oob' --two-factor'"
    )
    assert f"Successfully logged in as '{settings.rhsso.rhsso_user}'." in result.stdout
