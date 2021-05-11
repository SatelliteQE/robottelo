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
@pytest.mark.parametrize('ldap_auth_source', ['AD', 'IPA'], indirect=True)
def test_positive_endtoend(ldap_auth_source, module_org, module_location):
    """Create/update/delete LDAP authentication with AD using names of different types

    :id: e3607c97-7c48-4cf6-b119-2bfd895d9325

    :expectedresults: Whether creating/updating/deleting LDAP Auth with AD/IPA is successful.

    :parametrized: yes

    :CaseImportance: Critical
    """
    for server_name in generate_strings_list():
        authsource = entities.AuthSourceLDAP(
            onthefly_register=True,
            account=ldap_auth_source['ldap_user_name'],
            account_password=ldap_auth_source['ldap_user_passwd'],
            base_dn=ldap_auth_source['base_dn'],
            groups_base=ldap_auth_source['group_base_dn'],
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=LDAP_ATTR['login_ad'],
            server_type=LDAP_SERVER_TYPE['API']['ad'],
            attr_mail=LDAP_ATTR['mail'],
            name=server_name,
            host=ldap_auth_source['ldap_hostname'],
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
