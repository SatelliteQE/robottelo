# -*- encoding: utf-8 -*-
"""Test class for Locations UI

:Requirement: Location

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_ipaddr, gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.datafactory import (
    filtered_datapoint,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.decorators import (
    run_only_on,
    skip_if_bug_open,
    skip_if_not_set,
    tier1,
    tier2,
    upgrade,
)
from robottelo.constants import (
    ANY_CONTEXT,
    DEFAULT_ORG,
    INSTALL_MEDIUM_URL,
    LIBVIRT_RESOURCE_URL,
    OS_TEMPLATE_DATA_FILE,
)
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_loc, make_templates, set_context
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_org_loc_data():
    """Returns a list of valid org/location data"""
    return [
        {'org_name': gen_string('alpha', 242),
         'loc_name': gen_string('alpha', 242)},
        {'org_name': gen_string('numeric', 242),
         'loc_name': gen_string('numeric', 242)},
        {'org_name': gen_string('alphanumeric', 242),
         'loc_name': gen_string('alphanumeric', 242)},
        {'org_name': gen_string('utf8', 80),
         'loc_name': gen_string('utf8', 80)},
        {'org_name': gen_string('latin1', 242),
         'loc_name': gen_string('latin1', 242)},
        {'org_name': gen_string('html', 217),
         'loc_name': gen_string('html', 217)}
    ]


@filtered_datapoint
def valid_env_names():
    """Returns a list of valid environment names"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    ]


class LocationTestCase(UITestCase):
    """Implements Location tests in UI"""
    location = None

    @classmethod
    def setUpClass(cls):
        """Set up an organization for tests."""
        super(LocationTestCase, cls).setUpClass()
        cls.org_ = entities.Organization().search(query={
            'search': 'name="{0}"'.format(DEFAULT_ORG)
        })[0]

    # Auto Search

    @run_only_on('sat')
    @tier1
    def test_positive_auto_search(self):
        """Can auto-complete search for location by partial name

        :id: 6aaf104b-481a-4dd9-8639-8ddb1e4d6828

        :expectedresults: Created location can be auto search by its partial
            name

        :CaseImportance: Critical
        """
        loc_name = gen_string('alpha')
        with Session(self) as session:
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

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create Location with valid name only

        :id: 92b23082-09e4-49e1-92e1-d6d89d5180ac

        :expectedresults: Location is created, label is auto-generated

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for loc_name in generate_strings_list():
                with self.subTest(loc_name):
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_names(self):
        """Create location with invalid name

        :id: 85f05458-b86c-4d94-a412-ea03412c4588

        :expectedresults: location is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for loc_name in invalid_values_list(interface='ui'):
                with self.subTest(loc_name):
                    make_loc(session, name=loc_name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Create location with valid values, then create a new one with same
        values.

        :id: 33983f00-406b-4289-b9e2-ffe6901bf99d

        :expectedresults: location is not created

        :CaseImportance: Critical
        """
        loc_name = gen_string('utf8')
        with Session(self) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            make_loc(session, name=loc_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @run_only_on('sat')
    @tier2
    def test_positive_create_with_location_and_org(self):
        """Create and select both organization and location.

        :id: a1640ada-d4e9-447e-9e1b-40d17e1ede7e

        :expectedresults: Both organization and location are selected.

        :CaseLevel: Integration
        """
        with Session(self) as session:
            for test_data in valid_org_loc_data():
                with self.subTest(test_data):
                    org_name = test_data['org_name']
                    loc_name = test_data['loc_name']
                    org = entities.Organization(name=org_name).create()
                    self.assertEqual(org.name, org_name)
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    location = session.nav.go_to_select_loc(loc_name)
                    organization = session.nav.go_to_select_org(org_name)
                    self.assertEqual(location, loc_name)
                    self.assertEqual(organization, org_name)

    # Positive Update

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Create Location with valid values then update its name

        :id: 79d8dbbb-9b7f-4482-a0f5-4fe72713d575

        :expectedresults: Location name is updated

        :CaseImportance: Critical
        """
        loc_name = gen_string('alpha')
        with Session(self) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.location.update(loc_name, new_name=new_name)
                    self.assertIsNotNone(self.location.search(new_name))
                    loc_name = new_name  # for next iteration

    # Negative Update

    @run_only_on('sat')
    @tier1
    def test_negative_update_with_too_long_name(self):
        """Create Location with valid values then fail to update
        its name

        :id: 57fed455-47f0-4b7c-a58e-3d8f6d761da9

        :expectedresults: Location name is not updated

        :CaseImportance: Critical
        """
        loc_name = gen_string('alphanumeric')
        with Session(self) as session:
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            new_name = gen_string('alpha', 247)
            self.location.update(loc_name, new_name=new_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create location with valid values then delete it.

        :id: b7664152-9398-499c-b165-3107f4350ba4

        :expectedresults: Location is deleted

        :CaseImportance: Critical
        """
        with Session(self):
            for loc_name in generate_strings_list():
                with self.subTest(loc_name):
                    entities.Location(name=loc_name).create()
                    self.location.delete(loc_name, dropdown_present=True)

    @run_only_on('sat')
    @tier2
    def test_positive_add_subnet(self):
        """Add a subnet by using location name and subnet name

        :id: fe70ffba-e594-48d5-b2c5-be93e827cc60

        :expectedresults: subnet is added

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self) as session:
            for subnet_name in generate_strings_list():
                with self.subTest(subnet_name):
                    loc_name = gen_string('alpha')
                    subnet = entities.Subnet(
                        name=subnet_name,
                        network=gen_ipaddr(ip3=True),
                        mask='255.255.255.0',
                    ).create()
                    self.assertEqual(subnet.name, subnet_name)
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    self.location.update(loc_name, new_subnets=[subnet_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_subnets'])
                    element = session.nav.wait_until_element(
                        (strategy, value % subnet_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_domain(self):
        """Add a domain to a Location

        :id: 4f50f5cb-64eb-4790-b4c5-62d67669f48f

        :expectedresults: Domain is added to Location

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self) as session:
            for domain_name in generate_strings_list():
                with self.subTest(domain_name):
                    loc_name = gen_string('alpha')
                    domain = entities.Domain(name=domain_name).create()
                    self.assertEqual(domain.name, domain_name)
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    self.location.update(loc_name, new_domains=[domain_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_domains'])
                    element = session.nav.wait_until_element(
                        (strategy, value % domain_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_user(self):
        """Create user then add that user by using the location name

        :id: bf9b3fc2-6193-4edc-aaec-cd7b87f0804c

        :expectedresults: User is added to location

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self) as session:
            # User names does not accept html values
            for user_name in generate_strings_list(
                    length=10,
                    exclude_types=['html']):
                with self.subTest(user_name):
                    loc_name = gen_string('alpha')
                    password = gen_string('alpha')
                    user = entities.User(
                        login=user_name,
                        firstname=user_name,
                        lastname=user_name,
                        password=password,
                    ).create()
                    self.assertEqual(user.login, user_name)
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    self.location.update(loc_name, new_users=[user_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_users'])
                    element = session.nav.wait_until_element(
                        (strategy, value % user_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1321543)
    @tier2
    def test_positive_update_with_all_users(self):
        """Create location and add user to it. Check and uncheck 'all users'
        setting. Verify that user is assigned to location and vice versa
        location is assigned to user

        :id: 17f85968-4aa6-4e2e-82d9-b01bc17031e7

        :expectedresults: Location and user entities assigned to each other

        :BZ: 1479736

        :CaseLevel: Integration
        """
        loc_name = gen_string('alpha')
        user = entities.User().create()
        with Session(self) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_loc(session, name=loc_name)
            self.location.update(loc_name, new_users=[user.login])
            self.location.search_and_click(loc_name)
            self.location.click(tab_locators['context.tab_users'])
            self.assertIsNotNone(self.location.wait_until_element(
                common_locators['entity_deselect'] % user.login))
            for value in [True, False]:
                self.location.assign_value(
                    locators['location.all_users'], value)
                self.location.click(common_locators['submit'])
                self.user.search_and_click(user.login)
                self.user.click(tab_locators['tab_loc'])
                self.assertIsNotNone(self.user.wait_until_element(
                    common_locators['entity_deselect'] % loc_name))
                self.location.search_and_click(loc_name)
                self.location.click(tab_locators['context.tab_users'])
                self.assertIsNotNone(self.location.wait_until_element(
                    common_locators['entity_deselect'] % user.login))

    @run_only_on('sat')
    @skip_if_bug_open('bugzilla', 1321543)
    @tier2
    def test_positive_update_with_all_users_setting_only(self):
        """Create location and do not add user to it. Check and uncheck
        'all users' setting. Verify that for both operation expected location
        is assigned to user

        :id: 6596962b-8fd0-4a82-bf54-fa6a31147311

        :expectedresults: Location entity is assigned to user after checkbox
            was enabled and then disabled afterwards

        :BZ: 1321543

        :CaseLevel: Integration
        """
        loc_name = gen_string('alpha')
        user = entities.User().create()
        with Session(self) as session:
            set_context(session, org=ANY_CONTEXT['org'])
            make_loc(session, name=loc_name)
            for value in [True, False]:
                self.location.search_and_click(loc_name)
                self.location.click(tab_locators['context.tab_users'])
                self.location.assign_value(
                    locators['location.all_users'], value)
                self.location.click(common_locators['submit'])
                self.user.search_and_click(user.login)
                self.user.click(tab_locators['tab_loc'])
                self.assertIsNotNone(self.user.wait_until_element(
                    common_locators['entity_deselect'] % loc_name))

    @run_only_on('sat')
    @tier1
    def test_positive_check_all_values_hostgroup(self):
        """check whether host group has the 'All values' checked.

        :id: ca2f2522-ba34-4d20-87f4-7777ec9a1282

        :expectedresults: host group 'All values' checkbox is checked.

        :CaseImportance: Critical
        """
        loc_name = gen_string('alpha')
        with Session(self) as session:
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

    @run_only_on('sat')
    @tier2
    def test_positive_add_hostgroup(self):
        """Add a hostgroup by using the location name and hostgroup name

        :id: e998d20c-e201-4675-b45f-8768f59584da

        :expectedresults: hostgroup is added to location

        :CaseLevel: Integration
        """
        strategy, value = common_locators['all_values_selection']
        with Session(self) as session:
            for host_grp_name in generate_strings_list():
                with self.subTest(host_grp_name):
                    loc_name = gen_string('alpha')
                    host_grp = entities.HostGroup(name=host_grp_name).create()
                    self.assertEqual(host_grp.name, host_grp_name)
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_hostgrps'])
                    element = session.nav.wait_until_element(
                        (strategy, value % host_grp_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_org(self):
        """Add a organization by using the location name

        :id: 27d56d64-6866-46b6-962d-1ac2a11ae136

        :expectedresults: organization is added to location

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    loc_name = gen_string('alpha')
                    org = entities.Organization(name=org_name).create()
                    self.assertEqual(org.name, org_name)
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    self.location.update(
                        loc_name, new_organizations=[org_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(
                        tab_locators['context.tab_organizations'])
                    element = session.nav.wait_until_element(
                        (strategy, value % org_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_add_environment(self):
        """Add environment by using location name and environment name

        :id: bbca1af0-a31f-4096-bc6e-bb341ffed575

        :expectedresults: environment is added

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self) as session:
            for env_name in valid_env_names():
                with self.subTest(env_name):
                    loc_name = gen_string('alpha')
                    env = entities.Environment(name=env_name).create()
                    self.assertEqual(env.name, env_name)
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    self.location.update(loc_name, new_envs=[env_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_env'])
                    element = session.nav.wait_until_element(
                        (strategy, value % env_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @skip_if_not_set('compute_resources')
    @tier2
    def test_positive_add_compresource(self):
        """Add compute resource using the location name and compute resource
        name

        :id: 1d24414a-666d-490d-89b9-cd0704684cdd

        :expectedresults: compute resource is added successfully

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self) as session:
            for resource_name in generate_strings_list():
                with self.subTest(resource_name):
                    loc_name = gen_string('alpha')
                    url = (LIBVIRT_RESOURCE_URL %
                           settings.compute_resources.libvirt_hostname)
                    resource = entities.LibvirtComputeResource(
                        name=resource_name, url=url).create()
                    self.assertEqual(resource.name, resource_name)
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    self.location.update(
                        loc_name, new_resources=[resource_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_resources'])
                    element = session.nav.wait_until_element(
                        (strategy, value % resource_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_add_medium(self):
        """Add medium by using the location name and medium name

        :id: 738c5ff1-ef09-466f-aaac-64f194cac78d

        :expectedresults: medium is added

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_deselect']
        with Session(self) as session:
            for medium_name in generate_strings_list():
                with self.subTest(medium_name):
                    loc_name = gen_string('alpha')
                    medium = entities.Media(
                        name=medium_name,
                        path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
                        os_family='Redhat',
                    ).create()
                    self.assertEqual(medium.name, medium_name)
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    self.location.update(loc_name, new_medias=[medium_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_media'])
                    element = session.nav.wait_until_element(
                        (strategy, value % medium_name))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier1
    def test_positive_check_all_values_template(self):
        """check whether config template has the 'All values' checked.

        :id: 358cf1c0-4187-4b5a-b900-5971e708b83f

        :expectedresults: configtemplate 'All values' checkbox is checked.

        :CaseImportance: Critical
        """
        loc_name = gen_string('alpha')
        with Session(self) as session:
            page = session.nav.go_to_loc
            make_loc(session, name=loc_name)
            self.assertIsNotNone(self.location.search(loc_name))
            selected = self.location.check_all_values(
                page, loc_name, locators['location.select_name'],
                tab_locators['context.tab_template'], context='location')
            self.assertIsNotNone(selected)

    @run_only_on('sat')
    @tier2
    def test_positive_add_template(self):
        """Add config template by using location name and config template name.

        :id: 8faf60d1-f4d6-4a58-a484-606a42957ce7

        :expectedresults: config template is added.

        :CaseLevel: Integration
        """
        strategy, value = common_locators['all_values_selection']
        with Session(self) as session:
            for template in generate_strings_list():
                with self.subTest(template):
                    loc_name = gen_string('alpha')
                    make_loc(session, name=loc_name)
                    self.assertIsNotNone(self.location.search(loc_name))
                    make_templates(
                        session,
                        name=template,
                        template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                        custom_really=True,
                        template_type='Provisioning template',
                    )
                    self.assertIsNotNone(self.template.search(template))
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_template'])
                    element = session.nav.wait_until_element(
                        (strategy, value % template))
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_environment(self):
        """Remove environment by using location name & environment name

        :id: eaf08f82-d76c-4bd5-bc9b-ac91ca409b81

        :expectedresults: environment is removed from Location

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self) as session:
            for env_name in valid_env_names():
                with self.subTest(env_name):
                    loc_name = gen_string('alpha')
                    env = entities.Environment(
                        name=env_name,
                        organization=[self.org_],
                    ).create()
                    self.assertEqual(env.name, env_name)
                    make_loc(
                        session,
                        envs=[env_name],
                        name=loc_name,
                        organizations=[self.org_.name],
                    )
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_env'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % env_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.location.update(loc_name, envs=[env_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_env'])
                    element = session.nav.wait_until_element(
                        (strategy, value % env_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_subnet(self):
        """Remove subnet by using location name and subnet name

        :id: 53bc28a4-1fe1-4628-b7b9-18ea4b07dfc8

        :expectedresults: subnet is added then removed

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self) as session:
            for subnet_name in generate_strings_list():
                with self.subTest(subnet_name):
                    loc_name = gen_string('alpha')
                    subnet = entities.Subnet(
                        name=subnet_name,
                        network=gen_ipaddr(ip3=True),
                        mask='255.255.255.0',
                    ).create()
                    self.assertEqual(subnet.name, subnet_name)
                    make_loc(
                        session,
                        name=loc_name,
                        organizations=[self.org_.name],
                        subnets=[subnet_name],
                    )
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_subnets'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % subnet_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.location.update(loc_name, subnets=[subnet_name])
                    self.location.search_and_click(loc_name)
                    self.location.click(tab_locators['context.tab_subnets'])
                    element = session.nav.wait_until_element(
                        (strategy, value % subnet_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_domain(self):
        """Add a domain to an location and remove it by location name and
        domain name

        :id: 39374e24-2b38-47f4-b69b-c2b0ca0d754f

        :expectedresults: the domain is removed from the location

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self) as session:
            for domain_name in generate_strings_list():
                with self.subTest(domain_name):
                    loc_name = gen_string('alpha')
                    domain = entities.Domain(
                        name=domain_name,
                        organization=[self.org_],
                    ).create()
                    self.assertEqual(domain.name, domain_name)
                    make_loc(
                        session,
                        domains=[domain_name],
                        name=loc_name,
                        organizations=[self.org_.name],
                    )
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_domains'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % domain_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.location.update(loc_name, domains=[domain_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_domains'])
                    element = session.nav.wait_until_element(
                        (strategy, value % domain_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    @upgrade
    def test_positive_remove_user(self):
        """Create admin users then add user and remove it by using the location
        name

        :id: c2dd189d-c928-4051-ae38-c08a15b95879

        :expectedresults: The user is added then removed from the location

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self) as session:
            # User names does not accept html values
            for user_name in generate_strings_list(
                    length=10,
                    exclude_types=['html']):
                with self.subTest(user_name):
                    loc_name = gen_string('alpha')
                    user = entities.User(
                        login=user_name,
                        firstname=user_name,
                        lastname=user_name,
                        password=gen_string('alpha'),
                    ).create()
                    self.assertEqual(user.login, user_name)
                    make_loc(
                        session,
                        name=loc_name,
                        organizations=[self.org_.name],
                        users=[user_name],
                    )
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_users'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % user_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.location.update(loc_name, users=[user_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_users'])
                    element = session.nav.wait_until_element(
                        (strategy, value % user_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_hostgroup(self):
        """Add a hostgroup and remove it by using the location name and
        hostgroup name

        :id: dd8c58af-3037-44c0-a7f7-5e8337f110c9

        :expectedresults: hostgroup is added to location then removed

        :CaseLevel: Integration
        """
        strategy, value = common_locators['all_values_selection']
        with Session(self) as session:
            for host_grp_name in generate_strings_list():
                with self.subTest(host_grp_name):
                    loc_name = gen_string('alpha')
                    host_grp = entities.HostGroup(
                        name=host_grp_name,
                        organization=[self.org_],
                    ).create()
                    self.assertEqual(host_grp.name, host_grp_name)
                    make_loc(
                        session,
                        name=loc_name,
                        organizations=[self.org_.name],
                    )
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_hostgrps'])
                    element = session.nav.wait_until_element(
                        (strategy, value % host_grp_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.hostgroup.delete(host_grp_name, dropdown_present=True)
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_hostgrps'])
                    element = session.nav.wait_until_element(
                        (strategy, value % host_grp_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNone(element)

    @run_only_on('sat')
    @skip_if_not_set('compute_resources')
    @tier2
    @upgrade
    def test_positive_remove_compresource(self):
        """Remove compute resource by using the location name and compute
        resource name

        :id: dae7c7ae-b162-4601-8727-f227d1544e09

        :expectedresults: compute resource is added then removed

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self) as session:
            for resource_name in generate_strings_list():
                with self.subTest(resource_name):
                    loc_name = gen_string('alpha')
                    url = (LIBVIRT_RESOURCE_URL %
                           settings.compute_resources.libvirt_hostname)
                    resource = entities.LibvirtComputeResource(
                        name=resource_name,
                        organization=[self.org_],
                        url=url,
                    ).create()
                    self.assertEqual(resource.name, resource_name)
                    make_loc(
                        session,
                        name=loc_name,
                        organizations=[self.org_.name],
                        resources=[resource_name],
                    )
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_resources'])
                    element = self.location.wait_until_element(
                        (strategy1, value1 % resource_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.location.update(loc_name, resources=[resource_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_resources'])
                    element = session.nav.wait_until_element(
                        (strategy, value % resource_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_medium(self):
        """Remove medium by using location name and medium name

        :id: 61dece81-73bf-4f80-8894-ed7ca745120c

        :expectedresults: medium is added then removed

        :CaseLevel: Integration
        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        with Session(self) as session:
            for medium_name in generate_strings_list():
                with self.subTest(medium_name):
                    loc_name = gen_string('alpha')
                    medium = entities.Media(
                        name=medium_name,
                        organization=[self.org_],
                        os_family='Redhat',
                        path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
                    ).create()
                    self.assertEqual(medium.name, medium_name)
                    make_loc(
                        session,
                        medias=[medium_name],
                        organizations=[self.org_.name],
                        name=loc_name,
                    )
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_media'])
                    element = session.nav.wait_until_element(
                        (strategy1, value1 % medium_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.location.update(loc_name, medias=[medium_name])
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_media'])
                    element = session.nav.wait_until_element(
                        (strategy, value % medium_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNotNone(element)

    @run_only_on('sat')
    @tier2
    def test_positive_remove_template(self):
        """Remove config template

        :id: f510eb04-6bbb-4153-bda0-a183d070b9f2

        :expectedresults: config template is added and then removed

        :CaseLevel: Integration
        """
        strategy, value = common_locators['all_values_selection']
        with Session(self) as session:
            for template_name in generate_strings_list(length=8):
                with self.subTest(template_name):
                    loc_name = gen_string('alpha')
                    make_templates(
                        session,
                        name=template_name,
                        template_path=get_data_file(OS_TEMPLATE_DATA_FILE),
                        template_type='Provisioning template',
                        custom_really=True,
                    )
                    self.assertIsNotNone(self.template.search(template_name))
                    make_loc(
                        session,
                        name=loc_name,
                        organizations=[self.org_.name],
                    )
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_template'])
                    element = session.nav.wait_until_element(
                        (strategy, value % template_name))
                    # Item is listed in 'Selected Items' list and not
                    # 'All Items' list.
                    self.assertIsNotNone(element)
                    self.template.delete(template_name, dropdown_present=True)
                    self.location.search_and_click(loc_name)
                    session.nav.click(tab_locators['context.tab_template'])
                    element = session.nav.wait_until_element(
                        (strategy, value % template_name))
                    # Item is listed in 'All Items' list and not
                    # 'Selected Items' list.
                    self.assertIsNone(element)
