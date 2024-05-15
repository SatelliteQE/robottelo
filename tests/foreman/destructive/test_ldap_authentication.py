"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseComponent: Authentication

:Team: Endeavour

:CaseImportance: High

"""

import os
from time import sleep

from navmazing import NavigationTriesExceeded
import pyotp
import pytest

from robottelo.config import settings
from robottelo.constants import CERT_PATH, HAMMER_CONFIG, HAMMER_SESSIONS, LDAP_ATTR
from robottelo.exceptions import CLIReturnCodeError
from robottelo.logging import logger
from robottelo.utils.datafactory import gen_string

pytestmark = [pytest.mark.destructive, pytest.mark.run_in_one_thread]

EXTERNAL_GROUP_NAME = 'foobargroup'

NO_KERB_MSG = 'There is no active Kerberos session. Have you run kinit?'
AUTH_FAILED_MSG = (
    'Could not authenticate using negotiation protocol\n  - have you run kinit (for Kerberos)?'
)
NO_SESSION_BUT_KERB_MSG = (
    'No session, but there is an active Kerberos session, that will be used for negotiate login.'
)
AUTH_OK = 'Successfully authenticated using negotiate auth, using the KEYRING principal.'
SESSION_OK = "Session exists, currently logged in as 'current Kerberos user'."
ACCESS_DENIED = 'Access denied\nMissing one of the required permissions: view_hosts'
NO_CREDS = 'Credentials are not configured.'  # status when user not logged in and creds not in conf
USING_CREDS = (
    'Using configured credentials for user'  # status when user not logged in and creds in conf
)
UNABLE_AUTH = 'Unable to authenticate user'  # attempting to do something without being logged in


def set_certificate_in_satellite(server_type, sat, hostname=None):
    """update the cert settings in satellite based on type of ldap server"""
    if server_type == 'IPA':
        certfile = 'ipa.crt'
        idm_cert_path_url = os.path.join(settings.ipa.hostname, 'ipa/config/ca.crt')
        sat.download_file(file_url=idm_cert_path_url, local_path=CERT_PATH, file_name=certfile)
    elif server_type == 'AD':
        certfile = 'satqe-QE-SAT6-AD-CA.cer'
        assert hostname is not None
        sat.execute('yum -y --disableplugin=foreman-protector install cifs-utils')
        command = r'mount -t cifs -o username=administrator,pass={0} //{1}/c\$ /mnt'
        sat.execute(command.format(settings.ldap.password, hostname))
        result = sat.execute(
            f'cp /mnt/Users/Administrator/Desktop/satqe-QE-SAT6-AD-CA.cer {CERT_PATH}'
        )
        if result.status != 0:
            raise AssertionError('Failed to copy the AD server certificate at right path')
    result = sat.execute(f'update-ca-trust extract && restorecon -R {CERT_PATH}')
    if result.status != 0:
        raise AssertionError('Failed to update and trust the certificate')
    sat.execute(f'install /{CERT_PATH}/{certfile} /etc/pki/tls/certs/')
    sat.execute(
        f'ln -s {certfile} /etc/pki/tls/certs/$(openssl x509 '
        f'-noout -hash -in /etc/pki/tls/certs/{certfile}).0'
    )
    result = sat.execute('systemctl restart httpd')
    if result.status != 0:
        raise AssertionError(f'Failed to restart the httpd after applying {server_type} cert')


@pytest.fixture
def ldap_tear_down(module_target_sat):
    """Teardown the all ldap settings user, usergroup and ldap delete"""
    yield
    ldap_auth_sources = module_target_sat.api.AuthSourceLDAP().search()
    for ldap_auth in ldap_auth_sources:
        users = module_target_sat.api.User(auth_source=ldap_auth).search()
        for user in users:
            user.delete()
        ldap_auth.delete()


@pytest.fixture
def external_user_count(module_target_sat):
    """return the external auth source user count"""
    users = module_target_sat.api.User().search()
    return len([user for user in users if user.auth_source_name == 'External'])


@pytest.fixture
def groups_teardown(module_target_sat):
    """teardown for groups created for external/remote groups"""
    yield
    # tier down groups
    for group_name in ('sat_users', 'sat_admins', EXTERNAL_GROUP_NAME):
        user_groups = module_target_sat.api.UserGroup().search(
            query={'search': f'name="{group_name}"'}
        )
        if user_groups:
            user_groups[0].delete()


@pytest.fixture
def rhsso_groups_teardown(module_target_sat, default_sso_host):
    """Teardown the rhsso groups"""
    yield
    for group_name in ('sat_users', 'sat_admins'):
        default_sso_host.delete_rhsso_group(group_name)


@pytest.fixture
def configure_hammer_session(parametrized_enrolled_sat, enable=True):
    """Take backup of the hammer config file and enable use_sessions"""
    parametrized_enrolled_sat.execute(f'cp {HAMMER_CONFIG} {HAMMER_CONFIG}.backup')
    parametrized_enrolled_sat.execute(f"sed -i '/:use_sessions.*/d' {HAMMER_CONFIG}")
    parametrized_enrolled_sat.execute(
        f"echo '  :use_sessions: {'true' if enable else 'false'}' >> {HAMMER_CONFIG}"
    )
    yield
    parametrized_enrolled_sat.execute(f'mv -f {HAMMER_CONFIG}.backup {HAMMER_CONFIG}')


def generate_otp(secret):
    """Return the time_based_otp"""
    time_otp = pyotp.TOTP(secret, digest='SHA1', digits=6, interval=120)
    return time_otp.now()


@pytest.mark.upgrade
@pytest.mark.parametrize('auth_data', ['AD_2019', 'IPA'], indirect=True)
def test_positive_create_with_https(
    session, module_subscribe_satellite, test_name, auth_data, ldap_tear_down, module_target_sat
):
    """Create LDAP auth_source for IDM with HTTPS.

    :id: 7ff3daa4-2317-11ea-aeb8-d46d6dd3b5b2

    :customerscenario: true

    :steps:
        1. Create a new LDAP Auth source with HTTPS, provide organization and
           location information.
        2. Fill in all the fields appropriately.
        3. Login with existing LDAP user present.

    :BZ: 1785621

    :expectedresults: LDAP auth source for HTTPS should be successful and LDAP login
        should work as expected.

    :parametrized: yes
    """
    if auth_data['auth_type'] == 'ipa':
        set_certificate_in_satellite(server_type='IPA', sat=module_target_sat)
        username = settings.ipa.user
    else:
        set_certificate_in_satellite(
            server_type='AD', sat=module_target_sat, hostname=auth_data['ldap_hostname']
        )
        username = settings.ldap.username
    org = module_target_sat.api.Organization().create()
    loc = module_target_sat.api.Location().create()
    ldap_auth_name = gen_string('alphanumeric')

    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': auth_data['ldap_hostname'],
                'ldap_server.ldaps': True,
                'ldap_server.server_type': auth_data['server_type'],
                'account.account_name': auth_data['ldap_user_cn'],
                'account.password': auth_data['ldap_user_passwd'],
                'account.base_dn': auth_data['base_dn'],
                'account.groups_base_dn': auth_data['group_base_dn'],
                'account.onthefly_register': True,
                'attribute_mappings.login': auth_data['attr_login'],
                'attribute_mappings.first_name': LDAP_ATTR['firstname'],
                'attribute_mappings.last_name': LDAP_ATTR['surname'],
                'attribute_mappings.mail': LDAP_ATTR['mail'],
                'locations.resources.assigned': [loc.name],
                'organizations.resources.assigned': [org.name],
            }
        )
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        assert session.ldapauthentication.read_table_row(ldap_auth_name)['Name'] == ldap_auth_name
        ldap_source = session.ldapauthentication.read(ldap_auth_name)
        assert ldap_source['ldap_server']['name'] == ldap_auth_name
        assert ldap_source['ldap_server']['host'] == auth_data['ldap_hostname']
        assert ldap_source['ldap_server']['port'] == '636'
    with (
        module_target_sat.ui_session(
            test_name, username, auth_data['ldap_user_passwd']
        ) as ldapsession,
        pytest.raises(NavigationTriesExceeded),
    ):
        ldapsession.user.search('')
    assert module_target_sat.api.User().search(query={'search': f'login="{username}"'})


def test_single_sign_on_ldap_ipa_server(
    subscribe_satellite, func_enroll_idm_and_configure_external_auth, target_sat
):
    """Verify the single sign-on functionality with external authentication

    :id: 9813a4da-4639-11ea-9780-d46d6dd3b5b2

    :setup: Enroll the IDM Configuration for External Authentication

    :steps: Assert single sign-on session user directed to satellite instead login page

    :expectedresults: After single sign on user should redirected from /extlogin to /hosts page

    :BZ: 1941997
    """
    result = target_sat.execute(f'echo {settings.ipa.password} | kinit {settings.ipa.user}')
    assert result.status == 0
    result = target_sat.execute(f'curl -k -u : --negotiate {target_sat.url}/users/extlogin/')
    assert 'redirected' in result.stdout
    assert f'{target_sat.url}/hosts' in result.stdout


@pytest.mark.parametrize('func_enroll_ad_and_configure_external_auth', ['AD_2019'], indirect=True)
def test_single_sign_on_ldap_ad_server(
    subscribe_satellite, func_enroll_ad_and_configure_external_auth, target_sat
):
    """Verify the single sign-on functionality with external authentication

    :id: 3c233aa4-c817-11ea-b105-d46d6dd3b5b2

    :setup: Enroll the AD Configuration for External Authentication

    :steps: Assert single sign-on session user is directed to satellite instead of login page

    :expectedresults: After single sign on, user should be redirected from /extlogin to /hosts page
        using curl. It should navigate to hosts page. (verify using url only)

    :BZ: 1941997
    """
    # create the kerberos ticket for authentication
    result = target_sat.execute(f'echo {settings.ldap.password} | kinit {settings.ldap.username}')
    assert result.status == 0
    result = target_sat.execute(f'curl -k -u : --negotiate {target_sat.url}/users/extlogin/')
    assert 'redirected' in result.stdout
    assert f'{target_sat.url}/hosts' in result.stdout


def test_single_sign_on_using_rhsso(
    enable_external_auth_rhsso, rhsso_setting_setup, module_target_sat
):
    """Verify the single sign-on functionality with external authentication RH-SSO

    :id: 18a77de8-570f-11ea-a202-d46d6dd3b5b2

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Create Mappers on RHSSO Instance and Update the Settings in Satellite
        2. Login into Satellite using RHSSO login page redirected by Satellite

    :expectedresults: After entering the login details in RHSSO page user should
        logged into Satellite
    """
    with module_target_sat.ui_session(login=False) as session:
        session.rhsso_login.login(
            {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.rhsso_password}
        )
        with pytest.raises(NavigationTriesExceeded):
            session.user.search('')
        actual_user = session.task.read_all(widget_names="current_user")['current_user']
        assert settings.rhsso.rhsso_user in actual_user


def test_external_logout_rhsso(rhsso_setting_setup, enable_external_auth_rhsso, module_target_sat):
    """Verify the external logout page navigation with external authentication RH-SSO

    :id: 87b5e08e-69c6-11ea-8126-e74d80ea4308

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Create Mappers on RHSSO Instance and Update the Settings in Satellite
        2. Login into Satellite using RHSSO login page redirected by Satellite
        3. Logout from Satellite and Verify the external_logout page displayed

    :expectedresults: After logout from Satellite navigate should be external_loout page
    """
    with module_target_sat.ui_session(login=False) as session:
        login_details = {
            'username': settings.rhsso.rhsso_user,
            'password': settings.rhsso.rhsso_password,
        }
        session.rhsso_login.login(login_details)
        view = session.rhsso_login.logout()
        assert view['login_again'] == 'Click to log in again'
        session.rhsso_login.login(login_details, external_login=True)
        actual_user = session.task.read_all(widget_names='current_user')['current_user']
        assert settings.rhsso.rhsso_user in actual_user


def test_session_expire_rhsso_idle_timeout(
    rhsso_setting_setup,
    enable_external_auth_rhsso,
    rhsso_setting_setup_with_timeout,
    module_target_sat,
    default_sso_host,
):
    """Verify the idle session expiration timeout with external authentication RH-SSO

    :id: 80247b30-a988-11ea-943c-d46d6dd3b5b2

    :steps:
        1. Change the idle timeout settings for the External Authentication
        2. Login into Satellite using RHSSO login and wait for the idle timeout

    :CaseImportance: Medium

    :expectedresults: After completion of the idle timeout user session
        should get expired
    """
    with module_target_sat.ui_session(login=False) as session:
        session.rhsso_login.login(
            {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.rhsso_password}
        )
        sleep(
            150
        )  # give the browser some time to actually logout, even though Satellite should terminate session after one minute
        with pytest.raises(NavigationTriesExceeded) as error:
            session.task.read_all(widget_names='current_user')['current_user']
        assert error.typename == 'NavigationTriesExceeded'


def test_external_new_user_login_and_check_count_rhsso(
    enable_external_auth_rhsso,
    rhsso_setting_setup,
    external_user_count,
    module_target_sat,
    default_sso_host,
):
    """Verify the external new user login and verify the external user count

    :id: bf938ea2-6df9-11ea-a7cf-951107ed0bbb

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :CaseImportance: Medium

    :steps:
        1. Create new user on RHSSO Instance and Update the Settings in Satellite
        2. Verify the login for that user

    :CaseImportance: Medium

    :expectedresults: New User created in RHSSO server should able to get log-in
        and correct count shown for external users
    """
    client_id = default_sso_host.get_rhsso_client_id()
    user_details = default_sso_host.create_new_rhsso_user(client_id)
    login_details = {
        'username': user_details['username'],
        'password': settings.rhsso.rhsso_password,
    }
    with module_target_sat.ui_session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        actual_user = rhsso_session.task.read_all(widget_names='current_user')['current_user']
        assert user_details['firstName'] in actual_user
    users = module_target_sat.api.User().search()
    updated_count = len([user for user in users if user.auth_source_name == 'External'])
    assert updated_count == external_user_count + 1
    # checking delete user can't login anymore
    default_sso_host.delete_rhsso_user(user_details['username'])
    with module_target_sat.ui_session(login=False) as rhsso_session:
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.rhsso_login.login(login_details)
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.task.read_all()
        assert error.typename == 'NavigationTriesExceeded'


def test_login_failure_rhsso_user_if_internal_user_exist(
    rhsso_setting_setup,
    enable_external_auth_rhsso,
    module_org,
    module_location,
    module_target_sat,
    default_sso_host,
):
    """Verify the failure of login for the external rhsso user in case same username
    internal user exists

    :id: e573902c-ed1a-11ea-835a-d46d6dd3b5b2

    :BZ: 1873439

    :customerscenario: true

    :CaseImportance: High

    :steps:
        1. create an internal user
        2. create a rhsso user with same username mentioned in internal user
        3. update the satellite to use rhsso and now try login using external rhsso user

    :expectedresults: external rhsso user should not able to login with same username as internal
    """
    username = gen_string('alpha')
    module_target_sat.api.User(
        admin=True,
        default_organization=module_org,
        default_location=module_location,
        login=username,
        password=settings.rhsso.rhsso_password,
    ).create()
    external_rhsso_user = default_sso_host.create_new_rhsso_user(username=username)
    login_details = {
        'username': external_rhsso_user['username'],
        'password': settings.rhsso.rhsso_password,
    }
    with module_target_sat.ui_session(login=False) as rhsso_session:
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.rhsso_login.login(login_details)
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.task.read_all()
        assert error.typename == 'NavigationTriesExceeded'


def test_user_permissions_rhsso_user_after_group_delete(
    rhsso_setting_setup,
    enable_external_auth_rhsso,
    session,
    module_org,
    module_location,
    module_target_sat,
    default_sso_host,
):
    """Verify the rhsso user permissions in satellite should get revoked after the
        termination of rhsso user's external rhsso group

    :id: 782926c0-d109-41a0-af7a-bffd658f59d7

    :CaseImportance: Medium

    :steps:
        1. create usergroup with admin permissions respectively
        2. assigned that group to rhsso user
        3. verify the permission of the rhsso user in Satellite
        4. delete the rhsso group

    :expectedresults: external rhsso user's permissions should get revoked after external rhsso
        group deletion.
    """
    default_sso_host.get_rhsso_client_id()
    username = settings.rhsso.rhsso_user
    location_name = gen_string('alpha')
    login_details = {
        'username': username,
        'password': settings.rhsso.rhsso_password,
    }

    group_name = gen_string('alpha')
    default_sso_host.create_group(group_name=group_name)
    default_sso_host.update_rhsso_user(username, group_name=group_name)

    # creating satellite external group
    user_group = module_target_sat.cli_factory.usergroup({'admin': 1, 'name': group_name})
    external_auth_source = module_target_sat.cli.ExternalAuthSource.info({'name': "External"})
    module_target_sat.cli_factory.usergroup_external(
        {
            'auth-source-id': external_auth_source['id'],
            'user-group-id': user_group['id'],
            'name': group_name,
        }
    )

    # verify the rhsso-user permissions
    with module_target_sat.ui_session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        rhsso_session.location.create({'name': location_name})
        assert rhsso_session.location.search(location_name)[0]['Name'] == location_name
        current_user = rhsso_session.location.read(location_name, 'current_user')['current_user']
        assert login_details['username'] in current_user

    # delete the rhsso group and verify the rhsso-user permissions
    default_sso_host.delete_rhsso_group(group_name=group_name)
    with module_target_sat.ui_session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.location.create({'name': location_name})
        assert error.typename == 'NavigationTriesExceeded'


def test_user_permissions_rhsso_user_multiple_group(
    rhsso_setting_setup,
    enable_external_auth_rhsso,
    session,
    module_org,
    module_location,
    groups_teardown,
    rhsso_groups_teardown,
    module_target_sat,
    default_sso_host,
):
    """Verify the permissions of the rhsso user, if it exists in multiple groups (admin/non-admin).
        The rhsso user should contain the highest level of permissions from among the
        multiple groups. In this case, it should contain the admin permissions.

    :id: 311a2180-d5ea-4bbb-a147-25697fdebac7

    :CaseImportance: Medium

    :steps:
        1. create sat_users and sat_admins usergroups with non-admin and admin
            permissions respectively
        2. assigned these groups to rhsso user
        3. verify the permission of the rhsso user in Satellite

    :expectedresults: external rhsso user have highest level of permissions from among the
        multiple groups.
    """
    default_sso_host.get_rhsso_client_id()
    username = settings.rhsso.rhsso_user
    location_name = gen_string('alpha')
    login_details = {
        'username': username,
        'password': settings.rhsso.rhsso_password,
    }
    katello_role = module_target_sat.api.Role().create()
    module_target_sat.api.Filter(
        role=katello_role,
        permission=module_target_sat.api.Permission().search(
            query={'search': 'resource_type="Katello::ActivationKey"'}
        ),
    ).create()

    group_names = ['sat_users', 'sat_admins']
    arguments = [{'roles': katello_role.name}, {'admin': 1}]
    external_auth_source = module_target_sat.cli.ExternalAuthSource.info({'name': "External"})
    for group_name, argument in zip(group_names, arguments, strict=True):
        # adding/creating rhsso groups
        default_sso_host.create_group(group_name=group_name)
        default_sso_host.update_rhsso_user(username, group_name=group_name)
        argument['name'] = group_name

        # creating satellite external groups
        user_group = module_target_sat.cli_factory.usergroup(argument)
        module_target_sat.cli_factory.usergroup_external(
            {
                'auth-source-id': external_auth_source['id'],
                'user-group-id': user_group['id'],
                'name': group_name,
            }
        )

    # verify that user has highest level of permission
    with module_target_sat.ui_session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        rhsso_session.location.create({'name': location_name})
        assert rhsso_session.location.search(location_name)[0]['Name'] == location_name
        current_user = rhsso_session.location.read(location_name, 'current_user')['current_user']
        assert login_details['username'] in current_user


def test_totp_user_login(
    enable_external_auth_rhsso, rhsso_setting_setup, ad_data, module_target_sat
):
    """Verify the TOTP authentication of LDAP user interlinked with RH-SSO

    :id: cf8dfa00-4f48-11eb-b7d5-d46d6dd3b5b2

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Setup the Satellite to integrate with RHSSO
        2. Login into Satellite using LDAP user which is linked to RHSSO

    :CaseImportance: Medium

    :expectedresults: After entering the login details in RHSSO page user should
        logged into Satellite
    """
    ad_data = ad_data()
    login_details = {
        'username': ad_data['ldap_user_name'],
        'password': ad_data['ldap_user_passwd'],
    }
    with module_target_sat.ui_session(login=False) as rhsso_session:
        totp = generate_otp(secret=settings.rhsso.totp_secret)
        rhsso_session.rhsso_login.login(login_details, totp={'totp': totp})
        assert rhsso_session.bookmark.search("controller = hosts")


def test_permissions_external_ldap_mapped_rhsso_group(
    rhsso_setting_setup, ad_data, groups_teardown, module_target_sat
):
    """Verify the usergroup permissions are synced correctly with LDAP usergroup mapped
        with the rhsso. The ldap user gets right permissions based on the role

    :id: a7bd84b8-4f6c-11eb-8eb2-d46d6dd3b5b2

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Setup the Satellite to integrate with RHSSO
        2. Create the user group and mapped with the external ldap rhsso user group

    :CaseImportance: Medium

    :expectedresults: The external ldap mapped rhsso user should contain the permissions
        based on the user group level
    """
    ad_data = ad_data()
    login_details = {
        'username': ad_data['ldap_user_name'],
        'password': ad_data['ldap_user_passwd'],
    }
    with module_target_sat.ui_session(url='/users/login/') as session:
        session.usergroup.create(
            {
                'usergroup.name': EXTERNAL_GROUP_NAME,
                'roles.resources.assigned': ['Viewer'],
                'external_groups.name': EXTERNAL_GROUP_NAME,
                'external_groups.auth_source': 'EXTERNAL',
            }
        )

    with module_target_sat.ui_session(login=False) as rhsso_session:
        totp = generate_otp(secret=settings.rhsso.totp_secret)
        rhsso_session.rhsso_login.login(login_details, totp={'totp': totp})
        assert rhsso_session.user.search(ad_data['ldap_user_name']) is not None


def test_negative_negotiate_login_without_ticket(
    parametrized_enrolled_sat,
    configure_ipa_api,
    configure_hammer_negotiate,
):
    """Verify that login nor other hammer commands work without
    the Kerberos ticket and proper messages are displayed.

    :id: 5815ba45-7e77-4390-b350-483ee853ab90

    :parametrized: yes

    :setup: Enroll the AD Configuration for External Authentication

    :steps:
        1. Check auth status.
        2. Try to negotiate login without Kerberos ticket.
        3. Try to list hosts.

    :expectedresults:
        1. Proper messages are returned in all cases.
        2. Login and hosts listing fails without Kerberos ticket.
    """
    result = parametrized_enrolled_sat.cli.Auth.status()
    assert NO_KERB_MSG in str(result)

    with pytest.raises(CLIReturnCodeError) as context:
        parametrized_enrolled_sat.cli.AuthLogin.negotiate()
    assert AUTH_FAILED_MSG in context.value.message

    with pytest.raises(CLIReturnCodeError) as context:
        parametrized_enrolled_sat.cli.Host.list()
    assert AUTH_FAILED_MSG in context.value.message


def test_positive_negotiate_login_with_ticket(
    request,
    parametrized_enrolled_sat,
    configure_ipa_api,
    configure_hammer_negotiate,
    sessions_tear_down,
):
    """Verify that we are able to log in, user is created but access restricted.

    :id: 87ebbb79-f2b8-4fbc-83af-6358b2f0749f

    :parametrized: yes

    :setup: Enroll the AD Configuration for External Authentication

    :steps:
        1. Get Kerberos ticket, check for status.
        2. Log in using the ticket, check it succeeds.
        3. Verify an external user is created without permissions and enforcing works.

    :expectedresults:
        1. Kerberos ticket can be acquired.
        2. Negotiate login works with the ticket.
        3. External user is created and permissions enforcing works.
        4. Proper messages are returned in all cases.
    """
    auth_type = request.node.callspec.params['parametrized_enrolled_sat']
    user = (
        settings.ipa.user
        if 'IDM' in auth_type
        else f'{settings.ldap.username}@{settings.ldap.realm}'
    )
    password = settings.ipa.password if 'IDM' in auth_type else settings.ldap.password

    result = parametrized_enrolled_sat.execute(f'echo {password} | kinit {user}')
    assert result.status == 0
    result = parametrized_enrolled_sat.execute('klist')
    assert f'Default principal: {user}' in result.stdout
    result = parametrized_enrolled_sat.cli.Auth.status()
    assert NO_SESSION_BUT_KERB_MSG in str(result)

    # Log in and check for status
    result = parametrized_enrolled_sat.cli.AuthLogin.negotiate()
    assert AUTH_OK in str(result)
    result = parametrized_enrolled_sat.cli.Auth.status()
    assert SESSION_OK in str(result)

    # Check the user was created in the Satellite without any permissions
    user = parametrized_enrolled_sat.api.User().search(query={'search': f'login={user.lower()}'})
    assert len(user) == 1
    user = user[0].read()
    assert user.auth_source_name == 'External'
    assert not user.admin
    assert len(user.role) == 0

    # Check permission enforcing works for the new user
    with pytest.raises(CLIReturnCodeError) as context:
        parametrized_enrolled_sat.cli.Host.list()
    assert ACCESS_DENIED in context.value.message


def test_positive_negotiate_CRUD(
    request,
    parametrized_enrolled_sat,
    configure_ipa_api,
    configure_hammer_negotiate,
    sessions_tear_down,
):
    """Verify that basic CRUD operations work with hammer.

    :id: 2f3bd6d3-3fb6-4f53-9ee0-68ed4f3ebb7f

    :parametrized: yes

    :setup: Enroll the AD Configuration for External Authentication

    :steps:
        1. Get Kerberos ticket, check for status.
        2. Add permissions to the new user.
        3. Perform listing and CRUD operations via hammer.
        4. Remove permissions from the user.

    :expectedresults:
        1. Kerberos ticket can be acquired.
        2. Automatic login occurs on first hammer command.
        3. Listing and CRUD operations via hammer succeed.

    :BZ: 2122617
    """
    auth_type = request.node.callspec.params['parametrized_enrolled_sat']
    user = (
        settings.ipa.user
        if 'IDM' in auth_type
        else f'{settings.ldap.username}@{settings.ldap.realm}'
    )
    password = settings.ipa.password if 'IDM' in auth_type else settings.ldap.password

    result = parametrized_enrolled_sat.execute(f'echo {password} | kinit {user}')
    assert result.status == 0

    # Add the permissions for CRUD operations
    user = parametrized_enrolled_sat.api.User().search(query={'search': f'login={user.lower()}'})[0]
    role = parametrized_enrolled_sat.api.Role().search(query={'search': 'name="Manager"'})[0]
    user.role = [role]
    user.update(['role'])

    # Check that listing and automatic login on first hammer
    # command (when Kerberos ticket exists) succeeds.
    result = parametrized_enrolled_sat.cli.Architecture.list()
    assert len(result)
    result = parametrized_enrolled_sat.cli.Auth.status()
    assert SESSION_OK in str(result)

    # Create
    name = gen_string('alphanumeric')
    arch = parametrized_enrolled_sat.cli.Architecture.create({'name': name})

    # Read
    arch_read = parametrized_enrolled_sat.cli.Architecture.info({'name': name})
    assert arch_read == arch

    # Update
    new_name = gen_string('alphanumeric')
    result = parametrized_enrolled_sat.cli.Architecture.update({'name': name, 'new-name': new_name})
    assert 'updated' in str(result)
    arch_read = parametrized_enrolled_sat.cli.Architecture.info({'name': new_name})
    assert arch_read['name'] == new_name

    # Delete
    result = parametrized_enrolled_sat.cli.Architecture.delete({'name': new_name})
    assert 'deleted' in result
    with pytest.raises(CLIReturnCodeError) as context:
        parametrized_enrolled_sat.cli.Architecture.info({'name': new_name})
    assert 'not found' in context.value.message

    # Remove the permissions
    user.role = []
    user.update(['role'])


def test_positive_negotiate_logout(
    request,
    parametrized_enrolled_sat,
    configure_ipa_api,
    configure_hammer_negotiate,
    sessions_tear_down,
):
    """Verify the logout behaves properly.

    :id: 30baeea2-b07f-468f-8c26-58d59c118742

    :parametrized: yes

    :setup: Enroll the AD Configuration for External Authentication

    :steps:
        1. Get Kerberos ticket and log in.
        2. Log out and check the session was closed properly.
        3. Verify that next hammer command fails.

    :expectedresults:
        1. Session is closed on log out properly on logout.
        2. Hammer command fails after log out.
        3. Proper messages are returned in all cases.
    """
    auth_type = request.node.callspec.params['parametrized_enrolled_sat']
    user = (
        settings.ipa.user
        if 'IDM' in auth_type
        else f'{settings.ldap.username}@{settings.ldap.realm}'
    )
    password = settings.ipa.password if 'IDM' in auth_type else settings.ldap.password

    result = parametrized_enrolled_sat.execute(f'echo {password} | kinit {user}')
    assert result.status == 0
    result = parametrized_enrolled_sat.cli.AuthLogin.negotiate()
    assert AUTH_OK in str(result)

    # Log out, verify the hammer sessions was closed
    result = parametrized_enrolled_sat.cli.Auth.logout()
    assert 'Logged out.' in str(result)
    result = parametrized_enrolled_sat.execute(
        f'cat {HAMMER_SESSIONS}/https_{parametrized_enrolled_sat.hostname}'
    )
    assert '"id":null' in result.stdout
    result = parametrized_enrolled_sat.cli.Auth.status()
    assert NO_SESSION_BUT_KERB_MSG in str(result)

    # Destroy the ticket so no new session is open
    # and verify that hammer command cannot pass
    parametrized_enrolled_sat.execute('kdestroy')
    with pytest.raises(CLIReturnCodeError) as context:
        parametrized_enrolled_sat.cli.Host.list()
    assert AUTH_FAILED_MSG in context.value.message


@pytest.mark.parametrize(
    ('parametrized_enrolled_sat', 'user_not_exists'),
    [('IDM', settings.ipa.user), ('AD', f'{settings.ldap.username}@{settings.ldap.realm.lower()}')],
    indirect=True,
    ids=['IDM', 'AD'],
)
def test_positive_autonegotiate(
    request,
    parametrized_enrolled_sat,
    configure_ipa_api,
    configure_hammer_negotiate,
    sessions_tear_down,
    user_not_exists,
    hammer_logout,
):
    """Verify that when logged out, negotiation happens automatically with ticket

    :id: 2f3bd6d3-3fb6-4f53-7ee0-68bd4faebb7f

    :parametrized: yes

    :setup: Kerberized sat with API krb authn and autonegotiation enabled

    :steps:
        1. Get Kerberos ticket, check for status.
        2. Attempt to do some API operation.

    :expectedresults:
        1. Kerberos ticket can be acquired.
        2. Automatic login occurs on first hammer command, user is created
    """
    auth_type = request.node.callspec.params['parametrized_enrolled_sat']
    user = (
        settings.ipa.user
        if 'IDM' in auth_type
        else f'{settings.ldap.username}@{settings.ldap.realm}'
    )
    password = settings.ipa.password if 'IDM' in auth_type else settings.ldap.password

    result = parametrized_enrolled_sat.execute(f'echo {password} | kinit {user}')
    assert result.status == 0

    # Try to do an operation with user not yet added.
    # Expect the user to get added and access denied.
    with pytest.raises(CLIReturnCodeError) as exc:
        result = parametrized_enrolled_sat.cli.Host.list()
    assert ACCESS_DENIED in exc.value.stderr
    user = parametrized_enrolled_sat.api.User().search(query={'search': f'login={user.lower()}'})
    assert len(user) == 1
    user = user[0].read()
    assert user.auth_source_name == 'External'
    assert not user.admin
    assert len(user.role) == 0


@pytest.mark.parametrize(
    ('parametrized_enrolled_sat', 'user_not_exists'),
    [('IDM', settings.ipa.user), ('AD', f'{settings.ldap.username}@{settings.ldap.realm.lower()}')],
    indirect=True,
    ids=['IDM', 'AD'],
)
def test_positive_negotiate_manual_with_autonegotiation_disabled(
    request,
    parametrized_enrolled_sat,
    configure_ipa_api,
    configure_hammer_no_negotiate,
    configure_hammer_no_creds,
    configure_hammer_session,
    sessions_tear_down,
    user_not_exists,
    hammer_logout,
):
    """Negotiation works manually when autonegotiation is disabled.

    :id: 87ebbb79-c2b8-4fbc-83af-6358b2f0749d

    :parametrized: yes

    :setup: Kerberized sat with API krb authn and autonegotiation enabled

    :steps:
        1. Get Kerberos ticket, check for status.
        2. Log in manually using the ticket.
        3. Attempt to do some API operation.

    :expectedresults:
        1. Kerberos ticket can be acquired.
        2. Manual login successful, user is created.
        3. Session is kept for following Hammer commands.
    """
    with parametrized_enrolled_sat.omit_credentials():
        auth_type = request.node.callspec.params['parametrized_enrolled_sat']
        user = (
            settings.ipa.user
            if 'IDM' in auth_type
            else f'{settings.ldap.username}@{settings.ldap.realm}'
        )
        password = settings.ipa.password if 'IDM' in auth_type else settings.ldap.password

        result = parametrized_enrolled_sat.execute(f'echo {password} | kinit {user}')
        assert result.status == 0
        result = parametrized_enrolled_sat.execute('klist')
        assert f'Default principal: {user}' in result.stdout
        result = parametrized_enrolled_sat.cli.Auth.status()
        # negotiation disabled so no mention of Kerberos
        assert NO_CREDS in str(result)

        # Log in and check for status
        result = parametrized_enrolled_sat.cli.AuthLogin.negotiate()
        assert AUTH_OK in str(result)
        result = parametrized_enrolled_sat.cli.Auth.status()
        assert SESSION_OK in str(result)

        # Check the user was created in the Satellite without any permissions
        users = parametrized_enrolled_sat.api.User().search(
            query={'search': f'login={user.lower()}'}
        )
        logger.info(f'Users after login: {users}')
        assert len(users) == 1
        user = users[0].read()
        assert user.auth_source_name == 'External'
        assert not user.admin
        assert len(user.role) == 0

        # Check permission enforcing works for the new user
        with pytest.raises(CLIReturnCodeError) as exc:
            parametrized_enrolled_sat.cli.Host.list()
        assert ACCESS_DENIED in exc.value.message


@pytest.mark.parametrize(
    'configure_hammer_session',
    [True, False],
    indirect=True,
    ids=['sessions_enabled', 'sessions_disabled'],
)
@pytest.mark.parametrize(
    ('parametrized_enrolled_sat', 'user_not_exists'),
    [('IDM', settings.ipa.user), ('AD', f'{settings.ldap.username}@{settings.ldap.realm.lower()}')],
    indirect=True,
    ids=['IDM', 'AD'],
)
def test_negative_autonegotiate_with_autonegotiation_disabled(
    request,
    parametrized_enrolled_sat,
    configure_ipa_api,
    configure_hammer_no_negotiate,
    configure_hammer_no_creds,
    configure_hammer_session,
    sessions_tear_down,
    user_not_exists,
    hammer_logout,
):
    """Autonegotiation doesn't occur when it's disabled

    :id: 87ebbb79-f5b8-4fbc-83af-6358b2f0749e

    :parametrized: yes

    :setup: Kerberized sat with API krb authn and autonegotiation enabled

    :steps:
        1. Get Kerberos ticket, check for status.
        2. Attempt to do some API operation.

    :expectedresults:
        1. Kerberos ticket can be acquired.
        2. Autonegotiation doesn't occur
        3. Action is denied and user not created because the user isn't authenticated.
    """
    with parametrized_enrolled_sat.omit_credentials():
        auth_type = request.node.callspec.params['parametrized_enrolled_sat']
        user = (
            settings.ipa.user
            if 'IDM' in auth_type
            else f'{settings.ldap.username}@{settings.ldap.realm}'
        )
        password = settings.ipa.password if 'IDM' in auth_type else settings.ldap.password

        result = parametrized_enrolled_sat.execute(f'echo {password} | kinit {user}')
        assert result.status == 0
        result = parametrized_enrolled_sat.execute('klist')
        assert f'Default principal: {user}' in result.stdout
        result = parametrized_enrolled_sat.cli.Auth.status()
        # negotiation disabled so no mention of Kerberos
        assert NO_CREDS in str(result)

        # Attempt to do something using autonegotiate. It should fail since it is disabled.
        with pytest.raises(CLIReturnCodeError) as exc:
            parametrized_enrolled_sat.cli.Host.list()
        assert UNABLE_AUTH in exc.value.message
        # User has not been added
        user = parametrized_enrolled_sat.api.User().search(query={'search': f'login={user}'})
        assert not user
