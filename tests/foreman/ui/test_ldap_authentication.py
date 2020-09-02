"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Integration

:CaseComponent: LDAP

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os
from time import sleep

import pyotp
import pytest
from airgun.session import Session
from fauxfactory import gen_url
from nailgun import entities
from navmazing import NavigationTriesExceeded
from pytest import raises
from pytest import skip

from robottelo import ssh
from robottelo.api.utils import create_role_permissions
from robottelo.config import settings
from robottelo.constants import CERT_PATH
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


@fixture()
def ldap_usergroup_name():
    """Return some random usergroup name, and attempt to delete such usergroup when test finishes.
    """
    usergroup_name = gen_string('alphanumeric')
    yield usergroup_name
    user_groups = entities.UserGroup().search(query={'search': 'name="{}"'.format(usergroup_name)})
    if user_groups:
        user_groups[0].delete()


@fixture()
def ldap_tear_down():
    """Teardown the all ldap settings user, usergroup and ldap delete"""
    yield
    ldap_auth_sources = entities.AuthSourceLDAP().search()
    for ldap_auth in ldap_auth_sources:
        users = entities.User(auth_source=ldap_auth).search()
        for user in users:
            user.delete()
        ldap_auth.delete()


@fixture()
def rhsso_setting_setup(request):
    """Update the RHSSO setting and revert it in cleanup"""
    update_rhsso_settings_in_satellite()

    def rhsso_setting_cleanup():
        update_rhsso_settings_in_satellite(revert=True)

    request.addfinalizer(rhsso_setting_cleanup)


@fixture()
def rhsso_setting_setup_with_timeout(rhsso_setting_setup, request):
    """Update the RHSSO setting with timeout setting and revert it in cleanup"""
    setting_entity = entities.Setting().search(query={'search': f'name=idle_timeout'})[0]
    setting_entity.value = 1
    setting_entity.update({'value'})

    def setting_timeout_cleanup():
        setting_entity.value = 30
        setting_entity.update({'value'})

    request.addfinalizer(setting_timeout_cleanup)


@fixture()
def external_user_count():
    """return the external auth source user count"""
    users = entities.User().search()
    yield len([user for user in users if user.auth_source_name == 'External'])


def update_rhsso_settings_in_satellite(revert=False):
    """Update or Revert the RH-SSO settings in satellite"""
    rhhso_settings = {
        'authorize_login_delegation': True,
        'authorize_login_delegation_auth_source_user_autocreate': 'External',
        'login_delegation_logout_url': f'https://{settings.server.hostname}/users/extlogout',
        'oidc_algorithm': 'RS256',
        'oidc_audience': [f'{settings.server.hostname}-foreman-openidc'],
        'oidc_issuer': f'{settings.rhsso.host_url}/auth/realms/{settings.rhsso.realm}',
        'oidc_jwks_url': f'{settings.rhsso.host_url}/auth/realms'
        f'/{settings.rhsso.realm}/protocol/openid-connect/certs',
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


def generate_otp(secret):
    """Return the time_based_otp """
    time_otp = pyotp.TOTP(secret)
    return time_otp.now()


@tier2
def test_positive_end_to_end_ad(session, ldap_tear_down, ldap_data):
    """Perform end to end testing for LDAP authentication component with AD

    :id: a6528239-e090-4379-a850-3900ee625b24

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High
    """
    new_server = gen_url()
    ldap_auth_name = gen_string('alphanumeric')
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


@tier2
@upgrade
def test_positive_create_with_ad_org_and_loc(session, ldap_tear_down, ldap_data):
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
    ldap_auth_name = gen_string('alphanumeric')
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


@skip_if_not_set('ipa')
@tier2
def test_positive_create_with_idm_org_and_loc(session, ldap_tear_down, ipa_data):
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


@skip_if_not_set('ipa')
@destructive
def test_positive_create_with_idm_https(session, test_name, ldap_tear_down, ipa_data):
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


@destructive
def test_positive_create_with_ad_https(session, test_name, ldap_tear_down, ldap_data):
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


@tier2
def test_positive_add_katello_role(
    test_name, session, auth_source, ldap_usergroup_name, ldap_tear_down, ldap_data
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


@upgrade
@tier2
def test_positive_update_external_roles(
    test_name, session, auth_source, ldap_usergroup_name, ldap_tear_down, ldap_data
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


@tier2
@upgrade
def test_positive_delete_external_roles(
    test_name, session, auth_source, ldap_usergroup_name, ldap_tear_down, ldap_data
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


@tier2
def test_positive_update_external_user_roles(
    test_name, session, auth_source, ldap_usergroup_name, ldap_tear_down, ldap_data
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


@tier2
def test_positive_add_admin_role_with_org_loc(
    test_name, session, auth_source, ldap_usergroup_name, module_org, ldap_tear_down, ldap_data
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


@tier2
def test_positive_add_foreman_role_with_org_loc(
    test_name,
    session,
    auth_source,
    ldap_usergroup_name,
    module_org,
    module_loc,
    ldap_tear_down,
    ldap_data,
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


@tier2
def test_positive_add_katello_role_with_org(
    test_name, session, auth_source, ldap_usergroup_name, module_org, ldap_tear_down, ldap_data
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


@tier2
@upgrade
def test_positive_create_user_in_ldap_mode(session, auth_source, ldap_tear_down):
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


@tier2
def test_positive_login_ad_user_no_roles(auth_source, test_name, ldap_tear_down, ldap_data):
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


@tier2
@upgrade
def test_positive_login_ad_user_basic_roles(
    test_name, session, auth_source, ldap_tear_down, ldap_data
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


@upgrade
@tier2
def test_positive_login_user_password_otp(auth_source_ipa, test_name, ldap_tear_down, ipa_data):
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


@tier2
def test_negative_login_user_with_invalid_password_otp(
    auth_source_ipa, test_name, ldap_tear_down, ipa_data
):
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
def test_single_sign_on_ldap_ipa_server(enroll_idm_and_configure_external_auth, ldap_tear_down):
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
def test_single_sign_on_ldap_ad_server(enroll_ad_and_configure_external_auth):
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
        run_command(cmd='satellite-installer --foreman-ipa-authentication=true', timeout=800)
        run_command('systemctl restart gssproxy.service')
        run_command('systemctl enable gssproxy.service')

        # restart the deamon and httpd services
        httpd_service_content = (
            '.include /lib/systemd/system/httpd.service\n[Service]' '\nEnvironment=GSS_USE_PROXY=1'
        )
        run_command(f'echo "{httpd_service_content}" > /etc/systemd/system/httpd.service')
        run_command('systemctl daemon-reload && systemctl restart httpd.service')

        # create the kerberos ticket for authentication
        run_command(f'echo {settings.ldap.password} | kinit {settings.ldap.username}')
        result = run_command(
            f"curl -k -u : --negotiate " f"https://{settings.server.hostname}/users/extlogin/"
        )
        result = ''.join(result)
        assert 'redirected' in result
        assert f"https://{settings.server.hostname}/users" in result
        assert f"-{settings.ldap.username}" in result
    finally:
        # resetting the settings to default for external auth
        run_command(cmd='satellite-installer --foreman-ipa-authentication=false', timeout=800)
        run_command('foreman-maintain service restart', timeout=300)


@destructive
def test_single_sign_on_using_rhsso(enable_external_auth_rhsso, rhsso_setting_setup, session):
    """Verify the single sign-on functionality with external authentication RH-SSO

    :id: 18a77de8-570f-11ea-a202-d46d6dd3b5b2

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Create Mappers on RHSSO Instance and Update the Settings in Satellite
        2. Login into Satellite using RHSSO login page redirected by Satellite

    :expectedresults: After entering the login details in RHSSO page user should
        logged into Satellite
    """
    with session(login=False):
        session.rhsso_login.login(
            {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.password}
        )
        with raises(NavigationTriesExceeded):
            session.user.search('')
        actual_user = session.task.read_all(widget_names="current_user")['current_user']
        assert settings.rhsso.rhsso_user in actual_user


@destructive
def test_external_logout_rhsso(enable_external_auth_rhsso, rhsso_setting_setup, session):
    """Verify the external logout page navigation with external authentication RH-SSO

    :id: 87b5e08e-69c6-11ea-8126-e74d80ea4308

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Create Mappers on RHSSO Instance and Update the Settings in Satellite
        2. Login into Satellite using RHSSO login page redirected by Satellite
        3. Logout from Satellite and Verify the external_logout page displayed

    :expectedresults: After logout from Satellite navigate should be external_loout page
    """
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


@destructive
def test_session_expire_rhsso_idle_timeout(
    enable_external_auth_rhsso, rhsso_setting_setup_with_timeout, session
):
    """Verify the idle session expiration timeout with external authentication RH-SSO

    :id: 80247b30-a988-11ea-943c-d46d6dd3b5b2

    :steps:
        1. Change the idle timeout settings for the External Authentication
        2. Login into Satellite using RHSSO login and wait for the idle timeout

    :expectedresults: After completion of the idle timeout user session
        should get expired
    """
    with session(login=False):
        session.rhsso_login.login(
            {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.password}
        )
        sleep(360)
        with raises(NavigationTriesExceeded) as error:
            session.task.read_all(widget_names="current_user")['current_user']
        assert error.typename == "NavigationTriesExceeded"


@destructive
def test_external_new_user_login_and_check_count_rhsso(
    enable_external_auth_rhsso, external_user_count, rhsso_setting_setup, session
):
    """Verify the external new user login and verify the external user count

    :id: bf938ea2-6df9-11ea-a7cf-951107ed0bbb

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :CaseImportance: Medium

    :steps:
        1. Create new user on RHSSO Instance and Update the Settings in Satellite
        2. Verify the login for that user

    :expectedresults: New User created in RHSSO server should able to get log-in
        and correct count shown for external users
    """
    client_id = get_rhsso_client_id()
    user_details = create_new_rhsso_user(client_id)
    login_details = {
        'username': user_details['username'],
        'password': settings.rhsso.password,
    }
    with Session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        actual_user = rhsso_session.task.read_all(widget_names="current_user")['current_user']
        assert user_details['firstName'] in actual_user
    users = entities.User().search()
    updated_count = len([user for user in users if user.auth_source_name == 'External'])
    assert updated_count == external_user_count + 1
    # checking delete user can't login anymore
    delete_rhsso_user(user_details['username'])
    with Session(login=False) as rhsso_session:
        with raises(NavigationTriesExceeded) as error:
            rhsso_session.rhsso_login.login(login_details)
            rhsso_session.task.read_all()
        assert error.typename == "NavigationTriesExceeded"


@pytest.mark.skip_if_open("BZ:1873439")
@destructive
def test_login_failure_rhsso_user_if_internal_user_exist(
    enable_external_auth_rhsso, rhsso_setting_setup, session, module_org, module_loc
):
    """Verify the failure of login for the external rhsso user in case same username
    internal user exists

    :id: e573902c-ed1a-11ea-835a-d46d6dd3b5b2

    :BZ: 1873439

    :CaseImportance: High

    :steps:
        1. create an internal user
        2. create a rhsso user with same username mentioned in internal user
        3. update the satellite to use rhsso and now try login using external rhsso user

    :expectedresults: external rhsso user should not able to login with same username as internal
    """
    client_id = get_rhsso_client_id()
    username = gen_string('alpha')
    entities.User(
        admin=True,
        default_organization=module_org,
        default_location=module_loc,
        login=username,
        password=settings.rhsso.password,
    ).create()
    external_rhsso_user = create_new_rhsso_user(client_id, username=username)
    login_details = {
        'username': external_rhsso_user['username'],
        'password': settings.rhsso.password,
    }
    with Session(login=False) as rhsso_session:
        with raises(NavigationTriesExceeded) as error:
            rhsso_session.rhsso_login.login(login_details)
            rhsso_session.task.read_all()
        assert error.typename == "NavigationTriesExceeded"


@tier2
def test_positive_test_connection_functionality(session, ldap_data, ipa_data):
    """Verify for a positive test connection response

    :id: 5daf3976-9b5c-11ea-96f8-4ceb42ab8dbc

    :steps: Assert test connection of AD and IPA.

    :expectedresults: Positive test connection of AD and IPA
    """
    with session:
        for ldap_host in (ldap_data['ldap_hostname'], ipa_data['ldap_ipa_hostname']):
            session.ldapauthentication.test_connection({'ldap_server.host': ldap_host})


@tier2
def test_negative_login_with_incorrect_password(test_name):
    """Attempt to login in Satellite an IDM user with the wrong password

    :id: 3f09de90-a656-11ea-aa43-4ceb42ab8dbc

    :steps:
        1. Randomaly generate a string as a incorrect password.
        2. Try login with the incorrect password

    :expectedresults: Login fails
    """
    incorrect_password = gen_string('alphanumeric')
    username = settings.ipa.user_ipa
    with Session(test_name, user=username, password=incorrect_password) as ldapsession:
        with raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == "NavigationTriesExceeded"


@tier2
def test_negative_login_with_disable_user(ipa_data, auth_source_ipa):
    """Disabled IDM user cannot login

    :id: 49f28006-aa1f-11ea-90d3-4ceb42ab8dbc

    :steps: Try login from the disabled user

    :expectedresults: Login fails
    """
    with Session(
        user=ipa_data['disabled_user_ipa'], password=ipa_data['ldap_ipa_user_passwd']
    ) as ldapsession:
        with raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == "NavigationTriesExceeded"


@tier2
def test_email_of_the_user_should_be_copied(session, auth_source_ipa, ipa_data, ldap_tear_down):
    """Email of the user created in idm server ( set as external authorization source)
    should be copied to the satellite.

    :id: 9ce7d7c6-dc73-11ea-8a97-4ceb42ab8dbc

    :steps:
        1. Create a new auth source with onthefly enabled
        2. Login to the satellite with the user (from IDM) to create the account
        3. Assert the email of the newly created user

    :expectedresults: Email is copied to Satellite:
    """
    run_command(
        cmd=f"echo {settings.ipa.password_ipa} | kinit admin", hostname=settings.ipa.hostname_ipa
    )
    result = run_command(
        cmd=f"ipa user-find --login {ipa_data['user_ipa']}", hostname=settings.ipa.hostname_ipa
    )
    for line in result:
        if 'Email' in line:
            _, result = line.split(': ', 2)
            break
    with Session(
        user=ipa_data['user_ipa'], password=ipa_data['ldap_ipa_user_passwd']
    ) as ldapsession:
        ldapsession.task.read_all()
    with session:
        user_value = session.user.read(ipa_data['user_ipa'])
        assert user_value['user']['mail'] == result


@tier2
def test_deleted_idm_user_should_not_be_able_to_login(auth_source_ipa, ldap_tear_down):
    """After deleting a user in IDM, user should not be able to login into satellite

    :id: 18ad0526-e083-11ea-b1ad-4ceb42ab8dbc

    :steps:
        1. Create a new auth source with onthefly enabled
        2. Create a new user in IDM and assigning a group to it.
        3. Login to satellite to create the user
        4. Delete the user from IDM
        5. Try login to the satellite from the user

    :expectedresults: User login fails
    """
    result = ssh.command(
        cmd=f"echo {settings.ipa.password_ipa} | kinit admin", hostname=settings.ipa.hostname_ipa
    )
    assert result.return_code == 0
    test_user = gen_string('alpha')
    add_user_cmd = (
        f"echo {settings.ipa.password_ipa} | ipa user-add {test_user} --first"
        f"={test_user} --last={test_user} --password"
    )
    result = ssh.command(cmd=add_user_cmd, hostname=settings.ipa.hostname_ipa)
    assert result.return_code == 0
    group = settings.ipa.grpbasedn_ipa.split(',')
    for line in group:
        if 'group' in line:
            _, group = line.split('=')
            break
    result = ssh.command(
        cmd=f"ipa group-add-member {group} --user={test_user}", hostname=settings.ipa.hostname_ipa,
    )
    assert result.return_code == 0
    with Session(user=test_user, password=settings.ipa.password_ipa) as ldapsession:
        ldapsession.task.read_all()
    result = ssh.command(cmd=f"ipa user-del {test_user}", hostname=settings.ipa.hostname_ipa)
    assert result.return_code == 0
    with Session(user=test_user, password=settings.ipa.password_ipa) as ldapsession:
        with raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == "NavigationTriesExceeded"
