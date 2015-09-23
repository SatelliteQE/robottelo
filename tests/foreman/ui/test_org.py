# -*- encoding: utf-8 -*-
# pylint: disable=R0904
"""Test class for Organization UI"""

from ddt import ddt
from fauxfactory import gen_ipaddr, gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import INSTALL_MEDIUM_URL, LIBVIRT_RESOURCE_URL
from robottelo.helpers import (
    generate_strings_list, invalid_names_list, invalid_values_list)
from robottelo.decorators import (
    data, run_only_on, skip_if_bug_open, stubbed)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_lifecycle_environment, make_org
from robottelo.ui.locators import common_locators, locators, tab_locators
from robottelo.ui.session import Session


@ddt
class Org(UITestCase):
    """Implements Organization tests in UI"""

    # Tests for issues

    @skip_if_bug_open('bugzilla', 1177610)
    def test_auto_search(self):
        """@test: Search for an organization can be auto-completed by partial
        name

        @feature: Organizations

        @assert: Auto search for created organization works as intended

        @BZ: 1177610

        """
        org_name = gen_string('alpha')
        part_string = org_name[:3]
        with Session(self.browser) as session:
            page = session.nav.go_to_org
            make_org(session, org_name=org_name)
            auto_search = self.org.auto_complete_search(
                page, locators['org.org_name'], part_string, org_name,
                search_key='name')
            self.assertIsNotNone(auto_search)

    # Positive Create

    @data(*generate_strings_list())
    def test_positive_create_with_different_names(self, org_name):
        """@test: Create organization with valid name only.

        @feature: Organizations

        @assert: Organization is created, label is auto-generated

        @BZ: 1131469

        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    @stubbed('parent_org feature is disabled currently')
    @data(*generate_strings_list())
    def test_positive_create_with_parent(self, parent_name):
        """@test: Create organization with valid name, label, parent_org, desc.

        @feature: Organizations

        @assert: organization is created.

        """
        org_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_org(session, org_name=parent_name)
            make_org(
                session,
                org_name=org_name,
                label=gen_string('alpha'),
                desc=gen_string('alpha'),
                parent_org=parent_name
            )
            self.assertIsNotNone(self.org.search(org_name))

    @data({'name': gen_string('alpha'),
           'label': gen_string('alpha')},
          {'name': gen_string('numeric'),
           'label': gen_string('numeric')},
          {'name': gen_string('alphanumeric'),
           'label': gen_string('alphanumeric')})
    # As label cannot contain chars other than ascii alpha numerals, '_', '-'.
    def test_positive_create_with_diff_names_and_labels(self, test_data):
        """@test: Create organization with valid unmatching name and label only

        @feature: Organizations

        @assert: organization is created, label does not match name

        """
        org_name = test_data['name']
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, label=test_data['label'])
            self.org.search(org_name).click()
            name = session.nav.wait_until_element(
                locators['org.name']).get_attribute('value')
            label = session.nav.wait_until_element(
                locators['org.label']).get_attribute('value')
            self.assertNotEqual(name, label)

    @data(gen_string('alpha'),
          gen_string('numeric'),
          gen_string('alphanumeric'))
    # As label cannot contain chars other than ascii alpha numerals, '_', '-'.
    def test_positive_create_with_same_names_and_labels(self, org_data):
        """@test: Create organization with valid matching name and label only.

        @feature: Organizations

        @assert: organization is created, label matches name

        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_data, label=org_data)
            self.org.search(org_data).click()
            name = self.org.wait_until_element(
                locators['org.name']).get_attribute('value')
            label = self.org.wait_until_element(
                locators['org.label']).get_attribute('value')
            self.assertEqual(name, label)

    @skip_if_bug_open('bugzilla', 1079482)
    @skip_if_bug_open('bugzilla', 1131469)
    @data(*generate_strings_list())
    def test_positive_create_with_auto_gen_label(self, org_name):
        """@test: Create organization with valid name. Check that organization
        label is auto-populated

        @feature: Organizations

        @assert: organization is created, label is auto-generated

        @BZ: 1079482

        @BZ: 1131469

        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.search(org_name).click()
            label = session.nav.wait_until_element(locators['org.label'])
            label_value = label.get_attribute('value')
            self.assertIsNotNone(label_value)

    @data(*generate_strings_list())
    def test_positive_create_with_both_location_and_org(self, name):
        """@test: Select both organization and location.

        @feature: Organizations

        @assert: Both organization and location are selected.

        """
        location = entities.Location(name=name).create()
        self.assertEqual(location.name, name)
        with Session(self.browser) as session:
            make_org(session, org_name=name, locations=[name])
            self.assertIsNotNone(self.org.search(name))
            organization = session.nav.go_to_select_org(name)
            location = session.nav.go_to_select_loc(name)
            self.assertEqual(organization, name)
            self.assertEqual(location, name)

    @data(*invalid_values_list())
    def test_negative_create_with_different_names(self, org_name):
        """@test: Try to create organization and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        @feature: Organizations Negative Tests

        @assert: organization is not created

        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @skip_if_bug_open('bugzilla', 1131469)
    @data(*generate_strings_list())
    def test_negative_create_with_same_name(self, org_name):
        """@test: Create organization with valid values, then create a new one
        with same values.

        @feature: Organizations Negative Test.

        @assert: organization is not created

        @BZ: 1131469

        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.create(org_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    # Positive Delete

    @data(*generate_strings_list())
    def test_positive_delete(self, org_name):
        """@test: Create organization with valid values then delete it.

        @feature: Organizations Positive Delete test.

        @assert: Organization is deleted successfully

        """
        entities.Organization(name=org_name).create()
        with Session(self.browser) as session:
            session.nav.go_to_org()
            self.org.remove(org_name)

    @skip_if_bug_open('bugzilla', 1225588)
    @data(*generate_strings_list())
    def test_positive_delete_bz1225588(self, org_name):
        """@test: Create Organization with valid values and upload manifest.
        Then try to delete that organization.

        @feature: Organization Positive Delete Test.

        @assert: Organization is deleted successfully.

        """
        org = entities.Organization(name=org_name).create()
        with open(manifests.clone(), 'rb') as manifest:
            upload_manifest(org.id, manifest)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org_name, name='DEV')
            make_lifecycle_environment(
                session, org_name, name='QE', prior='DEV'
            )
            # Org cannot be deleted when selected,
            # So switching to Default Org and then deleting.
            session.nav.go_to_select_org('Default Organization')
            self.org.remove(org_name)
            session.nav.go_to_dashboard()
            status = self.org.search(org_name)
            # Check for at least ten times that org is deleted due #1225588
            for _ in range(10):
                status = self.org.search(org_name)
                if status is None:
                    break
            self.assertIsNone(status)

    # Negative Delete

    # Positive Update

    @skip_if_bug_open('bugzilla', 1131469)
    @data(*generate_strings_list())
    def test_positive_update_with_different_names(self, new_name):
        """@test: Create organization with valid values then update its name.

        @feature: Organizations Positive Update test.

        @assert: Organization name is updated successfully

        @BZ: 1131469

        """
        org_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_name=new_name)
            self.assertIsNotNone(self.org.search(new_name))

    # Negative Update

    @skip_if_bug_open('bugzilla', 1131469)
    @data(*invalid_names_list())
    def test_negative_update(self, new_name):
        """@test: Create organization with valid values then try to update it
        using incorrect name values

        @feature: Organizations Negative Update test.

        @assert: Organization name is not updated

        @BZ: 1131469

        """
        org_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_name=new_name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    # Miscellaneous

    @skip_if_bug_open('bugzilla', 1131469)
    @data(*generate_strings_list())
    def test_search_key(self, org_name):
        """@test: Create organization and search/find it.

        @feature: Organizations search.

        @assert: Proper organization found

        @BZ: 1131469

        """
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))

    # Associations

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_remove_domain(self, domain_name):
        """@test: Add a domain to an organization and remove it by organization
        name and domain name.

        @feature: Organizations Disassociate domain.

        @assert: the domain is removed from the organization

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        domain = entities.Domain(name=domain_name).create()
        self.assertEqual(domain.name, domain_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, domains=[domain_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_domains'])
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % domain_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, domains=[domain_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_domains'])
            element = session.nav.wait_until_element((strategy,
                                                      value % domain_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    #  Note: HTML username is invalid as per the UI msg.
    @data(
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
        gen_string('utf8'),
        gen_string('latin1'),
    )
    def test_remove_user(self, user_name):
        """@test: Create admin users then add user and remove it
        by using the organization name.

        @feature: Organizations Disassociate user.

        @assert: The user is added then removed from the organization

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        user = entities.User(
            login=user_name,
            firstname=user_name,
            lastname=user_name,
            password=gen_string('alpha'),
        ).create()
        self.assertEqual(user.login, user_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, users=[user_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_users'])
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % user_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, users=[user_name], new_users=None)
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_users'])
            element = session.nav.wait_until_element((strategy,
                                                      value % user_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_remove_hostgroup(self, host_grp_name):
        """@test: Add a hostgroup and remove it by using the organization
        name and hostgroup name.

        @feature: Organizations Remove Hostgroup.

        @assert: hostgroup is added to organization then removed.

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        host_grp = entities.HostGroup(name=host_grp_name).create()
        self.assertEqual(host_grp.name, host_grp_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, hostgroups=[host_grp_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_hostgrps'])
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % host_grp_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, hostgroups=[host_grp_name],
                            new_hostgroups=None)
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_hostgrps'])
            element = session.nav.wait_until_element((strategy,
                                                      value % host_grp_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_add_smartproxy_1(self, test_data):
        """@test: Add a smart proxy by using org and smartproxy name

        @feature: Organizations

        @assert: smartproxy is added

        @status: manual

        """

        pass

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_add_subnet(self, subnet_name):
        """@test: Add a subnet using organization name and subnet name.

        @feature: Organizations associate subnet.

        @assert: subnet is added.

        """
        strategy, value = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        subnet = entities.Subnet(
            name=subnet_name,
            network=gen_ipaddr(ip3=True),
            mask='255.255.255.0'
        ).create()
        self.assertEqual(subnet.name, subnet_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_subnets=[subnet_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_subnets'])
            element = session.nav.wait_until_element((strategy,
                                                      value % subnet_name))
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_add_domain(self, domain_name):
        """@test: Add a domain to an organization.

        @feature: Organizations associate domain.

        @assert: Domain is added to organization.

        """
        strategy, value = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        domain = entities.Domain(name=domain_name).create()
        self.assertEqual(domain.name, domain_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_domains=[domain_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_domains'])
            element = session.nav.wait_until_element((strategy,
                                                      value % domain_name))
            self.assertIsNotNone(element)

    @data(
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
        gen_string('utf8'),
        gen_string('latin1'),
    )
    def test_add_user(self, user_name):
        """@test: Create different types of users then add user using
        organization name.

        @feature: Organizations associate user.

        @assert: User is added to organization.

        """
        strategy, value = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        user = entities.User(
            login=user_name,
            firstname=user_name,
            lastname=user_name,
            password=gen_string('alpha')
        ).create()
        self.assertEqual(user.login, user_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_users=[user_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_users'])
            element = session.nav.wait_until_element((strategy,
                                                      value % user_name))
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_add_hostgroup(self, host_grp_name):
        """@test: Add a hostgroup by using the organization
        name and hostgroup name.

        @feature: Organizations associate host-group.

        @assert: hostgroup is added to organization

        """
        strategy, value = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        host_grp = entities.HostGroup(name=host_grp_name).create()
        self.assertEqual(host_grp.name, host_grp_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_hostgroups=[host_grp_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_hostgrps'])
            element = session.nav.wait_until_element((strategy,
                                                      value % host_grp_name))
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_add_location(self, location_name):
        """@test: Add a location by using the organization name and location
        name

        @feature: Organizations associate location.

        @assert: location is added to organization.

        """
        strategy, value = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        location = entities.Location(name=location_name).create()
        self.assertEqual(location.name, location_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_locations=[location_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_locations'])
            element = session.nav.wait_until_element((strategy,
                                                      value % location_name))
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_remove_computeresource(self, resource_name):
        """@test: Remove compute resource using the organization name and
        compute resource name.

        @feature: Organizations dis-associate compute-resource.

        @assert: compute resource is added then removed.

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        url = LIBVIRT_RESOURCE_URL % settings.server.hostname
        resource = entities.LibvirtComputeResource(
            name=resource_name,
            url=url
        ).create()
        self.assertEqual(resource.name, resource_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, resources=[resource_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_resources'])
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % resource_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, resources=[resource_name],
                            new_resources=None)
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_resources'])
            element = session.nav.wait_until_element((strategy,
                                                      value % resource_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_remove_medium(self, medium_name):
        """@test: Remove medium by using organization name and medium name.

        @feature: Organizations disassociate installation media.

        @assert: medium is added then removed.

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        medium = entities.Media(
            name=medium_name,
            path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
            os_family='Redhat',
        ).create()
        self.assertEqual(medium.name, medium_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name,
                     medias=[medium_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_media'])
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % medium_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.navigator.go_to_org()
            self.org.update(org_name, medias=[medium_name],
                            new_medias=None)
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_media'])
            element = session.nav.wait_until_element((strategy,
                                                      value % medium_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_remove_configtemplate(self, template_name):
        """@test: Remove config template.

        @feature: Organizations dissociate config templates.

        @assert: configtemplate is added then removed.

        @BZ: 1129612

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        entities.ConfigTemplate(name=template_name).create()
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, templates=[template_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_template'])
            element = session.nav.wait_until_element(
                (strategy1, value1 % template_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, templates=[template_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_template'])
            element = self.org.wait_until_element(
                (strategy, value % template_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    )
    def test_add_environment(self, env_name):
        """@test: Add environment by using organization name and env name.

        @feature: Organizations associate environment.

        @assert: environment is added.

        """
        strategy, value = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        env = entities.Environment(name=env_name).create_json()
        self.assertEqual(env['name'], env_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_envs=[env_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_env'])
            element = session.nav.wait_until_element((strategy,
                                                      value % env_name))
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @stubbed()
    @data("""DATADRIVENGOESHERE
        smartproxy name is alpha
        smartproxy name is numeric
        smartproxy name is alpha_numeric
        smartproxy name  is utf-8
        smartproxy name is latin1
        smartproxy name is html
    """)
    def test_remove_smartproxy_1(self, test_data):
        """@test: Remove smartproxy by using organization name and smartproxy
        name

        @feature: Organizations

        @assert: smartproxy is added then removed

        @status: manual

        """

        pass

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_add_computeresource(self, resource_name):
        """@test: Add compute resource using the organization
        name and compute resource name.

        @feature: Organizations associate compute resource.

        @assert: compute resource is added.

        """
        strategy, value = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        url = LIBVIRT_RESOURCE_URL % settings.server.hostname
        resource = entities.LibvirtComputeResource(
            name=resource_name,
            url=url,
        ).create()
        self.assertEqual(resource.name, resource_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_resources=[resource_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_resources'])
            element = session.nav.wait_until_element((strategy,
                                                      value % resource_name))
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_add_medium(self, medium_name):
        """@test: Add medium by using the organization name and medium name.

        @feature: Organizations associate medium.

        @assert: medium is added.

        """
        strategy, value = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        medium = entities.Media(
            name=medium_name,
            path_=INSTALL_MEDIUM_URL % gen_string('alpha', 6),
            os_family='Redhat',
        ).create()
        self.assertEqual(medium.name, medium_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_medias=[medium_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_media'])
            element = session.nav.wait_until_element((strategy,
                                                      value % medium_name))
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_add_configtemplate(self, template_name):
        """@test: Add config template by using organization name and
        config template name.

        @feature: Organizations associate config template.

        @assert: config template is added

        @BZ: 1129612

        """
        strategy, value = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        entities.ConfigTemplate(name=template_name).create()
        with Session(self.browser) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            self.org.update(org_name, new_templates=[template_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_template'])
            element = session.nav.wait_until_element(
                (strategy, value % template_name))
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(gen_string('alpha'),
          gen_string('numeric'),
          gen_string('alphanumeric'))
    def test_remove_environment(self, env_name):
        """@test: Remove environment by using org & environment name.

        @feature: Organizations dis-associate environment.

        @assert: environment is removed from Organization.

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        env = entities.Environment(name=env_name).create_json()
        self.assertEqual(env['name'], env_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, envs=[env_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_env'])
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % env_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, envs=[env_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_env'])
            element = session.nav.wait_until_element((strategy,
                                                      value % env_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)

    @run_only_on('sat')
    @data(*generate_strings_list())
    def test_remove_subnet(self, subnet_name):
        """@test: Remove subnet by using organization name and subnet name.

        @feature: Organizations dis-associate subnet.

        @assert: subnet is added then removed.

        """
        strategy, value = common_locators['entity_select']
        strategy1, value1 = common_locators['entity_deselect']
        org_name = gen_string('alpha')
        subnet = entities.Subnet(
            name=subnet_name,
            network=gen_ipaddr(ip3=True),
            mask='255.255.255.0',
        ).create()
        self.assertEqual(subnet.name, subnet_name)
        with Session(self.browser) as session:
            make_org(session, org_name=org_name, subnets=[subnet_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_subnets'])
            element = session.nav.wait_until_element((strategy1,
                                                      value1 % subnet_name))
            # Item is listed in 'Selected Items' list and not 'All Items' list.
            self.assertIsNotNone(element)
            self.org.update(org_name, subnets=[subnet_name])
            self.org.search(org_name).click()
            session.nav.click(tab_locators['context.tab_subnets'])
            element = session.nav.wait_until_element((strategy,
                                                      value % subnet_name))
            # Item is listed in 'All Items' list and not 'Selected Items' list.
            self.assertIsNotNone(element)
