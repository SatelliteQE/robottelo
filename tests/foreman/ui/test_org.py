# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Organization UI
"""

import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest
from ddt import data, ddt
from nose.plugins.attrib import attr
from robottelo.common import conf
from robottelo.common.helpers import (generate_name, generate_strings_list,
                                      generate_string, generate_ipaddr,
                                      generate_email_address, get_data_file)
from robottelo.common.constants import NOT_IMPLEMENTED, OS_TEMPLATE_DATA_FILE
from robottelo.common.decorators import bzbug
from robottelo.ui.locators import common_locators, tab_locators, locators
from tests.foreman.ui.baseui import BaseUI

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


@ddt
class Org(BaseUI):
    """
    Implements Organization tests in UI
    """

    # Tests for issues

    def test_redmine_4443(self):
        """
        @test: Can auto-complete search for an organization by partial name
        @feature: Organizations
        @assert: Created organization can be auto search by its partial name
        @BZ: redmine #4443
        """

        org_name = generate_name(8)
        part_string = org_name[:3]
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.auto_complete_search
                             (part_string, org_name, search_key='name'))

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
        # select_org = self.navigator.go_to_select_org(org_name)
        self.navigator.go_to_org()
        # self.assertIsNotNone(select_org)  TODO: Add scroll logic Bug: 1053587
        self.assertIsNotNone(self.org.search(org_name))

    @attr('ui', 'org', 'implemented')
    @data({'label': generate_string('alpha', 10),
           'name': generate_string('alpha', 10),
           'desc': generate_string('alpha', 10)},
          {'label': generate_string('numeric', 10),
           'name': generate_string('numeric', 10),
           'desc': generate_string('numeric', 10)},
          {'label': generate_string('alphanumeric', 10),
           'name': generate_string('alphanumeric', 10),
           'desc': generate_string('alphanumeric', 10)},
          {'label': generate_string('alpha', 10),
           'name': generate_string('utf8', 10),
           'desc': generate_string('utf8', 10)},
          {'label': generate_string('alpha', 10),
           'name': generate_string('html', 20),
           'desc': generate_string('html', 10)})
    def test_positive_create_2(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name, label, parent_org, desc
        @assert: organization is created
        """

        parent = generate_name(8, 8)
        desc = test_data['desc']
        label = test_data['label']
        org_name = test_data['name']
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        # If parent org is not required to be static.
        self.org.create(parent)
        self.navigator.go_to_org()
        self.org.create(org_name, label=label, desc=desc,
                        parent_org=parent)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))

    @attr('ui', 'org', 'implemented')
    @data({'name': generate_string('alpha', 10),
           'label': generate_string('alpha', 10)},
          {'name': generate_string('numeric', 10),
           'label': generate_string('numeric', 10)},
          {'name': generate_string('alphanumeric', 10),
           'label': generate_string('alphanumeric', 10)})
    # As label cannot contain chars other than ascii alpha numerals, '_', '-'.
    def test_positive_create_3(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid unmatching name and label only
        @assert: organization is created, label does not match name
        """

        name_loc = locators["org.name"]
        label_loc = locators["org.label"]
        org_name = test_data['name']
        org_label = test_data['label']
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name, label=org_label)
        self.navigator.go_to_org()
        self.org.search(org_name).click()
        name = self.org.wait_until_element(name_loc).get_attribute("value")
        label = self.org.wait_until_element(label_loc).get_attribute("value")
        self.assertNotEqual(name, label)

    @attr('ui', 'org', 'implemented')
    @data({'data': generate_string('alpha', 10)},
          {'data': generate_string('numeric', 10)},
          {'data': generate_string('alphanumeric', 10)})
    # As label cannot contain chars other than ascii alpha numerals, '_', '-'.
    def test_positive_create_4(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid matching name and label only
        @assert: organization is created, label matches name
        """
        name_loc = locators["org.name"]
        label_loc = locators["org.label"]
        org_name = org_label = test_data['data']
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name, label=org_label)
        self.navigator.go_to_org()
        self.org.search(org_name).click()
        name = self.org.wait_until_element(name_loc).get_attribute("value")
        label = self.org.wait_until_element(label_loc).get_attribute("value")
        self.assertEqual(name, label)

    @bzbug("1079482")
    @attr('ui', 'org', 'implemented')
    @data({'name': generate_string('alpha', 10),
           'desc': generate_string('alpha', 10)},
          {'name': generate_string('numeric', 10),
           'desc': generate_string('numeric', 10)},
          {'name': generate_string('alphanumeric', 10),
           'desc': generate_string('alphanumeric', 10)},
          {'name': generate_string('utf8', 10),
           'desc': generate_string('utf8', 10)},
          {'name': generate_string('html', 20),
           'desc': generate_string('html', 10)})
    def test_positive_create_5(self, test_data):
        """
        @feature: Organizations
        @test: Create organization with valid name and description only
        @assert: organization is created, label is auto-generated
        @BZ: 1079482
        """

        desc = test_data['desc']
        org_name = test_data['name']
        label_loc = locators["org.label"]
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name, desc=desc)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_org()
        self.org.search(org_name).click()
        label_ele = self.org.wait_until_element(label_loc)
        label_value = label_ele.get_attribute("value")
        self.assertTrue(label_value)

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

    # Associations

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_domain_1(self, domain):
        """
        @feature: Organizations
        @test: Add a domain to an organization and remove it by organization
        name and domain name
        @assert: the domain is removed from the organization
        @BZ: 1076562
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        strategy1 = common_locators["entity_deselect"][0]
        value1 = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_domains()
        self.domain.create(domain)
        self.assertIsNotNone(self.domain.search(domain))
        self.navigator.go_to_org()
        self.org.create(org_name, domains=[domain], edit=True)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_domains"]).click()
        element = self.org.wait_until_element((strategy1,
                                               value1 % domain))
        # Item is listed in 'Selected Items' list and not 'All Items' list.
        self.assertTrue(element)
        self.org.update(org_name, domains=[domain])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_domains"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % domain))
        # Item is listed in 'All Items' list and not 'Selected Items' list.
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_user_3(self, user_name):
        """
        @feature: Organizations
        @test: Create admin users then add user and remove it
        by using the organization name
        @assert: The user is added then removed from the organization
        @BZ: 1076562
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        strategy1 = common_locators["entity_deselect"][0]
        value1 = common_locators["entity_deselect"][1]
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
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_users"]).click()
        element = self.org.wait_until_element((strategy1,
                                               value1 % user_name))
        # Item is listed in 'Selected Items' list and not 'All Items' list.
        self.assertTrue(element)
        self.navigator.go_to_org()
        self.org.update(org_name, users=[user_name], new_users=None)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_users"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % user_name))
        # Item is listed in 'All Items' list and not 'Selected Items' list.
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_hostgroup_1(self, host_grp):
        """
        @feature: Organizations
        @test: Add a hostgroup and remove it by using the organization
        name and hostgroup name
        @assert: hostgroup is added to organization then removed
        @BZ: 1076562
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        strategy1 = common_locators["entity_deselect"][0]
        value1 = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_host_groups()
        self.hostgroup.create(host_grp)
        self.assertIsNotNone(self.hostgroup.search(host_grp))
        self.navigator.go_to_org()
        self.org.create(org_name, hostgroups=[host_grp], edit=True)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_hostgrps"]).click()
        element = self.org.wait_until_element((strategy1,
                                               value1 % host_grp))
        # Item is listed in 'Selected Items' list and not 'All Items' list.
        self.assertTrue(element)
        self.navigator.go_to_org()
        self.org.update(org_name, hostgroups=[host_grp], new_hostgroups=None)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_hostgrps"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % host_grp))
        # Item is listed in 'All Items' list and not 'Selected Items' list.
        self.assertTrue(element)

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
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

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_subnet_1(self, subnet_name):
        """
        @feature: Organizations
        @test: Add a subnet by using organization name and subnet name
        @assert: subnet is added
        @BZ: 1076562
        """

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_subnets()
        self.subnet.create(None, subnet_name, subnet_network,
                           subnet_mask)
        self.assertIsNotNone(self.subnet.search_subnet(subnet_name))
        self.navigator.go_to_org()
        self.org.update(org_name, new_subnets=[subnet_name])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_subnets"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % subnet_name))
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_domain_1(self, domain):
        """
        @feature: Organizations
        @test: Add a domain to an organization
        @assert: Domain is added to organization
        @BZ: 1076562
        """

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_domains()
        self.domain.create(domain)
        self.assertIsNotNone(self.domain.search(domain))
        self.navigator.go_to_org()
        self.org.update(org_name, new_domains=[domain])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_domains"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % domain))
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_user_2(self, user):
        """
        @feature: Organizations
        @test: Create different types of users then add user
        by using the organization name
        @assert: User is added to organization
        @BZ: 1076562
        """

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
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
        self.org.update(org_name, new_users=[user])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_users"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % user))
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_hostgroup_1(self, host_grp):
        """
        @feature: Organizations
        @test: Add a hostgroup by using the organization
        name and hostgroup name
        @assert: hostgroup is added to organization
        @BZ: 1076562
        """

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_host_groups()
        self.hostgroup.create(host_grp)
        self.assertIsNotNone(self.hostgroup.search(host_grp))
        self.org.update(org_name, new_hostgroups=[host_grp])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_hostgrps"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % host_grp))
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_location_1(self, location):
        """
        @feature: Organizations
        @test: Add a location by using the organization
        name and location name
        @assert: location is added to organization
        @BZ: 1076562
        """

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_host_groups()
        self.location.create(location)
        self.assertIsNotNone(self.location.search(location))
        self.org.update(org_name, new_locations=[location])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_locations"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % location))
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_computeresource_1(self, resource_name):
        """
        @feature: Organizations
        @test: Remove computeresource by using the organization
        name and computeresource name
        @assert: computeresource is added then removed
        @BZ: 1076562
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        strategy1 = common_locators["entity_deselect"][0]
        value1 = common_locators["entity_deselect"][1]
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
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_resources"]).click()
        element = self.org.wait_until_element((strategy1,
                                               value1 % resource_name))
        # Item is listed in 'Selected Items' list and not 'All Items' list.
        self.assertTrue(element)
        self.org.update(org_name, resources=[resource_name],
                        new_resources=None)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_resources"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % resource_name))
        # Item is listed in 'All Items' list and not 'Selected Items' list.
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_medium_1(self, medium):
        """
        @feature: Organizations
        @test: Remove medium by using organization name and medium name
        @assert: medium is added then removed
        @BZ: 1076562
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        strategy1 = common_locators["entity_deselect"][0]
        value1 = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
        path = URL % generate_name(6)
        os_family = "Red Hat"
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_installation_media()
        self.medium.create(medium, path, os_family)
        self.assertIsNotNone(self.medium.search(medium))
        self.navigator.go_to_org()
        self.org.create(org_name, medias=[medium], edit=True)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_media"]).click()
        element = self.org.wait_until_element((strategy1,
                                               value1 % medium))
        # Item is listed in 'Selected Items' list and not 'All Items' list.
        self.assertTrue(element)
        self.org.update(org_name, medias=[medium],
                        new_medias=None)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_media"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % medium))
        # Item is listed in 'All Items' list and not 'Selected Items' list.
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_configtemplate_1(self, template):
        """
        @feature: Organizations
        @test: Remove config template
        @assert: configtemplate is added then removed
        @BZ: 1076562
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        strategy1 = common_locators["entity_deselect"][0]
        value1 = common_locators["entity_deselect"][1]
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
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_template"]).click()
        element = self.org.wait_until_element((strategy1,
                                               value1 % template))
        # Item is listed in 'Selected Items' list and not 'All Items' list.
        self.assertTrue(element)
        self.org.update(org_name, templates=[template])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_template"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % template))
        # Item is listed in 'All Items' list and not 'Selected Items' list.
        self.assertTrue(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_environment_1(self, env):
        """
        @feature: Organizations
        @test: Add environment by using organization name and evironment name
        @assert: environment is added
        @status: manual
        """

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.assertIsNotNone(self.org.search(org_name))
        self.navigator.go_to_environments()
        self.environment.create(env, None)
        search = self.environment.search(env)
        self.assertIsNotNone(search)
        self.navigator.go_to_org()
        self.org.update(org_name, new_envs=[env])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_env"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % env))
        self.assertTrue(element)

    @unittest.skip(NOT_IMPLEMENTED)
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
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

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_computeresource_1(self, resource_name):
        """
        @feature: Organizations
        @test: Add compute resource using the organization
        name and computeresource name
        @assert: computeresource is added
        @BZ: 1076562
        """

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
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
        self.org.update(org_name, new_resources=[resource_name])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_resources"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % resource_name))
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_medium_1(self, medium):
        """
        @feature: Organizations
        @test: Add medium by using the organization name and medium name
        @assert: medium is added
        @BZ: 1076562
        """

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
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
        self.org.update(org_name, new_medias=[medium])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_media"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % medium))
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_configtemplate_1(self, template):
        """
        @feature: Organizations
        @test: Add config template by using organization name and
        configtemplate name
        @assert: configtemplate is added
        @BZ: 1076562
        """

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
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
        self.org.update(org_name, new_templates=[template])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_media"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % template))
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_environment_1(self, env):
        """
        @feature: Organizations
        @test: Remove environment by using organization name & evironment name
        @assert: environment is removed from Organization
        @BZ: 1076562
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        strategy1 = common_locators["entity_deselect"][0]
        value1 = common_locators["entity_deselect"][1]
        org_name = generate_name(8, 8)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_environments()
        self.environment.create(env, None)
        search = self.environment.search(env)
        self.assertIsNotNone(search)
        self.navigator.go_to_org()
        self.org.create(org_name, envs=[env], edit=True)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_env"]).click()
        element = self.org.wait_until_element((strategy1,
                                               value1 % env))
        # Item is listed in 'Selected Items' list and not 'All Items' list.
        self.assertTrue(element)
        self.org.update(org_name, new_envs=[env])
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_env"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % env))
        # Item is listed in 'All Items' list and not 'Selected Items' list.
        self.assertTrue(element)

    @bzbug('1076562')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_subnet_1(self, subnet_name):
        """
        @feature: Organizations
        @test: Remove subnet by using organization name and subnet name
        @assert: subnet is added then removed
        @BZ: 1076562
        """

        strategy = common_locators["entity_select"][0]
        value = common_locators["entity_select"][1]
        strategy1 = common_locators["entity_deselect"][0]
        value1 = common_locators["entity_deselect"][1]
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
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_subnets"]).click()
        element = self.org.wait_until_element((strategy1,
                                               value1 % subnet_name))
        # Item is listed in 'Selected Items' list and not 'All Items' list.
        self.assertTrue(element)
        self.org.update(org_name, subnets=[subnet_name], new_subnets=None)
        self.org.search(org_name).click()
        self.org.wait_until_element(tab_locators["orgs.tab_subnets"]).click()
        element = self.org.wait_until_element((strategy,
                                               value % subnet_name))
        # Item is listed in 'All Items' list and not 'Selected Items' list.
        self.assertTrue(element)
