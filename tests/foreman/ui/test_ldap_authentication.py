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
from airgun.session import Session
from fauxfactory import gen_url
from nailgun import entities
from navmazing import NavigationTriesExceeded

from robottelo import ssh
from robottelo.api.utils import create_role_permissions
from robottelo.cli.factory import make_usergroup
from robottelo.cli.factory import make_usergroup_external
from robottelo.cli.ldapauthsource import ExternalAuthSource
from robottelo.config import settings
from robottelo.constants import CERT_PATH
from robottelo.constants import LDAP_ATTR
from robottelo.constants import PERMISSIONS
from robottelo.constants import RHEL_7_MAJOR_VERSION
from robottelo.datafactory import gen_string
from robottelo.helpers import file_downloader
from robottelo.rhsso_utils import create_group
from robottelo.rhsso_utils import create_new_rhsso_user
from robottelo.rhsso_utils import delete_rhsso_group
from robottelo.rhsso_utils import delete_rhsso_user
from robottelo.rhsso_utils import get_rhsso_client_id
from robottelo.rhsso_utils import run_command
from robottelo.rhsso_utils import update_rhsso_user
from robottelo.utils.issue_handlers import is_open


pytestmark = [pytest.mark.run_in_one_thread]

EXTERNAL_GROUP_NAME = 'foobargroup'


def set_certificate_in_satellite(server_type, default_sat, hostname=None):
    """update the cert settings in satellite based on type of ldap server"""
    if server_type == 'IPA':
        idm_cert_path_url = os.path.join(settings.ipa.hostname, 'ipa/config/ca.crt')
        file_downloader(
            file_url=idm_cert_path_url,
            local_path=CERT_PATH,
            file_name='ipa.crt',
            hostname=default_sat.hostname,
        )
    elif server_type == 'AD':
        assert hostname is not None
        ssh.command('yum -y --disableplugin=foreman-protector install cifs-utils')
        command = r'mount -t cifs -o username=administrator,pass={0} //{1}/c\$ /mnt'
        ssh.command(command.format(settings.ldap.password, hostname))
        result = ssh.command(
            f'cp /mnt/Users/Administrator/Desktop/satqe-QE-SAT6-AD-CA.cer {CERT_PATH}'
        )
        if result.return_code != 0:
            raise AssertionError('Failed to copy the AD server certificate at right path')
    result = ssh.command(f'update-ca-trust extract && restorecon -R {CERT_PATH}')
    if result.return_code != 0:
        raise AssertionError('Failed to update and trust the certificate')
    result = ssh.command('systemctl restart httpd')
    if result.return_code != 0:
        raise AssertionError(f'Failed to restart the httpd after applying {server_type} cert')


def unsubscribe():
    """unregisters a machine from cdn"""
    run_command('subscription-manager unregister')
    run_command('subscription-manager clean')


@pytest.fixture(scope='module')
def clean_rhsm():
    """removes pre-existing candlepin certs and resets RHSM."""
    # removing the katello-ca-consumer
    run_command('rpm -qa | grep katello-ca-consumer | xargs -r rpm -e')

    # resetting rhsm.conf to point to cdn.
    run_command(
        "sed -i -e 's/^hostname.*/hostname=subscription.rhsm.redhat.com/' " "/etc/rhsm/rhsm.conf"
    )
    run_command("sed -i -e 's|^prefix.*|prefix=/subscription|' /etc/rhsm/rhsm.conf")
    run_command("sed -i -e 's|^baseurl.*|baseurl=https://cdn.redhat.com|' " "/etc/rhsm/rhsm.conf")
    run_command(
        "sed -i -e "
        "'s/^repo_ca_cert.*/repo_ca_cert=%(ca_cert_dir)sredhat-uep.pem/' "
        "/etc/rhsm/rhsm.conf"
    )


@pytest.fixture(scope='module')
def subscribe_satellite(clean_rhsm):
    """subscribe satellite to cdn"""
    run_command(
        'subscription-manager register --force --user={} --password={} {}'.format(
            settings.subscription.rhn_username,
            settings.subscription.rhn_password,
            # set release to "7Server" currently with this scope
            f'--release="{RHEL_7_MAJOR_VERSION}Server"',
        )
    )
    has_success_msg = 'Successfully attached a subscription'
    attach_cmd = f'subscription-manager attach --pool={settings.subscription.rhn_poolid}'
    result = run_command(attach_cmd)
    if has_success_msg in ''.join(result):
        run_command(
            f'subscription-manager repos --enable "rhel-{RHEL_7_MAJOR_VERSION}-server-extras-rpms"'
        )
        yield
    else:
        pytest.fail("Failed to attach system to pool. Aborting Test!.")
    unsubscribe()


@pytest.fixture()
def ldap_usergroup_name():
    """Return some random usergroup name,
    and attempt to delete such usergroup when test finishes.
    """
    usergroup_name = gen_string('alphanumeric')
    yield usergroup_name
    user_groups = entities.UserGroup().search(query={'search': f'name="{usergroup_name}"'})
    if user_groups:
        user_groups[0].delete()


@pytest.fixture()
def ldap_tear_down():
    """Teardown the all ldap settings user, usergroup and ldap delete"""
    yield
    ldap_auth_sources = entities.AuthSourceLDAP().search()
    for ldap_auth in ldap_auth_sources:
        users = entities.User(auth_source=ldap_auth).search()
        for user in users:
            user.delete()
        ldap_auth.delete()


@pytest.fixture()
def external_user_count():
    """return the external auth source user count"""
    users = entities.User().search()
    yield len([user for user in users if user.auth_source_name == 'External'])


@pytest.fixture()
def groups_teardown():
    """teardown for groups created for external/remote groups"""
    yield
    # tier down groups
    for group_name in ('sat_users', 'sat_admins', EXTERNAL_GROUP_NAME):
        user_groups = entities.UserGroup().search(query={'search': f'name="{group_name}"'})
        if user_groups:
            user_groups[0].delete()


@pytest.fixture()
def rhsso_groups_teardown():
    """Teardown the rhsso groups"""
    yield
    for group_name in ('sat_users', 'sat_admins'):
        delete_rhsso_group(group_name)


@pytest.fixture()
def multigroup_setting_cleanup():
    """Adding and removing the user to/from ipa group"""
    sat_users = settings.ipa.groups
    idm_users = settings.ipa.group_users
    ssh.command(cmd=f'echo {settings.ipa.password} | kinit admin', hostname=settings.ipa.hostname)
    cmd = f'ipa group-add-member {sat_users[0]} --users={idm_users[1]}'
    ssh.command(cmd, hostname=settings.ipa.hostname)
    yield
    cmd = f'ipa group-remove-member {sat_users[0]} --users={idm_users[1]}'
    ssh.command(cmd, hostname=settings.ipa.hostname)


@pytest.fixture()
def ipa_add_user():
    """Create an IPA user and delete it"""
    result = ssh.command(
        cmd=f'echo {settings.ipa.password} | kinit admin', hostname=settings.ipa.hostname
    )
    assert result.return_code == 0
    test_user = gen_string('alpha')
    add_user_cmd = (
        f'echo {settings.ipa.password} | ipa user-add {test_user} --first'
        f'={test_user} --last={test_user} --password'
    )
    result = ssh.command(cmd=add_user_cmd, hostname=settings.ipa.hostname)
    assert result.return_code == 0
    yield test_user

    result = ssh.command(cmd=f'ipa user-del {test_user}', hostname=settings.ipa.hostname)
    assert result.return_code == 0


def generate_otp(secret):
    """Return the time_based_otp"""
    time_otp = pyotp.TOTP(secret)
    return time_otp.now()


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
def test_positive_end_to_end(session, ldap_tear_down, ldap_auth_source):
    """Perform end to end testing for LDAP authentication component

    :id: a6528239-e090-4379-a850-3900ee625b24

    :expectedresults: All expected CRUD actions finished successfully

    :CaseLevel: Integration

    :CaseImportance: High

    :parametrized: yes
    """
    new_server = gen_url()
    ldap_auth_name = gen_string('alphanumeric')
    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ldap_auth_source['ldap_hostname'],
                'ldap_server.server_type': ldap_auth_source['server_type'],
                'account.account_name': ldap_auth_source['ldap_user_name'],
                'account.password': ldap_auth_source['ldap_user_passwd'],
                'account.base_dn': ldap_auth_source['base_dn'],
                'account.groups_base_dn': ldap_auth_source['group_base_dn'],
                'attribute_mappings.login': ldap_auth_source['attr_login'],
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


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_create_org_and_loc(session, ldap_tear_down, ldap_auth_source):
    """Create LDAP auth_source with org and loc assigned.

    :id: 4f595af4-fc01-44c6-a614-a9ec827e3c3c

    :steps:
        1. Create a new LDAP Auth source, provide organization and
           location information.
        2. Fill in all the fields appropriately.

    :expectedresults: Whether creating LDAP Auth and associating org
        and loc is successful.

    :parametrized: yes
    """
    org = entities.Organization().create()
    loc = entities.Location().create()
    ldap_auth_name = gen_string('alphanumeric')
    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ldap_auth_source['ldap_hostname'],
                'ldap_server.server_type': ldap_auth_source['server_type'],
                'account.account_name': ldap_auth_source['ldap_user_name'],
                'account.password': ldap_auth_source['ldap_user_passwd'],
                'account.base_dn': ldap_auth_source['base_dn'],
                'account.groups_base_dn': ldap_auth_source['group_base_dn'],
                'attribute_mappings.login': ldap_auth_source['attr_login'],
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
        assert ldap_source['ldap_server']['host'] == ldap_auth_source['ldap_hostname']
        assert ldap_source['ldap_server']['port'] == '389'
        assert ldap_source['ldap_server']['server_type'] == ldap_auth_source['server_type']
        assert ldap_source['account']['account_name'] == ldap_auth_source['ldap_user_name']
        assert ldap_source['account']['base_dn'] == ldap_auth_source['base_dn']
        assert ldap_source['account']['groups_base_dn'] == ldap_auth_source['group_base_dn']
        assert not ldap_source['account']['onthefly_register']
        assert ldap_source['account']['usergroup_sync']
        assert ldap_source['attribute_mappings']['login'] == ldap_auth_source['attr_login']
        assert ldap_source['attribute_mappings']['first_name'] == LDAP_ATTR['firstname']
        assert ldap_source['attribute_mappings']['last_name'] == LDAP_ATTR['surname']
        assert ldap_source['attribute_mappings']['mail'] == LDAP_ATTR['mail']


@pytest.mark.upgrade
@pytest.mark.parametrize('ldap_auth_source', ['AD_2016', 'AD_2019', 'IPA'], indirect=True)
@pytest.mark.destructive
def test_positive_create_with_https(
    session, subscribe_satellite, test_name, ldap_auth_source, ldap_tear_down, default_sat
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
    if ldap_auth_source['auth_type'] == 'ipa':
        set_certificate_in_satellite(server_type='IPA', default_sat=default_sat)
        username = settings.ipa.user
    else:
        set_certificate_in_satellite(
            server_type='AD', default_sat=default_sat, hostname=ldap_auth_source['ldap_hostname']
        )
        username = settings.ldap.username
    org = entities.Organization().create()
    loc = entities.Location().create()
    ldap_auth_name = gen_string('alphanumeric')

    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ldap_auth_source['ldap_hostname'],
                'ldap_server.ldaps': True,
                'ldap_server.server_type': ldap_auth_source['server_type'],
                'account.account_name': ldap_auth_source['ldap_user_cn'],
                'account.password': ldap_auth_source['ldap_user_passwd'],
                'account.base_dn': ldap_auth_source['base_dn'],
                'account.groups_base_dn': ldap_auth_source['group_base_dn'],
                'account.onthefly_register': True,
                'attribute_mappings.login': ldap_auth_source['attr_login'],
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
        assert ldap_source['ldap_server']['host'] == ldap_auth_source['ldap_hostname']
        assert ldap_source['ldap_server']['port'] == '636'
    with Session(test_name, username, ldap_auth_source['ldap_user_passwd']) as ldapsession:
        with pytest.raises(NavigationTriesExceeded):
            ldapsession.user.search('')
    users = entities.User().search(
        query={'search': 'login="{}"'.format(ldap_auth_source['ldap_user_name'])}
    )
    assert users[0].login == ldap_auth_source['ldap_user_name']


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
def test_positive_add_katello_role(
    test_name,
    session,
    auth_source,
    auth_source_ipa,
    ldap_usergroup_name,
    ldap_tear_down,
    ldap_auth_source,
):
    """Associate katello roles to User Group.
    [belonging to external User Group.]

    :id: aa5e3bf4-cb42-43a4-93ea-a2eea54b847a

    :Steps:
        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. Create and associate an External UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to
        access katello entities as per roles.

    :parametrized: yes
    """
    if ldap_auth_source['auth_type'] == 'ipa':
        auth_source_name = 'LDAP-' + auth_source_ipa.name
    else:
        auth_source_name = 'LDAP-' + auth_source.name
    ak_name = gen_string('alpha')
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
    with Session(
        test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
    ) as session:
        with pytest.raises(NavigationTriesExceeded):
            session.architecture.search('')
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert ldap_auth_source['ldap_user_name'] in current_user


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_update_external_roles(
    test_name, session, auth_source, ldap_usergroup_name, ldap_tear_down, ldap_auth_source
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

    :parametrized: yes
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
            test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
        ) as ldapsession:
            with pytest.raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.location.create({'name': location_name})
            assert ldapsession.location.search(location_name)[0]['Name'] == location_name
            current_user = ldapsession.location.read(location_name, 'current_user')['current_user']
            assert ldap_auth_source['ldap_user_name'] in current_user
        session.usergroup.update(
            ldap_usergroup_name, {'roles.resources.assigned': [katello_role.name]}
        )
        session.usergroup.refresh_external_group(ldap_usergroup_name, EXTERNAL_GROUP_NAME)
    with Session(
        test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
    ) as session:
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert ldap_auth_source['ldap_user_name'] in current_user


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_delete_external_roles(
    test_name, session, auth_source, ldap_usergroup_name, ldap_tear_down, ldap_auth_source
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

    :parametrized: yes
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
            test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
        ) as ldapsession:
            with pytest.raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.location.create({'name': location_name})
            assert ldapsession.location.search(location_name)[0]['Name'] == location_name
            current_user = ldapsession.location.read(location_name, 'current_user')['current_user']
            assert ldap_auth_source['ldap_user_name'] in current_user
        session.usergroup.update(
            ldap_usergroup_name, {'roles.resources.unassigned': [foreman_role.name]}
        )
    with Session(
        test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
    ) as ldapsession:
        with pytest.raises(NavigationTriesExceeded):
            ldapsession.location.create({'name': gen_string('alpha')})


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
def test_positive_update_external_user_roles(
    test_name, session, auth_source, ldap_usergroup_name, ldap_tear_down, ldap_auth_source
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

    :parametrized: yes
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
            test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
        ) as ldapsession:
            ldapsession.location.create({'name': location_name})
            assert ldapsession.location.search(location_name)[0]['Name'] == location_name
            current_user = ldapsession.location.read(location_name, 'current_user')['current_user']
            assert ldap_auth_source['ldap_user_name'] in current_user
        session.user.update(
            ldap_auth_source['ldap_user_name'], {'roles.resources.assigned': [katello_role.name]}
        )
    with Session(
        test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
    ) as session:
        with pytest.raises(NavigationTriesExceeded):
            ldapsession.architecture.search('')
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert ldap_auth_source['ldap_user_name'] in current_user


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA'], indirect=True)
@pytest.mark.tier2
def test_positive_add_admin_role_with_org_loc(
    test_name,
    session,
    auth_source,
    auth_source_ipa,
    ldap_usergroup_name,
    module_org,
    ldap_tear_down,
    ldap_auth_source,
):
    """Associate Admin role to User Group with org and loc set.
    [belonging to external User Group.]

    :id: 00841778-f89e-4445-a6c6-f1470b6da32e

    :parametrized: yes

    :setup: LDAP Auth Source should be created with Org and Location
            Associated.

    :Steps:
        1. Create an UserGroup.
        2. Assign admin role to UserGroup.
        3. Create and associate an External UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to
        access some of the pages, with the associated org and loc
        in LDAP Auth source page as the context set.
    """
    if ldap_auth_source['auth_type'] == 'ipa':
        auth_source_name = 'LDAP-' + auth_source_ipa.name
    else:
        auth_source_name = 'LDAP-' + auth_source.name
    ak_name = gen_string('alpha')
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
    with Session(
        test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
    ) as session:
        session.location.create({'name': location_name})
        assert session.location.search(location_name)[0]['Name'] == location_name
        location = session.location.read(location_name, ['current_user', 'primary'])
        assert ldap_auth_source['ldap_user_name'] in location['current_user']
        assert location['primary']['name'] == location_name
        session.organization.select(module_org.name)
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        ak = session.activationkey.read(ak_name, 'details.name')
        assert ak['details']['name'] == ak_name


@pytest.mark.parametrize('ldap_auth_source', ['AD_2016', 'AD_2019', 'IPA'], indirect=True)
@pytest.mark.tier2
def test_positive_add_foreman_role_with_org_loc(
    test_name,
    session,
    auth_source,
    auth_source_ipa,
    ldap_usergroup_name,
    module_org,
    module_loc,
    ldap_tear_down,
    ldap_auth_source,
):
    """Associate foreman roles to User Group with org and loc set.
    [belonging to external User Group.]

    :id: b39d7b2a-6d78-4c35-969a-37c8317ce64f

    :parametrized: yes

    :setup: LDAP Auth Source should be created with Org and Location
            Associated.

    :Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. Create and associate an External UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to
        access foreman entities as per roles, with the associated org and
        loc in LDAP Auth source page as the context set.
    """
    if ldap_auth_source['auth_type'] == 'ipa':
        auth_source_name = 'LDAP-' + auth_source_ipa.name
    else:
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
            test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
        ) as ldapsession:
            with pytest.raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.hostgroup.create({'host_group.name': name})
        hostgroup = session.hostgroup.read(name, ['organizations', 'locations'])
        assert len(hostgroup['organizations']['resources']['assigned']) == 1
        assert module_org.name in hostgroup['organizations']['resources']['assigned']
        assert len(hostgroup['locations']['resources']['assigned']) == 1
        assert module_loc.name in hostgroup['locations']['resources']['assigned']


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA'], indirect=True)
@pytest.mark.tier2
def test_positive_add_katello_role_with_org(
    test_name,
    session,
    auth_source,
    auth_source_ipa,
    ldap_usergroup_name,
    module_org,
    ldap_tear_down,
    ldap_auth_source,
):
    """Associate katello roles to User Group with org set.
    [belonging to external User Group.]

    :id: a2ebd4de-eb0a-47da-81e8-00942eedcbf6

    :parametrized: yes

    :setup: LDAP Auth Source should be created with Organization associated.

    :Steps:
        1. Create an UserGroup.
        2. Assign some katello roles to UserGroup.
        3. Create and associate an External UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to
        access katello entities as per roles, with the associated org
        in LDAP Auth source page as the context set.
    """
    if ldap_auth_source['auth_type'] == 'ipa':
        auth_source_name = 'LDAP-' + auth_source_ipa.name
    else:
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
            test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
        ) as ldapsession:
            with pytest.raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.activationkey.create({'name': ak_name})
        results = session.activationkey.search(ak_name)
        assert results[0]['Name'] == ak_name
        session.organization.select(different_org.name)
        assert not session.activationkey.search(ak_name)[0]['Name'] == ak_name
    ak = (
        entities.ActivationKey(organization=module_org)
        .search(query={'search': f'name={ak_name}'})[0]
        .read()
    )
    assert ak.organization.id == module_org.id


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_create_user_in_ldap_mode(
    session, auth_source, auth_source_ipa, auth_source_open_ldap, ldap_auth_source, ldap_tear_down
):
    """Create User in ldap mode

    :id: 0668b2ca-831e-4568-94fb-80e45dd7d001

    :parametrized: yes

    :expectedresults: User is created without specifying the password
    """
    auth_source_name = 'LDAP-' + auth_source.name
    name = gen_string('alpha')
    with session:
        session.user.create({'user.login': name, 'user.auth': auth_source_name})
        assert session.user.search(name)[0]['Username'] == name
        user_values = session.user.read(name)
        assert user_values['user']['auth'] == auth_source_name


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA'], indirect=True)
@pytest.mark.tier2
def test_positive_login_user_no_roles(
    auth_source, auth_source_ipa, test_name, ldap_tear_down, ldap_auth_source
):
    """Login with LDAP Auth for user with no roles/rights

    :id: 7dc8d9a7-ff08-4d8e-a842-d370ffd69741

    :setup: assure properly functioning server for authentication

    :steps: Login to server with an user.

    :expectedresults: Log in to foreman UI successfully but cannot access
        functional areas of UI

    :parametrized: yes
    """
    with Session(
        test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
    ) as ldapsession:
        ldapsession.task.read_all()


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA'], indirect=True)
@pytest.mark.tier2
@pytest.mark.upgrade
def test_positive_login_user_basic_roles(
    test_name, session, auth_source, auth_source_ipa, ldap_tear_down, ldap_auth_source
):
    """Login with LDAP for user with roles/rights

    :id: ef202e94-8e5d-4333-a4bc-e573b03ebfc8

    :parametrized: yes

    :setup: assure properly functioning server for authentication

    :steps: Login to server with an user.

    :expectedresults: Log in to foreman UI successfully and can access
        appropriate functional areas in UI
    """
    name = gen_string('alpha')
    role = entities.Role().create()
    permissions = {'Architecture': PERMISSIONS['Architecture']}
    create_role_permissions(role, permissions)
    with Session(
        test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
    ) as ldapsession:
        with pytest.raises(NavigationTriesExceeded):
            ldapsession.usergroup.search('')
    with session:
        session.user.update(
            ldap_auth_source['ldap_user_name'], {'roles.resources.assigned': [role.name]}
        )
    with Session(
        test_name, ldap_auth_source['ldap_user_name'], ldap_auth_source['ldap_user_passwd']
    ) as ldapsession:
        ldapsession.architecture.create({'name': name})
        assert ldapsession.architecture.search(name)[0]['Name'] == name


@pytest.mark.upgrade
@pytest.mark.tier2
def test_positive_login_user_password_otp(auth_source_ipa, test_name, ldap_tear_down, ipa_data):
    """Login with password with time based OTP

    :id: be7eb5d6-3228-4660-aa64-c56f9f3ec5e0

    :setup: Assure properly functioning IPA server for authentication

    :steps: Login to server with an IPA user with time_based OTP.

    :expectedresults: Log in to foreman UI successfully
    """

    otp_pass = f"{ipa_data['ldap_user_passwd']}{generate_otp(ipa_data['time_based_secret'])}"
    with Session(test_name, ipa_data['ipa_otp_username'], otp_pass) as ldapsession:
        with pytest.raises(NavigationTriesExceeded):
            ldapsession.user.search('')
    users = entities.User().search(
        query={'search': 'login="{}"'.format(ipa_data['ipa_otp_username'])}
    )
    assert users[0].login == ipa_data['ipa_otp_username']


@pytest.mark.tier2
def test_negative_login_user_with_invalid_password_otp(
    auth_source_ipa, test_name, ldap_tear_down, ipa_data
):
    """Login with password with time based OTP

    :id: 3718c86e-5976-4fb8-9c80-4685d53bd955

    :setup: Assure properly functioning IPA server for authentication

    :steps: Login to server with an IPA user with invalid OTP.

    :expectedresults: Log in to foreman UI should be failed
    """

    password_with_otp = f"{ipa_data['ldap_user_passwd']}{gen_string(str_type='numeric', length=6)}"
    with Session(test_name, ipa_data['ipa_otp_username'], password_with_otp) as ldapsession:
        with pytest.raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.destructive
def test_single_sign_on_ldap_ipa_server(
    subscribe_satellite, enroll_idm_and_configure_external_auth, ldap_tear_down, default_sat
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
        run_command(cmd='satellite-installer --foreman-ipa-authentication=true', timeout=800)
        run_command('foreman-maintain service restart', timeout=300)
        if is_open('BZ:1941997'):
            curl_command = f'curl -k -u : --negotiate {default_sat.url}/users/extlogin'
        else:
            curl_command = f'curl -k -u : --negotiate {default_sat.url}/users/extlogin/'
        result = run_command(curl_command)
        result = ''.join(result)
        assert 'redirected' in result
        assert f'{default_sat.url}/hosts' in result
        assert 'You are being' in result
    finally:
        # resetting the settings to default for external auth
        run_command(cmd='satellite-installer --foreman-ipa-authentication=false', timeout=800)
        run_command('foreman-maintain service restart', timeout=300)
        run_command(
            cmd=f'ipa service-del HTTP/{default_sat.hostname}',
            hostname=settings.ipa.hostname,
        )
        run_command(
            cmd=f'ipa host-del {default_sat.hostname}',
            hostname=settings.ipa.hostname,
        )


@pytest.mark.parametrize(
    'enroll_ad_and_configure_external_auth', ['AD_2016', 'AD_2019'], indirect=True
)
@pytest.mark.destructive
def test_single_sign_on_ldap_ad_server(
    subscribe_satellite, enroll_ad_and_configure_external_auth, default_sat
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
        if is_open('BZ:1941997'):
            curl_command = f'curl -k -u : --negotiate {default_sat.url}/users/extlogin'
        else:
            curl_command = f'curl -k -u : --negotiate {default_sat.url}/users/extlogin/'
        result = run_command(curl_command)
        result = ''.join(result)
        assert 'redirected' in result
        assert f'{default_sat.url}/hosts' in result
    finally:
        # resetting the settings to default for external auth
        run_command(cmd='satellite-installer --foreman-ipa-authentication=false', timeout=800)
        run_command('foreman-maintain service restart', timeout=300)


@pytest.mark.destructive
def test_single_sign_on_using_rhsso(subscribe_satellite, rhsso_setting_setup, session):
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
            {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.rhsso_password}
        )
        with pytest.raises(NavigationTriesExceeded):
            session.user.search('')
        actual_user = session.task.read_all(widget_names="current_user")['current_user']
        assert settings.rhsso.rhsso_user in actual_user


@pytest.mark.external_auth
@pytest.mark.destructive
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
            'password': settings.rhsso.rhsso_password,
        }
        session.rhsso_login.login(login_details)
        view = session.rhsso_login.logout()
        assert view['login_again'] == 'Click to log in again'
        session.rhsso_login.login(login_details, external_login=True)
        actual_user = session.task.read_all(widget_names='current_user')['current_user']
        assert settings.rhsso.rhsso_user in actual_user


@pytest.mark.external_auth
@pytest.mark.destructive
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
            {'username': settings.rhsso.rhsso_user, 'password': settings.rhsso.rhsso_password}
        )
        sleep(360)
        with pytest.raises(NavigationTriesExceeded) as error:
            session.task.read_all(widget_names='current_user')['current_user']
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.external_auth
@pytest.mark.destructive
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
        'password': settings.rhsso.rhsso_password,
    }
    with Session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        actual_user = rhsso_session.task.read_all(widget_names='current_user')['current_user']
        assert user_details['firstName'] in actual_user
    users = entities.User().search()
    updated_count = len([user for user in users if user.auth_source_name == 'External'])
    assert updated_count == external_user_count + 1
    # checking delete user can't login anymore
    delete_rhsso_user(user_details['username'])
    with Session(login=False) as rhsso_session:
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.rhsso_login.login(login_details)
            rhsso_session.task.read_all()
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.external_auth
@pytest.mark.skip_if_open("BZ:1873439")
@pytest.mark.destructive
def test_login_failure_rhsso_user_if_internal_user_exist(
    enable_external_auth_rhsso, rhsso_setting_setup, session, module_org, module_loc
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
    entities.User(
        admin=True,
        default_organization=module_org,
        default_location=module_loc,
        login=username,
        password=settings.rhsso.rhsso_password,
    ).create()
    external_rhsso_user = create_new_rhsso_user(client_id, username=username)
    login_details = {
        'username': external_rhsso_user['username'],
        'password': settings.rhsso.rhsso_password,
    }
    with Session(login=False) as rhsso_session:
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.rhsso_login.login(login_details)
            rhsso_session.task.read_all()
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.external_auth
@pytest.mark.destructive
def test_user_permissions_rhsso_user_after_group_delete(
    enable_external_auth_rhsso,
    rhsso_setting_setup,
    session,
    module_org,
    module_loc,
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
    user_group = make_usergroup({'admin': 1, 'name': group_name})
    external_auth_source = ExternalAuthSource.info({'name': "External"})
    make_usergroup_external(
        {
            'auth-source-id': external_auth_source['id'],
            'user-group-id': user_group['id'],
            'name': group_name,
        }
    )

    # verify the rhsso-user permissions
    with Session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        rhsso_session.location.create({'name': location_name})
        assert rhsso_session.location.search(location_name)[0]['Name'] == location_name
        current_user = rhsso_session.location.read(location_name, 'current_user')['current_user']
        assert login_details['username'] in current_user

    # delete the rhsso group and verify the rhsso-user permissions
    delete_rhsso_group(group_name=group_name)
    with Session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        with pytest.raises(NavigationTriesExceeded) as error:
            rhsso_session.location.create({'name': location_name})
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.external_auth
@pytest.mark.destructive
def test_user_permissions_rhsso_user_multiple_group(
    enable_external_auth_rhsso,
    rhsso_setting_setup,
    session,
    module_org,
    module_loc,
    groups_teardown,
    rhsso_groups_teardown,
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
    katello_role = entities.Role().create()
    create_role_permissions(katello_role, user_permissions)

    group_names = ['sat_users', 'sat_admins']
    arguments = [{'role': katello_role}, {'admin': 1}]
    external_auth_source = ExternalAuthSource.info({'name': "External"})
    for group_name, argument in zip(group_names, arguments):
        # adding/creating rhsso groups
        create_group(group_name=group_name)
        update_rhsso_user(username, group_name=group_name)
        argument['name'] = group_name

        # creating satellite external groups
        user_group = make_usergroup(argument)
        make_usergroup_external(
            {
                'auth-source-id': external_auth_source['id'],
                'user-group-id': user_group['id'],
                'name': group_name,
            }
        )

    # verify that user has highest level of permission
    with Session(login=False) as rhsso_session:
        rhsso_session.rhsso_login.login(login_details)
        rhsso_session.location.create({'name': location_name})
        assert rhsso_session.location.search(location_name)[0]['Name'] == location_name
        current_user = rhsso_session.location.read(location_name, 'current_user')['current_user']
        assert login_details['username'] in current_user


@pytest.mark.destructive
def test_totp_user_login(session, ad_data):
    """Verify the TOTP authentication of LDAP user interlinked with RH-SSO

    :id: cf8dfa00-4f48-11eb-b7d5-d46d6dd3b5b2

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Setup the Satellite to integrate with RHSSO
        2. Login into Satellite using LDAP user which is linked to RHSSO

    :expectedresults: After entering the login details in RHSSO page user should
        logged into Satellite
    """
    ad_data = ad_data()
    login_details = {
        'username': ad_data['ldap_user_name'],
        'password': ad_data['ldap_user_passwd'],
    }
    with Session(login=False) as rhsso_session:
        totp = generate_otp(secret=settings.rhsso.totp_secret)
        rhsso_session.rhsso_login.login(login_details, totp={'totp': totp})
        assert rhsso_session.bookmark.search("controller = hosts")


@pytest.mark.destructive
def test_permissions_external_ldap_mapped_rhsso_group(
    rhsso_setting_setup, session, ad_data, groups_teardown
):
    """Verify the usergroup permissions are synced correctly with LDAP usergroup mapped
        with the rhsso. The ldap user gets right permissions based on the role

    :id: a7bd84b8-4f6c-11eb-8eb2-d46d6dd3b5b2

    :setup: Enroll the RH-SSO Configuration for External Authentication

    :steps:
        1. Setup the Satellite to integrate with RHSSO
        2. Create the user group and mapped with the external ldap rhsso user group

    :expectedresults: The external ldap mapped rhsso user should contain the permissions
        based on the user group level

    """
    ad_data = ad_data()
    login_details = {
        'username': ad_data['ldap_user_name'],
        'password': ad_data['ldap_user_passwd'],
    }
    with Session(url='/users/login/') as session:
        session.usergroup.create(
            {
                'usergroup.name': EXTERNAL_GROUP_NAME,
                'roles.resources.assigned': ['Viewer'],
                'external_groups.name': EXTERNAL_GROUP_NAME,
                'external_groups.auth_source': 'EXTERNAL',
            }
        )

    with Session(login=False) as rhsso_session:
        totp = generate_otp(secret=settings.rhsso.totp_secret)
        rhsso_session.rhsso_login.login(login_details, totp={'totp': totp})
        assert rhsso_session.user.search(ad_data['ldap_user_name']) is not None


@pytest.mark.parametrize("ldap_auth_source", ["AD", "IPA", "OPENLDAP"], indirect=True)
@pytest.mark.tier2
def test_positive_test_connection_functionality(session, ldap_auth_source):
    """Verify for a positive test connection response

    :id: 5daf3976-9b5c-11ea-96f8-4ceb42ab8dbc

    :steps: Assert test connection of AD, IPA and OPENLDAP.

    :expectedresults: Positive test connection of AD and IPA

    :parametrized: yes
    """
    with session:
        session.ldapauthentication.test_connection(
            {'ldap_server.host': ldap_auth_source['ldap_hostname']}
        )


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
def test_negative_login_with_incorrect_password(test_name, ldap_auth_source):
    """Attempt to login in Satellite an user with the wrong password

    :id: 3f09de90-a656-11ea-aa43-4ceb42ab8dbc

    :steps:
        1. Randomaly generate a string as a incorrect password.
        2. Try login with the incorrect password

    :expectedresults: Login fails

    :parametrized: yes
    """
    incorrect_password = gen_string('alphanumeric')
    with Session(
        test_name, user=ldap_auth_source['ldap_user_name'], password=incorrect_password
    ) as ldapsession:
        with pytest.raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.tier2
def test_negative_login_with_disable_user(ipa_data, auth_source_ipa):
    """Disabled IDM user cannot login

    :id: 49f28006-aa1f-11ea-90d3-4ceb42ab8dbc

    :steps: Try login from the disabled user

    :expectedresults: Login fails
    """
    with Session(
        user=ipa_data['disabled_user_ipa'], password=ipa_data['ldap_user_passwd']
    ) as ldapsession:
        with pytest.raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.tier2
def test_email_of_the_user_should_be_copied(session, auth_source_ipa, ipa_data, ldap_tear_down):
    """Email of the user created in idm server ( set as external authorization source )
    should be copied to the satellite.

    :id: 9ce7d7c6-dc73-11ea-8a97-4ceb42ab8dbc

    :steps:
        1. Create a new auth source with onthefly enabled
        2. Login to the satellite with the user (from IDM) to create the account
        3. Assert the email of the newly created user

    :expectedresults: Email is copied to Satellite:
    """
    run_command(cmd=f'echo {settings.ipa.password} | kinit admin', hostname=settings.ipa.hostname)
    result = run_command(
        cmd=f"ipa user-find --login {ipa_data['ldap_user_name']}",
        hostname=settings.ipa.hostname,
    )
    for line in result:
        if 'Email' in line:
            _, result = line.split(': ', 2)
            break
    with Session(
        user=ipa_data['ldap_user_name'], password=ipa_data['ldap_user_passwd']
    ) as ldapsession:
        ldapsession.task.read_all()
    with session:
        user_value = session.user.read(ipa_data['ldap_user_name'], widget_names='user')
        assert user_value['user']['mail'] == result


@pytest.mark.tier2
def test_deleted_idm_user_should_not_be_able_to_login(auth_source_ipa, ldap_tear_down):
    """After deleting a user in IDM, user should not be able to login into satellite

    :id: 18ad0526-e083-11ea-b1ad-4ceb42ab8dbc

    :steps:
        1. Create a new auth source with onthefly enabled
        2. Login to satellite to create the user
        3. Delete the user from IDM
        4. Try login to the satellite from the user

    :expectedresults: User login fails
    """
    result = ssh.command(
        cmd=f"echo {settings.ipa.password} | kinit admin", hostname=settings.ipa.hostname
    )
    assert result.return_code == 0
    test_user = gen_string('alpha')
    add_user_cmd = (
        f'echo {settings.ipa.password} | ipa user-add {test_user} --first'
        f'={test_user} --last={test_user} --password'
    )
    result = ssh.command(cmd=add_user_cmd, hostname=settings.ipa.hostname)
    assert result.return_code == 0
    with Session(user=test_user, password=settings.ipa.password) as ldapsession:
        ldapsession.task.read_all()
    result = ssh.command(cmd=f'ipa user-del {test_user}', hostname=settings.ipa.hostname)
    assert result.return_code == 0
    with Session(user=test_user, password=settings.ipa.password) as ldapsession:
        with pytest.raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
def test_onthefly_functionality(session, ldap_auth_source, ldap_tear_down):
    """User will not be created automatically in Satellite if onthefly is
    disabled

    :id: 6998de30-ef77-11ea-a0ce-0c7a158cbff4

    :Steps:
        1. Create an auth source with onthefly disabled
        2. Try login with a user from auth source

    :expectedresults: Login fails

    :parametrized: yes
    """
    ldap_auth_name = gen_string('alphanumeric')
    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ldap_auth_source['ldap_hostname'],
                'ldap_server.server_type': ldap_auth_source['server_type'],
                'account.account_name': ldap_auth_source['ldap_user_cn'],
                'account.password': ldap_auth_source['ldap_user_passwd'],
                'account.base_dn': ldap_auth_source['base_dn'],
                'account.groups_base_dn': ldap_auth_source['group_base_dn'],
                'account.onthefly_register': False,
                'attribute_mappings.login': ldap_auth_source['attr_login'],
                'attribute_mappings.first_name': LDAP_ATTR['firstname'],
                'attribute_mappings.last_name': LDAP_ATTR['surname'],
                'attribute_mappings.mail': LDAP_ATTR['mail'],
            }
        )
    with Session(
        user=ldap_auth_source['ldap_user_name'], password=ldap_auth_source['ldap_user_passwd']
    ) as ldapsession:
        with pytest.raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == 'NavigationTriesExceeded'


@pytest.mark.stubbed
def test_login_logout_using_cac_card():
    """Verify Satellite Integration with RHSSO Server Login, Logout using CAC Card from Satellite UI

    :id: e79385ac-f679-11ea-b961-d46d6dd3b5b2

    :CaseImportance: High

    :CaseAutomation: ManualOnly

    :steps:
        1. configure the Satellite with RH-SSO instance
        2. configure the firefox to use the CAC card cert, insert the CAC card
        3. open the satellite url from firefox browser, authenticate using CAC card

    :expectedresults: Satellite login/logout should be successful
    """


@pytest.mark.stubbed
def test_timeout_and_cac_card_ejection():
    """Verify CAC card ejection and timeout with Satellite integrated with RHSSO

    :id: 8de96d2a-f67c-11ea-8a63-d46d6dd3b5b2

    :CaseImportance: High

    :CaseAutomation: ManualOnly

    :steps:
        1. configure the Satellite with RH-SSO instance
        2. configure the firefox to use the CAC card cert, insert the CAC card
        3. open the satellite url from firefox browser, authenticate using CAC card
        4. setup the timeout setting in satellite
        5. eject the cac card

    :expectedresults: Satellite should terminate the session after mentioned timeout in setting
    """


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
@pytest.mark.skip_if_open('BZ:1670397')
def test_verify_attribute_of_users_are_updated(session, ldap_auth_source, ldap_tear_down):
    """Verify if attributes of LDAP user are updated upon first login when
        onthefly is disabled

    :id: 163b346c-03be-11eb-acb9-0c7a158cbff4

    :customerscenario: true

    :Steps:
        1. Create authsource with onthefly disabled
        2. Create a user manually and select the authsource created
        3. Attributes of the user (like names and email) should be synced.

    :BZ: 1670397

    :expectedresults: The attributes should be synced.

    :parametrized: yes
    """
    ldap_auth_name = gen_string('alphanumeric')
    auth_source_name = 'LDAP-' + ldap_auth_name
    with session:
        session.ldapauthentication.create(
            {
                'ldap_server.name': ldap_auth_name,
                'ldap_server.host': ldap_auth_source['ldap_hostname'],
                'ldap_server.server_type': ldap_auth_source['server_type'],
                'account.account_name': ldap_auth_source['ldap_user_name'],
                'account.password': ldap_auth_source['ldap_user_passwd'],
                'account.base_dn': ldap_auth_source['base_dn'],
                'account.onthefly_register': False,
                'account.groups_base_dn': ldap_auth_source['group_base_dn'],
                'attribute_mappings.login': ldap_auth_source['attr_login'],
                'attribute_mappings.first_name': LDAP_ATTR['firstname'],
                'attribute_mappings.last_name': LDAP_ATTR['surname'],
                'attribute_mappings.mail': LDAP_ATTR['mail'],
            }
        )
        session.user.create(
            {
                'user.login': ldap_auth_source['ldap_user_name'],
                'user.auth': auth_source_name,
                'roles.admin': True,
            }
        )
    with Session(
        user=ldap_auth_source['ldap_user_name'], password=ldap_auth_source['ldap_user_passwd']
    ) as ldapsession:
        with pytest.raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == 'NavigationTriesExceeded'
    with session:
        user_values = session.user.read(ldap_auth_source['ldap_user_name'])
        assert ldap_auth_source['ldap_user_name'] == user_values['user']['login']
        assert ldap_auth_source['ldap_user_name'] in user_values['user']['firstname']
        assert ldap_auth_source['ldap_user_name'] in user_values['user']['lastname']
        assert ldap_auth_source['ldap_user_name'] in user_values['user']['mail']


@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA', 'OPENLDAP'], indirect=True)
@pytest.mark.tier2
def test_login_failure_if_internal_user_exist(
    session, test_name, ldap_auth_source, module_org, module_loc
):
    """Verify the failure of login for the AD/IPA user in case same username
    internal user exists

    :id: 04ad146e-c2b5-4ec6-980e-327ad4350826

    :CaseImportance: High

    :parametrized: yes

    :steps:
        1. create an internal user with the same username as user existing in AD/IPA
        2. add the auth source in satellite and now try login using AD/IPA user

    :expectedresults: external AD/IPA user should not be able to login with the
        same username as internal
    """
    try:
        internal_username = ldap_auth_source['ldap_user_name']
        internal_password = gen_string('alphanumeric')
        user = entities.User(
            admin=True,
            default_organization=module_org,
            default_location=module_loc,
            login=internal_username,
            password=internal_password,
        ).create()
        with Session(
            test_name, internal_username, ldap_auth_source['ldap_user_passwd']
        ) as ldapsession:
            with pytest.raises(NavigationTriesExceeded) as error:
                ldapsession.user.search('')
            assert error.typename == 'NavigationTriesExceeded'
    finally:
        entities.User(id=user.id).delete()


@pytest.mark.skip_if_open("BZ:1812688")
@pytest.mark.tier2
def test_userlist_with_external_admin(session, auth_source_ipa, ldap_tear_down, groups_teardown):
    """All the external users should be displayed to all LDAP admins (internal and external).

    :id: 7c7bf34a-06f9-11eb-b174-d46d6dd3b5b2

    :steps:
        1. Create 2 groups on an IPA server: e.g. sat_admins and sat_users.
        2. On IPA, create user e.g. "idm_admin" and add to sat_admins.
        3. On IPA, create user e.g. "idm_user" and add to sat_users.
        4. Create IPA/IDM auth source
        5. Create 2 local groups on Satellite: sat_admins and sat_users, link them to their
            counterparts from IPA.
        6. Assign non-admin permissions to the sat_users group
        7. Check the Admin checkbox for the sat_admins group.
        8. On browser window 1, log into Satellite with user "idm_user"
            i.e. a member of the remote sat_users group.
        9. login with both local and remote admin and navigate to Administer > Users.

    :BZ: 1812688

    :expectedresults: show all users, remote or local, regardless of you being logged
        into Satellite as a local or remote admin.
    """
    # step 1, 2, 3 are already done from IDM and gather the data from settings
    sat_admins, sat_users = settings.ipa.groups
    idm_admin, idm_user = settings.ipa.group_users

    auth_source_name = f'LDAP-{auth_source_ipa.name}'
    user_permissions = {'Katello::ActivationKey': PERMISSIONS['Katello::ActivationKey']}
    katello_role = entities.Role().create()
    create_role_permissions(katello_role, user_permissions)
    with session:
        session.usergroup.create(
            {
                'usergroup.name': 'sat_users',
                'roles.resources.assigned': [katello_role.name],
                'external_groups.name': sat_users,
                'external_groups.auth_source': auth_source_name,
            }
        )
        session.usergroup.create(
            {
                'usergroup.name': 'sat_admins',
                'roles.admin': True,
                'external_groups.name': sat_admins,
                'external_groups.auth_source': auth_source_name,
            }
        )
    with Session(user=idm_user, password=settings.server.ssh_password) as ldapsession:
        assert idm_user in ldapsession.task.read_all()['current_user']

    # verify the users count with local admin and remote/external admin
    with Session(user=idm_admin, password=settings.server.ssh_password) as remote_admin_session:
        with Session(
            user=settings.server.admin_username, password=settings.server.admin_password
        ) as local_admin_session:
            assert local_admin_session.user.search(idm_user)[0]['Username'] == idm_user
            assert remote_admin_session.user.search(idm_user)[0]['Username'] == idm_user


@pytest.mark.skip_if_open('BZ:1883209')
@pytest.mark.tier2
def test_positive_group_sync_open_ldap_authsource(
    test_name, session, auth_source_open_ldap, ldap_usergroup_name, ldap_tear_down, open_ldap_data
):
    """Associate katello roles to User Group. [belonging to external OpenLDAP User Group.]

    :id: 11d148bc-015c-11eb-8043-d46d6dd3b5b2

    :BZ: 1883209

    :Steps:
        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. Create and associate an External OpenLDAP UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to access katello
        entities as per roles.
    """
    ak_name = gen_string('alpha')
    auth_source_name = 'LDAP-' + auth_source_open_ldap.name
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
    user_name = open_ldap_data.open_ldap_user
    with Session(test_name, user_name, open_ldap_data.password) as session:
        with pytest.raises(NavigationTriesExceeded):
            session.architecture.search('')
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert user_name.capitalize() in current_user


@pytest.mark.tier2
def test_verify_group_permissions(
    session, auth_source_ipa, multigroup_setting_cleanup, groups_teardown, ldap_tear_down
):
    """Verify group permission for external linked group

    :id: 7e2ef59c-0c68-11eb-b6f3-0c7a158cbff4

    :Steps:
        1. Create two usergroups and link it with external group having a
        user in common
        2. Give those usergroup different permissions
        3. Try login with the user common in both external group

    :expectedresults: Group with higher permission is applied on the user
    """
    sat_users = settings.ipa.groups
    idm_users = settings.ipa.group_users
    auth_source_name = f'LDAP-{auth_source_ipa.name}'
    user_permissions = {None: ['access_dashboard']}
    katello_role = entities.Role().create()
    create_role_permissions(katello_role, user_permissions)
    with session:
        session.usergroup.create(
            {
                'usergroup.name': 'sat_users',
                'roles.resources.assigned': [katello_role.name],
                'external_groups.name': sat_users[0],
                'external_groups.auth_source': auth_source_name,
            }
        )
        session.usergroup.create(
            {
                'usergroup.name': 'sat_admins',
                'roles.admin': True,
                'external_groups.name': sat_users[1],
                'external_groups.auth_source': auth_source_name,
            }
        )
    location_name = gen_string('alpha')
    with Session(user=idm_users[1], password=settings.server.ssh_password) as ldapsession:
        ldapsession.location.create({'name': location_name})
        assert ldapsession.location.search(location_name)[0]['Name'] == location_name


@pytest.mark.tier2
def test_verify_ldap_filters_ipa(session, ipa_add_user, auth_source_ipa, ipa_data, ldap_tear_down):
    """Verifying ldap filters in authsource to restrict access

    :id: 0052b272-08b1-11eb-80c6-0c7a158cbff4

    :Steps:
        1. Create authsource with onthefly enabled and ldap filter
        2. Verify login from users according to the filter

    :expectedresults: Login fails for restricted user
    """

    # 'test_user' able to login before the filter is applied.
    test_user = ipa_add_user
    with Session(user=test_user, password=ipa_data['ldap_user_passwd']) as ldapsession:
        ldapsession.task.read_all()

    # updating the authsource with filter
    group_name = ipa_data['groups'][0]
    ldap_data = f"(memberOf=cn={group_name},{ipa_data['group_base_dn']})"
    session.ldapauthentication.update(auth_source_ipa.name, {'account.ldap_filter': ldap_data})

    # 'test_user' not able login as it gets filtered out
    with Session(user=test_user, password=ipa_data['ldap_user_passwd']) as ldapsession:
        with pytest.raises(NavigationTriesExceeded) as error:
            ldapsession.user.search('')
        assert error.typename == 'NavigationTriesExceeded'
