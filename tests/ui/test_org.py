# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Organization UI
"""

from ddt import data, ddt
from robottelo.common.helpers import generate_name
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import redminebug
from tests.ui.baseui import BaseUI


@ddt
class Org(BaseUI):
    """
    Implements Organization tests in UI
    """

    def create_org(self, org_name=None):
        """Creates Org"""
        org_name = org_name or generate_name(8, 8)
        self.navigator.go_to_org()  # go to org page
        self.org.create(org_name)
        self.navigator.go_to_org()

    def test_create_org(self):
        """
        @Feature: Org - Positive create
        @Test: Create an org with a valid org name
        @Assert: Org is created
        """
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        select_org = self.navigator.go_to_select_org(org_name)
        self.assertIsNotNone(select_org)
        self.assertIsNotNone(
            self.org.search(org_name))

    def test_update_org(self):
        """
        @Feature: Org - Positive Update
        @Test: Update an org with a valid new org name
        @Assert: Org is updated
        """
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.org.search(org_name)
        new_name = generate_name(8, 8)
        self.org.update(org_name, new_name)
        self.assertIsNotNone(
            self.org.search(new_name))

    def test_remove_org(self):
        """
        @Feature: Org - Positive Delete
        @Test: Delete an org given a valid existing org name
        @Assert: Org is deleted
        """
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.create_org(org_name)
        self.org.remove(org_name, really=True)
        self.assertIsNone(
            self.org.search(org_name))

    # Positive Create

    @data("""DATADRIVENGOESHERE
        name is alpha, label and description are blank
        name is numeric, label and description are blank
        name is alphanumeric, label and description are blank
        name is utf-8, label and description are blank
        name is latin1, label and description are blank
        name is html, label and description are blank
        """)
    def test_positive_create_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name only
        @assert: organization is created, label is auto-generated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name and label are alpha and match, description is blank
        name and label are numeric and match, description is blank
        name and label are alphanumeric and match, description is blank
        name and label are utf-8 and match, description is blank
        name and label are latin1 and match, description is blank
        name and label are html and match, description is blank
        """)
    def test_positive_create_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid matching name and label only
        @assert: organization is created, label matches name
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name and label are alpha, description is blank
        name and label are numeric, description is blank
        name and label are alphanumeric, description is blank
        name and label are utf-8, description is blank
        name and label are latin1, description is blank
        name and label are html, description is blank
        """)
    def test_positive_create_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid unmatching name and label only
        @assert: organization is created, label does not match name
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name and description are alpha, label is blank
        name and description are numeric, label is blank
        name and description are alphanumeric, label is blank
        name and description are utf-8, label is blank
        name and description are latin1, label is blank
        name and description are html, label is blank
        """)
    def test_positive_create_4(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name and description only
        @assert: organization is created, label is auto-generated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name, label and description are alpha, name and label match
        name, label and description are numeric, name and label match
        name, label and description are alphanumeric, name and label match
        name, label and description are utf-8, name and label match
        name, label and description are latin1, name and label match
        name, label and description are html, name and label match
        """)
    def test_positive_create_5(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name, label and description
        @assert: organization is created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

        #Negative Create

    @data("""DATADRIVENGOESHERE
        label and description are alpha, update name is alpha 300 chars
        label and description are alpha, update name is numeric 300 chars
        label and description are alpha, update name is alphanumeric 300 chars
        label and description are alpha, update name is utf-8 300 chars
        label and description are alpha, update name is latin1 300 chars
        label and description are alpha, update name is html 300 chars

    """)
    def test_negative_create_0(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        too long
        @assert: organization is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        label and description are alpha, name is blank
        label and description are numeric, name is blank
        label and description are alphanumeric, name is blank
        label and description are utf-8, name is blank
        label and description are latin1, name is blank
        label and description are html, name is blank
    """)
    def test_negative_create_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        blank
        @assert: organization is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        label and description are alpha, name is whitespace
        label and description are numeric, name is whitespace
        label and description are alphanumeric, name is whitespace
        label and description are utf-8, name is whitespace
        label and description are latin1, name is whitespace
        label and description are html, name is whitespace
    """)
    def test_negative_create_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        whitespace
        @assert: organization is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name, label and description are alpha
        name, label and description are numeric
        name, label and description are alphanumeric
        name, label and description are utf-8
        name, label and description are latin1
        name, label and description are html
    """)
    def test_negative_create_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values, then create a new one
        with same values.
        @assert: organization is not created
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    # Positive Delete

    @data("""DATADRIVENGOESHERE
        name, label and description are alpha
        name, label and description are numeric
        name, label and description are alphanumeric
        name, label and description are utf-8
        name, label and description are latin1
        name, label and description are html
    """)
    def test_positive_delete_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then delete it
        @assert: organization is deleted
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    # Negative Delete

    # Positive Update

    @data("""DATADRIVENGOESHERE
        update name is alpha
        update name is numeric
        update name is alphanumeric
        update name is utf-8
        update name is latin1
        update name is html
    """)
    def test_positive_update_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update its name
        @assert: organization name is updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update label is alpha
        update label is numeric
        update label is alphanumeric
        update label is utf-8
        update label is latin1
        update label is html
    """)
    def test_positive_update_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update its label
        @assert: organization label is updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update description is alpha
        update description is numeric
        update description is alphanumeric
        update description is utf-8
        update description is latin1
        update description is html
    """)
    def test_positive_update_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update its
        description
        @assert: organization description is updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update name, label and description are alpha
        update name, label and description are numeric
        update name, label and description are alphanumeric
        update name, label and description are utf-8
        update name, label and description are latin1
        update name, label and description are html
    """)
    def test_positive_update_4(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then update all values
        @assert: organization name, label and description are updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    # Negative Update

    @data("""DATADRIVENGOESHERE
        update name is whitespace
        update name is alpha 300 chars long
        update name is numeric 300 chars long
        update name is alphanumeric 300 chars long
        update name is utf-8 300 chars long
        update name is latin1 300 chars long
        update name is html 300 chars long
    """)
    def test_negative_update_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then fail to update
        its name
        @assert: organization name is not updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update label is whitespace
        update label is alpha 300 chars long
        update label is numeric 300 chars long
        update label is alphanumeric 300 chars long
        update label is utf-8 300 chars long
        update label is latin1 300 chars long
        update label is html 300 chars long
    """)
    def test_negative_update_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then fail to update
        its label
        @assert: organization label is not updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        update description is alpha 300 chars long
        update description is numeric 300 chars long
        update description is alphanumeric 300 chars long
        update description is utf-8 300 chars long
        update description is latin1 300 chars long
        update description is html 300 chars long
    """)
    def test_negative_update_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid values then fail to update
        its description
        @assert: organization description is not updated
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    #Miscelaneous

    @data("""DATADRIVENGOESHERE
        name, label and description are is alpha
        name, label and description are is numeric
        name, label and description are is alphanumeric
        name, label and description are is utf-8
        name, label and description are is latin1
        name, label and description are is html
    """)
    def test_list_key_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization and list it
        @assert: organization is displayed/listed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name, label and description are is alpha
        name, label and description are is numeric
        name, label and description are is alphanumeric
        name, label and description are is utf-8
        name, label and description are is latin1
        name, label and description are is html
    """)
    def test_search_key_1(self, test_data):
        """
        @feature: Organizations
        @test: Create organization and search/find it
        @assert: organization can be found
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        name, label and description are is alpha
        name, label and description are is numeric
        name, label and description are is alphanumeric
        name, label and description are is utf-8
        name, label and description are is latin1
        name, label and description are is html
    """)
    def test_info_key_1(self, test_data):
        """
        @feature: Organizations
        @test: Create single organization and get its info
        @assert: specific information for organization matches the
        creation values
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    # Associations

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_remove_domain_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        name and domain name
        @assert: the domain is removed from the organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_remove_domain_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        ID and domain name
        @assert: the domain is removed from the organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_remove_domain_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        name and domain ID
        @assert: the domain is removed from the organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_remove_domain_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        ID and domain ID
        @assert: the domain is removed from the organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @redminebug('4294')
    @redminebug('4295')
    @redminebug('4296')
    @data("""DATADRIVENGOESHERE
        user name is alpha
        user name is numeric
        user name is alpha_numeric
        user name is utf-8
        user name is latin1
        user name is html
    """)
    def test_remove_user_1(self, test_data):
        """
        @feature: Organizations
        @test: Create different types of users then add/remove user
        by using the organization ID
        by using the organization ID
        @assert: User is added and then removed from organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @redminebug('4294')
    @redminebug('4295')
    @redminebug('4296')
    @data("""DATADRIVENGOESHERE
        user name is alpha
        user name is numeric
        user name is alpha_numeric
        user name is utf-8
        user name is latin1
        user name is html
    """)
    def test_remove_user_2(self, test_data):
        """
        @feature: Organizations
        @test: Create different types of users then add/remove user
        by using the organization name
        @assert: The user is added then removed from the organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @redminebug('4294')
    @redminebug('4295')
    @redminebug('4296')
    @data("""DATADRIVENGOESHERE
        user name is alpha and admin
        user name is numeric and admin
        user name is alpha_numeric and admin
        user name is utf-8 and admin
        user name is latin1 and admin
        user name is html and admin
    """)
    def test_remove_user_3(self, test_data):
        """
        @feature: Organizations
        @test: Create admin users then add user and remove it
        by using the organization name
        @assert: The user is added then removed from the organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_remove_hostgroup_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        name and hostgroup name
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_remove_hostgroup_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        ID and hostgroup name
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_remove_hostgroup_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        name and hostgroup ID
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_remove_hostgroup_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        ID and hostgroup ID
        @assert: hostgroup is added to organization then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_add_smartproxy_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_add_smartproxy_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy name
        @assert: smartproxy is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_add_smartproxy_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization name and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_add_smartproxy_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a smart proxy by using organization ID and smartproxy ID
        @assert: smartproxy is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_add_subnet_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a subnet by using organization name and subnet name
        @assert: subnet is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_add_subnet_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a subnet by using organization ID and subnet name
        @assert: subnet is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_add_subnet_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a subnet by using organization name and subnet ID
        @assert: subnet is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_add_subnet_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a subnet by using organization ID and subnet ID
        @assert: subnet is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @redminebug('4219')
    @redminebug('4294')
    @redminebug('4295')
    @data("""DATADRIVENGOESHERE
        domain name is alpha
        domain name is numeric
        domain name is alph_numeric
        domain name is utf-8
        domain name is latin1
        domain name is html
    """)
    def test_add_domain_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a domain to an organization
        @assert: Domain is added to organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        user name is alpha
        user name is numeric
        user name is alpha_numeric
        user name is utf-8
        user name is latin1
        user name is html
    """)
    def test_add_user_1(self, test_data):
        """
        @feature: Organizations
        @test: Create different types of users then add user
        by using the organization ID
        @assert: User is added to organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        user name is alpha
        user name is numeric
        user name is alpha_numeric
        user name is utf-8
        user name is latin1
        user name is html
    """)
    def test_add_user_2(self, test_data):
        """
        @feature: Organizations
        @test: Create different types of users then add user
        by using the organization name
        @assert: User is added to organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        user name is alpha and an admin
        user name is numeric and an admin
        user name is alpha_numeric and an admin
        user name is utf-8 and an admin
        user name is latin1 and an admin
        user name is html and an admin
    """)
    def test_add_user_3(self, test_data):
        """
        @feature: Organizations
        @test: Create admin users then add user by using the organization name
        @assert: User is added to organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_add_hostgroup_1(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        name and hostgroup name
        @assert: hostgroup is added to organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_add_hostgroup_2(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        ID and hostgroup name
        @assert: hostgroup is added to organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_add_hostgroup_3(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        name and hostgroup ID
        @assert: hostgroup is added to organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        hostgroup name is alpha
        hostgroup name is numeric
        hostgroup name is alpha_numeric
        hostgroup name is utf-8
        hostgroup name is latin1
        hostgroup name is html
    """)
    def test_add_hostgroup_4(self, test_data):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        ID and hostgroup ID
        @assert: hostgroup is added to organization
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_remove_computeresource_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        name and computeresource name
        @assert: computeresource is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_remove_computeresource_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        ID and computeresource name
        @assert: computeresource is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_remove_computeresource_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        name and computeresource ID
        @assert: computeresource is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_remove_computeresource_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        ID and computeresource ID
        @assert: computeresource is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
        """)
    def test_remove_medium_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove medium by using organization name and medium name
        @assert: medium is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
        """)
    def test_remove_medium_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove medium by using organization ID and medium name
        @assert: medium is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
        """)
    def test_remove_medium_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove medium by using organization name and medium ID
        @assert: medium is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
        """)
    def test_remove_medium_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove medium by using organization ID and medium ID
        @assert: medium is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_remove_configtemplate_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove config template
        @assert: configtemplate is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_remove_environment_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove environment by using organization name and
        evironment name
        @assert: environment is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_remove_environment_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove environment by using organization ID and
        evironment name
        @assert: environment is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_remove_environment_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove environment by using organization name and
        evironment ID
        @assert: environment is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_remove_environment_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove environment by using organization ID and
        evironment ID
        @assert: environment is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_remove_smartproxy_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_remove_smartproxy_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy name
        @assert: smartproxy is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_remove_smartproxy_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization name and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_remove_smartproxy_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove smartproxy by using organization ID and smartproxy ID
        @assert: smartproxy is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_add_computeresource_1(self, test_data):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        name and computeresource name
        @assert: computeresource is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_add_computeresource_2(self, test_data):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        ID and computeresource name
        @assert: computeresource is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_add_computeresource_3(self, test_data):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        name and computeresource ID
        @assert: computeresource is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        computeresource is alpha
        computeresource is numeric
        computeresource is alpha_numeric
        computeresource is utf-8
        computeresource is latin1
        computeresource is html
    """)
    def test_add_computeresource_4(self, test_data):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        ID and computeresource ID
        @assert: computeresource is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
    """)
    def test_add_medium_1(self, test_data):
        """
        @feature: Organizations
        @test: Add medium by using the organization name and medium name
        @assert: medium is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
    """)
    def test_add_medium_2(self, test_data):
        """
        @feature: Organizations
        @test: Add medium by using the organization ID and medium name
        @assert: medium is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
    """)
    def test_add_medium_3(self, test_data):
        """
        @feature: Organizations
        @test: Add medium by using the organization name and medium ID
        @assert: medium is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        medium name is alpha
        medium name is numeric
        medium name is alpha_numeric
        medium name is utf-8
        medium name is latin1
        medium name is html
    """)
    def test_add_medium_4(self, test_data):
        """
        @feature: Organizations
        @test: Add medium by using the organization ID and medium ID
        @assert: medium is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_add_configtemplate_1(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization name and
        configtemplate name
        @assert: configtemplate is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_add_configtemplate_2(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization ID and
        configtemplate name
        @assert: configtemplate is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_add_configtemplate_3(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization name and
        configtemplate ID
        @assert: configtemplate is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        configtemplate name is alpha
        configtemplate name is numeric
        configtemplate name is alpha_numeric
        configtemplate name is utf-8
        configtemplate name is latin1
        configtemplate name  is html
    """)
    def test_add_configtemplate_4(self, test_data):
        """
        @feature: Organizations
        @test: Add config template by using organization ID and
        configtemplate ID
        @assert: configtemplate is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_add_environment_1(self, test_data):
        """
        @feature: Organizations
        @test: Add environment by using organization name and evironment name
        @assert: environment is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_add_environment_2(self, test_data):
        """
        @feature: Organizations
        @test: Add environment by using organization ID and evironment name
        @assert: environment is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_add_environment_3(self, test_data):
        """
        @feature: Organizations
        @test: Add environment by using organization name and evironment ID
        @assert: environment is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        environment name is alpha
        environment name is numeric
        environment name is alpha_numeric
        environment name is utf-8
        environment name is latin1
        environment name  is html
    """)
    def test_add_environment_4(self, test_data):
        """
        @feature: Organizations
        @test: Add environment by using organization ID and evironment ID
        @assert: environment is added
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_remove_subnet_1(self, test_data):
        """
        @feature: Organizations
        @test: Remove subnet by using organization name and subnet name
        @assert: subnet is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_remove_subnet_2(self, test_data):
        """
        @feature: Organizations
        @test: Remove subnet by using organization ID and subnet name
        @assert: subnet is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_remove_subnet_3(self, test_data):
        """
        @feature: Organizations
        @test: Remove subnet by using organization name and subnet ID
        @assert: subnet is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)

    @data("""DATADRIVENGOESHERE
        subnet name is alpha
        subnet name is numeric
        subnet name is alpha_numeric
        subnet name is utf-8
        subnet name is latin1
        subnet name  is html
    """)
    def test_remove_subnet_4(self, test_data):
        """
        @feature: Organizations
        @test: Remove subnet by using organization ID and subnet ID
        @assert: subnet is added then removed
        @status: manual
        """

        self.fail(NOT_IMPLEMENTED)
