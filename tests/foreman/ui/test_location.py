# -*- encoding: utf-8 -*-
# pylint: disable=R0904
"""Test class for Locations UI"""

from ddt import ddt
from fauxfactory import gen_ipaddr, gen_string
from nailgun import entities
from robottelo.common import conf
from robottelo.common.decorators import (
    bz_bug_is_open,
    data,
    run_only_on,
    skip_if_bug_open,
)
from robottelo.common.constants import (
    ANY_CONTEXT,
    INSTALL_MEDIUM_URL,
    LIBVIRT_RESOURCE_URL,
    OS_TEMPLATE_DATA_FILE,
)
from robottelo.common.helpers import generate_strings_list, get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_loc, make_templates, set_context
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class Location(UITestCase):
    """Implements Location tests in UI"""
    location = None

    # Auto Search

    @skip_if_bug_open('bugzilla', 1177610)
    def test_auto_search(self):
        """@test: Can auto-complete search for location by partial name

        @feature: Locations

        @assert: Created location can be auto search by its partial name

        @BZ: 1177610

        """
        loc_name = gen_string('alpha')
        with Session(self.browser) as session:
            page = session.nav.go_to_loc
            make_loc(session, name=loc_name)
            auto_search = self.location.auto_complete_search(
                page,
                locators['location.select_name'],
                loc_name[:3],
                loc_name,
                search_key='name'
            )
            self.assertIsNotNone(auto_search)

    # Positive Create

    @data(*generate_strings_list())
    def test_positive_create_with_different_names(self, loc_name):
        """@test: Create Location with valid name only

        @feature: Locations

        @assert: Location is created, label is auto-generated

        """
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))

    @data(*generate_strings_list(len1=247))
    def test_negative_create_with_too_long_names(self, loc_name):
        """@test: Create location with name as too long

        @feature: Locations

        @assert: location is not created

        """
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @data('', '  ')
    def test_negative_create_with_blank_name(self, loc_name):
        """@test: Create location with name as blank

        @feature: Locations

        @assert: location is not created

        """
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    def test_negative_create_with_same_name(self):
        """@test: Create location with valid values, then create a new one
        with same values.

        @feature: Locations

        @assert: location is not created

        """
        loc_name = gen_string('utf8')
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @data({'org_name': gen_string('alpha', 10),
           'loc_name': gen_string('alpha', 10)},
          {'org_name': gen_string('numeric', 10),
           'loc_name': gen_string('numeric', 10)},
          {'org_name': gen_string('alphanumeric', 10),
           'loc_name': gen_string('alphanumeric', 10)},
          {'org_name': gen_string('utf8', 10),
           'loc_name': gen_string('utf8', 10)},
          {'org_name': gen_string('latin1', 20),
           'loc_name': gen_string('latin1', 10)},
          {'org_name': gen_string('html', 20),
           'loc_name': gen_string('html', 10)})
    def test_positive_create_with_location_and_org(self, test_data):
        """@test: Select both organization and location.

        @feature: Locations

        @assert: Both organization and location are selected.

        """
        org_name = test_data['org_name']
        loc_name = test_data['loc_name']
        org = entities.Organization(name=org_name).create()
        self.assertEqual(org.name, org_name)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            location = session.nav.go_to_select_loc(loc_name)
            organization = session.nav.go_to_select_org(org_name)
            self.assertEqual(location, loc_name)
            self.assertEqual(organization, org_name)

    # Positive Update

    @data(*generate_strings_list())
    def test_positive_update_with_different_names(self, new_name):
        """@test: Create Location with valid values then update its name

        @feature: Locations

        @assert: Location name is updated

        """
        loc_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_name=new_name)
            self.assertIsNotNone(self.location.search(new_name))

    # Negative Update

    def test_negative_update_with_too_long_name(self):
        """@test: Create Location with valid values then fail to update
        its name

        @feature: Locations

        @assert: Location name is not updated

        """
        loc_name = gen_string('alphanumeric')
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            new_name = gen_string('alpha', 247)
            self.location.update(loc_name, new_name=new_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @data(*generate_strings_list())
    def test_positive_delete(self, loc_name):
        """@test: Create location with valid values then delete it.

        @feature: Location Positive Delete test.

        @assert: Location is deleted

        """
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.delete(loc_name)
            self.assertIsNone(self.location.search(loc_name))

    @data(*generate_strings_list())
    def test_add_subnet(self, subnet_name):
        """@test: Add a subnet by using location name and subnet name

        @feature: Locations

        @assert: subnet is added

        """
        strategy, value = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        subnet = entities.Subnet(
            name=subnet_name,
            network=gen_ipaddr(ip3=True),
            mask='255.255.255.0',
        ).create()
        self.assertEqual(subnet.name, subnet_name)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_subnets=[subnet_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_subnets'])
            element = session.nav.wait_until_element(
                (strategy, value % subnet_name))
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_add_domain(self, domain_name):
        """@test: Add a domain to a Location

        @feature: Locations

        @assert: Domain is added to Location

        """
        strategy, value = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        domain = entities.Domain(name=domain_name).create()
        self.assertEqual(domain.name, domain_name)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_domains=[domain_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_domains'])
            element = session.nav.wait_until_element(
                (strategy, value % domain_name))
            self.assertIsNotNone(element)

    @data(
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
        gen_string('utf8'),
        gen_string('latin1')
    )
    def test_add_user(self, user_name):
        """@test: Create user then add that user by using the location name

        @feature: Locations

        @assert: User is added to location

        """
        strategy, value = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        password = gen_string('alpha')
        user = entities.User(
            login=user_name,
            firstname=user_name,
            lastname=user_name,
            password=password,
        ).create()
        self.assertEqual(user.login, user_name)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_users=[user_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_users'])
            element = session.nav.wait_until_element(
                (strategy, value % user_name))
            self.assertIsNotNone(element)

    def test_allvalues_hostgroup(self):
        """@test: check whether host group has the 'All values' checked.

        @feature: Locations

        @assert: host group 'All values' checkbox is checked.

        """
        loc_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            selected = self.location.check_all_values(
                session.nav.go_to_loc,
                loc_name,
                locators['location.select_name'],
                tab_locators['context.tab_hostgrps'],
                context='location',
            )
            self.assertIsNotNone(selected)

    @data(*generate_strings_list())
    def test_add_hostgroup(self, host_grp_name):
        """@test: Add a hostgroup by using the location name and hostgroup name

        @feature: Locations

        @assert: hostgroup is added to location

        """
        strategy, value = common_locators['all_values_selection']
        loc_name = gen_string('alpha')
        host_grp = entities.HostGroup(name=host_grp_name).create()
        self.assertEqual(host_grp.name, host_grp_name)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_hostgrps'])
            element = session.nav.wait_until_element(
                (strategy, value % host_grp_name))
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_add_org(self, org_name):
        """@test: Add a organization by using the location name

        @feature: Locations

        @assert: organization is added to location

        """
        strategy, value = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        org = entities.Organization(name=org_name).create()
        self.assertEqual(org.name, org_name)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_organizations=[org_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_organizations'])
            element = session.nav.wait_until_element(
                (strategy, value % org_name))
            self.assertIsNotNone(element)

    @data(
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric')
    )
    def test_add_environment(self, env_name):
        """@test: Add environment by using location name and environment name

        @feature: Locations

        @assert: environment is added

        """
        strategy, value = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        env = entities.Environment(name=env_name).create()
        self.assertEqual(env.name, env_name)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_envs=[env_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_env'])
            element = session.nav.wait_until_element(
                (strategy, value % env_name))
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_add_computeresource(self, resource_name):
        """@test: Add compute resource using the location name and
        compute resource name

        @feature: Locations

        @assert: compute resource is added successfully

        """
        strategy, value = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        url = (LIBVIRT_RESOURCE_URL % conf.properties['main.server.hostname'])
        resource = entities.LibvirtComputeResource(
            name=resource_name, url=url).create()
        self.assertEqual(resource.name, resource_name)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_resources=[resource_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_resources'])
            element = session.nav.wait_until_element(
                (strategy, value % resource_name))
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_add_medium(self, medium_name):
        """@test: Add medium by using the location name and medium name

        @feature: Locations

        @assert: medium is added

        """
        strategy, value = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        medium = entities.Media(
            name=medium_name,
            path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
            os_family='Redhat',
        ).create()
        self.assertEqual(medium.name, medium_name)
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            self.location.update(loc_name, new_medias=[medium_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_media'])
            element = session.nav.wait_until_element(
                (strategy, value % medium_name))
            self.assertIsNotNone(element)

    def test_allvalues_configtemplate(self):
        """@test: check whether config template has the 'All values' checked.

        @feature: Locations

        @assert: configtemplate 'All values' checkbox is checked.

        """
        loc_name = gen_string('alpha')
        with Session(self.browser) as session:
            page = session.nav.go_to_loc
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            selected = self.location.check_all_values(
                page, loc_name, locators['location.select_name'],
                tab_locators['context.tab_template'], context='location')
            self.assertIsNotNone(selected)

    @data(*generate_strings_list())
    def test_add_configtemplate(self, template):
        """@test: Add config template by using location name and config
        template name.

        @feature: Locations

        @assert: config template is added.

        """
        strategy, value = common_locators['all_values_selection']
        loc_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_templates(
                session,
                name=template,
                template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                custom_really=True,
                template_type='provision',
            )
            self.assertIsNotNone(self.template.search(template))
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_template'])
            element = session.nav.wait_until_element(
                (strategy, value % template))
            self.assertIsNotNone(element)

    @data(
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric')
    )
    def test_remove_environment(self, env_name):
        """@test: Remove environment by using location name & environment name

        @feature: Locations

        @assert: environment is removed from Location

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        env = entities.Environment(name=env_name).create()
        self.assertEqual(env.name, env_name)
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_loc(session, name=loc_name, envs=[env_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_env'])
            element = session.nav.wait_until_element(
                (strategy1, value1 % env_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.location.update(loc_name, envs=[env_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_env'])
            element = session.nav.wait_until_element(
                (strategy, value % env_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_remove_subnet(self, subnet_name):
        """@test: Remove subnet by using location name and subnet name

        @feature: Locations

        @assert: subnet is added then removed

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        subnet = entities.Subnet(
            name=subnet_name,
            network=gen_ipaddr(ip3=True),
            mask='255.255.255.0',
        ).create()
        self.assertEqual(subnet.name, subnet_name)
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_loc(session, name=loc_name, subnets=[subnet_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_subnets'])
            element = session.nav.wait_until_element(
                (strategy1, value1 % subnet_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.location.update(loc_name, subnets=[subnet_name])
            self.location.search(loc_name).click()
            self.location.click(tab_locators['context.tab_subnets'])
            element = session.nav.wait_until_element(
                (strategy, value % subnet_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_remove_domain(self, domain_name):
        """@test: Add a domain to an location and remove it by location name
        and domain name

        @feature: Locations

        @assert: the domain is removed from the location

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        domain = entities.Domain(name=domain_name).create()
        self.assertEqual(domain.name, domain_name)
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_loc(session, name=loc_name, domains=[domain_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_domains'])
            element = session.nav.wait_until_element(
                (strategy1, value1 % domain_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.location.update(loc_name, domains=[domain_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_domains'])
            element = session.nav.wait_until_element(
                (strategy, value % domain_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @data(
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
        gen_string('utf8'),
        gen_string('latin1')
    )
    def test_remove_user(self, user_name):
        """@test: Create admin users then add user and remove it by using the
        location name

        @feature: Locations

        @assert: The user is added then removed from the location

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        user = entities.User(
            login=user_name,
            firstname=user_name,
            lastname=user_name,
            password=gen_string('alpha'),
        ).create()
        self.assertEqual(user.login, user_name)
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_loc(session, name=loc_name, users=[user_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_users'])
            element = session.nav.wait_until_element(
                (strategy1, value1 % user_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.location.update(loc_name, users=[user_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_users'])
            element = session.nav.wait_until_element(
                (strategy, value % user_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_remove_hostgroup(self, host_grp_name):
        """@test: Add a hostgroup and remove it by using the location name and
        hostgroup name

        @feature: Locations

        @assert: hostgroup is added to location then removed

        """
        strategy, value = common_locators['all_values_selection']
        loc_name = gen_string('alpha')
        host_grp = entities.HostGroup(name=host_grp_name).create()
        self.assertEqual(host_grp.name, host_grp_name)
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_loc(session, name=loc_name)
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_hostgrps'])
            element = session.nav.wait_until_element(
                (strategy, value % host_grp_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.hostgroup.delete(host_grp_name, True)
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_hostgrps'])
            element = session.nav.wait_until_element(
                (strategy, value % host_grp_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNone(element)

    @data(*generate_strings_list())
    def test_remove_computeresource(self, resource_name):
        """@test: Remove compute resource by using the location name and
        compute resource name

        @feature: Locations

        @assert: compute resource is added then removed

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        url = (LIBVIRT_RESOURCE_URL % conf.properties['main.server.hostname'])
        resource = entities.LibvirtComputeResource(
            name=resource_name, url=url).create()
        self.assertEqual(resource.name, resource_name)
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_loc(session, name=loc_name, resources=[resource_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_resources'])
            element = self.location.wait_until_element(
                (strategy1, value1 % resource_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.location.update(loc_name, resources=[resource_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_resources'])
            element = session.nav.wait_until_element(
                (strategy, value % resource_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @data(*generate_strings_list())
    def test_remove_medium(self, medium_name):
        """@test: Remove medium by using location name and medium name

        @feature: Locations

        @assert: medium is added then removed

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        loc_name = gen_string('alpha')
        medium = entities.Media(
            name=medium_name,
            path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
            os_family='Redhat',
        ).create()
        self.assertEqual(medium.name, medium_name)
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_loc(session, name=loc_name, medias=[medium_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_media'])
            element = session.nav.wait_until_element(
                (strategy1, value1 % medium_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.location.update(loc_name, medias=[medium_name])
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_media'])
            element = session.nav.wait_until_element(
                (strategy, value % medium_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @data(
        {u'user_name': gen_string('alpha', 8)},
        {u'user_name': gen_string('numeric', 8)},
        {u'user_name': gen_string('alphanumeric', 8)},
        {u'user_name': gen_string('utf8', 8), 'bugzilla': 1164247},
        {u'user_name': gen_string('latin1', 8)},
        {u'user_name': gen_string('html', 8)},)
    def test_remove_configtemplate(self, testdata):
        """
        @test: Remove config template

        @feature: Locations

        @assert: config template is added and then removed

        """
        bug_id = testdata.pop('bugzilla', None)
        if bug_id is not None and bz_bug_is_open(bug_id):
            self.skipTest('Bugzilla bug {0} is open.'.format(bug_id))

        template = testdata['user_name']
        strategy, value = common_locators['all_values_selection']
        loc_name = gen_string('alpha')
        with Session(self.browser) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_templates(
                session,
                name=template,
                template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                template_type='provision',
                custom_really=True,
            )
            self.assertIsNotNone(self.template.search(template))
            make_loc(session, name=loc_name)
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_template'])
            element = session.nav.wait_until_element(
                (strategy, value % template))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.template.delete(template)
            self.location.search(loc_name).click()
            session.nav.click(tab_locators['context.tab_template'])
            element = session.nav.wait_until_element(
                (strategy, value % template))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNone(element)
