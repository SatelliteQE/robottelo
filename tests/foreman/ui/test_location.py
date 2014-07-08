# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

# pylint: disable=R0904

"""
Test class for Locations UI
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
from robottelo.ui.factory import (make_loc, make_subnet, make_domain,
                                  make_user, make_org, make_hostgroup)
from robottelo.ui.locators import common_locators, tab_locators, locators
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

    @attr('ui', 'location', 'implemented')
    @data(*generate_strings_list())
    def test_add_subnet_1(self):
        """
        @feature: Locations
        @test: Add a subnet by using location name and subnet name
        @assert: subnet is added
        """
        subnet_name = "fed121"
        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
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

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
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

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
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

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
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

        strategy = common_locators["entity_deselect"][0]
        value = common_locators["entity_deselect"][1]
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
