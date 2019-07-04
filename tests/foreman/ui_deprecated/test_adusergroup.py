"""Test class for Active Directory Feature

:Requirement: Adusergroup

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
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
    upgrade
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
        with Session(self) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            if self.user.search(self.ldap_user_name):
                self.user.delete(self.ldap_user_name)
            if self.usergroup.search(self.usergroup_name):
                self.usergroup.delete(self.usergroup_name)
        super(ActiveDirectoryUserGroupTestCase, self).tearDown()

    def check_external_user(self):
        """Check whether external user is active and reachable. That operation
        also add that user into application system for internal configuration
        procedures
        """
        strategy, value = locators['login.loggedin']
        with Session(self, self.ldap_user_name, self.ldap_user_passwd):
            self.assertIsNotNone(self.login.wait_until_element(
                (strategy, value % self.ldap_user_name)
            ))

    @tier1
    def test_positive_add_admin_role(self):
        """Associate Admin role to User Group. [belonging to external AD User
        Group.]

        :id: c3371810-1ddc-4a2c-b7e1-3b4d5db3a755

        :Steps:

            1. Create an UserGroup.
            2. Assign admin role to UserGroup.
            3. Create and associate an External AD UserGroup.

        :expectedresults: Whether a User belonging to User Group is able to
            access some of the pages.

        :CaseImportance: Critical
        """
        self.check_external_user()
        with Session(self) as session:
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
            )
        with Session(
                self, self.ldap_user_name, self.ldap_user_passwd) as session:
            session.nav.go_to_users()
            session.nav.go_to_roles()
            session.nav.go_to_content_views()

    @tier2
    def test_positive_add_foreman_role(self):
        """Associate foreman roles to User Group.
        [belonging to external AD User Group.]

        :id: c11fbf85-e144-4576-99e3-1ba111479f0f

        :Steps:

            1. Create an UserGroup.
            2. Assign some foreman roles to UserGroup.
            3. Create and associate an External AD UserGroup.

        :expectedresults: Whether a User belonging to User Group is able to
            access foreman entities as per roles.

        :CaseLevel: Integration
        """
        self.check_external_user()
        strategy, value = locators['login.loggedin']
        foreman_role = gen_string('alpha')
        location_name = gen_string('alpha')
        with Session(self) as session:
            make_role(session, name=foreman_role)
            self.role.add_permission(
                foreman_role,
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
            )
        with Session(
            self,
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

        :id: aa5e3bf4-cb42-43a4-93ea-a2eea54b847a

        :Steps:

            1. Create an UserGroup.
            2. Assign some foreman roles to UserGroup.
            3. Create and associate an External AD UserGroup.

        :expectedresults: Whether a User belonging to User Group is able to
            access katello entities as per roles.

        :CaseLevel: Integration
        """
        self.check_external_user()
        katello_role = gen_string('alpha')
        org_name = gen_string('alpha')
        with Session(self) as session:
            make_role(session, name=katello_role)
            self.role.add_permission(
                katello_role,
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
            )
        with Session(
                self,
                self.ldap_user_name,
                self.ldap_user_passwd
        ) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    @tier1
    def test_positive_create_external(self):
        """Create External AD User Group as per AD group

        :id: b5e64316-55b9-4480-8701-308e91be9344

        :Steps:

            1. Create an UserGroup.
            2. Assign some roles to UserGroup.
            3. Create an External AD UserGroup as per the UserGroup name in AD

        :expectedresults: Whether creation of External AD User Group is
            possible.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: 8f2cde96-644a-4729-880a-65a22c7e7262

        :Steps:

            1. Create an UserGroup.
            2. Assign External AD UserGroup as per the UserGroup name in AD.
            3. Repeat steps 1) and 2), but provide the same external UserGroup
               name

        :expectedresults: Creation of User Group should not be possible with
            same External AD User Group name.

        :CaseImportance: Critical
        """
        new_usergroup_name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 2fd12301-9a35-49f1-9723-2b74551414c2

        :Steps:

            1. Create an UserGroup.
            2. Assign some roles to UserGroup.
            3. Create an External AD UserGroup with any random name.

        :expectedresults: Creation of External AD User Group should not be
            possible with random name.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: 364e9ddc-4ab7-46a9-b52c-8159aab7f811

        :Steps:

            1. Create an UserGroup.
            2. Assign some roles to UserGroup.
            3. Create an External AD UserGroup as per the UserGroup name in AD.
            4. Delete the External AD UserGroup.
               Note:- Deletion as of sat6.1 is possible only via CLI and not
               via UI.

        :expectedresults: Deletion of External AD User Group should be possible
            and the user should not be able to perform the roles that were
            assigned to it at the UserGroup level.

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @skip_if_bug_open('bugzilla', '1221971')
    @upgrade
    @tier2
    def test_positive_update_external_roles(self):
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
        self.check_external_user()
        foreman_role = gen_string('alpha')
        katello_role = gen_string('alpha')
        org_name = gen_string('alpha')
        loc_name = gen_string('alpha')
        with Session(self) as session:
            make_role(session, name=foreman_role)
            self.role.add_permission(
                foreman_role,
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
            )
        with Session(
            self,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
        with Session(self) as session:
            make_role(session, name=katello_role)
            self.role.add_permission(
                katello_role,
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
            self,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    @tier2
    @upgrade
    def test_positive_delete_external_roles(self):
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
        self.check_external_user()
        foreman_role = gen_string('alpha')
        with Session(self) as session:
            make_role(session, name=foreman_role)
            self.role.add_permission(
                foreman_role,
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
            )
        with Session(
            self, self.ldap_user_name, self.ldap_user_passwd
        ) as session:
            session.nav.go_to_loc()
        with Session(self):
            self.usergroup.update(
                self.usergroup_name, roles=[foreman_role], entity_select=False)
        with Session(
            self,
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
        self.check_external_user()
        foreman_role = gen_string('alpha')
        katello_role = gen_string('alpha')
        org_name = gen_string('alpha')
        loc_name = gen_string('alpha')
        with Session(self) as session:
            make_role(session, name=foreman_role)
            self.role.add_permission(
                foreman_role,
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
            )
        with Session(
            self,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
        with Session(self) as session:
            make_role(session, name=katello_role)
            self.role.add_permission(
                katello_role,
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
            self,
            self.ldap_user_name,
            self.ldap_user_passwd,
        ) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    @stubbed()
    @tier2
    def test_positive_add_external_user(self):
        """New user added to UserGroup at AD side inherits roles in Sat6

        :id: da41d197-85d5-4405-98ec-30c1d69f4c93

        :setup: UserGroup with specified roles.

        :steps:
            1. Create an UserGroup.
            2. Assign some roles to UserGroup.
            3. Create an External AD UserGroup as per the UserGroup name in AD.
            4. On AD server side, assign a new user to a UserGroup.
            5. Login to sat6 with the above new AD user and attempt to access
               the functional areas assigned to the user.

        :expectedresults: User can access feature areas as defined by roles in
            the UserGroup of which he is a part.

        :caseautomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_add_admin_role_with_org_loc(self):
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

    @stubbed()
    @tier2
    def test_positive_add_foreman_role_with_org_loc(self):
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

    @stubbed()
    @tier2
    def test_positive_add_katello_role_with_org_loc(self):
        """Associate katello roles to User Group with org and loc set.
        [belonging to external AD User Group.]

        :id: a2ebd4de-eb0a-47da-81e8-00942eedcbf6

        :setup: LDAP Auth Source should be created with Org and Location
                Associated.

        :Steps:
            1. Create an UserGroup.
            2. Assign some foreman roles to UserGroup.
            3. Create and associate an External AD UserGroup.

        :expectedresults: Whether a User belonging to User Group is able to
            access katello entities as per roles, with the associated org and
            loc in LDAP Auth source page as the context set.

        :CaseLevel: Integration
        """
