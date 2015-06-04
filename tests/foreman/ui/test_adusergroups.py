"""Test class for Active Directory Feature"""
from robottelo.test import UITestCase
from robottelo.common.decorators import stubbed


class ADUserGroups(UITestCase):
    """Implements Active Directory feature tests in UI."""

    @stubbed()
    def test_create_ldap_auth_withad(self):
        """@Test: Create LDAP authentication with AD

        @Feature: LDAP Authentication - Active Directory - create LDAP AD

        @steps:

        1. Create a new LDAP Auth source with AD.
        2. Fill in all the fields appropriately for AD.

        @Assert: Whether creating LDAP Auth with AD is successful.

        @Status: Manual

        """

    @stubbed()
    def test_delete_ldap_auth_withad(self):
        """@Test: Delete LDAP authentication with AD

        @Feature: LDAP Authentication - Active Directory - delete LDAP AD

        @steps:

        1. Delete LDAP Auth source with AD.
        2. Fill in all the fields appropriately for AD.

        @Assert: Whether deleting LDAP Auth with AD is successful.

        @Status: Manual

        """

    @stubbed()
    def test_adusergroup_admin_role(self):
        """@Test: Associate Admin role to User Group.
        [belonging to external AD User Group.]

        @Feature: LDAP Authentication - Active Directory - associate Admin
        role

        @Steps:

        1. Create an UserGroup.
        2. Assign admin role to UserGroup.
        3. create and associate an External AD UserGroup.

        @Assert: Whether a User belonging to User Group is able to
        access all the pages.

        @Status: Manual

        """

    @stubbed()
    def test_adusergroup_foreman_role(self):
        """@Test: Associate foreman roles to User Group.
        [belonging to external AD User Group.]

        @Feature: LDAP Authentication - Active Directory - associate foreman
        roles.

        @Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. create and associate an External AD UserGroup.

        @Assert: Whether a User belonging to User Group is able to
        access foreman entities as per roles.

        @Status: Manual

        """

    @stubbed()
    def test_adusergroup_katello_role(self):
        """@Test: Associate katello roles to User Group.
        [belonging to external AD User Group.]

        @Feature: LDAP Authentication - Active Directory - associate katello
        roles

        @Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. create and associate an External AD UserGroup.

        @Assert: Whether a User belonging to User Group is able to access
        katello entities as per roles.

        @Status: Manual

        """

    @stubbed()
    def test_create_external_adusergroup_1(self):
        """@Test: Create External AD User Group as per AD group

        @Feature: LDAP Authentication - Active Directory - create

        @Steps:

        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. create an External AD UserGroup as per the UserGroup name in AD

        @Assert: Whether creation of External AD User Group is possible.

        @Status: Manual

        """

    @stubbed()
    def test_create_external_adusergroup_2(self):
        """@Test: Create another External AD User Group with same name

        @Feature: LDAP Authentication - Active Directory - create

        @Steps:

        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. create an External AD UserGroup as per the UserGroup name in AD.
        4. Repeat steps 1) and 2) and provide the same UserGroup name for
           step 3).

        @Assert: Creation of External AD User Group should not be possible with
        same name.

        @Status: Manual

        """

    @stubbed()
    def test_create_external_adusergroup_3(self):
        """@Test: Create External AD User Group with random name

        @Feature: LDAP Authentication - Active Directory - create

        @Steps:

        1. Create an UserGroup.
        2. Assign some roles to UserGroup.
        3. create an External AD UserGroup with any random name.

        @Assert: Creation of External AD User Group should not be possible with
        random name.

        @Status: Manual

        """

    @stubbed()
    def test_delete_external_adusergroup(self):
        """@Test: Delete External AD User Group

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

    @stubbed()
    def test_external_adusergroup_roles_update(self):
        """@test: Added AD UserGroup roles get pushed down to user

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

        @status: Manual

        """

    @stubbed()
    def test_external_adusergroup_roles_delete(self):
        """@test: Deleted AD UserGroup roles get pushed down to user

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

        @status: Manual

        """

    @stubbed()
    def test_external_adUserGroup_additional_user_roles(self):
        """@test: Assure that user has roles/can access feature areas for
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

        @status: Manual

        """

    @stubbed()
    def test_external_adUserGroup_user_add(self):
        """@test: New user added to UserGroup at AD side inherits roles in Sat6

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
