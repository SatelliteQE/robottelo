# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

# pylint: disable=R0904
"""Test class for Locations UI"""

from ddt import ddt
from fauxfactory import FauxFactory
from nose.plugins.attrib import attr
from robottelo.common import conf
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.common.helpers import (
    generate_strings_list, generate_ipaddr, generate_email_address,
    get_data_file)
from robottelo.common.constants import OS_TEMPLATE_DATA_FILE
from robottelo.test import UITestCase
from robottelo.ui.factory import (
    make_loc, make_subnet, make_domain, make_env, make_user, make_org,
    make_hostgroup, make_resource, make_media, make_templates)
from robottelo.ui.locators import common_locators, tab_locators, locators
from robottelo.ui.session import Session


URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"


@ddt
class Location(UITestCase):
    """Implements Location tests in UI"""

    # Auto Search

    def test_auto_search(self):
        """@test: Can auto-complete search for location by partial name

        @feature: Locations

        @assert: Created location can be auto search by its partial name

        """
        loc_name = FauxFactory.generate_string("alpha", 8)
        part_string = loc_name[:3]
        with Session(self.browser) as session:
            page = session.nav.go_to_loc
            make_loc(session, name=loc_name)
            auto_search = self.location.auto_complete_search(
                page, locators['location.select_name'], part_string,
                loc_name, search_key='name')
            self.assertIsNotNone(auto_search)

    # Positive Create

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_positive_create_1(self, loc_name):
        """@test: Create Location with valid name only

        @feature: Locations

        @assert: Location is created, label is auto-generated

        """

        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))

    @skip_if_bug_open('bugzilla', 1123818)
    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list(len1=247))
    def test_negative_create_1(self, loc_name):
        """@test: Create location with name as too long

        @feature: Locations

        @assert: location is not created

        @BZ: 1123818

        """
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_negative_create_2(self):
        """@test: Create location with name as blank

        @feature: Locations

        @assert: location is not created

        """

        loc_name = ""
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_negative_create_3(self):
        """@test: Create location with name as whitespace

        @feature: Locations

        @assert: location is not created

        """

        loc_name = "    "
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_negative_create_4(self, loc_name):
        """@test: Create location with valid values, then create a new one
        with same values.

        @feature: Locations

        @assert: location is not created

        """

        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    # Positive Update

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_positive_update_1(self, new_name):
        """@test: Create Location with valid values then update its name

        @feature: Locations

        @assert: Location name is updated

        """

        loc_name = FauxFactory.generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_name=new_name)
            self.assertIsNotNone(self.location.search(new_name))

    # Negative Update

    @skip_if_bug_open('bugzilla', 1123818)
    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_negative_update_1(self, loc_name):
        """@test: Create Location with valid values then fail to update
        its name

        @feature: Locations

        @assert: Location name is not updated

        @BZ: 1123818

        """

        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            new_name = FauxFactory.generate_string("alpha", 256)
            self.location.update(loc_name, new_name=new_name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    # Miscellaneous

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_search_key_1(self, loc_name):
        """@test: Create location and search/find it

        @feature: Locations

        @assert: location can be found

        """
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_subnet_1(self, subnet_name):
        """@test: Add a subnet by using location name and subnet name

        @feature: Locations

        @assert: subnet is added

        """
        strategy, value = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
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
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_domain_1(self, domain):
        """@test: Add a domain to a Location

        @feature: Locations

        @assert: Domain is added to Location

        """
        strategy, value = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
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
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data({'name': FauxFactory.generate_string('alpha', 8)},
          {'name': FauxFactory.generate_string('numeric', 8)},
          {'name': FauxFactory.generate_string('alphanumeric', 8)},
          {'name': FauxFactory.generate_string('utf8', 8)},
          {'name': FauxFactory.generate_string('latin1', 8)})
    def test_add_user_1(self, testdata):
        """@test: Create user then add user
        by using the location name

        @feature: Locations

        @assert: User is added to location

        """
        user = testdata['name']
        strategy, value = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        password = FauxFactory.generate_string("alpha", 8)
        email = generate_email_address()
        search_key = "login"
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_user(session, username=user, first_name=user,
                      last_name=user, email=email,
                      password1=password, password2=password)
            self.assertIsNotNone(self.user.search(user, search_key))
            self.location.update(loc_name, new_users=[user])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_users"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % user))
            self.assertIsNotNone(element)

    def test_allvalues_hostgroup(self):
        """@test: check whether host group has the 'All values' checked.

        @feature: Locations

        @assert: host group 'All values' checkbox is checked.

        """
        loc_name = FauxFactory.generate_string("alpha", 8)
        with Session(self.browser) as session:
            page = session.nav.go_to_loc
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            selected = self.location.check_all_values(
                page, loc_name, locators["location.select_name"],
                tab_locators["context.tab_hostgrps"], context="location")
            self.assertIsNotNone(selected)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_hostgroup_1(self, host_grp):
        """@test: Add a hostgroup by using the location
        name and hostgroup name

        @feature: Locations

        @assert: hostgroup is added to location

        """
        strategy, value = common_locators["all_values_selection"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_hostgroup(session, name=host_grp)
            self.assertIsNotNone(self.hostgroup.search(host_grp))
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_hostgrps"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % host_grp))
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_org_1(self, org):
        """@test: Add a organization by using the location
        name

        @feature: Locations

        @assert: organization is added to location

        """
        strategy, value = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
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
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data({'name': FauxFactory.generate_string('alpha', 8)},
          {'name': FauxFactory.generate_string('numeric', 8)},
          {'name': FauxFactory.generate_string('alphanumeric', 8)})
    def test_add_environment_1(self, testdata):
        """@test: Add environment by using location name and evironment name

        @feature: Locations

        @assert: environment is added

        """
        env = testdata['name']
        strategy, value = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_env(session, name=env)
            self.assertIsNotNone(self.environment.search(env))
            self.location.update(loc_name, new_envs=[env])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_env"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % env))
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_computeresource_1(self, resource_name):
        """@test: Add compute resource using the location
        name and computeresource name

        @feature: Locations

        @assert: computeresource is added

        """
        strategy, value = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_resource(session, name=resource_name,
                          provider_type="Libvirt", url=url)
            self.assertIsNotNone(self.compute_resource.search(resource_name))
            self.location.update(loc_name, new_resources=[resource_name])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_resources"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % resource_name))
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_medium_1(self, medium):
        """@test: Add medium by using the location name and medium name

        @feature: Locations

        @assert: medium is added

        """
        strategy, value = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        path = URL % FauxFactory.generate_string("alpha", 6)
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
            self.assertIsNotNone(element)

    def test_allvalues_configtemplate(self):
        """@test: check whether config template has the 'All values' checked.

        @feature: Locations

        @assert: configtemplate 'All values' checkbox is checked.

        """
        loc_name = FauxFactory.generate_string("alpha", 8)
        with Session(self.browser) as session:
            page = session.nav.go_to_loc
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            selected = self.location.check_all_values(
                page, loc_name, locators["location.select_name"],
                tab_locators["context.tab_template"], context="location")
            self.assertIsNotNone(selected)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_configtemplate_1(self, template):
        """@test: Add config template by using location name and
        configtemplate name.

        @feature: Locations

        @assert: configtemplate is added.

        """
        strategy, value = common_locators["all_values_selection"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_templates(session, name=template, template_path=template_path,
                           custom_really=True, template_type=temp_type)
            self.assertIsNotNone(self.template.search(template))
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_template"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % template))
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data({'name': FauxFactory.generate_string('alpha', 8)},
          {'name': FauxFactory.generate_string('numeric', 8)},
          {'name': FauxFactory.generate_string('alphanumeric', 8)})
    def test_remove_environment_1(self, testdata):
        """@test: Remove environment by using location name & evironment name

        @feature: Locations

        @assert: environment is removed from Location

        """
        env = testdata['name']
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
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
            self.assertIsNotNone(element)
            self.location.update(loc_name, envs=[env])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_env"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % env))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_remove_subnet_1(self, subnet_name):
        """@test: Remove subnet by using location name and subnet name

        @feature: Locations

        @assert: subnet is added then removed

        """
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
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
            self.assertIsNotNone(element)
            self.location.update(loc_name, subnets=[subnet_name])
            self.location.search(loc_name).click()
            self.location.wait_until_element(
                tab_locators["context.tab_subnets"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % subnet_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_remove_domain_1(self, domain):
        """@test: Add a domain to an location and remove it by location
        name and domain name

        @feature: Locations

        @assert: the domain is removed from the location

        """

        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_domain(session, name=domain)
            self.assertIsNotNone(self.domain.search(domain))
            make_loc(session, name=loc_name, domains=[domain], edit=True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_domains"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % domain))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.location.update(loc_name, domains=[domain])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_domains"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % domain))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data({'name': FauxFactory.generate_string('alpha', 8)},
          {'name': FauxFactory.generate_string('numeric', 8)},
          {'name': FauxFactory.generate_string('alphanumeric', 8)},
          {'name': FauxFactory.generate_string('utf8', 8)},
          {'name': FauxFactory.generate_string('latin1', 8)})
    def test_remove_user_1(self, testdata):
        """@test: Create admin users then add user and remove it
        by using the location name

        @feature: Locations

        @assert: The user is added then removed from the location

        """
        user_name = testdata['name']
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        password = FauxFactory.generate_string("alpha", 8)
        email = generate_email_address()
        search_key = "login"
        with Session(self.browser) as session:
            make_user(session, username=user_name, first_name=user_name,
                      last_name=user_name, email=email,
                      password1=password, password2=password)
            self.assertIsNotNone(self.user.search(user_name, search_key))
            make_loc(session, name=loc_name, users=[user_name], edit=True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_users"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % user_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.location.update(loc_name, users=[user_name])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_users"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % user_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_remove_hostgroup_1(self, host_grp):
        """@test: Add a hostgroup and remove it by using the location
        name and hostgroup name

        @feature: Locations

        @assert: hostgroup is added to location then removed

        """
        strategy, value = common_locators["all_values_selection"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_hostgroup(session, name=host_grp)
            self.assertIsNotNone(self.hostgroup.search(host_grp))
            make_loc(session, name=loc_name, edit=True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_hostgrps"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % host_grp))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.hostgroup.delete(host_grp, True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_hostgrps"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % host_grp))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNone(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_remove_computeresource_1(self, resource_name):
        """@test: Remove computeresource by using the location
        name and computeresource name

        @feature: Locations

        @assert: computeresource is added then removed

        """
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        libvirt_url = "qemu+tcp://%s:16509/system"
        url = (libvirt_url % conf.properties['main.server.hostname'])
        with Session(self.browser) as session:
            make_resource(session, name=resource_name, provider_type="Libvirt",
                          url=url)
            self.assertIsNotNone(self.compute_resource.search(resource_name))
            make_loc(session, name=loc_name, resources=[resource_name],
                     edit=True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_resources"]).click()
            ele = self.location.wait_until_element((strategy1,
                                                    value1 % resource_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(ele)
            self.location.update(loc_name, resources=[resource_name])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_resources"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % resource_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_remove_medium_1(self, medium):
        """@test: Remove medium by using location name and medium name

        @feature: Locations

        @assert: medium is added then removed

        """
        strategy, value = common_locators["entity_select"]
        strategy1, value1 = common_locators["entity_deselect"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        path = URL % FauxFactory.generate_string("alpha", 6)
        os_family = "Red Hat"
        with Session(self.browser) as session:
            make_media(session, name=medium, path=path, os_family=os_family)
            self.assertIsNotNone(self.medium.search(medium))
            make_loc(session, name=loc_name, medias=[medium], edit=True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_media"]).click()
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % medium))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.location.update(loc_name, medias=[medium])
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_media"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % medium))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @skip_if_bug_open('bugzilla', 1096333)
    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_remove_configtemplate_1(self, template):
        """@test: Remove config template

        @feature: Locations

        @assert: configtemplate is added then removed

        @BZ: 1096333

        """
        strategy, value = common_locators["all_values_selection"]
        loc_name = FauxFactory.generate_string("alpha", 8)
        temp_type = 'provision'
        template_path = get_data_file(OS_TEMPLATE_DATA_FILE)
        with Session(self.browser) as session:
            make_templates(session, name=template, template_path=template_path,
                           template_type=temp_type, custom_really=True)
            self.assertIsNotNone(self.template.search(template))
            make_loc(session, name=loc_name, edit=True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_template"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % template))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.template.delete(template, True)
            self.location.search(loc_name).click()
            session.nav.wait_until_element(
                tab_locators["context.tab_template"]).click()
            element = session.nav.wait_until_element((strategy,
                                                      value % template))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNone(element)
