"""Test for User Group related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: UsersRoles

:Team: Endeavour

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha
import pytest

from robottelo.constants import LDAP_ATTR, LDAP_SERVER_TYPE
from robottelo.utils.shared_resource import SharedResource


@pytest.fixture
def user_group_with_ldap_user_setup(ad_data, usergroup_upgrade_shared_satellite, upgrade_action):
    """Create User-group in pre_upgrade version.

    :steps:
        1. Create ldap auth pre upgrade.
        2. Login with ldap User in satellite and logout.
        3. Create external user_group viewer role and synced ldap user gets the role.

    :expectedresults: The usergroup, with ldap user as member, should be created successfully.
    """
    target_sat = usergroup_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'usergroup_upgrade_{gen_alpha()}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_loc', organization=[org]).create()
        test_data = Box(
            {
                'satellite': target_sat,
                'ad_data': ad_data,
                'user_group': None,
            }
        )
        ad_data = ad_data()
        member_group = 'foobargroup'
        LOGEDIN_MSG = "Using configured credentials for user '{0}'."
        auth_source = target_sat.api.AuthSourceLDAP(
            onthefly_register=True,
            account=f"cn={ad_data.ldap_user_name},{ad_data.base_dn}",
            account_password=ad_data.ldap_user_passwd,
            base_dn=ad_data.base_dn,
            groups_base=ad_data.group_base_dn,
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=LDAP_ATTR['login_ad'],
            server_type=LDAP_SERVER_TYPE['API']['ad'],
            attr_mail=LDAP_ATTR['mail'],
            name=f'{test_name}_auth_source',
            host=ad_data.ldap_hostname,
            tls=False,
            port='389',
            organization=[org],
            location=[location],
        ).create()
        viewer_role = target_sat.cli.Role.info({'name': 'Viewer'})
        user_group = target_sat.cli_factory.usergroup()
        target_sat.cli_factory.usergroup_external(
            {
                'auth-source-id': auth_source.id,
                'user-group-id': user_group['id'],
                'name': member_group,
            }
        )
        target_sat.cli.UserGroup.add_role({'id': user_group['id'], 'role-id': viewer_role['id']})
        user_group = target_sat.cli.UserGroup.info({'id': user_group['id']})
        result = target_sat.cli.Auth.with_user(
            username=ad_data.ldap_user_name, password=ad_data.ldap_user_passwd
        ).status()
        assert LOGEDIN_MSG.format(ad_data.ldap_user_name) in result[0]['message']
        target_sat.cli.UserGroupExternal.refresh(
            {'user-group-id': user_group['id'], 'name': member_group}
        )
        role_list = target_sat.cli.Role.with_user(
            username=ad_data.ldap_user_name, password=ad_data.ldap_user_passwd
        ).list()
        assert len(role_list) > 1
        test_data.user_group = target_sat.api.UserGroup().search(
            query={'search': f'name={user_group["name"]}'}
        )[0]
        sat_upgrade.ready()
        target_sat._session = None
        yield test_data


@pytest.mark.usergroup_upgrades
def test_verify_user_group_membership(
    user_group_with_ldap_user_setup,
):
    """After upgrade, check the LDAP user created before the upgrade still exists and its
     update functionality should work.

    :id: 7545fc6a-bd57-4403-90c8-c68a7a3b5bca

    :steps:
        1. Verify LDAP user created before upgrade is part of user group.
        2. Verify that LDAP user retains role assigned before upgrade.

    :expectedresults: After upgrade, user group and role membership should remain the same
    """
    target_sat = user_group_with_ldap_user_setup.satellite
    ad_data = user_group_with_ldap_user_setup.ad_data()
    user_group = user_group_with_ldap_user_setup.user_group
    user = target_sat.api.User().search(query={'search': f'login={ad_data["ldap_user_name"]}'})[0]
    assert user.id == user_group.read().user[0].id
    role_list = target_sat.cli.Role.with_user(
        username=ad_data['ldap_user_name'], password=ad_data['ldap_user_passwd']
    ).list()
    assert len(role_list) > 1
