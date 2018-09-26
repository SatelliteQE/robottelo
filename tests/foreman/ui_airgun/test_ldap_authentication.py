"""Test class for Active Directory Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from nailgun import entities
from robottelo.config import settings
from robottelo.constants import LDAP_ATTR, LDAP_SERVER_TYPE
from robottelo.datafactory import gen_string
from robottelo.decorators import (
    fixture,
    skip_if_not_set,
    tier2,
    upgrade,
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
        'ldap_ipa_user_passwd': settings.ipa.password_ipa,
        'ipa_base_dn': settings.ipa.basedn_ipa,
        'ipa_group_base_dn': settings.ipa.grpbasedn_ipa,
        'ldap_ipa_hostname': settings.ipa.hostname_ipa,
    }


@skip_if_not_set('ldap')
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
