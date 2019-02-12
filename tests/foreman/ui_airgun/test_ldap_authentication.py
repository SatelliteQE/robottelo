"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from navmazing import NavigationTriesExceeded
from pytest import raises
from widgetastic.exceptions import NoSuchElementException

from airgun.session import Session
from nailgun import entities

from robottelo.api.utils import create_role_permissions
from robottelo.config import settings
from robottelo.constants import (
    LDAP_ATTR,
    LDAP_SERVER_TYPE,
    PERMISSIONS,
)
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    bz_bug_is_open,
    fixture,
    run_in_one_thread,
    skip_if_not_set,
    tier2,
    upgrade,
)


pytestmark = [run_in_one_thread]


EXTERNAL_GROUP_NAME = 'foobargroup'


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
        'ldap_ipa_user_passwd': settings.ipa.password_ipa,
        'ipa_base_dn': settings.ipa.basedn_ipa,
        'ipa_group_base_dn': settings.ipa.grpbasedn_ipa,
        'ldap_ipa_hostname': settings.ipa.hostname_ipa,
    }


@fixture(scope='module')
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


@fixture()
def ldap_user_name(ldap_data, test_name):
    """Add LDAP user to satellite by logging in, return username to test and delete the user (if
    still exists) when test finishes.
    """
    with Session(
            test_name,
            ldap_data['ldap_user_name'],
            ldap_data['ldap_user_passwd'],
    ):
        pass
    yield ldap_data['ldap_user_name']
    users = entities.User().search(query={
        'search': 'login="{}"'.format(ldap_data['ldap_user_name'])
    })
    if users:
        users[0].delete()


@fixture()
def ldap_usergroup_name():
    """Return some random usergroup name, and attempt to delete such usergroup when test finishes.
    """
    usergroup_name = gen_string('alphanumeric')
    yield usergroup_name
    user_groups = entities.UserGroup().search(query={
        'search': 'name="{}"'.format(usergroup_name)
    })
    if user_groups:
        user_groups[0].delete()


@skip_if_not_set('ldap')
@tier2
def test_positive_create_with_ad(session, ldap_data):
    """Create LDAP authentication with AD

    :id: 02ca85b7-5029-4618-a835-63b002767cf7

    :steps:

        1. Create a new LDAP Auth source with AD.
        2. Fill in all the fields appropriately for AD.

    :expectedresults: Whether creating LDAP Auth with AD is successful.

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    with session:
        session.ldapauthentication.create({
            'ldap_server.name': name,
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
        })
        assert session.ldapauthentication.read_table_row(name)['Name'] == name


@skip_if_not_set('ldap')
@tier2
def test_positive_delete_with_ad(session, ldap_data):
    """Delete LDAP authentication with AD

    :id: 3cf59a72-ca99-40b1-bbd3-c1c80a4ae741

    :steps:

        1. Create a new LDAP Auth source with AD.
        2. Delete LDAP Auth source with AD.

    :expectedresults: Whether deleting LDAP Auth with AD is successful.

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    with session:
        session.ldapauthentication.create({
            'ldap_server.name': name,
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
        })
        assert session.ldapauthentication.read_table_row(name)
        session.ldapauthentication.delete(name)
        assert not session.ldapauthentication.read_table_row(name)


@skip_if_not_set('ldap')
@tier2
@upgrade
def test_positive_create_with_ad_org_and_loc(session, ldap_data):
    """Create LDAP auth_source for AD with org and loc assigned.

    :id: 4f595af4-fc01-44c6-a614-a9ec827e3c3c

    :steps:
        1. Create a new LDAP Auth source with AD, provide organization and
           location information.
        2. Fill in all the fields appropriately for AD.

    :expectedresults: Whether creating LDAP Auth with AD and associating org
        and loc is successful.

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    org = entities.Organization().create()
    loc = entities.Location().create()
    with session:
        session.ldapauthentication.create({
            'ldap_server.name': name,
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
            'organizations.resources.assigned': [org.name]
        })
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        assert session.ldapauthentication.read_table_row(name)['Name'] == name
        ldap_source = session.ldapauthentication.read(name)
        assert ldap_source['ldap_server']['name'] == name
        assert ldap_source['ldap_server']['host'] == ldap_data['ldap_hostname']
        assert ldap_source['ldap_server']['port'] == '389'
        assert ldap_source[
            'ldap_server']['server_type'] == LDAP_SERVER_TYPE['UI']['ad']
        assert ldap_source[
            'account']['account_name'] == ldap_data['ldap_user_name']
        assert ldap_source['account']['base_dn'] == ldap_data['base_dn']
        assert ldap_source[
            'account']['groups_base_dn'] == ldap_data['group_base_dn']
        assert not ldap_source['account']['onthefly_register']
        assert ldap_source['account']['usergroup_sync']
        assert ldap_source[
            'attribute_mappings']['login'] == LDAP_ATTR['login_ad']
        assert ldap_source[
            'attribute_mappings']['first_name'] == LDAP_ATTR['firstname']
        assert ldap_source[
            'attribute_mappings']['last_name'] == LDAP_ATTR['surname']
        assert ldap_source['attribute_mappings']['mail'] == LDAP_ATTR['mail']


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

    :CaseImportance: Critical
    """
    name = gen_string('alpha')
    org = entities.Organization().create()
    loc = entities.Location().create()
    with session:
        session.ldapauthentication.create({
            'ldap_server.name': name,
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
            'organizations.resources.assigned': [org.name]
        })
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=loc.name)
        assert session.ldapauthentication.read_table_row(name)['Name'] == name
        ldap_source = session.ldapauthentication.read(name)
        assert ldap_source['ldap_server']['name'] == name
        assert ldap_source[
            'ldap_server']['host'] == ipa_data['ldap_ipa_hostname']
        assert ldap_source['ldap_server']['port'] == '389'
        assert ldap_source[
            'ldap_server']['server_type'] == LDAP_SERVER_TYPE['UI']['ipa']
        assert ldap_source[
            'account']['account_name'] == ipa_data['ldap_ipa_user_name']
        assert ldap_source['account']['base_dn'] == ipa_data['ipa_base_dn']
        assert ldap_source[
            'account']['groups_base_dn'] == ipa_data['ipa_group_base_dn']
        assert not ldap_source['account']['onthefly_register']
        assert ldap_source['account']['usergroup_sync']
        assert ldap_source[
            'attribute_mappings']['login'] == LDAP_ATTR['login']
        assert ldap_source[
            'attribute_mappings']['first_name'] == LDAP_ATTR['firstname']
        assert ldap_source[
            'attribute_mappings']['last_name'] == LDAP_ATTR['surname']
        assert ldap_source['attribute_mappings']['mail'] == LDAP_ATTR['mail']


@tier2
def test_positive_add_katello_role(
        session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name):
    """Associate katello roles to User Group.
    [belonging to external AD User Group.]

    :id: aa5e3bf4-cb42-43a4-93ea-a2eea54b847a

    :Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. Create and associate an External AD UserGroup.

    :expectedresults: Whether a User belonging to User Group is able to
        access katello entities as per roles.

    :CaseLevel: Integration
    """
    ak_name = gen_string('alpha')
    auth_source_name = 'LDAP-' + auth_source.name
    user_permissions = {'Katello::ActivationKey': PERMISSIONS['Katello::ActivationKey']}
    katello_role = entities.Role().create()
    create_role_permissions(katello_role, user_permissions)
    with session:
        session.usergroup.create({
            'usergroup.name': ldap_usergroup_name,
            'roles.resources.assigned': [katello_role.name],
            'external_groups.name': EXTERNAL_GROUP_NAME,
            'external_groups.auth_source': auth_source_name,
        })
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.user.update(ldap_data['ldap_user_name'], {'user.auth': auth_source_name})
        session.usergroup.refresh_external_group(ldap_usergroup_name, EXTERNAL_GROUP_NAME)
    with Session(
            test_name,
            ldap_data['ldap_user_name'],
            ldap_data['ldap_user_passwd'],
    ) as session:
        with raises(NavigationTriesExceeded):
            session.architecture.search('')
        if bz_bug_is_open(1652938):
            try:
                session.activationkey.search('')
            except NoSuchElementException:
                session.browser.refresh()
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert current_user == ldap_data['ldap_user_name']


@upgrade
@tier2
def test_positive_update_external_roles(
        session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name):
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

    :CaseLevel: Integration
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
        session.usergroup.create({
            'usergroup.name': ldap_usergroup_name,
            'roles.resources.assigned': [foreman_role.name],
            'external_groups.name': EXTERNAL_GROUP_NAME,
            'external_groups.auth_source': auth_source_name,
        })
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.user.update(ldap_data['ldap_user_name'], {'user.auth': auth_source_name})
        with Session(
                test_name,
                ldap_data['ldap_user_name'],
                ldap_data['ldap_user_passwd'],
        ) as ldapsession:
            with raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.location.create({'name': location_name})
            assert ldapsession.location.search(location_name)[0]['Name'] == location_name
            current_user = ldapsession.location.read(location_name, 'current_user')['current_user']
            assert current_user == ldap_data['ldap_user_name']
        session.usergroup.update(
            ldap_usergroup_name, {'roles.resources.assigned': [katello_role.name]})
        session.usergroup.refresh_external_group(ldap_usergroup_name, EXTERNAL_GROUP_NAME)
    with Session(
            test_name,
            ldap_data['ldap_user_name'],
            ldap_data['ldap_user_passwd'],
    ) as session:
        if bz_bug_is_open(1652938):
            try:
                session.activationkey.search('')
            except NoSuchElementException:
                session.browser.refresh()
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert current_user == ldap_data['ldap_user_name']


@tier2
@upgrade
def test_positive_delete_external_roles(
        session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name):
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

    :CaseLevel: Integration
    """
    auth_source_name = 'LDAP-' + auth_source.name
    location_name = gen_string('alpha')
    foreman_role = entities.Role().create()
    foreman_permissions = {'Location': PERMISSIONS['Location']}
    create_role_permissions(foreman_role, foreman_permissions)
    with session:
        session.usergroup.create({
            'usergroup.name': ldap_usergroup_name,
            'roles.resources.assigned': [foreman_role.name],
            'external_groups.name': EXTERNAL_GROUP_NAME,
            'external_groups.auth_source': auth_source_name,
        })
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.user.update(ldap_data['ldap_user_name'], {'user.auth': auth_source_name})
        with Session(
                test_name,
                ldap_data['ldap_user_name'],
                ldap_data['ldap_user_passwd'],
        ) as ldapsession:
            with raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            ldapsession.location.create({'name': location_name})
            assert ldapsession.location.search(location_name)[0]['Name'] == location_name
            current_user = ldapsession.location.read(location_name, 'current_user')['current_user']
            assert current_user == ldap_data['ldap_user_name']
        session.usergroup.update(
            ldap_usergroup_name, {'roles.resources.unassigned': [foreman_role.name]})
    with Session(
            test_name,
            ldap_data['ldap_user_name'],
            ldap_data['ldap_user_passwd'],
    ) as ldapsession:
        with raises(NavigationTriesExceeded):
            ldapsession.location.create({'name': gen_string('alpha')})


@tier2
def test_positive_update_external_user_roles(
        session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name):
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

    :CaseLevel: Integration
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
        session.usergroup.create({
            'usergroup.name': ldap_usergroup_name,
            'roles.resources.assigned': [foreman_role.name],
            'external_groups.name': EXTERNAL_GROUP_NAME,
            'external_groups.auth_source': auth_source_name,
        })
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.user.update(ldap_data['ldap_user_name'], {'user.auth': auth_source_name})
        with Session(
                test_name,
                ldap_data['ldap_user_name'],
                ldap_data['ldap_user_passwd'],
        ) as ldapsession:
            ldapsession.location.create({'name': location_name})
            assert ldapsession.location.search(location_name)[0]['Name'] == location_name
            current_user = ldapsession.location.read(location_name, 'current_user')['current_user']
            assert current_user == ldap_data['ldap_user_name']
        session.user.update(
            ldap_data['ldap_user_name'], {'roles.resources.assigned': [katello_role.name]})
    with Session(
            test_name,
            ldap_data['ldap_user_name'],
            ldap_data['ldap_user_passwd'],
    ) as session:
        with raises(NavigationTriesExceeded):
            ldapsession.architecture.search('')
        if bz_bug_is_open(1652938):
            try:
                session.activationkey.search('')
            except NoSuchElementException:
                session.browser.refresh()
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        current_user = session.activationkey.read(ak_name, 'current_user')['current_user']
        assert current_user == ldap_data['ldap_user_name']


@tier2
def test_positive_add_admin_role_with_org_loc(
        session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name,
        module_org):
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

    :CaseImportance: Critical
    """
    ak_name = gen_string('alpha')
    auth_source_name = 'LDAP-' + auth_source.name
    location_name = gen_string('alpha')
    with session:
        session.usergroup.create({
            'usergroup.name': ldap_usergroup_name,
            'roles.admin': True,
            'external_groups.name': EXTERNAL_GROUP_NAME,
            'external_groups.auth_source': auth_source_name,
        })
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.user.update(ldap_data['ldap_user_name'], {'user.auth': auth_source_name})
    with Session(
            test_name,
            ldap_data['ldap_user_name'],
            ldap_data['ldap_user_passwd'],
    ) as session:
        session.location.create({'name': location_name})
        assert session.location.search(location_name)[0]['Name'] == location_name
        location = session.location.read(location_name, ['current_user', 'primary'])
        assert location['current_user'] == ldap_data['ldap_user_name']
        assert location['primary']['name'] == location_name
        if bz_bug_is_open(1652938):
            try:
                session.activationkey.search('')
            except NoSuchElementException:
                session.browser.refresh()
        session.organization.select(module_org.name)
        session.activationkey.create({'name': ak_name})
        assert session.activationkey.search(ak_name)[0]['Name'] == ak_name
        ak = session.activationkey.read(ak_name, 'details.name')
        assert ak['details']['name'] == ak_name


@tier2
def test_positive_add_foreman_role_with_org_loc(
        session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name,
        module_org, module_loc):
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

    :CaseLevel: Integration
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
        session.usergroup.create({
            'usergroup.name': ldap_usergroup_name,
            'roles.resources.assigned': [foreman_role.name],
            'external_groups.name': EXTERNAL_GROUP_NAME,
            'external_groups.auth_source': auth_source_name,
        })
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.user.update(ldap_data['ldap_user_name'], {'user.auth': auth_source_name})
        session.usergroup.refresh_external_group(ldap_usergroup_name, EXTERNAL_GROUP_NAME)
        with Session(
                test_name,
                ldap_data['ldap_user_name'],
                ldap_data['ldap_user_passwd'],
        ) as ldapsession:
            with raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            if bz_bug_is_open(1652938):
                try:
                    ldapsession.hostgroup.search('')
                except NoSuchElementException:
                    ldapsession.browser.refresh()
            ldapsession.hostgroup.create({'host_group.name': name})
        hostgroup = session.hostgroup.read(name, ['organizations', 'locations'])
        assert len(hostgroup['organizations']['resources']['assigned']) == 1
        assert module_org.name in hostgroup['organizations']['resources']['assigned']
        assert len(hostgroup['locations']['resources']['assigned']) == 1
        assert module_loc.name in hostgroup['locations']['resources']['assigned']


@tier2
def test_positive_add_katello_role_with_org(
        session, ldap_data, ldap_user_name, test_name, auth_source, ldap_usergroup_name,
        module_org):
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

    :CaseLevel: Integration
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
        session.usergroup.create({
            'usergroup.name': ldap_usergroup_name,
            'roles.resources.assigned': [katello_role.name],
            'external_groups.name': EXTERNAL_GROUP_NAME,
            'external_groups.auth_source': auth_source_name,
        })
        assert session.usergroup.search(ldap_usergroup_name)[0]['Name'] == ldap_usergroup_name
        session.user.update(ldap_data['ldap_user_name'], {'user.auth': auth_source_name})
        session.usergroup.refresh_external_group(ldap_usergroup_name, EXTERNAL_GROUP_NAME)
        with Session(
                test_name,
                ldap_data['ldap_user_name'],
                ldap_data['ldap_user_passwd'],
        ) as ldapsession:
            with raises(NavigationTriesExceeded):
                ldapsession.architecture.search('')
            if bz_bug_is_open(1652938):
                try:
                    ldapsession.activationkey.search('')
                except NoSuchElementException:
                    ldapsession.browser.refresh()
            ldapsession.activationkey.create({'name': ak_name})
        # Since it's not possible to fetch assigned organization via UI directly,
        # verify AK can be found in right org, can't be found in wrong one and
        # double check via API
        if bz_bug_is_open(1652938):
            try:
                session.activationkey.search('')
            except NoSuchElementException:
                session.browser.refresh()
        results = session.activationkey.search(ak_name)
        assert results[0]['Name'] == ak_name
        session.organization.select(different_org.name)
        assert not session.activationkey.search(ak_name)
    ak = entities.ActivationKey(organization=module_org).search(
        query={'search': 'name={}'.format(ak_name)})[0].read()
    assert ak.organization.id == module_org.id
