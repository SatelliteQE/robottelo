# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Organization CLI
"""

from ddt import data, ddt
from robottelo.cli.factory import (
    make_domain, make_environment, make_hostgroup, make_medium, make_org,
    make_proxy, make_subnet, make_template, make_user)
from robottelo.cli.org import Org
from tests.cli.basecli import BaseCLI
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import (bzbug, redminebug)


@ddt
class TestOrg(BaseCLI):
    """
    Tests for Organizations via Hammer CLI

    Known Issues:
    * http://projects.theforeman.org/issues/4219 # Affects UI
    * http://projects.theforeman.org/issues/4242
    * http://projects.theforeman.org/issues/4294
    * http://projects.theforeman.org/issues/4295
    * http://projects.theforeman.org/issues/4296
    """

    @bzbug('1062306')
    def test_create_org(self):
        """
        @Feature: Org - Positive Create
        @Test: Check if Org can be created
        @Assert: Org is created
        """
        result = make_org()
        org_info = Org().info({'name': result['name']})
        #TODO: Assert fails currently for an existing bug
        self.assertEqual(result['name'], org_info.stdout['name'])

    @bzbug('1061658')
    def test_delete_org(self):
        """
        @Feature: Org - Positive Delete
        @Test: Check if Org can be deleted
        @Assert: Org is deleted
        """
        result = make_org()
        return_value = Org().delete({'name': result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Delete Org - retcode")
        self.assertFalse(return_value.stderr)

    def test_list_org(self):
        """
        @Feature: Org - List
        @Test: Check if Org can be listed
        @Assert: Org is listed
        """
        return_value = Org().list()
        self.assertTrue(return_value.return_code == 0,
                        "List Org - retcode")
        self.assertFalse(return_value.stderr)

    def test_info_org(self):
        """
        @Feature: Org - Info
        @Test: Check if Org info can be retrieved
        @Assert: Org info is retreived
        """
        result = make_org()
        return_value = Org().info({'name': result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Info Org - retcode")
        self.assertFalse(return_value.stderr)

    def test_add_subnet(self):
        """
        @Feature: Org - Subnet
        @Test: Check if a subnet can be added to an Org
        @Assert: Subnet is added to the org
        """
        org_result = make_org()
        subnet_result = make_subnet()
        return_value = Org().add_subnet(
            {'name': org_result['name'], 'subnet': subnet_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Add subnet - retcode")
        self.assertFalse(return_value.stderr)

    def test_remove_subnet(self):
        """
        @Feature: Org - Subnet
        @Test: Check if a subnet can be removed from an Org
        @Assert: Subnet is removed from the org
        """
        org_result = make_org()
        subnet_result = make_subnet()
        Org().add_subnet(
            {'name': org_result['name'], 'subnet': subnet_result['name']})
        return_value = Org().remove_subnet(
            {'name': org_result['name'], 'subnet': subnet_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Remove Subnet - retcode")
        self.assertFalse(return_value.stderr)

    def test_add_domain(self):
        """
        @Feature: Org - Domain
        @Test: Check if a domain can be added to an Org
        @Assert: Domain is added to the org
        """
        org_result = make_org()
        domain_result = make_domain()
        return_value = Org().add_domain(
            {'name': org_result['name'], 'domain': domain_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Add Domain - retcode")
        self.assertFalse(return_value.stderr)

    def test_remove_domain(self):
        """
        @Feature: Org - Domain
        @Test: Check if a Domain can be removed from an Org
        @Assert: Domain is removed from the org
        """
        org_result = make_org()
        domain_result = make_domain()
        Org().add_domain(
            {'name': org_result['name'], 'domain': domain_result['name']})
        return_value = Org().remove_domain(
            {'name': org_result['name'], 'domain': domain_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Remove Domain - retcode")
        self.assertFalse(return_value.stderr)

    def test_add_user(self):
        """
        @Feature: Org - User
        @Test: Check if a User can be added to an Org
        @Assert: User is added to the org
        """
        org_result = make_org()
        user_result = make_user()
        return_value = Org().add_user(
            {'name': org_result['name'], 'user-id': user_result['login']})
        self.assertTrue(return_value.return_code == 0,
                        "Add User - retcode")
        self.assertFalse(return_value.stderr)

    def test_remove_user(self):
        """
        @Feature: Org - User
        @Test: Check if a User can be removed from an Org
        @Assert: User is removed from the org
        """
        org_result = make_org()
        user_result = make_user()
        Org().add_user(
            {'name': org_result['name'], 'user-id': user_result['login']})
        return_value = Org().remove_user(
            {'name': org_result['name'], 'user-id': user_result['login']})
        self.assertTrue(return_value.return_code == 0,
                        "Remove User - retcode")
        self.assertFalse(return_value.stderr)

    def test_add_hostgroup(self):
        """
        @Feature: Org - Hostrgroup
        @Test: Check if a hostgroup can be added to an Org
        @Assert: Hostgroup is added to the org
        """
        org_result = make_org()
        hostgroup_result = make_hostgroup()
        return_value = Org().add_hostgroup({
            'name': org_result['name'],
            'hostgroup': hostgroup_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Add Hostgroup - retcode")
        self.assertFalse(return_value.stderr)

    def test_remove_hostgroup(self):
        """
        @Feature: Org - Subnet
        @Test: Check if a hostgroup can be removed from an Org
        @Assert: Hostgroup is removed from the org
        """
        org_result = make_org()
        hostgroup_result = make_hostgroup()
        Org().add_hostgroup({
            'name': org_result['name'],
            'hostgroup': hostgroup_result['name']})
        return_value = Org().remove_hostgroup({
            'name': org_result['name'],
            'hostgroup': hostgroup_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Remove Hostgroup - retcode")
        self.assertFalse(return_value.stderr)

    def test_add_computeresource(self):
        """
        @Feature: Org - Compute Resource
        @Test: Check if a Compute Resource can be added to an Org
        @Assert: Compute Resource is added to the org
        """
        #TODO: Test should be done once computeresource base class is added
        self.fail(NOT_IMPLEMENTED)

    def test_remove_computeresource(self):
        """
        @Feature: Org - ComputeResource
        @Test: Check if a ComputeResource can be removed from an Org
        @Assert: ComputeResource is removed from the org
        """
        #TODO: Test should be done once computeresource base class is added
        self.fail(NOT_IMPLEMENTED)

    def test_add_medium(self):
        """
        @Feature: Org - Medium
        @Test: Check if a Medium can be added to an Org
        @Assert: Medium is added to the org
        """
        org_result = make_org()
        medium_result = make_medium()
        return_value = Org().add_medium({
            'name': org_result['name'],
            'medium': medium_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Add Medium - retcode")
        self.assertFalse(return_value.stderr)

    def test_remove_medium(self):
        """
        @Feature: Org - Medium
        @Test: Check if a Medium can be removed from an Org
        @Assert: Medium is removed from the org
        """
        org_result = make_org()
        medium_result = make_medium()
        Org().add_medium({
            'name': org_result['name'],
            'medium': medium_result['name']})
        return_value = Org().remove_medium({
            'name': org_result['name'],
            'medium': medium_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Remove Medium - retcode")
        self.assertFalse(return_value.stderr)

    @bzbug('1062295')
    def test_add_configtemplate(self):
        """
        @Feature: Org - Config Template
        @Test: Check if a Config Template can be added to an Org
        @Assert: Config Template is added to the org
        """
        org_result = make_org()
        template_result = make_template()
        return_value = Org().add_configtemplate({
            'name': org_result['name'],
            'configtemplate': template_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Add ConfigTemplate- retcode")
        self.assertFalse(return_value.stderr)

    @bzbug('1062295')
    def test_remove_configtemplate(self):
        """
        @Feature: Org - ConfigTemplate
        @Test: Check if a ConfigTemplate can be removed from an Org
        @Assert: ConfigTemplate is removed from the org
        """
        org_result = make_org()
        template_result = make_template()
        Org().add_configtemplate({
            'name': org_result['name'],
            'configtemplate': template_result['name']})
        return_value = Org().remove_configtemplate({
            'name': org_result['name'],
            'configtemplate': template_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Remove ConfigTemplate- retcode")
        self.assertFalse(return_value.stderr)

    def test_add_environment(self):
        """
        @Feature: Org - Environment
        @Test: Check if an environment can be added to an Org
        @Assert: Environment is added to the org
        """
        org_result = make_org()
        env_result = make_environment()
        return_value = Org().add_environment({
            'name': org_result['name'],
            'environment': env_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Add Environment - retcode")
        self.assertFalse(return_value.stderr)

    def test_remove_environment(self):
        """
        @Feature: Org - Environment
        @Test: Check if an Environment can be removed from an Org
        @Assert: Environment is removed from the org
        """
        org_result = make_org()
        env_result = make_environment()
        Org().add_environment({
            'name': org_result['name'],
            'environment': env_result['name']})
        return_value = Org().remove_environment({
            'name': org_result['name'],
            'environment': env_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Remove Environment - retcode")
        self.assertFalse(return_value.stderr)

    @bzbug('1062303')
    def test_add_smartproxy(self):
        """
        @Feature: Org - Smartproxy
        @Test: Check if a Smartproxy can be added to an Org
        @Assert: Smartproxy is added to the org
        """
        org_result = make_org()
        proxy_result = make_proxy()
        return_value = Org().add_smartproxy({
            'name': org_result['name'],
            'proxy': proxy_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Add smartproxy - retcode")
        self.assertFalse(return_value.stderr)

    @bzbug('1062303')
    def test_remove_smartproxy(self):
        """
        @Feature: Org - Smartproxy
        @Test: Check if a Smartproxy can be removed from an Org
        @Assert: Smartproxy is removed from the org
        """
        org_result = make_org()
        proxy_result = make_proxy()
        Org().add_smartproxy({
            'name': org_result['name'],
            'proxy': proxy_result['name']})
        return_value = Org().remove_smartproxy({
            'name': org_result['name'],
            'proxy': proxy_result['name']})
        self.assertTrue(return_value.return_code == 0,
                        "Remove smartproxy - retcode")
        self.assertFalse(return_value.stderr)

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
