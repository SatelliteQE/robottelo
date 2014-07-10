# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

# pylint: disable=R0904

"""
Test class for Locations UI
"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common import conf
from robottelo.common.decorators import data
from robottelo.common.helpers import (generate_strings_list,
                                      generate_string, generate_ipaddr,
                                      generate_email_address, get_data_file)
from robottelo.common.constants import OS_TEMPLATE_DATA_FILE
from robottelo.test import UITestCase
from robottelo.ui.factory import (make_loc, make_subnet, make_domain, make_env,
                                  make_user, make_org, make_hostgroup,
                                  make_resource, make_media, make_templates)
from robottelo.ui.locators import common_locators, tab_locators
from robottelo.ui.session import Session


URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


@ddt
class Location(UITestCase):
    """
    Implements Location tests in UI
    """

    # Positive Create

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_1(self, loc_name):
        """
        @feature: Locations
        @test: Create Location with valid name only
        @assert: Location is created, label is auto-generated
        """

        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_negative_create_1(self, loc_name):
        """
        @feature: Locations
        @test: Create location with name as too long
        @assert: location is not created
        """
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertTrue(error)

    def test_negative_create_2(self):
        """
        @feature: Locations
        @test: Create location with name as blank
        @assert: location is not created
        """

        loc_name = ""
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertTrue(error)

    def test_negative_create_3(self):
        """
        @feature: Locations
        @test: Create location with name as whitespace
        @assert: location is not created
        """

        loc_name = "    "
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertTrue(error)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_4(self, loc_name):
        """
        @feature: Locations
        @test: Create location with valid values, then create a new one
        with same values.
        @assert: location is not created
        """

        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertTrue(error)

    # Positive Update

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_1(self, new_name):
        """
        @feature: Locations
        @test: Create Location with valid values then update its name
        @assert: Location name is updated
        """

        loc_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_name=new_name)
            self.assertIsNotNone(self.location.search(new_name))

    # Negative Update

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_negative_update_1(self, loc_name):
        """
        @feature: Locations
        @test: Create Location with valid values then fail to update
        its name
        @assert: Location name is not updated
        """

        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            new_name = generate_string("alpha", 256)
            self.org.update(loc_name, new_name=new_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertTrue(error)

    # Miscellaneous

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_search_key_1(self, loc_name):
        """
        @feature: Locations
        @test: Create location and search/find it
        @assert: location can be found
        """

        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))

    def test_autocomplete_search(self):
        """
        @test: Can auto-complete search for an location by partial name
        @feature: Locations
        @assert: Created location can be auto search by its partial name
        """

        loc_name = generate_string("alpha", 8)
        part_string = loc_name[:3]
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.auto_complete_search(
                part_string, loc_name, search_key='name'))

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_subnet_1(self):
        """
        @feature: Locations
        @test: Add a subnet by using location name and subnet name
        @assert: subnet is added
        """
        subnet_name = "fed121"
        strategy, value = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_subnet(session, orgs=None, subnet_name=subnet_name,
                        subnet_network=subnet_network, subnet_mask=subnet_mask)
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name))
            self.location.update(loc_name, new_subnets=[subnet_name])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_subnets"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % subnet_name))
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_domain_1(self, domain):
        """
        @feature: Locations
        @test: Add a domain to a Location
        @assert: Domain is added to Location
        """

        strategy, value = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_domain(session, name=domain)
            self.assertIsNotNone(self.domain.search(domain))
            self.location.update(loc_name, new_domains=[domain])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_domains"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % domain))
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_user_1(self, user):
        """
        @feature: Locations
        @test: Create user then add user
        by using the location name
        @assert: User is added to location
        """

        strategy, value = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        password = generate_string("alpha", 8)
        email = generate_email_address()
        search_key = "login"
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_user(session, username=user, email=email,
                      password1=password, password2=password)
            self.assertIsNotNone(self.user.search(user, search_key))
            self.location.update(loc_name, new_users=[user])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_users"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % user))
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_hostgroup_1(self, host_grp):
        """
        @feature: Locations
        @test: Add a hostgroup by using the location
        name and hostgroup name
        @assert: hostgroup is added to location
        """

        strategy, value = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_hostgroup(session, name=host_grp)
            self.assertIsNotNone(self.hostgroup.search(host_grp))
            self.location.update(loc_name, new_hostgroups=[host_grp])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_hostgrps"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % host_grp))
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_org_1(self, org):
        """
        @feature: Locations
        @test: Add a organization by using the location
        name
        @assert: organization is added to location
        """

        strategy, value = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_org(session, org_name=org)
            self.assertIsNotNone(self.org.search(org))
            self.location.update(loc_name, new_organizations=[org])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_organizations"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % org))
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_environment_1(self, env):
        """
        @feature: Locations
        @test: Add environment by using location name and evironment name
        @assert: environment is added
        """

        strategy, value = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_env(session, name=env, orgs=None)
            self.assertIsNotNone(self.environment.search(env))
            self.location.update(loc_name, new_envs=[env])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_env"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % env))
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_computeresource_1(self, resource_name):
        """
        @feature: Locations
        @test: Add compute resource using the location
        name and computeresource name
        @assert: computeresource is added
        """

        strategy, value = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_resource(session, name=resource_name, orgs=None,
                          provider_type="Libvirt", url=url)
            self.assertIsNotNone(self.compute_resource.search(resource_name))
            self.location.update(loc_name, new_resources=[resource_name])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_resources"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % resource_name))
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_medium_1(self, medium):
        """
        @feature: Locations
        @test: Add medium by using the location name and medium name
        @assert: medium is added
        """

        strategy, value = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        path = URL % generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_media(session, name=medium, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(medium))
            self.location.update(loc_name, new_medias=[medium])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_media"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % medium))
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_configtemplate_1(self, template):
        """
        @feature: Locations
        @test: Add config template by using location name and
        configtemplate name
        @assert: configtemplate is added
        """

        strategy, value = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_templates(session, name=template, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(template))
            self.location.update(loc_name, new_templates=[template])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_template"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % template))
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_remove_environment_1(self, env):
        """
        @feature: Locations
        @test: Remove environment by using location name & evironment name
        @assert: environment is removed from Location
        """

        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_env(session, name=env, orgs=None)
            self.assertIsNotNone(self.environment.search(env))
            make_loc(session, name=loc_name, envs=[env], edit=True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_env"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % env))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertTrue(element)
            self.location.update(loc_name, envs=[env])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_env"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % env))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertTrue(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_remove_subnet_1(self, subnet_name):
        """
        @feature: Locations
        @test: Remove subnet by using location name and subnet name
        @assert: subnet is added then removed
        """

        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        loc_name = generate_string("alpha", 8)
        subnet_network = generate_ipaddr(ip3=True)
        subnet_mask = "255.255.255.0"
        with Session(self.browser) as session:
            make_subnet(session, subnet_name=subnet_name,
                        subnet_network=subnet_network, subnet_mask=subnet_mask)
            self.assertIsNotNone(self.subnet.search_subnet(subnet_name))
            make_loc(session, name=loc_name, subnets=[subnet_name], edit=True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_subnets"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % subnet_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertTrue(element)
            self.location.update(loc_name, subnets=[subnet_name])
            self.location.search(loc_name).click()
            self.location.wait_until_element(
                tab_locators["context.tab_subnets"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % subnet_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertTrue(element)
