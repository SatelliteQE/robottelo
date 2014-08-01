# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

# pylint: disable=R0904

"""
Test class for Organization UI
"""

import sys
from ddt import ddt
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest
from nose.plugins.attrib import attr
from robottelo.common import conf
from robottelo.common.decorators import data
from robottelo.common.helpers import (generate_strings_list,
                                      generate_string, generate_ipaddr,
                                      generate_email_address, get_data_file)
from robottelo.common.constants import OS_TEMPLATE_DATA_FILE
from robottelo.common.decorators import skip_if_bz_bug_open, stubbed
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_org, make_templates, make_domain, make_user, make_hostgroup,
    make_subnet, make_loc, make_resource, make_media, make_env)
from robottelo.ui.locators import common_locators, tab_locators, locators
from robottelo.ui.session import Session

URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


@ddt
class Org(UITestCase):
    """
    Implements Organization tests in UI
    """

    # Tests for issues

    def test_auto_search(self):
        """
        @test: Can auto-complete search for an organization by partial name
        @feature: Organizations
        @assert: Created organization can be auto search by its partial name
        """

        org_name = generate_string("alpha", 8)
        part_string = org_name[:3]
        with Session(self.browser) as session:
            page = session.nav.go_to_org
            make_org(session, org_name=org_name)
            auto_search = self.org.auto_complete_search(
                page, locators["org.org_name"], part_string, org_name,
                search_key='name')
            self.assertIsNotNone(auto_search)

    # Positive Create

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_1(self, org_name):
        """
        @test: Create organization with valid name only.
        @feature: Organizations
        @assert: organization is created, label is auto-generated
        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    @unittest.skip("parent_org feature is disabled currently")
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
           'name': generate_string('latin1', 20),
           'desc': generate_string('latin1', 10)},
          {'label': generate_string('alpha', 10),
           'name': generate_string('html', 20),
           'desc': generate_string('html', 10)})
    def test_positive_create_2(self, test_data):
        """
        @test: Create organization with valid name, label, parent_org, desc.
        @feature: Organizations
        @assert: organization is created.
        """
        parent = generate_string("alpha", 8)
        desc = test_data['desc']
        label = test_data['label']
        org_name = test_data['name']
        with Session(self.browser) as session:
            make_org(session, org_name=parent)
            make_org(session, org_name=org_name, label=label,
                     desc=desc, parent_org=parent)
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
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, label=org_label)
            self.org.search(org_name).click()
            name = session.nav.wait_until_element(
                name_loc).get_attribute("value")
            label = session.nav.wait_until_element(
                label_loc).get_attribute("value")
            self.assertNotEqual(name, label)

    @attr('ui', 'org', 'implemented')
    @data({'data': generate_string('alpha', 10)},
          {'data': generate_string('numeric', 10)},
          {'data': generate_string('alphanumeric', 10)})
    # As label cannot contain chars other than ascii alpha numerals, '_', '-'.
    def test_positive_create_4(self, test_data):
        """
        @test: Create organization with valid matching name and label only.
        @feature: Organizations
        @assert: organization is created, label matches name
        """
        name_loc = locators["org.name"]
        label_loc = locators["org.label"]
        org_name = org_label = test_data['data']
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, label=org_label)
            name = self.org.wait_until_element(
                name_loc).get_attribute("value")
            label = self.org.wait_until_element(
                label_loc).get_attribute("value")
            self.assertEqual(name, label)

    @skip_if_bz_bug_open("1079482")
    @attr('ui', 'org', 'implemented')
    @data({'name': generate_string('alpha', 10),
           'desc': generate_string('alpha', 10)},
          {'name': generate_string('numeric', 10),
           'desc': generate_string('numeric', 10)},
          {'name': generate_string('alphanumeric', 10),
           'desc': generate_string('alphanumeric', 10)},
          {'name': generate_string('utf8', 10),
           'desc': generate_string('utf8', 10)},
          {'name': generate_string('latin1', 20),
           'desc': generate_string('latin1', 10)},
          {'name': generate_string('html', 20),
           'desc': generate_string('html', 10)})
    def test_positive_create_5(self, test_data):
        """
        @test: Create organization with valid name and description only.
        @feature: Organizations
        @assert: organization is created, label is auto-generated
        @BZ: 1079482
        """

        desc = test_data['desc']
        org_name = test_data['name']
        label_loc = locators["org.label"]
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, desc=desc)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.search(org_name).click()
            label_ele = session.nav.wait_until_element(label_loc)
            label_value = label_ele.get_attribute("value")
            self.assertIsNotNone(label_value)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_0(self, org_name):
        """
        @test: Create organization with valid label and description, name is
        too long.
        @feature: Organizations Negative Tests
        @assert: organization is not created
        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_negative_create_1(self):
        """
        @test: Create organization with valid label and description, name is
        blank.
        @feature: Organizations - Negative Tests
        @assert: organization is not created
        """
        org_name = ""
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_negative_create_2(self):
        """
        @test: Create organization with valid label and description, name is
        whitespace.
        @feature: Organizations Negative Test.
        @assert: organization is not created
        """
        org_name = "    "
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_3(self, org_name):
        """
        @test: Create organization with valid values, then create a new one
        with same values.
        @feature: Organizations Negative Test.
        @assert: organization is not created
        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.create(org_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    # Positive Delete

    @stubbed('Organization deletion is disabled')
    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_positive_delete_1(self, org_name):
        """
        @test: Create organization with valid values then delete it.
        @feature: Organizations Positive Delete test.
        @assert: organization is deleted
        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.remove(org_name, really=True)
            self.assertIsNone(self.org.search(org_name))

    # Negative Delete

    # Positive Update

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_1(self, new_name):
        """
        @test: Create organization with valid values then update its name.
        @feature: Organizations Positive Update test.
        @assert: organization name is updated
        """

        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_name=new_name)
            self.assertIsNotNone(self.org.search(new_name))

    # Negative Update

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_negative_update_1(self, org_name):
        """
        @test: Create organization with valid values then fail to update
        its name.
        @feature: Organizations Negative Update test.
        @assert: organization name is not updated
        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            new_name = generate_string("alpha", 256)
            self.org.update(org_name, new_name=new_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    # Miscellaneous

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_search_key_1(self, org_name):
        """
        @test: Create organization and search/find it.
        @feature: Organizations search.
        @assert: organization can be found
        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    # Associations

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_domain_1(self, domain):
        """
        @test: Add a domain to an organization and remove it by organization
        name and domain name.
        @feature: Organizations Disassociate domain.
        @assert: the domain is removed from the organization
        """
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_domain(session, name=domain)
            self.assertIsNotNone(self.domain.search(domain))
            make_org(session, org_name=org_name, domains=[domain],
                     edit=True)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_domains"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % domain))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, domains=[domain])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_domains"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % domain))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    #  Note: HTML username is invalid as per the UI msg.
    @attr('ui', 'org', 'implemented')
    @data({'name': generate_string('alpha', 8)},
          {'name': generate_string('numeric', 8)},
          {'name': generate_string('alphanumeric', 8)},
          {'name': generate_string('utf8', 8)},
          {'name': generate_string('latin1', 8)})
    def test_remove_user_3(self, testdata):
        """
        @test: Create admin users then add user and remove it
        by using the organization name.
        @feature: Organizations dis-associate user.
        @assert: The user is added then removed from the organization
        """
        user_name = testdata['name']
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        password = generate_string("alpha", 8)
        email = generate_email_address()
        search_key = "login"
        with Session(self.browser) as session:
            make_user(session, username=user_name, email=email,
                      password1=password, password2=password)
            self.assertIsNotNone(self.user.search(user_name, search_key))
            make_org(session, org_name=org_name, users=[user_name], edit=True)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_users"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % user_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, users=[user_name], new_users=None)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_users"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % user_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_hostgroup_1(self, host_grp):
        """
        @test: Add a hostgroup and remove it by using the organization
        name and hostgroup name.
        @feature: Organizations remove hostgroup.
        @assert: hostgroup is added to organization then removed.
        """
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_hostgroup(session, name=host_grp)
            self.assertIsNotNone(self.hostgroup.search(host_grp))
            make_org(session, org_name=org_name, hostgroups=[host_grp],
                     edit=True)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_hostgrps"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % host_grp))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, hostgroups=[host_grp],
                            new_hostgroups=None)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_hostgrps"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % host_grp))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @stubbed
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

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_subnet_1(self, subnet_name):
        """
        @feature: Organizations associate subnet.
        @test: Add a subnet by using organization name and subnet name.
        @assert: subnet is added.
        """
        strategy, value = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            make_subnet(session, subnet_name=subnet_name,
                        subnet_network=subnet_network, subnet_mask=subnet_mask)
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name))
            self.org.update(org_name, new_subnets=[subnet_name])
            self.org.search(org_name).click()
            self.org.wait_until_element(
                tab_locators["context.tab_subnets"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % subnet_name))
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_domain_1(self, domain):
        """
        @test: Add a domain to an organization.
        @feature: Organizations associate domain.
        @assert: Domain is added to organization.
        """
        strategy, value = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            make_domain(session, name=domain)
            self.assertIsNotNone(self.domain.search(domain))
            self.org.update(org_name, new_domains=[domain])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_domains"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % domain))
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data({'name': generate_string('alpha', 8)},
          {'name': generate_string('numeric', 8)},
          {'name': generate_string('alphanumeric', 8)},
          {'name': generate_string('utf8', 8)},
          {'name': generate_string('latin1', 8)})
    def test_add_user_2(self, testdata):
        """
        @test: Create different types of users then add user
        by using the organization name.
        @feature: Organizations associate user.
        @assert: User is added to organization.
        """
        user = testdata['name']
        strategy, value = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        password = generate_string("alpha", 8)
        email = generate_email_address()
        search_key = "login"
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            make_user(session, username=user, email=email,
                      password1=password, password2=password)
            self.assertIsNotNone(self.user.search(user, search_key))
            self.org.update(org_name, new_users=[user])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_users"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % user))
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_hostgroup_1(self, host_grp):
        """
        @test: Add a hostgroup by using the organization
        name and hostgroup name.
        @feature: Organizations associate host-group.
        @assert: hostgroup is added to organization
        """
        strategy, value = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            make_hostgroup(session, name=host_grp)
            self.assertIsNotNone(self.hostgroup.search(host_grp))
            self.org.update(org_name, new_hostgroups=[host_grp])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_hostgrps"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % host_grp))
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_location_1(self, location):
        """
        @test: Add a location by using the organization
        name and location name.
        @feature: Organizations associate location.
        @assert: location is added to organization.
        """
        strategy, value = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            make_loc(session, name=location)
            self.assertIsNotNone(self.location.search(location))
            self.org.update(org_name, new_locations=[location])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_locations"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % location))
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_computeresource_1(self, resource_name):
        """
        @test: Remove computeresource by using the organization
        name and computeresource name.
        @feature: Organizations dis-associate compute-resource.
        @assert: computeresource is added then removed.
        """
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=resource_name, provider_type="Libvirt",
                          url=url)
            self.assertIsNotNone(self.compute_resource.search(resource_name))
            make_org(session, org_name=org_name, resources=[resource_name],
                     edit=True)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_resources"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % resource_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, resources=[resource_name],
                            new_resources=None)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_resources"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % resource_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_medium_1(self, medium):
        """
        @feature: Organizations disassociate installation media.
        @test: Remove medium by using organization name and medium name.
        @assert: medium is added then removed.
        """
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=medium, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(medium))
            make_org(session, org_name=org_name, medias=[medium], edit=True)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_media"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % medium))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.navigator.go_to_org()
            self.org.update(org_name, medias=[medium],
                            new_medias=None)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_media"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % medium))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_configtemplate_1(self, template):
        """
        @test: Remove config template.
        @feature: Organizations dissociate config templates.
        @assert: configtemplate is added then removed.
        """
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=template, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(template))
            make_org(session, org_name=org_name, templates=[template],
                     edit=True)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_template"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % template))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, templates=[template])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_template"]).click()
            element = self.org.wait_until_element((strategy,
                                                   value % template))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data({'name': generate_string('alpha', 8)},
          {'name': generate_string('numeric', 8)},
          {'name': generate_string('alphanumeric', 8)})
    def test_add_environment_1(self, testdata):
        """
        @test: Add environment by using organization name and evironment name.
        @feature: Organizations associate environment.
        @assert: environment is added.
        """
        env = testdata['name']
        strategy, value = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            make_env(session, name=env)
            search = self.environment.search(env)
            self.assertIsNotNone(search)
            self.org.update(org_name, new_envs=[env])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_env"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % env))
            self.assertIsNotNone(element)

    @stubbed
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

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_computeresource_1(self, resource_name):
        """
        @test: Add compute resource using the organization
        name and computeresource name.
        @feature: Organizations associate compute resource.
        @assert: computeresource is added.
        """
        strategy, value = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            make_resource(session, name=resource_name, orgs=[org_name],
                          provider_type="Libvirt", url=url)
            self.assertIsNotNone(self.compute_resource.search(resource_name))
            self.org.update(org_name, new_resources=[resource_name])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_resources"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % resource_name))
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_medium_1(self, medium):
        """
        @test: Add medium by using the organization name and medium name.
        @feature: Organizations associate medium.
        @assert: medium is added.
        """
        strategy, value = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            make_media(session, name=medium, path=path,
                       os_family=os_family)
            self.assertIsNotNone(self.medium.search(medium))
            self.org.update(org_name, new_medias=[medium])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_media"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % medium))
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_add_configtemplate_1(self, template):
        """
        @test: Add config template by using organization name and
        configtemplate name.
        @feature: Organizations associate config template.
        @assert: configtemplate is added
        """
        strategy, value = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            session.nav.go_to_provisioning_templates()
            make_templates(session, name=template, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(template))
            self.org.update(org_name, new_templates=[template])
            self.org.search(org_name).click()
            self.org.wait_until_element(
                tab_locators["context.tab_template"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % template))
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data({'name': generate_string('alpha', 8)},
          {'name': generate_string('numeric', 8)},
          {'name': generate_string('alphanumeric', 8)})
    def test_remove_environment_1(self, testdata):
        """
        @test: Remove environment by using organization name & evironment name.
        @feature: Organizations dis-associate environment.
        @assert: environment is removed from Organization.
        """
        env = testdata['name']
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_env(session, name=env)
            search = self.environment.search(env)
            self.assertIsNotNone(search)
            make_org(session, org_name=org_name, envs=[env],
                     edit=True)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_env"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % env))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, envs=[env])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_env"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % env))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'org', 'implemented')
    @data(*generate_strings_list())
    def test_remove_subnet_1(self, subnet_name):
        """
        @test: Remove subnet by using organization name and subnet name.
        @feature: Organizations dis-associate subnet.
        @assert: subnet is added then removed.
        """
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        org_name = generate_string("alpha", 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=subnet_name,
                        subnet_network=subnet_network, subnet_mask=subnet_mask)
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name))
            make_org(session, org_name=org_name, subnets=[subnet_name],
                     edit=True)
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_subnets"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % subnet_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, subnets=[subnet_name])
            self.org.search(org_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_subnets"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % subnet_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)
