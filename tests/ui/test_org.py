# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Organization UI
"""

import unittest
from ddt import data, ddt
from nose.plugins.attrib import attr
from robottelo.common import conf
from robottelo.common.helpers import (generate_name, generate_strings_list,
                                      generate_string, generate_ipaddr,
                                      generate_email_address, get_data_file)
from robottelo.common.constants import NOT_IMPLEMENTED, OS_TEMPLATE_DATA_FILE
from robottelo.common.decorators import bzbug, redminebug
from robottelo.ui.locators import common_locators, tab_locators
from tests.ui.baseui import BaseUI

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


@ddt
class Org(BaseUI):
    """
    Implements Organization tests in UI
    """

    # Positive Create

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_1(self, org_name):
        """
        @feature: Organizations
        @test: Create organization with valid name only
        @assert: organization is created, label is auto-generated
        """
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        #select_org = self.navigator.go_to_select_org(org_name)
        self.navigator.go_to_org()
        #self.assertIsNotNone(select_org)  TODO: Add scroll logic Bug: 1053587
        self.assertIsNotNone(self.org.search(org_name))

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_0(self, org_name):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        too long
        @assert: organization is not created
        """
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        error = self.org.wait_until_element(common_locators["name_haserror"])
        self.assertTrue(error)

    def test_negative_create_1(self):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        blank
        @assert: organization is not created
        """

        org_name = ""
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        error = self.org.wait_until_element(common_locators["name_haserror"])
        self.assertTrue(error)

    def test_negative_create_2(self):
        """
        @feature: Organizations
        @test: Create organization with valid label and description, name is
        whitespace
        @assert: organization is not created
        """

        org_name = "    "
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        error = self.org.wait_until_element(common_locators["name_haserror"])
        self.assertTrue(error)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_3(self, org_name):
        """
        @feature: Organizations
        @test: Create organization with valid values, then create a new one
        with same values.
        @assert: organization is not created
        """

        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.org.create(org_name)
        error = self.org.wait_until_element(common_locators["name_haserror"])
        self.assertTrue(error)

    # Positive Delete

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_positive_delete_1(self, org_name):
        """
        @feature: Organizations
        @test: Create organization with valid values then delete it
        @assert: organization is deleted
        """

        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.org.remove(org_name, really=True)
        self.assertIsNone(self.org.search(org_name))

    # Negative Delete

    # Positive Update

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_1(self, new_name):
        """
        @feature: Organizations
        @test: Create organization with valid values then update its name
        @assert: organization name is updated
        """
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.org.update(org_name, new_name)
        self.assertIsNotNone(self.org.search(new_name))

    # Negative Update

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_negative_update_1(self, org_name):
        """
        @feature: Organizations
        @test: Create organization with valid values then fail to update
        its name
        @assert: organization name is not updated
        """

        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        new_name = generate_name(256)
        self.org.update(org_name, new_name)
        error = self.org.wait_until_element(common_locators["name_haserror"])
        self.assertTrue(error)

    # Miscellaneous

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_search_key_1(self, org_name):
        """
        @feature: Organizations
        @test: Create organization and search/find it
        @assert: organization can be found
        """

        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))

    @bzbug('1073601')
    def test_search_org_html(self):
        """
        @feature: Organizations
        @test: Create organization and search/find with html data
        @assert: organization with html data can be found
        """

        org_name = generate_string("html", 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))

    # Associations

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_domain_1(self, domain):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        name and domain name
        @assert: the domain is removed from the organization
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_domains()
        self.domain.create(domain)
        self.assertIsNotNone(self.domain.search(domain))
        self.navigator.go_to_org()
        self.org.create(org_name, domains=[domain], edit=True)
        self.assertIsNotNone(self.org.search(org_name))
        self.org.update(org_name, domains=[domain])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_domains"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % domain))
        self.assertTrue(element)

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_user_3(self, user_name):
        """
        @feature: Organizations
        @test: Create admin users then add user and remove it
        by using the organization name
        @assert: The user is added then removed from the organization
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        org_name = generate_name(8, 8)
        password = generate_name(8)
        email = generate_email_address()
        search_key = "login"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_users()
        self.user.create(user_name, email, password, password)
        self.assertIsNotNone(self.user.search(user_name, search_key))
        self.navigator.go_to_org()
        self.org.create(org_name, users=[user_name], edit=True)
        self.assertIsNotNone(self.org.search(org_name))
        self.org.update(org_name, users=[user_name], new_users=None)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_users"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % user_name))
        self.assertTrue(element)

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_subnet_1(self, subnet_name):
        """
        @feature: Organizations
        @test: Add a subnet by using organization name and subnet name
        @assert: subnet is added
        """

        org_name = generate_name(8, 8)
        new_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_subnets()
        self.subnet.create([org_name], subnet_name, subnet_network,
                           subnet_mask)
        self.assertIsNotNone(self.subnet.search_subnet(subnet_name))
        self.navigator.go_to_org()
        self.org.update(org_name, new_name=new_name,
                        new_subnets=[subnet_name])
        self.assertIsNotNone(self.org.search(new_name))

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_domain_1(self, domain):
        """
        @feature: Organizations
        @test: Add a domain to an organization
        @assert: Domain is added to organization
        """
        org_name = generate_name(8, 8)
        new_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_domains()
        self.domain.create(domain)
        self.assertIsNotNone(self.domain.search(domain))
        self.navigator.go_to_org()
        self.org.update(org_name, new_name=new_name,
                        new_domains=[domain])
        self.assertIsNotNone(self.org.search(new_name))

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_user_2(self, user):
        """
        @feature: Organizations
        @test: Create different types of users then add user
        by using the organization name
        @assert: User is added to organization
        """

        org_name = generate_name(8, 8)
        new_name = generate_name(8, 8)
        password = generate_name(8)
        email = generate_email_address()
        search_key = "login"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_users()
        self.user.create(user, email, password, password)
        self.assertIsNotNone(self.user.search(user, search_key))
        self.navigator.go_to_org()
        self.org.update(org_name, new_name=new_name,
                        new_users=[user])
        self.assertIsNotNone(self.org.search(new_name))

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_computeresource_1(self, resource_name):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        name and computeresource name
        @assert: computeresource is added then removed
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        org_name = generate_name(8, 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_compute_resources()
        self.compute_resource.create(resource_name, None,
                                     provider_type="Libvirt",
                                     url=url)
        self.navigator.go_to_compute_resources()
        self.assertIsNotNone(self.compute_resource.search(resource_name))
        self.navigator.go_to_org()
        self.org.create(org_name, resources=[resource_name], edit=True)
        self.assertIsNotNone(self.org.search(org_name))
        self.org.update(org_name, resources=[resource_name],
                        new_resources=None)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_resources"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % resource_name))
        self.assertTrue(element)

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_medium_1(self, medium):
        """
        @feature: Organizations
        @test: Remove medium by using organization name and medium name
        @assert: medium is added then removed
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        org_name = generate_name(8, 8)
        path = URL % generate_name(6)
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_installation_media()
        self.medium.create(medium, path, os_family)
        self.assertIsNotNone(self.medium.search(medium))
        self.navigator.go_to_org()
        self.org.create(org_name, medias=[medium], edit=True)
        self.assertIsNotNone(self.org.search(org_name))
        self.org.update(org_name, medias=[medium],
                        new_medias=None)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_media"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % medium))
        self.assertTrue(element)


    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_configtemplate_1(self, template):
        """
        @feature: Organizations
        @test: Remove config template
        @assert: configtemplate is added then removed
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        org_name = generate_name(8, 8)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_provisioning_templates()
        self.template.create(template, template_path, True,
                             temp_type, None)
        self.assertIsNotNone(self.template.search(template))
        self.navigator.go_to_org()
        self.org.create(org_name, templates=[template],
                        edit=True)
        self.assertIsNotNone(self.org.search(org_name))
        self.org.update(org_name, templates=[template])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_template"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % template))
        self.assertTrue(element)

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_computeresource_1(self, resource_name):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        name and computeresource name
        @assert: computeresource is added
        """

        org_name = generate_name(8, 8)
        new_name = generate_name(8, 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_compute_resources()
        self.compute_resource.create(resource_name, [org_name],
                                     provider_type="Libvirt",
                                     url=url)
        self.navigator.go_to_compute_resources()
        self.assertIsNotNone(self.compute_resource.search(resource_name))
        self.navigator.go_to_org()
        self.org.update(org_name, new_name=new_name,
                        new_resources=[resource_name])
        self.assertIsNotNone(self.org.search(new_name))

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_medium_1(self, medium):
        """
        @feature: Organizations
        @test: Add medium by using the organization name and medium name
        @assert: medium is added
        """

        org_name = generate_name(8, 8)
        new_name = generate_name(8, 8)
        path = URL % generate_name(6)
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_installation_media()
        self.medium.create(medium, path, os_family)
        self.assertIsNotNone(self.medium.search(medium))
        self.navigator.go_to_org()
        self.org.update(org_name, new_name=new_name,
                        new_medias=[medium])
        self.assertIsNotNone(self.org.search(new_name))

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_configtemplate_1(self, template):
        """
        @feature: Organizations
        @test: Add config template by using organization name and
        configtemplate name
        @assert: configtemplate is added
        """

        org_name = generate_name(8, 8)
        new_name = generate_name(8, 8)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_provisioning_templates()
        self.template.create(template, template_path, True,
                             temp_type, None)
        self.assertIsNotNone(self.template.search(template))
        self.navigator.go_to_org()
        self.org.update(org_name, new_name=new_name,
                        new_templates=[template])
        self.assertIsNotNone(self.org.search(new_name))

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_subnet_1(self, subnet_name):
        """
        @feature: Organizations
        @test: Remove subnet by using organization name and subnet name
        @assert: subnet is added then removed
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        org_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_subnets()
        self.subnet.create(None, subnet_name, subnet_network,
                           subnet_mask)
        self.assertIsNotNone(self.subnet.search_subnet(subnet_name))
        self.navigator.go_to_org()
        self.org.create(org_name, subnets=[subnet_name], edit=True)
        self.assertIsNotNone(self.org.search(org_name))
        self.org.update(org_name, subnets=[subnet_name], new_subnets=None)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_subnets"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % subnet_name))
        self.assertTrue(element)

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass

    @unittest.skip(NOT_IMPLEMENTED)
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

        pass
