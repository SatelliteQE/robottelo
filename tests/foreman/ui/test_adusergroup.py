"""Test class for Active Directory Feature"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import (
    LDAP_SERVER_TYPE, LDAP_ATTR, PERMISSIONS, ANY_CONTEXT)
from robottelo.decorators import (
    run_in_one_thread,
    stubbed,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
    tier2,
)
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_role, make_usergroup, make_loc, make_org, set_context)
from robottelo.ui.locators import common_locators, locators, menu_locators
from robottelo.ui.session import Session
from selenium.webdriver.common.action_chains import ActionChains


@run_in_one_thread
class ActiveDirectoryUserGroupTestCase(UITestCase):
    """Implements Active Directory feature tests in UI."""

    @classmethod
    @skip_if_not_set('ldap')
    def setUpClass(cls):  # noqa
        super(ActiveDirectoryUserGroupTestCase, cls).setUpClass()
        cls.ldap_user_name = settings.ldap.username
        cls.ldap_user_passwd = settings.ldap.password
        cls.base_dn = settings.ldap.basedn
        cls.group_base_dn = settings.ldap.grpbasedn
        cls.ldap_hostname = settings.ldap.hostname
        cls.usergroup_name = gen_string('alpha')

        authsource_attrs = entities.AuthSourceLDAP(
            onthefly_register=True,
            account=cls.ldap_user_name,
            account_password=cls.ldap_user_passwd,
            base_dn=cls.base_dn,
            groups_base=cls.group_base_dn,
            attr_firstname=LDAP_ATTR['firstname'],
            attr_lastname=LDAP_ATTR['surname'],
            attr_login=LDAP_ATTR['login_ad'],
            server_type=LDAP_SERVER_TYPE['API']['ad'],
            attr_mail=LDAP_ATTR['mail'],
            name=gen_string('alpha'),
            host=cls.ldap_hostname,
            tls=False,
            port='389',
        ).create()
        cls.ldap_server_name = authsource_attrs.name

    def tearDown(self):
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            if self.user.search(self.ldap_user_name):
                self.user.delete(self.ldap_user_name)
            if self.usergroup.search(self.usergroup_name):
                self.usergroup.delete(self.usergroup_name, True)
        super(ActiveDirectoryUserGroupTestCase, self).tearDown()

    def check_external_user(self):
        """Check whether external user is active and reachable. That operation
        also add that user into application system for internal configuration
        procedures
        """
        strategy, value = locators['login.loggedin']
        with Session(
                self.browser, self.ldap_user_name, self.ldap_user_passwd):
            self.assertIsNotNone(self.login.wait_until_element(
                (strategy, value % self.ldap_user_name)
            ))

    @tier1
    def test_positive_add_admin_role(self):
        """Associate Admin role to User Group.
        [belonging to external AD User Group.]

        @Feature: LDAP Authentication - Active Directory - associate Admin
        role

        @Steps:

        1. Create an UserGroup.
        2. Assign admin role to UserGroup.
        3. Create and associate an External AD UserGroup.

        @Assert: Whether a User belonging to User Group is able to access some
        of the pages.
        """
        self.check_external_user()
        with Session(self.browser) as session:
            make_usergroup(
                session,
                name=self.usergroup_name,
                roles=['admin'],
                ext_usergrp='foobargroup',
                ext_authsourceid='LDAP-' + self.ldap_server_name,
            )
            self.assertIsNotNone(self.usergroup.search(self.usergroup_name))
            set_context(session, org=ANY_CONTEXT['org'])
            self.user.update(
                username=self.ldap_user_name,
                authorized_by='LDAP-' + self.ldap_server_name,
                password=self.ldap_user_passwd,
            )
        with Session(
            self.browser,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ):
            session.nav.go_to_users()
            session.nav.go_to_roles()
            session.nav.go_to_content_views()

    @tier2
    def test_positive_add_foreman_role(self):
        """Associate foreman roles to User Group.
        [belonging to external AD User Group.]

        @Feature: LDAP Authentication - Active Directory - associate foreman
        roles.

        @Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. Create and associate an External AD UserGroup.

        @Assert: Whether a User belonging to User Group is able to access
        foreman entities as per roles.
        """
        self.check_external_user()
        strategy, value = locators['login.loggedin']
        foreman_role = gen_string('alpha')
        location_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(session, name=foreman_role)
            self.role.update(
                foreman_role,
                add_permission=True,
                permission_list=PERMISSIONS['Location'],
                resource_type='Location',
            )
            make_usergroup(
                session,
                name=self.usergroup_name,
                roles=[foreman_role],
                ext_usergrp='foobargroup',
                ext_authsourceid="LDAP-" + self.ldap_server_name,
            )
            self.assertIsNotNone(self.usergroup.search(self.usergroup_name))
            set_context(session, org=ANY_CONTEXT['org'])
            self.user.update(
                username=self.ldap_user_name,
                authorized_by='LDAP-' + self.ldap_server_name,
                password=self.ldap_user_passwd,
            )
        with Session(
            self.browser,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            self.assertIsNotNone(self.login.wait_until_element(
                (strategy, value % self.ldap_user_name)
            ))
            make_loc(session, name=location_name)
            self.assertIsNotNone(self.location.search(location_name))

    @tier2
    def test_positive_add_katello_role(self):
        """Associate katello roles to User Group.
        [belonging to external AD User Group.]

        @Feature: LDAP Authentication - Active Directory - associate katello
        roles

        @Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. Create and associate an External AD UserGroup.

        @Assert: Whether a User belonging to User Group is able to access
        katello entities as per roles.
        """
        self.check_external_user()
        katello_role = gen_string('alpha')
        org_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(session, name=katello_role)
            self.role.update(
                katello_role,
                add_permission=True,
                permission_list=PERMISSIONS['Organization'],
                resource_type='Organization',
            )
            make_usergroup(
                session,
                name=self.usergroup_name,
                roles=[katello_role],
                ext_usergrp='foobargroup',
                ext_authsourceid='LDAP-' + self.ldap_server_name,
            )
            self.assertIsNotNone(self.usergroup.search(self.usergroup_name))
            set_context(session, org=ANY_CONTEXT['org'])
            self.user.update(
                username=self.ldap_user_name,
                authorized_by='LDAP-' + self.ldap_server_name,
                password=self.ldap_user_passwd,
            )
        with Session(
                self.browser,
                self.ldap_user_name,
                self.ldap_user_passwd
        ) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    @tier1
    def test_positive_create_external(self):
        """Create External AD User Group as per AD group

        @Feature: LDAP Authentication - Active Directory - create

        @Steps:

        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup as per the UserGroup name in AD

        @Assert: Whether creation of External AD User Group is possible.
        """
        with Session(self.browser) as session:
            make_usergroup(
                session,
                name=self.usergroup_name,
                roles=['admin'],
                ext_usergrp='foobargroup',
                ext_authsourceid='LDAP-' + self.ldap_server_name,
            )
            self.assertIsNotNone(self.usergroup.search(self.usergroup_name))

    @tier1
    def test_negative_create_external_with_same_name(self):
        """Attempt to create two User Groups with same External AD User Group
        name

        @Feature: LDAP Authentication - Active Directory - create

        @Steps:

        1. Create an UserGroup.
        2. Assign External AD UserGroup as per the UserGroup name in AD.
        3. Repeat steps 1) and 2), but provide the same external UserGroup name

        @Assert: Creation of User Group should not be possible with same
        External AD User Group name.
        """
        new_usergroup_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_usergroup(
                session,
                name=self.usergroup_name,
                roles=['admin'],
                ext_usergrp='foobargroup',
                ext_authsourceid='LDAP-' + self.ldap_server_name,
            )
            self.assertIsNotNone(self.usergroup.search(self.usergroup_name))
            make_usergroup(
                session,
                name=new_usergroup_name,
                roles=['admin'],
                ext_usergrp='foobargroup',
                ext_authsourceid='LDAP-' + self.ldap_server_name,
            )
            self.assertIsNone(self.usergroup.search(new_usergroup_name))

    @tier1
    def test_negative_create_external_with_invalid_name(self):
        """Create External AD User Group with random name

        @Feature: LDAP Authentication - Active Directory - create

        @Steps:

        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup with any random name.

        @Assert: Creation of External AD User Group should not be possible with
        random name.
        """
        with Session(self.browser) as session:
            make_usergroup(
                session,
                name=self.usergroup_name,
                roles=['admin'],
                ext_usergrp=gen_string('alpha'),
                ext_authsourceid='LDAP-' + self.ldap_server_name,
            )
            self.assertIsNotNone(self.usergroup.wait_until_element(
                common_locators['haserror']
            ))
            self.assertIsNone(self.usergroup.search(self.usergroup_name))

    @stubbed()
    @tier2
    def test_positive_delete_external(self):
        """Delete External AD User Group

        @Feature: LDAP Authentication - Active Directory - delete

        @Steps:

        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup as per the UserGroup name in AD.
        4. Delete the External AD UserGroup.

        Note:- Deletion as of sat6.1 is possible only via CLI and not via UI.

        @Assert: Deletion of External AD User Group should be possible and the
        user should not be able to perform the roles that were assigned to it
        at the UserGroup level.

        @Status: Manual
        """

    @skip_if_bug_open('bugzilla', '1221971')
    @tier2
    def test_positive_update_external_roles(self):
        """Added AD UserGroup roles get pushed down to user

        @feature: LDAP Authentication - Active directory - update

        @setup: assign additional roles to the UserGroup

        @steps:
        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup as per the UserGroup name in AD.
        4. Login to sat6 with the AD user.
        5. Assign additional roles to the UserGroup.
        6. Login to sat6 with LDAP user that is part of aforementioned
        UserGroup.

        @assert: User has access to all NEW functional areas that are assigned
        to aforementioned UserGroup.
        """
        self.check_external_user()
        foreman_role = gen_string('alpha')
        katello_role = gen_string('alpha')
        org_name = gen_string('alpha')
        loc_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(session, name=foreman_role)
            self.role.update(
                foreman_role,
                add_permission=True,
                permission_list=PERMISSIONS['Location'],
                resource_type='Location',
            )
            make_usergroup(
                session,
                name=self.usergroup_name,
                roles=[foreman_role],
                ext_usergrp='foobargroup',
                ext_authsourceid='LDAP-' + self.ldap_server_name,
            )
            self.assertIsNotNone(self.usergroup.search(self.usergroup_name))
            set_context(session, org=ANY_CONTEXT['org'])
            self.user.update(
                username=self.ldap_user_name,
                authorized_by='LDAP-' + self.ldap_server_name,
                password=self.ldap_user_passwd,
            )
        with Session(
            self.browser,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
        with Session(self.browser) as session:
            make_role(session, name=katello_role)
            self.role.update(
                katello_role,
                add_permission=True,
                permission_list=PERMISSIONS['Organization'],
                resource_type='Organization',
            )
            self.usergroup.update(
                self.usergroup_name,
                new_roles=[katello_role],
                entity_select=True,
            )
            self.usergroup.refresh_ext_group(
                self.usergroup_name, 'foobargroup')
            self.assertIsNotNone(self.usergroup.wait_until_element(
                common_locators['notif.success']))
        with Session(
            self.browser,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    @tier2
    def test_positive_delete_external_roles(self):
        """Deleted AD UserGroup roles get pushed down to user

        @feature: LDAP Authentication - Active directory - update

        @setup: delete roles from an AD UserGroup

        @steps:
        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup as per the UserGroup name in AD.
        4. Login to sat6 with the AD user.
        5. Unassign some of the existing roles of the UserGroup.
        6. Login to sat6 with LDAP user that is part of aforementioned
        UserGroup.

        @assert: User no longer has access to all deleted functional areas
        that were assigned to aforementioned UserGroup.
        """
        self.check_external_user()
        foreman_role = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(session, name=foreman_role)
            self.role.update(
                foreman_role,
                add_permission=True,
                permission_list=PERMISSIONS['Location'],
                resource_type='Location',
            )
            make_usergroup(
                session,
                name=self.usergroup_name,
                roles=[foreman_role],
                ext_usergrp='foobargroup',
                ext_authsourceid='LDAP-' + self.ldap_server_name,
            )
            self.assertIsNotNone(self.usergroup.search(self.usergroup_name))
            set_context(session, org=ANY_CONTEXT['org'])
            self.user.update(
                username=self.ldap_user_name,
                authorized_by='LDAP-' + self.ldap_server_name,
                password=self.ldap_user_passwd,
            )
        with Session(
            self.browser, self.ldap_user_name, self.ldap_user_passwd
        ) as session:
            session.nav.go_to_loc()
        with Session(self.browser):
            self.usergroup.update(
                self.usergroup_name, roles=[foreman_role], entity_select=False)
        with Session(
            self.browser,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            ActionChains(
                self.browser
            ).move_to_element(session.nav.wait_until_element(
                menu_locators['menu.any_context']
            )).perform()
            self.assertIsNone(session.nav.wait_until_element(
                menu_locators['loc.manage_loc']
            ))

    @tier2
    def test_positive_update_external_user_roles(self):
        """Assure that user has roles/can access feature areas for
        additional roles assigned outside any roles assigned by his group

        @feature: LDAP Authentication - Active directory - update

        @setup: Assign roles to UserGroup and configure external
        UserGroup subsequently assign specified roles to the user(s).
        roles that are not part of the larger UserGroup

        @steps:
        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup as per the UserGroup name in AD.
        4. Assign some more roles to a User(which is part of external AD
        UserGroup) at the User level.
        5. Login to sat6 with the above AD user and attempt to access areas
        assigned specifically to user.

        @assert: User can access not only those feature areas in his
        UserGroup but those additional feature areas / roles assigned
        specifically to user
        """
        self.check_external_user()
        foreman_role = gen_string('alpha')
        katello_role = gen_string('alpha')
        org_name = gen_string('alpha')
        loc_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_role(session, name=foreman_role)
            self.role.update(
                foreman_role,
                add_permission=True,
                permission_list=PERMISSIONS['Location'],
                resource_type='Location',
            )
            make_usergroup(
                session,
                name=self.usergroup_name,
                roles=[foreman_role],
                ext_usergrp='foobargroup',
                ext_authsourceid='LDAP-' + self.ldap_server_name,
            )
            self.assertIsNotNone(self.usergroup.search(self.usergroup_name))
            set_context(session, org=ANY_CONTEXT['org'])
            self.user.update(
                username=self.ldap_user_name,
                authorized_by='LDAP-' + self.ldap_server_name,
                password=self.ldap_user_passwd,
            )
        with Session(
            self.browser,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
        with Session(self.browser) as session:
            make_role(session, name=katello_role)
            self.role.update(
                katello_role,
                add_permission=True,
                permission_list=PERMISSIONS['Organization'],
                resource_type='Organization',
            )
            set_context(session, org=ANY_CONTEXT['org'])
            self.user.update(
                self.ldap_user_name,
                new_roles=[katello_role],
                select=True,
            )
        with Session(
            self.browser,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    @stubbed()
    @tier2
    def test_positive_add_external_user(self):
        """New user added to UserGroup at AD side inherits roles in Sat6

        @feature: LDAP Authentication - Active directory - update

        @setup: UserGroup with specified roles.

        @steps:
        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. Create an External AD UserGroup as per the UserGroup name in AD.
        4. On AD server side, assign a new user to a UserGroup.
        5. Login to sat6 with the above new AD user and attempt to access the
        functional areas assigned to the user.

        @assert: User can access feature areas as defined by roles in the
        UserGroup of which he is a part.

        @status: Manual
        """
