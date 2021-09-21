"""Test class for Ldapauthsource Feature

:Requirement: Ldapauthsource

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: LDAP

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.constants import LDAP_ATTR
from robottelo.constants import LDAP_SERVER_TYPE
from robottelo.datafactory import generate_strings_list


@pytest.mark.tier3
@pytest.mark.upgrade
@pytest.mark.parametrize('auth_source_type', ['AD', 'IPA'])
def test_positive_endtoend(auth_source_type, module_org, module_location, ad_data, ipa_data):
    """Create/update/delete LDAP authentication with AD using names of different types

    :id: e3607c97-7c48-4cf6-b119-2bfd895d9325

    :expectedresults: Whether creating/updating/deleting LDAP Auth with AD/IPA is successful.

    :parametrized: yes

    :CaseImportance: Critical
    """
    for server_name in generate_strings_list():
        if auth_source_type == 'AD':
            auth_source_data = ad_data()
            auth_type_attr = LDAP_ATTR[f'login_{auth_source_type.lower()}']
        elif auth_source_type == 'IPA':
            auth_source_data = ipa_data
            auth_source_data['ldap_user_name'] = auth_source_data['ldap_user_cn']
            auth_type_attr = LDAP_ATTR['login']
        authsource = entities.AuthSourceLDAP(
            onthefly_register=True,
            account=auth_source_data['ldap_user_cn'],
            account_password=auth_source_data['ldap_user_passwd'],
            base_dn=auth_source_data['base_dn'],
            groups_base=auth_source_data['group_base_dn'],
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=auth_type_attr,
            server_type=LDAP_SERVER_TYPE['API'][auth_source_type.lower()],
            attr_mail=LDAP_ATTR['mail'],
            name=server_name,
            host=auth_source_data['ldap_hostname'],
            tls=False,
            port='389',
            organization=[module_org],
            location=[module_location],
        ).create()

        assert authsource.name == server_name
        for new_name in generate_strings_list():
            authsource.name = new_name
            authsource = authsource.update(['name'])
            assert authsource.name == new_name
        authsource.delete()
        with pytest.raises(HTTPError):
            authsource.read()
