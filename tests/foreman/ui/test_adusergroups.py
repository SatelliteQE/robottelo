"""Test class for Active Directory Feature"""
from robottelo.test import UITestCase
from robottelo.common.decorators import stubbed


class ADUserGroups(UITestCase):
    """Implements Active Directory feature tests in UI."""

    @stubbed()
    def test_create_ldap_auth_withAD(self):
        """@Test: Create LDAP authentication with AD

        @Feature: Active Directory - create LDAP AD

        @steps:

        1. Create a new LDAP Auth source with AD
        2. Fill in all the fields appropriately for AD

        @Assert: Whether creating LDAP Auth with AD is successful.

        @Status: Manual

        """

    @stubbed()
    def test_delete_ldap_auth_withAD(self):
        """@Test: Delete LDAP authentication with AD

        @Feature: Active Directory - delete LDAP AD

        @steps:

        1. Delete LDAP Auth source with AD
        2. Fill in all the fields appropriately for AD

        @Assert: Whether deleting LDAP Auth with AD is successful.

        @Status: Manual

        """

    @stubbed()
    def test_adusergroup_admin_role(self):
        """@Test: Associate Admin role to User Group.
        [belonging to external AD User Group.]

        @Feature: Active Directory - associate Admin role

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

        @Feature: Active Directory - associate foreman roles.

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

        @Feature: Active Directory - associate katello roles

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

        @Feature: Active Directory - create

        @Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. create an External AD UserGroup as per the usergroup name in AD

        @Assert: Whether creation of External AD User Group is possible.

        @Status: Manual

        """

    @stubbed()
    def test_create_external_adusergroup_2(self):
        """@Test: Create another External AD User Group with same name

        @Feature: Active Directory - create

        @Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. create an External AD UserGroup as per the usergroup name in AD
        4. Repeat steps 1) and 2) and provide the same usergroup name for
           step 3)

        @Assert: Creation of External AD User Group should not be possible with
        same name.

        @Status: Manual

        """

    @stubbed()
    def test_create_external_adusergroup_3(self):
        """@Test: Create External AD User Group with random name

        @Feature: Active Directory - create

        @Steps:

        1. Create an UserGroup.
        2. Assign some foreman roles to UserGroup.
        3. create an External AD UserGroup with any random name.

        @Assert: Creation of External AD User Group should not be possible with
        random name.

        @Status: Manual

        """
