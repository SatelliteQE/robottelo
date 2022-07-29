"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: LDAP

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os
from time import sleep

import pyotp
import pytest
from navmazing import NavigationTriesExceeded

from robottelo.api.utils import create_role_permissions
from robottelo.config import settings
from robottelo.constants import CERT_PATH
from robottelo.constants import LDAP_ATTR
from robottelo.constants import PERMISSIONS
from robottelo.datafactory import gen_string
from robottelo.rhsso_utils import create_group
from robottelo.rhsso_utils import create_new_rhsso_user
from robottelo.rhsso_utils import delete_rhsso_group
from robottelo.rhsso_utils import delete_rhsso_user
from robottelo.rhsso_utils import get_rhsso_client_id
from robottelo.rhsso_utils import run_command
from robottelo.rhsso_utils import update_rhsso_user
from robottelo.utils.issue_handlers import is_open

pytestmark = [pytest.mark.destructive, pytest.mark.run_in_one_thread]

EXTERNAL_GROUP_NAME = 'foobargroup'


def set_certificate_in_satellite(server_type, sat, hostname=None):
    """update the cert settings in satellite based on type of ldap server"""
    if server_type == 'IPA':
        certfile = 'ipa.crt'
        idm_cert_path_url = os.path.join(settings.ipa.hostname, 'ipa/config/ca.crt')
        sat.get(
            remote_path=idm_cert_path_url,
            local_path=CERT_PATH + certfile,
        )
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


@pytest.fixture()
def ldap_tear_down(module_target_sat):
    """Teardown the all ldap settings user, usergroup and ldap delete"""
    yield
    ldap_auth_sources = module_target_sat.api.AuthSourceLDAP().search()
    for ldap_auth in ldap_auth_sources:
        users = module_target_sat.api.User(auth_source=ldap_auth).search()
        for user in users:
            user.delete()
        ldap_auth.delete()


@pytest.fixture()
def external_user_count(module_target_sat):
    """return the external auth source user count"""
    users = module_target_sat.api.User().search()
    yield len([user for user in users if user.auth_source_name == 'External'])


@pytest.fixture()
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


@pytest.fixture()
def rhsso_groups_teardown(module_target_sat):
    """Teardown the rhsso groups"""
    yield
    for group_name in ('sat_users', 'sat_admins'):
        delete_rhsso_group(group_name)


def generate_otp(secret):
    """Return the time_based_otp"""
    time_otp = pyotp.TOTP(secret)
    return time_otp.now()


@pytest.mark.upgrade
@pytest.mark.parametrize('auth_data', ['AD_2016', 'AD_2019', 'IPA'], indirect=True)
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
    with module_target_sat.ui_session(
        test_name, username, auth_data['ldap_user_passwd']
    ) as ldapsession:
        with pytest.raises(NavigationTriesExceeded):
            ldapsession.user.search('')
    users = module_target_sat.api.User().search(
        query={'search': 'login="{}"'.format(auth_data['ldap_user_name'])}
    )
    assert users[0].login == auth_data['ldap_user_name']


def test_single_sign_on_ldap_ipa_server(
    subscribe_satellite, func_enroll_idm_and_configure_external_auth, target_sat
):
    """Verify the single sign-on functionality with external authentication

    :id: 9813a4da-4639-11ea-9780-d46d6dd3b5b2

    :setup: Enroll the IDM Configuration for External Authentication

    :steps: Assert single sign-on session user directed to satellite instead login page

    :expectedresults: After single sign on user should redirected from /extlogin to /hosts page

    """
    # register the satellite with IPA for single sign-on and update external auth
    try:
        run_command(cmd='subscription-manager repos --enable rhel-7-server-optional-rpms')
        run_command(cmd='satellite-installer --foreman-ipa-authentication=true', timeout=800000)
        run_command('satellite-maintain service restart', timeout=300000)
        if is_open('BZ:1941997'):
            curl_command = f'curl -k -u : --negotiate {target_sat.url}/users/extlogin'
        else:
            curl_command = f'curl -k -u : --negotiate {target_sat.url}/users/extlogin/'
        result = run_command(curl_command)
        assert 'redirected' in result
        assert f'{target_sat.url}/hosts' in result
        assert 'You are being' in result
    finally:
        # resetting the settings to default for external auth
        run_command(cmd='satellite-installer --foreman-ipa-authentication=false', timeout=800000)
        run_command('satellite-maintain service restart', timeout=300000)
        run_command(
            cmd=f'ipa service-del HTTP/{target_sat.hostname}',
            hostname=settings.ipa.hostname,
        )
        run_command(
            cmd=f'ipa host-del {target_sat.hostname}',
            hostname=settings.ipa.hostname,
        )


@pytest.mark.parametrize(
    'enroll_ad_and_configure_external_auth', ['AD_2016', 'AD_2019'], indirect=True
)
def test_single_sign_on_ldap_ad_server(
    subscribe_satellite, enroll_ad_and_configure_external_auth, target_sat
):
    """Verify the single sign-on functionality with external authentication

    :id: 3c233aa4-c817-11ea-b105-d46d6dd3b5b2

    :setup: Enroll the AD Configuration for External Authentication

    :steps: Assert single sign-on session user is directed to satellite instead of login page

    :expectedresults: After single sign on, user should be redirected from /extlogin to /users page
        using curl. It should navigate to user's profile page.(verify using url only)

    """
    # register the satellite with AD for single sign-on and update external auth
    try:
        # enable the foreman-ipa-authentication feature
        target_sat.execute('satellite-installer --foreman-ipa-authentication=true', timeout=800000)
        target_sat.execute('systemctl restart gssproxy.service')
        target_sat.execute('systemctl enable gssproxy.service')

        # restart the deamon and httpd services
        httpd_service_content = (
            '.include /lib/systemd/system/httpd.service\n[Service]' '\nEnvironment=GSS_USE_PROXY=1'
        )
        target_sat.execute(f'echo "{httpd_service_content}" > /etc/systemd/system/httpd.service')
        target_sat.execute('systemctl daemon-reload && systemctl restart httpd.service')

        # create the kerberos ticket for authentication
        target_sat.execute(f'echo {settings.ldap.password} | kinit {settings.ldap.username}')
        if is_open('BZ:1941997'):
            curl_command = f'curl -k -u : --negotiate {target_sat.url}/users/extlogin'
        else:
            curl_command = f'curl -k -u : --negotiate {target_sat.url}/users/extlogin/'
        result = target_sat.execute(curl_command)
        assert 'redirected' in result
        assert f'{target_sat.url}/hosts' in result
    finally:
        # resetting the settings to default for external auth
        target_sat.execute('satellite-installer --foreman-ipa-authentication=false', timeout=800000)
        target_sat.execute('satellite-maintain service restart', timeout=300000)


def test_single_sign_on_using_rhsso(
    module_subscribe_satellite, rhsso_setting_setup, enable_external_auth_rhsso, module_target_sat
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


def test_external_logout_rhsso(enable_external_auth_rhsso, rhsso_setting_setup, module_target_sat):
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
    enable_external_auth_rhsso, rhsso_setting_setup_with_timeout, module_target_sat
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
        sleep(360)
        with pytest.raises(NavigationTriesExceeded) as error:
            session.task.read_all(widget_names='current_user')['current_user']
        assert error.typename == 'NavigationTriesExceeded'


def test_external_new_user_login_and_check_count_rhsso(
    enable_external_auth_rhsso, external_user_count, rhsso_setting_setup, module_target_sat
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
    client_id = get_rhsso_client_id()
    user_details = create_new_rhsso_user(client_id)
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
    delete_rhsso_user(user_details['username'])
    with module_target_sat.ui_session(login=False) as rhsso_session:
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.rhsso_login.login(login_details)
            rhsso_session.task.read_all()
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.skip_if_open("BZ:1873439")
def test_login_failure_rhsso_user_if_internal_user_exist(
    enable_external_auth_rhsso,
    rhsso_setting_setup,
    module_org,
    module_location,
    module_target_sat,
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
    client_id = get_rhsso_client_id()
    username = gen_string('alpha')
    module_target_sat.api.User(
        admin=True,
        default_organization=module_org,
        default_location=module_location,
        login=username,
        password=settings.rhsso.rhsso_password,
    ).create()
    external_rhsso_user = create_new_rhsso_user(client_id, username=username)
    login_details = {
        'username': external_rhsso_user['username'],
        'password': settings.rhsso.rhsso_password,
    }
    with module_target_sat.ui_session(login=False) as rhsso_session:
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.rhsso_login.login(login_details)
            rhsso_session.task.read_all()
        assert error.typename == 'NavigationTriesExceeded'


def test_user_permissions_rhsso_user_after_group_delete(
    enable_external_auth_rhsso,
    rhsso_setting_setup,
    session,
    module_org,
    module_location,
    module_target_sat,
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
    username = settings.rhsso.rhsso_user
    location_name = gen_string('alpha')
    login_details = {
        'username': username,
        'password': settings.rhsso.rhsso_password,
    }

    group_name = gen_string('alpha')
    create_group(group_name=group_name)
    update_rhsso_user(username, group_name=group_name)

    # creating satellite external group
    user_group = module_target_sat.cli_factory.make_usergroup({'admin': 1, 'name': group_name})
    external_auth_source = module_target_sat.cli.ExternalAuthSource.info({'name': "External"})
    module_target_sat.cli_factory.make_usergroup_external(
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
    delete_rhsso_group(group_name=group_name)
    with module_target_sat.ui_session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.location.create({'name': location_name})
        assert error.typename == 'NavigationTriesExceeded'


def test_user_permissions_rhsso_user_multiple_group(
    enable_external_auth_rhsso,
    rhsso_setting_setup,
    session,
    module_org,
    module_location,
    groups_teardown,
    rhsso_groups_teardown,
    module_target_sat,
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
    username = settings.rhsso.rhsso_user
    location_name = gen_string('alpha')
    login_details = {
        'username': username,
        'password': settings.rhsso.rhsso_password,
    }
    user_permissions = {'Katello::ActivationKey': PERMISSIONS['Katello::ActivationKey']}
    katello_role = module_target_sat.api.Role().create()
    create_role_permissions(katello_role, user_permissions)

    group_names = ['sat_users', 'sat_admins']
    arguments = [{'role': katello_role}, {'admin': 1}]
    external_auth_source = module_target_sat.cli.ExternalAuthSource.info({'name': "External"})
    for group_name, argument in zip(group_names, arguments):
        # adding/creating rhsso groups
        create_group(group_name=group_name)
        update_rhsso_user(username, group_name=group_name)
        argument['name'] = group_name

        # creating satellite external groups
        user_group = module_target_sat.cli_factory.make_usergroup(argument)
        module_target_sat.cli_factory.make_usergroup_external(
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


def test_totp_user_login(ad_data, module_target_sat):
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
