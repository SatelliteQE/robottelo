"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: LDAP

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import copy
import os

import decorator
import pyotp
from airgun.session import Session
from fauxfactory import gen_url
from nailgun import entities
from navmazing import NavigationTriesExceeded
from pytest import raises
from pytest import skip

from robottelo import ssh
from robottelo.api.utils import create_role_permissions
from robottelo.config import settings
from robottelo.constants import AUDIENCE_MAPPER
from robottelo.constants import CERT_PATH
from robottelo.constants import GROUP_MEMBERSHIP_MAPPER
from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE
from robottelo.constants import PERMISSIONS
from robottelo.datafactory import gen_string
from robottelo.decorators import destructive
from robottelo.decorators import fixture
from robottelo.decorators import run_in_one_thread
from robottelo.decorators import setting_is_set
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier2
from robottelo.decorators import upgrade
from robottelo.helpers import file_downloader
from robottelo.rhsso_utils import create_mapper
from robottelo.rhsso_utils import create_new_rhsso_user
from robottelo.rhsso_utils import delete_rhsso_user
from robottelo.rhsso_utils import get_rhsso_client_id
from robottelo.rhsso_utils import run_command


pytestmark = [run_in_one_thread]


EXTERNAL_GROUP_NAME = 'foobargroup'

if not setting_is_set('ldap'):
    skip('skipping tests due to missing ldap settings', allow_module_level=True)


def set_certificate_in_satellite(server_type):
    """update the cert settings in satellite based on type of ldap server"""
    if server_type == 'IPA':
        idm_cert_path_url = os.path.join(settings.ipa.hostname_ipa, 'ipa/config/ca.crt')
        file_downloader(
            file_url=idm_cert_path_url,
            local_path=CERT_PATH,
            file_name='ipa.crt',
            hostname=settings.server.hostname,
        )
    elif server_type == 'AD':
        ssh.command('yum -y --disableplugin=foreman-protector install cifs-utils')
        command = r'mount -t cifs -o username=administrator,pass={0} //{1}/c\$ /mnt'
        ssh.command(command.format(settings.ldap.password, settings.ldap.hostname))
        result = ssh.command(
            'cp /mnt/Users/Administrator/Desktop/satqe-QE-SAT6-AD-CA.cer {}'.format(CERT_PATH)
        )
        if result.return_code != 0:
            raise AssertionError('Failed to copy the AD server certificate at right path')
    result = ssh.command('update-ca-trust extract && restorecon -R {}'.format(CERT_PATH))
    if result.return_code != 0:
        raise AssertionError('Failed to update and trust the certificate')
    result = ssh.command('systemctl restart httpd')
    if result.return_code != 0:
        raise AssertionError(
            'Failed to restart the httpd after applying {} cert'.format(server_type)
        )


@fixture(scope='module')
def ldap_data():
    return {
        'ldap_user_name': settings.ldap.username,
        'ldap_user_passwd': settings.ldap.password,
        'base_dn': settings.ldap.basedn,
        'group_base_dn': settings.ldap.grpbasedn,
        'ldap_hostname': settings.ldap.hostname,
    }


@fixture(scope='module')
def ipa_data():
    return {
        'ldap_ipa_user_name': settings.ipa.username_ipa,
        'ipa_otp_username': settings.ipa.otp_user,
        'ldap_ipa_user_passwd': settings.ipa.password_ipa,
        'ipa_base_dn': settings.ipa.basedn_ipa,
        'ipa_group_base_dn': settings.ipa.grpbasedn_ipa,
        'ldap_ipa_hostname': settings.ipa.hostname_ipa,
        'time_based_secret': settings.ipa.time_based_secret,
    }


@fixture(scope='function')
def auth_source(ldap_data, module_org, module_loc):
    return entities.AuthSourceLDAP(
        onthefly_register=True,
        account=ldap_data['ldap_user_name'],
        account_password=ldap_data['ldap_user_passwd'],
        base_dn=ldap_data['base_dn'],
        groups_base=ldap_data['group_base_dn'],
        attr_firstname=LDAP_ATTR['firstname'],
        attr_lastname=LDAP_ATTR['surname'],
        attr_login=LDAP_ATTR['login_ad'],
        server_type=LDAP_SERVER_TYPE['API']['ad'],
        attr_mail=LDAP_ATTR['mail'],
        name=gen_string('alpha'),
        host=ldap_data['ldap_hostname'],
        tls=False,
        port='389',
        organization=[module_org],
        location=[module_loc],
    ).create()


@fixture(scope='function')
def auth_source_ipa(ipa_data, module_org, module_loc):
    return entities.AuthSourceLDAP(
        onthefly_register=True,
        account=ipa_data['ldap_ipa_user_name'],
        account_password=ipa_data['ldap_ipa_user_passwd'],
        base_dn=ipa_data['ipa_base_dn'],
        groups_base=ipa_data['ipa_group_base_dn'],
        attr_firstname=LDAP_ATTR['firstname'],
        attr_lastname=LDAP_ATTR['surname'],
        attr_login=LDAP_ATTR['login'],
        server_type=LDAP_SERVER_TYPE['API']['ipa'],
        attr_mail=LDAP_ATTR['mail'],
        name=gen_string('alpha'),
        host=ipa_data['ldap_ipa_hostname'],
        tls=False,
        port='389',
        organization=[module_org],
        location=[module_loc],
    ).create()


@fixture()
def ldap_user_name(ldap_data, test_name):
    """Add LDAP user to satellite by logging in, return username to test and delete the user (if
    still exists) when test finishes.
    """
    with Session(test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']):
        pass
    yield ldap_data['ldap_user_name']
    users = entities.User().search(
        query={'search': 'login="{}"'.format(ldap_data['ldap_user_name'])}
    )
    if users:
        users[0].delete()


@fixture()
def ldap_usergroup_name():
    """Return some random usergroup name, and attempt to delete such usergroup when test finishes.
    """
    usergroup_name = gen_string('alphanumeric')
    yield usergroup_name
    user_groups = entities.UserGroup().search(query={'search': 'name="{}"'.format(usergroup_name)})
    if user_groups:
        user_groups[0].delete()


@fixture(scope='module')
def ldap_auth_name():
    """Return some random ldap name, and attempt to delete all ldap when test starts.
    """
    ldap = entities.AuthSourceLDAP().search()
    for ldap_auth in range(len(ldap)):
        users = entities.User(auth_source=ldap[ldap_auth]).search()
        for user in range(len(users)):
            users[user].delete()
        ldap[ldap_auth].delete()
    ldap_name = gen_string('alphanumeric')
    yield ldap_name


@fixture(scope='module')
def enroll_idm_and_configure_external_auth():
    """Enroll the Satellite6 Server to an IDM Server."""
    run_command(cmd='yum -y --disableplugin=foreman-protector install ipa-client ipa-admintools')

    run_command(
        cmd='echo {0} | kinit admin'.format(settings.ipa.password_ipa),
        hostname=settings.ipa.hostname_ipa,
    )
    result = run_command(
        cmd='ipa host-add --random {}'.format(settings.server.hostname),
        hostname=settings.ipa.hostname_ipa,
    )

    for line in result:
        if "Random password" in line:
            _, password = line.split(': ', 2)
            break
    run_command(
        cmd='ipa service-add HTTP/{}'.format(settings.server.hostname),
        hostname=settings.ipa.hostname_ipa,
    )
    _, domain = settings.ipa.hostname_ipa.split('.', 1)
    run_command(
        cmd="ipa-client-install --password '{}' --domain {} --server {} --realm {} -U".format(
            password, domain, settings.ipa.hostname_ipa, domain.upper()
        )
    )


def update_rhsso_settings_in_satellite(revert=False):
    """Update or Revert the RH-SSO settings in satellite"""
    rhhso_settings = {
        'authorize_login_delegation': True,
        'authorize_login_delegation_auth_source_user_autocreate': 'External',
        'oidc_algorithm': 'RS256',
        'oidc_audience': '{}-foreman-openidc'.format(settings.server.hostname),
        'oidc_issuer': '{}/auth/realms/{}'.format(settings.rhsso.host_url, settings.rhsso.realm),
        'oidc_jwks_url': '{}/auth/realms/{}/protocol/openid-connect/certs'.format(
            settings.rhsso.host_url, settings.rhsso.realm
        ),
    }
    if not revert:
        for setting_name, setting_value in rhhso_settings.items():
            setting_entity = entities.Setting().search(
                query={'search': 'name={}'.format(setting_name)}
            )[0]
            setting_entity.value = setting_value
            setting_entity.update({'value'})
    else:
        setting_entity = entities.Setting().search(
            query={'search': 'name=authorize_login_delegation'}
        )[0]
        setting_entity.value = False
        setting_entity.update({'value'})


@fixture(scope='module')
def enroll_configure_rhsso_external_auth():
    """Enroll the Satellite6 Server to an RHSSO Server."""
    run_command(
        cmd='yum -y --disableplugin=foreman-protector install '
        'mod_auth_openidc keycloak-httpd-client-install'
    )
    run_command(
        cmd='echo {0} | keycloak-httpd-client-install --app-name foreman-openidc \
                --keycloak-server-url {1} \
                --keycloak-admin-username "admin" \
                --keycloak-realm "{2}" \
                --keycloak-admin-realm master \
                --keycloak-auth-role root-admin -t openidc -l /users/extlogin --force'.format(
            settings.rhsso.password, settings.rhsso.host_url, settings.rhsso.realm,
        )
    )
    run_command(
        cmd="satellite-installer --foreman-keycloak true "
        "--foreman-keycloak-app-name 'foreman-openidc' "
        "--foreman-keycloak-realm '{}' ".format(settings.rhsso.realm),
        timeout=600,
    )
    run_command(cmd="systemctl restart httpd")


@fixture(scope='module')
def enable_external_auth_rhsso(enroll_configure_rhsso_external_auth):
    """register the satellite with RH-SSO Server for single sign-on"""
    client_id = get_rhsso_client_id()
    create_mapper(GROUP_MEMBERSHIP_MAPPER, client_id)
    audience_mapper = copy.deepcopy(AUDIENCE_MAPPER)
    audience_mapper["config"]["included.client.audience"] = audience_mapper["config"][
        "included.client.audience"
    ].format(rhsso_host=settings.server.hostname)
    create_mapper(audience_mapper, client_id)


def generate_otp(secret):
    """Return the time_based_otp """
    time_otp = pyotp.TOTP(secret)
    return time_otp.now()


def ldap_tear_down():
    """Teardown the all ldap settings user, usergroup and ldap delete"""
    ldap = entities.AuthSourceLDAP().search()
    for ldap_auth in range(len(ldap)):
        users = entities.User(auth_source=ldap[ldap_auth]).search()
        for user in range(len(users)):
            users[user].delete()
        ldap[ldap_auth].delete()
    user_groups = entities.UserGroup().search()
    for user_group in user_groups:
        user_group.delete()


def ldap_wrapper(test_func):
    """This decorator will take care of tear_down for ldap resources and wraps test function"""

    def test_wrapper(test_func, *args, **kwargs):
        try:
            test_func(*args, **kwargs)
        finally:
            ldap_tear_down()

    return decorator.decorator(test_wrapper, test_func)


@ldap_wrapper
@tier2
def test_positive_end_to_end_ad(session, ldap_data, ldap_auth_name):
    """Perform end to end testing for LDAP authentication component with AD

    :id: a6528239-e090-4379-a850-3900ee625b24

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    new_server = gen_url()
    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ldap_data['ldap_hostname'],
                'ldap_server.server_type': LDAP_SERVER_TYPE['UI']['ad'],
                'account.account_name': ldap_data['ldap_user_name'],
                'account.password': ldap_data['ldap_user_passwd'],
                'account.base_dn': ldap_data['base_dn'],
                'account.groups_base_dn': ldap_data['group_base_dn'],
                'attribute_mappings.login': LDAP_ATTR['login_ad'],
                'attribute_mappings.first_name': LDAP_ATTR['firstname'],
                'attribute_mappings.last_name': LDAP_ATTR['surname'],
                'attribute_mappings.mail': LDAP_ATTR['mail'],
            }
        )
        assert session.ldapauthentication.read_table_row(ldap_auth_name)['Name'] == ldap_auth_name
        session.ldapauthentication.update(ldap_auth_name, {'ldap_server.host': new_server})
        assert session.ldapauthentication.read_table_row(ldap_auth_name)['Server'] == new_server
        session.ldapauthentication.delete(ldap_auth_name)
        assert not session.ldapauthentication.read_table_row(ldap_auth_name)


@ldap_wrapper
@tier2
@upgrade
def test_positive_create_with_ad_org_and_loc(session, ldap_data, ldap_auth_name):
    """Create LDAP auth_source for AD with org and loc assigned.

    :id: 4f595af4-fc01-44c6-a614-a9ec827e3c3c

    :steps:
        1. Create a new LDAP Auth source with AD, provide organization and
           location information.
        2. Fill in all the fields appropriately for AD.

    :expectedresults: Whether creating LDAP Auth with AD and associating org
        and loc is successful.
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ldap_data['ldap_hostname'],
                'ldap_server.server_type': LDAP_SERVER_TYPE['UI']['ad'],
                'account.account_name': ldap_data['ldap_user_name'],
                'account.password': ldap_data['ldap_user_passwd'],
                'account.base_dn': ldap_data['base_dn'],
                'account.groups_base_dn': ldap_data['group_base_dn'],
                'attribute_mappings.login': LDAP_ATTR['login_ad'],
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
        assert ldap_source['ldap_server']['host'] == ldap_data['ldap_hostname']
        assert ldap_source['ldap_server']['port'] == '389'
        assert ldap_source['ldap_server']['server_type'] == LDAP_SERVER_TYPE['UI']['ad']
        assert ldap_source['account']['account_name'] == ldap_data['ldap_user_name']
        assert ldap_source['account']['base_dn'] == ldap_data['base_dn']
        assert ldap_source['account']['groups_base_dn'] == ldap_data['group_base_dn']
        assert not ldap_source['account']['onthefly_register']
        assert ldap_source['account']['usergroup_sync']
        assert ldap_source['attribute_mappings']['login'] == LDAP_ATTR['login_ad']
        assert ldap_source['attribute_mappings']['first_name'] == LDAP_ATTR['firstname']
        assert ldap_source['attribute_mappings']['last_name'] == LDAP_ATTR['surname']
        assert ldap_source['attribute_mappings']['mail'] == LDAP_ATTR['mail']


@ldap_wrapper
@skip_if_not_set('ipa')
@tier2
def test_positive_create_with_idm_org_and_loc(session, ipa_data):
    """Create LDAP auth_source for IDM with org and loc assigned.

    :id: bc70bcff-1241-4d8e-9713-da752d6c4798

    :steps:
        1. Create a new LDAP Auth source with IDM, provide organization and
           location information.
        2. Fill in all the fields appropriately for IDM.

    :expectedresults: Whether creating LDAP Auth source with IDM and
        associating org and loc is successful.
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    ldap_auth_name = gen_string('alphanumeric')
    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ipa_data['ldap_ipa_hostname'],
                'ldap_server.server_type': LDAP_SERVER_TYPE['UI']['ipa'],
                'account.account_name': ipa_data['ldap_ipa_user_name'],
                'account.password': ipa_data['ldap_ipa_user_passwd'],
                'account.base_dn': ipa_data['ipa_base_dn'],
                'account.groups_base_dn': ipa_data['ipa_group_base_dn'],
                'attribute_mappings.login': LDAP_ATTR['login'],
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
        assert ldap_source['ldap_server']['host'] == ipa_data['ldap_ipa_hostname']
        assert ldap_source['ldap_server']['port'] == '389'
        assert ldap_source['ldap_server']['server_type'] == LDAP_SERVER_TYPE['UI']['ipa']
        assert ldap_source['account']['account_name'] == ipa_data['ldap_ipa_user_name']
        assert ldap_source['account']['base_dn'] == ipa_data['ipa_base_dn']
        assert ldap_source['account']['groups_base_dn'] == ipa_data['ipa_group_base_dn']
        assert not ldap_source['account']['onthefly_register']
        assert ldap_source['account']['usergroup_sync']
        assert ldap_source['attribute_mappings']['login'] == LDAP_ATTR['login']
        assert ldap_source['attribute_mappings']['first_name'] == LDAP_ATTR['firstname']
        assert ldap_source['attribute_mappings']['last_name'] == LDAP_ATTR['surname']
        assert ldap_source['attribute_mappings']['mail'] == LDAP_ATTR['mail']


@ldap_wrapper
@skip_if_not_set('ipa')
@destructive
def test_positive_create_with_idm_https(session, test_name, ipa_data):
    """Create LDAP auth_source for IDM with HTTPS.

    :id: 7ff3daa4-2317-11ea-aeb8-d46d6dd3b5b2

    :steps:
        1. Create a new LDAP Auth source with IDM and HTTPS, provide organization and
           location information.
        2. Fill in all the fields appropriately for IDM.
        3. Login with existing LDAP user present in IDM.

    :BZ: 1785621

    :expectedresults: LDAP auth source for IDM with HTTPS should be successful and LDAP login
        should work as expected.
    """
    set_certificate_in_satellite(server_type='IPA')
    org = entities.Organization().create()
    loc = entities.Location().create()
    ldap_auth_name = gen_string('alphanumeric')
    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ipa_data['ldap_ipa_hostname'],
                'ldap_server.ldaps': True,
                'ldap_server.server_type': LDAP_SERVER_TYPE['UI']['ipa'],
                'account.account_name': ipa_data['ldap_ipa_user_name'],
                'account.password': ipa_data['ldap_ipa_user_passwd'],
                'account.base_dn': ipa_data['ipa_base_dn'],
                'account.groups_base_dn': ipa_data['ipa_group_base_dn'],
                'account.onthefly_register': True,
                'attribute_mappings.login': LDAP_ATTR['login'],
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
        assert ldap_source['ldap_server']['host'] == ipa_data['ldap_ipa_hostname']
        assert ldap_source['ldap_server']['port'] == '636'
    username = settings.ipa.user_ipa
    full_name = '{} katello'.format(settings.ipa.user_ipa)
    with Session(test_name, username, ipa_data['ldap_ipa_user_passwd']) as ldapsession:
        with raises(NavigationTriesExceeded):
            ldapsession.usergroup.search('')
        assert ldapsession.task.read_all()['current_user'] == full_name


@ldap_wrapper
@destructive
def test_positive_create_with_ad_https(session, test_name, ldap_data):
    """Create LDAP auth_source for AD with HTTPS.

    :id: 739a82a2-2b01-11ea-93ea-398446a2b98f

    :steps:
        1. Create a new LDAP Auth source with AD and HTTPS, provide organization and
           location information.
        2. Fill in all the fields appropriately for AD.
        3. Login with existing LDAP user present in AD.

    :BZ: 1785621

    :expectedresults: LDAP auth source for AD with HTTPS should be successful and LDAP login
        should work as expected.
    """
    set_certificate_in_satellite(server_type='AD')
    org = entities.Organization().create()
    loc = entities.Location().create()
    ldap_auth_name = gen_string('alphanumeric')
    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ldap_data['ldap_hostname'],
                'ldap_server.ldaps': True,
                'ldap_server.server_type': LDAP_SERVER_TYPE['UI']['ad'],
                'account.account_name': ldap_data['ldap_user_name'],
                'account.password': ldap_data['ldap_user_passwd'],
                'account.base_dn': ldap_data['base_dn'],
                'account.groups_base_dn': ldap_data['group_base_dn'],
                'account.onthefly_register': True,
                'attribute_mappings.login': LDAP_ATTR['login_ad'],
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
        assert ldap_source['ldap_server']['host'] == ldap_data['ldap_hostname']
        assert ldap_source['ldap_server']['port'] == '636'
    with Session(test_name, settings.ldap.username, ldap_data['ldap_user_passwd']) as ldapsession:
        with raises(NavigationTriesExceeded):
            ldapsession.usergroup.search('')
        assert ldapsession.task.read_all()['current_user'] == settings.ldap.username


@ldap_wrapper
@tier2
def test_positive_add_katello_role(
    session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name
):
    """Associate katello roles to User Group.
    [belonging to external AD User Group.]

    :id: aa5e3bf4-cb42-43a4-93ea-a2eea54b847a

    :Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. Create and associate an External AD UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to
        access katello entities as per roles.
    """
    ak_name = gen_string('alpha')
    auth_source_name = 'LDAP-' + auth_source.name
    user_permissions = {'Katello::ActivationKey': PERMISSIONS['Katello::ActivationKey']}
    katello_role = entities.Role().create()
    create_role_permissions(katello_role, user_permissions)
    with session:
        session.usergroup.create(
            {
                'usergroup.name': ldap_usergroup_name,
                'roles.resources.assigned': [katello_role.name],
                'external_groups.name': EXTERNAL_GROUP_NAME,
                'external_groups.auth_source': auth_source_name,
            }
        )
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.usergroup.refresh_external_group(ldap_usergroup_name, EXTERNAL_GROUP_NAME)
    with Session(test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']) as session:
        with raises(NavigationTriesExceeded):
            session.architecture.search('')
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert current_user == ldap_data['ldap_user_name']


@ldap_wrapper
@upgrade
@tier2
def test_positive_update_external_roles(
    session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name
):
    """Added AD UserGroup roles get pushed down to user

    :id: f3ca1aae-5461-4af3-a508-82679bb6afed

    :setup: assign additional roles to the UserGroup

    :steps:
        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup as per the UserGroup name in AD.
        4. Login to sat6 with the AD user.
        5. Assign additional roles to the UserGroup.
        6. Login to sat6 with LDAP user that is part of aforementioned
           UserGroup.

    :expectedresults: User has access to all NEW functional areas that are
        assigned to aforementioned UserGroup.
    """
    ak_name = gen_string('alpha')
    auth_source_name = 'LDAP-' + auth_source.name
    location_name = gen_string('alpha')
    foreman_role = entities.Role().create()
    katello_role = entities.Role().create()
    foreman_permissions = {'Location': PERMISSIONS['Location']}
    katello_permissions = {'Katello::ActivationKey': PERMISSIONS['Katello::ActivationKey']}
    create_role_permissions(foreman_role, foreman_permissions)
    create_role_permissions(katello_role, katello_permissions)
    with session:
        session.usergroup.create(
            {
                'usergroup.name': ldap_usergroup_name,
                'roles.resources.assigned': [foreman_role.name],
                'external_groups.name': EXTERNAL_GROUP_NAME,
                'external_groups.auth_source': auth_source_name,
            }
        )
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        with Session(
            test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']
        ) as ldapsession:
            with raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.location.create({'name': location_name})
            assert ldapsession.location.search(location_name)[0]['Name'] == location_name
            current_user = ldapsession.location.read(location_name, 'current_user')['current_user']
            assert current_user == ldap_data['ldap_user_name']
        session.usergroup.update(
            ldap_usergroup_name, {'roles.resources.assigned': [katello_role.name]}
        )
        session.usergroup.refresh_external_group(ldap_usergroup_name, EXTERNAL_GROUP_NAME)
    with Session(test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']) as session:
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert current_user == ldap_data['ldap_user_name']


@ldap_wrapper
@tier2
@upgrade
def test_positive_delete_external_roles(
    session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name
):
    """Deleted AD UserGroup roles get pushed down to user

    :id: 479bc8fe-f6a3-4c89-8c7e-3d997315383f

    :setup: delete roles from an AD UserGroup

    :steps:
        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup as per the UserGroup name in AD.
        4. Login to sat6 with the AD user.
        5. Unassign some of the existing roles of the UserGroup.
        6. Login to sat6 with LDAP user that is part of aforementioned
           UserGroup.

    :expectedresults: User no longer has access to all deleted functional
        areas that were assigned to aforementioned UserGroup.
    """
    auth_source_name = 'LDAP-' + auth_source.name
    location_name = gen_string('alpha')
    foreman_role = entities.Role().create()
    foreman_permissions = {'Location': PERMISSIONS['Location']}
    create_role_permissions(foreman_role, foreman_permissions)
    with session:
        session.usergroup.create(
            {
                'usergroup.name': ldap_usergroup_name,
                'roles.resources.assigned': [foreman_role.name],
                'external_groups.name': EXTERNAL_GROUP_NAME,
                'external_groups.auth_source': auth_source_name,
            }
        )
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        with Session(
            test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']
        ) as ldapsession:
            with raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.location.create({'name': location_name})
            assert ldapsession.location.search(location_name)[0]['Name'] == location_name
            current_user = ldapsession.location.read(location_name, 'current_user')['current_user']
            assert current_user == ldap_data['ldap_user_name']
        session.usergroup.update(
            ldap_usergroup_name, {'roles.resources.unassigned': [foreman_role.name]}
        )
    with Session(
        test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']
    ) as ldapsession:
        with raises(NavigationTriesExceeded):
            ldapsession.location.create({'name': gen_string('alpha')})


@ldap_wrapper
@tier2
def test_positive_update_external_user_roles(
    session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name
):
    """Assure that user has roles/can access feature areas for
    additional roles assigned outside any roles assigned by his group

    :id: a487f7d6-22f2-4e42-b34f-8d984f721c83

    :setup: Assign roles to UserGroup and configure external UserGroup
        subsequently assign specified roles to the user(s).  roles that are
        not part of the larger UserGroup

    :steps:
        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup as per the UserGroup name in AD.
        4. Assign some more roles to a User(which is part of external AD
           UserGroup) at the User level.
        5. Login to sat6 with the above AD user and attempt to access areas
           assigned specifically to user.

    :expectedresults: User can access not only those feature areas in his
        UserGroup but those additional feature areas / roles assigned
        specifically to user
    """
    ak_name = gen_string('alpha')
    auth_source_name = 'LDAP-' + auth_source.name
    location_name = gen_string('alpha')
    foreman_role = entities.Role().create()
    katello_role = entities.Role().create()
    foreman_permissions = {'Location': PERMISSIONS['Location']}
    katello_permissions = {'Katello::ActivationKey': PERMISSIONS['Katello::ActivationKey']}
    create_role_permissions(foreman_role, foreman_permissions)
    create_role_permissions(katello_role, katello_permissions)
    with session:
        session.usergroup.create(
            {
                'usergroup.name': ldap_usergroup_name,
                'roles.resources.assigned': [foreman_role.name],
                'external_groups.name': EXTERNAL_GROUP_NAME,
                'external_groups.auth_source': auth_source_name,
            }
        )
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        with Session(
            test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']
        ) as ldapsession:
            ldapsession.location.create({'name': location_name})
            assert ldapsession.location.search(location_name)[0]['Name'] == location_name
            current_user = ldapsession.location.read(location_name, 'current_user')['current_user']
            assert current_user == ldap_data['ldap_user_name']
        session.user.update(
            ldap_data['ldap_user_name'], {'roles.resources.assigned': [katello_role.name]}
        )
    with Session(test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']) as session:
        with raises(NavigationTriesExceeded):
            ldapsession.architecture.search('')
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert current_user == ldap_data['ldap_user_name']


@ldap_wrapper
@tier2
def test_positive_add_admin_role_with_org_loc(
    session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name, module_org
):
    """Associate Admin role to User Group with org and loc set.
    [belonging to external AD User Group.]

    :id: 00841778-f89e-4445-a6c6-f1470b6da32e

    :setup: LDAP Auth Source should be created with Org and Location
            Associated.

    :Steps:
        1. Create an UserGroup.
        2. Assign admin role to UserGroup.
        3. Create and associate an External AD UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to
        access some of the pages, with the associated org and loc
        in LDAP Auth source page as the context set.
    """
    ak_name = gen_string('alpha')
    auth_source_name = 'LDAP-' + auth_source.name
    location_name = gen_string('alpha')
    with session:
        session.usergroup.create(
            {
                'usergroup.name': ldap_usergroup_name,
                'roles.admin': True,
                'external_groups.name': EXTERNAL_GROUP_NAME,
                'external_groups.auth_source': auth_source_name,
            }
        )
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
    with Session(test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']) as session:
        session.location.create({'name': location_name})
        assert session.location.search(location_name)[0]['Name'] == location_name
        location = session.location.read(location_name, ['current_user', 'primary'])
        assert location['current_user'] == ldap_data['ldap_user_name']
        assert location['primary']['name'] == location_name
        session.organization.select(module_org.name)
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        ak = session.activationkey.read(ak_name, 'details.name')
        assert ak['details']['name'] == ak_name


@ldap_wrapper
@tier2
def test_positive_add_foreman_role_with_org_loc(
    session,
    ldap_data,
    ldap_user_name,
    test_name,
    auth_source,
    ldap_usergroup_name,
    module_org,
    module_loc,
):
    """Associate foreman roles to User Group with org and loc set.
    [belonging to external AD User Group.]

    :id: b39d7b2a-6d78-4c35-969a-37c8317ce64f

    :setup: LDAP Auth Source should be created with Org and Location
            Associated.

    :Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. Create and associate an External AD UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to
        access foreman entities as per roles, with the associated org and
        loc in LDAP Auth source page as the context set.
    """
    auth_source_name = 'LDAP-' + auth_source.name
    name = gen_string('alpha')
    user_permissions = {
        'Hostgroup': PERMISSIONS['Hostgroup'],
        'Location': ['assign_locations'],
        'Organization': ['assign_organizations'],
    }
    foreman_role = entities.Role().create()
    create_role_permissions(foreman_role, user_permissions)
    with session:
        session.usergroup.create(
            {
                'usergroup.name': ldap_usergroup_name,
                'roles.resources.assigned': [foreman_role.name],
                'external_groups.name': EXTERNAL_GROUP_NAME,
                'external_groups.auth_source': auth_source_name,
            }
        )
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.usergroup.refresh_external_group(ldap_usergroup_name, EXTERNAL_GROUP_NAME)
        with Session(
            test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']
        ) as ldapsession:
            with raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.hostgroup.create({'host_group.name': name})
        hostgroup = session.hostgroup.read(name, ['organizations', 'locations'])
        assert len(hostgroup['organizations']['resources']['assigned']) == 1
        assert module_org.name in hostgroup['organizations']['resources']['assigned']
        assert len(hostgroup['locations']['resources']['assigned']) == 1
        assert module_loc.name in hostgroup['locations']['resources']['assigned']


@ldap_wrapper
@tier2
def test_positive_add_katello_role_with_org(
    session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name, module_org
):
    """Associate katello roles to User Group with org set.
    [belonging to external AD User Group.]

    :id: a2ebd4de-eb0a-47da-81e8-00942eedcbf6

    :setup: LDAP Auth Source should be created with Organization associated.

    :Steps:
        1. Create an UserGroup.
        2. Assign some katello roles to UserGroup.
        3. Create and associate an External AD UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to
        access katello entities as per roles, with the associated org
        in LDAP Auth source page as the context set.
    """
    auth_source_name = 'LDAP-' + auth_source.name
    ak_name = gen_string('alpha')
    user_permissions = {
        'Katello::ActivationKey': PERMISSIONS['Katello::ActivationKey'],
        'Location': ['assign_locations'],
        'Organization': ['assign_organizations'],
    }
    katello_role = entities.Role().create()
    create_role_permissions(katello_role, user_permissions)
    different_org = entities.Organization().create()
    with session:
        session.usergroup.create(
            {
                'usergroup.name': ldap_usergroup_name,
                'roles.resources.assigned': [katello_role.name],
                'external_groups.name': EXTERNAL_GROUP_NAME,
                'external_groups.auth_source': auth_source_name,
            }
        )
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.usergroup.refresh_external_group(ldap_usergroup_name, EXTERNAL_GROUP_NAME)
        with Session(
            test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']
        ) as ldapsession:
            with raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.activationkey.create({'name': ak_name})
        results = session.activationkey.search(ak_name)
        assert results[0]['Name'] == ak_name
        session.organization.select(different_org.name)
        assert not session.activationkey.search(ak_name)[0]['Name'] == ak_name
    ak = (
        entities.ActivationKey(organization=module_org)
        .search(query={'search': 'name={}'.format(ak_name)})[0]
        .read()
    )
    assert ak.organization.id == module_org.id


@ldap_wrapper
@tier2
@upgrade
def test_positive_create_user_in_ldap_mode(session, auth_source):
    """Create User in ldap mode

    :id: 0668b2ca-831e-4568-94fb-80e45dd7d001

    :expectedresults: User is created without specifying the password
    """
    auth_source_name = 'LDAP-' + auth_source.name
    name = gen_string('alpha')
    with session:
        session.user.create({'user.login': name, 'user.auth': auth_source_name})
        assert session.user.search(name)[0]['Username'] == name
        user_values = session.user.read(name)
        assert user_values['user']['auth'] == auth_source_name


@ldap_wrapper
@tier2
def test_positive_login_ad_user_no_roles(test_name, ldap_data, ldap_user_name, auth_source):
    """Login with LDAP Auth- AD for user with no roles/rights

    :id: 7dc8d9a7-ff08-4d8e-a842-d370ffd69741

    :setup: assure properly functioning AD server for authentication

    :steps: Login to server with an AD user.

    :expectedresults: Log in to foreman UI successfully but cannot access
        functional areas of UI
    """
    with Session(
        test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']
    ) as ldapsession:
        with raises(NavigationTriesExceeded):
            ldapsession.user.search('')
        assert ldapsession.task.read_all()['current_user'] == ldap_data['ldap_user_name']


@ldap_wrapper
@tier2
@upgrade
def test_positive_login_ad_user_basic_roles(
    session, test_name, ldap_data, ldap_user_name, auth_source
):
    """Login with LDAP - AD for user with roles/rights

    :id: ef202e94-8e5d-4333-a4bc-e573b03ebfc8

    :setup: assure properly functioning AD server for authentication

    :steps: Login to server with an AD user.

    :expectedresults: Log in to foreman UI successfully and can access
        appropriate functional areas in UI
    """
    name = gen_string('alpha')
    role = entities.Role().create()
    permissions = {'Architecture': PERMISSIONS['Architecture']}
    create_role_permissions(role, permissions)
    with Session(
        test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']
    ) as ldapsession:
        with raises(NavigationTriesExceeded):
            ldapsession.usergroup.search('')
    with session:
        session.user.update(ldap_data['ldap_user_name'], {'roles.resources.assigned': [role.name]})
    with Session(
        test_name, ldap_data['ldap_user_name'], ldap_data['ldap_user_passwd']
    ) as ldapsession:
        ldapsession.architecture.create({'name': name})
        assert ldapsession.architecture.search(name)[0]['Name'] == name


@ldap_wrapper
@upgrade
@tier2
def test_positive_login_user_password_otp(test_name, ipa_data, auth_source_ipa):
    """Login with password with time based OTP

    :id: be7eb5d6-3228-4660-aa64-c56f9f3ec5e0

    :setup: Assure properly functioning IPA server for authentication

    :steps: Login to server with an IPA user with time_based OTP.

    :expectedresults: Log in to foreman UI successfully

    """
    password_with_otp = "{0}{1}".format(
        ipa_data['ldap_ipa_user_passwd'], generate_otp(ipa_data['time_based_secret'])
    )
    with Session(test_name, ipa_data['ipa_otp_username'], password_with_otp) as ldapsession:
        with raises(NavigationTriesExceeded):
            ldapsession.user.search('')
        expected_user = "{} {}".format(ipa_data['ipa_otp_username'], ipa_data['ipa_otp_username'])
        assert ldapsession.task.read_all()['current_user'] == expected_user
    users = entities.User().search(
        query={'search': 'login="{}"'.format(ipa_data['ipa_otp_username'])}
    )
    assert users[0].login == ipa_data['ipa_otp_username']


@ldap_wrapper
@tier2
def test_negative_login_user_with_invalid_password_otp(test_name, ipa_data, auth_source_ipa):
    """Login with password with time based OTP

    :id: 3718c86e-5976-4fb8-9c80-4685d53bd955

    :setup: Assure properly functioning IPA server for authentication

    :steps: Login to server with an IPA user with invalid OTP.

    :expectedresults: Log in to foreman UI should be failed

    """
    password_with_otp = "{0}{1}".format(
        ipa_data['ldap_ipa_user_passwd'], gen_string(str_type='numeric', length=6)
    )
    with Session(test_name, ipa_data['ipa_otp_username'], password_with_otp) as ldapsession:
        with raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == "NavigationTriesExceeded"


@destructive
@ldap_wrapper
def test_single_sign_on_ldap_ipa_server(enroll_idm_and_configure_external_auth):
    """Verify the single sign-on functionality with external authentication

    :id: 9813a4da-4639-11ea-9780-d46d6dd3b5b2

    :setup: Enroll the IDM Configuration for External Authentication

    :steps: Assert single sign-on session user directed to satellite instead login page

    :expectedresults: After single sign on user should redirected from /extlogin to /hosts page

    """
    # register the satellite with IPA for single sign-on and update external auth
    try:
        run_command(cmd="subscription-manager repos --enable rhel-7-server-optional-rpms")
        run_command(cmd='satellite-installer --foreman-ipa-authentication=true', timeout=800)
        run_command('foreman-maintain service restart', timeout=300)
        result = run_command(
            cmd="curl -k -u : --negotiate https://{}/users/extlogin/".format(
                settings.server.hostname
            ),
            hostname=settings.ipa.hostname_ipa,
        )
        result = ''.join(result)
        assert 'redirected' in result
        assert 'https://{}/hosts'.format(settings.server.hostname) in result
        assert 'You are being' in result
    finally:
        # resetting the settings to default for external auth
        run_command(cmd='satellite-installer --foreman-ipa-authentication=false', timeout=800)
        run_command('foreman-maintain service restart', timeout=300)
        run_command(
            cmd='ipa service-del HTTP/{}'.format(settings.server.hostname),
            hostname=settings.ipa.hostname_ipa,
        )
        run_command(
            cmd='ipa host-del {}'.format(settings.server.hostname),
            hostname=settings.ipa.hostname_ipa,
        )


@destructive
def test_single_sign_on_using_rhsso(enable_external_auth_rhsso, session):
    """Verify the single sign-on functionality with external authentication RH-SSO

    :id: 18a77de8-570f-11ea-a202-d46d6dd3b5b2

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Create Mappers on RHSSO Instance and Update the Settings in Satellite
        2. Login into Satellite using RHSSO login page redirected by Satellite

    :expectedresults: After entering the login details in RHSSO page user should
        logged into Satellite
    """
    try:
        update_rhsso_settings_in_satellite()
        with session(login=False):
            session.rhsso_login.login(
                {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.password}
            )
            with raises(NavigationTriesExceeded):
                session.user.search('')
                actual_user = session.task.read_all(widget_names="current_user")['current_user']
                assert settings.rhsso.rhsso_user in actual_user

    finally:
        update_rhsso_settings_in_satellite(revert=True)


@upgrade
@destructive
def test_external_logout_rhsso(enable_external_auth_rhsso, session):
    """Verify the external logout page navigation with external authentication RH-SSO

    :id: 87b5e08e-69c6-11ea-8126-e74d80ea4308

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Create Mappers on RHSSO Instance and Update the Settings in Satellite
        2. Login into Satellite using RHSSO login page redirected by Satellite
        3. Logout from Satellite and Verify the external_logout page displayed

    :expectedresults: After logout from Satellite navigate should be external_loout page
    """
    try:
        update_rhsso_settings_in_satellite()
        with session(login=False):
            login_details = {
                'username': settings.rhsso.rhsso_user,
                'password': settings.rhsso.password,
            }
            session.rhsso_login.login(login_details)
            view = session.rhsso_login.logout()
            assert view['login_again'] == "Click to log in again"
            session.rhsso_login.login(login_details, external_login=True)
            actual_user = session.task.read_all(widget_names="current_user")['current_user']
            assert settings.rhsso.rhsso_user in actual_user
    finally:
        update_rhsso_settings_in_satellite(revert=True)


@upgrade
@destructive
def test_external_new_user_login(enable_external_auth_rhsso, session):
    """Verify the external logout page navigation with external authentication RH-SSO

    :id: bf938ea2-6df9-11ea-a7cf-951107ed0bbb

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Create new user on RHSSO Instance and Update the Settings in Satellite
        2. Verify the login for that user

    :expectedresults: New User created in RHSSO server should able to get log-in
    """
    client_id = get_rhsso_client_id()
    try:
        update_rhsso_settings_in_satellite()
        user_details = create_new_rhsso_user(client_id)
        login_details = {
            'username': user_details['username'],
            'password': settings.rhsso.password,
        }
        with session(login=False):
            session.rhsso_login.login(login_details)
            actual_user = session.task.read_all(widget_names="current_user")['current_user']
            assert user_details['firstName'] in actual_user
    finally:
        update_rhsso_settings_in_satellite(revert=True)
        delete_rhsso_user(user_details['username'])
